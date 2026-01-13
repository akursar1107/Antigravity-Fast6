"""
Clean CSV Import Module
Imports picks from CSV with comprehensive validation and automatic team detection.
"""

import logging
import pandas as pd
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import re

from .nfl_data import get_game_schedule, load_rosters
from .name_matching import names_match
from .db_connection import get_db_connection
from .db_users import add_user, get_all_users
from .db_weeks import add_week, get_week_by_season_week
from .db_picks import add_pick
import config

logger = logging.getLogger(__name__)


# Valid NFL team abbreviations
VALID_TEAMS = set(config.TEAM_ABBR_MAP.values())

# Valid positions
VALID_POSITIONS = {'QB', 'RB', 'WR', 'TE', 'FB', 'OL', 'DL', 'LB', 'DB', 'K', 'P'}

# Default odds if none provided
DEFAULT_ODDS = -110


class ImportValidationError(Exception):
    """Raised when CSV data fails validation."""
    pass


class ImportResult:
    """Container for import results and statistics."""
    def __init__(self):
        self.success_count = 0
        self.error_count = 0
        self.warning_count = 0
        self.errors: List[Dict] = []
        self.warnings: List[Dict] = []
        self.success_picks: List[Dict] = []
        
    def add_error(self, row_num: int, field: str, message: str, row_data: Dict = None):
        """Add an error for a specific row."""
        self.error_count += 1
        self.errors.append({
            'row': row_num,
            'field': field,
            'message': message,
            'data': row_data
        })
        
    def add_warning(self, row_num: int, field: str, message: str):
        """Add a warning for a specific row."""
        self.warning_count += 1
        self.warnings.append({
            'row': row_num,
            'field': field,
            'message': message
        })
        
    def add_success(self, row_num: int, pick_data: Dict):
        """Record a successful import."""
        self.success_count += 1
        self.success_picks.append({
            'row': row_num,
            **pick_data
        })
        
    def get_summary(self) -> str:
        """Get human-readable summary."""
        summary = f"""
=== Import Summary ===
✓ Successful: {self.success_count}
✗ Errors: {self.error_count}
⚠ Warnings: {self.warning_count}
"""
        if self.errors:
            summary += "\n--- Errors ---\n"
            for err in self.errors[:10]:  # Show first 10
                summary += f"Row {err['row']}: {err['field']} - {err['message']}\n"
            if len(self.errors) > 10:
                summary += f"... and {len(self.errors) - 10} more errors\n"
                
        if self.warnings:
            summary += "\n--- Warnings ---\n"
            for warn in self.warnings[:10]:
                summary += f"Row {warn['row']}: {warn['field']} - {warn['message']}\n"
            if len(self.warnings) > 10:
                summary += f"... and {len(self.warnings) - 10} more warnings\n"
                
        return summary


def validate_week(week_value) -> Optional[int]:
    """Validate week number is valid NFL week."""
    try:
        week = int(week_value)
        if 1 <= week <= 22:  # Regular season (1-18) + Playoffs (19-22)
            return week
    except (ValueError, TypeError):
        pass
    return None


def validate_team(team: str) -> Optional[str]:
    """Validate and normalize team abbreviation."""
    if not team:
        return None
    
    team = str(team).strip().upper()
    
    # Check if it's already a valid abbreviation
    if team in VALID_TEAMS:
        return team
    
    # Try to find it in the full name mapping
    for full_name, abbr in config.TEAM_ABBR_MAP.items():
        if team.lower() == full_name.lower():
            return abbr
    
    return None


def parse_odds(odds_value) -> float:
    """Parse odds value, default to -110 if empty or invalid."""
    if pd.isna(odds_value) or odds_value == '' or odds_value is None:
        return DEFAULT_ODDS
    
    try:
        odds = float(odds_value)
        # Sanity check - odds should be reasonable
        if -10000 <= odds <= 10000:
            return odds
    except (ValueError, TypeError):
        logger.warning(f"Invalid odds value: {odds_value}, using default {DEFAULT_ODDS}")
    
    return DEFAULT_ODDS


def calculate_theoretical_return(odds: float, bet_size: float = 1.0) -> float:
    """Calculate theoretical return from odds."""
    if odds >= 0:
        return bet_size * (odds / 100)
    else:
        return bet_size * (100 / abs(odds))


