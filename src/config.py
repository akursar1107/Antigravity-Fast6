# Configuration and Constants

# API Configuration
ODDS_API_KEY = "11d265853d712ded110d5e0a5ff82c5b"  # Ideally move to st.secrets in production
ODDS_API_MARKET = "player_anytime_td"  # Market type for First TD odds
ODDS_API_BASE_URL = "https://api.the-odds-api.com/v4"
ODDS_API_SPORT = "americanfootball_nfl"
ODDS_API_REGIONS = "us"
ODDS_API_FORMAT = "american"

# Season Configuration
SEASONS = list(range(2025, 1999, -1))

# Team Abbreviation Mapping (Full Name -> Abbreviation)
TEAM_ABBR_MAP = {
    # Full names
    "Arizona Cardinals": "ARI", "Atlanta Falcons": "ATL", "Baltimore Ravens": "BAL", "Buffalo Bills": "BUF",
    "Carolina Panthers": "CAR", "Chicago Bears": "CHI", "Cincinnati Bengals": "CIN", "Cleveland Browns": "CLE",
    "Dallas Cowboys": "DAL", "Denver Broncos": "DEN", "Detroit Lions": "DET", "Green Bay Packers": "GB",
    "Houston Texans": "HOU", "Indianapolis Colts": "IND", "Jacksonville Jaguars": "JAX", "Kansas City Chiefs": "KC",
    "Las Vegas Raiders": "LV", "Los Angeles Chargers": "LAC", "Los Angeles Rams": "LA", "Miami Dolphins": "MIA",
    "Minnesota Vikings": "MIN", "New England Patriots": "NE", "New Orleans Saints": "NO", "New York Giants": "NYG",
    "New York Jets": "NYJ", "Philadelphia Eagles": "PHI", "Pittsburgh Steelers": "PIT", "San Francisco 49ers": "SF",
    "Seattle Seahawks": "SEA", "Tampa Bay Buccaneers": "TB", "Tennessee Titans": "TEN", "Washington Commanders": "WAS",
    # Short city names (for CSV compatibility)
    "Arizona": "ARI", "Atlanta": "ATL", "Baltimore": "BAL", "Buffalo": "BUF",
    "Carolina": "CAR", "Chicago": "CHI", "Cincinnati": "CIN", "Cleveland": "CLE",
    "Dallas": "DAL", "Denver": "DEN", "Detroit": "DET", "Green Bay": "GB",
    "Houston": "HOU", "Indianapolis": "IND", "Jacksonville": "JAX", "Kansas City": "KC",
    "Las Vegas": "LV", "LA Chargers": "LAC", "LA Rams": "LA", "Miami": "MIA",
    "Minnesota": "MIN", "New England": "NE", "New Orleans": "NO", "NY Giants": "NYG",
    "NY Jets": "NYJ", "Philadelphia": "PHI", "Pittsburgh": "PIT", "San Francisco": "SF",
    "Seattle": "SEA", "Tampa Bay": "TB", "Tennessee": "TEN", "Washington": "WAS"
}
