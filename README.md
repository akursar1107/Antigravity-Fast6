# 🏈 NFL Touchdown Tracker

A Streamlit web application that helps users analyze and predict **first touchdown scorers** in NFL games by integrating real-time player statistics with current betting odds.

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

- **📅 Game Schedule**: Browse upcoming NFL games for any season
- **📊 Player & Team Stats**: View first touchdown scoring rates and historical data
- **💰 Odds Integration**: Real-time betting odds from integrated API
- **🎯 Prediction Tracking**: Make picks and track your predictions
- **📈 Advanced Analysis**: Compare player performance against betting odds to identify +EV opportunities

## Tech Stack

- **Streamlit** - Interactive web UI
- **nflreadpy** - NFL game and player data
- **pandas** - Data processing and analysis
- **Python 3** - Core language

## Project Structure

```
Fast6/
├── src/
│   ├── app.py              # Main Streamlit application
│   ├── config.py           # Configuration & constants
│   ├── data_processor.py   # Data fetching & processing logic
│   └── __pycache__/
├── tests/
│   ├── test_logic.py       # Unit tests
│   └── __pycache__/
├── requirements.txt        # Python dependencies
├── DEPLOYMENT.md           # Cloud deployment guide
├── ROADMAP.md              # Future features & improvements
└── README.md               # This file
```

## Deployment

For cloud deployment instructions, see [DEPLOYMENT.md](DEPLOYMENT.md).

## Roadmap

See [ROADMAP.md](ROADMAP.md) for planned features including:

### Infrastructure & Backend
- Database integration for persistence
- Docker containerization
- Automated data pipeline (GitHub Actions/Cron)

### Advanced Analysis
- Implied Probability vs. Actual Rate comparison
- Defensive matchup analysis
- +EV (Positive Expected Value) indicators

### User Experience
- User profiles / simple name selector
- Leaderboards for gamification
- Prediction history & ROI tracking

### DevOps & Quality
- CI/CD pipeline with GitHub Actions
- Code formatting (black) and linting (ruff)
- Automated testing on every push

## Contributing

Feel free to open issues and pull requests to improve the app!

## License

MIT License - see repository for details
