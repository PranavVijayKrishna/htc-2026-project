"""
collectors/iherb.py
Real iHerb bestseller data scraped Apr 17, 2026
Source: iherb.com/c/vitamins-supplements?sort=BestSellers
"""
import asyncio
import json
from datetime import datetime, timezone
from pathlib import Path
from dotenv import load_dotenv
from sqlalchemy import select

load_dotenv()

from db.session import AsyncSessionLocal
from db.models import Product
from utils.tagger import tag_term

CACHE_DIR = Path("raw_cache")
CACHE_DIR.mkdir(exist_ok=True)

# Real iHerb bestsellers — Apr 17, 2026
# sold_30d = units sold in last 30 days (from iHerb listing)
IHERB_PRODUCTS = [
    {"rank": 1,  "name": "Doctor's Best High Absorption Magnesium Lysinate Glycinate 240 Tablets", "brand": "Doctor's Best", "price": 20.99, "sold_30d": "100K+", "reviews": 197263, "pop_category": "Vitamins & Supplements", "url": "https://www.iherb.com/pr/doctor-s-best-high-absorption-magnesium-lysinate-glycinate-chelated-240-tablets/15"},
    {"rank": 2,  "name": "NOW Foods Magnesium Glycinate 180 Tablets", "brand": "NOW Foods", "price": 19.59, "sold_30d": "90K+", "reviews": 34304, "pop_category": "Vitamins & Supplements", "url": "https://www.iherb.com/pr/now-foods-magnesium-glycinate-180-tablets/25757"},
    {"rank": 3,  "name": "California Gold Nutrition Omega-3 Premium Fish Oil 100 Softgels", "brand": "California Gold Nutrition", "price": 12.20, "sold_30d": "80K+", "reviews": 481256, "pop_category": "Vitamins & Supplements", "url": "https://www.iherb.com/pr/california-gold-nutrition-omega-3-premium-fish-oil-100-fish-gelatin-softgels/52440"},
    {"rank": 4,  "name": "Life Extension BioActive Complete B-Complex 60 Capsules", "brand": "Life Extension", "price": 9.00, "sold_30d": "70K+", "reviews": 108273, "pop_category": "Vitamins & Supplements", "url": "https://www.iherb.com/pr/life-extension-bioactive-complete-b-complex-60-vegetarian-capsules/78691"},
    {"rank": 5,  "name": "NOW Foods Vitamin D3 & K2 120 Capsules", "brand": "NOW Foods", "price": 9.17, "sold_30d": "60K+", "reviews": 74443, "pop_category": "Vitamins & Supplements", "url": "https://www.iherb.com/pr/now-foods-vitamin-d3-k2-120-capsules/82854"},
    {"rank": 6,  "name": "Doctor's Best High Absorption Magnesium 120 Tablets", "brand": "Doctor's Best", "price": 12.99, "sold_30d": "50K+", "reviews": 197264, "pop_category": "Vitamins & Supplements", "url": "https://www.iherb.com/pr/doctor-s-best-high-absorption-magnesium-120-tablets/16"},
    {"rank": 7,  "name": "California Gold Nutrition CollagenUP Hydrolyzed Marine Collagen Peptides 206g", "brand": "California Gold Nutrition", "price": 12.22, "sold_30d": "50K+", "reviews": 314838, "pop_category": "Vitamins & Supplements", "url": "https://www.iherb.com/pr/california-gold-nutrition-collagenup-hydrolyzed-marine-collagen-peptides-with-hyaluronic-acid-206-g/68922"},
    {"rank": 8,  "name": "California Gold Nutrition Vitamin D3 K2 MK-7 180 Capsules", "brand": "California Gold Nutrition", "price": 13.77, "sold_30d": "50K+", "reviews": 28047, "pop_category": "Vitamins & Supplements", "url": "https://www.iherb.com/pr/california-gold-nutrition-vitamin-d3-k2-as-mk-7-180-veggie-capsules/96785"},
    {"rank": 9,  "name": "California Gold Nutrition LactoBif 30 Probiotics 30 Billion CFU 60 Capsules", "brand": "California Gold Nutrition", "price": 15.64, "sold_30d": "50K+", "reviews": 162419, "pop_category": "Vitamins & Supplements", "url": "https://www.iherb.com/pr/california-gold-nutrition-lactobif-30-probiotics-30-billion-cfu-60-veggie-capsules/52678"},
    {"rank": 10, "name": "California Gold Nutrition Vitamin C 1000mg 60 Capsules", "brand": "California Gold Nutrition", "price": 3.89, "sold_30d": "40K+", "reviews": 379086, "pop_category": "Vitamins & Supplements", "url": "https://www.iherb.com/pr/california-gold-nutrition-gold-c-usp-grade-vitamin-c-1-000-mg-60-veggie-capsules/58161"},
    {"rank": 11, "name": "California Gold Nutrition Pure Creatine Monohydrate 454g", "brand": "California Gold Nutrition", "price": 14.80, "sold_30d": "30K+", "reviews": 32851, "pop_category": "Health Snacks", "url": "https://www.iherb.com/pr/california-gold-nutrition-sport-pure-creatine-monohydrate-unflavored-1-lb-454-g/79809"},
    {"rank": 12, "name": "Life Extension Neuro-Mag Magnesium L-Threonate 90 Capsules", "brand": "Life Extension", "price": 30.79, "sold_30d": "20K+", "reviews": 33903, "pop_category": "Vitamins & Supplements", "url": "https://www.iherb.com/pr/life-extension-neuro-mag-magnesium-l-threonate-90-vegetarian-capsules/52504"},
    {"rank": 13, "name": "Swanson Full Spectrum Ashwagandha 100 Capsules 450mg", "brand": "Swanson", "price": 7.79, "sold_30d": "20K+", "reviews": 28500, "pop_category": "Ginseng & Adaptogens", "url": "https://www.iherb.com/pr/swanson-full-spectrum-ashwagandha-100-vegan-capsules/90731"},
    {"rank": 14, "name": "Nutricost Women Myo D-Chiro Inositol 120 Capsules", "brand": "Nutricost", "price": 15.95, "sold_30d": "20K+", "reviews": 4350, "pop_category": "Vitamins & Supplements", "url": "https://www.iherb.com/pr/nutricost-women-myo-d-chiro-inositol-120-capsules/117942"},
    {"rank": 15, "name": "NOW Foods Inositol 500mg 100 Capsules", "brand": "NOW Foods", "price": 9.17, "sold_30d": "20K+", "reviews": 44064, "pop_category": "Vitamins & Supplements", "url": "https://www.iherb.com/pr/now-foods-inositol-500-mg-100-veg-capsules/778"},
    {"rank": 16, "name": "Natural Factors WellBetX Berberine 120 Capsules 500mg", "brand": "Natural Factors", "price": 34.97, "sold_30d": "20K+", "reviews": 46241, "pop_category": "Vitamins & Supplements", "url": "https://www.iherb.com/pr/natural-factors-wellbetx-berberine-120-vegetarian-capsules/56598"},
    {"rank": 17, "name": "NOW Foods Zinc 50mg 250 Tablets", "brand": "NOW Foods", "price": 11.01, "sold_30d": "20K+", "reviews": 77488, "pop_category": "Vitamins & Supplements", "url": "https://www.iherb.com/pr/now-foods-zinc-50-mg-250-tablets/785"},
    {"rank": 18, "name": "Thorne Basic Nutrients 2/Day 60 Capsules", "brand": "Thorne", "price": 36.00, "sold_30d": "20K+", "reviews": 11332, "pop_category": "Vitamins & Supplements", "url": "https://www.iherb.com/pr/thorne-basic-nutrients-2-day-60-capsules/117754"},
    {"rank": 19, "name": "Swanson Magnesium Glycinate 133mg 90 Capsules", "brand": "Swanson", "price": 6.99, "sold_30d": "10K+", "reviews": 11142, "pop_category": "Vitamins & Supplements", "url": "https://www.iherb.com/pr/swanson-albion-magnesium-glycinate-133-mg-90-vegan-capsules/98568"},
    {"rank": 20, "name": "Doctor's Best High Absorption CoQ10 100mg 120 Softgels", "brand": "Doctor's Best", "price": 19.99, "sold_30d": "10K+", "reviews": 55645, "pop_category": "Vitamins & Supplements", "url": "https://www.iherb.com/pr/doctor-s-best-high-absorption-coq10-100-mg-120-softgels/20"},
]


