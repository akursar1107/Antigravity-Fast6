# Data Ingestion & Schema Improvement Plan

**Status**: Draft for Phase 11 | **Priority**: CRITICAL | **Effort**: 3-4 days

---

## Executive Summary

The current schema lacks integrity constraints, automated pipelines, and proper normalization. Players must manually run scripts to populate analytics data, position information is incomplete, and graded picks don't automatically update leaderboards.

**Goals:**
1. ✅ Ensure data integrity with FK constraints & unique indexes
2. ✅ Automate player stats & position enrichment
3. ✅ Create event-driven updates (grade pick → update leaderboard)
4. ✅ Support Polymarket/Kalshi integration
5. ✅ Optimize query performance

---

## Current State Analysis

### Schema Issues

#### ❌ Missing Primary/Foreign Key Relationships
```
Current:
  picks.game_id (TEXT) → points to NFL games, but no games table
  picks.user_id (INT) → users.id ✓ (has FK)
  results.pick_id (INT) → picks.id ✓ (has FK but NO CASCADE)
  
Problem:
  - Can delete games without knowing which picks are affected
  - Can delete users and orphan their picks
  - No referential integrity enforcement
```

#### ❌ Missing Unique Constraints
```
Current:
  CREATE TABLE picks (
    id INTEGER PRIMARY KEY,
    user_id INTEGER NOT NULL,
    week_id INTEGER NOT NULL,
    player_name TEXT NOT NULL,
    ...
  )

Problem:
  - Duplicate picks allowed (same user, week, player)
  - We've already seen this: 75 picks but many are duplicates
  - Manual deduplication required (see BUGFIX_WEEK_BYTES_DUPLICATES.md)

Solution:
  ALTER TABLE picks ADD UNIQUE (user_id, week_id, player_name)
```

#### ❌ Missing Indexes
```
Current:
  Only implicit indexes on PRIMARY KEYs
  
Hot Queries Missing Indexes:
  - SELECT * FROM player_stats WHERE position = 'WR' AND team = 'KC'
  - SELECT * FROM picks WHERE user_id = 1 AND week_id = 5
  - SELECT * FROM results WHERE pick_id IN (...)
  - SELECT * FROM team_ratings WHERE team = 'ARI' ORDER BY week DESC
  
Performance Impact:
  - Full table scans for common analytics queries
  - Player performance queries scan all 485 players every time
```

#### ❌ Incomplete Position/Roster Data
```
Current:
  player_stats table has position column, but:
  - 118 of 485 players have position="Unknown"
  - Position data not sourced from NFL rosters
  - No automated position enrichment on new players
  
Root Cause:
  - Script manually created POSITION_MAP with 24 known players
  - Rest require nflreadpy roster data lookup
  
Missing:
  - No ETL step to backfill positions from rosters
  - No on-insert trigger to auto-assign position for new players
```

#### ❌ Empty Market Tables
```
Current:
  - market_odds: 0 rows (designed for Polymarket/Kalshi)
  - market_outcomes: 0 rows (designed for market resolution)
  - kickoff_decisions: 0 rows (designed for kickoff decisions)

Problem:
  - Schema exists but no ingestion pipeline
  - Prediction market features can't work
  - Code written to use these tables but never populated

Status:
  - polymarket_api.py: Implemented but unused
  - kalshi_api.py: Implemented but unused
  - No services calling these APIs
```

#### ❌ No Automated First TD Calculation
```
Current:
  - Manual SQL: SELECT player_name, COUNT(*) FROM results WHERE is_correct=1 GROUP BY player_name
  - Inline Python aggregation in scripts
  - First TD counts stale until re-run

Pipeline Missing:
  1. When result is graded → update player_stats.first_td_count
  2. When result is un-graded → decrement player_stats.first_td_count
  3. When player_stats changes → invalidate leaderboard cache
```

---

## Proposed Schema Changes

### 1. Add Games Table (Reference Table)

```sql
CREATE TABLE games (
    id TEXT PRIMARY KEY,  -- game_id from nflreadpy (e.g., "2025_01_KC_LV")
    season INTEGER NOT NULL,
    week INTEGER NOT NULL,
    game_date DATE NOT NULL,
    home_team TEXT NOT NULL,
    away_team TEXT NOT NULL,
    home_score INTEGER,
    away_score INTEGER,
    status TEXT CHECK(status IN ('scheduled', 'in_progress', 'final')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (season, week) REFERENCES weeks(season, week),
    UNIQUE(season, week, home_team, away_team)
);

CREATE INDEX idx_games_season_week ON games(season, week);
CREATE INDEX idx_games_teams ON games(home_team, away_team);
```

