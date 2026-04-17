# scoring.py - built from real PoP product catalog

POP_CORE_INGREDIENTS = [
    "ginger", "ginseng", "honey", "reishi", "mushroom",
    "herbal", "tea", "loquat", "ginseng extract"
]

POP_CATEGORIES = {
    "ginseng": [
        "ginseng", "american ginseng", "korean ginseng", "ginseng extract",
        "ginseng powder", "ginseng candy", "ginseng tea", "adaptogen",
        "ashwagandha", "eleuthero", "rhodiola"
    ],
    "teas": [
        "tea", "green tea", "black tea", "herbal tea", "chamomile",
        "peppermint", "hibiscus", "matcha", "kombucha", "oolong",
        "white tea", "rooibos", "loose leaf"
    ],
    "snacks": [
        "ginger chew", "ginger candy", "honey crystal", "wafer", "cracker",
        "gummy", "chew", "snack bar", "dried fruit", "fruit snack"
    ],
    "health & wellness": [
        "reishi", "mushroom", "probiotic", "prebiotic", "collagen",
        "sea moss", "elderberry", "turmeric", "lion's mane", "chaga",
        "adaptogens", "immune", "supplement", "vitamin", "fiber", "protein"
    ],
    "candy & confections": [
        "candy", "lozenge", "gummi", "chocolate", "biscuit", "cookie",
        "wafer", "shortbread", "mooncake", "loquat candy", "honey candy"
    ],
    "personal care": [
        "tiger balm", "balm", "ointment", "patch", "oil", "soap",
        "cream", "salve", "lotion", "yunnan baiyao", "kwan loong"
    ],
    "food & beverage": [
        "instant noodle", "cooking oil", "cornstarch", "soup", "beverage",
        "instant drink", "tea drink", "honey", "syrup", "sauce"
    ],
    "cookies & biscuits": [
        "cookie", "biscuit", "shortbread", "wafer", "danish", "butter cookie",
        "crackers", "petit beurre"
    ]
}

# High tariff / trade risk countries
HIGH_TARIFF_COUNTRIES = [
    "china", "russia", "iran", "north korea", "venezuela"
]

# Scoring weights
DEFAULT_WEIGHTS = {
    "growth": 0.35,
    "relevance": 0.25,
    "cross_signal": 0.20,
    "competition_gap": 0.15,
    "recency": 0.05
}


def get_relevance_score(term: str) -> tuple[float, str]:
    """Check how relevant a trending term is to PoP's real product categories."""
    term_lower = term.lower()

    for category, keywords in POP_CATEGORIES.items():
        for keyword in keywords:
            if keyword in term_lower or term_lower in keyword:
                return 1.0, category

    for category, keywords in POP_CATEGORIES.items():
        for keyword in keywords:
            if any(word in keyword for word in term_lower.split()):
                return 0.5, category

    return 0.0, "uncategorized"


def get_angle(term: str) -> tuple[str, str]:
    """Determine distribute vs develop based on PoP's real core lines."""
    term_lower = term.lower()

    # Direct match to PoP core ingredient = extend existing line
    for core in POP_CORE_INGREDIENTS:
        if core in term_lower or term_lower in core:
            return "develop", f"Extend existing PoP {core} product line with new format"

    # Trend is in a PoP-adjacent category — suggest a ginger or ginseng blend
    _, category = get_relevance_score(term)
    if category in ("teas", "health & wellness", "snacks", "food & beverage"):
        blend_core = "ginger" if any(w in term_lower for w in ("tea", "beverage", "drink")) else "ginseng"
        return "develop", f"Potential {term}-{blend_core} blend under PoP Wellness line"

    return "distribute", f"Source existing {term} product from compliant supplier"


def apply_tariff_penalty(country_of_origin: str) -> float:
    """Returns penalty based on trade risk of origin country."""
    if country_of_origin.lower() in HIGH_TARIFF_COUNTRIES:
        return 0.15
    return 0.0


def generate_rationale(
    term: str,
    category: str,
    growth: float,
    angle: str,
    suggestion: str
) -> str:
    """Generate plain-English rationale for a buyer — no jargon."""
    growth_pct = round(growth * 100)

    if angle == "develop":
        return (
            f"{term.title()} is growing {growth_pct}% week-over-week in the "
            f"{category} category. {suggestion}."
        )
    else:
        return (
            f"{term.title()} is growing {growth_pct}% week-over-week in the "
            f"{category} category. {suggestion} — review for sourcing feasibility."
        )


def score_opportunity(
    term: str,
    growth: float,
    cross_signal: float,
    competition_gap: float,
    recency: float,
    country_of_origin: str = "unknown",
    weights: dict = None
) -> dict:
    """Master scoring function. Returns full opportunity dict."""
    if weights is None:
        weights = DEFAULT_WEIGHTS

    relevance, category = get_relevance_score(term)

    final_score = (
        weights["growth"] * growth +
        weights["relevance"] * relevance +
        weights["cross_signal"] * cross_signal +
        weights["competition_gap"] * competition_gap +
        weights["recency"] * recency
    )

    angle, suggestion = get_angle(term)
    rationale = generate_rationale(term, category, growth, angle, suggestion)
    tariff_flagged = country_of_origin.lower() in HIGH_TARIFF_COUNTRIES

    return {
        "term": term,
        "score": round(final_score * 10, 2),
        "category": category,
        "angle": angle,
        "suggestion": suggestion,
        "rationale": rationale,
        "tariff_flagged": tariff_flagged,
        "country_of_origin": country_of_origin,
        "components": {
            "growth": round(growth, 2),
            "relevance": round(relevance, 2),
            "cross_signal": round(cross_signal, 2),
            "competition_gap": round(competition_gap, 2),
            "recency": round(recency, 2),
        }
    }