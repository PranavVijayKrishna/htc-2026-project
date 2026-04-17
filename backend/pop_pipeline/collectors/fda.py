"""
collectors/fda.py
Downloads and parses FDA public banned/restricted ingredient data.

Sources:
  1. FDA Dietary Supplement Ingredient Advisory List (public CSV/JSON)
  2. FDA Import Alerts (selected, cached locally)
  3. Hardcoded high-risk ingredient list (industry knowledge)

Writes to compliance_flags table when called with a product.
Also maintains a local fda_restricted.json reference file.

Usage:
    python -m collectors.fda                 # refresh the list
    from collectors.fda import is_fda_safe   # use in P2 scoring
"""
import asyncio
import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import httpx
from dotenv import load_dotenv
from sqlalchemy import select

load_dotenv()

from db.session import AsyncSessionLocal
from db.models import Product, ComplianceFlag

CACHE_DIR = Path("raw_cache")
CACHE_DIR.mkdir(exist_ok=True)

FDA_CACHE_PATH = Path("raw_cache/fda_restricted.json")

# ── FDA Data Sources ─────────────────────────────────────────
FDA_SOURCES = {
    # FDA CFSAN Adverse Event Reporting System — dietary supps
    "dietary_supplement_alerts": (
        "https://www.fda.gov/food/dietary-supplements/"
        "dietary-supplement-ingredient-advisory-list"
    ),
    # FDA tainted products database (JSON endpoint)
    "tainted_products": (
        "https://www.accessdata.fda.gov/scripts/sda/sdNavigation.cfm"
        "?sd=tainted_supplements_cder&displayAll=true&page=1"
    ),
}

# ── Hardcoded high-risk ingredients (always flag these) ──────
# Sources: FDA warnings + industry compliance standards
FDA_RESTRICTED_INGREDIENTS = {
    # Stimulants banned in US dietary supplements
    "ephedrine", "ephedra", "sibutramine", "phenolphthalein",
    "dmaa", "1,3-dimethylamylamine", "aegeline", "acacia rigidula",
    "dmha", "octodrine", "dmba", "bmpea", "deterenol",
    # Weight loss - FDA recalled
    "2,4-dinitrophenol", "dnp",
    # Sexual enhancement - common FDA taint
    "sildenafil", "tadalafil", "vardenafil",
    # Anabolic steroids
    "androstenedione", "dehydroepiandrosterone",
    # Problematic herbs
    "aristolochic acid", "comfrey",  # hepatotoxic
    "kava",  # liver risk (conditional)
    "coltsfoot", "life root", "tansy ragwort",  # pyrrolizidine alkaloids
    # Heavy metals above threshold (flag by name)
    "lead acetate",
    # Cannabinoids (FDA regulatory gray zone)
    "thc", "delta-8 thc", "delta-9 thc",
    # Recalled in 2023-2024
    "tianeptine", "kratom",  # FDA warning letters issued
    "amanita muscaria",
}

# ── High tariff / trade restriction countries ─────────────────
HIGH_TARIFF_COUNTRIES = {
    "china": "Section 301 tariffs (up to 145%) — supply chain risk",
    "russia": "Comprehensive sanctions — avoid",
    "north korea": "Full embargo",
    "iran": "Comprehensive sanctions",
    "belarus": "Significant sanctions",
    "myanmar": "Import restrictions",
    "cuba": "US embargo",
    "venezuela": "Targeted sanctions",
}

# Countries with MODERATE risk (flag but don't auto-reject)
MODERATE_RISK_COUNTRIES = {
    "india": "Occasional FDA import alerts; verify GMP certification",
    "vietnam": "Some tariff exposure; verify supplier",
    "indonesia": "Monitor for new tariff orders",
    "bangladesh": "Labor/quality concerns; verify",
}


def build_restricted_set() -> dict:
    """
    Combines hardcoded list with any downloaded FDA data.
    Returns structured dict for serialization.
    """
    return {
        "restricted_ingredients": sorted(FDA_RESTRICTED_INGREDIENTS),
        "high_tariff_countries":  HIGH_TARIFF_COUNTRIES,
        "moderate_risk_countries": MODERATE_RISK_COUNTRIES,
        "last_updated": datetime.now(timezone.utc).isoformat(),
        "sources": list(FDA_SOURCES.keys()),
    }


