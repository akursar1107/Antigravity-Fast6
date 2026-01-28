# Configuration Guide

Complete reference for Fast6 configuration system.

---

## Overview

Fast6 uses a centralized JSON configuration file (`src/config.json`) to manage all application settings. This eliminates hardcoded values and enables environment-specific customization without code changes.

**Key Features:**
- ✅ Centralized configuration in JSON format
- ✅ Environment-based overrides via st.secrets and environment variables
- ✅ Dynamic theming (colors, fonts, spacing)
- ✅ Feature toggles (enable/disable features)
- ✅ Easy to modify without touching code

---

## Configuration Structure

### `app` Section
Application metadata and settings.

```json
{
  "app": {
    "name": "Fast6",
    "version": "1.0.0",
    "current_season": 2025,
    "database_path": "data/fast6.db",
    "description": "NFL First TD Prediction Pool"
  }
}
```

| Field | Type | Purpose | Example |
|-------|------|---------|---------|
| `name` | string | App display name | "Fast6" |
| `version` | string | Current version | "1.0.0" |
| `current_season` | integer | Active NFL season | 2025 |
| `database_path` | string | SQLite database location | "data/fast6.db" |
| `description` | string | App tagline | "NFL First TD Prediction Pool" |

**How to modify:**
```bash
# Change to 2026 season
# Edit src/config.json, line 3:
"current_season": 2026
```

---

### `seasons` Section
List of available seasons for users to select.

```json
{
  "seasons": [2025, 2024, 2023, 2022, 2021, 2020, 2019, 2018, 2017, 2016]
}
```

**How to modify:**
```bash
# Add 2026, remove 2016
"seasons": [2026, 2025, 2024, 2023, 2022, 2021, 2020, 2019, 2018, 2017]
```

**Accessing in code:**
```python
from config import SEASONS
# SEASONS = [2025, 2024, ...]

# In UI
season = st.selectbox("Season", SEASONS)
```

---

### `scoring` Section
Points and scoring rules.

```json
{
  "scoring": {
    "first_td_win": 3,
    "any_time_td": 1,
    "name_match_threshold": 0.75,
    "auto_grade_enabled": true
  }
}
```

| Field | Type | Purpose | Example |
|-------|------|---------|---------|
| `first_td_win` | integer | Points for correct first TD pick | 3 |
| `any_time_td` | integer | Points for anytime TD pick | 1 |
| `name_match_threshold` | float | Fuzzy matching confidence (0.0-1.0) | 0.75 |
| `auto_grade_enabled` | boolean | Enable auto-grading | true |

**How to modify:**
```bash
# Make first TD worth 5 points instead of 3
"first_td_win": 5,

# Lower fuzzy match threshold for more aggressive matching
"name_match_threshold": 0.70,

# Disable auto-grading
"auto_grade_enabled": false
```

**Accessing in code:**
```python
from config import SCORING_FIRST_TD, SCORING_ANY_TIME
# SCORING_FIRST_TD = 3
# SCORING_ANY_TIME = 1

# In SQL queries (uses f-strings):
cursor.execute(f"""
    SELECT SUM(CASE WHEN is_correct = 1 THEN {SCORING_FIRST_TD} ELSE 0 END) as points
    FROM results
""")
```

---

### `teams` Section
All 32 NFL teams with divisions and conferences.

```json
{
  "teams": {
    "ARI": {
      "full_name": "Arizona Cardinals",
      "division": "NFC West",
      "conference": "NFC"
    },
    "ATL": {
      "full_name": "Atlanta Falcons",
      "division": "NFC South",
      "conference": "NFC"
    }
    // ... 30 more teams
  }
}
```

| Field | Type | Purpose | Example |
|-------|------|---------|---------|
| Key (3-char) | string | Team abbreviation | "ARI" |
| `full_name` | string | Full team name | "Arizona Cardinals" |
| `division` | string | NFL division | "NFC West" |
| `conference` | string | Conference (AFC/NFC) | "NFC" |

**How to modify:**
```bash
# Update team name
"ARI": {
  "full_name": "Arizona Cardinals",
  "division": "NFC West",
  "conference": "NFC"
}
```

**Accessing in code:**
```python
from config import TEAM_MAP, TEAM_ABBR_MAP

# Get full name from abbreviation
team_name = TEAM_MAP["ARI"]  # "Arizona Cardinals"

# Get abbreviation from full name
abbr = TEAM_ABBR_MAP["Arizona Cardinals"]  # "ARI"

# List all NFC teams
nfc_teams = {k: v for k, v in TEAM_MAP.items() if v['conference'] == 'NFC'}
```

