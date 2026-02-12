# services/analytics/ — Business Logic Analytics

This package contains **analytics that use the database** and implement Fast6
business logic. It depends on `analytics/` for low-level NFL data.

- **player_stats.py**: Player performance tracking, TD analysis
- **roi_trends.py**: User profitability, ROI calculations
- **elo_ratings.py**: Team power rankings via ELO system
- **defense_analysis.py**: Defensive matchup analysis

For **low-level NFL data loading** (play-by-play, schedules), see `analytics/`.
