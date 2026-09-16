"""Rockstar Character Hub - entry point. Run with: python main.py"""

import questionary
from questionary import Choice

import characters as chars
import config
import display
import quiz
import ratings as rt
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

BACK = "← Back"


# ---------- helpers ----------

def pick_character(options: list[dict], ratings: dict, message: str = "Choose a character:") -> dict | None:
    """Let the user pick one character from `options`. Returns None on Back or Ctrl+C."""
    if not options:
        return None
    choices = []
    for character in chars.sort_by_name(options):
        rating = ratings.get(character["id"])
        label = f"{character['name']}  ({character['game']})"
        if rating:
            label += f"  [{rating['tier']}]"
        choices.append(Choice(title=label, value=character["id"]))
    choices.append(BACK)

    character_id = questionary.select(message, choices=choices).ask()
    if character_id is None or character_id == BACK:
        return None
    return chars.find_by_id(options, character_id)


def pick_from(message: str, options: list[str], keep_order: bool = False) -> str | None:
    """Select one string from `options` with a Back choice. Returns None on Back or Ctrl+C.

    Options are sorted alphabetically unless `keep_order` is True.
    """
    ordered = list(options) if keep_order else sorted(options)
    answer = questionary.select(message, choices=ordered + [BACK]).ask()
    if answer is None or answer == BACK:
        return None
    return answer


def view_characters(characters: list[dict], ratings: dict, settings: dict, title: str) -> None:
    """Show a table, then let the user open characters one by one until they go back."""
    display.show_characters(chars.sort_by_name(characters), ratings, title)
    while True:
        character = pick_character(characters, ratings, "Open a character:")
        if character is None:
            return
        display.show_character_details(character, settings["spoilers"], ratings.get(character["id"]))


def save_ratings(ratings: dict) -> None:
    if save_json(config.RATINGS_FILE, ratings):
        display.success("Ratings saved.")


# ---------- menus ----------

def browse_menu(characters: list[dict], ratings: dict, settings: dict) -> None:
    """Filter by game or role, then show the table and let the user open a character."""
    while True:
        mode = questionary.select(
            "Browse by:",
            choices=["All characters", "Game", "Role", BACK],
        ).ask()

        if mode is None or mode == BACK:
            return
        if mode == "All characters":
            view_characters(characters, ratings, settings, "All characters")
            continue

        if mode == "Game":
            value = pick_from("Which game?", chars.get_games_by_year(characters), keep_order=True)
            field = "game"
        else:
            value = pick_from("Which role?", list(chars.get_roles(characters)))
            field = "role"

        if value is None:
            continue
        view_characters(chars.filter_by(characters, field, value), ratings, settings, value)


def search_menu(characters: list[dict], ratings: dict, settings: dict) -> None:
    query = questionary.text("Type a name (or part of it):").ask()
    if query is None:
        return
    results = chars.search(characters, query)
    if not results:
        display.warning(f"No characters match '{query.strip()}'.")
        return
    view_characters(results, ratings, settings, f"Results for '{query.strip()}'")


def rate_menu(characters: list[dict], ratings: dict, settings: dict) -> None:
    """Pick a character, rate it, save ratings to RATINGS_FILE."""
    series = pick_from("Which series?", list(chars.get_series(characters)))
    if series is None:
        return
    character = pick_character(chars.filter_by(characters, "series", series), ratings, "Who do you want to rate?")
    if character is None:
        return

    display.show_character_details(character, settings["spoilers"])
    rating = rt.rate_character(character, ratings)
    if rating is None:
        display.warning("Rating cancelled.")
        return

    display.show_rating_result(character["name"], rating["overall"], rating["tier"])
    save_ratings(ratings)


def tier_list_menu(characters: list[dict], ratings: dict) -> None:
    display.show_tier_list(rt.build_tier_list(ratings, characters))


def compare_menu(characters: list[dict], ratings: dict) -> None:
    rated = rt.rated_characters(characters, ratings)
    if len(rated) < 2:
        display.warning("Rate at least two characters to compare them.")
        return

    first = pick_character(rated, ratings, "First character:")
    if first is None:
        return
    others = [character for character in rated if character["id"] != first["id"]]
    second = pick_character(others, ratings, "Second character:")
    if second is None:
        return

    first_rating = ratings[first["id"]]
    second_rating = ratings[second["id"]]
    winners = rt.compare(first["name"], first_rating, second["name"], second_rating)
    display.show_comparison(first, second, first_rating, second_rating, winners)


