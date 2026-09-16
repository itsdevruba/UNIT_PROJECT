"""Rockstar Character Hub - entry point. Run with: python main.py"""

import questionary

import config
import display
from storage import load_json, save_json

MAIN_MENU = [
    "Browse characters",
    "Search by name",
    "Rate a character",
    "My tier list",
    "Compare two characters",
    "Which character are you?",
    "Settings",
    "Exit",
]


def browse_menu(characters: list[dict], ratings: dict) -> None:
    """Filter by series / game / role, then show the table and let the user open a character."""
    pass


def search_menu(characters: list[dict], ratings: dict) -> None:
    pass


def rate_menu(characters: list[dict], ratings: dict) -> None:
    """Pick a character, rate it, save ratings to RATINGS_FILE."""
    pass


def tier_list_menu(characters: list[dict], ratings: dict) -> None:
    pass


def compare_menu(characters: list[dict], ratings: dict) -> None:
    pass


def quiz_menu(characters: list[dict]) -> None:
    """Quick quiz / My last result / Back."""
    pass


def settings_menu(settings: dict) -> None:
    """Spoiler-free mode on/off, reset my ratings, back."""
    pass


def main() -> None:
    characters = load_json(config.CHARACTERS_FILE, default=[])
    ratings = load_json(config.RATINGS_FILE, default={})
    settings = {"spoilers": False}

    display.show_banner()

    try:
        while True:
            choice = questionary.select("What would you like to do?", choices=MAIN_MENU).ask()

            if choice is None or choice == "Exit":
                break
            elif choice == "Browse characters":
                browse_menu(characters, ratings)
            elif choice == "Search by name":
                search_menu(characters, ratings)
            elif choice == "Rate a character":
                rate_menu(characters, ratings)
            elif choice == "My tier list":
                tier_list_menu(characters, ratings)
            elif choice == "Compare two characters":
                compare_menu(characters, ratings)
            elif choice == "Which character are you?":
                quiz_menu(characters)
            elif choice == "Settings":
                settings_menu(settings)
    except KeyboardInterrupt:
        pass
    finally:
        display.console.print("\n[bold]Goodbye, partner. 🤠[/bold]")


if __name__ == "__main__":
    main()
