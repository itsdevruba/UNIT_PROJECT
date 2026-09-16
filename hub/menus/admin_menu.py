"""Admin tools: quiz results, users & ratings, and managing characters."""

import questionary

from hub import characters as chars
from hub import config
from hub import display
from hub import ratings as rt
from hub import users
from hub.menus.helpers import BACK, confirm, pick_character, pick_from, pick_result
from hub.storage import load_json, save_json

ADMIN_MENU = ["Quiz results", "Users & ratings", "Manage characters", "Log out"]
FIELDS_TO_EDIT = ["bio", "spoiler_notes", "affiliation", "role", "traits"]


# ---------- quiz results ----------

def quiz_results_menu() -> None:
    while True:
        results = load_json(config.QUIZ_RESULTS_FILE, default=[])
        newest_first = list(reversed(results))
        display.show_quiz_results(newest_first)
        if not results:
            return

        choice = questionary.select("Quiz results:", choices=["Open a result", "Delete a result",
                                                              "Delete ALL results", BACK]).ask()
        if choice is None or choice == BACK:
            return

        if choice == "Open a result":
            result = pick_result(newest_first)
            if result:
                display.show_quiz_result(result["matches"], result["traits"], result["player"],
                                         result.get("reason", ""))

        elif choice == "Delete a result":
            result = pick_result(newest_first, "Which result do you want to delete?")
            if result and confirm(f"Delete {result['player']}'s {result['series']} result from {result['taken_at']}?"):
                results.remove(result)
                if save_json(config.QUIZ_RESULTS_FILE, results):
                    display.success("Result deleted.")

        elif choice == "Delete ALL results":
            if confirm(f"Delete all {len(results)} quiz results? This cannot be undone."):
                if save_json(config.QUIZ_RESULTS_FILE, []):
                    display.success("All quiz results deleted.")


# ---------- users & ratings ----------

def users_menu(characters: list[dict], all_ratings: dict) -> None:
    while True:
        results = load_json(config.QUIZ_RESULTS_FILE, default=[])
        user_list = users.list_users(all_ratings, results)
        display.show_users(user_list)
        if not user_list:
            return

        name = pick_from("Open a user:", [user["name"] for user in user_list])
        if name is None:
            return
        user_detail_menu(name, characters, all_ratings)


def user_detail_menu(name: str, characters: list[dict], all_ratings: dict) -> None:
    while True:
        key = users.find_user_key(all_ratings, name)
        user_ratings = all_ratings.get(key, {}) if key else {}
        choice = questionary.select(
            f"User: {name}",
            choices=["View tier list", "Delete their ratings", "Delete their quiz results",
                     "Delete user completely", BACK],
        ).ask()

        if choice is None or choice == BACK:
            return

        if choice == "View tier list":
            display.show_tier_list(rt.build_tier_list(user_ratings, characters), f"{name}'s Tier List")

        elif choice == "Delete their ratings":
            if not user_ratings:
                display.warning(f"{name} has no ratings.")
            elif confirm(f"Delete all {len(user_ratings)} ratings by {name}?"):
                users.delete_user_ratings(all_ratings, name)
                if save_json(config.RATINGS_FILE, all_ratings):
                    display.success(f"{name}'s ratings deleted.")

        elif choice == "Delete their quiz results":
            results = load_json(config.QUIZ_RESULTS_FILE, default=[])
            count = len(users.results_for(results, name))
            if not count:
                display.warning(f"{name} has no quiz results.")
            elif confirm(f"Delete {count} quiz result(s) by {name}?"):
                if save_json(config.QUIZ_RESULTS_FILE, users.without_user_results(results, name)):
                    display.success(f"{name}'s quiz results deleted.")

        elif choice == "Delete user completely":
            if confirm(f"Delete {name} with all their ratings and quiz results?"):
                users.delete_user_ratings(all_ratings, name)
                results = users.without_user_results(load_json(config.QUIZ_RESULTS_FILE, default=[]), name)
                if save_json(config.RATINGS_FILE, all_ratings) and save_json(config.QUIZ_RESULTS_FILE, results):
                    display.success(f"{name} deleted.")
                return


# ---------- characters ----------

def ask_text(message: str, default: str = "", required: bool = False) -> str | None:
    """Ask for text. Re-ask if `required` and empty. None on Ctrl+C."""
    while True:
        value = questionary.text(message, default=default).ask()
        if value is None:
            return None
        if required and not value.strip():
            display.error("This field is required.")
            continue
        return value.strip()