def quiz_menu(characters: list[dict], questions: list[dict]) -> None:
    """Take the quiz / see everyone's results / back."""
    while True:
        choice = questionary.select(
            "Which character are you?",
            choices=["Take the quiz", "All results", BACK],
        ).ask()

        if choice is None or choice == BACK:
            return
        if choice == "All results":
            results_menu()
            continue

        player = quiz.ask_name()
        if player is None:
            continue
        series = pick_from(f"Hi {player}! Match you with characters from:", list(chars.get_series(characters)))
        if series is None:
            continue

        display.console.print(f"[dim]Answer {len(questions)} questions honestly. There are no wrong answers.[/dim]")
        result = quiz.take_quiz(questions, chars.filter_by(characters, "series", series), series, player)
        if result is None:
            display.warning("Quiz cancelled.")
            continue

        display.show_quiz_result(result["matches"], result["traits"], player)
        results = load_json(config.QUIZ_RESULTS_FILE, default=[])
        results.append(result)
        save_json(config.QUIZ_RESULTS_FILE, results)


def results_menu() -> None:
    """Show all quiz results (newest first) and let the user open one."""
    results = load_json(config.QUIZ_RESULTS_FILE, default=[])
    results.reverse()
    display.show_quiz_results(results)
    if not results:
        return

    while True:
        choices = [
            Choice(title=f"{r['player']}  ({r['series']}, {r['taken_at']})", value=str(index))
            for index, r in enumerate(results)
        ]
        picked = questionary.select("Open a result:", choices=choices + [BACK]).ask()
        if picked is None or picked == BACK:
            return
        result = results[int(picked)]
        display.show_quiz_result(result["matches"], result["traits"], result["player"])


def settings_menu(ratings: dict, settings: dict) -> None:
    """Spoiler-free mode on/off, reset my ratings, back."""
    while True:
        spoiler_label = "Spoiler-free mode: " + ("OFF (story notes visible)" if settings["spoilers"] else "ON")
        choice = questionary.select("Settings:", choices=[spoiler_label, "Reset my ratings", BACK]).ask()

        if choice is None or choice == BACK:
            return
        if choice == spoiler_label:
            settings["spoilers"] = not settings["spoilers"]
            display.success("Story notes are now " + ("visible." if settings["spoilers"] else "hidden."))
        elif choice == "Reset my ratings":
            if not ratings:
                display.warning("You have no ratings to reset.")
                continue
            sure = questionary.confirm(f"Delete all {len(ratings)} ratings? This cannot be undone.", default=False).ask()
            if sure:
                ratings.clear()
                save_ratings(ratings)


def main() -> None:
    characters = load_json(config.CHARACTERS_FILE, default=[])
    ratings = load_json(config.RATINGS_FILE, default={})
    questions = load_json(config.QUESTIONS_FILE, default=[])
    settings = {"spoilers": False}

    display.show_banner()
    if not characters:
        display.error(f"No characters found. Make sure {config.CHARACTERS_FILE} exists.")
        return

    try:
        while True:
            choice = questionary.select("What would you like to do?", choices=MAIN_MENU).ask()

            if choice is None or choice == "Exit":
                break
            elif choice == "Browse characters":
                browse_menu(characters, ratings, settings)
            elif choice == "Search by name":
                search_menu(characters, ratings, settings)
            elif choice == "Rate a character":
                rate_menu(characters, ratings, settings)
            elif choice == "My tier list":
                tier_list_menu(characters, ratings)
            elif choice == "Compare two characters":
                compare_menu(characters, ratings)
            elif choice == "Which character are you?":
                quiz_menu(characters, questions)
            elif choice == "Settings":
                settings_menu(ratings, settings)
    except KeyboardInterrupt:
        pass
    finally:
        display.console.print("\n[bold]Goodbye, partner.[/bold]")


if __name__ == "__main__":
    main()
