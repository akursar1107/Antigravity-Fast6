# 🏈 Fast6 - NFL First TD Prediction Tool

A Streamlit web application for managing **first touchdown scorer predictions** across a friend group. Admin inputs picks, friends view leaderboard and ROI tracking. Integrates NFL game data with real-time betting odds. **Phase 1 Complete ✅ | Phase 2 In Progress 🚀**

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

# Run the app
streamlit run src/app.py
```

The app will be available at **http://localhost:8501**

## Features

### Admin Interface
- **👥 User Management**: Add/remove group members
- **📝 Pick Input**: Select week and first TD scorer for each game
- **✅ Update Results**: Mark picks correct/incorrect, manual grade with ROI
- **📊 View Stats**: Member records with quick-edit data editor
- **📥 Import CSV**: Bulk import picks with Home/Visitor team matching to game_id
- **🎯 Grade Picks (NEW)**: Auto-grade ungraded picks using PBP data, edit picks before grading

### Public Dashboard
- **🏆 Leaderboard**: Group standings with ROI, Avg Odds, Theo Return, ROI Efficiency
- **📝 Weekly Picks**: Browse picks by week with Odds and Returns
- **📋 All Touchdowns**: Database of all season TDs
- **📅 Weekly Schedule**: Game schedules and results
- **📊 Analysis**: Team/player/position first TD statistics
- **🚀 First TD per Game**: Game-by-game breakdown

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
├── src/770 lines)
│   ├── config.py                   # Constants & API keys
│   ├── data_processor.py           # NFL data + CSV import (700 lines)
│   └── views/
│       ├── admin_page.py           # Admin interface (1000+ lines, 6g
│   └── pages/
│       ├── admin_page.py           # Admin interface (4 tabs)
│       └── public_dashboard.py     # Public dashboard (6 tabs)
├── data/
│   └── fast6.db                    # SQLite database
├── tests/
│   ├── test_logic.py               # Data processor tests
│   ├── test_database.py            # Database tests
│   └── test_phase1.py              # Integration tests
├── requirements.txt                # Dependencies
├── PHASE1_COMPLETE.md              # Phase 1 documentation
├── DEPLOYMENT.md                   # Cloud deployment guide
├── ROADMAP.md                      # Phase 2+ features
└── README.md                       # This file
```

## Phase 1 Status

**✅ COMPLETE** - All Phase 1 features implemented and tested:
- Database persistence (SQLite with game_id tracking)
- Admin interface with user/pick/result/stats management
- CSV import with Home/Visitor team matching to game_ids
- Public leaderboard and picks viewer with ROI tracking
- Comprehensive test suite

See [PHASE1_COMPLETE.md](PHASE1_COMPLETE.md) for detailed documentation.

## Phase 2 In Progress 🚀

**Current Work:**
- ✅ Grade Picks tab with PBP data auto-detection
- ✅ CSV import matching Home/Visitor teams to game_ids
- 🚀 Point system for First TD and Anytime TD scorers
- 🚀 Codebase refactoring for maintainability

See [ROADMAP.md](ROADMAP.md) for planned enhancements.

## Deployment

For cloud deployment instructions, see [DEPLOYMENT.md](DEPLOYMENT.md).

## Contributing

Feel free to open issues and pull requests to improve the app!

## License

MIT License - see repository for details
