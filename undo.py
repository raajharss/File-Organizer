"""
Undo utility for Smart File Organizer.
Reverses file movements recorded in logs/movements.json.

Usage:
    python undo.py                 # undo the most recent run
    python undo.py --run <run_id>  # undo one specific run
    python undo.py --all           # undo every recorded movement
"""

import sys
import json
import shutil
import argparse
from pathlib import Path

LOG_DIR = Path("logs")
MOVEMENTS_FILE = LOG_DIR / "movements.json"


def load_history() -> list:
    if not MOVEMENTS_FILE.exists():
        print("No movement history found. Nothing to undo.")
        sys.exit(0)
    with open(MOVEMENTS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_history(history: list):
    with open(MOVEMENTS_FILE, "w", encoding="utf-8") as f:
        json.dump(history, f, indent=2)


def undo_entries(entries: list) -> list:
    """Moves files back to their original location. Returns entries that failed."""
    failed = []
    for entry in entries:
        new_path = Path(entry["new_path"])
        original_path = Path(entry["original_path"])
        if not new_path.exists():
            print(f"Skipped (file already missing): {new_path}")
            failed.append(entry)
            continue
        if original_path.exists():
            print(f"Skipped (would overwrite existing file): {original_path}")
            failed.append(entry)
            continue
        original_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(new_path), str(original_path))
        print(f"Restored: {new_path.name} -> {original_path}")
    return failed


def main():
    parser = argparse.ArgumentParser(description="Undo Smart File Organizer movements")
    parser.add_argument("--run", help="Undo a specific run_id")
    parser.add_argument("--all", action="store_true", help="Undo every recorded movement")
    args = parser.parse_args()

    history = load_history()
    if not history:
        print("Movement history is empty. Nothing to undo.")
        return

    if args.all:
        to_undo = history
        remaining = []
    elif args.run:
        to_undo = [e for e in history if e["run_id"] == args.run]
        remaining = [e for e in history if e["run_id"] != args.run]
        if not to_undo:
            print(f"No entries found for run_id: {args.run}")
            return
    else:
        latest_run = history[-1]["run_id"]
        to_undo = [e for e in history if e["run_id"] == latest_run]
        remaining = [e for e in history if e["run_id"] != latest_run]

    print(f"Undoing {len(to_undo)} movement(s)...")
    failed = undo_entries(to_undo)

    # Keep failed entries in history in case the file was moved by hand later;
    # drop the ones that were successfully restored.
    save_history(remaining + failed)
    print("\nDone.")


if __name__ == "__main__":
    main()