def find_game_id(season: int, week: int, visitor: str, home: str, schedule_df: pd.DataFrame) -> Optional[str]:
    """
    Find game_id from schedule data.
    
    Args:
        season: NFL season year
        week: Week number
        visitor: Away team abbreviation
        home: Home team abbreviation
        schedule_df: Schedule DataFrame from get_game_schedule()
        
    Returns:
        game_id string or None if not found
    """
    if schedule_df.empty:
        return None
    
    # Filter to this week
    week_games = schedule_df[schedule_df['week'] == week]
    
    # Find matching game
    matching_games = week_games[
        (week_games['away_team'] == visitor) & 
        (week_games['home_team'] == home)
    ]
    
    if not matching_games.empty:
        return matching_games.iloc[0]['game_id']
    
    # Try reverse (in case visitor/home are swapped)
    matching_games = week_games[
        (week_games['away_team'] == home) & 
        (week_games['home_team'] == visitor)
    ]
    
    if not matching_games.empty:
        logger.warning(f"Teams appear swapped for Week {week}: {visitor} @ {home}")
        return matching_games.iloc[0]['game_id']
    
    return None


def find_player_team(player_name: str, season: int, rosters_df: pd.DataFrame) -> Optional[str]:
    """
    Find which team a player belongs to by searching rosters.
    Uses fuzzy matching and returns the BEST match (highest similarity score).
    
    Args:
        player_name: Player's name
        season: NFL season
        rosters_df: DataFrame of rosters from load_rosters()
        
    Returns:
        Team abbreviation or None if not found
    """
    if not player_name or rosters_df.empty:
        return None
    
    from difflib import SequenceMatcher
    
    best_match_team = None
    best_match_name = None
    best_score = 0.0  # Will track highest score among matches
    
    # Search roster DataFrame and find BEST match
    for _, player_row in rosters_df.iterrows():
        roster_name = player_row.get('full_name', '')
        if not roster_name:
            continue
        
        # Use the same name matching logic from name_matching.py
        # This handles last names, abbreviations, etc.
        if names_match(player_name, roster_name, threshold=0.70):
            # Calculate score to find the BEST match among all matches
            score = SequenceMatcher(None, player_name.lower(), roster_name.lower()).ratio()
            
            if score > best_score:
                best_score = score
                best_match_team = player_row.get('team', None)
                best_match_name = roster_name
    
    # Log the best match found for debugging
    if best_match_team:
        logger.debug(f"Matched '{player_name}' → '{best_match_name}' ({best_match_team}) [score: {best_score:.3f}]")
    
    return best_match_team


