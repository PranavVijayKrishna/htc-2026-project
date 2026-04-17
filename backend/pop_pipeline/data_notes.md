# data_notes.md — What Each Source Measures
*For judges' Q&A and team reference*

---

## 1. Google Trends (`source = "google_trends"`)

**What it measures:** Relative search interest (0–100 scale) for a keyword in the US over the past 90 days. 100 = peak popularity in the period; 50 = half of peak.

**Why it matters for PoP:** Search volume is the best proxy for *consumer demand that hasn't yet been filled* — people searching for "ashwagandha gummies" before they're widely stocked is a buying signal.

**Signal score formula:**
- `raw_signal_score` = average interest over 90 days (0–100)
- `growth_rate` = (mean of last 14 days − mean of prior 14 days) / prior 14 days × 100

**Limitations:**
- Normalized within each batch — compare terms from the same batch only
- Doesn't distinguish between brand searches and category searches
- Lags ~1–3 days behind real-world events

**Refresh cadence:** Every 6 hours (or on `/api/admin/refresh`)

---

## 2. Reddit (`source = "reddit"`)

**What it measures:** Post count + engagement (upvotes + 2× comments) for a term across 7 wellness subreddits in the last 30 days.

**Why it matters for PoP:** Reddit discussions often *precede* mainstream Google search spikes by 2–6 weeks. Early adopters and supplement enthusiasts live here. If r/Nootropics is buzzing about urolithin A before it's on Amazon's front page, that's the signal PoP needs.

**Subreddits monitored:**
| Subreddit | Focus |
|-----------|-------|
| r/Supplements | General supplements, vitamins |
| r/Nootropics | Cognitive enhancers, adaptogens |
| r/HerbalMedicine | Traditional + herbal remedies |
| r/HealthyFood | Clean eating, functional foods |
| r/Kombucha | Fermented + probiotic beverages |
| r/nutrition | Mainstream nutrition trends |
| r/herbalism | Traditional herbalism |

**Signal score formula:**
- `raw_signal_score` = (mention_count / max_mentions × 50) + (total_engagement / max_engagement × 50)

**Limitations:**
- Subreddit removal policies can affect counts
- Some terms may be too niche for any Reddit hits
- PRAW read-only API; no authentication required beyond app credentials

---

## 3. Amazon Bestsellers (`source = "amazon"`)

**What it measures:** Current bestseller rank (1–50) in 6 product category pages. Lower rank = higher sales velocity.

**Why it matters for PoP:** Amazon rank is *commercial validation* — it shows what's actually selling, not just being searched. Rising rank = growing demand. Rank delta (previous rank − current rank) > 10 = fast mover.

**Categories scraped:**
| Category | PoP Mapping |
|----------|-------------|
| Health → Vitamins & Supplements | Vitamins & Supplements |
| Grocery → Herbal Teas | Herbal Teas |
| Grocery → Health Foods | Health Snacks |
| Sports → Protein Bars | Health Snacks |
| Health → Pain Relievers | Personal Care |
| Grocery → Kombucha | Functional Beverages |

**Key fields:**
- `amazon_rank` = current rank
- `amazon_rank_prev` = rank on last pipeline run
- `rank_delta` = prev − current (positive = rising)

**Limitations:**
- Amazon HTML structure changes frequently; scraper may need adjustment
- Does not include sales volume (Amazon doesn't publish this)
- Country of origin and ingredients require fetching individual product pages (out of scope for MVP)

---

## 4. FDA Compliance (`source = "fda"`)

**What it measures:** Whether a product's ingredients appear on FDA restriction/warning lists, and whether the product's country of origin carries tariff risk.

**Rules checked per product:**

| Rule | Pass Condition | PoP Requirement |
|------|---------------|-----------------|
| `fda_ingredient_check` | No ingredient matches restricted list | Required |
| `shelf_life_12mo` | shelf_life_months ≥ 12 | Required |
| `country_tariff_risk` | Country not in high-risk list | Flagged (not auto-rejected) |

**High tariff countries (auto-flag):** China, Russia, North Korea, Iran, Belarus, Myanmar, Cuba, Venezuela

**Moderate risk countries (warn):** India, Vietnam, Indonesia, Bangladesh

**Data source:** FDA tainted supplements database (live fetch) + hardcoded industry knowledge list.

**Limitations:**
- Shelf life and ingredients are often not available from Amazon scraping; defaults to "unknown"
- FDA list is advisory — buyers should verify against current FDA.gov
- Country of origin is inferred; not always accurate from product page alone

---

## Composite Score Formula

```
composite_score = (
    0.40 × google_signal_normalized +
    0.30 × reddit_signal_normalized +
    0.20 × growth_rate_normalized   +
    0.10 × amazon_signal            # placeholder; not yet fully wired
)
```

All sub-scores are normalized to 0–100 before weighting.

**Interpretation:**
- 80–100: Strong multi-source signal → high-priority investigation
- 60–79:  Clear trend → recommend buyer review
- 40–59:  Emerging signal → monitor
- < 40:   Weak signal → low priority

---

## Known Good Demo Terms (hand-curated)

These terms reliably show real signal across sources for demo purposes:

1. `ashwagandha` — consistent top-10 Google Trends + Reddit
2. `lion's mane` — fast-growing nootropic category
3. `sea moss` — viral on social (TikTok → Reddit → Google)
4. `berberine` — "Nature's Ozempic" search spike 2023–2025
5. `matcha` — stable high-volume tea trend
6. `kombucha` — validated on both Reddit and Amazon
7. `collagen peptides` — strong Amazon bestseller movement
8. `mushroom coffee` — new category, fast growth
9. `nmn supplement` — longevity trend accelerating
10. `ginger shot` — close to PoP's core product line
