"""
Smart File Organizer — GUI
----------------------------
A simple point-and-click interface for organizer.py, so someone with
no coding or terminal experience can use it: pick a folder, click a
button, done.

Run with:
    python3 gui.py

See README.md for packaging this into a double-clickable app for
Mac (.app) and Windows (.exe).
"""

import os
import sys
import threading
import logging
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from organizer import load_config, organize
from undo import load_history, save_history, undo_entries


def resource_path(relative_path: str) -> str:
    """
    Resolve a bundled file's path whether running from source or from a
    PyInstaller-packaged app. PyInstaller extracts bundled data files
    (like config.json) into a temp folder referenced by sys._MEIPASS.
    """
    base_path = getattr(sys, "_MEIPASS", os.path.abspath("."))
    return os.path.join(base_path, relative_path)


class TextHandler(logging.Handler):
    """Routes Python logging output into a Tkinter Text widget instead of the console."""

    def __init__(self, text_widget):
        super().__init__()
        self.text_widget = text_widget

    def emit(self, record):
        msg = self.format(record)

        def append():
            self.text_widget.configure(state="normal")
            self.text_widget.insert(tk.END, msg + "\n")
            self.text_widget.see(tk.END)
            self.text_widget.configure(state="disabled")

        self.text_widget.after(0, append)


def configure_styles():
    """
    Uses the 'clam' theme instead of each OS's native theme.

    Why: on macOS, the native 'aqua' Tk theme ignores custom background/
    foreground colors on buttons (especially while pressed), which is
    why button text can disappear on click. 'clam' is a theme Tk renders
    itself rather than handing off to the OS, so colors stay consistent
    and readable on both macOS and Windows.
    """
    style = ttk.Style()
    style.theme_use("clam")

    style.configure(
        "Primary.TButton",
        background="#2e7d32",
        foreground="white",
        padding=(14, 10),
        font=("Helvetica", 11, "bold"),
        borderwidth=0,
    )
    style.map(
        "Primary.TButton",
        background=[("active", "#276a2b"), ("pressed", "#1b4d20"), ("disabled", "#9e9e9e")],
        foreground=[("disabled", "#e0e0e0")],
    )

    style.configure(
        "Danger.TButton",
        background="#c62828",
        foreground="white",
        padding=(14, 10),
        font=("Helvetica", 11, "bold"),
        borderwidth=0,
    )
    style.map(
        "Danger.TButton",
        background=[("active", "#a82121"), ("pressed", "#7a1818"), ("disabled", "#9e9e9e")],
        foreground=[("disabled", "#e0e0e0")],
    )

    style.configure(
        "Secondary.TButton",
        background="#37474f",
        foreground="white",
        padding=(12, 8),
        font=("Helvetica", 10),
        borderwidth=0,
    )
    style.map(
        "Secondary.TButton",
        background=[("active", "#2c383e"), ("pressed", "#1e2529")],
    )

    style.configure("Section.TLabelframe", background="#f5f5f5", padding=12)
    style.configure("Section.TLabelframe.Label", font=("Helvetica", 10, "bold"), background="#f5f5f5")
    style.configure("Body.TFrame", background="#f5f5f5")
    style.configure("Body.TLabel", background="#f5f5f5")

    return style


