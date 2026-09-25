# Smart File Organizer

A command-line tool that automatically sorts files in a folder into
category subfolders (Images, Documents, Videos, Code, etc.) based on
rules defined in `config.json`. Every move is logged, so any run can
be safely reversed with `undo.py`.

Built as a practical automation project — the kind of "save X hours a
week" script that's the entry point into business process automation.

## Features

- **Config-driven** — add/remove categories or extensions in `config.json`, no code changes needed
- **Dry-run mode** — preview exactly what would happen before touching any files
- **Collision-safe** — never overwrites a file; auto-renames duplicates (`report.pdf` -> `report(1).pdf`)
- **Full undo** — every move is logged to `logs/movements.json` and can be reversed, and undo itself refuses to overwrite a file that's back in place
- **Logging** — every run is recorded to `logs/organizer.log`, both on screen and in the file

## Project structure

```
smart-file-organizer/
├── organizer.py     # main script — scans and sorts a folder
├── undo.py           # reverses movements recorded by organizer.py
├── config.json        # defines categories and file extension rules
├── README.md
└── logs/              # created automatically on first run
    ├── organizer.log
    └── movements.json
```

## Setup

No external libraries — everything used is Python's standard library.
Requires Python 3.8+.

```bash
git clone <your-repo-url>
cd smart-file-organizer
```

## Usage

**1. Preview first (recommended)**

```bash
python organizer.py /path/to/messy/folder --dry-run
```

**2. Run it for real**

```bash
python organizer.py /path/to/messy/folder
```

**3. Made a mistake? Undo it**

```bash
python undo.py              # undo the most recent run
python undo.py --run <id>   # undo one specific run (shown after each run)
python undo.py --all        # undo everything ever recorded
```

## Customizing rules

Edit `config.json`. Example — add a "Design" category:

```json
"Design": ["psd", "ai", "xd", "fig"]
```

Any extension not listed falls back to the `Others` folder
(configurable via `fallback_category`).

## Known limitations / what I'd add next

- Currently sorts one folder level only (not recursive into subfolders) — intentional, to avoid re-sorting an already-organized structure
- Could add a `--schedule` mode using `schedule` or a cron job for fully hands-off automation
- Could add file-size or date-based rules (e.g. archive anything older than 6 months)

## Why I built this

Manually organizing client files, downloads, and exports is a small
but constant time sink — exactly the kind of repetitive task that's
worth automating first. This was built as the first proof-of-work
project in a self-directed AI/automation learning path (Python →
SQL/Data Analysis → ML → Deep Learning → Generative & Agentic AI).
