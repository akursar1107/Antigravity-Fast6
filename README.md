# 🏈 Fast6 - NFL First TD Prediction Tool

A Streamlit web application for managing **first touchdown scorer predictions** across a friend group. Admin inputs picks, friends view leaderboard and ROI tracking. Integrates NFL game data with real-time betting odds.

**Status:** v2.0.0 ✅ Clean Architecture Implemented | Production Ready

> **Latest Update (Feb 3, 2026):** Complete architectural restructuring with clean architecture principles. Core business logic now independent of Streamlit/database, improved testability and maintainability. See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for details.

## Quick Start

### Prerequisites
- Python 3.8+
- Virtual environment (recommended)

### Installation & Running

```bash
# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run the app (legacy architecture)
streamlit run src/app.py

# Or run with new clean architecture (v2.0.0)
streamlit run src/app_v2.py
```

The app will be available at **http://localhost:8501**

## Documentation

**Architecture & Development**:
- [Architecture Reference](docs/ARCHITECTURE.md) - Clean architecture design and principles
- [Configuration Guide](docs/guides/CONFIG_GUIDE.md) - Settings and customization
- [Deployment Guide](docs/deployment/DEPLOYMENT.md) - Production deployment

**Project Status**:
- [Changelog](docs/CHANGELOG.md) - Version history and updates
- [Phase Completions](archive/completed-phases/) - Historical phase documentation

## Features

### Admin Interface
- **👥 User Management**: Add/remove group members
- **📝 Pick Input**: Select week and first TD scorer for each game
- **✅ Update Results**: Mark picks correct/incorrect with ROI calculation
- **🎯 Auto-Grade**: Grade picks using play-by-play data with fuzzy matching
- **📥 CSV Import**: Bulk import picks with automatic game ID matching
- **📊 Analytics**: ELO ratings, player performance, ROI trends

### Public Dashboard
- **🏆 Leaderboard**: Group standings, ROI, efficiency metrics
- **📝 Weekly Picks**: Browse picks with odds and actual returns
- **🌟 Player Performance**: Hot/cold tracker, TD rates, position leaders
- **💰 ROI Trends**: Profitability analysis, cumulative returns
- **⚡ Power Rankings**: ELO-based team ratings and matchup analysis
- **🛡️ Defense Matchups**: Defensive weakness analysis
- **📅 Schedule**: Game schedules and results

## Tech Stack

- **Streamlit** v1.52.2 - Interactive web UI
- **SQLite** - Local database persistence with game_id foreign key
- **nflreadpy** v0.1.5 - NFL game and player data, schedule matching
- **pandas** v2.3.3 - Data processing and analysis
- **Python 3.13** - Core language
- **requests** - API calls for odds data

## Project Structure

```
Fast6/
├── src/                            # Main application code
│   ├── app.py                      # Streamlit entry point
│   ├── config.py                   # Configuration loader (JSON-based)
│   ├── config.json                 # Centralized configuration
│   ├── data_processor.py           # Data processing (deprecated)
│   ├── database.py                 # Database operations (deprecated)
│   ├── utils/                      # Utility modules (14 modules)
│   │   ├── db_connection.py        # Database connection
│   │   ├── db_users.py             # User CRUD
│   │   ├── db_picks.py             # Pick CRUD
│   │   ├── db_weeks.py             # Week CRUD
│   │   ├── db_stats.py             # Statistics & leaderboards
│   │   ├── theming.py              # Dynamic CSS generation
│   │   ├── grading_logic.py        # Auto-grading
│   │   ├── nfl_data.py             # NFL API integration
│   │   ├── odds_api.py             # Odds API integration
│   │   └── ...other utilities
│   └── views/                      # View components
│       ├── admin_page.py           # Admin router (74 lines)
│       ├── public_dashboard.py     # Public router (74 lines)
│       ├── admin/                  # Admin submodules (6 tabs)
│       └── tabs/                   # Dashboard submodules (6 tabs)
├── data/                           # Data directory
│   └── fast6.db                    # SQLite database
├── tests/                          # Test suite
│   └── test_logic.py               # Unit tests
├── archive/                        # Obsolete files (git-ignored)
├── resources/                      # Reference projects (git-ignored)
├── requirements.txt                # Dependencies
├── DEPLOYMENT.md                   # Cloud deployment guide
├── ROADMAP.md                      # Feature roadmap
└── README.md                       # This file
```

## Implementation Status

### ✅ Phase 1: Core Foundation (Complete)
- Database integration with SQLite
- Admin interface with 6 management tabs
- Public dashboard with 6 data views
- CSV import with game ID matching
- Auto-grading with fuzzy name matching

### ✅ Phase 2: Configuration Refactoring (Complete)
- JSON configuration system (`config.json`)
- Centralized scoring, seasons, teams, API configuration
- All hardcoded values replaced with config references
- Configuration loader with st.secrets support

### ✅ Phase 3: Dynamic UI Theming (Complete)
- Dynamic CSS generation from configuration
- Modern gradient backgrounds and animations
- Glass-morphism UI effects
- Theme customization via JSON (no code changes needed)
- Full code modularization (34 Python modules)

### ✅ Phase 4: Documentation & Testing (Complete)
- CONFIG_GUIDE.md - Complete configuration reference
- THEMING_GUIDE.md - Theme customization guide
- 78 unit/integration tests (100% pass rate)
- Code optimization: batch DB ops, caching, SQL extraction

### ✅ Phase 5: Advanced Analytics (Complete)
- **Player Performance Tracking**: Hot/cold indicators, TD rates, position leaders
- **ROI & Profitability Trends**: Cumulative ROI, weekly performance, strategy analysis
- **Team ELO Rating System**: Power rankings, matchup predictions, rating trends
- **Defensive Matchup Analysis**: Weak defenses, position matchups, recommendations
- 4 new dashboard tabs with 12+ interactive visualizations
- 3,300+ lines of new analytics code

See [ROADMAP.md](ROADMAP.md) for planned enhancements.

## Deployment

### 🚀 Deploy to Railway (Recommended)

Railway is the recommended hosting platform - it offers a free tier, automatic Docker detection, and persistent storage.

```bash
# Option 1: GitHub Integration (Easiest)
# 1. Push to GitHub
# 2. Connect repo at railway.app
# 3. Railway auto-deploys!

# Option 2: Railway CLI
npm install -g @railway/cli
railway login
railway init
railway up
```

For detailed deployment instructions, see [DOCKER.md](DOCKER.md).

## Contributing

Feel free to open issues and pull requests to improve the app!

## License

MIT License - see repository for details
