# PoP Trend Intelligence Pipeline — P1 Setup Guide

## Quick Start (Hour 0–1)

### 1. Install dependencies
```bash
cd pop_pipeline
pip install -r requirements.txt
```

### 2. Configure environment
```bash
cp .env.example .env
# Edit .env with your credentials:
#   DATABASE_URL       → Neon or Supabase connection string
#   REDDIT_CLIENT_ID   → from reddit.com/prefs/apps
#   REDDIT_CLIENT_SECRET
#   ADMIN_SECRET       → any secret string for the refresh endpoint
```

### 3. Get Reddit credentials (5 min)
1. Go to https://www.reddit.com/prefs/apps
2. Click "Create App" → type: **script**
3. Name: `pop_trend_bot`, redirect: `http://localhost`
4. Copy `client_id` (under app name) and `secret`

### 4. Initialize database
```bash
python -m db.init_db
```
This creates all 4 tables and seeds PoP categories.

### 5. Run the full pipeline
```bash
python -m pipeline.runner
```
Or run individual collectors:
```bash
python -m collectors.google_trends
python -m collectors.reddit
python -m collectors.amazon
python -m collectors.fda
```

### 6. Start the API server
```bash
uvicorn api.main:app --reload --port 8000
```

---

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/` | Health check |
| GET | `/api/trends` | All trends with scores |
| GET | `/api/products` | Amazon products with rank deltas |
| GET | `/api/recommendations` | Top opportunities for buyer dashboard |
| GET | `/api/pipeline/status` | Check if pipeline is running |
| POST | `/api/admin/refresh` | Trigger pipeline (needs `X-Admin-Secret` header) |

### Trigger a refresh (for P3 to call from dashboard):
```bash
curl -X POST "http://localhost:8000/api/admin/refresh" \
     -H "X-Admin-Secret: changeme_hackathon_2026"
```

### Trigger single source:
```bash
curl -X POST "http://localhost:8000/api/admin/refresh?source=google" \
     -H "X-Admin-Secret: changeme_hackathon_2026"
```

---

## Project Structure

```
pop_pipeline/
├── api/
│   └── main.py            # FastAPI app + all endpoints
├── collectors/
│   ├── google_trends.py   # Google Trends ingestion
│   ├── reddit.py          # Reddit PRAW ingestion
│   ├── amazon.py          # Amazon bestseller scraper
│   └── fda.py             # FDA compliance data loader
├── db/
│   ├── models.py          # SQLAlchemy ORM (4 tables)
│   ├── session.py         # Async session factory
│   └── init_db.py         # Table creation + category seed
├── pipeline/
│   ├── runner.py          # Orchestrates all collectors
│   └── scorer.py          # Composite score computation
├── utils/
│   ├── seed_terms.py      # ~60 seed ingredient/product terms
│   └── tagger.py          # Maps terms → PoP categories
├── raw_cache/             # All raw fetched data (auto-created)
├── data_notes.md          # Source documentation for judges
├── requirements.txt
└── .env.example
```

---

## Sharing with Team

Once your DB is up and pipeline has run once, share with team:

```
# In team Slack/Discord:
DATABASE_URL=<your neon/supabase url>
API_BASE=http://<your-server>:8000

# P2 (scoring/filtering): use GET /api/trends and the fda.py functions
# P3 (frontend): use GET /api/recommendations for the dashboard
```

## Deployment (Render)

1. Push to GitHub
2. New Web Service → connect repo → build command: `pip install -r requirements.txt`
3. Start command: `uvicorn api.main:app --host 0.0.0.0 --port 8000`
4. Add env vars in Render dashboard
5. Optional: Add Cron Job → `python -m pipeline.runner` every 6 hours
