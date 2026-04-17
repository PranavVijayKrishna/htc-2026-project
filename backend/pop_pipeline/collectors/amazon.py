"""
collectors/amazon.py
Scrapes Amazon bestseller pages for ~6 health/wellness categories.
Tracks rank deltas vs. previous run.
Respects robots.txt style delays; caches raw HTML to disk.

Category pages covered:
  - Health & Household > Vitamins & Supplements
  - Grocery & Gourmet Food > Herbal Teas
  - Grocery & Gourmet Food > Health Foods
  - Health > Sports Nutrition > Protein Bars
  - Grocery > Candy > Ginger Candies
  - Beauty & Personal Care > Pain Relief

Usage:
    python -m collectors.amazon
"""
import asyncio
import json
import re
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import httpx
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from sqlalchemy import select
from tenacity import retry, stop_after_attempt, wait_exponential

load_dotenv()

from db.session import AsyncSessionLocal
from db.models import Product, Trend
from utils.tagger import normalize_term, tag_term

CACHE_DIR = Path("raw_cache")
CACHE_DIR.mkdir(exist_ok=True)

# ── Target categories ────────────────────────────────────────
AMAZON_CATEGORIES = {
    "vitamins_supplements": {
        "url": "https://www.amazon.com/Best-Sellers-Health-Personal-Care-Vitamins-Dietary-Supplements/zgbs/hpc/3760911",
        "pop_category": "Vitamins & Supplements",
    },
    "herbal_teas": {
        "url": "https://www.amazon.com/Best-Sellers-Grocery-Gourmet-Food-Herbal-Teas/zgbs/grocery/16318611",
        "pop_category": "Herbal Teas",
    },
    "health_foods": {
        "url": "https://www.amazon.com/Best-Sellers-Grocery-Gourmet-Food-Health-Foods/zgbs/grocery/6502838011",
        "pop_category": "Health Snacks",
    },
    "protein_bars": {
        "url": "https://www.amazon.com/Best-Sellers-Sports-Nutrition-Bars/zgbs/sporting-goods/6932782011",
        "pop_category": "Health Snacks",
    },
    "personal_care_pain": {
        "url": "https://www.amazon.com/Best-Sellers-Health-Personal-Care-Pain-Relievers/zgbs/hpc/3760901",
        "pop_category": "Personal Care",
    },
    "functional_beverages": {
        "url": "https://www.amazon.com/Best-Sellers-Grocery-Gourmet-Food-Kombucha/zgbs/grocery/16578131",
        "pop_category": "Functional Beverages",
    },
}

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=2, min=5, max=30))
def _fetch_page(url: str) -> str:
    """Fetch a page with retries. Returns HTML string."""
    with httpx.Client(headers=HEADERS, timeout=20, follow_redirects=True) as client:
        resp = client.get(url)
        resp.raise_for_status()
        return resp.text


def _parse_bestsellers(html: str, category_key: str, pop_category: str) -> list[dict]:
    """
    Parse Amazon bestseller HTML.
    Returns list of product dicts.
    """
    soup = BeautifulSoup(html, "lxml")
    items = []

    # Amazon uses several different bestseller list structures
    # Try the zg-item-immersion approach first (most common)
    product_cells = soup.select("div.zg-item-immersion") or soup.select("li.zg-item-immersion")

    if not product_cells:
        # Fallback: newer layout
        product_cells = soup.select("div[class*='p13n-sc-uncoverable-faceout']")

    for rank_idx, cell in enumerate(product_cells[:50], 1):
        try:
            # Title
            title_el = (
                cell.select_one("div.p13n-sc-truncate") or
                cell.select_one("span.zg-text-center-align") or
                cell.select_one("a.a-link-normal span")
            )
            title = title_el.get_text(strip=True) if title_el else None
            if not title:
                continue

            # URL / ASIN
            link_el = cell.select_one("a.a-link-normal")
            product_url = ""
            asin = None
            if link_el and link_el.get("href"):
                href = link_el["href"]
                product_url = f"https://www.amazon.com{href}" if href.startswith("/") else href
                asin_match = re.search(r"/dp/([A-Z0-9]{10})", product_url)
                if asin_match:
                    asin = asin_match.group(1)

            # Price
            price_el = cell.select_one("span.p13n-sc-price") or cell.select_one("span.a-color-price")
            price_str = price_el.get_text(strip=True) if price_el else ""
            price = None
            price_match = re.search(r"[\d.]+", price_str.replace(",", ""))
            if price_match:
                price = float(price_match.group())

            # Brand (often in the title or a separate span)
            brand_el = cell.select_one("span.a-size-small.a-color-base")
            brand = brand_el.get_text(strip=True) if brand_el else None

            items.append({
                "name":              title,
                "brand":             brand,
                "source":            "amazon",
                "pop_category":      pop_category,
                "amazon_category":   category_key,
                "amazon_rank":       rank_idx,
                "asin":              asin,
                "url":               product_url,
                "price":             price,
                "country_of_origin": None,  # Would need product page; skip for now
                "ingredients":       [],
                "shelf_life_months": None,
                "fetched_at":        datetime.now(timezone.utc).isoformat(),
            })

        except Exception:
            continue

    return items


