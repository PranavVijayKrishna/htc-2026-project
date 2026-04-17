from fastapi import FastAPI
from scoring import score_opportunity

app = FastAPI()

@app.get("/")
def root():
    return {"msg": "backend working"}

@app.get("/api/test-score")
def test_score():
    kombucha = score_opportunity(
        term="kombucha",
        growth=0.8,
        cross_signal=1.0,
        competition_gap=0.6,
        recency=0.9
    )
    sea_moss = score_opportunity(
        term="sea moss",
        growth=0.7,
        cross_signal=0.5,
        competition_gap=0.8,
        recency=0.8
    )
    lions_mane = score_opportunity(
        term="lion's mane",
        growth=0.9,
        cross_signal=1.0,
        competition_gap=0.7,
        recency=1.0
    )
    return {
        "kombucha": kombucha,
        "sea_moss": sea_moss,
        "lions_mane": lions_mane
    }