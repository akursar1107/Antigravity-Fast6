"""
User Performance Analytics Service

Calculates advanced metrics: Brier scores, ROI by odds range, streaks,
accuracy by position and game type.
"""

from typing import Dict, List, Optional, Callable, Any
import pandas as pd
import backend.config as config


# Default repository function (can be overridden for testing)
def _default_picks_repo(user_id: int, season: int) -> List[Dict]:
    """Default implementation using db_stats."""
    from backend.utils import get_user_picks_with_results
    return get_user_picks_with_results(user_id, season)


def _default_rosters_repo(season: int) -> Optional[pd.DataFrame]:
    """Default implementation for loading rosters."""
    from backend.analytics.nfl_data import load_rosters
    return load_rosters(season)


class PickerPerformanceService:
    """
    Advanced performance analytics for users.
    
    Uses dependency injection for data access, enabling:
    - Easy testing with mock data
    - Flexible data sources
    - Optimized data loading (load once, use many times)
    """
    
    def __init__(
        self,
        picks_repo: Optional[Callable[[int, int], List[Dict]]] = None,
        rosters_repo: Optional[Callable[[int], Optional[pd.DataFrame]]] = None
    ):
        """
        Initialize service with optional repository dependencies.
        
        Args:
            picks_repo: Function(user_id, season) -> List[Dict] for fetching picks with results
            rosters_repo: Function(season) -> DataFrame for fetching roster data
        """
        self.picks_repo = picks_repo or _default_picks_repo
        self.rosters_repo = rosters_repo or _default_rosters_repo
        
        # Cache for expensive operations
        self._roster_cache: Dict[int, Optional[pd.DataFrame]] = {}
    
    def _get_rosters(self, season: int) -> Optional[pd.DataFrame]:
        """Get rosters with caching."""
        if season not in self._roster_cache:
            self._roster_cache[season] = self.rosters_repo(season)
        return self._roster_cache[season]
    
    def _calculate_brier_score_from_picks(self, picks: List[Dict]) -> float:
        """
        Calculate Brier score from pre-loaded picks (0 = perfect, 1 = worst).
        
        Measures calibration of probability estimates.
        Formula: BS = (1/N) * Σ(predicted_prob - actual_outcome)²
        """
        if not picks:
            return 0.0
        
        from backend.analytics.odds_utils import american_to_probability
        
        squared_errors = []
        
        for pick in picks:
            # Get odds (use config default if not available)
            odds = pick.get('odds')
            if odds is None:
                odds = config.DEFAULT_ODDS
            implied_prob = american_to_probability(odds)
            
            # Actual outcome: 1 if correct, 0 if incorrect
            actual = 1.0 if pick.get('is_correct') else 0.0
            
            # Squared error
            error = (implied_prob - actual) ** 2
            squared_errors.append(error)
        
        brier = sum(squared_errors) / len(squared_errors) if squared_errors else 0.0
        return round(brier, 4)
    
    def _calculate_roi_by_odds_range_from_picks(self, picks: List[Dict]) -> pd.DataFrame:
        """
        Calculate ROI for different odds buckets from pre-loaded picks.
        """
        if not picks:
            return pd.DataFrame(columns=['odds_range', 'picks', 'wins', 'roi_percent'])
        
        results = []
        
        for min_odds, max_odds, label in config.ODDS_BUCKETS:
            picks_in_range = []
            for p in picks:
                odds = p.get('odds')
                if odds is None:
                    odds = config.DEFAULT_ODDS
                if min_odds <= abs(odds) < max_odds:
                    picks_in_range.append(p)
            
            if not picks_in_range:
                continue
            
            wins = sum(1 for p in picks_in_range if p.get('is_correct'))
            
            # Calculate ROI: (total_return - total_stake) / total_stake
            total_return = 0.0
            for p in picks_in_range:
                odds = p.get('odds') or config.DEFAULT_ODDS
                if p.get('is_correct'):
                    if odds > 0:
                        total_return += 1.0 + (odds / 100.0)
                    else:
                        total_return += 1.0 + (100.0 / abs(odds))
                # Lost picks return 0
            
            stake = len(picks_in_range)
            roi = (total_return - stake) / stake * 100 if stake > 0 else 0.0
            
            results.append({
                'odds_range': label,
                'picks': len(picks_in_range),
                'wins': wins,
                'roi_percent': round(roi, 2)
            })
        
        return pd.DataFrame(results)
    
    def _calculate_streak_stats_from_picks(self, picks: List[Dict]) -> Dict:
        """
        Calculate hot/cold streak statistics from pre-loaded picks.
        """
        if not picks:
            return {
                'current_streak': 0,
                'longest_win_streak': 0,
                'longest_loss_streak': 0,
                'is_hot': False
            }
        
        streak = 0
        longest_win = 0
        longest_loss = 0
        
        for pick in picks:
            is_correct = pick.get('is_correct', False)
            
            if is_correct:
                if streak <= 0:
                    streak = 1
                else:
                    streak += 1
            else:
                if streak >= 0:
                    streak = -1
                else:
                    streak -= 1
            
            if streak > 0:
                longest_win = max(longest_win, streak)
            else:
                longest_loss = max(longest_loss, abs(streak))
        
        current_streak = streak
        
        # Is hot: 3+ wins in last 5 picks
        recent = picks[-5:] if len(picks) >= 5 else picks
        recent_wins = sum(1 for p in recent if p.get('is_correct'))
        is_hot = recent_wins >= 3
        
        return {
            'current_streak': current_streak,
            'longest_win_streak': longest_win,
            'longest_loss_streak': longest_loss,
            'is_hot': is_hot
        }
    
    def _calculate_accuracy_by_position_from_picks(
        self, picks: List[Dict], season: int
    ) -> pd.DataFrame:
        """
        Calculate pick accuracy broken down by player position from pre-loaded picks.
        """
        if not picks:
            return pd.DataFrame(columns=['position', 'picks', 'correct', 'accuracy'])
        
        # Get rosters (cached)
        roster_df = self._get_rosters(season)
        
        # Build position map
        position_map = {}
        if roster_df is not None and not roster_df.empty:
            position_map = dict(zip(roster_df['full_name'], roster_df['position']))
        
        position_stats = {}
        
        for pick in picks:
            player_name = pick.get('player_name', '')
            position = position_map.get(player_name, 'Unknown')
            
            if position not in position_stats:
                position_stats[position] = {'picks': 0, 'correct': 0}
            
            position_stats[position]['picks'] += 1
            if pick.get('is_correct'):
                position_stats[position]['correct'] += 1
        
        # Convert to DataFrame
        results = []
        for position, stats in position_stats.items():
            accuracy = stats['correct'] / stats['picks'] if stats['picks'] > 0 else 0.0
            results.append({
                'position': position,
                'picks': stats['picks'],
                'correct': stats['correct'],
                'accuracy': round(accuracy * 100, 2)
            })
        
        return pd.DataFrame(results).sort_values('accuracy', ascending=False)
    
    def _calculate_accuracy_by_game_type_from_picks(self, picks: List[Dict]) -> pd.DataFrame:
        """
        Calculate accuracy broken down by game type from pre-loaded picks.
        """
        if not picks:
            return pd.DataFrame(columns=['game_type', 'picks', 'correct', 'accuracy'])
        
        game_type_stats = {}
        
        for pick in picks:
            game_type = pick.get('game_type', 'Unknown')
            
            if game_type not in game_type_stats:
                game_type_stats[game_type] = {'picks': 0, 'correct': 0}
            
            game_type_stats[game_type]['picks'] += 1
            if pick.get('is_correct'):
                game_type_stats[game_type]['correct'] += 1
        
        # Convert to DataFrame
        results = []
        for game_type, stats in game_type_stats.items():
            accuracy = stats['correct'] / stats['picks'] if stats['picks'] > 0 else 0.0
            results.append({
                'game_type': game_type,
                'picks': stats['picks'],
                'correct': stats['correct'],
                'accuracy': round(accuracy * 100, 2)
            })
        
        return pd.DataFrame(results).sort_values('picks', ascending=False)
    
    # ============= PUBLIC API =============
    # These methods are the public interface. They either load data once,
    # or delegate to the optimized _from_picks methods.
    
    def calculate_brier_score(self, user_id: int, season: int) -> float:
        """
        Calculate Brier score for a user (0 = perfect, 1 = worst).
        
        For single metric access. Use get_user_performance_summary() 
        for multiple metrics to avoid redundant data loading.
        """
        picks = self.picks_repo(user_id, season)
        return self._calculate_brier_score_from_picks(picks)
    
    def calculate_roi_by_odds_range(self, user_id: int, season: int) -> pd.DataFrame:
        """
        Calculate ROI for different odds buckets.
        
        For single metric access. Use get_user_performance_summary()
        for multiple metrics to avoid redundant data loading.
        """
        picks = self.picks_repo(user_id, season)
        return self._calculate_roi_by_odds_range_from_picks(picks)
    
    def calculate_streak_stats(self, user_id: int, season: int) -> Dict:
        """
        Calculate hot/cold streak statistics.
        
        For single metric access. Use get_user_performance_summary()
        for multiple metrics to avoid redundant data loading.
        """
        picks = self.picks_repo(user_id, season)
        return self._calculate_streak_stats_from_picks(picks)
    
    def calculate_accuracy_by_position(self, user_id: int, season: int) -> pd.DataFrame:
        """
        Calculate pick accuracy broken down by player position.
        
        For single metric access. Use get_user_performance_summary()
        for multiple metrics to avoid redundant data loading.
        """
        picks = self.picks_repo(user_id, season)
        return self._calculate_accuracy_by_position_from_picks(picks, season)
    
    def calculate_accuracy_by_game_type(self, user_id: int, season: int) -> pd.DataFrame:
        """
        Calculate accuracy broken down by game type.
        
        For single metric access. Use get_user_performance_summary()
        for multiple metrics to avoid redundant data loading.
        """
        picks = self.picks_repo(user_id, season)
        return self._calculate_accuracy_by_game_type_from_picks(picks)
    
    def get_user_performance_summary(self, user_id: int, season: int) -> Dict:
        """
        Get comprehensive performance summary for a user.
        
        OPTIMIZED: Loads pick data ONCE and reuses for all calculations.
        This is 5x faster than calling individual methods.
        
        Args:
            user_id: User ID
            season: NFL season
            
        Returns:
            Dict with all performance metrics
        """
        # Load data ONCE
        picks = self.picks_repo(user_id, season)
        
        if not picks:
            return {
                'total_picks': 0,
                'wins': 0,
                'losses': 0,
                'win_rate': 0.0,
                'brier_score': 0.0,
                'streaks': {
                    'current_streak': 0,
                    'longest_win_streak': 0,
                    'longest_loss_streak': 0,
                    'is_hot': False
                },
                'roi_summary': pd.DataFrame(columns=['odds_range', 'picks', 'wins', 'roi_percent']),
                'accuracy_by_position': pd.DataFrame(columns=['position', 'picks', 'correct', 'accuracy']),
                'accuracy_by_game_type': pd.DataFrame(columns=['game_type', 'picks', 'correct', 'accuracy'])
            }
        
        total_picks = len(picks)
        wins = sum(1 for p in picks if p.get('is_correct'))
        losses = total_picks - wins
        win_rate = wins / total_picks if total_picks > 0 else 0.0
        
        # Calculate all metrics using pre-loaded picks (no redundant data loading)
        return {
            'total_picks': total_picks,
            'wins': wins,
            'losses': losses,
            'win_rate': round(win_rate * 100, 2),
            'brier_score': self._calculate_brier_score_from_picks(picks),
            'streaks': self._calculate_streak_stats_from_picks(picks),
            'roi_summary': self._calculate_roi_by_odds_range_from_picks(picks),
            'accuracy_by_position': self._calculate_accuracy_by_position_from_picks(picks, season),
            'accuracy_by_game_type': self._calculate_accuracy_by_game_type_from_picks(picks)
        }
