"""
NFL Data Loader - Centralized data loading with intelligent caching.

Single point of access for NFL PBP data, schedules, rosters, and TD lookups.
Supports lazy loading and pre-built caches.
"""

from typing import Optional, Dict, Tuple
import pandas as pd
from utils.nfl_data import load_data, get_game_schedule, load_rosters, get_first_tds


class TDLookupCache:
    """Fast lookup cache for first TD scorers by game."""
    
    def __init__(self, first_tds_df: pd.DataFrame):
        """
        Initialize TD cache from first TDs DataFrame.
        
        Args:
            first_tds_df: DataFrame with first TD records
        """
        self._cache: Dict[str, pd.DataFrame] = {}
        self._first_tds = first_tds_df
        self._build_cache()
    
    def _build_cache(self):
        """Pre-build game_id index for fast lookup."""
        if self._first_tds is None or self._first_tds.empty:
            return
        
        for game_id in self._first_tds['game_id'].unique():
            game_tds = self._first_tds[self._first_tds['game_id'] == game_id]
            self._cache[game_id] = game_tds
    
    def get_first_td_for_game(self, game_id: str) -> pd.DataFrame:
        """
        Get first TD scorer(s) for a specific game.
        
        Args:
            game_id: Game ID (e.g., '2025_01_KC_TB')
            
        Returns:
            DataFrame with first TD records for that game, or empty DataFrame
        """
        return self._cache.get(game_id, pd.DataFrame())
    
    def get_first_tds_for_team(self, team: str) -> pd.DataFrame:
        """
        Get all first TDs scored by a team.
        
        Args:
            team: Team abbreviation
            
        Returns:
            DataFrame with all first TDs by that team
        """
        return self._first_tds[self._first_tds['posteam'] == team] if self._first_tds is not None else pd.DataFrame()


class NFLDataLoader:
    """
    Centralized NFL data loading with intelligent caching.
    
    Lazy-loads expensive data, pre-builds indices for fast lookups.
    """
    
    def __init__(self, season: int):
        """
        Initialize data loader for a season.
        
        Args:
            season: NFL season (e.g., 2025)
        """
        self.season = season
        self._pbp_data = None
        self._schedule = None
        self._rosters = None
        self._first_tds = None
        self._td_cache = None
        self._is_initialized = False
    
    @property
    def pbp_data(self) -> pd.DataFrame:
        """Lazy-load play-by-play data."""
        if self._pbp_data is None:
            self._pbp_data = self._load_pbp()
        return self._pbp_data
    
    @property
    def schedule(self) -> pd.DataFrame:
        """Lazy-load schedule data."""
        if self._schedule is None:
            self._schedule = self._load_schedule()
        return self._schedule
    
    @property
    def rosters(self) -> pd.DataFrame:
        """Lazy-load roster data."""
        if self._rosters is None:
            self._rosters = self._load_rosters()
        return self._rosters
    
    @property
    def first_tds(self) -> pd.DataFrame:
        """Get first TDs (derived from PBP)."""
        if self._first_tds is None:
            self._first_tds = self._extract_first_tds()
        return self._first_tds
    
    @property
    def td_cache(self) -> TDLookupCache:
        """Get or build TD lookup cache."""
        if self._td_cache is None:
            self._td_cache = TDLookupCache(self.first_tds)
        return self._td_cache
    
    def _load_pbp(self) -> pd.DataFrame:
        """Load PBP data from nflreadpy."""
        try:
            return load_data(self.season)
        except Exception as e:
            print(f"Error loading PBP data for {self.season}: {e}")
            return pd.DataFrame()
    
    def _load_schedule(self) -> pd.DataFrame:
        """Load schedule data."""
        try:
            pbp = self.pbp_data
            return get_game_schedule(pbp, self.season) if not pbp.empty else pd.DataFrame()
        except Exception as e:
            print(f"Error loading schedule for {self.season}: {e}")
            return pd.DataFrame()
    
    def _load_rosters(self) -> pd.DataFrame:
        """Load roster data."""
        try:
            return load_rosters(self.season)
        except Exception as e:
            print(f"Error loading rosters for {self.season}: {e}")
            return pd.DataFrame()
    
    def _extract_first_tds(self) -> pd.DataFrame:
        """Extract first TDs from PBP."""
        try:
            from utils.nfl_data import get_first_tds
            pbp = self.pbp_data
            return get_first_tds(pbp) if not pbp.empty else pd.DataFrame()
        except Exception as e:
            print(f"Error extracting first TDs: {e}")
            return pd.DataFrame()
    
    def get_all_touchdowns(self) -> pd.DataFrame:
        """Get all touchdowns (not just first)."""
        try:
            from utils.nfl_data import get_touchdowns
            pbp = self.pbp_data
            return get_touchdowns(pbp) if not pbp.empty else pd.DataFrame()
        except Exception as e:
            print(f"Error loading all touchdowns: {e}")
            return pd.DataFrame()
    
    def get_game_first_tds(self, game_id: str) -> pd.DataFrame:
        """
        Fast lookup for first TD(s) in a specific game.
        
        Args:
            game_id: Game ID
            
        Returns:
            First TD records for that game
        """
        return self.td_cache.get_first_td_for_game(game_id)
    
    def get_team_first_tds(self, team: str) -> pd.DataFrame:
        """
        Get all first TDs scored by a team.
        
        Args:
            team: Team abbreviation
            
        Returns:
            First TDs by team
        """
        return self.td_cache.get_first_tds_for_team(team)
    
    def reload(self):
        """Force reload all data (e.g., after new games are added)."""
        self._pbp_data = None
        self._schedule = None
        self._rosters = None
        self._first_tds = None
        self._td_cache = None
        self._is_initialized = False
    
    def get_summary(self) -> Dict:
        """Get data loader status and summary."""
        return {
            'season': self.season,
            'pbp_rows': len(self.pbp_data),
            'schedule_rows': len(self.schedule),
            'roster_rows': len(self.rosters),
            'first_tds': len(self.first_tds),
            'unique_games': self.pbp_data['game_id'].nunique() if not self.pbp_data.empty else 0,
        }
