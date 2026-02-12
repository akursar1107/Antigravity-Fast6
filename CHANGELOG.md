# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),

## [Unreleased]

### Added
- Performance Breakdown: multi-user comparison table (win rate, Brier, picks, streaks)
- `GET /api/analytics/performance-breakdown` endpoint
- Mobile UX: 44px touch targets on nav, bottom nav safe-area, content padding for fixed nav
- Design system: UX principles, mobile section, optimization opportunities
- CI/CD workflow (GitHub Actions) for backend and frontend tests
- Rate limiting on login endpoint (5 requests/minute)
- CHANGELOG.md and LICENSE
- Analytics tabbed interface (Overview | Performance | Touchdowns)
- Touchdowns table with view toggle (All touchdowns | First TD only) and week/team filters
- `GET /api/analytics/all-touchdowns` endpoint with `first_td_only` filter
- `GET /api/analytics/user-stats` endpoint for win rate, Brier score, streaks

### Changed
- Analytics page: consolidated into tabs; single Touchdowns table replaces separate All Touchdowns and First TD of Game sections
- **Documentation**: Updated ANALYTICS_GUIDE, README API table, ARCHITECTURE_DIAGRAMS (touchdowns table), DESIGN_SYSTEM; moved completed plans to archive
- Pinned backend dependencies in requirements.txt for reproducible builds
- Improved production error handling (no exception details in response when debug=false)
- Config validation at startup (database path consistency)
- **Documentation**: Updated README, docs, web/README, data/README, and deployment guide for Next.js + FastAPI; Docker/Railway env vars and volume instructions
- **Dockerfile**: Health check uses `${PORT}` for Railway; `DATABASE_PATH` default; build/run notes
- **railway.json**: Formatted for readability

### Security
- Documented auth posture: username-only auth intended for private friend groups only

### Fixed
- README paths corrected for project root (project root vs Fast6 subfolder)

## [1.0.0] - 2025

- Initial release: Next.js dashboard, FastAPI backend, SQLite, NFL data integration, auto-grading, analytics
