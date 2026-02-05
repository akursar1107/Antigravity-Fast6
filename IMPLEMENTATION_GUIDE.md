# How to Apply These Migrations

## Quick Start

```bash
cd Fast6
source .venv/bin/activate

# 1. Backup your database
cp data/fast6.db data/fast6.db.backup-20260203

# 2. Add migration functions to src/database/migrations.py
# (Copy all migration_v9 through migration_v14 functions)

# 3. Update MIGRATIONS dict at bottom of migrations.py
MIGRATIONS = {
    1: migration_v1_initial_schema,
    # ...
    8: migration_v8_...,
    9: migration_v9_create_games_table,
    10: migration_v10_create_rosters_table,
    11: migration_v11_add_picks_unique_constraint,
    12: migration_v12_add_picks_game_fk,
    13: migration_v13_add_performance_indexes,
    14: migration_v14_add_triggers,
}

# 4. Run the app (migrations auto-apply)
streamlit run src/app.py

# 5. Verify migrations applied
sqlite3 data/fast6.db
> SELECT version FROM schema_version ORDER BY version DESC LIMIT 5;
> .schema games  # Verify new table exists
```

---

## Step-by-Step Implementation

### Step 1: Update migrations.py

Copy the migration functions from [SQL_MIGRATIONS_V9_V14.md](SQL_MIGRATIONS_V9_V14.md) into `src/database/migrations.py`.

**File**: `src/database/migrations.py`

```python
# At bottom of file, find the MIGRATIONS dictionary
MIGRATIONS = {
    1: migration_v1_initial_schema,
    2: migration_v2_...,
    # ... existing migrations ...
    8: migration_v8_...,
    
    # ADD THESE:
    9: migration_v9_create_games_table,
    10: migration_v10_create_rosters_table,
    11: migration_v11_add_picks_unique_constraint,
    12: migration_v12_add_picks_game_fk,
    13: migration_v13_add_performance_indexes,
    14: migration_v14_add_triggers,
}
```

### Step 2: Create Ingestion Services

Create `src/services/data_sync/` directory with three files:

#### File 1: `src/services/data_sync/__init__.py`
```python
"""Data sync services for automated ingestion."""

from .roster_ingestion import sync_rosters
from .game_sync import sync_games_for_season

__all__ = ['sync_rosters', 'sync_games_for_season']
```

#### File 2: `src/services/data_sync/roster_ingestion.py`
```python
"""
Roster ingestion service.
Loads NFL rosters from nflreadpy and populates rosters table.
"""

import nflreadpy as nfl
import streamlit as st
import logging
from database import get_db_connection
from typing import Dict

logger = logging.getLogger(__name__)


@st.cache_data(ttl=86400)  # Cache for 24 hours
def sync_rosters(season: int) -> Dict[str, int]:
    """
    Load NFL rosters from nflreadpy and populate rosters table.
    
    Args:
        season: NFL season year (e.g., 2025)
    
    Returns:
        Dict with statistics: {'inserted': N, 'updated': N, 'errors': N}
    """
    logger.info(f"Syncing rosters for season {season}")
    
    stats = {'inserted': 0, 'updated': 0, 'errors': 0}
    
    try:
        # Load rosters from nflreadpy
        rosters_df = nfl.load_rosters(seasons=[int(season)]).to_pandas()
        logger.info(f"Loaded {len(rosters_df)} roster entries from nflreadpy")
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        for _, player in rosters_df.iterrows():
            try:
                player_name = player.get('full_name', '')
                team = player.get('team', '')
                position = player.get('position', 'Unknown')
                jersey = player.get('jersey_number')
                player_id = player.get('player_id')
                
                if not player_name or not team:
                    continue
                
                # Upsert into rosters table
                cursor.execute('''
                    INSERT OR REPLACE INTO rosters 
                    (season, player_name, team, position, jersey_number, nflreadpy_id)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (season, player_name, team, position, jersey, player_id))
                
                stats['inserted'] += 1
            
            except Exception as e:
                logger.error(f"Error syncing {player.get('full_name')}: {e}")
                stats['errors'] += 1
        
        conn.commit()
        conn.close()
        
        logger.info(f"Roster sync complete: {stats}")
        return stats
    
    except Exception as e:
        logger.error(f"Error loading rosters for {season}: {e}")
        return stats


def get_player_position(player_name: str, team: str, season: int) -> str:
    """
    Look up player position from rosters table.
    
    Args:
        player_name: Player name (e.g., "Patrick Mahomes")
        team: Team abbreviation (e.g., "KC")
        season: NFL season year
    
    Returns:
        Position (e.g., "QB") or "Unknown" if not found
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT position FROM rosters
            WHERE player_name = ? AND team = ? AND season = ?
            LIMIT 1
        ''', (player_name, team, season))
        
        result = cursor.fetchone()
        conn.close()
        
        return result[0] if result else 'Unknown'
    
    except Exception as e:
        logger.error(f"Error looking up position for {player_name}: {e}")
        return 'Unknown'
```

