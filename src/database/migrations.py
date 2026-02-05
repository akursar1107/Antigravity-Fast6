"""
Database migrations system for Fast6.
Provides versioned schema evolution with rollback capability.

Usage:
    from src.utils.migrations import run_migrations
    run_migrations()  # Apply all pending migrations
"""

import sqlite3
import logging
from typing import Callable, Dict
from pathlib import Path
from src.utils.error_handling import log_exception, DatabaseError

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
    Get the current schema version from src.database.
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


def migration_v8_add_prediction_market_odds(conn: sqlite3.Connection) -> None:
    """
    Version 8: Add tables for prediction market odds tracking.

    Tables:
    - market_odds: Historical odds snapshots from Polymarket and Kalshi
    - market_outcomes: Resolved market outcomes for comparison analysis
    """
    cursor = conn.cursor()

    # Check if market_odds table already exists
    cursor.execute("PRAGMA table_info(market_odds)")
    columns = [row[1] for row in cursor.fetchall()]

    if not columns:
        # Main odds table - stores historical price snapshots
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS market_odds (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source TEXT NOT NULL CHECK(source IN ('polymarket', 'kalshi', 'odds_api')),
                game_id TEXT NOT NULL,
                season INTEGER NOT NULL,
                week INTEGER NOT NULL,
                player_name TEXT NOT NULL,
                team TEXT,
                implied_probability REAL NOT NULL,
                american_odds INTEGER,
                raw_price REAL,
                volume REAL,
                market_id TEXT,
                snapshot_time TIMESTAMP NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(source, game_id, player_name, snapshot_time)
            )
        """)

        # Market outcomes - tracks resolution for analysis
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS market_outcomes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source TEXT NOT NULL,
                game_id TEXT NOT NULL,
                market_id TEXT NOT NULL,
                player_name TEXT NOT NULL,
                resolved_outcome TEXT CHECK(resolved_outcome IN ('yes', 'no', 'void')),
                actual_first_td_scorer TEXT,
                resolution_time TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(source, market_id)
            )
        """)

        # Indexes for efficient queries
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_market_odds_game ON market_odds(game_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_market_odds_player ON market_odds(player_name)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_market_odds_season_week ON market_odds(season, week)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_market_odds_source ON market_odds(source)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_market_odds_snapshot ON market_odds(snapshot_time)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_market_outcomes_game ON market_outcomes(game_id)")

        conn.commit()
        logger.info("Applied migration v8: Added prediction market tables")
    else:
        logger.info("Migration v8: market_odds table already exists, skipping")


# ============= MIGRATION REGISTRY =============

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
            UNIQUE(season, week, home_team, away_team)
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


def migration_v10_create_rosters_table(conn: sqlite3.Connection) -> None:
    """
    Version 10: Create rosters table for player position normalization.
    
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
            position TEXT NOT NULL,
            jersey_number INTEGER,
            nflreadpy_id TEXT UNIQUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(season, player_name, team)
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


def migration_v11_add_picks_unique_constraint(conn: sqlite3.Connection) -> None:
    """
    Version 11: Add UNIQUE constraint to prevent duplicate picks.
    
    Constraint: UNIQUE(user_id, week_id, player_name)
    
    This prevents:
    - User can't pick same player twice in same week
    - Accidental duplicate imports from CSV
    - UI bugs causing multiple submissions
    """
    cursor = conn.cursor()
    
    # Check if constraint already exists
    cursor.execute("PRAGMA index_list(picks)")
    indexes = cursor.fetchall()
    constraint_exists = any('unique_user_week_player' in str(idx) for idx in indexes)
    
    if constraint_exists:
        logger.info("Migration v11: unique constraint already exists, skipping")
        return
    
    # Before applying unique constraint, remove duplicates
    logger.info("Removing duplicate picks before applying constraint...")
    
    # Keep only the most recent pick for each (user_id, week_id, player_name)
    cursor.execute('''
        DELETE FROM picks WHERE id NOT IN (
            SELECT MAX(id) FROM picks 
            GROUP BY user_id, week_id, player_name
        )
    ''')
    duplicates_removed = cursor.rowcount
    conn.commit()
    if duplicates_removed > 0:
        logger.info(f"Removed {duplicates_removed} duplicate picks")
    
    # Get current schema
    cursor.execute("PRAGMA table_info(picks)")
    columns = cursor.fetchall()
    
    # Create new table with constraint
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
            FOREIGN KEY (week_id) REFERENCES weeks(id)
        )
    ''')
    
    # Copy existing data
    cursor.execute('''
        INSERT INTO picks_new 
        SELECT * FROM picks
    ''')
    
    # Recreate indexes
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_picks_user_week ON picks_new(user_id, week_id)
    ''')
    
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_picks_week_id ON picks_new(week_id)
    ''')
    
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_picks_game_id ON picks_new(game_id)
    ''')
    
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_picks_player_name ON picks_new(player_name)
    ''')
    
    # Drop old table and rename
    cursor.execute('DROP TABLE picks')
    cursor.execute('ALTER TABLE picks_new RENAME TO picks')
    
    conn.commit()
    logger.info("Applied migration v11: Added UNIQUE constraint to picks")


def migration_v12_add_performance_indexes(conn: sqlite3.Connection) -> None:
    """
    Version 12: Add indexes to optimize query performance.
    
    Indexes added:
    - results(is_correct): Filter by graded status
    - results(pick_id): Join with picks
    - player_stats(position, season): WR/RB leader queries
    - player_stats(team): Team-based queries
    - team_ratings(team, week): Recent team ratings
    - market_odds(game_id, snapshot_time): Market history
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
    logger.info("Applied migration v12: Added performance indexes")


def migration_v13_add_triggers(conn: sqlite3.Connection) -> None:
    """
    Version 13: Add database triggers for automatic updates.
    
    Triggers:
    1. update_player_stats_on_result_insert: Increment first_td_count when pick graded
    2. update_player_stats_on_result_delete: Decrement if grading reversed
    
    These triggers maintain the invariant:
        player_stats.first_td_count = COUNT(results where is_correct=1)
    """
    cursor = conn.cursor()
    
    # Check if triggers already exist
    cursor.execute("SELECT name FROM sqlite_master WHERE type='trigger' AND name='update_player_stats_on_result_insert'")
    if cursor.fetchone():
        logger.info("Migration v13: triggers already exist, skipping")
        return
    
    # Trigger 1: Insert
    cursor.execute('''
        CREATE TRIGGER IF NOT EXISTS update_player_stats_on_result_insert
        AFTER INSERT ON results
        FOR EACH ROW
        WHEN NEW.is_correct = 1
        BEGIN
            -- Get the pick details and update player_stats
            INSERT OR IGNORE INTO player_stats (player_name, season, team, position, first_td_count)
            SELECT 
                p.player_name,
                w.season,
                p.team,
                'Unknown',
                0
            FROM picks p
            JOIN weeks w ON p.week_id = w.id
            WHERE p.id = NEW.pick_id;
            
            UPDATE player_stats SET
                first_td_count = first_td_count + 1
            WHERE player_name = (SELECT player_name FROM picks WHERE id = NEW.pick_id)
              AND season = (SELECT season FROM weeks WHERE id = (SELECT week_id FROM picks WHERE id = NEW.pick_id))
              AND team = (SELECT team FROM picks WHERE id = NEW.pick_id);
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
        END
    ''')
    
    conn.commit()
    logger.info("Applied migration v13: Added automation triggers")


def migration_v14_backfill_player_positions(conn: sqlite3.Connection) -> None:
    """
    Version 14: Backfill player positions from rosters table.
    
    This migration looks up positions from rosters table and updates
    player_stats entries that have position='Unknown'.
    
    Note: This only works AFTER rosters have been synced via the ingestion service.
    """
    cursor = conn.cursor()
    
    # Check if rosters table has data
    cursor.execute("SELECT COUNT(*) FROM rosters")
    roster_count = cursor.fetchone()[0]
    
    if roster_count == 0:
        logger.info("Migration v14: No rosters data yet, skipping backfill. Run after roster sync.")
        return
    
    # Update player_stats positions from rosters
    cursor.execute('''
        UPDATE player_stats
        SET position = (
            SELECT r.position 
            FROM rosters r 
            WHERE r.player_name = player_stats.player_name 
              AND r.team = player_stats.team
              AND r.season = player_stats.season
            LIMIT 1
        )
        WHERE position = 'Unknown'
          AND EXISTS (
              SELECT 1 FROM rosters r 
              WHERE r.player_name = player_stats.player_name 
                AND r.team = player_stats.team
                AND r.season = player_stats.season
          )
    ''')
    
    updated_count = cursor.rowcount
    conn.commit()
    
    if updated_count > 0:
        logger.info(f"Applied migration v14: Backfilled {updated_count} player positions")
    else:
        logger.info("Migration v14: No positions to backfill")


MIGRATIONS: Dict[int, tuple[Callable[[sqlite3.Connection], None], str]] = {
    1: (migration_v1_initial_schema, "Initial database schema"),
    2: (migration_v2_add_game_id, "Add game_id to picks table"),
    3: (migration_v3_add_any_time_td, "Add any_time_td to results table"),
    4: (migration_v4_additional_indexes, "Add performance indexes"),
    5: (migration_v5_add_kickoff_decisions_table, "Add kickoff_decisions table"),
    6: (migration_v6_add_player_stats, "Add player_stats table for performance tracking"),
    7: (migration_v7_add_team_ratings, "Add team_ratings table for ELO system"),
    8: (migration_v8_add_prediction_market_odds, "Add prediction market odds tables"),
    9: (migration_v9_create_games_table, "Create games table for NFL schedule"),
    10: (migration_v10_create_rosters_table, "Create rosters table for player positions"),
    11: (migration_v11_add_picks_unique_constraint, "Add unique constraint to picks"),
    12: (migration_v12_add_performance_indexes, "Add performance indexes for queries"),
    13: (migration_v13_add_triggers, "Add triggers for automatic player_stats updates"),
    14: (migration_v14_backfill_player_positions, "Backfill player positions from rosters"),
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
                except sqlite3.IntegrityError as e:
                    log_exception(e, f"migration_v{version}", context={"description": description}, severity="error")
                    raise DatabaseError(f"Migration v{version} failed due to integrity constraint: {description}", context={"version": version})
                except sqlite3.OperationalError as e:
                    log_exception(e, f"migration_v{version}", context={"description": description}, severity="error")
                    raise DatabaseError(f"Migration v{version} failed due to operational error: {description}", context={"version": version})
                except Exception as e:
                    log_exception(e, f"migration_v{version}", context={"description": description}, severity="error")
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
