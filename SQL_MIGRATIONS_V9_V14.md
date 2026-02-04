# SQL Migrations for Schema Improvements

**Status**: Ready to implement in Phase 11  
**Database**: SQLite3  
**Environment**: Fast6 (Python 3.13, Streamlit)  

---

## Prerequisites

Before running migrations:
1. ✅ Backup database: `cp data/fast6.db data/fast6.db.backup-20260203`
2. ✅ Verify current schema version: `SELECT MAX(version) FROM schema_version`
3. ✅ Test migrations on backup first

---

## Migration v9: Create Games Reference Table

**Purpose**: Single source of truth for NFL games, links picks and market data to schedule

```python
# src/database/migrations.py

def migration_v9_create_games_table(conn: sqlite3.Connection) -> None:
    """
    Version 9: Create games table to track NFL schedule.
    
    Columns:
    - id: Unique game identifier from nflreadpy (e.g., "2025_01_KC_LV")
    - season: NFL season year (e.g., 2025)
    - week: NFL week number (1-18)
    - game_date: Date of game
    - home_team: Home team abbreviation (e.g., "KC")
    - away_team: Away team abbreviation (e.g., "LV")
    - home_score, away_score: Final scores (nullable until game ends)
    - status: "scheduled", "in_progress", or "final"
    
    Indexes for performance:
    - (season, week): Most common filter combination
    - (home_team, away_team): Check specific matchup
    """
    cursor = conn.cursor()
    
    # Check if table already exists
    cursor.execute("PRAGMA table_info(games)")
    if cursor.fetchall():
        logger.info("Migration v9: games table already exists, skipping")
        return
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS games (
            id TEXT PRIMARY KEY,
            season INTEGER NOT NULL,
            week INTEGER NOT NULL,
            game_date DATE NOT NULL,
            home_team TEXT NOT NULL,
            away_team TEXT NOT NULL,
            home_score INTEGER,
            away_score INTEGER,
            status TEXT DEFAULT 'scheduled' 
                CHECK(status IN ('scheduled', 'in_progress', 'final')),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(season, week, home_team, away_team),
            FOREIGN KEY (season) REFERENCES weeks(season)
        )
    ''')
    
    # Create indexes for common queries
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_games_season_week 
        ON games(season, week)
    ''')
    
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_games_teams 
        ON games(home_team, away_team)
    ''')
    
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_games_status 
        ON games(status)
    ''')
    
    conn.commit()
    logger.info("Applied migration v9: Created games table")
```

---

## Migration v10: Create Rosters Reference Table

**Purpose**: Normalize player positions, eliminate "Unknown" position problem

```python
def migration_v10_create_rosters_table(conn: sqlite3.Connection) -> None:
    """
    Version 10: Create rosters table for player position normalization.
    
    Columns:
    - id: Auto-increment primary key
    - season: NFL season year (e.g., 2025)
    - player_name: Full player name (e.g., "Patrick Mahomes")
    - team: Team abbreviation (e.g., "KC")
    - position: Player position (QB, RB, WR, TE, K, DEF)
    - jersey_number: Jersey number
    - nflreadpy_id: Unique player ID from nflreadpy (for tracking trades)
    
    Constraints:
    - UNIQUE(season, player_name, team): Prevent duplicate roster entries
    - UNIQUE(nflreadpy_id): Guarantee one entry per player ID
    
    This table is the source of truth for player positions.
    It's populated from nflreadpy on app startup and synced nightly.
    """
    cursor = conn.cursor()
    
    # Check if table already exists
    cursor.execute("PRAGMA table_info(rosters)")
    if cursor.fetchall():
        logger.info("Migration v10: rosters table already exists, skipping")
        return
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS rosters (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            season INTEGER NOT NULL,
            player_name TEXT NOT NULL,
            team TEXT NOT NULL,
            position TEXT NOT NULL 
                CHECK(position IN ('QB', 'RB', 'WR', 'TE', 'K', 'DEF')),
            jersey_number INTEGER,
            nflreadpy_id TEXT UNIQUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(season, player_name, team),
            FOREIGN KEY (season) REFERENCES weeks(season)
        )
    ''')
    
    # Create indexes for common queries
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_rosters_season_player 
        ON rosters(season, player_name)
    ''')
    
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_rosters_team_position 
        ON rosters(team, position)
    ''')
    
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_rosters_position 
        ON rosters(position)
    ''')
    
    conn.commit()
    logger.info("Applied migration v10: Created rosters table")
```

