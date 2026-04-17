"""
utils/tagger.py
Maps a free-text term to a PoP category.
Strategy:
  1. Exact / substring keyword match against categories table.
  2. Fuzzy match (rapidfuzz) for typos / variants.
  3. Returns None if no match found (let P2 handle unknown).
"""
from rapidfuzz import fuzz, process
from typing import Optional


# ── Static fallback map (used before DB is available) ───────
_KEYWORD_MAP: dict[str, str] = {
    # teas
    "tea": "Herbal Teas", "matcha": "Herbal Teas", "rooibos": "Herbal Teas",
    "chamomile": "Herbal Teas", "hibiscus": "Herbal Teas", "oolong": "Herbal Teas",
    # adaptogens
    "ashwagandha": "Ginseng & Adaptogens", "rhodiola": "Ginseng & Adaptogens",
    "lion's mane": "Ginseng & Adaptogens", "reishi": "Ginseng & Adaptogens",
    "cordyceps": "Ginseng & Adaptogens", "maca": "Ginseng & Adaptogens",
    "adaptogen": "Ginseng & Adaptogens", "schisandra": "Ginseng & Adaptogens",
    # ginseng
    "ginseng": "Ginseng & Adaptogens", "panax": "Ginseng & Adaptogens",
    # ginger
    "ginger": "Ginger Products",
    # functional beverages
    "kombucha": "Functional Beverages", "kefir": "Functional Beverages",
    "probiotic drink": "Functional Beverages", "electrolyte": "Functional Beverages",
    "mushroom coffee": "Functional Beverages", "nootropic drink": "Functional Beverages",
    "prebiotic soda": "Functional Beverages", "collagen drink": "Functional Beverages",
    # superfoods
    "sea moss": "Superfoods", "spirulina": "Superfoods", "chlorella": "Superfoods",
    "moringa": "Superfoods", "wheatgrass": "Superfoods", "baobab": "Superfoods",
    "black seed": "Superfoods", "bee pollen": "Superfoods",
    # supplements
    "berberine": "Vitamins & Supplements", "nmn": "Vitamins & Supplements",
    "nad+": "Vitamins & Supplements", "collagen peptides": "Vitamins & Supplements",
    "magnesium": "Vitamins & Supplements", "quercetin": "Vitamins & Supplements",
    "spermidine": "Vitamins & Supplements", "urolithin": "Vitamins & Supplements",
    # snacks
    "seaweed snack": "Health Snacks", "protein bar": "Health Snacks",
    "granola": "Health Snacks", "trail mix": "Health Snacks",
    "manuka honey": "Confections", "honey": "Confections", "lozenge": "Confections",
    # personal care
    "tiger balm": "Personal Care", "muscle rub": "Personal Care",
    "arnica": "Personal Care", "cbd": "Personal Care", "pain relief": "Personal Care",
}

# All known category names (for fuzzy category-level matching)
_ALL_CATEGORIES = list(set(_KEYWORD_MAP.values()))


def tag_term(term: str) -> Optional[str]:
    """
    Returns a PoP category name for a given term, or None.
    """
    term_lower = term.lower()

    # 1. Substring / prefix keyword match
    for keyword, category in _KEYWORD_MAP.items():
        if keyword in term_lower:
            return category

    # 2. Fuzzy match against keyword list (handles typos like 'ashwaghanda')
    result = process.extractOne(
        term_lower,
        list(_KEYWORD_MAP.keys()),
        scorer=fuzz.partial_ratio,
        score_cutoff=82,
    )
    if result:
        matched_keyword = result[0]
        return _KEYWORD_MAP[matched_keyword]

    return None


def normalize_term(term: str) -> str:
    """
    Lowercase, strip, collapse whitespace.
    Handles common misspellings via a correction dict.
    """
    corrections = {
        "ashwaghanda": "ashwagandha",
        "ashwaganda": "ashwagandha",
        "reishi mushroom": "reishi",
        "lion's mane mushroom": "lion's mane",
        "lions mane": "lion's mane",
        "sea moss gel": "sea moss",
        "ginger chews": "ginger chew",
    }
    cleaned = " ".join(term.lower().strip().split())
    return corrections.get(cleaned, cleaned)
