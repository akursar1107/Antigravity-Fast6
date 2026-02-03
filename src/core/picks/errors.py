"""Picks domain exceptions"""


class PickError(Exception):
    """Base picks exception"""
    pass


class PickValidationError(PickError):
    """Pick validation failed"""
    pass


class GameAlreadyStartedError(PickError):
    """Game has already started, no picks allowed"""
    pass


class DuplicatePickError(PickError):
    """User already has a pick for this game"""
    pass