def import_picks_from_csv(
    csv_path: str,
    season: int,
    dry_run: bool = False,
    auto_create_users: bool = True,
    corrections: Dict = None
) -> ImportResult:
    """
    Import picks from CSV with comprehensive validation.
    
    CSV Format Expected:
    Week | Gameday | Picker | Visitor | Home | Player | Position | 1st TD Odds
    
    Args:
        csv_path: Path to CSV file
        season: NFL season year
        dry_run: If True, validate only without inserting
        auto_create_users: If True, create users that don't exist
        corrections: Dict of {row_num: {'player': name, 'team': abbr}} for corrected picks
        
    Returns:
        ImportResult with statistics and error details
    """
    result = ImportResult()
    corrections = corrections or {}
    
    logger.info(f"Starting CSV import for season {season}")
    logger.info(f"Dry run: {dry_run}")
    if corrections:
        logger.info(f"Applying {len(corrections)} corrections")
    
    # Load CSV
    try:
        df = pd.read_csv(csv_path)
    except Exception as e:
        result.add_error(0, 'file', f"Failed to read CSV: {e}")
        return result
    
    # Validate required columns
    required_columns = ['Week', 'Picker', 'Visitor', 'Home', 'Player']
    missing_columns = [col for col in required_columns if col not in df.columns]
    if missing_columns:
        result.add_error(0, 'columns', f"Missing required columns: {missing_columns}")
        return result
    
    # Load NFL data
    logger.info("Loading NFL schedule and roster data...")
    try:
        from .nfl_data import load_data
        nfl_data = load_data(season)
        schedule = get_game_schedule(nfl_data, season)
        rosters = load_rosters(season)
    except Exception as e:
        result.add_error(0, 'nfl_data', f"Failed to load NFL data: {e}")
        return result
    
    # Get existing users
    existing_users = {user['name'].lower(): user for user in get_all_users()}
    
    # Process each row
    for idx, row in df.iterrows():
        row_num = idx + 2  # +2 because Excel is 1-indexed and has header row
        
        try:
            # Extract and validate basic fields
            week = validate_week(row.get('Week'))
            if week is None:
                result.add_error(row_num, 'Week', f"Invalid week: {row.get('Week')}")
                continue
            
            picker = str(row.get('Picker', '')).strip()
            if not picker:
                result.add_error(row_num, 'Picker', "Picker name is empty")
                continue
            
            visitor = validate_team(row.get('Visitor'))
            if visitor is None:
                result.add_error(row_num, 'Visitor', f"Invalid team: {row.get('Visitor')}")
                continue
            
            home = validate_team(row.get('Home'))
            if home is None:
                result.add_error(row_num, 'Home', f"Invalid team: {row.get('Home')}")
                continue
            
            player_name = str(row.get('Player', '')).strip()
            if not player_name:
                result.add_error(row_num, 'Player', "Player name is empty")
                continue
            
            # Parse odds
            odds = parse_odds(row.get('1st TD Odds'))
            if odds == DEFAULT_ODDS and pd.notna(row.get('1st TD Odds')):
                result.add_warning(row_num, '1st TD Odds', f"Invalid odds, using default {DEFAULT_ODDS}")
            
            theoretical_return = calculate_theoretical_return(odds)
            
            # Find game_id
            game_id = find_game_id(season, week, visitor, home, schedule)
            if not game_id:
                result.add_error(row_num, 'Game', f"Game not found: Week {week}, {visitor} @ {home}")
                continue
            
            # Find player's team from roster
            player_team = find_player_team(player_name, season, rosters)
            if not player_team:
                result.add_warning(row_num, 'Player Team', f"Player '{player_name}' not found in rosters, will set to Unknown")
                player_team = 'Unknown'
            
            # Check if this row has a correction
            if row_num in corrections:
                correction = corrections[row_num]
                player_name = correction['player']
                player_team = correction['team']
                logger.info(f"Applied correction for Row {row_num}: {player_name} ({player_team})")
            
            # Validate player's team is in the game
            if player_team != 'Unknown' and player_team not in [visitor, home]:
                result.add_error(
                    row_num, 
                    'Team Validation',
                    f"{player_name} plays for {player_team}, but game is {visitor} @ {home}",
                    row_data={'player': player_name, 'team': player_team, 'game': f"{visitor} @ {home}", 'game_id': game_id}
                )
                continue
            
            # Handle user
            picker_lower = picker.lower()
            if picker_lower in existing_users:
                user = existing_users[picker_lower]
                user_id = user['id']
            elif auto_create_users:
                if not dry_run:
                    user_id = add_user(picker)
                    existing_users[picker_lower] = {'id': user_id, 'name': picker}
                    logger.info(f"Created new user: {picker}")
                else:
                    user_id = -1  # Placeholder for dry run
                result.add_warning(row_num, 'User', f"Will create new user: {picker}")
            else:
                result.add_error(row_num, 'User', f"User '{picker}' does not exist")
                continue
            
            # Get or create week
            week_record = get_week_by_season_week(season, week)
            if not week_record:
                if not dry_run:
                    week_id = add_week(season, week)
                    logger.info(f"Created week: Season {season}, Week {week}")
                else:
                    week_id = -1  # Placeholder
            else:
                week_id = week_record['id']
            
            # Check for duplicates
            if not dry_run:
                conn = get_db_connection()
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT COUNT(*) FROM picks 
                    WHERE user_id = ? AND week_id = ? AND player_name = ?
                """, (user_id, week_id, player_name))
                duplicate_count = cursor.fetchone()[0]
                conn.close()
                
                if duplicate_count > 0:
                    result.add_warning(row_num, 'Duplicate', f"Pick already exists for {picker}/{player_name}/Week{week}")
                    continue
            
            # Insert pick
            if not dry_run:
                pick_id = add_pick(
                    user_id=user_id,
                    week_id=week_id,
                    team=player_team,
                    player_name=player_name,
                    odds=odds,
                    theoretical_return=theoretical_return,
                    game_id=game_id
                )
                logger.info(f"✓ Row {row_num}: {picker} - {player_name} ({player_team}) Week {week}")
            
            result.add_success(row_num, {
                'picker': picker,
                'week': week,
                'player': player_name,
                'team': player_team,
                'game': f"{visitor} @ {home}",
                'odds': odds
            })
            
        except Exception as e:
            result.add_error(row_num, 'Exception', f"Unexpected error: {str(e)}")
            logger.error(f"Error processing row {row_num}: {e}", exc_info=True)
    
    logger.info(result.get_summary())
    return result
