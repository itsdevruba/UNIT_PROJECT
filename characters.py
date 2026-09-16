"""Working with the list of characters: browse, filter, search, add."""


def get_series(characters: list[dict]) -> set[str]:
    """Return the unique series names (e.g. {"GTA", "Red Dead", "Bully"})."""
    # TODO: use a set comprehension
    pass


def get_games(characters: list[dict], series: str | None = None) -> set[str]:
    """Return unique game names, optionally only for one series."""
    pass


def filter_by(characters: list[dict], field: str, value: str) -> list[dict]:
    """Return characters whose `field` equals `value` (e.g. field="role", value="Protagonist")."""
    pass


def search(characters: list[dict], query: str) -> list[dict]:
    """Return characters whose name contains `query` (case-insensitive)."""
    pass


def find_by_id(characters: list[dict], character_id: str) -> dict | None:
    """Return the character with this id, or None."""
    pass


def add_character(characters: list[dict], new_character: dict) -> list[dict]:
    """Add a custom character. Raise ValueError if the name or id already exists."""
    pass