---

## Migration v11: Add Unique Constraint to Picks

**Purpose**: Prevent duplicate picks (same user, week, player)

```python
def migration_v11_add_picks_unique_constraint(conn: sqlite3.Connection) -> None:
    """
    Version 11: Add UNIQUE constraint to prevent duplicate picks.
    
    Constraint: UNIQUE(user_id, week_id, player_name)
    
    This prevents:
    - User can't pick same player twice in same week
    - Accidental duplicate imports from CSV
    - UI bugs causing multiple submissions
    
    Pre-flight: Deduplicates existing picks before applying constraint
    (see BUGFIX_WEEK_BYTES_DUPLICATES.md)
    """
    cursor = conn.cursor()
    
    # Check if constraint already exists
    cursor.execute("PRAGMA index_list(picks)")
    indexes = cursor.fetchall()
    constraint_exists = any('unique_user_week_player' in str(idx) for idx in indexes)
    
    if constraint_exists:
        logger.info("Migration v11: unique constraint already exists, skipping")
        return
    
    # Before applying unique constraint, we need to remove duplicates
    # This was already done in a bugfix, but let's be safe
    logger.info("Removing duplicate picks before applying constraint...")
    
    # Keep only the most recent pick for each (user_id, week_id, player_name)
    cursor.execute('''
        DELETE FROM picks WHERE id NOT IN (
            SELECT MAX(id) FROM picks 
            GROUP BY user_id, week_id, player_name
        )
    ''')
    conn.commit()
    logger.info(f"Removed {cursor.rowcount} duplicate picks")
    
    # Now apply the unique constraint via recreation
    # SQLite doesn't support ALTER TABLE to add constraints, so we:
    # 1. Create new table with constraint
    # 2. Copy data
    # 3. Drop old table
    # 4. Rename new table
    
    cursor.execute('''
        CREATE TABLE picks_new (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            week_id INTEGER NOT NULL,
            team TEXT NOT NULL,
            player_name TEXT NOT NULL,
            odds REAL,
            theoretical_return REAL,
            game_id TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(user_id, week_id, player_name),
            FOREIGN KEY (user_id) REFERENCES users(id),
            FOREIGN KEY (week_id) REFERENCES weeks(id),
            FOREIGN KEY (game_id) REFERENCES games(id)
        )
    ''')
    
    # Copy existing data
    cursor.execute('''
        INSERT INTO picks_new 
        SELECT * FROM picks
    ''')
    
    # Recreate indexes
    cursor.execute('''
        CREATE INDEX idx_picks_user_week ON picks_new(user_id, week_id)
    ''')
    
    cursor.execute('''
        CREATE INDEX idx_picks_week_id ON picks_new(week_id)
    ''')
    
    cursor.execute('''
        CREATE INDEX idx_picks_game_id ON picks_new(game_id)
    ''')
    
    cursor.execute('''
        CREATE INDEX idx_picks_player_name ON picks_new(player_name)
    ''')
    
    # Drop old table and rename
    cursor.execute('DROP TABLE picks')
    cursor.execute('ALTER TABLE picks_new RENAME TO picks')
    
    conn.commit()
    logger.info("Applied migration v11: Added UNIQUE constraint to picks")
```

---

## Migration v12: Add Game Foreign Key to Picks

**Purpose**: Link picks to specific games, enforce referential integrity

