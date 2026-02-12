"""Grading domain exceptions"""


class GradingError(Exception):
    """Base grading exception"""
    pass


class NoPlayByPlayDataError(GradingError):
    """No PBP data available for grading"""
    pass


class NameMatchError(GradingError):
    """Player name matching failed"""
    pass
