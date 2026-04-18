"""
pipeline/runner.py
Orchestrates all collectors in sequence.
Called by POST /api/admin/refresh and can be run directly.

Usage:
    python -m pipeline.runner
    python -m pipeline.runner --source google  # single source
"""
import asyncio
import argparse
import sys
from datetime import datetime

from collectors.google_trends import collect_google_trends, upsert_trends
from collectors.reddit import collect_reddit, upsert_reddit_trends
from collectors.amazon import collect_amazon, upsert_products
from collectors.iherb import collect_iherb, upsert_iherb_products
from collectors.fda import refresh_fda_data, run_compliance_check_all
from db.session import AsyncSessionLocal
from pipeline.scorer import compute_composite_scores


async def run_pipeline(sources: list[str] = None) -> dict:
    """
    Run the full pipeline (or subset).
    Returns summary dict for API response.
    """
    sources = sources or ["google", "amazon", "iherb", "fda"]
    start   = datetime.utcnow()
    summary = {"started_at": start.isoformat(), "steps": {}}

    print("\n" + "=" * 60)
    print(f"  PoP Trend Pipeline — {start.strftime('%Y-%m-%d %H:%M:%S UTC')}")
    print("=" * 60 + "\n")

    async with AsyncSessionLocal() as session:

        if "google" in sources:
            print("▶ Step 1/4: Google Trends")
            try:
                gt_data  = collect_google_trends()
                gt_count = await upsert_trends(session, gt_data)
                await session.commit()
                summary["steps"]["google_trends"] = {"status": "ok", "rows": gt_count}
            except Exception as e:
                summary["steps"]["google_trends"] = {"status": "error", "error": str(e)}
                print(f"  ✗ Google Trends failed: {e}")

        if "reddit" in sources:
            print("\n▶ Step 2/4: Reddit")
            try:
                r_data  = collect_reddit()
                r_count = await upsert_reddit_trends(session, r_data)
                await session.commit()
                summary["steps"]["reddit"] = {"status": "ok", "rows": r_count}
            except Exception as e:
                summary["steps"]["reddit"] = {"status": "error", "error": str(e)}
                print(f"  ✗ Reddit failed: {e}")

        if "amazon" in sources:
            print("\n▶ Step 3/4: Amazon")
            try:
                a_data  = collect_amazon()
                a_count = await upsert_products(session, a_data)
                await session.commit()
                summary["steps"]["amazon"] = {"status": "ok", "rows": a_count}
            except Exception as e:
                summary["steps"]["amazon"] = {"status": "error", "error": str(e)}
                print(f"  ✗ Amazon failed: {e}")

        if "iherb" in sources:
            print("\n▶ Step 3b/4: iHerb Bestsellers")
            try:
                ih_data  = collect_iherb()
                ih_count = await upsert_iherb_products(session, ih_data)
                await session.commit()
                summary["steps"]["iherb"] = {"status": "ok", "rows": ih_count}
            except Exception as e:
                summary["steps"]["iherb"] = {"status": "error", "error": str(e)}
                print(f"  ✗ iHerb failed: {e}")

        if "fda" in sources:
            print("\n▶ Step 4/4: FDA Compliance Flags")
            try:
                refresh_fda_data()
                await run_compliance_check_all()
                summary["steps"]["fda"] = {"status": "ok"}
            except Exception as e:
                summary["steps"]["fda"] = {"status": "error", "error": str(e)}
                print(f"  ✗ FDA failed: {e}")

        # Compute composite scores across all sources
        print("\n▶ Computing composite scores...")
        try:
            scored = await compute_composite_scores(session)
            await session.commit()
            summary["steps"]["scoring"] = {"status": "ok", "trends_scored": scored}
        except Exception as e:
            summary["steps"]["scoring"] = {"status": "error", "error": str(e)}
            print(f"  ✗ Scoring failed: {e}")

    elapsed = (datetime.utcnow() - start).total_seconds()
    summary["elapsed_seconds"] = round(elapsed, 1)
    summary["finished_at"] = datetime.utcnow().isoformat()

    print(f"\n✅ Pipeline complete in {elapsed:.1f}s")
    print(f"   Summary: {summary['steps']}")
    return summary


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="PoP Trend Pipeline")
    parser.add_argument(
        "--source",
        choices=["google", "reddit", "amazon", "fda", "all"],
        default="all",
        help="Which collector to run",
    )
    args = parser.parse_args()

    sources = None if args.source == "all" else [args.source]
    asyncio.run(run_pipeline(sources))
