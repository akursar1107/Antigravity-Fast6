"""
Analytics utilities for summarizing First TD data.
"""
from typing import Optional
import pandas as pd


def get_team_first_td_counts(first_tds_df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculates First TD counts by Team (posteam).
    Accepts pre-calculated first_tds DataFrame.
    """
    if first_tds_df is None or first_tds_df.empty:
        return pd.DataFrame()
    counts = first_tds_df['posteam'].value_counts().reset_index()
    counts.columns = ['Team', 'First TDs']
    return counts


def get_player_first_td_counts(first_tds_df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculates First TD counts by Player.
    Accepts pre-calculated first_tds DataFrame.
    """
    if first_tds_df is None or first_tds_df.empty:
        return pd.DataFrame()
    counts = first_tds_df['td_player_name'].value_counts().reset_index()
    counts.columns = ['Player', 'First TDs']
    return counts


def get_position_first_td_counts(first_tds_df: pd.DataFrame, roster_df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculates First TD counts by Position.
    Preferred join: first_tds.td_player_id -> rosters.gsis_id.
    Fallback: name-based join on lowercase trimmed names when IDs are missing.
    """
    if first_tds_df is None or first_tds_df.empty or roster_df is None or roster_df.empty:
        return pd.DataFrame()

    # Preferred: join by IDs
    if 'td_player_id' in first_tds_df.columns and 'gsis_id' in roster_df.columns:
        merged = first_tds_df.merge(roster_df, left_on='td_player_id', right_on='gsis_id', how='left')
        if 'position' in merged.columns:
            counts = merged['position'].value_counts().reset_index()
            counts.columns = ['Position', 'First TDs']
            return counts

    # Fallback: join by normalized names if available
    if 'td_player_name' in first_tds_df.columns and 'full_name' in roster_df.columns:
        tmp_ftd = first_tds_df.copy()
        tmp_ros = roster_df.copy()
        tmp_ftd['__name__'] = tmp_ftd['td_player_name'].astype(str).str.strip().str.lower()
        tmp_ros['__name__'] = tmp_ros['full_name'].astype(str).str.strip().str.lower()
        merged = tmp_ftd.merge(tmp_ros[['__name__', 'position']], on='__name__', how='left')
        if 'position' in merged.columns:
            counts = merged['position'].value_counts().reset_index()
            counts.columns = ['Position', 'First TDs']
            return counts

    return pd.DataFrame()