**Benefit**: Can query "all picks for games in week 3", detect game status changes, link market data to specific games.

### 2. Add Rosters Table (Reference Table)

```sql
CREATE TABLE rosters (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    season INTEGER NOT NULL,
    player_name TEXT NOT NULL,
    team TEXT NOT NULL,
    position TEXT NOT NULL,
    jersey_number INTEGER,
    nflreadpy_id TEXT UNIQUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (season) REFERENCES weeks(season),
    UNIQUE(season, player_name, team)
);

CREATE INDEX idx_rosters_team_position ON rosters(team, position);
CREATE INDEX idx_rosters_player_name ON rosters(player_name);
```

**Benefit**: Single source of truth for player positions; can auto-assign position when user picks player.

### 3. Fix Picks Table

```sql
-- ADD CONSTRAINTS
ALTER TABLE picks ADD CONSTRAINT unique_user_week_player 
    UNIQUE (user_id, week_id, player_name);

ALTER TABLE picks ADD CONSTRAINT fk_picks_games 
    FOREIGN KEY (game_id) REFERENCES games(id);

-- ADD INDEXES
CREATE INDEX idx_picks_user_week ON picks(user_id, week_id);
CREATE INDEX idx_picks_week_id ON picks(week_id);
CREATE INDEX idx_picks_game_id ON picks(game_id);
CREATE INDEX idx_picks_player_name ON picks(player_name);
```

**Benefit**: Prevents duplicate picks, enforces data integrity, speeds up common queries.

### 4. Fix Results Table

```sql
-- EXISTING but needs indexes
CREATE INDEX idx_results_pick_id ON results(pick_id);
CREATE INDEX idx_results_player_name ON results(player_name);
CREATE INDEX idx_results_is_correct ON results(is_correct);

-- ADD TRIGGER: Update player_stats when result is graded
CREATE TRIGGER update_player_stats_on_result_insert
AFTER INSERT ON results
FOR EACH ROW
WHEN NEW.is_correct = 1
BEGIN
    INSERT INTO player_stats (player_name, season, team, position, first_td_count)
    SELECT NEW.player_name, 
           (SELECT season FROM weeks WHERE id = (SELECT week_id FROM picks WHERE id = NEW.pick_id)),
           COALESCE((SELECT team FROM picks WHERE id = NEW.pick_id), 'Unknown'),
           'Unknown',  -- Will be updated by roster lookup
           1
    ON CONFLICT(player_name, season, team)
    DO UPDATE SET first_td_count = first_td_count + 1;
END;
```

**Benefit**: Automatic leaderboard updates; no manual re-runs needed.

### 5. Normalize Player Stats

```sql
-- Current issues:
-- - position="Unknown" for many players
-- - first_td_count calculated manually
-- - no link to rosters

-- New strategy:
ALTER TABLE player_stats ADD CONSTRAINT fk_player_stats_roster
    FOREIGN KEY (season, player_name, team) REFERENCES rosters(season, player_name, team);

CREATE INDEX idx_player_stats_position ON player_stats(position);
CREATE INDEX idx_player_stats_team_season ON player_stats(team, season);
```

**Benefit**: Position data normalized; can enforce referential integrity.

### 6. Enable Market Tables

```sql
-- market_odds table (mostly correct, just needs indexes)
CREATE INDEX idx_market_odds_game_player ON market_odds(game_id, player_name);
CREATE INDEX idx_market_odds_source_time ON market_odds(source, snapshot_time);

-- market_outcomes table (mostly correct, just needs indexes)
CREATE INDEX idx_market_outcomes_market_id ON market_outcomes(market_id);
CREATE INDEX idx_market_outcomes_resolution ON market_outcomes(resolution_time);

-- Add linking table: picks ↔ market_odds
CREATE TABLE IF NOT EXISTS pick_market_odds (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    pick_id INTEGER NOT NULL,
    market_id TEXT NOT NULL,
    source TEXT NOT NULL,
    market_price REAL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (pick_id) REFERENCES picks(id),
    UNIQUE(pick_id, market_id, source)
);
```

**Benefit**: Can link user picks to prediction markets, track market prices over time.

---

## Proposed Data Ingestion Pipeline

### Phase 1: Automated Roster Loading (on app startup)

