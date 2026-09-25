"""
Smart File Organizer
---------------------
Automatically sorts files in a target folder into category subfolders
(Images, Documents, Videos, etc.) based on rules defined in config.json.

Every move is logged to logs/movements.json, so it can be reversed
later with undo.py.

Usage:
    python organizer.py <folder_path>
    python organizer.py <folder_path> --dry-run
    python organizer.py <folder_path> --config custom_config.json
"""

import os
import sys
import json
import shutil
import logging
import argparse
from pathlib import Path
from datetime import datetime


LOG_DIR = Path("logs")
MOVEMENTS_FILE = LOG_DIR / "movements.json"
LOG_FILE = LOG_DIR / "organizer.log"


def setup_logging():
    LOG_DIR.mkdir(exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(message)s",
        handlers=[
            logging.FileHandler(LOG_FILE, encoding="utf-8"),
            logging.StreamHandler(sys.stdout),
        ],
    )


def load_config(config_path: str) -> dict:
    path = Path(config_path)
    if not path.exists():
        logging.error(f"Config file not found: {config_path}")
        sys.exit(1)
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def build_extension_map(config: dict) -> dict:
    """Flatten {category: [ext, ext, ...]} into {ext: category} for fast lookup."""
    ext_map = {}
    for category, extensions in config.get("categories", {}).items():
        for ext in extensions:
            ext_map[ext.lower()] = category
    return ext_map


def get_category(filename: str, ext_map: dict, fallback: str) -> str:
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    return ext_map.get(ext, fallback)


def unique_destination(dest: Path) -> Path:
    """If dest already exists, append a counter: file.txt -> file(1).txt"""
    if not dest.exists():
        return dest
    stem, suffix = dest.stem, dest.suffix
    counter = 1
    new_dest = dest.with_name(f"{stem}({counter}){suffix}")
    while new_dest.exists():
        counter += 1
        new_dest = dest.with_name(f"{stem}({counter}){suffix}")
    return new_dest


def record_movement(entry: dict):
    MOVEMENTS_FILE.parent.mkdir(exist_ok=True)
    history = []
    if MOVEMENTS_FILE.exists():
        with open(MOVEMENTS_FILE, "r", encoding="utf-8") as f:
            try:
                history = json.load(f)
            except json.JSONDecodeError:
                history = []
    history.append(entry)
    with open(MOVEMENTS_FILE, "w", encoding="utf-8") as f:
        json.dump(history, f, indent=2)


def organize(folder: str, config: dict, dry_run: bool = False):
    target = Path(folder).expanduser().resolve()
    if not target.is_dir():
        logging.error(f"'{folder}' is not a valid directory.")
        sys.exit(1)

    ext_map = build_extension_map(config)
    fallback = config.get("fallback_category", "Others")
    ignore_files = set(config.get("ignore_files", []))

    run_id = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    summary = {}

    files = [f for f in target.iterdir() if f.is_file() and f.name not in ignore_files]

    if not files:
        logging.info("No files to organize. Folder is already clean.")
        return

    logging.info(f"Scanning '{target}' -- {len(files)} file(s) found.")

    for file_path in files:
        category = get_category(file_path.name, ext_map, fallback)
        dest_folder = target / category
        dest_path = unique_destination(dest_folder / file_path.name)

        if dry_run:
            logging.info(f"[DRY RUN] Would move: {file_path.name} -> {category}/")
        else:
            dest_folder.mkdir(exist_ok=True)
            shutil.move(str(file_path), str(dest_path))
            logging.info(f"Moved: {file_path.name} -> {category}/{dest_path.name}")
            record_movement({
                "run_id": run_id,
                "timestamp": datetime.now().isoformat(),
                "original_path": str(file_path),
                "new_path": str(dest_path),
            })

        summary[category] = summary.get(category, 0) + 1

    print("\n--- Summary ---")
    for category, count in sorted(summary.items()):
        print(f"{category}: {count} file(s)")
    if dry_run:
        print("\n(dry run -- no files were actually moved)")
    else:
        print(f"\nRun ID: {run_id}  (use this with undo.py to reverse this run)")


def main():
    parser = argparse.ArgumentParser(description="Smart File Organizer")
    parser.add_argument("folder", help="Path to the folder you want to organize")
    parser.add_argument("--config", default="config.json", help="Path to config file")
    parser.add_argument("--dry-run", action="store_true", help="Preview changes without moving files")
    args = parser.parse_args()

    setup_logging()
    config = load_config(args.config)
    organize(args.folder, config, dry_run=args.dry_run)


if __name__ == "__main__":
    main()
