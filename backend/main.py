from fastapi import FastAPI
from scoring import score_opportunity
import psycopg2
import os

app = FastAPI()

def get_db_connection():
    return psycopg2.connect(os.environ.get("DATABASE_URL").replace("postgresql+asyncpg://", "postgresql://"))

@app.get("/")
def root():
    return {"msg": "backend working"}

@app.get("/api/test-score")
def test_score():
    kombucha = score_opportunity(term="kombucha", growth=0.8, cross_signal=1.0, competition_gap=0.6, recency=0.9)
    sea_moss = score_opportunity(term="sea moss", growth=0.7, cross_signal=0.5, competition_gap=0.8, recency=0.8)
    lions_mane = score_opportunity(term="lion's mane", growth=0.9, cross_signal=1.0, competition_gap=0.7, recency=1.0)
    return {"kombucha": kombucha, "sea_moss": sea_moss, "lions_mane": lions_mane}

@app.get("/api/recommendations")
def get_recommendations(
    category: str = None,
    angle: str = None,
    min_score: float = 0.0
):
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        cur.execute("""
            SELECT term, growth_rate, raw_signal_score, source_confidence
            FROM trends
        """)
        rows = cur.fetchall()
        cur.close()
        conn.close()

        results = []
        for row in rows:
            term, growth_rate, raw_signal_score, source_confidence = row

            # Normalize growth_rate from percentage to 0-1 (cap at 100%)
            growth = min(float(growth_rate) / 100.0, 1.0)
            growth = max(growth, 0.0)  # handle negative growth

            # Normalize raw_signal_score to 0-1
            recency = float(raw_signal_score) / 100.0

            # Use source_confidence as cross_signal
            cross_signal = float(source_confidence)

            # competition_gap — default 0.5 until P1 adds that data
            competition_gap = 0.5

            scored = score_opportunity(
                term=term,
                growth=growth,
                cross_signal=cross_signal,
                competition_gap=competition_gap,
                recency=recency
            )
            results.append(scored)

    except Exception as e:
        # Fallback to mock data if DB fails
        mock_trends = [
            {"term": "lion's mane", "growth": 0.9, "cross_signal": 1.0, "competition_gap": 0.7, "recency": 1.0},
            {"term": "kombucha", "growth": 0.8, "cross_signal": 1.0, "competition_gap": 0.6, "recency": 0.9},
            {"term": "ashwagandha", "growth": 0.75, "cross_signal": 1.0, "competition_gap": 0.5, "recency": 0.7},
        ]
        results = [score_opportunity(**t) for t in mock_trends]

    # Filter by category
    if category:
        results = [r for r in results if r["category"] == category]

    # Filter by angle
    if angle:
        results = [r for r in results if r["angle"] == angle]

    # Filter by min score
    results = [r for r in results if r["score"] >= min_score]

    # Sort by score descending
    results.sort(key=lambda x: x["score"], reverse=True)

    return {"results": results, "count": len(results)}