```python
# services/data_sync/roster_ingestion.py
@st.cache_data(ttl=86400)  # Cache 24 hours
def sync_rosters(season: int) -> Dict[str, int]:
    """
    Load NFL rosters from nflreadpy and populate rosters table.
    Called on app startup for current season.
    """
    rosters = nfl.load_rosters(seasons=[season]).to_pandas()
    
    stats = {'inserted': 0, 'updated': 0, 'errors': 0}
    
    for _, player in rosters.iterrows():
        try:
            # Insert or update roster entry
            db.upsert_roster(
                season=season,
                player_name=player['full_name'],
                team=player['team'],
                position=player['position'],
                jersey=player['jersey_number'],
                nflreadpy_id=player['player_id']
            )
            stats['inserted'] += 1
        except Exception as e:
            logger.error(f"Error syncing {player['full_name']}: {e}")
            stats['errors'] += 1
    
    return stats
```

**When**: App startup for current season only (cache 24h)
**Input**: nflreadpy rosters
**Output**: rosters table with 100+ players per season

### Phase 2: On-Insert Position Assignment

```python
# Trigger: When user picks a player, auto-assign position
def create_pick(user_id, week_id, team, player_name, odds, game_id):
    # 1. Insert pick
    pick_id = db.add_pick(user_id, week_id, team, player_name, odds, game_id)
    
    # 2. Look up position from rosters table
    season = db.get_week_season(week_id)
    position = db.get_player_position(player_name, team, season)
    
    # 3. Create player_stats entry if doesn't exist
    db.ensure_player_stats(
        player_name=player_name,
        season=season,
        team=team,
        position=position or 'Unknown'
    )
    
    return pick_id
```

**When**: On each pick creation
**Input**: pick data + season lookup
**Output**: Auto-populated player_stats with correct position

### Phase 3: Automated First TD Updates

```python
# Trigger: When result is graded
def grade_result(pick_id, actual_scorer, is_correct):
    # 1. Insert result
    result_id = db.add_result(pick_id, actual_scorer, is_correct)
    
    # 2. If correct, update player_stats
    if is_correct:
        pick = db.get_pick(pick_id)
        week = db.get_week(pick['week_id'])
        db.increment_player_stat(
            player_name=pick['player_name'],
            season=week['season'],
            stat='first_td_count',
            increment=1
        )
        
        # 3. Invalidate leaderboard cache
        st.cache_data.clear()  # Or use more granular cache invalidation
    
    return result_id
```

**When**: After result is graded
**Input**: pick_id, grading result
**Output**: Updated first_td_count, invalidated caches

### Phase 4: Nightly Data Refresh

```python
# Scheduled job (e.g., Airflow, task scheduler)
def nightly_data_sync():
    """Run every night at 2 AM"""
    current_season = config.CURRENT_SEASON
    
    # 1. Sync rosters (in case roster changes occurred)
    sync_rosters(current_season)
    
    # 2. Sync games for current week
    sync_games(current_season)
    
    # 3. Sync market odds (if Polymarket/Kalshi enabled)
    if config.FEATURES['prediction_markets']:
        sync_market_odds(current_season)
    
    # 4. Validate data integrity
    run_data_quality_checks()
    
    logger.info("Nightly data sync complete")
```

**When**: Daily at 2 AM (off-hours)
**Input**: NFL data sources
**Output**: Updated rosters, games, market data; validation report

---

## Implementation Roadmap

### ✅ Step 1: Create Games & Rosters Tables (1 day)
- Create migration v9: Add games table
- Create migration v10: Add rosters table
- Add indexes and constraints

### ✅ Step 2: Fix Existing Tables (1 day)
- Create migration v11: Add unique constraints to picks
- Create migration v12: Add FK to games
- Create migration v13: Add indexes to all tables
- Create migration v14: Add triggers for player_stats updates

### ✅ Step 3: Build Ingestion Services (1 day)
- `services/data_sync/roster_ingestion.py`: Load rosters on startup
- `services/data_sync/game_sync.py`: Load games for current season
- `services/data_sync/market_sync.py`: Load market odds from APIs
- Update `app.py` to call sync on startup

### ✅ Step 4: Update Database Layer (1 day)
- Update `database/players.py` to handle position auto-assignment
- Update `database/results.py` to include trigger-based updates
- Add validation functions for data quality

### ✅ Step 5: Testing & Deployment (½ day)
- Run existing tests
- Add integration tests for new pipelines
- Deploy migrations in order
- Monitor data quality

---

