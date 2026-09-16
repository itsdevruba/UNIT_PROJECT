"""Which character are you? A personality quiz using trait distance (no AI)."""

import questionary

from config import TRAITS, TOP_MATCHES


def max_points(questions: list[dict]) -> dict[str, int]:
    """Highest absolute points each trait can reach across all questions (used for scaling)."""
    pass


def run_quiz(questions: list[dict]) -> dict[str, int]:
    """Ask every question and add up the trait points of the chosen answers."""
    # TODO: questionary.select for each question; if the answer is None (Ctrl+C) stop the quiz
    pass


def to_scale(totals: dict[str, int], limits: dict[str, int]) -> dict[str, float]:
    """Map trait points from [-limit, +limit] to [0, 10]."""
    pass


def distance(a: dict[str, float], b: dict[str, float]) -> float:
    """Euclidean distance between two trait dictionaries."""
    pass


def best_matches(user: dict[str, float], characters: list[dict], top: int = TOP_MATCHES) -> list[tuple[str, int]]:
    """Return the `top` closest characters as (name, match_percent), best first."""
    pass
