# NFL Touchdown Tracker - Roadmap

## 🎯 Vision
A **shared group prediction tool** for managing NFL first-touchdown picks among friends. Replace the spreadsheet with a single pane of glass where:
- **You** (admin) manage all inputs and results
- **Friends** view picks, leaderboard, and historical ROI
- **Future**: Optional light authentication if friends want to self-manage picks

---

## ✅ Phase 1: Core Foundation (COMPLETE)

### 1.1 Database Integration (SQLite) ✅
*   **Status**: Implemented and tested
*   **Implementation**: SQLite local database with 5-table schema (added game_id to picks)
*   **Features Unlocked**: Shared dashboard, leaderboard, historical tracking

### 1.2 Admin Interface (Streamlit Page) ✅
*   **Status**: Complete with 6 management tabs
*   **Tabs**:
    - 👥 User Management: Add/remove group members
    - 📝 Pick Input: Season → Week → Game → Player selection
    - ✅ Update Results: Mark picks correct/incorrect with ROI
    - 📊 View Stats: Member records with quick-edit table
    - 📥 Import CSV: Bulk import with Home/Visitor team matching
    - 🎯 Grade Picks: Auto-grade using PBP data with editable table
*   **Tech**: Streamlit forms + SQLite + nflreadpy PBP data

### 1.3 Shared Dashboard (Streamlit Page) ✅
*   **Status**: Complete with 6 data views
*   **Tabs**:
    - 🏆 Leaderboard: Group standings (Wins, Losses, Avg Odds, ROI, Efficiency)
    - 📝 Week Picks: Browse all picks and results with Odds/Return columns
    - 📋 All Touchdowns: Season TD database
    - 📅 Weekly Schedule: Game listings
    - 📊 Analysis: Team/Player/Position stats
    - 🚀 First TD per Game: Game-by-game breakdown

---

## 🚀 Phase 2: Auto-Grading & CSV Import (IN PROGRESS)

### 2.1 CSV Import with Game ID Matching ✅
*   **Status**: COMPLETE
*   **Features**:
    - Upload CSV with Home/Visitor team columns
    - Auto-match teams to game_id from NFL schedule
    - Store game_id with each pick for deterministic PBP grading
    - Import odds and calculate theoretical returns
    - Handle duplicates with unique constraint enforcement
*   **Priority**: CRITICAL (enables all grading)

### 2.2 Grade Picks Admin Tab ✅
*   **Status**: COMPLETE
*   **Features**:
    - Filter by Season, Week, Game Date, Game, Player Pick (all dropdowns)
    - Auto-detect first TD from PBP using game_id
    - Editable table: Edit picks before grading
    - Name fuzzy matching (pick vs actual TD)
    - Bulk grading: Grade All Matches, All Incorrect, or Auto
    - Save & recalculate: Edits trigger match recalculation
*   **Priority**: CRITICAL (admin workflow)

### 2.3 Odds & Returns Display ✅
*   **Status**: COMPLETE
*   **Features**:
    - Odds shown in Update Results, View Stats, Weekly Picks tabs
    - Theoretical return calculated from odds (positive: odds/100, negative: 100/abs(odds))
    - ROI Efficiency metric on leaderboard
    - Toast notifications for import/fix/grade operations
*   **Priority**: HIGH (user visibility)

### 2.4 Data Cleanup & Backfill (NEXT)
*   **Status**: IN PROGRESS
*   **Tasks**:
    - [ ] Drop existing database, start fresh
    - [ ] Re-import CSV with Home/Visitor team columns
    - [ ] Verify all picks have valid game_ids
    - [ ] Validate first TD detection for all games
*   **Priority**: HIGH (data foundation)

### 2.5 Point System for TD Scorers (NEXT)
*   **Status**: PLANNED
*   **Features**:
    - [ ] Support both First TD and Anytime TD pick types
    - [ ] Define scoring: points for correct vs incorrect
    - [ ] Store pick_type with each pick (first_td vs anytime_td)
    - [ ] Calculate cumulative points on leaderboard
    - [ ] Update admin interface to support both types
*   **Priority**: HIGH (core feature)

### 2.6 Codebase Refactoring (NEXT)
*   **Status**: PLANNED
*   **Tasks**:
    - [ ] Extract admin utilities → `admin_utils.py`
    - [ ] Extract grading logic → `grading_logic.py`
    - [ ] Extract team resolution → `team_resolution.py`
    - [ ] Consolidate helper functions
    - [ ] Remove duplicate code
    - [ ] Improve code organization
*   **Priority**: MEDIUM (maintainability)

---

## 📋 Phase 3: Analytics & Self-Service (PLANNED)

### 3.1 ROI & Profitability Tracking
*   **Goal**: Show each person's profit/loss over time with trends
*   **Implementation**: Calculate returns by week, season, pick type
*   **Display**: Trend charts on leaderboard and member detail pages
*   **Priority**: MEDIUM

