"""
User Performance Analytics Service

Calculates advanced metrics: Brier scores, ROI by odds range, streaks,
accuracy by position and game type.
"""

from typing import Dict, List, Optional, Tuple
import pandas as pd
from utils import get_user_picks_with_results, get_all_users


class PickerPerformanceService:
    """Advanced performance analytics for users."""
    
    def __init__(self, results_repo=None, picks_repo=None):
        """
        Initialize service with optional repository dependencies.
        
        Args:
            results_repo: Results repository (for fetching result data)
            picks_repo: Picks repository (for fetching pick data)
        """
        self.results_repo = results_repo
        self.picks_repo = picks_repo
    
    def calculate_brier_score(self, user_id: int, season: int) -> float:
        """
        Calculate Brier score for a user (0 = perfect, 1 = worst).
        
        Measures calibration of probability estimates.
        Formula: BS = (1/N) * Σ(predicted_prob - actual_outcome)²
        
        Where:
        - predicted_prob = odds-implied probability (0.0 to 1.0)
        - actual_outcome = 1 if correct, 0 if incorrect
        
        Args:
            user_id: User ID
            season: NFL season
            
        Returns:
            Brier score as float (0 = perfect, 1 = worst)
        """
        picks = get_user_picks_with_results(user_id, season)
        
        if not picks:
            return 0.0
        
        from utils.odds_utils import american_to_probability
        
        squared_errors = []
        
        for pick in picks:
            # Get odds (default to +250 if not available)
            odds = pick.get('odds', 250)
            implied_prob = american_to_probability(odds)
            
            # Actual outcome: 1 if correct, 0 if incorrect
            actual = 1.0 if pick.get('is_correct') else 0.0
            
            # Squared error
            error = (implied_prob - actual) ** 2
            squared_errors.append(error)
        
        brier = sum(squared_errors) / len(squared_errors) if squared_errors else 0.0
        return round(brier, 4)
    
    def calculate_roi_by_odds_range(self, user_id: int, season: int) -> pd.DataFrame:
        """
        Calculate ROI for different odds buckets.
        
        Args:
            user_id: User ID
            season: NFL season
            
        Returns:
            DataFrame with columns: odds_range, picks, wins, roi_percent
        """
        picks = get_user_picks_with_results(user_id, season)
        
        if not picks:
            return pd.DataFrame(columns=['odds_range', 'picks', 'wins', 'roi_percent'])
        
        # Odds buckets from config (or defaults)
        buckets = [
            (100, 300, 'Favorites'),
            (300, 500, 'Moderate'),
            (500, 700, 'Longshots'),
            (700, 1000, 'Heavy Longshots'),
            (1000, 5000, 'Extreme Longshots')
        ]
        
        results = []
        
        for min_odds, max_odds, label in buckets:
            picks_in_range = [
                p for p in picks
                if p.get('odds') is not None and min_odds <= abs(p.get('odds')) < max_odds
            ]
            
            # If no picks in range with non-None odds, try with default
            if not picks_in_range:
                picks_in_range = [
                    p for p in picks
                    if p.get('odds') is None and min_odds <= 250 < max_odds
                ]
            
            if not picks_in_range:
                continue
            
            wins = sum(1 for p in picks_in_range if p.get('is_correct'))
            
            # Calculate ROI: (total_return - total_stake) / total_stake
            # Simplified: assume $1 per pick, calculate return from odds
            from utils.odds_utils import american_to_probability
            
            total_return = 0.0
            for p in picks_in_range:
                odds = p.get('odds') or 250  # Default to 250 if None
                if p.get('is_correct'):
                    if odds > 0:
                        total_return += 1.0 + (odds / 100.0)
                    else:
                        total_return += 1.0 + (100.0 / abs(odds))
                else:
                    total_return += 0.0  # Lost the stake
            
            stake = len(picks_in_range)
            roi = (total_return - stake) / stake * 100 if stake > 0 else 0.0
            
            results.append({
                'odds_range': label,
                'picks': len(picks_in_range),
                'wins': wins,
                'roi_percent': round(roi, 2)
            })
        
        return pd.DataFrame(results)
    
    def calculate_streak_stats(self, user_id: int, season: int) -> Dict:
        """
        Calculate hot/cold streak statistics.
        
        Args:
            user_id: User ID
            season: NFL season
            
        Returns:
            {
                'current_streak': 3,  # Positive = win streak, negative = loss
                'longest_win_streak': 5,
                'longest_loss_streak': 4,
                'is_hot': True  # 3+ wins in last 5 picks
            }
        """
        picks = get_user_picks_with_results(user_id, season)
        
        if not picks:
            return {
                'current_streak': 0,
                'longest_win_streak': 0,
                'longest_loss_streak': 0,
                'is_hot': False
            }
        
        # Calculate streaks
        streak = 0
        longest_win = 0
        longest_loss = 0
        current_streak = 0
        
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
    
    def calculate_accuracy_by_position(self, user_id: int, season: int) -> pd.DataFrame:
        """
        Calculate pick accuracy broken down by player position.
        
        Args:
            user_id: User ID
            season: NFL season
            
        Returns:
            DataFrame with columns: position, picks, correct, accuracy
        """
        picks = get_user_picks_with_results(user_id, season)
        
        if not picks:
            return pd.DataFrame(columns=['position', 'picks', 'correct', 'accuracy'])
        
        # Map picks to positions
        from utils.nfl_data import load_rosters
        
        roster_df = load_rosters(season)
        
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
    
    def calculate_accuracy_by_game_type(self, user_id: int, season: int) -> pd.DataFrame:
        """
        Calculate accuracy broken down by game type (Main Slate, Standalone, etc).
        
        Args:
            user_id: User ID
            season: NFL season
            
        Returns:
            DataFrame with columns: game_type, picks, correct, accuracy
        """
        picks = get_user_picks_with_results(user_id, season)
        
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
    
    def get_user_performance_summary(self, user_id: int, season: int) -> Dict:
        """
        Get comprehensive performance summary for a user.
        
        Args:
            user_id: User ID
            season: NFL season
            
        Returns:
            Dict with all performance metrics
        """
        picks = get_user_picks_with_results(user_id, season)
        
        if not picks:
            return {
                'total_picks': 0,
                'wins': 0,
                'losses': 0,
                'win_rate': 0.0,
                'brier_score': 0.0,
                'streaks': {},
                'roi_summary': None,
                'accuracy_by_position': None,
                'accuracy_by_game_type': None
            }
        
        total_picks = len(picks)
        wins = sum(1 for p in picks if p.get('is_correct'))
        losses = total_picks - wins
        win_rate = wins / total_picks if total_picks > 0 else 0.0
        
        return {
            'total_picks': total_picks,
            'wins': wins,
            'losses': losses,
            'win_rate': round(win_rate * 100, 2),
            'brier_score': self.calculate_brier_score(user_id, season),
            'streaks': self.calculate_streak_stats(user_id, season),
            'roi_summary': self.calculate_roi_by_odds_range(user_id, season),
            'accuracy_by_position': self.calculate_accuracy_by_position(user_id, season),
            'accuracy_by_game_type': self.calculate_accuracy_by_game_type(user_id, season)
        }