---

### `api` Section
API configuration for external services.

```json
{
  "api": {
    "odds_api": {
      "key_env_var": "ODDS_API_KEY",
      "base_url": "https://api.the-odds-api.com/v4",
      "sport": "americanfootball_nfl",
      "market": "player_anytime_td",
      "regions": "us",
      "format": "american",
      "cache_ttl": 3600
    }
  }
}
```

| Field | Type | Purpose | Example |
|-------|------|---------|---------|
| `key_env_var` | string | Environment variable name | "ODDS_API_KEY" |
| `base_url` | string | API base URL | "https://api.the-odds-api.com/v4" |
| `sport` | string | Sport type | "americanfootball_nfl" |
| `market` | string | Betting market | "player_anytime_td" |
| `regions` | string | Regions to query | "us" |
| `format` | string | Odds format | "american" |
| `cache_ttl` | integer | Cache time-to-live (seconds) | 3600 |

**How to set the API key:**

Option 1: Environment variable
```bash
export ODDS_API_KEY="your_key_here"
streamlit run src/app.py
```

Option 2: Streamlit secrets (recommended)
```bash
# Create .streamlit/secrets.toml
echo 'ODDS_API_KEY = "your_key_here"' > .streamlit/secrets.toml
```

Option 3: Access via code
```python
from config import ODDS_API_KEY
# Will load from st.secrets → environment variable → None
```

**Accessing in code:**
```python
from config import ODDS_API_BASE_URL, ODDS_API_SPORT, ODDS_API_MARKET

# In API calls
response = requests.get(
    f"{ODDS_API_BASE_URL}/sports/{ODDS_API_SPORT}/odds",
    params={"market": ODDS_API_MARKET, "regions": "us"}
)
```

---

### `ui_theme` Section
Colors, fonts, and visual styling.

```json
{
  "ui_theme": {
    "primary_color": "#667eea",
    "secondary_color": "#764ba2",
    "accent_color": "#f093fb",
    "success_color": "#48bb78",
    "error_color": "#f56565",
    "warning_color": "#ed8936",
    "info_color": "#4299e1",
    "font_family": "Inter, sans-serif",
    "border_radius": "20px"
  }
}
```

| Field | Type | Purpose | Example |
|-------|------|---------|---------|
| `primary_color` | hex | Main brand color | "#667eea" |
| `secondary_color` | hex | Secondary/accent color | "#764ba2" |
| `accent_color` | hex | Tertiary accent | "#f093fb" |
| `success_color` | hex | Success/positive state | "#48bb78" |
| `error_color` | hex | Error/negative state | "#f56565" |
| `warning_color` | hex | Warning state | "#ed8936" |
| `info_color` | hex | Info/neutral state | "#4299e1" |
| `font_family` | string | Font stack | "Inter, sans-serif" |
| `border_radius` | string | Border radius | "20px" |

**How to change theme:**
```bash
# Switch to dark mode colors
"primary_color": "#1e40af",
"secondary_color": "#7c3aed",
"accent_color": "#06b6d4"

# Or use a cool blue theme
"primary_color": "#0369a1",
"secondary_color": "#0284c7",
"accent_color": "#06b6d4"
```

**Accessing in code:**
```python
from config import THEME

# Theme is a dictionary with all colors
print(THEME["primary_color"])  # "#667eea"

# Used by dynamic theming
from utils.theming import generate_theme_css
css = generate_theme_css(THEME)
st.markdown(css, unsafe_allow_html=True)
```

---

### `positions` Section
Valid player positions.

```json
{
  "positions": ["QB", "RB", "WR", "TE", "FB", "K", "D/ST"]
}
```

**How to modify:**
```bash
# Add LS (long snapper) if needed
"positions": ["QB", "RB", "WR", "TE", "FB", "K", "LS", "D/ST"]
```

**Accessing in code:**
```python
from config import POSITIONS

# In dropdowns
position = st.selectbox("Position", POSITIONS)
```

---

### `features` Section
Feature toggles to enable/disable functionality.

```json
{
  "features": {
    "auto_grading": true,
    "csv_import": true,
    "admin_panel": true,
    "multi_group_support": false,
    "user_self_management": false
  }
}
```

| Field | Type | Purpose | Example |
|-------|------|---------|---------|
| `auto_grading` | boolean | Auto-grade picks from PBP | true |
| `csv_import` | boolean | Allow CSV bulk import | true |
| `admin_panel` | boolean | Show admin interface | true |
| `multi_group_support` | boolean | Support multiple groups | false |
| `user_self_management` | boolean | Allow users to enter picks | false |

