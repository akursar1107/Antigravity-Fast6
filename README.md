# 🏈 Fast6 - NFL First TD Prediction Tool

A Streamlit web application for managing **first touchdown scorer predictions** across a friend group. Admin inputs picks, friends view leaderboard and ROI tracking. Integrates NFL game data with real-time betting odds. **Phase 1 Complete ✅**

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
- **✅ Results Tracking**: Mark picks correct/incorrect with ROI calculation
- **📊 Member Stats**: View individual win %, picks, and returns

### Public Dashboard
- **🏆 Leaderboard**: Group standings with cumulative ROI
- **📝 Week Picks**: Browse all picks by member and result
- **📋 All Touchdowns**: Database of all season TDs
- **📅 Weekly Schedule**: Game schedules and results
- **📊 Analysis**: Team/player/position first TD statistics
- **💰 Odds Integration**: Real-time betting odds from API

## Tech Stack

- **Streamlit** v1.52.2 - Interactive web UI
- **SQLite** - Local database persistence
- **nflreadpy** v0.1.5 - NFL game and player data
- **pandas** v2.3.3 - Data processing and analysis
- **Python 3.13** - Core language
- **requests** - API calls for odds data

## Project Structure

```
Fast6/
├── src/
│   ├── app.py                      # Router (90 lines)
│   ├── database.py                 # SQLite CRUD (550 lines)
│   ├── config.py                   # Constants & API keys
│   ├── data_processor.py           # NFL data processing
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
- Database persistence (SQLite)
- Admin interface with user/pick/result management
- Public leaderboard and picks viewer
- ROI tracking and statistics
- Comprehensive test suite (8 integration tests)

See [PHASE1_COMPLETE.md](PHASE1_COMPLETE.md) for detailed documentation.

## Phase 2 & Beyond

See [ROADMAP.md](ROADMAP.md) for planned enhancements:
- Enhanced ROI analytics and trends
- Defensive matchup analysis
- User self-management (optional light auth)
- Multi-group support

## Deployment

For cloud deployment instructions, see [DEPLOYMENT.md](DEPLOYMENT.md).

## Contributing

Feel free to open issues and pull requests to improve the app!

## License

MIT License - see repository for details