def ask_traits(current: dict[str, int] | None = None) -> dict[str, int] | None:
    """Ask for each quiz trait from 0 to 10."""
    traits = {}
    for trait in config.TRAITS:
        default = str(current[trait]) if current else "5"
        while True:
            raw = questionary.text(f"{trait.capitalize()} (0-10):", default=default).ask()
            if raw is None:
                return None
            try:
                traits[trait] = rt.validate_score(raw)
                break
            except ValueError as error:
                display.error(str(error))
    return traits


def add_character_menu(characters: list[dict]) -> None:
    while True:
        name = ask_text("Character name:", required=True)
        if name is None:
            return
        if chars.find_by_id(characters, chars.make_id(name)) is None:
            break
        display.error(f"A character named '{name}' already exists. Try another name.")
    series = pick_from("Series:", config.SERIES, keep_order=True)
    if series is None:
        return

    other = "Other (type a new game)"
    game = pick_from("Game:", sorted(chars.get_games(characters, series)) + [other], keep_order=True)
    if game is None:
        return
    if game == other:
        game = ask_text("Game name:", required=True)
        if game is None:
            return

    role = pick_from("Role:", chars.ROLES, keep_order=True)
    affiliation = ask_text("Affiliation (optional):")
    bio = ask_text("Short spoiler-free bio (optional):")
    if role is None or affiliation is None or bio is None:
        return

    display.console.print("[dim]Quiz traits decide who this character matches with in the quiz.[/dim]")
    traits = ask_traits()
    if traits is None:
        return

    try:
        new_character = chars.add_character(characters, name, series, game, role, affiliation, bio)
    except ValueError as error:
        display.error(str(error))
        return

    new_character["traits"] = traits
    if save_json(config.CHARACTERS_FILE, characters):
        display.success(f"{new_character['name']} added.")
        display.show_character_details(new_character, spoilers=True)


def edit_character_menu(characters: list[dict]) -> None:
    character = pick_character(characters, message="Which character do you want to edit?")
    if character is None:
        return

    while True:
        display.show_character_details(character, spoilers=True)
        display.show_traits(character)
        field = pick_from("What do you want to change?", FIELDS_TO_EDIT, keep_order=True)
        if field is None:
            return

        if field == "traits":
            new_value = ask_traits(character["traits"])
        elif field == "role":
            new_value = pick_from("Role:", chars.ROLES, keep_order=True)
        else:
            new_value = ask_text(f"New {field.replace('_', ' ')}:", default=character.get(field, ""))

        if new_value is None:
            continue
        character[field] = new_value
        if save_json(config.CHARACTERS_FILE, characters):
            display.success(f"{character['name']}'s {field.replace('_', ' ')} updated.")


def delete_character_menu(characters: list[dict], all_ratings: dict) -> None:
    custom = [character for character in characters if character.get("custom")]
    if not custom:
        display.warning("There are no custom characters. Original characters can't be deleted.")
        return

    character = pick_character(custom, message="Which custom character do you want to delete?")
    if character is None or not confirm(f"Delete {character['name']}? Their ratings from all users will be removed too."):
        return

    chars.delete_character(characters, character["id"])
    removed = users.remove_character_ratings(all_ratings, character["id"])
    if save_json(config.CHARACTERS_FILE, characters) and save_json(config.RATINGS_FILE, all_ratings):
        display.success(f"{character['name']} deleted ({removed} rating(s) removed).")


def characters_menu(characters: list[dict], all_ratings: dict) -> None:
    while True:
        custom_count = sum(1 for character in characters if character.get("custom"))
        choice = questionary.select(
            f"Manage characters ({len(characters)} total, {custom_count} custom):",
            choices=["Add a character", "Edit a character", "Delete a custom character", BACK],
        ).ask()

        if choice is None or choice == BACK:
            return
        if choice == "Add a character":
            add_character_menu(characters)
        elif choice == "Edit a character":
            edit_character_menu(characters)
        elif choice == "Delete a custom character":
            delete_character_menu(characters, all_ratings)


def run_admin_session(characters: list[dict], all_ratings: dict) -> None:
    """Main loop for the admin."""
    while True:
        choice = questionary.select("[Admin] What would you like to do?", choices=ADMIN_MENU).ask()

        if choice is None or choice == "Log out":
            display.console.print("[dim]Admin logged out.[/dim]\n")
            return
        if choice == "Quiz results":
            quiz_results_menu()
        elif choice == "Users & ratings":
            users_menu(characters, all_ratings)
        elif choice == "Manage characters":
            characters_menu(characters, all_ratings)
