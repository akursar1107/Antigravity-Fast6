"""
Odds and probability utilities for American odds, EV calculations, and Kelly sizing.

All functions include type hints and input validation where appropriate.
"""

from typing import List


def american_to_probability(odds: int | float) -> float:
    """
    Convert American odds to implied probability (decimal between 0 and 1).

    Args:
        odds: American odds (e.g., +250, -150). Zero is invalid.

    Returns:
        Implied probability as a float in [0, 1].

    Raises:
        ValueError: If odds is 0.
    """
    if odds == 0:
        raise ValueError("American odds cannot be 0")
    if odds > 0:
        return 100.0 / (odds + 100.0)
    return abs(odds) / (abs(odds) + 100.0)


def probability_to_american(probability: float) -> int:
    """
    Convert a probability (0-1) to American odds (integer).

    Args:
        probability: Probability between 0 and 1 (exclusive).

    Returns:
        American odds as an integer. Positive for underdogs, negative for favorites.

    Raises:
        ValueError: If probability is not in (0, 1).
    """
    if not (0.0 < probability < 1.0):
        raise ValueError("Probability must be between 0 and 1 (exclusive)")
    if probability < 0.5:
        # Positive odds
        return int(round(100.0 * (1.0 - probability) / probability))
    # Negative odds
    return int(round(-probability * 100.0 / (1.0 - probability)))


def calculate_vig(probabilities: List[float]) -> float:
    """
    Calculate bookmaker margin (vig/overround) from a set of implied probabilities.

    Args:
        probabilities: List of implied probabilities (each between 0 and 1).

    Returns:
        Overround value: sum(probabilities) - 1.0
    """
    return sum(probabilities) - 1.0


def remove_vig(probabilities: List[float]) -> List[float]:
    """
    Normalize probabilities by removing vig so they sum to 1.0.

    Args:
        probabilities: List of implied probabilities (non-negative).

    Returns:
        List of fair probabilities that sum to 1.0.
    """
    total = sum(probabilities)
    if total <= 0:
        return [0.0 for _ in probabilities]
    return [p / total for p in probabilities]


def calculate_expected_value(odds: int | float, true_win_probability: float) -> float:
    """
    Calculate expected value of a $1 bet given American odds and true probability.

    EV formula (per $1 stake): EV = p * payout - (1 - p)
    where payout is the profit per $1 if the bet wins.

    Args:
        odds: American odds (e.g., +250, -150). Zero is invalid.
        true_win_probability: Estimated probability of winning (0.0 to 1.0).

    Returns:
        Expected value in dollars per $1 wagered.

    Raises:
        ValueError: If inputs are out of range.
    """
    if odds == 0:
        raise ValueError("American odds cannot be 0")
    if not (0.0 <= true_win_probability <= 1.0):
        raise ValueError("true_win_probability must be between 0 and 1")

    if odds > 0:
        payout = odds / 100.0
    else:
        payout = 100.0 / abs(odds)

    p = true_win_probability
    return (p * payout) - (1.0 - p)


def is_positive_ev(odds: int | float, true_win_probability: float) -> bool:
    """Return True if the expected value is positive."""
    return calculate_expected_value(odds, true_win_probability) > 0.0


def calculate_roi(total_return: float, total_stake: float) -> float:
    """
    Calculate ROI percentage given total return and total stake.

    Args:
        total_return: Total amount returned (including stake).
        total_stake: Total amount staked.

    Returns:
        ROI as a decimal (e.g., 0.12 for 12%).

    Raises:
        ValueError: If total_stake is <= 0.
    """
    if total_stake <= 0:
        raise ValueError("total_stake must be > 0")
    return (total_return - total_stake) / total_stake


def kelly_criterion(
    odds: int | float,
    win_probability: float,
    bankroll: float,
    fraction: float = 0.25,
) -> float:
    """
    Calculate the suggested stake using (fractional) Kelly Criterion.

    Kelly formula: k = (b*p - q) / b, where
        b = net payout per $1 stake (i.e., profit on win)
        p = win_probability
        q = 1 - p

    Args:
        odds: American odds (e.g., +250, -150).
        win_probability: Estimated win probability in [0, 1].
        bankroll: Total bankroll amount.
        fraction: Fraction of Kelly to use (e.g., 0.25). Applied to k.

    Returns:
        Suggested stake amount (non-negative).
    """
    if odds == 0:
        raise ValueError("American odds cannot be 0")
    if not (0.0 <= win_probability <= 1.0):
        raise ValueError("win_probability must be between 0 and 1")
    if bankroll < 0:
        raise ValueError("bankroll must be >= 0")
    if fraction < 0:
        raise ValueError("fraction must be >= 0")

    # Net payout per $1 stake (profit if win)
    b = (odds / 100.0) if odds > 0 else (100.0 / abs(odds))
    p = win_probability
    q = 1.0 - p
    k = (b * p - q) / b
    k = max(0.0, k)  # do not suggest negative stake
    k *= fraction
    return bankroll * k


def fractional_kelly(kelly_bet: float, fraction: float = 0.5) -> float:
    """
    Apply a fraction to a Kelly-calculated stake.

    Args:
        kelly_bet: Stake calculated by Kelly Criterion.
        fraction: Fraction to apply (e.g., 0.5 for half Kelly).

    Returns:
        Adjusted stake amount (non-negative).
    """
    if kelly_bet < 0:
        raise ValueError("kelly_bet must be >= 0")
    if fraction < 0:
        raise ValueError("fraction must be >= 0")
    return max(0.0, kelly_bet * fraction)