```python
def migration_v12_add_picks_game_fk(conn: sqlite3.Connection) -> None:
    """
    Version 12: Add FOREIGN KEY constraint from picks to games.
    
    This enforces referential integrity:
    - All picks must reference a valid game
    - Can't delete a game if picks reference it
    - Enables JOIN queries between picks and games
    """
    cursor = conn.cursor()
    
    # In SQLite, to add FK we need to:
    # 1. Create new table with FK
    # 2. Copy data (only keep picks with valid game_id)
    # 3. Drop old table
    # 4. Rename new table
    
    cursor.execute('''
        CREATE TABLE picks_new (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            week_id INTEGER NOT NULL,
            team TEXT NOT NULL,
            player_name TEXT NOT NULL,
            odds REAL,
            theoretical_return REAL,
            game_id TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(user_id, week_id, player_name),
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
            FOREIGN KEY (week_id) REFERENCES weeks(id) ON DELETE CASCADE,
            FOREIGN KEY (game_id) REFERENCES games(id) ON DELETE CASCADE
        )
    ''')
    
    # Copy only picks with valid game_id
    invalid_count = cursor.execute(
        'SELECT COUNT(*) FROM picks WHERE game_id IS NULL'
    ).fetchone()[0]
    
    if invalid_count > 0:
        logger.warning(f"Found {invalid_count} picks with NULL game_id")
        logger.warning("These picks will be deleted during migration")
        logger.warning("Recommendation: Backfill game_ids before migration")
    
    cursor.execute('''
        INSERT INTO picks_new 
        SELECT id, user_id, week_id, team, player_name, odds, 
               theoretical_return, game_id, created_at
        FROM picks WHERE game_id IS NOT NULL
    ''')
    
    # Recreate indexes
    cursor.execute('''
        CREATE INDEX idx_picks_user_week ON picks_new(user_id, week_id)
    ''')
    cursor.execute('''
        CREATE INDEX idx_picks_week_id ON picks_new(week_id)
    ''')
    cursor.execute('''
        CREATE INDEX idx_picks_game_id ON picks_new(game_id)
    ''')
    cursor.execute('''
        CREATE INDEX idx_picks_player_name ON picks_new(player_name)
    ''')
    
    # Drop old table and rename
    cursor.execute('DROP TABLE picks')
    cursor.execute('ALTER TABLE picks_new RENAME TO picks')
    
    conn.commit()
    logger.info("Applied migration v12: Added game_id FOREIGN KEY to picks")
```

---

## Migration v13: Add Performance Indexes

**Purpose**: Dramatically speed up common queries

```python
def migration_v13_add_performance_indexes(conn: sqlite3.Connection) -> None:
    """
    Version 13: Add indexes to optimize query performance.
    
    Indexes added:
    - results(is_correct): Filter by graded status
    - results(pick_id): Join with picks
    - player_stats(position, season): WR/RB leader queries
    - player_stats(team): Team-based queries
    - team_ratings(team, week): Recent team ratings
    - market_odds(game_id, snapshot_time): Market history
    
    Performance impact:
    - Leaderboard queries: 500ms → <100ms
    - Position filters: full scan → indexed lookup
    - Grading queries: linear → logarithmic
    """
    cursor = conn.cursor()
    
    # Results table indexes
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_results_is_correct 
        ON results(is_correct)
    ''')
    
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_results_pick_id 
        ON results(pick_id)
    ''')
    
    # Player stats indexes
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_player_stats_position_season 
        ON player_stats(position, season)
    ''')
    
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_player_stats_team_season 
        ON player_stats(team, season)
    ''')
    
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_player_stats_player_season 
        ON player_stats(player_name, season)
    ''')
    
    # Team ratings indexes
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_team_ratings_team_week 
        ON team_ratings(team, week)
    ''')
    
    # Market odds indexes (for future Polymarket/Kalshi integration)
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_market_odds_game_player 
        ON market_odds(game_id, player_name)
    ''')
    
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_market_odds_timestamp 
        ON market_odds(snapshot_time)
    ''')
    
    conn.commit()
    logger.info("Applied migration v13: Added performance indexes")
```

---

## Migration v14: Add Automation Triggers

**Purpose**: Auto-update first_td_count and maintain referential integrity

