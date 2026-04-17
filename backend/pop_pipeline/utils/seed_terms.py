"""
utils/seed_terms.py
Master list of ~60 ingredient / product terms fed into every collector.
P1 curated list — maps to PoP's core categories.
"""

SEED_TERMS = [
    # ── Adaptogens / Mushrooms ──────────────────────────────
    "ashwagandha",
    "rhodiola rosea",
    "lion's mane mushroom",
    "reishi mushroom",
    "cordyceps",
    "maca root",
    "holy basil tulsi",
    "eleuthero",
    "schisandra berry",

    # ── Ginseng (PoP core) ──────────────────────────────────
    "ginseng",
    "korean red ginseng",
    "american ginseng",
    "panax ginseng",

    # ── Ginger (PoP core) ──────────────────────────────────
    "ginger chew",
    "ginger candy",
    "crystallized ginger",
    "ginger shot",
    "ginger supplement",

    # ── Herbal Teas ─────────────────────────────────────────
    "matcha",
    "rooibos tea",
    "hibiscus tea",
    "chamomile tea",
    "turmeric tea",
    "mushroom tea",
    "elderberry tea",

    # ── Functional Beverages ────────────────────────────────
    "kombucha",
    "water kefir",
    "prebiotic soda",
    "mushroom coffee",
    "adaptogen drink",
    "collagen drink",
    "nootropic drink",
    "electrolyte powder",

    # ── Superfoods ──────────────────────────────────────────
    "sea moss gel",
    "black seed oil",
    "moringa powder",
    "spirulina powder",
    "chlorella",
    "baobab powder",
    "wheatgrass powder",
    "bee pollen",

    # ── Supplements ─────────────────────────────────────────
    "berberine",
    "nmn supplement",
    "nad+ supplement",
    "collagen peptides",
    "magnesium glycinate",
    "quercetin supplement",
    "spermidine",
    "urolithin a",

    # ── Snacks / Confections ────────────────────────────────
    "seaweed snack",
    "protein bar",
    "manuka honey",
    "herbal candy",
    "throat lozenge",
    "dark chocolate supplement",

    # ── Personal Care ───────────────────────────────────────
    "tiger balm",
    "arnica gel",
    "topical magnesium",
    "cbd pain relief",
    "muscle rub",
    "pain relief patch",
]

# Terms that strongly signal PoP product development opportunities
DEVELOPMENT_SIGNAL_TERMS = [
    "kombucha ginger",
    "ginseng adaptogen",
    "ginger turmeric",
    "mushroom ginseng",
    "probiotic ginger",
    "adaptogen candy",
    "functional ginger chew",
]
