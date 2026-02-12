# analytics/ — Low-level NFL & Odds Helpers

This package provides **data loading and aggregation utilities** for NFL play-by-play
and odds data. It does not depend on the database or business logic.

- **nfl_data.py**: Load NFL play-by-play, schedules, rosters (nflreadpy)
- **odds_utils.py**: Odds conversion, formatting
- **first_drive_success.py**: Opening drive analytics

Archived (see `archive/backend/analytics/`): analytics.py, opening_drive_analytics.py

For **business logic** (ELO, ROI, defense analysis, player stats) that uses the database,
see `services/analytics/`.
