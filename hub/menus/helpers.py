"""Small menu helpers shared by the user and admin menus."""

import questionary
from questionary import Choice

from hub import characters as chars
from hub import display

BACK = "← Back"


def pick_from(message: str, options: list[str], keep_order: bool = False) -> str | None:
    """Select one string from `options` with a Back choice. Returns None on Back or Ctrl+C.

    Options are sorted alphabetically unless `keep_order` is True.
    """
    ordered = list(options) if keep_order else sorted(options)
    answer = questionary.select(message, choices=ordered + [BACK]).ask()
    if answer is None or answer == BACK:
        return None
    return answer


def pick_character(
    options: list[dict], ratings: dict | None = None, message: str = "Choose a character:"
) -> dict | None:
    """Let the user pick one character from `options`. Returns None on Back or Ctrl+C."""
    if not options:
        return None
    ratings = ratings or {}
    choices = []
    for character in chars.sort_by_name(options):
        label = f"{character['name']}  ({character['game']})"
        rating = ratings.get(character["id"])
        if rating:
            label += f"  [{rating['tier']}]"
        choices.append(Choice(title=label, value=character["id"]))
    choices.append(BACK)

    character_id = questionary.select(message, choices=choices).ask()
    if character_id is None or character_id == BACK:
        return None
    return chars.find_by_id(options, character_id)


def confirm(message: str) -> bool:
    """Yes/No question that defaults to No. Ctrl+C counts as No."""
    return bool(questionary.confirm(message, default=False).ask())


def pick_result(results: list[dict], message: str = "Open a result:") -> dict | None:
    """Pick one quiz result from a list. Returns None on Back or Ctrl+C."""
    choices = [
        Choice(
            title=f"{result['player']}  ({result['series']}, {result['taken_at']})",
            value=str(index),
        )
        for index, result in enumerate(results)
    ]
    picked = questionary.select(message, choices=choices + [BACK]).ask()
    if picked is None or picked == BACK:
        return None
    return results[int(picked)]


def browse_results(results: list[dict]) -> None:
    """Let the user open results one by one until they go back."""
    while results:
        result = pick_result(results)
        if result is None:
            return
        display.show_saved_result(result)


def view_characters(characters: list[dict], ratings: dict, spoilers: bool, title: str) -> None:
    """Show a table, then let the user open characters one by one until they go back."""
    display.show_characters(chars.sort_by_name(characters), ratings, title)
    while True:
        character = pick_character(characters, ratings, "Open a character:")
        if character is None:
            return
        display.show_character_details(character, spoilers, ratings.get(character["id"]))
