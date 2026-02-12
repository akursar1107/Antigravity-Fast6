# 🏈 Fast6 — NFL First TD Prediction Platform

Full-stack web app for managing **first touchdown scorer predictions** across a friend group. Next.js dashboard backed by a FastAPI REST API, with NFL play-by-play integration, auto-grading, and advanced analytics.

## Quick Start

### Prerequisites

| Component | Version |
|-----------|---------|
| Node.js   | 18+     |
| Python    | 3.10+   |

### 1. Backend (FastAPI)

From the project root (directory containing `backend/`, `web/`, `requirements.txt`):

```bash
cd <project-root>
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# Start API server
uvicorn backend.api.fastapi_app:app --reload --port 8000
```

Backend runs at **http://localhost:8000** — interactive docs at `/docs`.

### 2. Frontend (Next.js)

```bash
cd web
npm install
cp .env.example .env.local   # then edit if needed

npm run dev
```

Frontend runs at **http://localhost:3000**.

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `NEXT_PUBLIC_API_BASE_URL` | `http://127.0.0.1:8000` | FastAPI backend URL |
| `NEXT_PUBLIC_APP_URL` | `http://localhost:3000` | Public app URL |
| `NEXT_PUBLIC_CURRENT_SEASON` | `2025` | Active NFL season |
| `NEXT_PUBLIC_TEST_USERNAME` | — | Dev-mode auto-login user |

Backend: `.env.example` (copy to `.env`) documents `SECRET_KEY`, `CORS_ORIGINS`, `DATABASE_PATH`, etc.

### 3. Populate sample data (optional)

If the site shows "No data yet" or empty leaderboards, seed the database:

```bash
cd <project-root>
source .venv/bin/activate
python -m backend.scripts.seed_all
```

This creates users (Phil, Alice, Bob), weeks, games, picks, and graded results. The frontend uses `NEXT_PUBLIC_TEST_USERNAME` (default: Phil) for dev-mode auth—ensure that user exists.

## Features

### Public Dashboard
- **Overview** — season stats, top performer, leaderboard snapshot
- **Leaderboard** — full standings with points, ROI, win %, correct picks
- **Analytics** — ROI trends chart, player performance table
- **Week Picks** — per-week picks table with grading status
- **Matchup Analysis** — head-to-head team stats for any game
- **About** — scoring rules and platform info

### Admin Panel (`/admin`)
- **Dashboard** — system KPIs (users, picks, grading progress)
- **Users** — create / delete members
- **Picks** — browse all picks by week
- **Grading** — grading progress bar, batch-grade via API

### API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/api/auth/login` | Get JWT token |
| `GET` | `/api/leaderboard/season/{season}` | Season standings |
| `GET` | `/api/leaderboard/week/{week_id}` | Weekly standings |
| `GET/POST` | `/api/picks` | List / create picks |
| `GET/POST` | `/api/results` | List / create results |
| `GET` | `/api/results/ungraded/list` | Ungraded picks (admin) |
| `GET` | `/api/analytics/roi-trends` | ROI by week |
| `GET` | `/api/analytics/player-stats` | Player TD stats |
| `GET` | `/api/analytics/grading-status` | Grading progress |
| `GET` | `/api/analytics/matchup/{game_id}` | Matchup breakdown |
| `GET` | `/api/admin/stats` | System stats (admin) |
| `POST` | `/api/admin/csv-import` | Bulk CSV import (admin) |

Full interactive docs: **http://localhost:8000/docs**

### Security & Auth

**Intended for private use:** Fast6 uses **username-only authentication** (no password). This is suitable for a trusted friend group sharing one device or a private network. Do **not** expose this app to the public internet without adding password auth or OAuth.

