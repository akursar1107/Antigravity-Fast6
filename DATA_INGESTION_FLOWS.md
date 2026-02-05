# Data Ingestion Flows

## Current State (Manual, Error-Prone)

```
┌─────────────────────────────────────────────────────────────────┐
│                     USER CREATES PICK                           │
│  pick = {user_id, week_id, team, player_name, odds}             │
└──────────────────────┬──────────────────────────────────────────┘
                       │
                       ├─→ INSERT INTO picks (...)
                       │
                       └─→ ❌ NO AUTO-POSITION LOOKUP
                           ❌ NO AUTO-PLAYER_STATS CREATION
                           ❌ MANUAL SCRIPT REQUIRED LATER

        DAYS LATER...

┌─────────────────────────────────────────────────────────────────┐
│              MANUAL PYTHON SCRIPT (Error-prone)                 │
│  python fix_positions.py  # Ad-hoc, not automated              │
│  python populate_stats.py  # Requires SSH/access                │
│  python dedupe_picks.py    # Fixes duplicates manually          │
└──────────────────────────────────────────────────────────────────┘
                       │
                       ├─→ UPDATE player_stats SET position='WR'
                       │
                       └─→ INSERT INTO player_stats (...)

        WEEKS LATER...

┌─────────────────────────────────────────────────────────────────┐
│           ADMIN GRADES PICKS (Manual result entry)              │
│  INSERT INTO results (pick_id, actual_scorer, is_correct)       │
└──────────────────────────────────────────────────────────────────┘
                       │
                       ├─→ ❌ NO AUTO-FIRST_TD_UPDATE
                       │   ❌ LEADERBOARD STALE
                       │   ❌ ANOTHER SCRIPT NEEDED

        DAYS LATER...

┌─────────────────────────────────────────────────────────────────┐
│           DASHBOARD QUERY (Slow, wrong data)                    │
│  SELECT * FROM player_stats WHERE position='WR'                 │
│  → May be missing new picks (not yet processed)                 │
│  → May show old First TD counts                                 │
└──────────────────────────────────────────────────────────────────┘

PROBLEMS:
❌ Position unknown until manual enrichment
❌ First TD counts don't update in real-time
❌ Player stats missing until scripts run
❌ No referential integrity
❌ Duplicate picks possible
❌ Query performance degrades as data grows
```

---

## Proposed State (Automated, Event-Driven)