```python
def migration_v14_add_triggers(conn: sqlite3.Connection) -> None:
    """
    Version 14: Add database triggers for automatic updates.
    
    Triggers:
    1. update_player_stats_on_result_insert: Increment first_td_count when pick graded
    2. update_player_stats_on_result_delete: Decrement if grading reversed
    
    These triggers maintain the invariant:
        player_stats.first_td_count = COUNT(results where is_correct=1)
    
    Benefits:
    - Leaderboard always accurate
    - No manual recalculation needed
    - Transactional consistency
    """
    cursor = conn.cursor()
    
    # Trigger 1: Insert
    cursor.execute('''
        CREATE TRIGGER IF NOT EXISTS update_player_stats_on_result_insert
        AFTER INSERT ON results
        FOR EACH ROW
        WHEN NEW.is_correct = 1
        BEGIN
            -- Get the pick details
            INSERT INTO player_stats (player_name, season, team, position, first_td_count)
            SELECT 
                p.player_name,
                w.season,
                p.team,
                'Unknown',  -- Will be updated by roster lookup service
                1
            FROM picks p
            JOIN weeks w ON p.week_id = w.id
            WHERE p.id = NEW.pick_id
            
            ON CONFLICT(player_name, season, team) DO UPDATE SET
                first_td_count = first_td_count + 1;
        END
    ''')
    
    # Trigger 2: Delete
    cursor.execute('''
        CREATE TRIGGER IF NOT EXISTS update_player_stats_on_result_delete
        AFTER DELETE ON results
        FOR EACH ROW
        WHEN OLD.is_correct = 1
        BEGIN
            -- Decrement first_td_count
            UPDATE player_stats SET
                first_td_count = MAX(0, first_td_count - 1)
            WHERE player_name = (SELECT player_name FROM picks WHERE id = OLD.pick_id)
              AND season = (SELECT season FROM weeks WHERE id = (SELECT week_id FROM picks WHERE id = OLD.pick_id))
              AND team = (SELECT team FROM picks WHERE id = OLD.pick_id);
            
            -- Delete entry if count reaches 0
            DELETE FROM player_stats
            WHERE first_td_count = 0
              AND any_time_td_count = 0
              AND red_zone_targets = 0;
        END
    ''')
    
    conn.commit()
    logger.info("Applied migration v14: Added automation triggers")
```

---

## Migration Execution Checklist

Before running migrations:
- [ ] Backup database
- [ ] Verify current schema version
- [ ] Test on backup copy first
- [ ] Prepare rollback plan

Execution order (must be sequential):
1. [ ] v9: Create games table
2. [ ] v10: Create rosters table
3. [ ] v11: Add unique constraint to picks
4. [ ] v12: Add game FK to picks
5. [ ] v13: Add performance indexes
6. [ ] v14: Add triggers

After migrations:
- [ ] Verify schema version updated
- [ ] Check all indexes created
- [ ] Test pick creation (verify auto-position)
- [ ] Test result grading (verify auto-update)
- [ ] Run data quality checks
- [ ] Monitor performance improvements

---

## Rollback Procedure

If migration fails, execute in reverse order:

```python
# Drop triggers
cursor.execute('DROP TRIGGER IF EXISTS update_player_stats_on_result_insert')
cursor.execute('DROP TRIGGER IF EXISTS update_player_stats_on_result_delete')

# Drop indexes (SQLite does this automatically when dropping tables)

# Restore picks table to pre-v12 state
cursor.execute('''
    CREATE TABLE picks_old (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        week_id INTEGER NOT NULL,
        team TEXT NOT NULL,
        player_name TEXT NOT NULL,
        odds REAL,
        theoretical_return REAL,
        game_id TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
''')
cursor.execute('INSERT INTO picks_old SELECT * FROM picks')
cursor.execute('DROP TABLE picks')
cursor.execute('ALTER TABLE picks_old RENAME TO picks')

# Drop new tables
cursor.execute('DROP TABLE IF EXISTS games')
cursor.execute('DROP TABLE IF EXISTS rosters')

# Record rollback
cursor.execute('DELETE FROM schema_version WHERE version > 8')
conn.commit()
```

---

## Testing the Migrations

```python
# Test 1: Verify games table
def test_games_table_created():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("PRAGMA table_info(games)")
    columns = [row[1] for row in cursor.fetchall()]
    assert 'id' in columns
    assert 'season' in columns
    assert 'game_date' in columns

# Test 2: Verify rosters table
def test_rosters_table_created():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("PRAGMA table_info(rosters)")
    columns = [row[1] for row in cursor.fetchall()]
    assert 'player_name' in columns
    assert 'position' in columns

# Test 3: Verify unique constraint on picks
def test_picks_unique_constraint():
    user_id, week_id = 1, 1
    add_pick(user_id, week_id, 'KC', 'Mahomes', 250, 'game_1')
    
    with pytest.raises(IntegrityError):
        add_pick(user_id, week_id, 'KC', 'Mahomes', 300, 'game_2')

# Test 4: Verify triggers update player_stats
def test_trigger_updates_first_td_count():
    pick_id = add_pick(1, 1, 'KC', 'Mahomes', 250, 'game_1')
    add_result(pick_id, 'Mahomes', is_correct=True)
    
    stats = get_player_stats('Mahomes', 2025, 'KC')
    assert stats['first_td_count'] == 1
```
