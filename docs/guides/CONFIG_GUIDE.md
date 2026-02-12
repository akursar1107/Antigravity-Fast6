# Configuration Guide

Fast6 uses two configuration sources. Avoid duplicating the same key in both.

---

## 1. `backend/config/` (config.json)

**Purpose:** App/UI configuration — teams, scoring, theme, feature flags, API endpoints.

**Source:** `backend/config/config.json` (loaded at import time).

**Used by:** Tests, grading logic, team lookups, UI theme, CSV import, analytics modules.

**Keys include:**
- `app` — current_season, current_week, database_path
- `scoring` — first_td_win, any_time_td, name_match_threshold
- `teams` — team abbreviations and full names
- `api` — odds API, Polymarket, Kalshi base URLs
- `ui_theme` — colors, fonts, border radius
- `features` — auto_grading, csv_import, admin_panel

**Sensitive values:** Use env vars (e.g. `ODDS_API_KEY`). Config loader falls back to env when a key is missing from JSON.

---

## 2. `backend/api/fastapi_config.py` (Pydantic Settings)

**Purpose:** Runtime settings — database path, JWT, CORS, server host/port.

**Source:** Environment variables and `.env` file (Pydantic v2 `BaseSettings`).

**Used by:** FastAPI app, auth, CORS, DB connection in API layer.

**Keys include:**
- `DATABASE_PATH` — SQLite file path
- `SECRET_KEY` — JWT signing (required secure value in production)
- `CORS_ORIGINS` — comma-separated origins
- `ENVIRONMENT` — development | production
- `DEBUG` — enable debug output

---

## Summary

| Concern       | Use config.json        | Use fastapi_config (env) |
|---------------|------------------------|---------------------------|
| Teams, scoring| ✅                     | —                         |
| Theme, feature flags | ✅               | —                         |
| DB path       | ✅ (fallback)          | ✅ (primary for API)       |
| JWT secret    | —                      | ✅                         |
| CORS origins  | —                      | ✅                         |

Do not duplicate the same setting in both. Prefer env for deployment-specific values; prefer config.json for app-wide constants.
