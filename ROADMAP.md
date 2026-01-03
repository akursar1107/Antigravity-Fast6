# NFL Touchdown Tracker - Future Roadmap

## 🎯 Vision
A **shared group prediction tool** for managing NFL first-touchdown picks among friends. Replace the spreadsheet with a single pane of glass where:
- **You** (admin) manage all inputs and results
- **Friends** view picks, leaderboard, and historical ROI
- **Future**: Optional light authentication if friends want to self-manage picks

---

## Phase 1: Core Foundation (Priority: HIGH)

### 1.1 Database Integration (SQLite)
*   **Goal**: Persist picks, results, and group standings.
*   **Implementation**: SQLite local database with the schema below.
*   **Feature Unlock**: Shared dashboard, leaderboard, historical tracking.

### 1.2 Admin Interface (Streamlit Page)
*   **Goal**: Easy way for you to manage picks and results.
*   **Implementation**: Admin-only page with forms to:
    - Create/edit weekly picks (player, team, odds, prediction)
    - Update game results and outcomes
    - Manage group members
*   **Tech**: Streamlit forms + SQLite updates

### 1.3 Shared Dashboard (Streamlit Page)
*   **Goal**: Friends see picks, results, and leaderboard.
*   **Implementation**: Public page showing:
    - This week's picks (odds, player, prediction)
    - Leaderboard (by correct picks or ROI)
    - Historical results and win rate

---

## Phase 2: Enhanced Analytics (Priority: MEDIUM)

### 2.1 ROI & Profitability Tracking
*   **Goal**: Show each person's theoretical profit/loss over time.
*   **Implementation**: Calculate returns based on odds and outcomes.

### 2.2 Defensive Matchup Analysis (Optional)
*   **Goal**: Provide context for picks (e.g., "This RB scores against weak defenses 65% of the time").
*   **Implementation**: Query historical data to suggest better picks.

---

## Phase 3: User Experience (Priority: LOW)

### 3.1 Light User Accounts (Future)
*   **Constraint**: Only add if friends actually want to submit picks themselves.
*   **Implementation**: Simple name selector (no password auth needed) stored in DB.
*   **Benefit**: Track individual picks and let them see "their" predictions.

### 3.2 Multi-Group Support
*   **Goal**: Support multiple friend groups with separate leaderboards.
*   **Implementation**: Add `group_id` to schema; switch context in Streamlit.

---

## Database Schema

### `users` table
```sql
CREATE TABLE users (
    user_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### `weeks` table
```sql
CREATE TABLE weeks (
    week_id INTEGER PRIMARY KEY AUTOINCREMENT,
    season INTEGER NOT NULL,
    week_number INTEGER NOT NULL,
    start_date DATE,
    end_date DATE,
    UNIQUE(season, week_number)
);
```

### `picks` table
```sql
CREATE TABLE picks (
    pick_id INTEGER PRIMARY KEY AUTOINCREMENT,
    week_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    player_name TEXT NOT NULL,
    team TEXT NOT NULL,
    position TEXT,
    odds REAL,  -- e.g., +400
    outcome TEXT,  -- 'pending', 'correct', 'incorrect'
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (week_id) REFERENCES weeks(week_id),
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);
```

### `results` table
```sql
CREATE TABLE results (
    result_id INTEGER PRIMARY KEY AUTOINCREMENT,
    pick_id INTEGER NOT NULL UNIQUE,
    game_date DATE,
    td_scorer_name TEXT,  -- Who actually scored first TD
    td_scorer_team TEXT,
    result TEXT,  -- 'correct', 'incorrect'
    theoretical_return REAL,  -- e.g., 4.00 for +400 odds
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (pick_id) REFERENCES picks(pick_id)
);
```

---

## Admin Interface (Streamlit Pages)

### Page: `admin.py`
```
🔐 ADMIN DASHBOARD

📋 Manage Picks
  - Select Week
  - Table of current picks (editable)
  - Form to add new pick:
    * User dropdown
    * Player name
    * Team
    * Odds input
    * Submit button

✅ Update Results
  - Select Week
  - Form to mark picks correct/incorrect
  - Show actual TD scorer for reference
  - Mark outcome + auto-calculate return

👥 Manage Users
  - List all users
  - Add/remove users from group
```

### Page: `dashboard.py` (Public)
```
🏈 NFL TD Tracker - Week 5 Results

📊 This Week's Picks
| User     | Player        | Team | Odds  | Result |
|----------|---------------|------|-------|--------|
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
