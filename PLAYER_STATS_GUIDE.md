# Player Performance Tracking Implementation Guide

## Overview
This guide provides step-by-step instructions for implementing player performance tracking in Fast6. This feature tracks which players score the most first-time touchdowns, shows their "form" (hot/cold), and helps users make better picks.

**Effort**: ~6 hours | **Impact**: High | **Complexity**: Medium

---

## 1. Database Schema

### New Table: `player_stats`
```sql
CREATE TABLE player_stats (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    season INTEGER NOT NULL,
    player_name TEXT NOT NULL,
    position TEXT,  -- WR, RB, TE, QB, etc.
    team TEXT NOT NULL,
    
    -- Cumulative stats
    td_count INTEGER DEFAULT 0,
    game_count INTEGER DEFAULT 0,
    
    -- Calculated
    td_rate REAL DEFAULT 0.0,  -- td_count / game_count
    recent_td_rate REAL DEFAULT 0.0,  -- last 5 games
    
    -- Metadata
    last_td_game_id INTEGER,  -- Most recent game with TD
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(season, player_name, team),
    FOREIGN KEY (team) REFERENCES teams(abbr)
);
```

### Why These Fields?
- `season`: Stats reset each year
- `td_rate`: Quick metric for "hot" status
- `recent_td_rate`: Last 5 games shows current form (vs season average)
- `last_td_game_id`: Know "X scored 3 games ago"
- `position`: Filter by WR/RB/TE (TEs might score differently)

---

## 2. Module Implementation: `src/utils/player_stats.py`

