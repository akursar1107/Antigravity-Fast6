# Unused Code Remediation Plan — Feb 2026

Plan to fix or implement the remaining built-but-unused items identified in the codebase audit.

---

## Completed

- **csv_import.py** and **csv_import_clean.py** — Archived to `archive/backend/data_import/`
- **Frontend API cleanup** — Removed dead exports from `web/src/lib/api.ts`; updated api.test.ts for 502 message
- **Analytics archive** — `analytics.py` and `opening_drive_analytics.py` → `archive/backend/analytics/`; removed from `utils` exports
- **Config documentation** — Added `docs/guides/CONFIG_GUIDE.md` (config.json vs fastapi_config)
- **Market data service** — Archived `market_data_service.py` → `archive/backend/services/`

---

## Remediation Options by Category

### 1. Analytics (Low Priority)

| Item | Action | Effort |
|------|--------|--------|
| `opening_drive_analytics.py` | **Archive** or **Wire** — If we want “opening drive” stats in the UI, add an API route and call it. Otherwise archive. | Low |
| `analytics.py` (get_team/player/position_first_td_counts) | **Archive** — Exported via utils but never used. Either add to an analytics endpoint or remove from utils exports. | Low |

**Recommendation:** Archive both unless we plan an “NFL First TD Trends” analytics tab. Remove from `backend.utils.__init__` exports.

---

### 2. Core Use Cases vs Direct DB (Medium Priority)

| Item | Action | Effort |
|------|--------|--------|
| `core/picks` and `core/grading` | **Wire or Archive** — The API routers use raw SQL. Core use cases exist but aren’t called. Two paths: (A) Refactor routers to use use cases for consistency, or (B) Archive core and keep current approach. | Medium |

**Recommendation:** Keep as-is for now. The direct DB approach works. If we want cleaner architecture later, wire use cases in a dedicated refactor.

---

### 3. Repositories (kickoff_repo, market_odds_repo)

| Item | Action | Effort |
|------|--------|--------|
| `kickoff_repo`, `market_odds_repo` | **Wire or Archive** — Tables exist; no API surface. Either add endpoints (e.g. kickoff decisions per game) or remove from exports if we don’t plan to use them. | Low–Medium |

**Recommendation:** Leave as-is. Tables and repos are harmless. Add API routes only if we need kickoff or market-odds features.

---

### 4. Market Data Service

| Item | Action | Effort |
|------|--------|--------|
| `market_data_service.py` | **Archive or Implement** — Fetches Polymarket/Kalshi odds. Not called by any route or cron. Either add a sync job/endpoint or archive. | Medium |

**Recommendation:** Archive unless we plan to expose prediction-market odds in the UI. The integrations (polymarket, kalshi) can stay for future use.

---

### 5. Dual Config (backend.config vs fastapi_config)

| Item | Action | Effort |
|------|--------|--------|
| `backend/config/` (config.json) | **Consolidate** — FastAPI uses pydantic-settings (env). Tests/config use config.json. Decide on a single source: migrate config.json values to env + pydantic, or keep both with clear roles. | Medium |

**Recommendation:** Keep both but document: `fastapi_config` for runtime (DB, JWT, CORS); `config.json` for app/UI (teams, scoring, theme). Avoid duplicating the same key in both.

---

### 6. Frontend API Cleanup (Low Effort)

| Item | Action | Effort |
|------|--------|--------|
| Unused client API functions | **Remove or Keep** — `getOddsAccuracy`, `getDefenseStats`, `getGradingStatus`, `deleteRequest`, and client variants of `getSeasonStats`, `getWeekPicks`, etc. Only used in tests. | Low |

**Recommendation:** Remove unused exports to reduce noise. Update tests to use `*Server` variants or mock `request()` directly.

---

## Suggested Implementation Order

1. **Frontend API cleanup** — Remove dead exports (30 min).
2. **Analytics archive** — Move `opening_drive_analytics.py` and `analytics.py` to archive; remove from utils exports (30 min).
3. **Config documentation** — Add a short doc clarifying config.json vs env (15 min).
4. **Market data** — Archive `market_data_service.py` if no near-term plans (15 min).

---

## Not Recommended

- **Refactoring API to use core use cases** — High effort, low immediate value. Defer.
- **Adding kickoff/market-odds API** — Only if we have a concrete feature need.
