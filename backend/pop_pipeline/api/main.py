"""
api/main.py — FastAPI application
Endpoints:
  GET  /                          health check
  GET  /api/trends                list top trends with scores + compliance
  GET  /api/products              list scraped products with flags
  GET  /api/recommendations       P2/P3 facing: top opportunities for PoP
  GET  /api/admin/weights         read current scoring weights
  POST /api/admin/weights         live weight tuning (demo moment — re-orders instantly)
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
from pydantic import BaseModel, field_validator
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession
from dotenv import load_dotenv
from groq import Groq
from duckduckgo_search import DDGS

load_dotenv()

from db.session import get_session
from db.models import Trend, Product, ComplianceFlag, Category
from pipeline.runner import run_pipeline

#from backend.filters.filters import run_filter

ADMIN_SECRET = os.getenv("ADMIN_SECRET", "changeme_hackathon_2026")

_groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))
_rationale_cache: dict = {}
_desc_cache: dict = {}

# Live-tunable weights — P3 demo moment (shift on stage, rankings re-order instantly)
_current_weights = {
    "growth":          0.40,
    "relevance":       0.30,
    "cross_signal":    0.05,  # Reddit gone, less cross-source signal
    "competition_gap": 0.10,
    "recency":         0.15,  # always 1.0 — guaranteed floor contribution
}

_VALID_WEIGHT_KEYS = set(_current_weights.keys())


class WeightsPayload(BaseModel):
    growth:          float
    relevance:       float
    cross_signal:    float
    competition_gap: float
    recency:         float

    @field_validator("growth", "relevance", "cross_signal", "competition_gap", "recency")
    @classmethod
    def between_zero_and_one(cls, v: float) -> float:
        if not (0.0 <= v <= 1.0):
            raise ValueError("Each weight must be between 0 and 1")
        return v

class ChatMessage(BaseModel):
    term:       str
    growth_pct: float
    category:   str
    angle:      str
    concept:    str
    messages:   list[dict]  # [{"role": "user"|"assistant", "content": "..."}]


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
    limit:            int           = Query(50, ge=1, le=200),
    exclude_failed:   bool          = Query(False, description="Hide products that fail any filter"),
    exclude_flagged:  bool          = Query(False, description="Hide products with origin warnings"),
    session:          AsyncSession  = Depends(get_session),
):
    result = await session.execute(
        select(Product).order_by(Product.amazon_rank).limit(limit)
    )
    products = result.scalars().all()

    output = []
    for p in products:
        # Build the dict your filter expects
        product_dict = {
            "shelf_life_months":  (p.meta_json or {}).get("shelf_life_months", 24),
            "ingredients":        (p.meta_json or {}).get("ingredients", []),
            "country_of_origin":  p.country_of_origin or "",
        }

        shelf_life_result, fda_result, origin_result = run_filter(product_dict)

        passed  = shelf_life_result.passed and fda_result.passed
        flags   = [r.flag for r in (shelf_life_result, fda_result, origin_result) if r.flag]
        reasons = [r.reason for r in (shelf_life_result, fda_result, origin_result) if r.reason]

        if exclude_failed  and not passed:   continue
        if exclude_flagged and flags:         continue

        output.append({
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
            # ── Filter results ──────────────────────────
            "filter": {
                "passed":  passed,
                "reasons": reasons,   # why it failed, if any
                "flags":   flags,     # warnings (non-blocking)
            },
        })

    return {"count": len(output), "products": output}



# ─────────────────────────────────────────────────────────────
# GET /api/recommendations  — P3 dashboard endpoint
# ─────────────────────────────────────────────────────────────
@app.get("/api/recommendations")
async def get_recommendations(
    category:  Optional[str] = Query(None),
    angle:     Optional[str] = Query(None, description="distribute | develop"),
    min_score: float         = Query(0.0),
    limit:     int           = Query(20, ge=1, le=100),
    session:   AsyncSession  = Depends(get_session),
):
    """
    Returns top trends ranked by composite score computed on-the-fly from
    _current_weights — so a POST /api/admin/weights re-orders results instantly.
    """
    result = await session.execute(
        select(Trend).where(Trend.raw_signal_score > 0).limit(200)
    )
    trends = result.scalars().all()

    w = _current_weights
    scored = []

    for trend in trends:
        meta = trend.meta_json or {}

        # Pull normalized sub-scores stored by scorer.py (all 0–100)
        gt_norm  = meta.get("gt_score_norm",  0.0) / 100
        gr_norm  = meta.get("growth_norm",    0.0) / 100
        sources_with_term = 0
        if gt_norm > 0:
            sources_with_term += 1

        iherb_result = await session.execute(
            select(Product).where(
                Product.source == "iherb",
                Product.name.ilike(f"%{trend.term}%")
            )
        )
        if iherb_result.scalars().first():
            sources_with_term += 1

        if trend.source == "amazon":
            sources_with_term += 1

        if sources_with_term >= 3:
            cross = 1.0
        elif sources_with_term == 2:
            cross = 0.5
        else:
            cross = 0.0

        # Real competition gap: fewer matching products in DB = better opportunity
        product_result = await session.execute(
            select(Product).where(Product.name.ilike(f"%{trend.term}%"))
        )
        competing_products = len(product_result.scalars().all())
        if competing_products == 0:
            competition_gap = 0.8
        elif competing_products <= 3:
            competition_gap = 0.6
        elif competing_products <= 10:
            competition_gap = 0.4
        else:
            competition_gap = 0.2

        sub_scores_missing = (gt_norm == 0 and gr_norm == 0)
        if sub_scores_missing:
            composite = (trend.raw_signal_score or 0) / 100
        else:
            composite = (
                w["growth"]          * gr_norm +
                w["relevance"]       * gt_norm +
                w["cross_signal"]    * cross   +
                w["competition_gap"] * competition_gap +
                w["recency"]         * 1.0
            )

        dev_opp  = meta.get("dev_opportunity", {})
        rec_angle = dev_opp.get("action", "distribute")

        if angle and rec_angle != angle:
            continue

        scored.append({
            "term":         trend.term,
            "score":        round(min(10.0, composite * 12), 2),
            "growth_pct":   trend.growth_rate,
            "angle":        rec_angle,
            "pop_line":     dev_opp.get("pop_line", ""),
            "concept":      dev_opp.get("concept", f"Investigate {trend.term}"),
            "description":  _build_product_desc(trend.term),
            "why_relevant": _build_llm_rationale(
                trend.term,
                dev_opp.get("pop_line", "health & wellness"),
                trend.growth_rate or 0,
                rec_angle,
                dev_opp.get("concept", f"Investigate {trend.term}"),
            ),
            "confidence":   trend.source_confidence,
            "sources_seen": meta.get("source", trend.source),
            "components": {
                "growth":          round(gr_norm, 2),
                "relevance":       round(gt_norm, 2),
                "cross_signal":    round(cross,   2),
                "competition_gap": round(competition_gap, 2),
                "recency":         1.0,
            },
        })

    scored.sort(key=lambda x: x["score"], reverse=True)
    filtered = [r for r in scored if r["score"] >= min_score]
    if category:
        filtered = [r for r in filtered if category.lower() in r["term"].lower()]

    return {"count": len(filtered), "recommendations": filtered[:limit]}


def _build_llm_rationale(term: str, category: str, growth_pct: float, angle: str, concept: str) -> str:
    if term in _rationale_cache:
        return _rationale_cache[term]
    try:
        prompt = f"""You are a CPG buyer at Prince of Peace. Write exactly 3 bullet points about this trend opportunity.