## Database Entity Relationship Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                      Existing Core                          │
├─────────────────────────────────────────────────────────────┤
│  users ──┐
│   └──────├── picks ──┐
│  weeks ──┤         └──── results
│ (games) ─┘
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                    NEW (Proposed)                           │
├─────────────────────────────────────────────────────────────┤
│  ┌──────────────┐
│  │   rosters    │  (player positions from nflreadpy)
│  │  season PK   │
│  │  player_name │
│  │  team        │
│  │  position    │
│  └──────────────┘
│         ↑
│         │ FK
│         │
│  ┌──────────────────┐
│  │  player_stats    │  (user picks + actual TDs)
│  │  season          │
│  │  player_name     │───→ references rosters
│  │  position        │
│  │  first_td_count  │
│  └──────────────────┘
│
│  ┌──────────────┐
│  │    games     │  (NFL schedule reference)
│  │  id PK       │
│  │  season      │
│  │  week        │
│  │  home_team   │
│  │  away_team   │
│  │  status      │
│  └──────────────┘
│         ↑
│         │ FK
│         │
│  ┌──────────────────┐
│  │     picks        │  (user predictions)
│  │  user_id         │
│  │  week_id         │
│  │  game_id         │───→ references games
│  │  player_name     │
│  │  UNIQUE(user_id, week_id, player_name)
│  └──────────────────┘

Market Integration:
  ┌─────────────────┐
  │  market_odds    │ (Polymarket/Kalshi prices)
  │  game_id        │───→ references games
  │  player_name    │
  │  source         │
  │  snapshot_time  │
  └─────────────────┘
         ↑
         │
  ┌─────────────────────────┐
  │  pick_market_odds       │ (picks linked to markets)
  │  pick_id                │───→ references picks
  │  market_id              │
  └─────────────────────────┘
```

---

## Normalization Analysis

### Current State (Partially Denormalized)
```
player_stats has:
  - player_name (text) - REPEATS across rows
  - season (int) - REPEATS across rows
  - team (text) - REPEATS across rows
  - position (text) - DENORMALIZED (should come from rosters)
  - first_td_count (int) - CALCULATED from results table
  
Problem: Position data is duplicated, not normalized
Solution: Create rosters (normalized) and reference via FK
```

### Target State (3NF)
```
rosters (normalized source of truth):
  PK: (season, player_name, team)
  position ← single source

player_stats (measures table):
  PK: (season, player_name, team)  
  FK: rosters(season, player_name, team)
  first_td_count ← calculated from results
  
Result: Position changes in rosters automatically available
```

---

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|-----------|
| Migrations break existing data | 🔴 Loss of picks | Test migrations on backup DB first |
| Foreign keys break app code | 🔴 App crashes | Update database layer before deploying FKs |
| Rosters outdated during season | 🟡 Position data stale | Nightly refresh + manual override |
| Triggers slow down grading | 🟡 UX lag | Index properly, monitor performance |
| Market API rate limits | 🟡 Missing market data | Cache aggressively, schedule off-peak |
| Unique constraint on picks fails | 🔴 Migration fails | Dedupe picks first (already done) |

---

## Testing Strategy

### Data Integrity Tests
```python
def test_no_duplicate_picks():
    """Verify unique constraint prevents duplicates"""
    user_id, week_id = 1, 1
    db.add_pick(user_id, week_id, 'KC', 'Mahomes', 250, 'game_1')
    
    with pytest.raises(IntegrityError):
        db.add_pick(user_id, week_id, 'KC', 'Mahomes', 300, 'game_1')

def test_position_auto_assignment():
    """Verify position assigned on pick creation"""
    pick_id = db.add_pick(1, 1, 'KC', 'Patrick Mahomes', 250, 'game_1')
    player_stats = db.get_player_stats('Patrick Mahomes', 2025, 'KC')
    
    assert player_stats['position'] == 'QB'

def test_first_td_auto_update():
    """Verify first_td_count incremented on grade"""
    pick_id = db.add_pick(1, 1, 'KC', 'Mahomes', 250, 'game_1')
    db.add_result(pick_id, 'Mahomes', is_correct=True)
    
    stats = db.get_player_stats('Mahomes', 2025, 'KC')
    assert stats['first_td_count'] == 1
```

---

## Success Criteria

✅ **Data Integrity**
- No duplicate picks possible (unique constraint)
- All FKs enforced
- All positions populated (< 5% unknown)

✅ **Automation**
- Rosters loaded on app startup
- Positions auto-assigned on pick creation
- First TD counts auto-updated on grade

✅ **Performance**
- Leaderboard queries < 100ms (vs current ~500ms)
- Position filter queries < 50ms
- No full table scans

✅ **Reliability**
- All 78 tests pass
- Data quality report runs nightly
- 0 orphaned records

---

## Next Actions

1. **Read skill**: `database-schema-designer` for detailed schema design guidance
2. **Create migration PR** with games + rosters tables
3. **Implement roster ingestion** service
4. **Add triggers** for automatic updates
5. **Update database layer** to use new tables
6. **Deploy migrations** in dev → staging → prod order
