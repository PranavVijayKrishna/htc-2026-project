"""
collectors/reddit.py
Searches 5 health/wellness subreddits for seed terms.
Scores by upvotes + comment count + recency.

Subreddits: r/HealthyFood, r/Supplements, r/Nootropics,
            r/HerbalMedicine, r/Kombucha

Usage:
    python -m collectors.reddit
"""
import asyncio
import json
import os
import re
from collections import defaultdict
from datetime import datetime, timezone, timedelta
from pathlib import Path

import praw
from dotenv import load_dotenv
from sqlalchemy import select

load_dotenv()

from db.session import AsyncSessionLocal
from db.models import Trend, Category
from utils.seed_terms import SEED_TERMS
from utils.tagger import normalize_term, tag_term

CACHE_DIR = Path("raw_cache")
CACHE_DIR.mkdir(exist_ok=True)

SUBREDDITS = [
    "HealthyFood",
    "Supplements",
    "Nootropics",
    "HerbalMedicine",
    "Kombucha",
    "nutrition",
    "herbalism",
]

LOOKBACK_DAYS = 30


def _build_reddit() -> praw.Reddit:
    return praw.Reddit(
        client_id     = os.getenv("REDDIT_CLIENT_ID"),
        client_secret = os.getenv("REDDIT_CLIENT_SECRET"),
        user_agent    = os.getenv("REDDIT_USER_AGENT", "pop_trend_bot/1.0"),
        read_only     = True,
    )


def _score_post(post) -> float:
    """Simple engagement score: upvotes + 2*comments (comments = stronger signal)."""
    return post.score + 2 * post.num_comments


def collect_reddit() -> dict:
    """
    Search each subreddit for each seed term.
    Aggregate mention count + engagement per term.
    Returns dict keyed by normalized term.
    """
    print(f"[Reddit] Starting collection across {len(SUBREDDITS)} subreddits...")
    reddit = _build_reddit()
    cutoff = datetime.now(timezone.utc) - timedelta(days=LOOKBACK_DAYS)

    # term → {mention_count, total_score, posts: [...]}
    term_data: dict[str, dict] = defaultdict(lambda: {
        "mention_count": 0,
        "total_score": 0.0,
        "top_posts": [],
    })

    for sub_name in SUBREDDITS:
        print(f"  Scanning r/{sub_name}...")
        try:
            subreddit = reddit.subreddit(sub_name)

            for term in SEED_TERMS:
                try:
                    results = subreddit.search(
                        query=term,
                        time_filter="month",
                        limit=25,
                        sort="relevance",
                    )
                    for post in results:
                        post_time = datetime.fromtimestamp(post.created_utc, tz=timezone.utc)
                        if post_time < cutoff:
                            continue

                        norm = normalize_term(term)
                        score = _score_post(post)
                        term_data[norm]["mention_count"] += 1
                        term_data[norm]["total_score"]   += score

                        # Keep top 3 posts per term
                        post_summary = {
                            "title":     post.title[:200],
                            "url":       f"https://reddit.com{post.permalink}",
                            "subreddit": sub_name,
                            "score":     post.score,
                            "comments":  post.num_comments,
                            "created":   post_time.isoformat(),
                        }
                        td = term_data[norm]["top_posts"]
                        td.append(post_summary)
                        td.sort(key=lambda x: x["score"], reverse=True)
                        term_data[norm]["top_posts"] = td[:3]

                except Exception as e:
                    # Subreddit might not exist or term has no results — skip silently
                    pass

        except Exception as e:
            print(f"    ✗ Error scanning r/{sub_name}: {e}")
            continue

    # ── Compute signal score (0-100 normalized) ─────────────
    results = {}
    max_mentions = max((v["mention_count"] for v in term_data.values()), default=1)
    max_score    = max((v["total_score"]   for v in term_data.values()), default=1)

    for term, data in term_data.items():
        if data["mention_count"] == 0:
            continue

        # Normalize to 0-100
        mention_norm = (data["mention_count"] / max_mentions) * 50
        score_norm   = (data["total_score"]   / max_score)    * 50
        signal       = round(mention_norm + score_norm, 2)

        results[term] = {
            "source":          "reddit",
            "term":            term,
            "mention_count":   data["mention_count"],
            "total_engagement": data["total_score"],
            "raw_signal_score": signal,
            "growth_rate_pct": None,   # Reddit doesn't give time-series easily
            "top_posts":       data["top_posts"],
            "fetched_at":      datetime.now(timezone.utc).isoformat(),
        }

    # ── Save raw cache ──────────────────────────────────────
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    cache_path = CACHE_DIR / f"reddit_{timestamp}.json"
    with open(cache_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"[Reddit] Raw cache saved → {cache_path}")
    print(f"[Reddit] Found signals for {len(results)} terms.")

    return results


async def upsert_reddit_trends(session, results: dict) -> int:
    count = 0
    for raw_term, data in results.items():
        norm_term     = normalize_term(raw_term)
        category_name = tag_term(norm_term)

        category_id = None
        if category_name:
            cat_result = await session.execute(
                select(Category).where(Category.name == category_name)
            )
            cat = cat_result.scalar_one_or_none()
            if cat:
                category_id = cat.id

        existing = await session.execute(
            select(Trend).where(Trend.source == "reddit", Trend.term == norm_term)
        )
        trend = existing.scalar_one_or_none()

        if trend:
            trend.raw_signal_score  = data["raw_signal_score"]
            trend.last_updated_at   = datetime.utcnow()
            trend.meta_json         = data
            trend.source_confidence = min(data["mention_count"] / 50.0, 1.0)
        else:
            trend = Trend(
                source            = "reddit",
                term              = norm_term,
                category_id       = category_id,
                raw_signal_score  = data["raw_signal_score"],
                source_confidence = min(data["mention_count"] / 50.0, 1.0),
                meta_json         = data,
            )
            session.add(trend)
        count += 1

    await session.flush()
    print(f"[Reddit] Upserted {count} trend rows.")
    return count


async def run():
    results = collect_reddit()
    async with AsyncSessionLocal() as session:
        await upsert_reddit_trends(session, results)
        await session.commit()
    print("[Reddit] ✅ Done")


if __name__ == "__main__":
    asyncio.run(run())