```python
"""
Player performance tracking for Fast6.

Tracks first TD scoring rates by player/season to help users:
1. Identify "hot" players (scoring more TDs recently)
2. Understand player form (trending up/down)
3. Make better picks based on recent performance
"""

from typing import Optional, Dict, List, Tuple
from datetime import datetime, timedelta
import sqlite3
from utils.db_connection import get_db_connection

class PlayerStats:
    """Track and manage player performance statistics."""
    
    @staticmethod
    def init_player_stats_table():
        """Create player_stats table if it doesn't exist."""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS player_stats (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                season INTEGER NOT NULL,
                player_name TEXT NOT NULL,
                position TEXT,
                team TEXT NOT NULL,
                td_count INTEGER DEFAULT 0,
                game_count INTEGER DEFAULT 0,
                td_rate REAL DEFAULT 0.0,
                recent_td_rate REAL DEFAULT 0.0,
                last_td_game_id INTEGER,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(season, player_name, team)
            )
        """)
        
        # Create index for faster lookups
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_player_stats_season_td_rate 
            ON player_stats(season, td_rate DESC)
        """)
        
        conn.commit()
        conn.close()
    
    @staticmethod
    def get_player_stats(
        season: int, 
        player_name: str, 
        team: str
    ) -> Optional[Dict]:
        """Get stats for a specific player."""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                SELECT id, td_count, game_count, td_rate, recent_td_rate, last_td_game_id
                FROM player_stats
                WHERE season = ? AND player_name = ? AND team = ?
            """, (season, player_name, team))
            
            row = cursor.fetchone()
            return dict(row) if row else None
        finally:
            conn.close()
    
    @staticmethod
    def get_hot_players(season: int, position: Optional[str] = None, limit: int = 25) -> List[Dict]:
        """Get hottest players (highest recent_td_rate) for the season."""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        try:
            if position:
                cursor.execute(f"""
                    SELECT 
                        player_name, 
                        team,
                        position,
                        td_count,
                        game_count,
                        td_rate,
                        recent_td_rate,
                        last_updated
                    FROM player_stats
                    WHERE season = ? AND position = ? AND game_count >= 3
                    ORDER BY recent_td_rate DESC
                    LIMIT ?
                """, (season, position, limit))
            else:
                cursor.execute("""
                    SELECT 
                        player_name, 
                        team,
                        position,
                        td_count,
                        game_count,
                        td_rate,
                        recent_td_rate,
                        last_updated
                    FROM player_stats
                    WHERE season = ? AND game_count >= 3
                    ORDER BY recent_td_rate DESC
                    LIMIT ?
                """, (season, limit))
            
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
        finally:
            conn.close()
    
    @staticmethod
    def get_team_player_stats(season: int, team: str) -> List[Dict]:
        """Get all players from a team, sorted by hot/cold."""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                SELECT 
                    player_name,
                    position,
                    td_count,
                    game_count,
                    td_rate,
                    recent_td_rate
                FROM player_stats
                WHERE season = ? AND team = ?
                ORDER BY recent_td_rate DESC
            """, (season, team))
            
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
        finally:
            conn.close()
    
    @staticmethod
    def update_player_stats(result_id: int, season: int):
        """
        Update player stats after a pick is graded.
        
        Call this after inserting a result that has is_correct = 1
        (meaning the first TD scorer was correct).
        
        Args:
            result_id: The result record ID
            season: The season year
        """
        conn = get_db_connection()
        cursor = conn.cursor()
        
        try:
            # Get the result details
            cursor.execute("""
                SELECT p.player_name, p.team, p.game_id
                FROM results r
                JOIN picks p ON r.pick_id = p.id
                WHERE r.id = ? AND r.is_correct = 1
            """, (result_id,))
            
            result = cursor.fetchone()
            if not result:
                return
            
            player_name, team, game_id = result[0], result[1], result[2]
            
            # Get player position from latest game
            cursor.execute("""
                SELECT position FROM nfl_players
                WHERE player_name = ? AND team = ?
                LIMIT 1
            """)
            position_row = cursor.fetchone()
            position = position_row[0] if position_row else None
            
            # Insert or update player_stats
            cursor.execute("""
                INSERT INTO player_stats (season, player_name, position, team, td_count, game_count, last_td_game_id)
                VALUES (?, ?, ?, ?, 1, 1, ?)
                ON CONFLICT(season, player_name, team) DO UPDATE SET
                    td_count = td_count + 1,
                    last_td_game_id = excluded.last_td_game_id,
                    last_updated = CURRENT_TIMESTAMP
            """, (season, player_name, position, team, game_id))
            
            # Recalculate rates
            PlayerStats._recalculate_rates(season, player_name, team, cursor)
            
            conn.commit()
        finally:
            conn.close()
    
    @staticmethod
    def _recalculate_rates(season: int, player_name: str, team: str, cursor):
        """Recalculate td_rate and recent_td_rate for a player."""
        
        # Overall TD rate
        cursor.execute("""
            SELECT td_count, game_count
            FROM player_stats
            WHERE season = ? AND player_name = ? AND team = ?
        """, (season, player_name, team))
        
        row = cursor.fetchone()
        if not row:
            return
        
        td_count, game_count = row
        td_rate = td_count / game_count if game_count > 0 else 0
        
        # Recent TD rate (last 5 games with this team)
        cursor.execute("""
            SELECT COUNT(*) as recent_tds
            FROM results r
            JOIN picks p ON r.pick_id = p.id
            WHERE p.player_name = ? 
            AND p.team = ?
            AND p.season = ?
            AND r.is_correct = 1
            ORDER BY p.id DESC
            LIMIT 5
        """, (player_name, team, season))
        
        recent_tds = cursor.fetchone()[0]
        recent_td_rate = recent_tds / 5 if recent_tds > 0 else 0  # Assumes 5 recent games tracked
        
        # Update rates
        cursor.execute("""
            UPDATE player_stats
            SET td_rate = ?, recent_td_rate = ?
            WHERE season = ? AND player_name = ? AND team = ?
        """, (td_rate, recent_td_rate, season, player_name, team))
    
    @staticmethod
    def get_form_badge(recent_td_rate: float) -> Tuple[str, str]:
        """
        Get visual badge for player form.
        
        Returns: (emoji, label) tuple
        """
        if recent_td_rate >= 0.4:
            return "🔥", "Hot"
        elif recent_td_rate >= 0.2:
            return "✓", "Average"
        else:
            return "❄️", "Cold"
    
    @staticmethod
    def get_player_summary(season: int, player_name: str, team: str) -> Optional[str]:
        """
        Get human-readable summary of player performance.
        
        Returns: "X has scored 3 TDs in last 5 games (hot)" or None
        """
        stats = PlayerStats.get_player_stats(season, player_name, team)
        if not stats:
            return None
        
        td_count = stats['td_count']
        recent_rate = stats['recent_td_rate']
        badge, label = PlayerStats.get_form_badge(recent_rate)
        
        return f"{badge} {player_name} has {td_count} TDs this season ({label} form)"
```

