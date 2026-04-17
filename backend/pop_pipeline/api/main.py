"""
api/main.py — FastAPI application
Endpoints:
  GET  /                          health check
  GET  /api/trends                list top trends with scores + compliance
  GET  /api/products              list scraped products with flags
  GET  /api/recommendations       P2/P3 facing: top opportunities for PoP
  POST /api/admin/refresh         trigger full pipeline re-run (admin only)
  POST /api/admin/refresh?source= trigger single-source re-run

Run:
    uvicorn api.main:app --reload --port 8000
"""
import asyncio
import os
from typing import Optional

from fastapi import FastAPI, Depends, HTTPException, Header, Query, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession
from dotenv import load_dotenv

load_dotenv()

from db.session import get_session
from db.models import Trend, Product, ComplianceFlag, Category
from pipeline.runner import run_pipeline

ADMIN_SECRET = os.getenv("ADMIN_SECRET", "changeme_hackathon_2026")

app = FastAPI(
    title="PoP Trend Intelligence API",
    description="Product discovery pipeline for Prince of Peace CPG",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # P3 frontend can be on any port
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Track pipeline status for polling ───────────────────────
_pipeline_status = {"running": False, "last_result": None}


# ─────────────────────────────────────────────────────────────
# Health check
# ─────────────────────────────────────────────────────────────
@app.get("/")
async def health():
    return {"status": "ok", "service": "PoP Trend Pipeline", "version": "1.0.0"}


# ─────────────────────────────────────────────────────────────
# GET /api/trends
# ─────────────────────────────────────────────────────────────
@app.get("/api/trends")
async def get_trends(
    category:  Optional[str] = Query(None, description="Filter by PoP category name"),
    source:    Optional[str] = Query(None, description="Filter by source (google_trends/reddit)"),
    min_score: float         = Query(0,    description="Minimum composite score"),
    limit:     int           = Query(50,   ge=1, le=200),
    session:   AsyncSession  = Depends(get_session),
):
    query = select(Trend).where(
        Trend.raw_signal_score >= min_score
    ).order_by(desc(Trend.raw_signal_score)).limit(limit)

    if source:
        query = query.where(Trend.source == source)

    result = await session.execute(query)
    trends = result.scalars().all()

    # Join category names
    cat_ids = {t.category_id for t in trends if t.category_id}
    cat_map = {}
    if cat_ids:
        cat_result = await session.execute(
            select(Category).where(Category.id.in_(cat_ids))
        )
        cat_map = {c.id: c.name for c in cat_result.scalars().all()}

    return {
        "count": len(trends),
        "trends": [
            {
                "id":              t.id,
                "term":            t.term,
                "source":          t.source,
                "category":        cat_map.get(t.category_id, "Unknown"),
                "score":           t.raw_signal_score,
                "growth_rate_pct": t.growth_rate,
                "confidence":      t.source_confidence,
                "dev_opportunity": (t.meta_json or {}).get("dev_opportunity"),
                "last_updated":    t.last_updated_at.isoformat() if t.last_updated_at else None,
            }
            for t in trends
        ],
    }


# ─────────────────────────────────────────────────────────────
# GET /api/products
# ─────────────────────────────────────────────────────────────
@app.get("/api/products")
async def get_products(
    limit:   int            = Query(50, ge=1, le=200),
    session: AsyncSession   = Depends(get_session),
):
    result = await session.execute(
        select(Product).order_by(Product.amazon_rank).limit(limit)
    )
    products = result.scalars().all()

    return {
        "count": len(products),
        "products": [
            {
                "id":                p.id,
                "name":              p.name,
                "brand":             p.brand,
                "source":            p.source,
                "amazon_rank":       p.amazon_rank,
                "rank_delta":        (
                    (p.amazon_rank_prev - p.amazon_rank)
                    if p.amazon_rank_prev and p.amazon_rank else None
                ),
                "price":             p.price,
                "country_of_origin": p.country_of_origin,
                "url":               p.url,
            }
            for p in products
        ],
    }


# ─────────────────────────────────────────────────────────────
# GET /api/recommendations  — P3 dashboard endpoint
# ─────────────────────────────────────────────────────────────
@app.get("/api/recommendations")
async def get_recommendations(
    session: AsyncSession = Depends(get_session),
):
    """
    Returns top 20 trends with compliance status and action recommendations.
    This is the main endpoint for the P3 buyer dashboard.
    """
    # Top trends by composite score
    result = await session.execute(
        select(Trend)
        .where(Trend.raw_signal_score > 0)
        .order_by(desc(Trend.raw_signal_score))
        .limit(20)
    )
    trends = result.scalars().all()

    recommendations = []
    for trend in trends:
        meta = trend.meta_json or {}
        dev_opp = meta.get("dev_opportunity", {})

        # Determine action
        action   = dev_opp.get("action", "investigate")
        pop_line = dev_opp.get("pop_line", "")
        concept  = dev_opp.get("concept", f"Investigate {trend.term}")

        rec = {
            "term":           trend.term,
            "score":          trend.raw_signal_score,
            "growth_pct":     trend.growth_rate,
            "action":         action,          # "develop" | "distribute" | "investigate"
            "pop_line":       pop_line,        # "Ginger" | "Ginseng" | ""
            "concept":        concept,
            "why_relevant":   _build_rationale(trend, meta),
            "confidence":     trend.source_confidence,
            "sources_seen":   meta.get("source", trend.source),
        }
        recommendations.append(rec)

    return {"count": len(recommendations), "recommendations": recommendations}


def _build_rationale(trend: Trend, meta: dict) -> str:
    """Human-readable explanation of why this trend is relevant to PoP."""
    parts = []
    gt_score = meta.get("gt_score_norm", 0)
    r_score  = meta.get("reddit_score_norm", 0)
    growth   = trend.growth_rate or 0

    if gt_score > 60:
        parts.append(f"High Google search volume ({gt_score:.0f}/100)")
    if r_score > 40:
        parts.append(f"Active Reddit discussion ({r_score:.0f}/100 engagement)")
    if growth > 20:
        parts.append(f"Growing fast (+{growth:.0f}% in 2 weeks)")
    elif growth < -20:
        parts.append(f"Declining trend ({growth:.0f}%)")

    if not parts:
        parts.append("Emerging signal across multiple sources")

    return "; ".join(parts)


# ─────────────────────────────────────────────────────────────
# GET /api/pipeline/status
# ─────────────────────────────────────────────────────────────
@app.get("/api/pipeline/status")
async def pipeline_status():
    return _pipeline_status


# ─────────────────────────────────────────────────────────────
# POST /api/admin/refresh  — DEMO SAFETY NET
# ─────────────────────────────────────────────────────────────
@app.post("/api/admin/refresh")
async def refresh_pipeline(
    background_tasks: BackgroundTasks,
    source: Optional[str] = Query(
        None,
        description="Run single source: google | reddit | amazon | fda",
    ),
    x_admin_secret: str = Header(..., description="Admin secret header"),
):
    """
    Trigger a full or partial pipeline refresh.
    Protected by X-Admin-Secret header.
    Runs in background — poll /api/pipeline/status for completion.
    """
    if x_admin_secret != ADMIN_SECRET:
        raise HTTPException(status_code=403, detail="Invalid admin secret")

    if _pipeline_status["running"]:
        return {"status": "already_running", "message": "Pipeline is already running"}

    sources = [source] if source else None

    async def _run():
        _pipeline_status["running"] = True
        try:
            result = await run_pipeline(sources)
            _pipeline_status["last_result"] = result
        finally:
            _pipeline_status["running"] = False

    background_tasks.add_task(_run)

    return {
        "status":  "started",
        "sources": sources or "all",
        "message": "Pipeline running in background. Poll /api/pipeline/status",
    }
