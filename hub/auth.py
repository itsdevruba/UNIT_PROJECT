"""Admin password: create, check and log in.

The password is never saved as plain text. We save a random salt and a
PBKDF2 hash of the password, and compare hashes when the admin logs in.
"""

import hashlib
import secrets

import questionary

from hub import display
from hub.config import ADMIN_FILE, MAX_LOGIN_ATTEMPTS, MIN_PASSWORD_LENGTH
from hub.storage import load_json, save_json

HASH_ITERATIONS = 100_000


def hash_password(password: str, salt: str) -> str:
    """Return the hex PBKDF2-SHA256 hash of `password` with `salt`."""
    digest = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), bytes.fromhex(salt), HASH_ITERATIONS
    )
    return digest.hex()


def validate_password(password: str) -> None:
    """Raise ValueError if the password is too short."""
    if len(password) < MIN_PASSWORD_LENGTH:
        raise ValueError(f"Password must be at least {MIN_PASSWORD_LENGTH} characters.")


def create_admin_password() -> bool:
    """Ask for a new admin password twice and save its hash. Returns True if saved."""
    while True:
        password = questionary.password("Create an admin password:").ask()
        if password is None:
            return False
        try:
            validate_password(password)
        except ValueError as error:
            display.error(str(error))
            continue

        again = questionary.password("Type it again:").ask()
        if again is None:
            return False
        if again != password:
            display.error("Passwords don't match. Try again.")
            continue

        salt = secrets.token_hex(16)
        if save_json(ADMIN_FILE, {"salt": salt, "password_hash": hash_password(password, salt)}):
            display.success("Admin password created.")
            return True
        return False


def check_password(password: str, admin: dict) -> bool:
    """True if `password` matches the saved hash."""
    return secrets.compare_digest(hash_password(password, admin["salt"]), admin["password_hash"])


def admin_login() -> bool:
    """Log in as admin. On first use, create the password instead."""
    admin = load_json(ADMIN_FILE, default=None)
    if not admin:
        display.warning("No admin password is set yet. Let's create one.")
        return create_admin_password()

    for attempt in range(1, MAX_LOGIN_ATTEMPTS + 1):
        password = questionary.password("Admin password:").ask()
        if password is None:
            return False
        if check_password(password, admin):
            display.success("Welcome, admin.")
            return True
        remaining = MAX_LOGIN_ATTEMPTS - attempt
        if remaining:
            display.error(f"Wrong password. {remaining} attempt(s) left.")

    display.error("Too many wrong attempts.")
    return False