def collect_amazon() -> dict[str, list[dict]]:
    """
    Scrape all category pages.
    Returns dict: category_key → list of product dicts.
    Also saves raw HTML and parsed results to cache.
    """
    print(f"[Amazon] Scraping {len(AMAZON_CATEGORIES)} category pages...")
    all_results: dict[str, list[dict]] = {}
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    for cat_key, cat_info in AMAZON_CATEGORIES.items():
        print(f"  Category: {cat_key}")
        try:
            html = _fetch_page(cat_info["url"])

            # Cache raw HTML
            html_path = CACHE_DIR / f"amazon_{cat_key}_{timestamp}.html"
            with open(html_path, "w", encoding="utf-8") as f:
                f.write(html)

            products = _parse_bestsellers(html, cat_key, cat_info["pop_category"])
            all_results[cat_key] = products
            print(f"    → {len(products)} products found")

            # Polite delay between pages
            time.sleep(4)

        except Exception as e:
            print(f"    ✗ Error scraping {cat_key}: {e}")
            all_results[cat_key] = []
            continue

    # Cache parsed JSON
    json_path = CACHE_DIR / f"amazon_parsed_{timestamp}.json"
    with open(json_path, "w") as f:
        json.dump(all_results, f, indent=2, default=str)
    print(f"[Amazon] Parsed results saved → {json_path}")

    total = sum(len(v) for v in all_results.values())
    print(f"[Amazon] Total products collected: {total}")
    return all_results


async def _load_previous_ranks(session) -> dict[str, int]:
    """Load ASIN → previous rank map from DB."""
    result = await session.execute(
        select(Product.asin, Product.amazon_rank).where(Product.asin.isnot(None))
    )
    return {row.asin: row.amazon_rank for row in result if row.amazon_rank}


async def upsert_products(session, all_results: dict[str, list[dict]]) -> int:
    """Upsert Amazon products. Returns count."""
    prev_ranks = await _load_previous_ranks(session)
    count = 0

    for cat_key, products in all_results.items():
        for p_data in products:
            asin = p_data.get("asin")

            # Try to link to a trend row by name matching
            trend_id = None
            norm_name = normalize_term(p_data["name"])
            category_name = tag_term(norm_name) or p_data["pop_category"]

            # Look for matching trend
            trend_result = await session.execute(
                select(Trend).where(
                    Trend.source == "google_trends"
                ).limit(1)  # simplified — P2 can refine this join
            )

            # Upsert by ASIN if available, else by name
            existing = None
            if asin:
                r = await session.execute(
                    select(Product).where(Product.asin == asin)
                )
                existing = r.scalar_one_or_none()

            if existing:
                # Update with new rank, preserve old rank as prev
                existing.amazon_rank_prev = prev_ranks.get(asin, existing.amazon_rank)
                existing.amazon_rank      = p_data["amazon_rank"]
                existing.price            = p_data.get("price")
                existing.updated_at       = datetime.utcnow()
            else:
                product = Product(
                    name              = p_data["name"][:512],
                    brand             = p_data.get("brand"),
                    source            = "amazon",
                    country_of_origin = p_data.get("country_of_origin"),
                    ingredients       = p_data.get("ingredients", []),
                    shelf_life_months = p_data.get("shelf_life_months"),
                    price             = p_data.get("price"),
                    url               = p_data.get("url"),
                    asin              = asin,
                    amazon_rank       = p_data["amazon_rank"],
                    amazon_rank_prev  = None,
                )
                session.add(product)
            count += 1

    await session.flush()
    print(f"[Amazon] Upserted {count} product rows.")
    return count


async def run():
    results = collect_amazon()
    async with AsyncSessionLocal() as session:
        await upsert_products(session, results)
        await session.commit()
    print("[Amazon] ✅ Done")


if __name__ == "__main__":
    asyncio.run(run())
