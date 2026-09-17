"""Rockstar Character Hub - entry point. Run with: python main.py"""

import questionary

from hub import config, display, users
from hub.auth import admin_login
from hub.menus.admin_menu import run_admin_session
from hub.menus.user_menu import run_user_session
from hub.storage import load_json, save_json

START_MENU = ["Log in as user", "Log in as admin", "Exit"]


def load_ratings() -> dict:
    """Load all users' ratings, converting the old single-user format if needed."""
    raw = load_json(config.RATINGS_FILE, default={})
    all_ratings = users.migrate_ratings(raw)
    if all_ratings is not raw:
        save_json(config.RATINGS_FILE, all_ratings)
    return all_ratings


def main() -> None:
    """Load the data, show the banner, and run the start menu until the user exits."""
    characters = load_json(config.CHARACTERS_FILE, default=[])
    questions = load_json(config.QUESTIONS_FILE, default=[])

    display.show_banner()
    if not characters:
        display.error(f"No characters found. Make sure {config.CHARACTERS_FILE} exists.")
        return
    all_ratings = load_ratings()

    try:
        while True:
            choice = questionary.select("Who's using the hub?", choices=START_MENU).ask()

            if choice is None or choice == "Exit":
                break
            elif choice == "Log in as user":
                name = users.ask_name("Enter your name:")
                if name:
                    run_user_session(name, characters, all_ratings, questions)
            elif choice == "Log in as admin":
                if admin_login():
                    run_admin_session(characters, all_ratings)
    except KeyboardInterrupt:
        pass
    finally:
        display.console.print("\n[bold]Goodbye, partner.[/bold]")


if __name__ == "__main__":
    main()