**How to disable a feature:**
```bash
# Disable CSV import
"csv_import": false

# Enable user self-management
"user_self_management": true
```

**Accessing in code:**
```python
from config import FEATURES

if FEATURES["auto_grading"]:
    show_grade_picks_tab()

if FEATURES["csv_import"]:
    show_csv_import_tab()
```

---

## Environment-Specific Configuration

### Local Development

Create `.streamlit/secrets.toml`:
```toml
ODDS_API_KEY = "dev_key_here"
```

### Production Deployment

Set environment variables:
```bash
export ODDS_API_KEY="prod_key_here"
export DATABASE_PATH="prod/fast6.db"
```

Or in Streamlit Cloud:
- Go to app settings
- Add secrets under "Secrets"
- Paste: `ODDS_API_KEY = "your_key"`

---

## Configuration Best Practices

### 1. **Never commit secrets**
```bash
# Good: Git ignores .streamlit/secrets.toml
.streamlit/secrets.toml

# Good: Use environment variables
export ODDS_API_KEY="xyz"

# Bad: Don't hardcode in config.json
"api_key": "xyz"
```

### 2. **Version your config**
```bash
# Commit config.json (without secrets)
git add src/config.json

# Don't commit secrets
echo ".streamlit/secrets.toml" >> .gitignore
```

### 3. **Use consistent naming**
```bash
# Good: Clear, descriptive names
"first_td_win": 3

# Bad: Unclear abbreviations
"ftd": 3
```

### 4. **Document custom values**
```bash
# Good: Leave comments in JSON
{
  "scoring": {
    "first_td_win": 3,  // Points for correct first TD pick
    "any_time_td": 1    // Points for anytime TD pick
  }
}

# Note: JSON doesn't support comments, use config.md instead
```

---

## Common Configuration Tasks

### Task 1: Change Scoring Rules

```bash
# Edit src/config.json
{
  "scoring": {
    "first_td_win": 5,      // Was 3, now 5 points
    "any_time_td": 2        // Was 1, now 2 points
  }
}

# Restart app
streamlit run src/app.py
```

### Task 2: Add a New Season

```bash
{
  "seasons": [2026, 2025, 2024, ...]  // Add 2026 at front
}
```

### Task 3: Change Theme

```bash
{
  "ui_theme": {
    "primary_color": "#FF6B6B",      // Red theme
    "secondary_color": "#4ECDC4"     // Teal
  }
}

# Refresh browser - theme updates instantly
```

### Task 4: Set API Key (3 ways)

**Way 1: Environment variable**
```bash
export ODDS_API_KEY="abc123xyz"
streamlit run src/app.py
```

**Way 2: Streamlit secrets**
```bash
cat > .streamlit/secrets.toml << 'EOF'
ODDS_API_KEY = "abc123xyz"
EOF
```

**Way 3: Streamlit Cloud**
- Paste in secrets section of app settings

---

## Troubleshooting

### Q: "ODDS_API_KEY not found in st.secrets or environment variables"

**A:** This is just a warning. The app works without it. To fix:
1. Get API key from https://the-odds-api.com
2. Create `.streamlit/secrets.toml` with: `ODDS_API_KEY = "your_key"`
3. Restart app

### Q: Changes to config.json aren't showing up

**A:** Restart the app:
```bash
# Stop the running streamlit process
pkill -f "streamlit run"

# Start again
streamlit run src/app.py
```

### Q: My custom colors don't show up

**A:** Check:
1. Are colors valid hex? (e.g., `#667eea`)
2. Did you restart the app?
3. Clear browser cache? (Ctrl+Shift+Delete)
4. Check that `.streamlit/config.toml` matches your colors

### Q: Can I use RGB colors instead of hex?

**A:** No, stick with hex format (`#667eea`). Use a converter:
- https://www.colorhexa.com/ (RGB to hex)
- https://htmlcolorcodes.com/

---

## JSON Schema Validation

To validate your config.json is correct:

```python
import json
import sys

try:
    with open('src/config.json') as f:
        config = json.load(f)
    print("✅ config.json is valid JSON")
    print(f"Seasons: {config['seasons']}")
    print(f"Teams: {len(config['teams'])}")
    print(f"Features: {config['features']}")
except json.JSONDecodeError as e:
    print(f"❌ Invalid JSON: {e}")
    sys.exit(1)
```

---

## Further Reading

- See `THEMING_GUIDE.md` for detailed theming documentation
- See `REFACTORING.md` for code architecture
- See `ROADMAP.md` for feature plans
