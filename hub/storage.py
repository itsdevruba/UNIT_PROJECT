"""Reading and writing JSON files safely."""

import json
from pathlib import Path

from hub import display


def load_json(path: Path, default):
    """Load JSON data from `path`.

    Returns `default` if the file does not exist.
    If the file is corrupted, back it up as `<name>.bak` and return `default`.
    """
    try:
        with open(path, "r", encoding="utf-8") as file:
            return json.load(file)
    except FileNotFoundError:
        return default
    except json.JSONDecodeError:
        backup = path.with_name(path.name + ".bak")
        path.replace(backup)
        display.warning(f"{path.name} was corrupted. A backup was saved as {backup.name}, starting fresh.")
        return default


def save_json(path: Path, data) -> bool:
    """Save `data` to `path` as pretty JSON.

    Writes to a temporary file first, then replaces the real file,
    so a crash in the middle of saving never leaves a half-written file.
    Returns True if saved, False if something went wrong.
    """
    temp = path.with_name(path.name + ".tmp")
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(temp, "w", encoding="utf-8") as file:
            json.dump(data, file, ensure_ascii=False, indent=2)
        temp.replace(path)
        return True
    except OSError as error:
        display.error(f"Could not save {path.name}: {error}")
        return False
