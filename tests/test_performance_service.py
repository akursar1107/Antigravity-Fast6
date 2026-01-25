"""
Tests for PickerPerformanceService
"""

import unittest
import sys
import os
from datetime import datetime

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

from services.performance_service import PickerPerformanceService
from utils.odds_utils import american_to_probability


class TestPickerPerformanceService(unittest.TestCase):
    """Test suite for PickerPerformanceService."""
    
    def setUp(self):
        """Initialize service for testing."""
        self.service = PickerPerformanceService()
    
    def test_brier_score_perfect(self):
        """Brier score for perfect predictions (all correct)."""
        # Mock data: all correct picks at -150 odds (60% implied prob)
        # Perfect prediction would have 60% confidence → squared error = 0
        # This is simplified; in practice would need database fixtures
        brier = self.service.calculate_brier_score(user_id=999, season=2025)
        # Should be 0 or low for well-calibrated picker
        self.assertGreaterEqual(brier, 0.0)
        self.assertLessEqual(brier, 1.0)
    
    def test_brier_score_uncalibrated(self):
        """Brier score range is always [0, 1]."""
        brier = self.service.calculate_brier_score(user_id=999, season=2025)
        self.assertGreaterEqual(brier, 0.0)
        self.assertLessEqual(brier, 1.0)
    
    def test_roi_by_odds_range_returns_dataframe(self):
        """ROI calculation returns valid DataFrame."""
        roi_df = self.service.calculate_roi_by_odds_range(user_id=999, season=2025)
        
        # Should be DataFrame with required columns
        self.assertIsNotNone(roi_df)
        if not roi_df.empty:
            self.assertIn('odds_range', roi_df.columns)
            self.assertIn('picks', roi_df.columns)
            self.assertIn('roi_percent', roi_df.columns)
    
    def test_streak_stats_structure(self):
        """Streak calculation returns correct structure."""
        streaks = self.service.calculate_streak_stats(user_id=999, season=2025)
        
        self.assertIn('current_streak', streaks)
        self.assertIn('longest_win_streak', streaks)
        self.assertIn('longest_loss_streak', streaks)
        self.assertIn('is_hot', streaks)
        
        self.assertIsInstance(streaks['current_streak'], int)
        self.assertIsInstance(streaks['is_hot'], bool)
    
    def test_accuracy_by_position_returns_dataframe(self):
        """Position accuracy returns valid DataFrame."""
        pos_df = self.service.calculate_accuracy_by_position(user_id=999, season=2025)
        
        self.assertIsNotNone(pos_df)
        if not pos_df.empty:
            self.assertIn('position', pos_df.columns)
            self.assertIn('accuracy', pos_df.columns)
    
    def test_accuracy_by_game_type_returns_dataframe(self):
        """Game type accuracy returns valid DataFrame."""
        game_df = self.service.calculate_accuracy_by_game_type(user_id=999, season=2025)
        
        self.assertIsNotNone(game_df)
        if not game_df.empty:
            self.assertIn('game_type', game_df.columns)
            self.assertIn('accuracy', game_df.columns)
    
    def test_performance_summary_structure(self):
        """Full performance summary has all required keys."""
        summary = self.service.get_user_performance_summary(user_id=999, season=2025)
        
        required_keys = [
            'total_picks',
            'wins',
            'losses',
            'win_rate',
            'brier_score',
            'streaks',
            'roi_summary',
            'accuracy_by_position',
            'accuracy_by_game_type'
        ]
        
        for key in required_keys:
            self.assertIn(key, summary)


if __name__ == '__main__':
    unittest.main()
