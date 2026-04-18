"""
collectors/openfoodfacts.py
Searches Open Food Facts API for health/wellness products.
Free, no API key needed.
Searches our seed terms to find real product data including ingredients.

Usage:
    python -m collectors.openfoodfacts
"""
import asyncio
import json
import time
from datetime import datetime, timezone
from pathlib import Path

import httpx
from dotenv import load_dotenv
from sqlalchemy import select
from tenacity import retry, stop_after_attempt, wait_exponential

load_dotenv()

from db.session import AsyncSessionLocal
from db.models import Product
from utils.seed_terms import SEED_TERMS

CACHE_DIR = Path("raw_cache")
CACHE_DIR.mkdir(exist_ok=True)

HEADERS = {
    "User-Agent": "PopTrendPipeline/1.0 (hackathon@uci.edu)",
    "Accept": "application/json",
}

# Focus on terms most relevant to PoP
SEARCH_TERMS = [
    "ashwagandha", "ginseng", "ginger", "lion's mane", "reishi",
    "matcha", "kombucha", "turmeric", "elderberry", "echinacea",
    "sea moss", "moringa", "spirulina", "berberine", "maca",
    "collagen", "probiotics", "magnesium glycinate", "tiger balm",
]

CATEGORY_MAP = {
    "ashwagandha": "Ginseng & Adaptogens",
    "ginseng": "Ginseng & Adaptogens",
    "ginger": "Ginger Products",
    "lion's mane": "Ginseng & Adaptogens",
    "reishi": "Ginseng & Adaptogens",
    "matcha": "Herbal Teas",
    "kombucha": "Functional Beverages",
    "turmeric": "Vitamins & Supplements",
    "elderberry": "Herbal Teas",
    "echinacea": "Herbal Teas",
    "sea moss": "Superfoods",
    "moringa": "Superfoods",
    "spirulina": "Superfoods",
    "berberine": "Vitamins & Supplements",
    "maca": "Ginseng & Adaptogens",
    "collagen": "Vitamins & Supplements",
    "probiotics": "Functional Beverages",
    "magnesium glycinate": "Vitamins & Supplements",
    "tiger balm": "Personal Care",
}


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=2, min=3, max=15))
def _search_term(term: str) -> list[dict]:
    url = "https://world.openfoodfacts.org/cgi/search.pl"
    params = {
        "search_terms": term,
        "search_simple": 1,
        "action": "process",
        "json": 1,
        "page_size": 10,
        "sort_by": "unique_scans_n",  # most scanned = most popular
    }
    with httpx.Client(headers=HEADERS, timeout=20) as client:
        resp = client.get(url, params=params)
        resp.raise_for_status()
        return resp.json().get("products", [])


def collect_openfoodfacts() -> list[dict]:
    print(f"[OpenFoodFacts] Searching {len(SEARCH_TERMS)} terms...")
    all_products = []
    seen_names = set()

    for i, term in enumerate(SEARCH_TERMS, 1):
        print(f"  [{i}/{len(SEARCH_TERMS)}] {term}")
        try:
            products = _search_term(term)
            for p in products:
                name = p.get("product_name", "").strip()
                if not name or name in seen_names:
                    continue
                seen_names.add(name)

                # Extract country
                countries = p.get("countries_tags", [])
                country = countries[0].replace("en:", "").title() if countries else None

                # Extract ingredients
                ingredients_text = p.get("ingredients_text", "") or ""
                ingredients = [
                    i.strip() for i in ingredients_text.split(",")
                    if i.strip()
                ][:10]  # keep first 10

                # Nutriscore
                nutriscore = p.get("nutriscore_grade", "").upper()

                all_products.append({
                    "name":              name[:512],
                    "brand":             p.get("brands", "").split(",")[0].strip() or None,
                    "source":            "openfoodfacts",
                    "pop_category":      CATEGORY_MAP.get(term, "Vitamins & Supplements"),
                    "search_term":       term,
                    "country_of_origin": country,
                    "ingredients":       ingredients,
                    "shelf_life_months": None,
                    "price":             None,
                    "url":               f"https://world.openfoodfacts.org/product/{p.get('code', '')}",
                    "nutriscore":        nutriscore,
                    "scans":             p.get("unique_scans_n", 0),
                    "fetched_at":        datetime.now(timezone.utc).isoformat(),
                })

            print(f"    → {len(products)} products found")
            time.sleep(1)  # polite delay

        except Exception as e:
            print(f"    ✗ Error: {e}")
            continue

    # Save cache
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    cache_path = CACHE_DIR / f"openfoodfacts_{timestamp}.json"
    with open(cache_path, "w") as f:
        json.dump(all_products, f, indent=2)
    print(f"[OpenFoodFacts] {len(all_products)} products saved → {cache_path}")
    return all_products


async def upsert_off_products(session, products: list) -> int:
    count = 0
    for p in products:
        existing = await session.execute(
            select(Product).where(
                Product.name == p["name"],
                Product.source == "openfoodfacts"
            )
        )
        product = existing.scalar_one_or_none()

        if product:
            product.ingredients = p.get("ingredients", [])
            product.country_of_origin = p.get("country_of_origin")
        else:
            product = Product(
                name              = p["name"],
                brand             = p.get("brand"),
                source            = "openfoodfacts",
                country_of_origin = p.get("country_of_origin"),
                ingredients       = p.get("ingredients", []),
                shelf_life_months = None,
                price             = None,
                url               = p.get("url", ""),
            )
            session.add(product)
            try:
                await session.flush()
            except Exception:
                await session.rollback()
                continue
        count += 1

    print(f"[OpenFoodFacts] Upserted {count} products.")
    return count


async def run():
    products = collect_openfoodfacts()
    async with AsyncSessionLocal() as session:
        await upsert_off_products(session, products)
        await session.commit()
    print("[OpenFoodFacts] ✅ Done")


if __name__ == "__main__":
    asyncio.run(run())
