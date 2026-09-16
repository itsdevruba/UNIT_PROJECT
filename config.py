"""Project-wide constants: file paths, rating criteria, tiers, and quiz traits."""

from pathlib import Path

# ---------- Paths ----------
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
CHARACTERS_FILE = DATA_DIR / "characters.json"
RATINGS_FILE = DATA_DIR / "user_ratings.json"
QUESTIONS_FILE = DATA_DIR / "questions.json"
QUIZ_RESULT_FILE = DATA_DIR / "last_quiz_result.json"

# ---------- Rating ----------
MIN_SCORE = 1
MAX_SCORE = 10

# criterion name -> weight (weights must add up to 1.0)
CRITERIA: dict[str, float] = {
    "writing": 0.30,
    "growth": 0.20,
    "charisma": 0.20,
    "combat": 0.15,
    "memorability": 0.15,
}

# (minimum overall score, tier letter), checked from top to bottom
TIERS: list[tuple[float, str]] = [
    (9.0, "S"),
    (8.0, "A"),
    (6.5, "B"),
    (5.0, "C"),
    (0.0, "D"),
]

# ---------- Quiz ----------
TRAITS: list[str] = ["loyalty", "morality", "temper", "humor", "ambition"]
TOP_MATCHES = 3

# ---------- Settings ----------
SERIES: list[str] = ["GTA", "Red Dead", "Bully"]
