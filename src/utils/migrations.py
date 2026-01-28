"""
Database migrations system for Fast6.
Provides versioned schema evolution with rollback capability.

Usage:
    from utils.migrations import run_migrations
    run_migrations()  # Apply all pending migrations
"""

import sqlite3
import logging
from typing import Callable, Dict
from pathlib import Path

logger = logging.getLogger(__name__)

# Database file location
DB_PATH = Path(__file__).parent.parent.parent / "data" / "fast6.db"


def get_connection() -> sqlite3.Connection:
    """Get a database connection."""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def _ensure_schema_version_table(conn: sqlite3.Connection) -> None:
    """Create schema_version table if it doesn't exist."""
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS schema_version (
            version INTEGER PRIMARY KEY,
            applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            description TEXT
        )
    """)
    conn.commit()


def get_current_version(conn: sqlite3.Connection) -> int:
    """
    Get the current schema version from database.
    Returns 0 if no version is recorded (new database).
    """
    _ensure_schema_version_table(conn)
    cursor = conn.cursor()
    cursor.execute("SELECT MAX(version) FROM schema_version")
    result = cursor.fetchone()
    return result[0] if result[0] is not None else 0


def set_version(conn: sqlite3.Connection, version: int, description: str) -> None:
    """Record a migration version in the database."""
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO schema_version (version, description) VALUES (?, ?)",
        (version, description)
    )
    conn.commit()




def migration_v5_add_kickoff_decisions_table(conn: sqlite3.Connection) -> None:
    """
    Version 5: Add kickoff_decisions table to track team kickoff choices per game.
    Columns: id, game_id, team, decision (RECEIVE/DEFER), result (TD/No TD/FG/Other), created_at
    """
    cursor = conn.cursor()
    cursor.execute("PRAGMA table_info(kickoff_decisions)")
    columns = [row[1] for row in cursor.fetchall()]
    if not columns:
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS kickoff_decisions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                game_id TEXT NOT NULL,
                team TEXT NOT NULL,
                decision TEXT CHECK(decision IN ('RECEIVE','DEFER')) NOT NULL,
                result TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_kickoff_game_id ON kickoff_decisions(game_id)")
        conn.commit()
        logger.info("Applied migration v5: Added kickoff_decisions table")
    else:
        logger.info("Migration v5: kickoff_decisions table already exists, skipping")

# ============= MIGRATION FUNCTIONS =============

def migration_v1_initial_schema(conn: sqlite3.Connection) -> None:
    def migration_v5_add_kickoff_decisions_table(conn: sqlite3.Connection) -> None:
        """
        Version 5: Add kickoff_decisions table to track team kickoff choices per game.
        Columns: id, game_id, team, decision (RECEIVE/DEFER), result (TD/No TD/FG/Other), created_at
        """
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(kickoff_decisions)")
        columns = [row[1] for row in cursor.fetchall()]
        if not columns:
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS kickoff_decisions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    game_id TEXT NOT NULL,
                    team TEXT NOT NULL,
                    decision TEXT CHECK(decision IN ('RECEIVE','DEFER')) NOT NULL,
                    result TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_kickoff_game_id ON kickoff_decisions(game_id)")
            conn.commit()
            logger.info("Applied migration v5: Added kickoff_decisions table")
        else:
            logger.info("Migration v5: kickoff_decisions table already exists, skipping")
    """
    Version 1: Initial database schema.
    Creates users, weeks, picks, and results tables with basic indexes.
    """
    cursor = conn.cursor()
    
    # Users table - group members
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            email TEXT UNIQUE,
            group_id INTEGER DEFAULT 1,
            is_admin BOOLEAN DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Weeks table - seasons and weeks
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS weeks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            season INTEGER NOT NULL,
            week INTEGER NOT NULL,
            started_at TIMESTAMP,
            ended_at TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(season, week)
        )
    """)
    
    # Picks table - user predictions
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS picks (
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
        )
    """)
    
    # Results table - actual outcomes
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            pick_id INTEGER NOT NULL UNIQUE,
            actual_scorer TEXT,
            is_correct BOOLEAN DEFAULT NULL,
            actual_return REAL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (pick_id) REFERENCES picks(id) ON DELETE CASCADE
        )
    """)
    
    # Create basic indexes
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_picks_user_week ON picks(user_id, week_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_results_pick_id ON results(pick_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_weeks_season ON weeks(season)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_weeks_season_week ON weeks(season, week)")
    
    conn.commit()
    logger.info("Applied migration v1: Initial schema")


def migration_v2_add_game_id(conn: sqlite3.Connection) -> None:
    """
    Version 2: Add game_id column to picks table.
    Allows linking picks directly to NFL game identifiers.
    """
    cursor = conn.cursor()
    
    # Check if column already exists
    cursor.execute("PRAGMA table_info(picks)")
    columns = [row[1] for row in cursor.fetchall()]
    
    if 'game_id' not in columns:
        cursor.execute("ALTER TABLE picks ADD COLUMN game_id TEXT")
        # Create index for game_id lookups
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_picks_game_id ON picks(game_id)")
        conn.commit()
        logger.info("Applied migration v2: Added game_id column to picks")
    else:
        logger.info("Migration v2: game_id column already exists, skipping")


def migration_v3_add_any_time_td(conn: sqlite3.Connection) -> None:
    """
    Version 3: Add any_time_td column to results table.
    Tracks whether player scored any TD (not just first TD).
    """
    cursor = conn.cursor()
    
    # Check if column already exists
    cursor.execute("PRAGMA table_info(results)")
    columns = [row[1] for row in cursor.fetchall()]
    
    if 'any_time_td' not in columns:
        cursor.execute("ALTER TABLE results ADD COLUMN any_time_td BOOLEAN DEFAULT NULL")
        conn.commit()
        logger.info("Applied migration v3: Added any_time_td column to results")
    else:
        logger.info("Migration v3: any_time_td column already exists, skipping")


def migration_v4_additional_indexes(conn: sqlite3.Connection) -> None:
    """
    Version 4: Add additional performance indexes.
    Improves query performance for leaderboard and grading operations.
    """
    cursor = conn.cursor()
    
    # Additional indexes for query optimization
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_picks_week_id ON picks(week_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_picks_user_id ON picks(user_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_results_correct ON results(is_correct)")
    
    conn.commit()
    logger.info("Applied migration v4: Additional performance indexes")


def migration_v6_add_player_stats(conn: sqlite3.Connection) -> None:
    """
    Version 6: Add player_stats table for tracking player performance over time.
    Enables hot/cold player tracking, TD rates, and performance trends.
    """
    cursor = conn.cursor()
    
    # Check if table already exists
    cursor.execute("PRAGMA table_info(player_stats)")
    columns = [row[1] for row in cursor.fetchall()]
    
    if not columns:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS player_stats (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                player_name TEXT NOT NULL,
                season INTEGER NOT NULL,
                team TEXT NOT NULL,
                position TEXT,
                games_played INTEGER DEFAULT 0,
                first_td_count INTEGER DEFAULT 0,
                any_time_td_count INTEGER DEFAULT 0,
                red_zone_targets INTEGER DEFAULT 0,
                red_zone_touches INTEGER DEFAULT 0,
                last_td_week INTEGER,
                recent_form TEXT DEFAULT 'AVERAGE',
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(player_name, season, team)
            )
        """)
        
        # Create indexes for efficient lookups
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_player_stats_season ON player_stats(season)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_player_stats_team ON player_stats(team)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_player_stats_position ON player_stats(position)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_player_stats_form ON player_stats(recent_form)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_player_stats_name_season ON player_stats(player_name, season)")
        
        conn.commit()
        logger.info("Applied migration v6: Added player_stats table")
    else:
        logger.info("Migration v6: player_stats table already exists, skipping")


def migration_v7_add_team_ratings(conn: sqlite3.Connection) -> None:
    """
    Version 7: Add team_ratings table for ELO-based team strength tracking.
    Enables power rankings and matchup difficulty assessment.
    """
    cursor = conn.cursor()
    
    # Check if table already exists
    cursor.execute("PRAGMA table_info(team_ratings)")
    columns = [row[1] for row in cursor.fetchall()]
    
    if not columns:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS team_ratings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                team TEXT NOT NULL,
                season INTEGER NOT NULL,
                week INTEGER NOT NULL,
                elo_rating REAL DEFAULT 1500.0,
                offensive_rating REAL DEFAULT 1500.0,
                defensive_rating REAL DEFAULT 1500.0,
                games_played INTEGER DEFAULT 0,
                wins INTEGER DEFAULT 0,
                losses INTEGER DEFAULT 0,
                points_for INTEGER DEFAULT 0,
                points_against INTEGER DEFAULT 0,
                rating_trend TEXT DEFAULT 'STABLE',
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(team, season, week)
            )
        """)
        
        # Create indexes for efficient lookups
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_team_ratings_season ON team_ratings(season)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_team_ratings_week ON team_ratings(season, week)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_team_ratings_team ON team_ratings(team)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_team_ratings_elo ON team_ratings(elo_rating)")
        
        conn.commit()
        logger.info("Applied migration v7: Added team_ratings table")
    else:
        logger.info("Migration v7: team_ratings table already exists, skipping")


# ============= MIGRATION REGISTRY =============

MIGRATIONS: Dict[int, tuple[Callable[[sqlite3.Connection], None], str]] = {
    1: (migration_v1_initial_schema, "Initial database schema"),
    2: (migration_v2_add_game_id, "Add game_id to picks table"),
    3: (migration_v3_add_any_time_td, "Add any_time_td to results table"),
    4: (migration_v4_additional_indexes, "Add performance indexes"),
    5: (migration_v5_add_kickoff_decisions_table, "Add kickoff_decisions table"),
    6: (migration_v6_add_player_stats, "Add player_stats table for performance tracking"),
    7: (migration_v7_add_team_ratings, "Add team_ratings table for ELO system"),
}


def run_migrations() -> Dict[str, int]:
    """
    Run all pending database migrations.
    
    Returns:
        Dict with migration statistics:
        - current_version: Version before migrations
        - target_version: Latest migration version
        - applied_count: Number of migrations applied
    """
    conn = get_connection()
    
    try:
        current_version = get_current_version(conn)
        target_version = max(MIGRATIONS.keys()) if MIGRATIONS else 0
        applied_count = 0
        
        logger.info(f"Current schema version: {current_version}, target: {target_version}")
        
        # Apply migrations in order
        for version in sorted(MIGRATIONS.keys()):
            if version > current_version:
                migration_func, description = MIGRATIONS[version]
                logger.info(f"Applying migration v{version}: {description}")
                
                try:
                    migration_func(conn)
                    set_version(conn, version, description)
                    applied_count += 1
                    logger.info(f"✓ Migration v{version} applied successfully")
                except Exception as e:
                    logger.error(f"✗ Migration v{version} failed: {e}")
                    raise
        
        if applied_count == 0:
            logger.info("Database schema is up to date")
        else:
            logger.info(f"Applied {applied_count} migration(s). Schema now at version {target_version}")
        
        return {
            'current_version': current_version,
            'target_version': target_version,
            'applied_count': applied_count
        }
    
    finally:
        conn.close()


def get_migration_history(conn: sqlite3.Connection) -> list:
    """Get the history of applied migrations."""
    _ensure_schema_version_table(conn)
    cursor = conn.cursor()
    cursor.execute("SELECT version, applied_at, description FROM schema_version ORDER BY version")
    return [dict(row) for row in cursor.fetchall()]


if __name__ == "__main__":
    # Test migrations
    print("Running database migrations...")
    result = run_migrations()
    print(f"Applied {result['applied_count']} migration(s)")
    print(f"Schema version: {result['current_version']} → {result['target_version']}")
