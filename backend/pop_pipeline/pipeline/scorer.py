"""
pipeline/scorer.py
Merges signals from Google Trends + Reddit into a single composite score.
Also flags product development opportunities.

Scoring formula (all normalized to 0-100):
  composite = (
      0.40 * google_signal   +   # search volume = consumer demand
      0.30 * reddit_signal   +   # social discussion = emerging interest
      0.20 * growth_rate     +   # momentum
      0.10 * amazon_signal       # commercial validation
  )
"""
import asyncio
from datetime import datetime

from sqlalchemy import select, func, update
from sqlalchemy.ext.asyncio import AsyncSession

from db.models import Trend, Product
from utils.seed_terms import DEVELOPMENT_SIGNAL_TERMS


import json
from pathlib import Path

def _load_pop_ingredients() -> list[str]:
    try:
        path = Path(__file__).parent.parent / "raw_cache" / "popus_ingredients.json"
        with open(path) as f:
            return [i.lower().strip() for i in json.load(f)]
    except Exception:
        return ["ginger", "ginseng", "honey", "reishi", "green tea"]

POP_INGREDIENTS = _load_pop_ingredients()

GINGER_SIGNALS  = ["ginger", "kombucha", "probiotic", "turmeric", "lemon"]
GINSENG_SIGNALS = ["adaptogen", "reishi", "ashwagandha", "lion's mane", "mushroom", "nootropic"]


async def compute_composite_scores(session: AsyncSession) -> int:
    """
    Pull all trend rows, compute composite score, store in raw_signal_score.
    Returns count of updated rows.
    """
    # Fetch Google Trends signals
    gt_result = await session.execute(
        select(Trend).where(Trend.source == "google_trends")
    )
    gt_trends = {t.term: t for t in gt_result.scalars().all()}

    # Fetch Reddit signals
    r_result = await session.execute(
        select(Trend).where(Trend.source == "reddit")
    )
    r_trends = {t.term: t for t in r_result.scalars().all()}

    # Get max values for normalization
    max_gt_score = max((t.raw_signal_score or 0 for t in gt_trends.values()), default=1)
    max_r_score  = max((t.raw_signal_score or 0 for t in r_trends.values()),  default=1)
    max_growth   = max((abs(t.growth_rate or 0) for t in gt_trends.values()),  default=1)

    all_terms = set(list(gt_trends.keys()) + list(r_trends.keys()))
    updated = 0

    for term in all_terms:
        gt = gt_trends.get(term)
        r  = r_trends.get(term)

        # Normalize each signal
        gt_norm  = ((gt.raw_signal_score or 0) / max_gt_score) * 100 if gt else 0
        r_norm   = ((r.raw_signal_score  or 0) / max_r_score)  * 100 if r  else 0
        gr_norm  = min((abs(gt.growth_rate or 0) / max_growth) * 100, 100) if gt else 0

        # Composite (Amazon not yet wired — set to 0 placeholder)
        composite = (
            0.40 * gt_norm +
            0.30 * r_norm  +
            0.20 * gr_norm +
            0.10 * 0        # amazon placeholder
        )

        # Detect development opportunities
        dev_flags = _detect_dev_opportunity(term)

        # Update the Google Trends row as the "canonical" row
        canonical = gt or r
        if canonical:
            canonical.raw_signal_score = round(composite, 2)
            canonical.meta_json = {
                **(canonical.meta_json or {}),
                "composite_score":    round(composite, 2),
                "gt_score_norm":      round(gt_norm, 2),
                "reddit_score_norm":  round(r_norm, 2),
                "growth_norm":        round(gr_norm, 2),
                "dev_opportunity":    dev_flags,
                "scored_at":          datetime.utcnow().isoformat(),
            }
            session.add(canonical)
            updated += 1

    await session.flush()
    print(f"[Scorer] Updated composite scores for {updated} trends.")
    return updated


def _detect_dev_opportunity(term: str) -> dict:
    term_lower = term.lower()

    pop_match = any(
        ingr in term_lower or term_lower in ingr
        for ingr in POP_INGREDIENTS
        if len(ingr) > 4
    )

    if pop_match:
        if any(s in term_lower for s in GINGER_SIGNALS):
            return {
                "type":     "product_development",
                "pop_line": "Ginger",
                "concept":  f"PoP Ginger + {term.title()} — new product concept",
                "action":   "develop",
            }
        elif any(s in term_lower for s in GINSENG_SIGNALS):
            return {
                "type":     "product_development",
                "pop_line": "Ginseng",
                "concept":  f"PoP Ginseng + {term.title()} functional product",
                "action":   "develop",
            }
        else:
            return {
                "type":     "product_development",
                "pop_line": "PoP Wellness",
                "concept":  f"PoP Wellness + {term.title()} — new product concept",
                "action":   "develop",
            }

    return {
        "type":    "distribution",
        "concept": f"Source existing {term.title()} products for PoP distribution",
        "action":  "distribute",
    }