class OrganizerApp:
    def __init__(self, root):
        self.root = root
        self.selected_folder = None

        root.title("Smart File Organizer")
        root.geometry("600x560")
        root.minsize(560, 520)
        root.configure(bg="#f5f5f5")

        configure_styles()

        header = ttk.Frame(root, style="Body.TFrame")
        header.pack(fill="x", padx=20, pady=(18, 4))
        ttk.Label(header, text="Smart File Organizer", font=("Helvetica", 18, "bold"), style="Body.TLabel").pack(
            anchor="w"
        )
        ttk.Label(
            header,
            text="Sorts a folder's files into Images, Documents, Videos, and more.",
            foreground="#616161",
            style="Body.TLabel",
        ).pack(anchor="w", pady=(2, 0))

        # --- Step 1: Folder ---
        folder_section = ttk.Labelframe(root, text="1.  Choose a folder", style="Section.TLabelframe")
        folder_section.pack(fill="x", padx=20, pady=10)

        self.folder_label_var = tk.StringVar(value="No folder selected")
        ttk.Button(folder_section, text="Browse...", style="Secondary.TButton", command=self.choose_folder).pack(
            side="left"
        )
        ttk.Label(
            folder_section, textvariable=self.folder_label_var, wraplength=380, style="Body.TLabel"
        ).pack(side="left", padx=12)

        # --- Step 2: Options ---
        options_section = ttk.Labelframe(root, text="2.  Options", style="Section.TLabelframe")
        options_section.pack(fill="x", padx=20, pady=10)

        self.dry_run_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            options_section,
            text="Dry run — preview only, don't move any files yet",
            variable=self.dry_run_var,
        ).pack(anchor="w")

        # --- Step 3: Actions ---
        actions_section = ttk.Labelframe(root, text="3.  Run it", style="Section.TLabelframe")
        actions_section.pack(fill="x", padx=20, pady=10)

        self.organize_btn = ttk.Button(
            actions_section, text="Organize Files", style="Primary.TButton", command=self.run_organize
        )
        self.organize_btn.pack(side="left", padx=(0, 10))

        self.undo_btn = ttk.Button(
            actions_section, text="Undo Last Run", style="Danger.TButton", command=self.run_undo
        )
        self.undo_btn.pack(side="left")

        # --- Log ---
        log_section = ttk.Labelframe(root, text="Activity log", style="Section.TLabelframe")
        log_section.pack(fill="both", expand=True, padx=20, pady=(10, 18))

        log_frame = ttk.Frame(log_section)
        log_frame.pack(fill="both", expand=True)

        self.log_box = tk.Text(
            log_frame,
            state="disabled",
            bg="#1e1e1e",
            fg="#4caf50",
            insertbackground="white",
            font=("Menlo", 10),
            wrap="word",
            relief="flat",
            padx=8,
            pady=8,
        )
        scrollbar = ttk.Scrollbar(log_frame, command=self.log_box.yview)
        self.log_box.configure(yscrollcommand=scrollbar.set)
        self.log_box.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        handler = TextHandler(self.log_box)
        handler.setFormatter(logging.Formatter("%(asctime)s | %(message)s", "%H:%M:%S"))
        root_logger = logging.getLogger()
        root_logger.addHandler(handler)
        root_logger.setLevel(logging.INFO)

    def choose_folder(self):
        folder = filedialog.askdirectory(title="Select a folder to organize")
        if folder:
            self.selected_folder = folder
            self.folder_label_var.set(folder)

    def set_buttons_enabled(self, enabled: bool):
        state = "!disabled" if enabled else "disabled"
        self.organize_btn.state([state])
        self.undo_btn.state([state])

    def run_organize(self):
        if not self.selected_folder:
            messagebox.showwarning("No folder selected", "Please choose a folder first.")
            return

        config = load_config(resource_path("config.json"))
        dry_run = self.dry_run_var.get()
        self.set_buttons_enabled(False)

        def task():
            try:
                summary = organize(self.selected_folder, config, dry_run=dry_run) or {}
                title = "Preview complete" if dry_run else "Organizing complete"
                lines = "\n".join(f"{cat}: {count}" for cat, count in sorted(summary.items()))
                body = lines if lines else "No files needed organizing."
                self.root.after(0, lambda: messagebox.showinfo(title, body))
            except Exception as e:
                self.root.after(0, lambda: messagebox.showerror("Error", str(e)))
            finally:
                self.root.after(0, lambda: self.set_buttons_enabled(True))

        threading.Thread(target=task, daemon=True).start()

    def run_undo(self):
        history = load_history()
        if not history:
            messagebox.showinfo("Nothing to undo", "No recorded movements found.")
            return

        latest_run = history[-1]["run_id"]
        to_undo = [e for e in history if e["run_id"] == latest_run]
        remaining = [e for e in history if e["run_id"] != latest_run]
        self.set_buttons_enabled(False)

        def task():
            try:
                failed = undo_entries(to_undo)
                save_history(remaining + failed)
                restored = len(to_undo) - len(failed)
                self.root.after(0, lambda: messagebox.showinfo("Undo complete", f"Restored {restored} file(s)."))
            except Exception as e:
                self.root.after(0, lambda: messagebox.showerror("Error", str(e)))
            finally:
                self.root.after(0, lambda: self.set_buttons_enabled(True))

        threading.Thread(target=task, daemon=True).start()


if __name__ == "__main__":
    root = tk.Tk()
    app = OrganizerApp(root)
    root.mainloop()