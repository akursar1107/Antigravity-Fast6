"""
Unified analytics for Opening Drive and Kickoff insights.
Combines First Drive Efficiency, First Game TD, and Kickoff Tendencies.
"""
import pandas as pd
import logging

logger = logging.getLogger(__name__)

def get_opening_drive_stats(pbp_df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate consolidated stats for:
    1. Times Received First (Count of Drive 1 starts as Receiving Team)
    2. First Game TD (Count of scoring the global first TD of the game)
    3. Score on First Drive (Count of scores on their own first possession)

    Returns:
        DataFrame with columns:
        - Team: Team name
        - Times Received First: Count
        - First Game TD: Count of games where they scored the first TD
        - Score on First Drive: Count of times they scored on their own first drive
        - Total Games: Count
    """
    if pbp_df.empty or 'game_id' not in pbp_df.columns or 'posteam' not in pbp_df.columns:
        return pd.DataFrame()

    try:
        # 1. Times Received First (Drive 1 starts)
        # We know Drive 1 posteam = Receiving Team (Step 595, 671 verification)
        first_drives = pbp_df[pbp_df['drive'] == 1].sort_values(['game_id', 'play_id'])
        first_drive_owners = first_drives.groupby('game_id').first().reset_index()
        received_first_counts = first_drive_owners['posteam'].value_counts()

        # 2. First Game TD (Global First TD)
        # Find the first TD of every game
        tds = pbp_df[pbp_df['touchdown'] == 1].sort_values(['game_id', 'play_id'])
        first_tds = tds.groupby('game_id').first().reset_index()
        # td_team is typically posteam, but let's verify if 'td_team' column exists or use posteam
        if 'td_team' in pbp_df.columns:
             first_game_td_counts = first_tds['td_team'].value_counts()
        else:
             first_game_td_counts = first_tds['posteam'].value_counts()

        # 3. Score on First Drive (Own First Possession)
        # We need to find each team's first offensive drive in every game.
        # For the receiving team, it's Drive 1.
        # For the kicking team, it's their first drive (likely Drive 2, but could be Drive 3 if special teams turnover etc.)
        # Let's simplify and assume we track "Score on Opening Drive" for the *Receiving Team* (as requested in "First Drive Efficiency").
        # OR: Does the user want "Times they scored on *their* first drive"?
        # "Times they scored on their first drive of a game" -> Implies Own First Possession.
        
        # To get "Own First Possession" for EVERY team:
        # Group by game and team, find min(drive).
        # Check if they scored on that drive.
        
        # Get all drives
        drives = pbp_df.groupby(['game_id', 'posteam', 'drive']).agg({
            'touchdown': 'sum', 
            'field_goal_result': 'first' # 'made', 'missed', 'blocked'
        }).reset_index()
        
        # Find first drive number for each team in each game
        first_drive_nums = drives.groupby(['game_id', 'posteam'])['drive'].min().reset_index()
        
        # Merge back to get result
        own_first_drives = first_drive_nums.merge(drives, on=['game_id', 'posteam', 'drive'])
        
        # proper score check (TD > 0 or FG == 'made')
        own_first_drives['scored'] = (
            (own_first_drives['touchdown'] > 0) | 
            (own_first_drives['field_goal_result'] == 'made')
        )
        
        first_drive_score_counts = own_first_drives[own_first_drives['scored'] == True]['posteam'].value_counts()

        # Total Games (for context/sorting?)
        total_games_home = pbp_df.groupby('home_team')['game_id'].nunique()
        total_games_away = pbp_df.groupby('away_team')['game_id'].nunique()
        total_games = (total_games_home.add(total_games_away, fill_value=0)).astype(int)

        # Combine
        summary = pd.DataFrame(index=total_games.index)
        summary['Total Games'] = total_games
        summary['Times Received First'] = received_first_counts.reindex(summary.index).fillna(0).astype(int)
        summary['First Game TD'] = first_game_td_counts.reindex(summary.index).fillna(0).astype(int)
        summary['Score on First Drive'] = first_drive_score_counts.reindex(summary.index).fillna(0).astype(int)
        
        # Clean up
        summary.index.name = 'Team'
        summary = summary.reset_index()
        
        return summary.sort_values('Times Received First', ascending=False)

    except Exception as e:
        logger.error(f"Error calculating opening drive stats: {e}")
        return pd.DataFrame()
