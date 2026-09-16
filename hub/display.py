"""Everything that prints to the terminal (rich tables, panels, colors)."""

import pyfiglet
from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from hub.config import CRITERIA, TIERS, TRAITS

console = Console()

TIER_COLORS = {"S": "bold yellow", "A": "bold green", "B": "bold cyan", "C": "bold magenta", "D": "bold red"}
SERIES_COLORS = {"GTA": "bright_green", "Red Dead": "red3", "Bully": "orange3"}


# ---------- small helpers ----------

def tier_badge(tier: str | None) -> str:
    """Return a colored tier letter, or a dim dash if not rated."""
    if not tier:
        return "[dim]—[/dim]"
    color = TIER_COLORS.get(tier, "white")
    return f"[{color}] {tier} [/{color}]"


def series_label(series: str) -> str:
    color = SERIES_COLORS.get(series, "white")
    return f"[{color}]{series}[/{color}]"


def success(message: str) -> None:
    console.print(f"[green]{message}[/green]")


def error(message: str) -> None:
    console.print(f"[bold red]Error:[/bold red] [red]{message}[/red]")


def warning(message: str) -> None:
    console.print(f"[bold yellow]Note:[/bold yellow] [yellow]{message}[/yellow]")


# ---------- screens ----------

def show_banner() -> None:
    """Print the big title and a short welcome line."""
    title = pyfiglet.figlet_format("Rockstar", font="slant")
    console.print(f"[bold yellow]{title}[/bold yellow]", end="")
    console.print("[bold]              C H A R A C T E R   H U B[/bold]")
    console.print("[dim]  GTA · Red Dead · Bully — rate, rank and find your match[/dim]\n")


def show_characters(characters: list[dict], ratings: dict | None = None, title: str = "Characters") -> None:
    """Print a table: name, series, game, role, affiliation, and the user's tier if rated."""
    if not characters:
        warning("No characters found.")
        return

    ratings = ratings or {}
    table = Table(title=f"[bold]{title}[/bold] [dim]({len(characters)})[/dim]", box=box.SIMPLE_HEAVY)
    table.add_column("#", justify="right", style="dim")
    table.add_column("Name", style="bold")
    table.add_column("Series")
    table.add_column("Game")
    table.add_column("Role")
    table.add_column("Affiliation", style="dim")
    table.add_column("My tier", justify="center")

    for number, character in enumerate(characters, start=1):
        rating = ratings.get(character["id"])
        name = character["name"] + (" [dim](custom)[/dim]" if character.get("custom") else "")
        table.add_row(
            str(number),
            name,
            series_label(character["series"]),
            character["game"],
            character["role"],
            character["affiliation"],
            tier_badge(rating["tier"] if rating else None),
        )
    console.print(table)


def show_character_details(character: dict, spoilers: bool = False, rating: dict | None = None) -> None:
    """Print one character's full info. Only show spoiler_notes if `spoilers` is True."""
    lines = [
        f"[bold]Series:[/bold]       {series_label(character['series'])}",
        f"[bold]Game:[/bold]         {character['game']}",
        f"[bold]Appears in:[/bold]   {', '.join(character.get('appears_in', []))}",
        f"[bold]Role:[/bold]         {character['role']}",
        f"[bold]Affiliation:[/bold]  {character['affiliation']}",
        "",
        character["bio"],
    ]

    if rating:
        lines.append("")
        lines.append(f"[bold]Your rating:[/bold] {rating['overall']} {tier_badge(rating['tier'])}")
        for criterion in CRITERIA:
            lines.append(f"  {criterion:<13} {score_bar(rating['scores'][criterion])}")

    if character.get("spoiler_notes"):
        lines.append("")
        if spoilers:
            lines.append(f"[bold red]Spoilers:[/bold red] {character['spoiler_notes']}")
        else:
            lines.append("[dim]Story notes hidden. Turn off spoiler-free mode in Settings to see them.[/dim]")

    console.print(Panel("\n".join(lines), title=f"[bold yellow]{character['name']}[/bold yellow]",
                        border_style="yellow", padding=(1, 2), width=min(console.width, 90)))


def score_bar(score: float, maximum: int = 10, width: int = 20) -> str:
    """Return a text bar like ██████████░░░░░░░░░░ 5."""
    filled = round(score / maximum * width)
    return f"[yellow]{'█' * filled}[/yellow][dim]{'░' * (width - filled)}[/dim] {score}"


def show_rating_result(name: str, overall: float, tier: str) -> None:
    """Print the result right after the user rates a character."""
    console.print(Panel(f"[bold]{name}[/bold]\nOverall score: [bold]{overall}[/bold] / 10   Tier: {tier_badge(tier)}",
                        border_style="green", expand=False))