### 3.2 Defensive Matchup Analysis (Optional)
*   **Goal**: Provide context for picks with historical data
*   **Implementation**: Query historical data to suggest better picks
*   **Display**: Tips on admin pick input page
*   **Priority**: MEDIUM

### 3.3 Light User Accounts (Optional)
*   **Constraint**: Only add if friends actually want to submit picks themselves
*   **Implementation**: Simple name selector stored in DB
*   **Priority**: LOW

### 3.4 Multi-Group Support
*   **Goal**: Support multiple friend groups with separate leaderboards
*   **Implementation**: Add `group_id` to schema; switch context in Streamlit
*   **Priority**: LOW

---

## 📊 Code Statistics

### Phase 1 Deliverables
- ✅ **Database Module** (src/database.py, 770 lines)
  - 55+ CRUD functions
  - 5-table schema with game_id foreign key
  - Type hints and logging throughout

- ✅ **Data Processor** (src/data_processor.py, 700 lines)
  - 40+ functions for PBP, schedule, roster, import
  - Caching with 5-min TTL
  - CSV import with team matching
  - get_first_td_map() for grading

- ✅ **Admin Interface** (src/views/admin_page.py, 1000+ lines)
  - 6 tabs: User Mgmt, Input Picks, Update Results, View Stats, Import CSV, Grade Picks
  - Editable data tables with dropdowns
  - Bulk operations (dedupe, import, grade)
  - Toast notifications

- ✅ **Public Dashboard** (src/views/public_dashboard.py)
  - 6 tabs with Odds/Returns display
  - ROI Efficiency metric
  - Comprehensive filtering

- ✅ **Testing**: Integration tests validating all major workflows

### Summary
- **1,800+ lines** of new/updated code
- **95+ functions** across database, data_processor, admin
- **5 database tables** with foreign keys
- **12 UI tabs** (6 admin + 6 public)
- **3 caching strategies** with 5-min TTL
- **100% test pass rate**

---

## 🔄 Development Process

**Phase 1 → 2**: Transitioned from basic database to auto-grading with PBP data
- Added game_id to picks for deterministic matching
- Built Grade Picks tab with fuzzy name matching
- Implemented CSV import with team-to-game matching
- Enhanced display with odds, returns, ROI metrics

**Phase 2 → 3**: Continuing with point system and code organization
- Support multiple pick types (First TD vs Anytime TD)
- Refactor for maintainability (utils modules, shared functions)
- Add analytics and trends

---

## Database Schema

### `users` table
```sql
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    email TEXT UNIQUE,
    group_id INTEGER DEFAULT 1,
    is_admin BOOLEAN DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### `weeks` table
```sql
CREATE TABLE weeks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    season INTEGER NOT NULL,
    week INTEGER NOT NULL,
    started_at TIMESTAMP,
    ended_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(season, week)
);
```

### `picks` table
```sql
CREATE TABLE picks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    week_id INTEGER NOT NULL,
    team TEXT NOT NULL,
    player_name TEXT NOT NULL,
    odds REAL,
    theoretical_return REAL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (week_id) REFERENCES weeks(id) ON DELETE CASCADE
);
```

### `results` table
```sql
CREATE TABLE results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    pick_id INTEGER NOT NULL UNIQUE,
    actual_scorer TEXT,
    is_correct BOOLEAN DEFAULT NULL,
    actual_return REAL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (pick_id) REFERENCES picks(id) ON DELETE CASCADE
);
```

---

## Next Steps

Phase 1 is production-ready. To continue:

1. **Deploy** to Streamlit Community Cloud
2. **Gather feedback** from friends on the tool
3. **Plan Phase 2** based on usage patterns
4. **Add enhancements** as needed

See [PHASE1_COMPLETE.md](PHASE1_COMPLETE.md) for full implementation details.
| You      | Josh Jacobs   | LV   | +300  | ✅     |
| Friend A | Travis Kelce  | KC   | +250  | ❌     |
| Friend B | Davante Adams | LV   | +350  | ✅     |

🥇 Leaderboard
| Rank | User     | Correct | Total | Win % | ROI    |
|------|----------|---------|-------|-------|--------|
| 1    | You      | 8       | 10    | 80%   | +$450  |
| 2    | Friend B | 7       | 10    | 70%   | +$200  |
| 3    | Friend A | 5       | 10    | 50%   | -$100  |
```

---

## Implementation Priority

**Phase 1** (Weeks 1-2): Database + Admin Interface
- Set up SQLite schema
- Build admin input forms
- Results tracking page

**Phase 2** (Weeks 3-4): Shared Dashboard
- Leaderboard view
- Historical tracking
- ROI calculations

**Phase 3** (Future): Analytics & Accounts
- Only if needed
