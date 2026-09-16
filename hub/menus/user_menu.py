"""Everything a logged-in user can do: browse, rate, tier list, compare, quiz."""

import questionary

from hub import characters as chars
from hub import config
from hub import display
from hub import quiz
from hub import ratings as rt
from hub import users
from hub.menus.helpers import BACK, confirm, pick_character, pick_from, pick_result, view_characters
from hub.storage import load_json, save_json

USER_MENU = [
    "Browse characters",
    "Search by name",
    "Rate a character",
    "My tier list",
    "Compare two characters",
    "Which character are you?",
    "Settings",
    "Log out",
]


def save_ratings(all_ratings: dict) -> None:
    if save_json(config.RATINGS_FILE, all_ratings):
        display.success("Ratings saved.")


def browse_menu(characters: list[dict], my_ratings: dict, settings: dict) -> None:
    """Filter by game or role, then show the table and let the user open a character."""
    while True:
        mode = questionary.select("Browse by:", choices=["All characters", "Game", "Role", BACK]).ask()

        if mode is None or mode == BACK:
            return
        if mode == "All characters":
            view_characters(characters, my_ratings, settings["spoilers"], "All characters")
            continue

        if mode == "Game":
            value = pick_from("Which game?", chars.get_games_by_year(characters), keep_order=True)
            field = "game"
        else:
            value = pick_from("Which role?", list(chars.get_roles(characters)))
            field = "role"

        if value is None:
            continue
        view_characters(chars.filter_by(characters, field, value), my_ratings, settings["spoilers"], value)


def search_menu(characters: list[dict], my_ratings: dict, settings: dict) -> None:
    query = questionary.text("Type a name (or part of it):").ask()
    if query is None:
        return
    results = chars.search(characters, query)
    if not results:
        display.warning(f"No characters match '{query.strip()}'.")
        return
    view_characters(results, my_ratings, settings["spoilers"], f"Results for '{query.strip()}'")


def rate_menu(characters: list[dict], all_ratings: dict, my_ratings: dict, settings: dict) -> None:
    """Pick a character, rate it, and save."""
    series = pick_from("Which series?", list(chars.get_series(characters)))
    if series is None:
        return
    character = pick_character(chars.filter_by(characters, "series", series), my_ratings, "Who do you want to rate?")
    if character is None:
        return

    display.show_character_details(character, settings["spoilers"])
    rating = rt.rate_character(character, my_ratings)
    if rating is None:
        display.warning("Rating cancelled.")
        return

    display.show_rating_result(character["name"], rating["overall"], rating["tier"])
    save_ratings(all_ratings)


def compare_menu(characters: list[dict], my_ratings: dict) -> None:
    rated = rt.rated_characters(characters, my_ratings)
    if len(rated) < 2:
        display.warning("Rate at least two characters to compare them.")
        return

    first = pick_character(rated, my_ratings, "First character:")
    if first is None:
        return
    others = [character for character in rated if character["id"] != first["id"]]
    second = pick_character(others, my_ratings, "Second character:")
    if second is None:
        return

    first_rating = my_ratings[first["id"]]
    second_rating = my_ratings[second["id"]]
    winners = rt.compare(first["name"], first_rating, second["name"], second_rating)
    display.show_comparison(first, second, first_rating, second_rating, winners)


def quiz_menu(name: str, characters: list[dict], questions: list[dict]) -> None:
    """Take the quiz / see my results / back."""
    while True:
        choice = questionary.select(
            "Which character are you?",
            choices=["Take the quiz", "My results", BACK],
        ).ask()

        if choice is None or choice == BACK:
            return

        if choice == "My results":
            mine = users.results_for(load_json(config.QUIZ_RESULTS_FILE, default=[]), name)
            mine.reverse()
            display.show_quiz_results(mine)
            while mine:
                result = pick_result(mine)
                if result is None:
                    break
                display.show_quiz_result(result["matches"], result["traits"], result["player"])
            continue

        series = pick_from(f"Match {name} with characters from:", list(chars.get_series(characters)))
        if series is None:
            continue

        display.console.print(f"[dim]Answer {len(questions)} questions honestly. There are no wrong answers.[/dim]")
        result = quiz.take_quiz(questions, chars.filter_by(characters, "series", series), series, name)
        if result is None:
            display.warning("Quiz cancelled.")
            continue

        display.show_quiz_result(result["matches"], result["traits"], name)
        results = load_json(config.QUIZ_RESULTS_FILE, default=[])
        results.append(result)
        save_json(config.QUIZ_RESULTS_FILE, results)


def settings_menu(all_ratings: dict, my_ratings: dict, settings: dict) -> None:
    """Spoiler-free mode on/off, reset my own ratings, back."""
    while True:
        spoiler_label = "Spoiler-free mode: " + ("OFF (story notes visible)" if settings["spoilers"] else "ON")
        choice = questionary.select("Settings:", choices=[spoiler_label, "Reset my ratings", BACK]).ask()

        if choice is None or choice == BACK:
            return
        if choice == spoiler_label:
            settings["spoilers"] = not settings["spoilers"]
            display.success("Story notes are now " + ("visible." if settings["spoilers"] else "hidden."))
        elif choice == "Reset my ratings":
            if not my_ratings:
                display.warning("You have no ratings to reset.")
            elif confirm(f"Delete all {len(my_ratings)} of your ratings? This cannot be undone."):
                my_ratings.clear()
                save_ratings(all_ratings)


def run_user_session(name: str, characters: list[dict], all_ratings: dict, questions: list[dict]) -> None:
    """Main loop for one logged-in user."""
    name = users.find_user_key(all_ratings, name) or name   # use the saved spelling for returning users
    my_ratings = users.get_user_ratings(all_ratings, name)
    settings = {"spoilers": False}
    display.console.print(f"\n[bold]Welcome, {name}.[/bold] [dim]You have rated {len(my_ratings)} character(s).[/dim]\n")

    while True:
        choice = questionary.select(f"[{name}] What would you like to do?", choices=USER_MENU).ask()

        if choice is None or choice == "Log out":
            break
        elif choice == "Browse characters":
            browse_menu(characters, my_ratings, settings)
        elif choice == "Search by name":
            search_menu(characters, my_ratings, settings)
        elif choice == "Rate a character":
            rate_menu(characters, all_ratings, my_ratings, settings)
        elif choice == "My tier list":
            display.show_tier_list(rt.build_tier_list(my_ratings, characters))
        elif choice == "Compare two characters":
            compare_menu(characters, my_ratings)
        elif choice == "Which character are you?":
            quiz_menu(name, characters, questions)
        elif choice == "Settings":
            settings_menu(all_ratings, my_ratings, settings)

    # don't keep empty entries for users who never rated anything
    key = users.find_user_key(all_ratings, name)
    if key is not None and not all_ratings[key]:
        del all_ratings[key]
    display.console.print(f"[dim]Logged out. See you, {name}.[/dim]\n")