def refresh_fda_data() -> dict:
    """
    Attempt to fetch live FDA data; fall back to hardcoded list.
    Always writes fda_restricted.json to raw_cache.
    """
    print("[FDA] Refreshing FDA restriction data...")

    data = build_restricted_set()

    # Attempt live fetch (best-effort — FDA pages are inconsistent)
    try:
        with httpx.Client(timeout=15, follow_redirects=True) as client:
            # FDA tainted supplements list
            resp = client.get(
                "https://www.accessdata.fda.gov/scripts/sda/sdNavigation.cfm"
                "?sd=tainted_supplements_cder&displayAll=true&page=1",
                headers={"Accept": "application/json, text/html"},
            )
            if resp.status_code == 200 and "json" in resp.headers.get("content-type", ""):
                fda_json = resp.json()
                # Extract ingredient names from FDA tainted products
                extra_terms = set()
                for item in fda_json.get("data", []):
                    ingr = item.get("Ingredient", "")
                    if ingr:
                        extra_terms.add(ingr.lower().strip())
                data["restricted_ingredients"] = sorted(
                    set(data["restricted_ingredients"]) | extra_terms
                )
                print(f"[FDA] Live fetch succeeded. Total restricted: {len(data['restricted_ingredients'])}")
    except Exception as e:
        print(f"[FDA] Live fetch failed (using hardcoded list): {e}")

    # Save to cache
    with open(FDA_CACHE_PATH, "w") as f:
        json.dump(data, f, indent=2)
    print(f"[FDA] Saved → {FDA_CACHE_PATH}")

    return data


def load_fda_data() -> dict:
    """Load from cache if available, otherwise refresh."""
    if FDA_CACHE_PATH.exists():
        with open(FDA_CACHE_PATH) as f:
            return json.load(f)
    return refresh_fda_data()


def is_fda_safe(ingredients: list[str]) -> tuple[bool, list[str]]:
    """
    Returns (is_safe: bool, flagged_ingredients: list[str]).
    Call this from P2 compliance filtering.
    """
    data = load_fda_data()
    restricted = set(data.get("restricted_ingredients", []))

    flagged = []
    for ingredient in ingredients:
        norm = ingredient.lower().strip()
        # Exact match
        if norm in restricted:
            flagged.append(ingredient)
            continue
        # Substring match (e.g. "ephedra extract" → "ephedra")
        for r in restricted:
            if r in norm or norm in r:
                flagged.append(ingredient)
                break

    return (len(flagged) == 0, flagged)


def check_country_risk(country: Optional[str]) -> tuple[str, str]:
    """
    Returns (risk_level: "high"|"moderate"|"low", reason: str).
    """
    if not country:
        return ("low", "Country not specified")

    country_lower = country.lower().strip()
    data = load_fda_data()

    high_risk = data.get("high_tariff_countries", {})
    mod_risk   = data.get("moderate_risk_countries", {})

    for c, reason in high_risk.items():
        if c in country_lower or country_lower in c:
            return ("high", reason)

    for c, reason in mod_risk.items():
        if c in country_lower or country_lower in c:
            return ("moderate", reason)

    return ("low", "No known restrictions")


async def run_compliance_check_all():
    """
    Run FDA + country checks on all products in DB.
    Writes compliance_flags rows.
    """
    refresh_fda_data()
    print("[FDA] Running compliance checks on all products...")

    async with AsyncSessionLocal() as session:
        result = await session.execute(select(Product))
        products = result.scalars().all()
        print(f"[FDA] Checking {len(products)} products...")

        flags_added = 0
        for product in products:
            # 1. FDA ingredient check
            ingredients = product.ingredients or []
            safe, flagged_ingr = is_fda_safe(ingredients)
            flag = ComplianceFlag(
                product_id = product.id,
                rule       = "fda_ingredient_check",
                passed     = safe,
                note       = f"Flagged: {flagged_ingr}" if flagged_ingr else "All clear",
            )
            session.add(flag)
            flags_added += 1

            # 2. Shelf life check
            shelf_ok = (product.shelf_life_months or 0) >= 12
            flag2 = ComplianceFlag(
                product_id = product.id,
                rule       = "shelf_life_12mo",
                passed     = shelf_ok,
                note       = f"Shelf life: {product.shelf_life_months} months"
                             if product.shelf_life_months else "Shelf life unknown",
            )
            session.add(flag2)
            flags_added += 1

            # 3. Country risk
            risk_level, reason = check_country_risk(product.country_of_origin)
            flag3 = ComplianceFlag(
                product_id = product.id,
                rule       = "country_tariff_risk",
                passed     = risk_level == "low",
                note       = f"{risk_level.upper()}: {reason}",
            )
            session.add(flag3)
            flags_added += 1

        await session.commit()
        print(f"[FDA] ✅ Added {flags_added} compliance flag rows.")


if __name__ == "__main__":
    # Refresh list + run compliance on all existing products
    asyncio.run(run_compliance_check_all())
