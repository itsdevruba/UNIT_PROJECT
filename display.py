"""Everything that prints to the terminal (rich tables, panels, colors)."""

import pyfiglet
from rich.console import Console
from rich.table import Table

console = Console()

TIER_COLORS = {"S": "bold yellow", "A": "green", "B": "cyan", "C": "magenta", "D": "red"}


def show_banner() -> None:
    """Print the big title (pyfiglet) and a short welcome line."""
    pass


def show_characters(characters: list[dict], ratings: dict | None = None) -> None:
    """Print a table: name, game, role, affiliation, and the user's tier if rated."""
    pass


def show_character_details(character: dict, spoilers: bool = False) -> None:
    """Print one character's full info. Only show spoiler_notes if `spoilers` is True."""
    pass


def show_tier_list(tier_list: dict[str, list[tuple[str, float]]]) -> None:
    """Print the tier list with a color per tier."""
    pass


def show_comparison(first: dict, second: dict, winners: dict[str, str]) -> None:
    """Print a side-by-side comparison table."""
    pass


def show_quiz_result(matches: list[tuple[str, int]], user_traits: dict[str, float]) -> None:
    """Print the best match, runner-ups, and a simple bar for each trait."""
    pass


def success(message: str) -> None:
    console.print(f"[green]✔ {message}[/green]")


def error(message: str) -> None:
    console.print(f"[red]✘ {message}[/red]")


def warning(message: str) -> None:
    console.print(f"[yellow]⚠ {message}[/yellow]")
