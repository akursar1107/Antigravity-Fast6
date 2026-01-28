"""
Analytics for first drive rushing/passing success rates.
"""
import pandas as pd

def get_first_drive_success_rates(pbp_df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate rushing and passing success rates on first drives (offense and defense).
    Returns DataFrame with team, rush_success_rate, pass_success_rate.
    """
    if pbp_df.empty or 'game_id' not in pbp_df.columns or 'posteam' not in pbp_df.columns:
        return pd.DataFrame()
    # Filter for first drives
    first_drives = pbp_df[pbp_df['drive'] == 1]
    # Define success: gain >= 4 yards on 1st down, >= 6 on 2nd, >= 3 on 3rd/4th
    def is_success(row):
        if row['down'] == 1:
            return row['yards_gained'] >= 4
        elif row['down'] == 2:
            return row['yards_gained'] >= 6
        else:
            return row['yards_gained'] >= 3
    first_drives = first_drives.copy()
    first_drives['success'] = first_drives.apply(is_success, axis=1)
    rush = first_drives[first_drives['play_type'] == 'run']
    pass_ = first_drives[first_drives['play_type'] == 'pass']
    rush_rates = rush.groupby('posteam')['success'].mean().rename('rush_success_rate')
    pass_rates = pass_.groupby('posteam')['success'].mean().rename('pass_success_rate')
    summary = pd.concat([rush_rates, pass_rates], axis=1).reset_index().rename(columns={'posteam': 'Team'})
    return summary