- Login is rate-limited (5 requests/minute)
- JWT tokens expire after 30 days; set `SECRET_KEY` to a secure value in production
- See `.env.example` for `SECRET_KEY`, `CORS_ORIGINS`, and other deployment settings

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | Next.js 16, React 19, TypeScript, Tailwind v4, Recharts |
| Backend | FastAPI, Uvicorn, Pydantic, python-jose (JWT) |
| Database | SQLite (WAL mode, foreign keys enforced) |
| NFL Data | nflreadpy, pandas |
| Testing | Vitest + React Testing Library (38 tests), pytest |

## Project Structure

```
Fast6/
├── web/                          # Next.js frontend
│   ├── src/app/                  # App Router pages
│   │   ├── page.tsx              # Overview dashboard
│   │   ├── leaderboard/          # Leaderboard page
│   │   ├── analytics/            # ROI + player stats
│   │   ├── weeks/[weekId]/       # Per-week picks
│   │   ├── matchups/[gameId]/    # Matchup analysis
│   │   ├── about/                # About page
│   │   └── admin/                # Admin section
│   │       ├── page.tsx          # Admin dashboard
│   │       ├── users/            # User management
│   │       ├── picks/            # Picks browser
│   │       └── grading/          # Grading progress
│   ├── src/components/           # Shared UI components
│   ├── src/lib/                  # API client, cache, auth
│   └── package.json
├── backend/                      # Python backend
│   ├── api/                      # FastAPI application
│   │   ├── fastapi_app.py        # App entry + lifespan
│   │   ├── fastapi_config.py     # Settings (pydantic-settings)
│   │   ├── fastapi_models.py     # Request/response schemas
│   │   ├── fastapi_security.py   # JWT utilities
│   │   ├── fastapi_dependencies.py # DB + auth dependencies
│   │   └── routers/              # Route handlers
│   ├── database/                 # SQLite layer (repository pattern)
│   │   ├── connection.py         # Connection management
│   │   └── migrations.py         # Versioned schema migrations
│   ├── config/                   # App configuration
│   │   ├── config.py             # JSON config loader
│   │   └── config.json           # Teams, scoring, theme, features
│   └── services/                 # Analytics, grading, sync
├── backend/tests/                # Python test suite
├── data/                         # SQLite database (gitignored)
├── Dockerfile                    # Production container
├── requirements.txt              # Python dependencies
└── README.md
```

## Testing

```bash
# Frontend (38 tests)
cd web && npm test

# Backend
cd <project-root> && python -m pytest backend/tests/ -v
```

## Deployment

### Docker (Backend Only)

The Dockerfile builds both frontend and backend, but **runs FastAPI only**.
The Next.js app is built but not served in the container.

```bash
docker build -t fast6 .
docker run -d -p 8000:8000 -v $(pwd)/data:/app/data fast6
```

- Mount a volume at `/app/data` for persistent SQLite storage
- Set `DATABASE_PATH=/app/data/fast6.db` and `SECRET_KEY` via `-e` if needed
- Deploy the frontend separately (Vercel, Railway) and set `NEXT_PUBLIC_API_BASE_URL` to this backend's URL
- See `docs/plans/NEXTJS_DEPLOYMENT.md`

### Railway (Backend)

1. Push to GitHub and connect repo at [railway.app](https://railway.app)
2. Railway auto-detects the Dockerfile (see `railway.json`) and deploys
3. **Required env vars** in Railway dashboard:
   - `DATABASE_PATH` — `/app/data/fast6.db` (or path to mounted volume)
   - `SECRET_KEY` — secure random string (e.g. `openssl rand -hex 32`)
   - `CORS_ORIGINS` — comma-separated frontend URLs (e.g. `https://your-app.vercel.app`)
4. Add a **volume** mounted at `/app/data` for persistent SQLite data

### Vercel (Frontend)

```bash
cd web && npx vercel
```

Set `NEXT_PUBLIC_API_BASE_URL` to your deployed backend URL (Railway, Docker host, etc.).

## Contributing

Open issues and pull requests welcome.

## License

MIT
