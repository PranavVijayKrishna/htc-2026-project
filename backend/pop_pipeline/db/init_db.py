"""
db/init_db.py — Run once to create all tables and seed categories.
Usage: python -m db.init_db
"""
import asyncio
import os
import ssl
from dotenv import load_dotenv
from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

load_dotenv()

from db.models import Base, Category

CATEGORIES = [
    {"name": "Herbal Teas", "pop_category": "teas", "keywords": ["herbal tea", "green tea", "chamomile", "peppermint tea", "ginger tea", "turmeric tea", "matcha", "rooibos", "hibiscus tea", "oolong"]},
    {"name": "Ginseng & Adaptogens", "pop_category": "health_wellness", "keywords": ["ginseng", "ashwagandha", "rhodiola", "maca", "reishi", "lion's mane", "cordyceps", "holy basil", "adaptogen"]},
    {"name": "Ginger Products", "pop_category": "health_wellness", "keywords": ["ginger chew", "ginger candy", "ginger supplement", "ginger shot", "ginger beer", "crystallized ginger"]},
    {"name": "Functional Beverages", "pop_category": "health_wellness", "keywords": ["kombucha", "kefir", "probiotic drink", "prebiotic soda", "electrolyte drink", "mushroom coffee", "nootropic drink"]},
    {"name": "Health Snacks", "pop_category": "dry_goods", "keywords": ["protein bar", "energy bar", "granola", "trail mix", "seaweed snack", "superfood snack"]},
    {"name": "Confections", "pop_category": "confections", "keywords": ["honey candy", "herbal candy", "lozenge", "throat drop", "manuka honey", "dark chocolate"]},
    {"name": "Vitamins & Supplements", "pop_category": "health_wellness", "keywords": ["vitamin d3", "magnesium glycinate", "zinc supplement", "omega 3", "probiotics", "collagen peptides", "berberine", "nmn"]},
    {"name": "Personal Care", "pop_category": "personal_care", "keywords": ["tiger balm", "topical analgesic", "muscle rub", "pain relief patch", "arnica gel"]},
    {"name": "Superfoods", "pop_category": "dry_goods", "keywords": ["spirulina", "chlorella", "moringa", "wheatgrass", "sea moss", "black seed oil"]},
]


async def init():
    raw_url = os.getenv("DATABASE_URL", "")
    if not raw_url:
        raise RuntimeError("DATABASE_URL not set in .env")

    db_url = raw_url.replace("?sslmode=require", "").replace("?ssl=true", "")
    ssl_ctx = ssl.create_default_context()

    engine = create_async_engine(
        db_url,
        echo=True,
        connect_args={"ssl": ssl_ctx},
    )
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with engine.begin() as conn:
        print("Creating tables...")
        await conn.run_sync(Base.metadata.create_all)
        print("Tables created ✓")

    async with async_session() as session:
        for cat_data in CATEGORIES:
            result = await session.execute(
                select(Category).where(Category.name == cat_data["name"])
            )
            existing = result.scalar_one_or_none()
            if not existing:
                session.add(Category(**cat_data))
                print(f"  Seeded: {cat_data['name']}")
            else:
                print(f"  Already exists: {cat_data['name']}")
        await session.commit()
        print("Categories seeded ✓")

    await engine.dispose()
    print("\n✅ Database initialized successfully!")


if __name__ == "__main__":
    asyncio.run(init())