def show_tier_list(tier_list: dict[str, list[tuple[str, float]]], title: str = "My Tier List") -> None:
    """Print the tier list with a color per tier."""
    if not any(tier_list.values()):
        warning("No rated characters yet.")
        return

    table = Table(title=f"[bold]{title}[/bold]", box=box.ROUNDED, show_header=False, padding=(0, 1))
    table.add_column("Tier", justify="center", width=5)
    table.add_column("Characters")

    for _, tier in TIERS:
        entries = tier_list.get(tier, [])
        if entries:
            names = "  ·  ".join(f"{name} [dim]{overall}[/dim]" for name, overall in entries)
        else:
            names = "[dim]—[/dim]"
        table.add_row(tier_badge(tier), names)
    console.print(table)


def show_comparison(first: dict, second: dict, first_rating: dict, second_rating: dict,
                    winners: dict[str, str]) -> None:
    """Print a side-by-side comparison table of two rated characters."""
    table = Table(title="[bold]Head to Head[/bold]", box=box.SIMPLE_HEAVY)
    table.add_column("Criterion")
    table.add_column(first["name"], justify="center")
    table.add_column(second["name"], justify="center")

    for criterion in CRITERIA:
        a = first_rating["scores"][criterion]
        b = second_rating["scores"][criterion]
        winner = winners.get(criterion)
        a_text = f"[bold green]{a}[/bold green]" if winner == first["name"] else str(a)
        b_text = f"[bold green]{b}[/bold green]" if winner == second["name"] else str(b)
        table.add_row(criterion.capitalize(), a_text, b_text)

    table.add_section()
    table.add_row("[bold]Overall[/bold]", f"[bold]{first_rating['overall']}[/bold]", f"[bold]{second_rating['overall']}[/bold]")
    table.add_row("[bold]Tier[/bold]", tier_badge(first_rating["tier"]), tier_badge(second_rating["tier"]))
    console.print(table)

    if first_rating["overall"] > second_rating["overall"]:
        console.print(f"Winner: [bold]{first['name']}[/bold] comes out on top.\n")
    elif second_rating["overall"] > first_rating["overall"]:
        console.print(f"Winner: [bold]{second['name']}[/bold] comes out on top.\n")
    else:
        console.print("It's a tie.\n")


def show_quiz_result(matches: list[tuple[str, int]], user_traits: dict[str, float], player: str = "You") -> None:
    """Print the best match, runner-ups, and a simple bar for each trait."""
    if not matches:
        warning("No match found.")
        return

    best_name, best_score = matches[0]
    verb = "You are" if player == "You" else f"{player} is"
    lines = [f"[bold yellow]{verb}... {best_name}[/bold yellow]   [green]{best_score}% match[/green]"]
    if len(matches) > 1:
        runner_ups = " · ".join(f"{name} {score}%" for name, score in matches[1:])
        lines.append(f"[dim]Runner-ups: {runner_ups}[/dim]")
    lines.append("")
    for trait in TRAITS:
        lines.append(f"{trait:<9} {score_bar(user_traits[trait])}")
    console.print(Panel("\n".join(lines), border_style="yellow", padding=(1, 2), expand=False))


def show_quiz_results(results: list[dict]) -> None:
    """Print everyone's quiz results, newest first."""
    if not results:
        warning("Nobody has taken the quiz yet.")
        return

    table = Table(title=f"[bold]Quiz Results[/bold] [dim]({len(results)})[/dim]", box=box.SIMPLE_HEAVY)
    table.add_column("#", justify="right", style="dim")
    table.add_column("Player", style="bold")
    table.add_column("Series")
    table.add_column("Character", style="yellow")
    table.add_column("Match", justify="right")
    table.add_column("Taken", style="dim")

    for number, result in enumerate(results, start=1):
        name, score = result["matches"][0]
        table.add_row(str(number), result["player"], series_label(result["series"]),
                      name, f"{score}%", result["taken_at"])
    console.print(table)


def show_users(users: list[dict]) -> None:
    """Print every user with how many ratings and quiz results they have."""
    if not users:
        warning("No users yet.")
        return
    table = Table(title=f"[bold]Users[/bold] [dim]({len(users)})[/dim]", box=box.SIMPLE_HEAVY)
    table.add_column("#", justify="right", style="dim")
    table.add_column("Name", style="bold")
    table.add_column("Ratings", justify="right")
    table.add_column("Quiz results", justify="right")
    for number, user in enumerate(users, start=1):
        table.add_row(str(number), user["name"], str(user["ratings"]), str(user["quiz_results"]))
    console.print(table)


def show_traits(character: dict) -> None:
    """Print a character's quiz traits as bars (admin view)."""
    lines = [f"{trait:<9} {score_bar(character['traits'][trait])}" for trait in TRAITS]
    console.print(Panel("\n".join(lines), title=f"[bold]{character['name']} traits[/bold]", expand=False))