#### File 3: `src/services/data_sync/game_sync.py`
```python
"""
Game sync service.
Loads NFL game schedule and populates games table.
"""

import nflreadpy as nfl
import streamlit as st
import logging
import pandas as pd
from database import get_db_connection
from typing import Dict

logger = logging.getLogger(__name__)


@st.cache_data(ttl=3600)  # Cache for 1 hour
def sync_games_for_season(season: int) -> Dict[str, int]:
    """
    Load NFL games from nflreadpy and populate games table.
    
    Args:
        season: NFL season year (e.g., 2025)
    
    Returns:
        Dict with statistics: {'inserted': N, 'errors': N}
    """
    logger.info(f"Syncing games for season {season}")
    
    stats = {'inserted': 0, 'errors': 0}
    
    try:
        # Load schedule from nflreadpy
        schedule_df = nfl.load_schedules(seasons=[int(season)]).to_pandas()
        logger.info(f"Loaded {len(schedule_df)} games from nflreadpy")
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        for _, game in schedule_df.iterrows():
            try:
                game_id = game.get('game_id', '')
                week = game.get('week')
                gameday = game.get('gameday')
                home_team = game.get('home_team', '')
                away_team = game.get('away_team', '')
                home_score = game.get('home_score')
                away_score = game.get('away_score')
                
                # Determine game status
                if pd.isna(home_score) or pd.isna(away_score):
                    status = 'scheduled'
                else:
                    status = 'final'
                
                if not game_id or not home_team or not away_team:
                    continue
                
                # Insert into games table
                cursor.execute('''
                    INSERT OR REPLACE INTO games
                    (id, season, week, game_date, home_team, away_team, 
                     home_score, away_score, status)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (game_id, season, week, gameday, home_team, away_team,
                      home_score if not pd.isna(home_score) else None,
                      away_score if not pd.isna(away_score) else None,
                      status))
                
                stats['inserted'] += 1
            
            except Exception as e:
                logger.error(f"Error syncing game {game.get('game_id')}: {e}")
                stats['errors'] += 1
        
        conn.commit()
        conn.close()
        
        logger.info(f"Game sync complete: {stats}")
        return stats
    
    except Exception as e:
        logger.error(f"Error loading games for {season}: {e}")
        return stats


def get_game_id(season: int, week: int, home_team: str, away_team: str) -> str:
    """
    Look up game_id from games table.
    
    Args:
        season: NFL season year
        week: NFL week number
        home_team: Home team abbreviation
        away_team: Away team abbreviation
    
    Returns:
        Game ID (e.g., "2025_01_KC_LV") or None if not found
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id FROM games
            WHERE season = ? AND week = ? AND home_team = ? AND away_team = ?
            LIMIT 1
        ''', (season, week, home_team, away_team))
        
        result = cursor.fetchone()
        conn.close()
        
        return result[0] if result else None
    
    except Exception as e:
        logger.error(f"Error looking up game: {e}")
        return None
```

### Step 3: Update app.py to Call Sync on Startup

**File**: `src/app.py`

Add this after `run_migrations()`:

```python
from services.data_sync import sync_rosters, sync_games_for_season
import config

# Run database migrations (replaces old init_db + ensure_* functions)
run_migrations()

# NEW: Sync reference tables on startup
try:
    sync_rosters(config.CURRENT_SEASON)
    sync_games_for_season(config.CURRENT_SEASON)
    logger.info("Reference tables synced on startup")
except Exception as e:
    logger.warning(f"Failed to sync reference tables: {e}")
    # App continues to work even if sync fails
```

### Step 4: Update Pick Creation to Auto-Assign Position

**File**: `src/database/picks.py`

Update the `add_pick` function:

```python
def add_pick(user_id, week_id, team, player_name, odds, game_id):
    """
    Create a new pick with auto-position assignment.
    
    NEW: Looks up position from rosters table
    NEW: Creates player_stats entry if doesn't exist
    """
    from services.data_sync.roster_ingestion import get_player_position
    from database.players import ensure_player_stats
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Get season from week_id
        cursor.execute("SELECT season FROM weeks WHERE id = ?", (week_id,))
        season_row = cursor.fetchone()
        season = season_row[0] if season_row else config.CURRENT_SEASON
        
        # 1. Insert pick
        cursor.execute('''
            INSERT INTO picks (user_id, week_id, team, player_name, odds, game_id, created_at)
            VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        ''', (user_id, week_id, team, player_name, odds, game_id))
        
        pick_id = cursor.lastrowid
        
        # 2. Look up position from rosters (NEW!)
        position = get_player_position(player_name, team, season)
        
        # 3. Ensure player_stats entry exists with position (NEW!)
        ensure_player_stats(player_name, season, team, position)
        
        conn.commit()
        logger.info(f"Created pick {pick_id} for {player_name} with position {position}")
        
        return pick_id
    
    except IntegrityError as e:
        if 'UNIQUE constraint failed' in str(e):
            logger.warning(f"Duplicate pick for {player_name} in week {week_id}")
            raise ValueError("Pick already exists for this player this week")
        raise
    
    finally:
        conn.close()
```

### Step 5: Test the Setup

```bash
# Activate venv
source .venv/bin/activate

# Run app
streamlit run src/app.py

# In another terminal, verify:
sqlite3 data/fast6.db

# Check schema version
> SELECT version FROM schema_version ORDER BY version DESC LIMIT 1;
14  # Should be 14

# Check tables created
> .tables
games rosters player_stats picks results ...

# Check rosters populated
> SELECT COUNT(*) FROM rosters WHERE season = 2025;
# Should return >100

# Check games populated
> SELECT COUNT(*) FROM games WHERE season = 2025;
# Should return 18 (NFL has 18 weeks)

# Test triggers (if you've graded a pick)
> SELECT first_td_count FROM player_stats WHERE player_name = 'Patrick Mahomes';
# Should show correct count
```

---

## Troubleshooting

### Q: Migration fails with "table already exists"
**A**: The migration checks with `PRAGMA table_info()` first. If it fails anyway:
```bash
sqlite3 data/fast6.db
> DROP TABLE IF EXISTS games;
> DELETE FROM schema_version WHERE version >= 9;
```
Then re-run.

### Q: Unique constraint on picks fails during migration
**A**: Deduplication wasn't complete. Manually dedupe first:
```sql
DELETE FROM picks WHERE id NOT IN (
    SELECT MAX(id) FROM picks 
    GROUP BY user_id, week_id, player_name
);
```

### Q: Foreign key constraint violates on picks
**A**: Some picks have `NULL` game_id. Backfill before migration:
```sql
-- For picks where game_id is NULL, try to look up from games table
UPDATE picks SET game_id = (
    SELECT games.id FROM games
    WHERE games.season = 2025 AND games.week = (SELECT week FROM weeks WHERE id = picks.week_id)
    LIMIT 1
)
WHERE game_id IS NULL;
```

### Q: Triggers don't fire
**A**: Verify they exist:
```sql
> SELECT name FROM sqlite_master WHERE type='trigger';
> -- Should show: update_player_stats_on_result_insert, update_player_stats_on_result_delete
```

### Q: Positions still showing "Unknown"
**A**: Rosters didn't sync properly. Manually trigger:
```bash
python3 << 'EOF'
import sys
sys.path.insert(0, 'src')
from services.data_sync import sync_rosters
stats = sync_rosters(2025)
print(f"Synced rosters: {stats}")
EOF
```

---

## Rollback Plan

If anything breaks, roll back is easy:

```bash
# 1. Restore backup
cp data/fast6.db.backup-20260203 data/fast6.db

# 2. Verify
sqlite3 data/fast6.db
> SELECT version FROM schema_version ORDER BY version DESC LIMIT 1;
8  # Back to v8
```

---

## Performance Verification

After migrations, verify performance improvements:

```python
import time
import streamlit as st
from database import get_db_connection

# Test 1: Leaderboard query
start = time.time()
conn = get_db_connection()
cursor = conn.cursor()
cursor.execute('''
    SELECT p.player_name, p.first_td_count FROM player_stats p
    WHERE p.position = 'WR' AND p.season = 2025
    ORDER BY p.first_td_count DESC LIMIT 10
''')
results = cursor.fetchall()
elapsed = time.time() - start

st.write(f"Leaderboard query: {elapsed*1000:.1f}ms")
st.write(f"Results: {len(results)} rows")
# Should be <100ms
```

---

## Success Checklist

After all migrations and setup:

- [ ] All 6 migrations applied (schema_version = 14)
- [ ] games table populated with 256+ games
- [ ] rosters table populated with 1000+ players
- [ ] Zero "Unknown" positions for recently picked players
- [ ] Leaderboard queries < 100ms
- [ ] Pick creation auto-assigns position
- [ ] Result grading auto-updates first_td_count
- [ ] All 78 tests pass
- [ ] App runs without errors
- [ ] Streamlit dashboard loads quickly

