# Fast6 Project Overview

**Status:** Phase 1 Complete ✅ | Phase 2 In Progress 🚀  
**Last Updated:** January 6, 2026

---

## 1. Project Overview

**Fast6** is a Streamlit-based web application for managing NFL first-touchdown scorer predictions within a friend group. The admin (you) controls all inputs, results, and grading, while friends view a shared leaderboard with ROI tracking and historical performance.

**Key Innovation:** Auto-grading using NFL play-by-play data with fuzzy name matching and game_id linking.

### Target Users
- **Admin (You)**: Manages picks, imports CSVs, grades results, updates game outcomes
- **Friends**: View picks, leaderboard, odds, returns, and historical stats

---

## 2. Vision & Goals

### Primary Vision
Create a **single pane of glass** for managing NFL first-touchdown predictions within a friend group, replacing spreadsheet-based tracking with a modern web application that auto-grades picks using real NFL data.

### Key Goals
1. **Simplify Pick Management** - CSV import and manual entry for weekly picks
2. **Auto-Grade with PBP Data** - Match picks to actual first TDs using NFL play-by-play
3. **Shared Transparency** - Friends see all picks, odds, returns, and standings
4. **Performance Tracking** - Monitor ROI, win rates, avg odds, theoretical returns
5. **Scalable Foundation** - Support future features (point systems, multi-group)

---

## 3. Current Architecture1.52.2
- **Database**: SQLite with 5-table schema (users, weeks, picks, results, game_id)
- **Data Source**: nflreadpy 0.1.5 (NFL PBP, schedule, roster data)
- **Data Processing**: pandas 2.3.3
- **Python**: 3.13
- **Deployment**: Streamlit Community Cloud (planned)

### Current Features (Phase 1 Complete + Phase 2 In Progress)
- ✅ 6-tab admin interface: User Mgmt, Pick Input, Update Results, View Stats, Import CSV, Grade Picks
- ✅ 6-tab public dashboard: Leaderboard, Weekly Picks, All TDs, Schedule, Analysis, First TD per Game
- ✅ CSV import with Home/Visitor team matching to game_id
- ✅ Auto-grading with PBP data using fuzzy name matching
- ✅ Odds display and theoretical return calculations
- ✅ ROI Efficiency metric on leaderboard
- 🚀 Point system for First TD and Anytime TD scorers (planned)
- 🚀 Codebase refactoring (planned)

### Project Structure
```
Fast6/
├── src/
│   ├── app.py                      # Router (90 lines)
│   ├── database.py                 # SQLite CRUD (770 lines)
│   ├── config.py                   # Constants & API keys
│   ├── data_processor.py           # NFL data + CSV import (700 lines)
│   └── views/
│       ├── admin_page.py           # Admin interface (1000+ lines, 6 tabs)
│       └── public_dashboard.py     # Public dashboard (6 tabs)
├── data/
│   └── fast6.db                    # SQLite database
├── tests/
│   ├── test_logic.py               # Data processor tests
│   ├── test_database.py            # Database tests
│   └── test_phase1.py              # Integration tests
├── requirements.txt                # Python dependencies
├── README.md                       # Quick start guide
├── PHASE1_COMPLETE.md              # Phase 1 documentation
├── ROADMAP.md                      # Feature roadmap
├── TODO.md                         # Current tasks
├── DEPLOYMENT.md                   # Deployment instructions
└── PROJECT.md                      # This file

requirements.txt        # Python dependencies
TODO.md                 # Refactoring & task tracking
```

---

## 4. Development Roadmap

### Phase 1: Core Foundation (COMPLETE ✅)
**Goal**: Establish database and admin/dashboard infrastructure

#### 1.1 Database Integration ✅
- SQLite database with 5-table schema (users, weeks, picks, results, game_id)
- 55+ CRUD operations for picks, results, statistics
- Persistent storage with cascading deletes
- Unique constraints and data integrity
- Migration system (ensure_game_id_column)

#### 1.2 Admin Interface ✅
- 6-tab admin page:
  1. User Management (add/delete members)
  2. Input Picks (manual pick entry)
  3. Update Results (mark correct/incorrect, delete picks)
  4. View Stats (quick-edit data table)
  5. Import CSV (bulk import with team matching)
  6. Grade Picks (auto-grade using PBP data)
- Editable tables with dropdowns
- Toast notifications for operations
- Maintenance tools (dedupe, backfill)

#### 1.3 Shared Dashboard ✅
- 6-tab public dashboard:
  1. Leaderboard (group standings with odds/ROI metrics)
  2. Week Picks (browse picks by week with results)
  3. All Touchdowns (season TD database)
  4. Weekly Schedule (game listings)
  5. Analysis (team/player/position stats)
  6. First TD per Game (game breakdown)
- Odds and theoretical return display
- ROI Efficiency metric

### Phase 2: Auto-Grading & CSV Import (IN PROGRESS 🚀)
**Goal**: Automate grading using NFL PBP data, enhance CSV import

##5-table schema with game_id foreign key
- SQLite for simplicity; easily migrated to PostgreSQL later
- Unique constraints for data integrity
- Cascading deletes for referential integrity

### Tables

#### `users`
Stores group member information.
```sql
CREATE TABLE users (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    email TEXT UNIQUE,
    is_admin BOOLEAN DEFAULT 0
);
```

#### `weeks`
Organizes picks by NFL season and week.
```sql
CREATE TABLE weeks (
    id INTEGER PRIMARY KEY,
    season INTEGER NOT NULL,
    week INTEGER NOT NULL,
    UNIQUE(season, week)
);
```