Data: {term} | +{growth_pct}% growth | {category} | {angle} | {concept}

Rules:
- Max 12 words for bullet 1 and 2
- Bullet 1: what the data signals (must include {growth_pct}%)
- Bullet 2: one specific next action for PoP
- Bullet 3: sourcing info — 1-2 real wholesale or retail links for {term}, country of origin, retailer name
- No filler words like "significant", "capitalize", "leverage"
- Write like an analyst note
- Use - not * for bullets
- For bullet 3 format: "Source: [Retailer] ([country]) — [url]"

Example format:
- [term] surging {growth_pct}% — [one insight]
- [specific action]: [who/what/where]
- Source: [Retailer Name] ([country]) — [url]"""
        response = _groq_client.chat.completions.create(
            model="qwen/qwen3-32b",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=200,
            temperature=0.7,
        )
        rationale = response.choices[0].message.content.strip()
        _rationale_cache[term] = rationale
        return rationale
    except Exception:
        return f"{term.title()} is growing {growth_pct:.0f}% week-over-week. Review for sourcing feasibility."


def _build_product_desc(term: str) -> str:
    if term in _desc_cache:
        return _desc_cache[term]
    try:
        prompt = f"""In one sentence of 20 words or fewer, describe what "{term}" is and name its 2-3 main active ingredients or compounds. Write for a non-technical retail buyer. No marketing language."""
        response = _groq_client.chat.completions.create(
            model="qwen/qwen3-32b",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=60,
            temperature=0.3,
        )
        desc = response.choices[0].message.content.strip().strip('"')
        _desc_cache[term] = desc
        return desc
    except Exception:
        return f"{term.title()} — a health and wellness ingredient gaining consumer interest."


# ─────────────────────────────────────────────────────────────
# GET /api/admin/weights  — read current weights
# POST /api/admin/weights — live weight tuning (demo moment)
# ─────────────────────────────────────────────────────────────
@app.get("/api/admin/weights")
async def get_weights():
    return _current_weights


@app.post("/api/admin/weights")
async def update_weights(
    payload: WeightsPayload,
    x_admin_secret: str = Header(...),
):
    if x_admin_secret != ADMIN_SECRET:
        raise HTTPException(status_code=403, detail="Invalid admin secret")

    _current_weights.update(payload.model_dump())
    return {"msg": "Weights updated", "weights": _current_weights}


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


# ─────────────────────────────────────────────────────────────
# POST /api/chat  — Dive Deeper chatbot per trend card
# ─────────────────────────────────────────────────────────────
@app.post("/api/chat")
async def chat_with_trend(payload: ChatMessage):
    # Angle-aware search: supplier hunt vs product dev research
    if payload.angle == "develop":
        query = f"{payload.term} CPG product development formulation manufacturer"
    else:
        query = f"{payload.term} supplement wholesale supplier sourcing"

    search_results = ""
    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=3))
            for r in results:
                search_results += f"- {r['title']}: {r['href']}\n"
    except Exception:
        search_results = "No search results available."

    system_prompt = f"""You are a helpful AI assistant. Answer questions about products, trends, and market opportunities in a friendly, conversational way.

Context: {payload.term} | +{payload.growth_pct}% growth | {payload.category} | {payload.angle}
Concept: {payload.concept}

Web results for context:
{search_results}

Keep answers concise and clear. Include relevant links from the search results when helpful."""

    try:
        response = _groq_client.chat.completions.create(
            model="qwen/qwen3-32b",
            messages=[
                {"role": "system", "content": system_prompt},
                *payload.messages,
            ],
            max_tokens=250,
            temperature=0.7,
        )
        return {"reply": response.choices[0].message.content.strip()}
    except Exception:
        return {"reply": "Sorry, I couldn't process that. Please try again."}
