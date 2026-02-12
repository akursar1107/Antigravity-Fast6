import unittest
import pandas as pd
import sys
import os



from backend.analytics.nfl_data import get_touchdowns, get_first_tds
from backend.utils.name_matching import names_match

class TestNFLData(unittest.TestCase):
    def setUp(self):
        # Create dummy data
        data = {
            'game_id': ['g1', 'g1', 'g1', 'g2', 'g2'],
            'play_id': [1, 2, 3, 10, 20],
            'touchdown': [0, 1, 1, 0, 1],
            'receiver_player_name': [None, 'Player A', 'Player B', None, 'Player C'],
            'rusher_player_name': [None, None, None, None, None],
            'passer_player_name': [None, None, None, None, None],
            'qtr': [1, 1, 2, 1, 2],
            'time': ['15:00', '10:00', '05:00', '14:00', '01:00']
        }
        self.df = pd.DataFrame(data)

    def test_get_touchdowns(self):
        tds = get_touchdowns(self.df)
        self.assertEqual(len(tds), 3)
        self.assertTrue(all(tds['touchdown'] == 1))

    def test_get_touchdowns_return_td_uses_returner_not_passer(self):
        """Return TDs (INT, fumble, punt) must use returner, not passer."""
        df = pd.DataFrame({
            'game_id': ['g1'],
            'play_id': [1],
            'touchdown': [1],
            'return_touchdown': [1],
            'receiver_player_name': [None],
            'rusher_player_name': [None],
            'passer_player_name': ['Wrong QB'],
            'returner_player_name': ['Correct Defender'],
        })
        tds = get_touchdowns(df)
        self.assertEqual(len(tds), 1)
        self.assertEqual(tds.iloc[0]['td_player_name'], 'Correct Defender')

    def test_get_first_tds(self):
        first = get_first_tds(self.df)
        self.assertEqual(len(first), 2)
        
        # Check game 1 first TD is play 2 (Player A)
        g1 = first[first['game_id'] == 'g1'].iloc[0]
        self.assertEqual(g1['play_id'], 2)
        self.assertEqual(g1['td_player_name'], 'Player A')

        # Check game 2 first TD is play 20 (Player C)
        g2 = first[first['game_id'] == 'g2'].iloc[0]
        self.assertEqual(g2['play_id'], 20)
        self.assertEqual(g2['td_player_name'], 'Player C')

    def test_names_match(self):
        # Exact match
        self.assertTrue(names_match("Aaron Jones", "Aaron Jones"))
        # First initial match
        self.assertTrue(names_match("Aaron Jones", "A.Jones"))
        self.assertTrue(names_match("J.Ferguson", "Jake Ferguson")) # Order shouldn't matter if we pass them consistently?
        # Actually logic expects (prediction, actual)
        # Prediction could be "Jake Ferguson" (full name) and Actual "J.Ferguson" (abbr)
        self.assertTrue(names_match("Jake Ferguson", "J.Ferguson"))
        
        # Mismatch
        self.assertFalse(names_match("Aaron Jones", "Julio Jones"))
        self.assertFalse(names_match("Aaron Jones", "A.Rodgers"))
        
        # Suffix handling
        self.assertTrue(names_match("Marvin Harrison Jr.", "M.Harrison"))

if __name__ == '__main__':
    unittest.main()