#### `picks`
Individual user predictions with game_id linking.
```sql
CREATE TABLE picks (
    id INTEGER PRIMARY KEY,
    user_id INTEGER NOT NULL,
    week_id INTEGER NOT NULL,
    team TEXT NOT NULL,
    player_name TEXT NOT NULL,
    odds REAL,
    theoretical_return REAL,
    game_id TEXT,  -- Links to NFL schedule (e.g., "2025_01_DAL_PHI")
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (week_id) REFERENCES weeks(id),
    UNIQUE(user_id, week_id, team, player_name)
);
```

#### `results`
Game outcomes and ROI calculations.
```sql
CREATE TABLE results (
    id INTEGER PRIMARY KEY,
    pick_id INTEGER NOT NULL UNIQUE,
    actual_scorer TEXT,
    is_correct BOOLEAN,
    actual_return REAL,
    FOREIGN KEY (pick_id) REFERENCES picks(id)
);
```

---

## 6. Key Features & Workflows

### Admin Workflows

**1. Import Picks from CSV**
```
Upload CSV (Home, Visitor, Player, Odds)
  ↓
Normalize team names via TEAM_ABBR_MAP
  ↓
Match teams to game_id from schedule
  ↓
Create users, weeks, picks, store game_id
  ↓
Display import summary with toast
```

**2. Grade Picks Automatically**
```
Select Season, Week, Game, Player filters
  ↓
Fetch ungraded picks with game_ids
  ↓
Load first TD data from PBP via get_first_td_map()
  ↓
Fuzzy match pick player vs actual TD scorer
  ↓
Display editable table with Match status
  ↓
Bulk grade: matches get theoretical_return, misses get -1.00
  ↓
Store results in database, display summary
```

**3. Edit Picks Before Grading**
```
Grade Picks table shows:
  - Player Pick, Game Date, Game (EDITABLE with dropdowns)
  - Detected First TD, Match status (READ-ONLY, auto-calculated)
  ↓
Edit pick data and click "Save & Recalculate"
  ↓
System recalculates game_id lookup and name matching
  ↓
Updates preview table with new Match/Result
```

### Public Workflows

**1. View Leaderboard**
```
Load leaderboard (members, wins, losses, avg_odds, theo_return, roi_efficiency)
  ↓
Sort by ROI or other metrics
  ↓
Expand member to see detail stats
```

**2. Browse Week Picks**
```
Select week
  ↓
Show all members' picks for that week
  ↓
Display Odds, Theo Return, Result, Actual Return  end_date DATE,
    UNIQUE(season, week_number)
);
```

#### `picks`
Individual user predictions for each week.
```sql
CREATE TABLE picks (
    pick_id INTEGER PRIMARY KEY AUTOINCREMENT,
    week_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    player_name TEXT NOT NULL,
    team TEXT NOT NULL,
    position TEXT,
    odds REAL,
    outcome TEXT,  -- 'pending', 'correct', 'incorrect'
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (week_id) REFERENCES weeks(week_id),
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);
```

#### `results`
Game outcomes and ROI calculations.
```sql
CREATE TABLE results (
    result_id INTEGER PRIMARY KEY AUTOINCREMENT,
    pick_id INTEGER NOT NULL UNIQUE,
    game_date DATE,
    td_scorer_name TEXT,
    td_scorer_team TEXT,
    result TEXT,  -- 'correct', 'incorrect'
    theoretical_return REAL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (pick_id) REFERENCES picks(pick_id)
);
```

---

## 7. Code Quality & Technical Highlights

### Data Accuracy
- **Game ID Matching**: Home/Visitor teams matched to NFL schedule via TEAM_ABBR_MAP
- **PBP Integration**: First TDs loaded from official play-by-play data
- **Fuzzy Matching**: Player names matched with suffix removal and initial comparison
- **Duplicate Prevention**: Unique constraint on (user_id, week_id, team, player_name)

### Performance
- **Caching**: 5-minute TTL on PBP, roster, schedule data
- **Efficient Queries**: Indexed lookups, aggregation at database level
- **Lazy Loading**: Data loaded on demand, not at startup

### Reliability
- **Cascading Deletes**: User/week deletion removes related picks/results
- **Transaction Safety**: Explicit commits, rollback on error
- **Error Handling**: Try-catch around external API calls
- **Schema Migration**: ensure_game_id_column() for safe updates

### Code Statistics
- **1,800+ lines** of new/updated code
- **95+ functions** across database, data_processor, admin
- **5 database tables** with foreign keys
- **12 UI tabs** (6 admin + 6 public)
- **3 caching strategies** with 5-min TTL

---

## 8. Deployment

### Local Development
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run src/app.py
```

### Cloud Deployment
See [DEPLOYMENT.md](DEPLOYMENT.md) for Streamlit Cloud setup.

### Environment Variables
Required for production:
- `odds_api_key` - API key for betting odds data (stored in Streamlit secrets)

---

## 9. Testing Strategy

### Current Tests
- Integration tests for CSV import with team matching
- Manual testing of Grade Picks tab with PBP auto-detection
- Name matching fuzzy logic validation
- Leaderboard calculations and ROI metrics

### Running Tests
```bash
python -m pytest tests/
```

---

## 10. Next Steps (Phase 2b)

1. **Database Reset** - Drop existing DB, fresh import with Home/Visitor CSV
2. **Point System** - Add First TD vs Anytime TD scoring logic
3. **Code Refactoring** - Extract utils modules (admin_utils, grading_logic, team_resolution)
4. **Analytics** - ROI trends and matchup analysis

---

## 11. Support & Contact

For questions or issues:
- Check [README.md](README.md) for quick start
- Review [ROADMAP.md](ROADMAP.md) for planned features
- See [TODO.md](TODO.md) for current work items
- See [PHASE1_COMPLETE.md](PHASE1_COMPLETE.md) for Phase 1 details

---

## 12. License

MIT License - See repository for details.
