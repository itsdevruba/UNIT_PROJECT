"""Reading and writing JSON files safely."""

import json
from pathlib import Path


def load_json(path: Path, default):
    """Load JSON data from `path`.

    Returns `default` if the file does not exist.
    If the file is corrupted, back it up as `<name>.bak` and return `default`.
    """
    # TODO:
    # 1. try: open the file with encoding="utf-8" and json.load it
    # 2. except FileNotFoundError: return default
    # 3. except json.JSONDecodeError: rename the file to .bak, warn the user, return default
    pass


def save_json(path: Path, data) -> None:
    """Save `data` to `path` as pretty JSON (indent=2, ensure_ascii=False)."""
    # TODO: create the parent folder if needed, then json.dump
    pass
