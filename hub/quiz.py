"""Which character are you? A personality quiz using trait distance (no AI)."""

from datetime import datetime

import questionary

from hub import display
from hub.config import TRAITS, TOP_MATCHES, QUIZ_STRETCH


def max_points(questions: list[dict]) -> dict[str, int]:
    """Highest absolute points each trait can reach across all questions (used for scaling)."""
    limits = {trait: 0 for trait in TRAITS}
    for question in questions:
        for trait in TRAITS:
            limits[trait] += max(abs(effects.get(trait, 0)) for effects in question["options"].values())
    return limits


def add_points(totals: dict[str, int], effects: dict[str, int]) -> None:
    """Add the trait points of one answer to the running totals."""
    for trait, points in effects.items():
        totals[trait] += points


def run_quiz(questions: list[dict]) -> dict[str, int] | None:
    """Ask every question and add up the trait points of the chosen answers.

    Returns None if the user cancels with Ctrl+C.
    """
    totals = {trait: 0 for trait in TRAITS}
    for number, question in enumerate(questions, start=1):
        answer = questionary.select(
            f"({number}/{len(questions)}) {question['text']}",
            choices=list(question["options"]),
        ).ask()
        if answer is None:
            return None
        add_points(totals, question["options"][answer])
    return totals


def to_scale(totals: dict[str, int], limits: dict[str, int], stretch: float = QUIZ_STRETCH) -> dict[str, float]:
    """Map trait points to a 0-10 scale where 5 is neutral.

    Points are divided by the trait's limit (giving -1 to +1), multiplied by `stretch`
    to spread results out, then moved to 0-10 and clamped.
    """
    scaled = {}
    for trait in TRAITS:
        limit = limits[trait] or 1
        value = 5 + (totals[trait] / limit) * 5 * stretch
        scaled[trait] = round(min(10, max(0, value)), 1)
    return scaled


def distance(a: dict[str, float], b: dict[str, float]) -> float:
    """Euclidean distance between two trait dictionaries."""
    return sum((a[trait] - b[trait]) ** 2 for trait in TRAITS) ** 0.5


def best_matches(user: dict[str, float], characters: list[dict], top: int = TOP_MATCHES) -> list[tuple[str, int]]:
    """Return the `top` closest characters as (name, match_percent), best first."""
    worst = distance({trait: 0 for trait in TRAITS}, {trait: 10 for trait in TRAITS})
    results = []
    for character in characters:
        match = round((1 - distance(user, character["traits"]) / worst) * 100)
        results.append((character["name"], match))
    results.sort(key=lambda result: result[1], reverse=True)
    return results[:top]


def take_quiz(questions: list[dict], characters: list[dict], series: str, player: str) -> dict | None:
    """Run the full quiz for one series and return the result record (or None if cancelled)."""
    if not questions:
        display.error("No quiz questions found.")
        return None
    if not characters:
        display.warning(f"No characters found for {series}.")
        return None

    totals = run_quiz(questions)
    if totals is None:
        return None

    traits = to_scale(totals, max_points(questions))
    return {
        "player": player,
        "series": series,
        "traits": traits,
        "matches": best_matches(traits, characters),
        "taken_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
    }