```
┌─────────────────────────────────────────────────────────────────┐
│                    APP STARTUP (5 seconds)                      │
│  - Load rosters from nflreadpy                                  │
│  - Populate rosters table (100+ players per season)             │
│  - Set up triggers for automatic updates                        │
│  → ✅ Single source of truth for positions                      │
└──────────────────────────────────────────────────────────────────┘
                       │
        ┌──────────────┴───────────────┐
        │                              │
        v                              v
   ┌────────────────┐    ┌────────────────┐
   │  rosters       │    │  games         │
   │  (players)     │    │  (schedule)    │
   │  position=QB   │    │  game_id       │
   │  position=WR   │    │  home_team     │
   └────────────────┘    └────────────────┘

         MOMENT: USER CREATES PICK
┌─────────────────────────────────────────────────────────────────┐
│                    CREATE_PICK(user, week, player)              │
└──────────────────────────────────────────────────────────────────┘
        │
        ├─1─→ INSERT INTO picks (user_id, week_id, player_name, ...)
        │      (UNIQUE constraint prevents duplicates)
        │
        ├─2─→ LOOKUP rosters.position WHERE player_name = 'Mahomes'
        │      → Returns 'QB'
        │
        └─3─→ ENSURE_PLAYER_STATS(player_name, season, team, position='QB')
               (auto-create if doesn't exist)

        ✅ Position assigned immediately
        ✅ Player stats created in one transaction
        ✅ No manual script needed

         MOMENT: ADMIN GRADES PICK
┌─────────────────────────────────────────────────────────────────┐
│              GRADE_PICK(pick_id, is_correct=True)               │
└──────────────────────────────────────────────────────────────────┘
        │
        ├─1─→ INSERT INTO results (pick_id, is_correct, actual_scorer)
        │
        └─2─→ TRIGGER: update_player_stats_on_result_insert
               IF is_correct = 1 THEN
                 UPDATE player_stats SET first_td_count = first_td_count + 1
                 WHERE player_name = (SELECT player_name FROM picks WHERE id=pick_id)

        ✅ First TD count updated immediately
        ✅ Leaderboard reflects change instantly
        ✅ Caches invalidated automatically

         MOMENT: DASHBOARD QUERY
┌─────────────────────────────────────────────────────────────────┐
│           GET_WR_LEADERS(season, week) [<100ms]                │
│  SELECT p.*, r.position FROM player_stats p                     │
│  JOIN rosters r ON (p.player_name = r.player_name ...)          │
│  WHERE r.position = 'WR' ORDER BY first_td_count DESC           │
│  [INDEXED by position]                                          │
└──────────────────────────────────────────────────────────────────┘

        ✅ Always has latest data
        ✅ Fast queries (indexed by position)
        ✅ Correct player positions
        ✅ Accurate First TD counts

         DAILY: NIGHTLY SYNC (Off-hours)
┌─────────────────────────────────────────────────────────────────┐
│              2 AM: NIGHTLY_DATA_SYNC()                          │
│  1. Sync rosters (catch mid-season trades/position changes)     │
│  2. Sync games (get updated scores, game status)                │
│  3. Sync market odds (Polymarket prices)                        │
│  4. Run data quality checks                                     │
│     - Verify all players have positions                         │
│     - Check for orphaned records                                │
│     - Alert on anomalies                                        │
└──────────────────────────────────────────────────────────────────┘

BENEFITS:
✅ Positions populated automatically
✅ First TD counts real-time
✅ Player stats always current
✅ Referential integrity enforced
✅ No duplicate picks possible
✅ Query performance optimized
✅ Data quality monitored nightly
```

---

## Data Quality Pipeline

```
INPUT:
  - nflreadpy (NFL rosters, play-by-play, schedule)
  - User picks (CSV import, UI form)
  - Grading decisions (admin)
  - Market APIs (Polymarket, Kalshi) [optional]

VALIDATION LAYER:
  ┌─────────────────────────────────────────┐
  │ Input Validation                        │
  ├─────────────────────────────────────────┤
  │ 1. Player name in rosters?              │
  │ 2. Team is valid NFL team?              │
  │ 3. Game exists in schedule?             │
  │ 4. Pick not duplicate?                  │
  │ 5. Odds format valid?                   │
  └─────────────────────────────────────────┘
            │
            v
  ┌─────────────────────────────────────────┐
  │ Transformation Layer                    │
  ├─────────────────────────────────────────┤
  │ 1. Match player name to full_name       │
  │    (Mahomes → Patrick Mahomes)          │
  │ 2. Look up position from rosters        │
  │ 3. Calculate game_id from schedule      │
  │ 4. Normalize team abbreviation          │
  │ 5. Calculate theoretical return         │
  └─────────────────────────────────────────┘
            │
            v
  ┌─────────────────────────────────────────┐
  │ Database Layer                          │
  ├─────────────────────────────────────────┤
  │ 1. Enforce unique constraints           │
  │ 2. Validate foreign keys                │
  │ 3. Auto-trigger player_stats updates    │
  │ 4. Maintain referential integrity       │
  │ 5. Log all changes                      │
  └─────────────────────────────────────────┘
            │
            v
  ┌─────────────────────────────────────────┐
  │ Quality Checks (Nightly)                │
  ├─────────────────────────────────────────┤
  │ 1. All picks have game_id?              │
  │ 2. All players have position?           │
  │ 3. No orphaned results?                 │
  │ 4. First TD counts match graded picks?  │
  │ 5. Team ratings calculated?             │
  └─────────────────────────────────────────┘
            │
            v
        OUTPUT:
          - Clean, normalized data
          - Quality report
          - Alerts on anomalies

FAILURE HANDLING:
  ❌ Validation fails → Reject pick, show user error
  ❌ Transform fails → Move to quarantine table for manual review
  ❌ DB constraint violates → Log error, don't insert
  ❌ Quality check fails → Alert admin to investigate
```

