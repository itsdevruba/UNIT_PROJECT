"""Users: names, per-user ratings, and per-user quiz results."""

import questionary

from hub import display
from hub.config import GUEST_NAME, MAX_NAME_LENGTH


def validate_name(raw: str) -> str:
    """Clean up a name (trim and collapse spaces). Raise ValueError if empty or too long."""
    name = " ".join(raw.split())
    if not name:
        raise ValueError("Please enter a name.")
    if len(name) > MAX_NAME_LENGTH:
        raise ValueError(f"Name is too long. Use {MAX_NAME_LENGTH} characters or fewer.")
    return name


def ask_name(message: str = "Enter your name:") -> str | None:
    """Ask for a name. Re-ask on invalid input, None on Ctrl+C."""
    while True:
        raw = questionary.text(message).ask()
        if raw is None:
            return None
        try:
            return validate_name(raw)
        except ValueError as error:
            display.error(str(error))


def same_name(a: str, b: str) -> bool:
    """Names match without caring about upper/lower case ("ruba" == "Ruba")."""
    return a.lower() == b.lower()


def find_user_key(all_ratings: dict, name: str) -> str | None:
    """Return the stored spelling of this user's name, or None if they have no ratings yet."""
    for key in all_ratings:
        if same_name(key, name):
            return key
    return None


def get_user_ratings(all_ratings: dict, name: str) -> dict:
    """Return this user's ratings dict, creating an empty one for new users."""
    key = find_user_key(all_ratings, name) or name
    return all_ratings.setdefault(key, {})


def migrate_ratings(data: dict) -> dict:
    """Old files stored ratings for one person: {"arthur-morgan": {...}}.

    New files store them per user: {"Ruba": {"arthur-morgan": {...}}}.
    If the old format is detected, move everything under GUEST_NAME.
    """
    if data and all(isinstance(value, dict) and "scores" in value for value in data.values()):
        display.warning(f"Old ratings found. They were moved to the user '{GUEST_NAME}'.")
        return {GUEST_NAME: data}
    return data


def results_for(results: list[dict], name: str) -> list[dict]:
    """Return only this user's quiz results."""
    return [result for result in results if same_name(result["player"], name)]


def list_users(all_ratings: dict, results: list[dict]) -> list[dict]:
    """Everyone with ratings or quiz results, sorted by name.

    Each item looks like {"name": ..., "ratings": 3, "quiz_results": 1}.
    """
    names = list(all_ratings)
    for result in results:
        if not any(same_name(result["player"], name) for name in names):
            names.append(result["player"])

    users = []
    for name in names:
        key = find_user_key(all_ratings, name)
        users.append(
            {
                "name": name,
                "ratings": len(all_ratings[key]) if key else 0,
                "quiz_results": len(results_for(results, name)),
            }
        )
    users.sort(key=lambda user: user["name"].lower())
    return users


def delete_user_ratings(all_ratings: dict, name: str) -> int:
    """Remove all ratings of one user. Returns how many were removed."""
    key = find_user_key(all_ratings, name)
    if key is None:
        return 0
    return len(all_ratings.pop(key))


def without_user_results(results: list[dict], name: str) -> list[dict]:
    """Return the results list without this user's quiz results."""
    return [result for result in results if not same_name(result["player"], name)]


def remove_character_ratings(all_ratings: dict, character_id: str) -> int:
    """Remove one character's ratings from every user (used when a character is deleted)."""
    removed = 0
    for user_ratings in all_ratings.values():
        if user_ratings.pop(character_id, None) is not None:
            removed += 1
    return removed
