"""Rating characters: collecting scores, weighted overall, tiers, comparison."""

from datetime import datetime

import questionary

from config import CRITERIA, TIERS, MIN_SCORE, MAX_SCORE


def validate_score(raw: str) -> int:
    """Convert user input to an int between MIN_SCORE and MAX_SCORE.

    Raise ValueError with a clear message if it is not valid.
    """
    pass


def ask_scores() -> dict[str, int]:
    """Ask the user for a score for each criterion. Re-ask on invalid input."""
    # TODO: loop over CRITERIA, use questionary.text, call validate_score inside try/except
    pass


def calculate_overall(scores: dict[str, int]) -> float:
    """Weighted average of the scores, rounded to 1 decimal."""
    pass


def get_tier(overall: float) -> str:
    """Return the tier letter for an overall score using TIERS."""
    pass


def rate_character(character: dict, ratings: dict) -> dict:
    """Ask for scores, calculate overall and tier, store them in `ratings` under the character id."""
    # TODO: include "scores", "overall", "tier", "rated_at" (datetime.now)
    pass


def build_tier_list(ratings: dict, characters: list[dict]) -> dict[str, list[tuple[str, float]]]:
    """Group rated characters by tier: {"S": [(name, overall), ...], "A": [...], ...}."""
    pass


def compare(first: dict, second: dict) -> dict[str, str]:
    """For each criterion, return the name of the character with the higher score (or "Tie")."""
    pass
