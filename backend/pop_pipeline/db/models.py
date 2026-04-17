"""
db/models.py — SQLAlchemy models for the 4 core tables.
Compatible with PostgreSQL (Neon / Supabase / local).
"""
from datetime import datetime
from typing import Any

from sqlalchemy import (
    BigInteger, Boolean, Column, DateTime, Float, ForeignKey,
    Integer, String, Text, JSON, ARRAY, UniqueConstraint, text,
)
from sqlalchemy.orm import DeclarativeBase, relationship


class Base(DeclarativeBase):
    pass


# ─────────────────────────────────────────────────────────────
# 1. categories  — maps external terms → PoP taxonomy
# ─────────────────────────────────────────────────────────────
class Category(Base):
    __tablename__ = "categories"

    id         = Column(Integer, primary_key=True, autoincrement=True)
    name       = Column(String(120), nullable=False, unique=True)   # e.g. "Herbal Teas"
    pop_category = Column(String(120), nullable=False)              # PoP's internal label
    keywords   = Column(ARRAY(Text), nullable=False, default=[])    # seed keyword list

    trends     = relationship("Trend", back_populates="category_rel")

    def __repr__(self):
        return f"<Category {self.name}>"


# ─────────────────────────────────────────────────────────────
# 2. trends  — one row per unique term/source combination
# ─────────────────────────────────────────────────────────────
class Trend(Base):
    __tablename__ = "trends"
    __table_args__ = (
        UniqueConstraint("source", "term", name="uq_trend_source_term"),
    )

    id               = Column(BigInteger, primary_key=True, autoincrement=True)
    source           = Column(String(60), nullable=False)    # "google_trends" | "reddit" | "amazon"
    term             = Column(String(255), nullable=False)   # normalized term
    category_id      = Column(Integer, ForeignKey("categories.id"), nullable=True)
    first_seen_at    = Column(DateTime, nullable=False, default=datetime.utcnow)
    last_updated_at  = Column(DateTime, nullable=False, default=datetime.utcnow,
                              onupdate=datetime.utcnow)
    growth_rate      = Column(Float, nullable=True)          # % week-over-week
    raw_signal_score = Column(Float, nullable=True)          # 0-100 normalised
    source_confidence = Column(Float, nullable=True)         # 0-1
    meta_json        = Column(JSON, nullable=True)           # extra source-specific data

    category_rel = relationship("Category", back_populates="trends")
    products     = relationship("Product", back_populates="trend")

    def __repr__(self):
        return f"<Trend {self.term!r} [{self.source}] score={self.raw_signal_score}>"


# ─────────────────────────────────────────────────────────────
# 3. products  — discovered product listings tied to a trend
# ─────────────────────────────────────────────────────────────
class Product(Base):
    __tablename__ = "products"

    id                = Column(BigInteger, primary_key=True, autoincrement=True)
    trend_id          = Column(BigInteger, ForeignKey("trends.id"), nullable=True)
    name              = Column(String(512), nullable=False)
    brand             = Column(String(255), nullable=True)
    source            = Column(String(60),  nullable=False)   # "amazon" | "reddit" | ...
    country_of_origin = Column(String(120), nullable=True)
    ingredients       = Column(ARRAY(Text), nullable=True)
    shelf_life_months = Column(Integer, nullable=True)
    price             = Column(Float, nullable=True)
    url               = Column(Text, nullable=True)
    asin              = Column(String(20), nullable=True, unique=True)
    amazon_rank       = Column(Integer, nullable=True)
    amazon_rank_prev  = Column(Integer, nullable=True)        # for delta calc
    created_at        = Column(DateTime, default=datetime.utcnow)
    updated_at        = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    trend    = relationship("Trend", back_populates="products")
    flags    = relationship("ComplianceFlag", back_populates="product")

    def __repr__(self):
        return f"<Product {self.name[:40]!r}>"


# ─────────────────────────────────────────────────────────────
# 4. compliance_flags  — write-only audit log of filter decisions
# ─────────────────────────────────────────────────────────────
class ComplianceFlag(Base):
    __tablename__ = "compliance_flags"

    id         = Column(BigInteger, primary_key=True, autoincrement=True)
    product_id = Column(BigInteger, ForeignKey("products.id"), nullable=False)
    rule       = Column(String(120), nullable=False)   # e.g. "shelf_life_12mo"
    passed     = Column(Boolean, nullable=False)
    note       = Column(Text, nullable=True)
    checked_at = Column(DateTime, default=datetime.utcnow)

    product = relationship("Product", back_populates="flags")

    def __repr__(self):
        return f"<Flag {self.rule} passed={self.passed}>"