---

## 3. Integration Points

### 3.1 Auto-grade Workflow (in `views/admin/grading.py`)

After grading results:
```python
# When user clicks "Grade" button
def grade_pick(result_id: int, season: int):
    # ... existing grading logic ...
    
    # NEW: Update player stats
    from utils.player_stats import PlayerStats
    PlayerStats.update_player_stats(result_id, season)
```

### 3.2 Pick Input UI (in `views/admin/picks.py`)

When showing player selector:
```python
import streamlit as st
from utils.player_stats import PlayerStats

season = st.sidebar.selectbox("Season", config.SEASONS)
team = st.selectbox("Team", teams)

# NEW: Show hot players for this team
st.subheader(f"Hot Players on {team}")
hot_players = PlayerStats.get_team_player_stats(season, team)

for player in hot_players:
    badge, label = PlayerStats.get_form_badge(player['recent_td_rate'])
    st.write(f"{badge} **{player['player_name']}** ({player['position']}) - {label} ({player['td_count']} TDs)")

# User still selects from all players (not just hot ones)
player_name = st.selectbox("Player", all_players, help="Sort by hot players above")
```

### 3.3 Public Dashboard (New Tab: `views/tabs/player_stats.py`)

```python
import streamlit as st
from utils.player_stats import PlayerStats
import config

def show_player_stats_tab():
    st.header("🔥 Hot Players This Season")
    
    col1, col2 = st.columns(2)
    
    with col1:
        season = st.selectbox("Season", config.SEASONS)
    
    with col2:
        position = st.selectbox(
            "Filter by Position",
            ["All", "WR", "RB", "TE", "QB"],
            key="player_stats_position"
        )
    
    # Get hot players
    pos_filter = None if position == "All" else position
    hot_players = PlayerStats.get_hot_players(season, position=pos_filter, limit=50)
    
    if hot_players:
        # Display as table
        df = pd.DataFrame([
            {
                "Player": p['player_name'],
                "Team": p['team'],
                "Position": p['position'],
                "TDs": p['td_count'],
                "Games": p['game_count'],
                "TD Rate": f"{p['td_rate']:.1%}",
                "Form": PlayerStats.get_form_badge(p['recent_td_rate'])[1],
            }
            for p in hot_players
        ])
        
        st.dataframe(df, use_container_width=True)
        
        # Show trends
        st.subheader("📈 Trending Up")
        trending_up = [p for p in hot_players if p['recent_td_rate'] > p['td_rate']]
        if trending_up:
            for p in trending_up[:5]:
                st.write(f"🔥 **{p['player_name']}** - Recent: {p['recent_td_rate']:.0%} (Overall: {p['td_rate']:.0%})")
    else:
        st.info("No player data available for selected filters")
```

---

## 4. Database Initialization

### In `src/config.py`, add initialization:
```python
def init_app():
    """Initialize app (called on startup)."""
    from utils.db_connection import init_db
    from utils.player_stats import PlayerStats
    
    # Initialize all tables
    init_db()
    PlayerStats.init_player_stats_table()
```

### In `src/app.py`, call on startup:
```python
import config

# Initialize app
config.init_app()
```

---

## 5. Testing

### Unit Tests: `tests/test_player_stats.py`

