"""
Data Export Utilities

Generate CSV snapshots for external analysis:
- Weekly picks with odds and results
- Historical leaderboards
- Player first TD statistics  
- User performance metrics
"""

from typing import Optional
import pandas as pd
from datetime import datetime
import os
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

# Default export directory
DEFAULT_EXPORT_DIR = "data/exports"


def _ensure_export_dir(export_dir: str = DEFAULT_EXPORT_DIR) -> str:
    """Create export directory if it doesn't exist."""
    Path(export_dir).mkdir(parents=True, exist_ok=True)
    return export_dir


def _timestamp_filename(base_name: str, export_dir: str = DEFAULT_EXPORT_DIR) -> str:
    """Generate timestamped filename."""
    now = datetime.now().strftime("%Y%m%d_%H%M%S")
    return os.path.join(export_dir, f"{base_name}_{now}.csv")


def export_weekly_picks_snapshot(
    week_id: int,
    season: int,
    picks_df: pd.DataFrame,
    export_dir: str = DEFAULT_EXPORT_DIR
) -> Optional[str]:
    """
    Export all picks for a week with odds and results.
    
    Args:
        week_id: Week ID
        season: NFL season
        picks_df: DataFrame with pick data (should include: user_name, player_name, team, odds, actual_return, is_correct)
        export_dir: Output directory
        
    Returns:
        Path to exported CSV, or None if failed
    """
    try:
        export_dir = _ensure_export_dir(export_dir)
        
        if picks_df is None or picks_df.empty:
            logger.warning(f"No picks found for week {week_id}")
            return None
        
        output_path = _timestamp_filename(f"picks_week{week_id}_season{season}", export_dir)
        
        # Select relevant columns
        cols = ['user_name', 'player_name', 'team', 'odds', 'actual_return', 'is_correct']
        export_cols = [c for c in cols if c in picks_df.columns]
        
        picks_df[export_cols].to_csv(output_path, index=False)
        logger.info(f"Exported {len(picks_df)} picks to {output_path}")
        return output_path
    
    except Exception as e:
        logger.error(f"Error exporting picks for week {week_id}: {e}")
        return None


def export_leaderboard_history(
    season: int,
    leaderboard_history: list,
    export_dir: str = DEFAULT_EXPORT_DIR
) -> Optional[str]:
    """
    Export historical leaderboard standings (one row per week, per user).
    
    Args:
        season: NFL season
        leaderboard_history: List of dicts with week-by-week standings
                            Each dict: {week, user_name, wins, losses, roi}
        export_dir: Output directory
        
    Returns:
        Path to exported CSV, or None if failed
    """
    try:
        export_dir = _ensure_export_dir(export_dir)
        
        if not leaderboard_history:
            logger.warning(f"No leaderboard history for season {season}")
            return None
        
        output_path = _timestamp_filename(f"leaderboard_history_season{season}", export_dir)
        
        lb_df = pd.DataFrame(leaderboard_history)
        lb_df.to_csv(output_path, index=False)
        logger.info(f"Exported leaderboard history ({len(lb_df)} rows) to {output_path}")
        return output_path
    
    except Exception as e:
        logger.error(f"Error exporting leaderboard history: {e}")
        return None


def export_player_stats(
    season: int,
    player_stats_df: pd.DataFrame,
    export_dir: str = DEFAULT_EXPORT_DIR
) -> Optional[str]:
    """
    Export first TD statistics for all players.
    
    Columns: player_name, team, position, games_played, first_tds, 
             any_time_tds, first_td_rate, avg_odds
    
    Args:
        season: NFL season
        player_stats_df: DataFrame with player statistics
        export_dir: Output directory
        
    Returns:
        Path to exported CSV, or None if failed
    """
    try:
        export_dir = _ensure_export_dir(export_dir)
        
        if player_stats_df is None or player_stats_df.empty:
            logger.warning(f"No player stats for season {season}")
            return None
        
        output_path = _timestamp_filename(f"player_stats_season{season}", export_dir)
        
        player_stats_df.to_csv(output_path, index=False)
        logger.info(f"Exported {len(player_stats_df)} players to {output_path}")
        return output_path
    
    except Exception as e:
        logger.error(f"Error exporting player stats: {e}")
        return None


def export_user_performance(
    season: int,
    user_summaries: list,
    export_dir: str = DEFAULT_EXPORT_DIR
) -> Optional[str]:
    """
    Export detailed user performance metrics.
    
    Args:
        season: NFL season
        user_summaries: List of dicts with user performance data
                       Each dict: {user_name, total_picks, wins, losses, 
                                  win_rate, roi, brier_score, streak}
        export_dir: Output directory
        
    Returns:
        Path to exported CSV, or None if failed
    """
    try:
        export_dir = _ensure_export_dir(export_dir)
        
        if not user_summaries:
            logger.warning(f"No user performance data for season {season}")
            return None
        
        output_path = _timestamp_filename(f"user_performance_season{season}", export_dir)
        
        perf_df = pd.DataFrame(user_summaries)
        perf_df.to_csv(output_path, index=False)
        logger.info(f"Exported {len(perf_df)} users to {output_path}")
        return output_path
    
    except Exception as e:
        logger.error(f"Error exporting user performance: {e}")
        return None


def export_season_snapshot(
    season: int,
    pbp_df: pd.DataFrame,
    picks_df: pd.DataFrame = None,
    leaderboard_df: pd.DataFrame = None,
    export_dir: str = DEFAULT_EXPORT_DIR
) -> dict:
    """
    Export comprehensive season snapshot (multiple files).
    
    Args:
        season: NFL season
        pbp_df: Play-by-play DataFrame
        picks_df: Picks DataFrame (optional)
        leaderboard_df: Leaderboard DataFrame (optional)
        export_dir: Output directory
        
    Returns:
        Dict with 'success' bool and 'files' list of exported paths
    """
    try:
        export_dir = _ensure_export_dir(export_dir)
        
        exported_files = []
        
        # Export PBP summary
        if pbp_df is not None and not pbp_df.empty:
            pbp_path = os.path.join(export_dir, f"pbp_summary_season{season}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv")
            pbp_summary = pbp_df[['game_id', 'week', 'posteam', 'defteam']].drop_duplicates()
            pbp_summary.to_csv(pbp_path, index=False)
            exported_files.append(pbp_path)
        
        # Export picks if provided
        if picks_df is not None and not picks_df.empty:
            picks_path = os.path.join(export_dir, f"season_picks_{season}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv")
            picks_df.to_csv(picks_path, index=False)
            exported_files.append(picks_path)
        
        # Export leaderboard if provided
        if leaderboard_df is not None and not leaderboard_df.empty:
            lb_path = os.path.join(export_dir, f"season_leaderboard_{season}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv")
            leaderboard_df.to_csv(lb_path, index=False)
            exported_files.append(lb_path)
        
        logger.info(f"Exported {len(exported_files)} files for season {season}")
        
        return {
            'success': len(exported_files) > 0,
            'files': exported_files,
            'season': season,
            'timestamp': datetime.now().isoformat()
        }
    
    except Exception as e:
        logger.error(f"Error exporting season snapshot: {e}")
        return {'success': False, 'files': [], 'error': str(e)}


def list_exported_files(export_dir: str = DEFAULT_EXPORT_DIR) -> list:
    """List all exported CSV files."""
    try:
        path = Path(export_dir)
        if not path.exists():
            return []
        return sorted([f.name for f in path.glob("*.csv")], reverse=True)
    except Exception as e:
        logger.error(f"Error listing exports: {e}")
        return []
