# PoP Intelligence — AI Product Discovery & Trend Intelligence

> Built at **Hack the Coast 2026** for **Prince of Peace (PoP)** CPG  
> A full-stack AI tool that surfaces trending health & wellness products for PoP buyers to source or develop.

---

## What It Does

Prince of Peace is a CPG distributor (ginger, ginseng, herbal teas, wellness supplements). Buyers need to know what consumers are searching for *right now* and whether PoP should **distribute** an existing product or **develop** a new product line.

PoP Intelligence scrapes live signals from Google Trends, iHerb, and Amazon, scores each opportunity with a weighted AI engine, and surfaces them in a ranked dashboard with:
- Color-coded score breakdowns
- AI-generated sourcing rationale (via Groq / Llama 3.3)
- A per-card "Dive Deeper" chatbot with live web search
- Live weight tuning (shift scoring weights mid-demo, rankings re-order instantly)

---

## Architecture

```
htc-2026-project/
├── app/                        # Next.js 16 frontend (App Router)
│   ├── page.tsx                # Landing page
│   ├── dashboard/page.tsx      # Opportunity dashboard
│   ├── globals.css             # Tailwind + animations
│   └── layout.tsx
│
└── backend/
    └── pop_pipeline/           # FastAPI backend (deployed on Render)
        ├── api/
        │   └── main.py         # All API routes
        ├── collectors/
        │   ├── google_trends.py
        │   ├── amazon.py
        │   ├── iherb.py
        │   └── fda.py
        ├── pipeline/
        │   ├── runner.py       # Orchestrates all collectors
        │   └── scorer.py       # Ingest-time composite scoring
        ├── db/
        │   ├── models.py       # SQLAlchemy models
        │   └── session.py      # Async DB session
        └── utils/
            └── seed_terms.py   # PoP-relevant seed keywords
```

---

## Tech Stack

| Layer | Tech |
|---|---|
| Frontend | Next.js 16, React 19, Tailwind CSS v4, TypeScript |
| Backend | FastAPI, SQLAlchemy (async), Alembic |
| Database | PostgreSQL (Neon serverless) |
| AI / LLM | Groq API — Llama 3.3 70B |
| Web Search | DuckDuckGo Search (real-time sourcing links) |
| Data Sources | Google Trends (pytrends), iHerb scraper, Amazon scraper, FDA API |
| Deployment | Render (backend), Vercel (frontend) |

---

## Scoring Engine

Every trend is scored on-the-fly at request time so that live weight tuning re-orders results instantly.

```
composite = (
  0.40 × growth_rate        # week-over-week search momentum
  0.30 × pop_relevance      # match to PoP's ingredient/category taxonomy
  0.10 × competition_gap    # fewer competing products = bigger gap
  0.05 × cross_signal       # term seen across multiple sources
  0.15 × recency            # always 1.0 — guaranteed floor contribution
)

display_score = min(10.0, composite × 12)
```

**Develop vs. Distribute logic:** if the trending term matches a PoP core ingredient (ginger, ginseng, reishi, etc.), the action is `develop` (extend existing line). Otherwise it's `distribute` (source from a supplier).

---

## API Endpoints

Base URL: `https://htc-2026-project.onrender.com`

| Method | Path | Description |
|---|---|---|
| `GET` | `/` | Health check |
| `GET` | `/api/recommendations` | Top scored opportunities (main dashboard feed) |
| `GET` | `/api/trends` | Raw trend rows with filters |
| `GET` | `/api/products` | Scraped products with compliance flags |
| `GET` | `/api/admin/weights` | Read current scoring weights |
| `POST` | `/api/admin/weights` | Update weights live (requires `X-Admin-Secret` header) |
| `POST` | `/api/admin/refresh` | Trigger full pipeline re-run in background |
| `GET` | `/api/pipeline/status` | Poll pipeline run status |
| `POST` | `/api/chat` | Dive Deeper chatbot with DuckDuckGo grounding |

### Query params — `/api/recommendations`

| Param | Default | Description |
|---|---|---|
| `category` | — | Filter by category name |
| `angle` | — | `distribute` or `develop` |
| `min_score` | `0.0` | Minimum display score (0–10) |
| `limit` | `20` | Max results (1–100) |

---

## Database Schema

| Table | Purpose |
|---|---|
| `trends` | One row per term/source. Stores raw signal score, growth rate, meta JSON with sub-scores. |
| `products` | Scraped product listings from Amazon and iHerb. Linked to trends. |
| `categories` | PoP taxonomy mapping (Ginseng, Teas, Snacks, Health & Wellness, etc.) |
| `compliance_flags` | Audit log of FDA/shelf-life filter results per product. |

---

## Local Development

### Backend

```bash
cd backend/pop_pipeline

# Install dependencies
pip install -r requirements.txt

# Set up environment
cp .env.example .env
# Fill in DATABASE_URL, GROQ_API_KEY, ADMIN_SECRET

# Run the API
uvicorn api.main:app --reload --port 8000
```

Trigger a pipeline run:
```bash
curl -X POST http://localhost:8000/api/admin/refresh \
  -H "X-Admin-Secret: changeme_hackathon_2026"
```

Run a single collector:
```bash
python -m pipeline.runner --source google
```

### Frontend

```bash
# From project root
npm install
npm run dev
# Opens at http://localhost:3000
```

---

## Environment Variables

Create `backend/pop_pipeline/.env`:

```env
# PostgreSQL (Neon or Supabase)
DATABASE_URL=postgresql+asyncpg://user:password@host:5432/dbname
DATABASE_SYNC_URL=postgresql+psycopg2://user:password@host:5432/dbname

# Groq (LLM rationale + chatbot)
GROQ_API_KEY=gsk_...

# Admin route protection
ADMIN_SECRET=changeme_hackathon_2026
```

---

## Deployment

**Backend → Render**

Configured via `backend/render.yaml`:
```yaml
buildCommand: pip install -r requirements.txt && pip install -r pop_pipeline/requirements.txt
startCommand: cd pop_pipeline && uvicorn api.main:app --host 0.0.0.0 --port $PORT
```

Set all env vars in the Render dashboard under Environment.

**Frontend → Vercel**

```bash
vercel --prod
```

Update `API_URL` and `CHAT_URL` constants in `app/dashboard/page.tsx` to point to your Render backend URL.

---

## Demo Flow

1. Open the landing page — hero, stats, how-it-works sections
2. Click **View Opportunities** → dashboard loads skeleton cards → real data appears
3. Each card shows: term name, amber score badge, 4 color-coded score bars, growth / confidence / action / PoP line meta grid
4. Click a card → detail view with score breakdown + LLM rationale bullets
5. Click **Dive Deeper** → chatbot with live DuckDuckGo-sourced supplier links
6. Admin demo: `POST /api/admin/weights` to shift weights → scores re-rank in real time

---

## Team

Built at **Hack the Coast 2026** — 48-hour hackathon.

| Role | Responsibilities |
|---|---|
| Person 1 | Data collection — Google Trends, Amazon, iHerb scrapers |
| Person 2 | Compliance & filters — FDA rules, shelf life, origin flags |
| Person 3 | Scoring engine, LLM rationale, API, frontend dashboard |
| Person 4 | UI/UX, weight tuning demo, presentation |

---

## License

Prince of Peace brand used for demonstration only.