```python
import pytest
from utils.player_stats import PlayerStats
import config

def test_init_table():
    """Test that table initializes correctly."""
    PlayerStats.init_player_stats_table()
    stats = PlayerStats.get_player_stats(2025, "Test Player", "ARI")
    assert stats is None  # No data yet

def test_update_stats():
    """Test that stats update after grading."""
    # Create test data...
    # Call update_player_stats()
    # Verify td_count increased
    pass

def test_get_hot_players():
    """Test retrieving hot players."""
    hot = PlayerStats.get_hot_players(2025, limit=10)
    assert len(hot) <= 10
    # Verify sorted by recent_td_rate
    pass

def test_form_badge():
    """Test form badge calculation."""
    emoji, label = PlayerStats.get_form_badge(0.5)
    assert emoji == "🔥"
    assert label == "Hot"
```

---

## 6. Performance Optimization

### Indexing
Already included in the schema:
```sql
CREATE INDEX idx_player_stats_season_td_rate ON player_stats(season, td_rate DESC)
```

### Caching (Optional)
```python
@st.cache_data(ttl=3600)  # Cache for 1 hour
def get_hot_players_cached(season: int):
    return PlayerStats.get_hot_players(season)
```

---

## 7. Data Migration from Existing Results

If you have existing graded results, populate player_stats:

```python
def backfill_player_stats(season: int):
    """Populate player_stats from existing results."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Get all correct picks (TDs that were scored)
        cursor.execute("""
            SELECT DISTINCT p.player_name, p.team
            FROM results r
            JOIN picks p ON r.pick_id = p.id
            WHERE r.is_correct = 1 AND p.season = ?
        """, (season,))
        
        players = cursor.fetchall()
        
        for player_name, team in players:
            # Count TDs for this player
            cursor.execute("""
                SELECT COUNT(*) FROM results r
                JOIN picks p ON r.pick_id = p.id
                WHERE p.player_name = ? AND p.team = ? AND p.season = ? AND r.is_correct = 1
            """, (player_name, team, season))
            
            td_count = cursor.fetchone()[0]
            
            # Estimate games (unique weeks)
            cursor.execute("""
                SELECT COUNT(DISTINCT p.week_id) FROM results r
                JOIN picks p ON r.pick_id = p.id
                WHERE p.player_name = ? AND p.team = ? AND p.season = ?
            """, (player_name, team, season))
            
            game_count = cursor.fetchone()[0]
            td_rate = td_count / game_count if game_count > 0 else 0
            
            # Insert into player_stats
            cursor.execute("""
                INSERT OR IGNORE INTO player_stats 
                (season, player_name, team, td_count, game_count, td_rate)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (season, player_name, team, td_count, game_count, td_rate))
        
        conn.commit()
        print(f"Backfilled stats for {len(players)} players")
    finally:
        conn.close()

# Call once:
# backfill_player_stats(2025)
```

---

## 8. Next Steps

1. **Implement `player_stats.py`** - Copy code above, test with unit tests
2. **Add to initialization** - Call `PlayerStats.init_player_stats_table()` on app startup
3. **Integrate with grading** - Call `PlayerStats.update_player_stats()` after each grade
4. **Add public dashboard tab** - Show hot players list and trends
5. **Backfill existing data** - Run migration if you have old results
6. **Test end-to-end** - Grade some picks, verify player_stats updates

---

## 9. Future Enhancements

- **Position-specific insights**: "TEs in this league score more than average"
- **Advanced metrics**: Yards-per-target, red zone touches, snap count percentage
- **Injury tracking**: "Player out, remove from hot list"
- **Seasonal trends**: "This player scores more in December"
- **Correlation analysis**: "If X scores, Y also likely (combo bets)"

---

## 11. Troubleshooting

| Issue | Solution |
|-------|----------|
| Player stats not updating | Verify `update_player_stats()` called after grade |
| Slow queries | Check indexes exist, add caching |
| Duplicate players (name + team) | UNIQUE constraint prevents this |
| Old season data wrong | Backfill with migration script |

