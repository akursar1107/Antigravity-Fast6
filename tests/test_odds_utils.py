import unittest
import sys
import os

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

from utils.odds_utils import (
    american_to_probability,
    probability_to_american,
    calculate_vig,
    remove_vig,
    calculate_expected_value,
    is_positive_ev,
    calculate_roi,
    kelly_criterion,
    fractional_kelly,
)


class TestOddsUtils(unittest.TestCase):
    def test_american_to_probability_positive(self):
        self.assertAlmostEqual(american_to_probability(250), 0.285714, places=6)

    def test_american_to_probability_negative(self):
        self.assertAlmostEqual(american_to_probability(-150), 0.6, places=6)

    def test_probability_to_american_positive(self):
        # 28.57% should be roughly +250
        self.assertEqual(probability_to_american(0.285714), 250)

    def test_probability_to_american_negative(self):
        # 60% should be roughly -150
        self.assertEqual(probability_to_american(0.6), -150)

    def test_vig_and_remove(self):
        probs = [0.52, 0.52]
        vig = calculate_vig(probs)
        self.assertAlmostEqual(vig, 0.04, places=6)
        fair = remove_vig(probs)
        self.assertAlmostEqual(sum(fair), 1.0, places=6)

    def test_expected_value_example(self):
        # For +250 odds and 35% win probability:
        # payout = 2.5 per $1 stake, EV = 0.35*2.5 - 0.65 = 0.225
        ev = calculate_expected_value(250, 0.35)
        self.assertAlmostEqual(ev, 0.225, places=6)

    def test_is_positive_ev(self):
        self.assertTrue(is_positive_ev(250, 0.35))
        self.assertFalse(is_positive_ev(250, 0.25))

    def test_calculate_roi(self):
        # Stake 100, return 115 → ROI = 15%
        self.assertAlmostEqual(calculate_roi(115.0, 100.0), 0.15, places=6)

    def test_kelly_criterion_non_negative(self):
        stake = kelly_criterion(250, 0.35, bankroll=1000.0, fraction=0.25)
        self.assertGreaterEqual(stake, 0.0)
        self.assertAlmostEqual(fractional_kelly(stake, 0.5), stake * 0.5, places=6)


if __name__ == '__main__':
    unittest.main()
