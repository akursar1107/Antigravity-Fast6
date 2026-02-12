# Fast6 Project Audit — February 2026

## Summary

Comprehensive review of the Fast6 codebase: bugs fixed, issues documented, and optimization recommendations.

---

## Fixes Applied

### 1. Broken imports in `csv_import_clean.py`
- **Issue:** `from .nfl_data` and `from .name_matching` failed — `nfl_data` lives in `backend.analytics`, not `data_import`.
- **Fix:** `backend.analytics.nfl_data` and `backend.utils.name_matching`.

### 2. ImportResult `picks_imported` typo
- **Issue:** `result.picks_imported` in csv_import_clean.py — `ImportResult` has `success_count`, not `picks_imported`.
- **Fix:** Use `result.success_count`.

### 3. Broken import in `team_utils.py`
- **Issue:** `from .nfl_data` inside `backfill_team_for_picks()` — `utils` has no `nfl_data`.
- **Fix:** `backend.analytics.nfl_data` and `backend.utils.name_matching`.

### 4. Results `payout` vs `actual_return` schema mismatch
- **Issue:** `fastapi_results.py` used `r.payout` and `INSERT ... payout`, but results table has `actual_return`.
- **Fix:** Use `actual_return` in queries and inserts.

### 5. Admin batch-grade missing `actual_return`
- **Issue:** Batch insert omitted `actual_return`, so ROI was null for those grades.
- **Fix:** Fetch pick’s odds, compute `actual_return`, and include in INSERT.

### 6. Grading `float + None` with null odds
- **Issue:** `stats['total_return'] += actual_return` when `theo_return` was None.
- **Fix:** `float(theo_return) if ... else 0.0` in `grading_logic.py`.

### 7. Debug mode default in production
- **Issue:** `debug: bool = True` could expose stack traces in production.
- **Fix:** Default to `False`; use `DEBUG=1` or `.env` for local dev.

---

## Recommendations (Not Implemented)

### Security
- **SECRET_KEY:** Ensure `SECRET_KEY` is overridden in production (never use dev default).
- **CORS:** Add production domains to `cors_origins` when deploying.

### Performance
- **Caching:** Leaderboard/stats queries are already cached; consider `@st.cache_data` in frontend.
- **N+1:** `DashboardLayoutWrapper` fetches multiple endpoints; consider a combined endpoint if it becomes a bottleneck.

### API / Frontend
- **README:** Update API paths from `/api/` to `/api/v1/` for consistency.
- **Admin grading:** Add a “Run auto-grade” button that calls `/api/admin/auto-grade` (if implemented).

### Data
- **game_id format:** Import uses `{season}_{week}_{away}_{home}`; nflreadpy may use a different format. This can cause “failed to match” during grading. Consider adding a mapping layer or using nflreadpy schedule for game IDs.

### Testing
- **Test coverage:** `csv_import_clean` and `team_utils.backfill_team_for_picks` are not covered by tests.
- **Frontend:** Run `npm test` in web/ to confirm frontend tests pass.

### Dependencies
- **Python:** `nflreadpy>=0.1.0` — ensure compatibility with current API.
- **Node:** `next@16.1.6` — keep Next.js and related tools updated.

---

## Files Changed

| File | Change |
|------|--------|
| `backend/data_import/csv_import_clean.py` | Import paths, `picks_imported` → `success_count` |
| `backend/utils/team_utils.py` | Import paths |
| `backend/api/routers/fastapi_results.py` | `payout` → `actual_return` |
| `backend/api/routers/fastapi_admin.py` | Batch-grade: add `actual_return` |
| `backend/grading/grading_logic.py` | Handle `theo_return is None` |
| `backend/api/fastapi_config.py` | `debug` default `False` |

---

## Verification

- `python -m pytest backend/tests/ -v` — 101 passed
- `backend.data_import.csv_import_clean import_picks_from_csv` — imports OK
- `backend.utils.team_utils backfill_team_for_picks` — imports OK
