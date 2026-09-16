"""Working with the list of characters: browse, filter, search, add."""

import re

from config import TRAITS

ROLES: list[str] = ["Protagonist", "Antagonist", "Supporting"]


def get_series(characters: list[dict]) -> set[str]:
    """Return the unique series names (e.g. {"GTA", "Red Dead", "Bully"})."""
    return {character["series"] for character in characters}


def get_games(characters: list[dict], series: str | None = None) -> set[str]:
    """Return unique game names, optionally only for one series."""
    games = set()
    for character in characters:
        if series is None or character["series"] == series:
            games.add(character["game"])
    return games


def get_games_by_year(characters: list[dict]) -> list[str]:
    """Return unique game names ordered by release year (oldest first)."""
    years = {}
    for character in characters:
        year = character.get("year") or 9999
        years[character["game"]] = min(year, years.get(character["game"], 9999))
    return sorted(years, key=lambda game: (years[game], game))


def get_roles(characters: list[dict]) -> set[str]:
    """Return the unique roles used in the data."""
    return {character["role"] for character in characters}


def filter_by(characters: list[dict], field: str, value: str) -> list[dict]:
    """Return characters whose `field` equals `value` (e.g. field="role", value="Protagonist").

    For the "game" field, a character also matches if the game is in its "appears_in" list,
    so John Marston shows up under both Red Dead games.
    """
    results = []
    for character in characters:
        if character.get(field) == value:
            results.append(character)
        elif field == "game" and value in character.get("appears_in", []):
            results.append(character)
    return results


def search(characters: list[dict], query: str) -> list[dict]:
    """Return characters whose name contains `query` (case-insensitive)."""
    query = query.strip().lower()
    if not query:
        return []
    return [character for character in characters if query in character["name"].lower()]


def find_by_id(characters: list[dict], character_id: str) -> dict | None:
    """Return the character with this id, or None."""
    for character in characters:
        if character["id"] == character_id:
            return character
    return None


def sort_by_name(characters: list[dict]) -> list[dict]:
    """Return a new list sorted alphabetically by name."""
    return sorted(characters, key=lambda character: character["name"].lower())


def make_id(name: str) -> str:
    """Turn a name into an id: "Carl \\"CJ\\" Johnson" -> "carl-cj-johnson"."""
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")


def add_character(
    characters: list[dict],
    name: str,
    series: str,
    game: str,
    role: str = "Supporting",
    affiliation: str = "None",
    bio: str = "",
) -> dict:
    """Create a custom character, add it to `characters`, and return it.

    Raise ValueError if the name is empty or the character already exists.
    """
    name = name.strip()
    if not name:
        raise ValueError("Name cannot be empty.")
    if not game.strip():
        raise ValueError("Game cannot be empty.")

    character_id = make_id(name)
    if find_by_id(characters, character_id) is not None:
        raise ValueError(f"A character named '{name}' already exists.")

    new_character = {
        "id": character_id,
        "name": name,
        "series": series,
        "game": game.strip(),
        "appears_in": [game.strip()],
        "year": None,
        "role": role,
        "affiliation": affiliation.strip() or "None",
        "traits": {trait: 5 for trait in TRAITS},
        "bio": bio.strip() or "A custom character added by the user.",
        "spoiler_notes": "",
        "community_tier": "",
        "source": "",
        "custom": True,
    }
    characters.append(new_character)
    return new_character
