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
*   **Implementation**: SQLite local database with complete schema (4 tables)
*   **Features Unlocked**: Shared dashboard, leaderboard, historical tracking

### 1.2 Admin Interface (Streamlit Page) ✅
*   **Status**: Complete with 4 management tabs
*   **Tabs**:
    - 👥 User Management: Add/remove group members
    - 📝 Pick Input: Season → Week → Game → Player selection
    - ✅ Results Tracking: Mark picks correct/incorrect with ROI
    - 📊 Statistics: View member win/loss records
*   **Tech**: Streamlit forms + SQLite

### 1.3 Shared Dashboard (Streamlit Page) ✅
*   **Status**: Complete with 6 data views
*   **Tabs**:
    - 🏆 Leaderboard: Group standings (wins, losses, ROI)
    - 📝 Week Picks: Browse all picks and results
    - 📋 All Touchdowns: Season TD database
    - 📅 Weekly Schedule: Game listings
    - 📊 Analysis: Team/Player/Position stats
    - 🚀 First TD per Game: Game-by-game breakdown

---

## 🚀 Phase 2: Enhanced Analytics (Planned)

### 2.1 ROI & Profitability Tracking
*   **Goal**: Show each person's profit/loss over time with trends
*   **Implementation**: Calculate returns based on odds and outcomes
*   **Priority**: MEDIUM

### 2.2 Defensive Matchup Analysis (Optional)
*   **Goal**: Provide context for picks with historical data
*   **Implementation**: Query historical data to suggest better picks
*   **Priority**: MEDIUM

---

## 📋 Phase 3: User Experience (Planned)

### 3.1 Light User Accounts (Optional)
*   **Constraint**: Only add if friends actually want to submit picks themselves
*   **Implementation**: Simple name selector stored in DB
*   **Priority**: LOW

### 3.2 Multi-Group Support
*   **Goal**: Support multiple friend groups with separate leaderboards
*   **Implementation**: Add `group_id` to schema; switch context in Streamlit
*   **Priority**: LOW

---

## 📊 Implementation Summary

### Phase 1 Deliverables
- ✅ **Database Module** (src/database.py, 550 lines)
  - 50+ CRUD functions
  - 4-table schema with foreign keys
  - Type hints and logging throughout

- ✅ **Admin Interface** (src/pages/admin_page.py, 4 tabs)
  - User management with add/delete
  - Pick input form
  - Result tracking interface
  - Statistics display

- ✅ **Public Dashboard** (src/pages/public_dashboard.py, 6 tabs)
  - Leaderboard with group standings
  - Week picks viewer
  - All remaining original tabs

- ✅ **Test Suite** (test_phase1.py)
  - 8 comprehensive integration tests
  - All features validated
  - Data integrity verified

### Code Statistics
- **1,140 lines** of new code
- **50+ database functions**
- **4 database tables**
- **10 total tabs** (4 admin + 6 public)
- **8 test suites** - 100% pass rate

---

## Database Schema (Phase 1)

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
