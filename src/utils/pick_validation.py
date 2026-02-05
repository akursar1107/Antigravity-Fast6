"""
Pick Validation Utilities
Validates picks before saving to ensure data integrity.
"""

from typing import List, Dict, Optional, Tuple
from datetime import datetime
import pandas as pd
from src.database import get_user_week_picks


class PickValidationError(Exception):
    """Raised when pick validation fails"""
    pass


class PickValidationWarning(Exception):
    """Raised when pick has warnings but can still be saved"""
    pass


def validate_pick(
    player_name: str,
    team: str,
    game_id: str,
    odds: Optional[float],
    user_id: int,
    week_id: int,
    roster_df: pd.DataFrame,
    schedule_df: pd.DataFrame,
    existing_picks: Optional[List[Dict]] = None
) -> Tuple[List[str], List[str]]:
    """
    Validate a pick before saving to database.
    
    Args:
        player_name: Name of player being picked
        team: Team abbreviation
        game_id: NFL game ID
        odds: American odds for the pick
        user_id: User making the pick
        week_id: Week ID from database
        roster_df: NFL roster DataFrame
        schedule_df: NFL schedule DataFrame
        existing_picks: List of existing picks for this user/week
    
    Returns:
        Tuple of (errors, warnings)
        - errors: List of error messages (pick should not be saved)
        - warnings: List of warning messages (pick can be saved but needs review)
    
    Example:
        >>> errors, warnings = validate_pick(
        ...     "Josh Allen", "BUF", "2024_01_BUF_MIA", -200, 1, 5, roster, schedule
        ... )
        >>> if errors:
        ...     print("Cannot save:", errors)
        >>> if warnings:
        ...     print("Warnings:", warnings)
    """
    errors = []
    warnings = []
    
    # 1. Check if player name is provided
    if not player_name or player_name.strip() == "" or player_name == "None":
        errors.append("Player name is required")
        return errors, warnings
    
    # 2. Check if team is valid
    if not team or team == "Unknown":
        errors.append("Team must be specified")
    
    # 3. Validate player exists in roster (if not D/ST)
    if not player_name.endswith(" D/ST"):
        if not roster_df.empty:
            # Try to find player in roster
            player_match = roster_df[
                roster_df['full_name'].str.lower() == player_name.lower()
            ]
            
            if player_match.empty:
                warnings.append(f"Player '{player_name}' not found in {datetime.now().year} roster")
            else:
                # Check if player's team matches pick team
                player_teams = player_match['team'].unique()
                if team not in player_teams:
                    warnings.append(
                        f"Player team mismatch: {player_name} plays for "
                        f"{', '.join(player_teams)}, not {team}"
                    )
    
    # 4. Validate game exists in schedule
    if not schedule_df.empty:
        game_match = schedule_df[schedule_df['game_id'] == game_id]
        
        if game_match.empty:
            errors.append(f"Game ID '{game_id}' not found in schedule")
        else:
            game = game_match.iloc[0]
            
            # Check if game has already started
            try:
                game_date = pd.to_datetime(game['game_date'])
                now = datetime.now()
                
                if game_date < now:
                    warnings.append(
                        f"Game already started on {game_date.strftime('%m/%d/%Y %H:%M')}"
                    )
            except Exception:
                pass  # Skip date check if parsing fails
            
            # Check if team is actually playing in this game
            home_team = game['home_team']
            away_team = game['away_team']
            
            if team not in [home_team, away_team]:
                errors.append(
                    f"Team {team} is not playing in this game "
                    f"({away_team} @ {home_team})"
                )
    
    # 5. Validate odds
    if odds is not None:
        if odds == 0:
            warnings.append("Odds are 0 - this is unusual")
        elif odds < -10000 or odds > 10000:
            warnings.append(f"Odds value ({odds}) seems extreme")
    else:
        warnings.append("No odds provided - theoretical return will be $0")
    
    # 6. Check for duplicate picks
    if existing_picks is None and week_id and user_id:
        existing_picks = get_user_week_picks(user_id, week_id)
    
    if existing_picks:
        # Check if user already has a pick for this team
        for pick in existing_picks:
            if pick.get('team') == team:
                # Same game, might be updating
                if pick.get('game_id') == game_id:
                    warnings.append(f"Updating existing pick for {team}")
                else:
                    errors.append(f"User already has a pick for {team} in a different game")
            
            # Check if picking same player twice
            existing_player = pick.get('player_name', '')
            if existing_player.lower() == player_name.lower():
                if pick.get('game_id') == game_id:
                    warnings.append(f"Updating existing pick for {player_name}")
                else:
                    warnings.append(f"User is picking {player_name} in multiple games")
    
    return errors, warnings


def validate_pick_batch(
    picks: List[Dict],
    roster_df: pd.DataFrame,
    schedule_df: pd.DataFrame
) -> Dict[int, Tuple[List[str], List[str]]]:
    """
    Validate multiple picks at once.
    
    Args:
        picks: List of pick dictionaries with keys: player_name, team, game_id, odds, user_id, week_id
        roster_df: NFL roster DataFrame
        schedule_df: NFL schedule DataFrame
    
    Returns:
        Dictionary mapping pick index to (errors, warnings) tuple
    
    Example:
        >>> results = validate_pick_batch(picks, roster, schedule)
        >>> for idx, (errors, warnings) in results.items():
        ...     if errors:
        ...         print(f"Pick {idx} has errors: {errors}")
    """
    results = {}
    
    for idx, pick in enumerate(picks):
        errors, warnings = validate_pick(
            player_name=pick.get('player_name', ''),
            team=pick.get('team', ''),
            game_id=pick.get('game_id', ''),
            odds=pick.get('odds'),
            user_id=pick.get('user_id'),
            week_id=pick.get('week_id'),
            roster_df=roster_df,
            schedule_df=schedule_df,
            existing_picks=None  # Would need to fetch per user
        )
        
        if errors or warnings:
            results[idx] = (errors, warnings)
    
    return results


def format_validation_message(errors: List[str], warnings: List[str]) -> str:
    """
    Format validation errors and warnings into a user-friendly message.
    
    Args:
        errors: List of error messages
        warnings: List of warning messages
    
    Returns:
        Formatted string for display
    """
    message_parts = []
    
    if errors:
        message_parts.append("**❌ Errors:**")
        for error in errors:
            message_parts.append(f"  • {error}")
    
    if warnings:
        message_parts.append("**⚠️ Warnings:**")
        for warning in warnings:
            message_parts.append(f"  • {warning}")
    
    return "\n".join(message_parts)
