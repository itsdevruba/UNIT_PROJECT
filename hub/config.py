"""Project-wide constants: file paths, rating criteria, tiers, and quiz traits."""

from pathlib import Path

# ---------- Paths ----------
BASE_DIR = Path(__file__).resolve().parent.parent  # project root (UNIT_PROJECT)
DATA_DIR = BASE_DIR / "data"
CHARACTERS_FILE = DATA_DIR / "characters.json"
RATINGS_FILE = DATA_DIR / "user_ratings.json"
QUESTIONS_FILE = DATA_DIR / "questions.json"
QUIZ_RESULTS_FILE = DATA_DIR / "quiz_results.json"
ADMIN_FILE = DATA_DIR / "admin.json"

# ---------- Rating ----------
MIN_SCORE = 0
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
WEAK_MATCH_PERCENT = 75  # below this, the result says no character fits perfectly
MAX_NAME_LENGTH = 30
# Most people pick a mix of answers, so raw scores bunch up around the middle.
# Stretching them away from 5 lets characters with strong traits be reachable.
QUIZ_STRETCH = 2.5

# ---------- AI interview (Ollama) ----------
OLLAMA_MODEL = "llama3.2:3b"

# ---------- Users & admin ----------
# Demo mode lets anyone try the app right away: the admin menu opens without a password.
# Set it to False to require the admin password.
DEMO_MODE = True
GUEST_NAME = "Guest"  # owner of ratings saved before user accounts existed
MIN_PASSWORD_LENGTH = 4
MAX_LOGIN_ATTEMPTS = 3

# ---------- Settings ----------
SERIES: list[str] = ["GTA", "Red Dead", "Bully"]
