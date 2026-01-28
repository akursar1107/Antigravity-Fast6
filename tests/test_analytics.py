import unittest
import pandas as pd
from utils.first_drive_success import get_first_drive_success_rates
from utils.first_drive_analytics import get_first_drive_scoring_rates
from utils.kickoff_analytics import get_team_kickoff_tendencies

class TestAnalyticsFunctions(unittest.TestCase):
    def setUp(self):
        # Minimal dummy play-by-play data for first drive analytics
        self.pbp = pd.DataFrame({
            'game_id': ['g1', 'g1', 'g1', 'g2', 'g2', 'g2'],
            'drive': [1, 1, 2, 1, 1, 2],
            'play_type': ['run', 'pass', 'run', 'run', 'pass', 'pass'],
            'down': [1, 2, 1, 1, 2, 1],
            'yards_gained': [5, 7, 2, 3, 8, 1],
            'posteam': ['A', 'A', 'A', 'B', 'B', 'B'],
            'touchdown': [0, 1, 0, 0, 0, 1],
            'field_goal_result': [None, None, None, None, None, None],
        })

    def test_first_drive_success_rates(self):
        df = get_first_drive_success_rates(self.pbp)
        self.assertIn('rush_success_rate', df.columns)
        self.assertIn('pass_success_rate', df.columns)
        self.assertTrue((df['rush_success_rate'] <= 1).all())
        self.assertTrue((df['pass_success_rate'] <= 1).all())

    def test_first_drive_scoring_rates(self):
        df = get_first_drive_scoring_rates(self.pbp)
        self.assertIn('first_drive_score_rate', df.columns)
        self.assertTrue((df['first_drive_score_rate'] <= 1).all())

    def test_kickoff_tendencies(self):
        # This function expects DB data, so just check it runs and returns a DataFrame
        df = get_team_kickoff_tendencies()
        self.assertIsInstance(df, pd.DataFrame)

if __name__ == '__main__':
    unittest.main()
