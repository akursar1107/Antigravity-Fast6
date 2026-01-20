"""
CSV Import utilities for picks and first TD mapping.
"""
from typing import Dict, Tuple, Optional
import pandas as pd
from utils.nfl_data import load_data, get_game_schedule, get_first_tds
import config
from utils import db_users, db_weeks, db_picks, db_stats


TEAM_CORRECTIONS = {
    "Detriot": "Detroit",
    "San Fran": "San Francisco",
    "Vistor": "Visitor",  # header correction
}


def _normalize_team_name(name: str) -> str:
    if not isinstance(name, str):
        return str(name or "").strip()
    name = name.strip()
    # Apply known corrections
    if name in TEAM_CORRECTIONS:
        name = TEAM_CORRECTIONS[name]
    return name


def _to_abbr(name: str) -> str:
    return config.TEAM_ABBR_MAP.get(name, name)


def _parse_odds(val) -> Optional[int]:
    try:
        if pd.isna(val):
            return None
        s = str(val).strip().replace(",", "")
        if s == "":
            return None
        return int(float(s))
    except Exception:
        return None


def _theoretical_return_from_odds(odds: Optional[int]) -> Optional[float]:
    if odds is None:
        return None
    try:
        if odds > 0:
            return float(odds) / 100.0
        elif odds < 0:
            return 100.0 / abs(float(odds))
        else:
            return 0.0
    except Exception:
        return None


def ingest_picks_from_csv(file_path: str, season: int) -> Dict[str, int]:
    """
    Import picks from a CSV file and associate game_id using Home/Visitor + Week matching.
    Auto-wipes existing season data before import.
    Expected columns: Week, Gameday, Picker, Visitor (or Vistor), Home, Player, 1st TD Odds
    """
    # Wipe season data first
    deleted = db_stats.delete_season_data(int(season))

    df = pd.read_csv(file_path)
    cols = [c.strip() for c in df.columns]
    df.columns = cols

    # Handle misspelled header 'Vistor'
    if 'Visitor' not in df.columns and 'Vistor' in df.columns:
        df.rename(columns={'Vistor': 'Visitor'}, inplace=True)

    # Filter to regular-season numeric weeks (1-18)
    def _week_to_int(w):
        try:
            return int(str(w).strip())
        except Exception:
            return None

    df['WeekInt'] = df['Week'].apply(_week_to_int)
    df = df[df['WeekInt'].between(1, 18, inclusive='both')]

    # Load schedule once
    pbp = load_data(int(season))
    schedule = get_game_schedule(pbp, int(season))

    picks_imported = 0

    for _, row in df.iterrows():
        try:
            week = int(row['WeekInt'])
            picker = str(row['Picker']).strip()
            away_raw = _normalize_team_name(row['Visitor'])
            home_raw = _normalize_team_name(row['Home'])
            player = str(row['Player']).strip()
            odds = _parse_odds(row.get('1st TD Odds'))
            theo = _theoretical_return_from_odds(odds)

            # Map to abbreviations
            away = _to_abbr(away_raw)
            home = _to_abbr(home_raw)

            # Find or create user
            user = db_users.get_user_by_name(picker)
            if not user:
                user_id = db_users.add_user(picker)
            else:
                user_id = user['id']

            # Ensure week exists
            week_row = db_weeks.get_week_by_season_week(int(season), week)
            if not week_row:
                week_id = db_weeks.add_week(int(season), week)
            else:
                week_id = week_row['id']

            # Match game_id
            game_id = None
            if not schedule.empty:
                match = schedule[(schedule['week'] == week) & (schedule['home_team'] == home) & (schedule['away_team'] == away)]
                if not match.empty:
                    game_id = str(match.iloc[0]['game_id'])

            # Store pick with Unknown team; grading will prefer game_id
            db_picks.add_pick(
                user_id=user_id,
                week_id=week_id,
                team='Unknown',
                player_name=player,
                odds=odds,
                theoretical_return=theo,
                game_id=game_id
            )
            picks_imported += 1
        except Exception:
            # Skip bad rows quietly for now
            continue

    return {
        'picks_deleted': deleted.get('picks_deleted', 0),
        'results_deleted': deleted.get('results_deleted', 0),
        'picks_imported': picks_imported,
        'results_imported': 0
    }


def get_first_td_map(season: int, week: Optional[int] = None) -> Dict[str, Dict[str, str]]:
    """
    Build a map of game_id -> {player, team, desc} for first TDs.
    """
    df = load_data(int(season))
    ftd = get_first_tds(df)
    if ftd.empty:
        return {}
    if week is not None:
        ftd = ftd[ftd['week'] == int(week)]
    mapping: Dict[str, Dict[str, str]] = {}
    for _, r in ftd.iterrows():
        mapping[str(r['game_id'])] = {
            'player': str(r.get('td_player_name', '') or ''),
            'team': str(r.get('posteam', '') or ''),
            'desc': str(r.get('desc', '') or ''),
        }
    return mapping