---

## Service Responsibilities

### data_sync.roster_ingestion
- Load NFL rosters from nflreadpy on app startup
- Upsert into rosters table (idempotent)
- Handle mid-season position changes
- Cache for 24 hours (refresh on demand)

### database.picks_repository
- Create pick with auto-position lookup
- Create player_stats if not exists
- Validate unique constraint
- Link pick to game via game_id

### database.results_repository
- Grade result (insert, update, or delete)
- Trigger automatic player_stats updates via database trigger
- Update first_td_count (increment/decrement)
- Invalidate leaderboard cache

### services.analytics.player_stats
- Query player stats with position filtering
- Calculate rolling statistics
- Generate leaderboard rankings
- Use indexed queries for performance

### services.data_quality
- Run nightly validation suite
- Detect orphaned records
- Alert on data anomalies
- Generate audit report

---

## Database Triggers Reference

### Trigger 1: Update player_stats on result insert

```sql
CREATE TRIGGER update_player_stats_on_result_insert
AFTER INSERT ON results
FOR EACH ROW
WHEN NEW.is_correct = 1
BEGIN
    -- Get pick details
    -- Update or insert player_stats with +1 first_td_count
END;
```

**Purpose**: Automatically increment first_td_count when a pick is graded as correct

**Called by**: INSERT INTO results (...)

**Side effects**: Invalidates leaderboard cache


### Trigger 2: Update player_stats on result delete

```sql
CREATE TRIGGER update_player_stats_on_result_delete
AFTER DELETE ON results
FOR EACH ROW
WHEN OLD.is_correct = 1
BEGIN
    -- Get pick details
    -- Update player_stats with -1 first_td_count
    -- Delete player_stats if first_td_count becomes 0
END;
```

**Purpose**: Decrement first_td_count if a grading is reversed

**Called by**: DELETE FROM results WHERE ...

**Side effects**: Invalidates leaderboard cache


### Trigger 3: Cascade delete picks when user deleted

```sql
-- ALREADY EXISTS in current schema
ALTER TABLE picks 
ADD CONSTRAINT fk_picks_users 
FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE;
```

**Purpose**: Clean up picks if user is deleted

**Effect**: Deletes all picks → triggers player_stats updates


---

## Migration Execution Plan

Execute migrations in this order (critical!):

### Phase A: Create Reference Tables (Safe, non-breaking)
1. **v9**: CREATE TABLE games (new table)
2. **v10**: CREATE TABLE rosters (new table)
3. **v11**: CREATE TABLE pick_market_odds (new table)

### Phase B: Add Constraints & Indexes (Add, don't remove)
4. **v12**: ALTER TABLE picks ADD UNIQUE(user_id, week_id, player_name)
5. **v13**: ALTER TABLE picks ADD FOREIGN KEY(game_id) REFERENCES games(id)
6. **v14**: CREATE INDEXes on all tables

### Phase C: Add Automation (Triggers)
7. **v15**: CREATE TRIGGER update_player_stats_on_result_insert
8. **v16**: CREATE TRIGGER update_player_stats_on_result_delete

### Phase D: Backfill Data (Backfill once, triggers maintain)
9. **Manual**: Populate rosters table via roster_ingestion.sync_rosters()
10. **Manual**: Populate games table for current season
11. **Manual**: Populate player_stats positions from rosters

### Rollback Plan (Executed in reverse)
- Drop triggers (Phase C)
- Drop constraints & indexes (Phase B)
- Delete data from new tables (Phase A)
- Restore from backup if needed