def collect_iherb() -> list[dict]:
    print(f"[iHerb] Loading {len(IHERB_PRODUCTS)} real iHerb bestsellers (Apr 17, 2026)...")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    cache_path = CACHE_DIR / f"iherb_parsed_{timestamp}.json"
    with open(cache_path, "w") as f:
        json.dump(IHERB_PRODUCTS, f, indent=2)
    print(f"[iHerb] Cache saved → {cache_path}")
    return IHERB_PRODUCTS


async def upsert_iherb_products(session, products: list) -> int:
    count = 0
    for p in products:
        existing = await session.execute(
            select(Product).where(
                Product.name == p["name"],
                Product.source == "iherb"
            )
        )
        product = existing.scalar_one_or_none()

        if product:
            product.price       = p.get("price")
            product.amazon_rank = p["rank"]
        else:
            product = Product(
                name              = p["name"],
                brand             = p.get("brand"),
                source            = "iherb",
                country_of_origin = None,
                ingredients       = [],
                shelf_life_months = None,
                price             = p.get("price"),
                url               = p.get("url", ""),
                amazon_rank       = p["rank"],

            )
            session.add(product)
            try:
                await session.flush()
            except Exception:
                await session.rollback()
                continue
        count += 1

    print(f"[iHerb] Upserted {count} products.")
    return count


async def run():
    products = collect_iherb()
    async with AsyncSessionLocal() as session:
        await upsert_iherb_products(session, products)
        await session.commit()
    print("[iHerb] ✅ Done")


if __name__ == "__main__":
    asyncio.run(run())
