"""Rating characters: collecting scores, weighted overall, tiers, comparison."""

from datetime import datetime

import questionary

from hub import display
from hub.config import CRITERIA, TIERS, MIN_SCORE, MAX_SCORE

CRITERIA_HINTS = {
    "writing": "How well written is the character and their story?",
    "growth": "How much do they change through the game?",
    "charisma": "Presence, dialogue, screen time you enjoy",
    "combat": "How skilled and dangerous are they?",
    "memorability": "Do they stay with you after the game?",
}


def validate_score(raw: str) -> int:
    """Convert user input to an int between MIN_SCORE and MAX_SCORE.

    Raise ValueError with a clear message if it is not valid.
    """
    raw = raw.strip()
    if not raw:
        raise ValueError("Please enter a score.")
    try:
        score = int(raw)
    except ValueError:
        raise ValueError(f"'{raw}' is not a whole number. Enter a number from {MIN_SCORE} to {MAX_SCORE}.")
    if not MIN_SCORE <= score <= MAX_SCORE:
        raise ValueError(f"{score} is out of range. Enter a number from {MIN_SCORE} to {MAX_SCORE}.")
    return score


def ask_scores(previous: dict[str, int] | None = None) -> dict[str, int] | None:
    """Ask the user for a score for each criterion. Re-ask on invalid input.

    If `previous` scores are given, they are shown as defaults (press Enter to keep).
    Returns None if the user cancels with Ctrl+C.
    """
    scores = {}
    for criterion, weight in CRITERIA.items():
        default = str(previous[criterion]) if previous else ""
        while True:
            raw = questionary.text(
                f"{criterion.capitalize()} ({int(weight * 100)}%) - {CRITERIA_HINTS[criterion]}:",
                default=default,
            ).ask()
            if raw is None:
                return None
            try:
                scores[criterion] = validate_score(raw)
                break
            except ValueError as error:
                display.error(str(error))
    return scores


def calculate_overall(scores: dict[str, int]) -> float:
    """Weighted average of the scores, rounded to 1 decimal (halves round up)."""
    total = 0.0
    for criterion, weight in CRITERIA.items():
        total += scores[criterion] * weight
    return int(total * 10 + 0.5 + 1e-9) / 10


def get_tier(overall: float) -> str:
    """Return the tier letter for an overall score using TIERS."""
    for minimum, tier in TIERS:
        if overall >= minimum:
            return tier
    return TIERS[-1][1]


def make_rating(scores: dict[str, int]) -> dict:
    """Build the rating record that gets saved in user_ratings.json."""
    overall = calculate_overall(scores)
    return {
        "scores": scores,
        "overall": overall,
        "tier": get_tier(overall),
        "rated_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
    }


def rate_character(character: dict, ratings: dict) -> dict | None:
    """Ask for scores, calculate overall and tier, store them in `ratings` under the character id.

    Returns the new rating, or None if the user cancelled.
    """
    previous = ratings.get(character["id"])
    if previous:
        display.console.print(f"[dim]You already rated {character['name']} "
                              f"({previous['overall']}). Press Enter to keep a score.[/dim]")

    scores = ask_scores(previous["scores"] if previous else None)
    if scores is None:
        return None

    rating = make_rating(scores)
    ratings[character["id"]] = rating
    return rating


def rated_characters(characters: list[dict], ratings: dict) -> list[dict]:
    """Return only the characters the user has rated."""
    return [character for character in characters if character["id"] in ratings]


def build_tier_list(ratings: dict, characters: list[dict]) -> dict[str, list[tuple[str, float]]]:
    """Group rated characters by tier: {"S": [(name, overall), ...], "A": [...], ...}.

    Characters inside each tier are sorted from highest to lowest score.
    """
    tier_list = {tier: [] for _, tier in TIERS}
    for character in rated_characters(characters, ratings):
        rating = ratings[character["id"]]
        tier_list[rating["tier"]].append((character["name"], rating["overall"]))

    for tier in tier_list:
        tier_list[tier].sort(key=lambda entry: entry[1], reverse=True)
    return tier_list


def compare(first_name: str, first_rating: dict, second_name: str, second_rating: dict) -> dict[str, str]:
    """For each criterion, return the name of the character with the higher score (or "Tie")."""
    winners = {}
    for criterion in CRITERIA:
        a = first_rating["scores"][criterion]
        b = second_rating["scores"][criterion]
        if a > b:
            winners[criterion] = first_name
        elif b > a:
            winners[criterion] = second_name
        else:
            winners[criterion] = "Tie"
    return winners
