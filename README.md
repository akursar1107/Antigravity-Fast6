# 🏈 Fast6 — NFL First TD Prediction Platform

Full-stack web app for managing **first touchdown scorer predictions** across a friend group. Next.js dashboard backed by a FastAPI REST API, with NFL play-by-play integration, auto-grading, and advanced analytics.

## Quick Start

### Prerequisites

| Component | Version |
|-----------|---------|
| Node.js   | 18+     |
| Python    | 3.10+   |

### 1. Backend (FastAPI)

```bash
cd Fast6
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# Start API server
uvicorn src.api.fastapi_app:app --reload --port 8000
```

Backend runs at **http://localhost:8000** — interactive docs at `/docs`.

### 2. Frontend (Next.js)

```bash
cd Fast6/web
npm install
cp .env.local.example .env.local   # then edit if needed

npm run dev
```

Frontend runs at **http://localhost:3000**.

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `NEXT_PUBLIC_API_BASE_URL` | `http://localhost:8000` | FastAPI backend URL |
| `NEXT_PUBLIC_CURRENT_SEASON` | `2025` | Active NFL season |
| `NEXT_PUBLIC_TEST_USERNAME` | — | Dev-mode auto-login user |

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
├── src/                          # Python backend
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
│   ├── config.py                 # JSON config loader
│   ├── config.json               # App settings
│   └── utils/                    # NFL data, grading, odds
├── tests/                        # Python test suite
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
cd Fast6 && python -m pytest tests/ -v
```

## Deployment

### Docker

```bash
docker build -t fast6 .
docker run -d -p 8000:8000 -v $(pwd)/data:/app/data fast6
```

### Railway (Recommended)

1. Push to GitHub
2. Connect repo at [railway.app](https://railway.app)
3. Railway auto-detects the Dockerfile and deploys

### Vercel (Frontend only)

```bash
cd web && npx vercel
```

Set `NEXT_PUBLIC_API_BASE_URL` to your deployed backend URL.

## Contributing

Open issues and pull requests welcome.

## License

MIT
