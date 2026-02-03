# Next.js Frontend (Phase 3) — Design

## Summary
Build a public, dark-mode analytics dashboard in Next.js (App Router, TypeScript). The app reads from the FastAPI endpoints and mirrors key Streamlit tabs without authentication. It favors clarity, fast iteration, and a clean data layer.

## Goals
- Provide a modern public dashboard for Fast6 data.
- Reuse existing FastAPI endpoints without changes.
- Keep the UI fast, responsive, and readable on mobile.
- Minimize backend coupling by using a thin client-side API wrapper.

## Non-Goals
- No authentication or admin tools in v1.
- No server-side caching or SSR data fetching.
- No feature parity with every Streamlit tab.

## Scope (v1)
Pages:
- `/` — Overview with summary stats and latest week highlight.
- `/leaderboard` — Season leaderboard.
- `/weeks/[weekId]` — Weekly picks and week leaderboard snapshot.
- `/analytics` — ROI trends, odds accuracy, player stats, defense stats.
- `/matchups/[gameId]` — Matchup analytics for a single game.
- `/about` — Data sources and project notes.

## API Integration
Base URL: `NEXT_PUBLIC_API_BASE_URL` (default `http://localhost:8000`).

Endpoints used:
- Leaderboard
  - `GET /api/leaderboard/season/{season}`
  - `GET /api/leaderboard/week/{week_id}`
  - `GET /api/leaderboard/season/{season}/stats`
- Analytics
  - `GET /api/analytics/roi-trends`
  - `GET /api/analytics/odds-accuracy`
  - `GET /api/analytics/player-stats`
  - `GET /api/analytics/team-defense`
  - `GET /api/analytics/matchup/{game_id}`
  - `GET /api/analytics/grading-status`
- Weeks and picks
  - `GET /api/weeks`
  - `GET /api/weeks/{week_id}`
  - `GET /api/picks?week_id={id}`

## Data Layer
Create `src/lib/api.ts` with typed helpers:
- `getLeaderboard(season)`
- `getWeekLeaderboard(weekId)`
- `getRoiTrends(season)`
- `getOddsAccuracy(season)`
- `getPlayerStats(season, limit)`
- `getDefenseStats(season)`
- `getMatchup(gameId)`

Use a shared `request()` wrapper with:
- base URL prefix
- 8s timeout
- one retry on 5xx
- normalized error shape: `{ ok: false, error: { message, status } }`

Client-side cache: in-memory `Map` with 60s TTL keyed by URL.

## UI and Layout
Style: dark analytics theme (charcoal background, neon accents). Use a consistent card system and compact tables.

Core components:
- `DashboardLayout` (nav, season selector, footer)
- `StatCard`, `ChartCard`, `Table`, `Badge`
- `Skeleton`, `EmptyState`, `ErrorBanner`

Charts:
- Line chart: ROI trends by week
- Bar chart: odds accuracy buckets
- Tables: leaderboard, player stats, defense stats

## Error Handling
- Show inline error banners with a retry button.
- Show empty state for missing data.
- Keep pages stable if one widget fails.

## Testing
- Unit tests for API helpers (mocked `fetch`).
- One integration test per major page to verify loading and error states.

## Accessibility
- Keyboard focus states for nav and buttons.
- High contrast for text and charts.
- Tables include headers and row labels.

## Deployment Notes
- Works on Vercel or Railway with `NEXT_PUBLIC_API_BASE_URL` set.
- No server-side secrets required.

## Open Questions
- None for v1. Add auth and admin later if needed.
