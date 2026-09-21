"""
Bibliography Search - Alessandra Bagnato

A small Tkinter desktop app to search the bagnato_bibliography.json file
using 1 to 5 keywords. An entry is only shown if ALL the keywords the user
filled in are found somewhere in it (title, authors or venue) - keywords
are combined with AND, not OR.

Usage:
    python bibliography_search.py

The script expects "bagnato_bibliography.json" to sit in the same folder.
If it is not found there, a file picker lets you choose it manually.
"""

import json
import os
import sys
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

NUM_KEYWORD_FIELDS = 5
JSON_FILENAME = "bagnato_bibliography.json"


def load_bibliography():
    """Load the bibliography JSON, asking the user for the file if needed."""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    default_path = os.path.join(script_dir, JSON_FILENAME)

    path = default_path
    if not os.path.isfile(path):
        messagebox.showinfo(
            "Bibliography file not found",
            f'"{JSON_FILENAME}" was not found next to this script.\n'
            "Please select the JSON file manually.",
        )
        path = filedialog.askopenfilename(
            title="Select bagnato_bibliography.json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
        )
        if not path:
            return None

    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, json.JSONDecodeError) as exc:
        messagebox.showerror("Error loading file", f"Could not read {path}:\n{exc}")
        return None

    return data


class BibliographySearchApp:
    def __init__(self, root, entries):
        self.root = root
        self.entries = entries or []

        root.title("Bagnato Bibliography Search")
        root.geometry("820x600")
        root.minsize(600, 400)

        self.keyword_vars = [tk.StringVar() for _ in range(NUM_KEYWORD_FIELDS)]

        self._build_widgets()

    # ------------------------------------------------------------------ UI
    def _build_widgets(self):
        outer = ttk.Frame(self.root, padding=12)
        outer.pack(fill="both", expand=True)
        outer.rowconfigure(2, weight=1)
        outer.columnconfigure(0, weight=1)

        # --- Keyword input area -------------------------------------------------
        input_frame = ttk.LabelFrame(outer, text="Keywords (1 to 5, all must match)")
        input_frame.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        for i in range(NUM_KEYWORD_FIELDS):
            input_frame.columnconfigure(i, weight=1)
            col = ttk.Frame(input_frame)
            col.grid(row=0, column=i, padx=6, pady=8, sticky="ew")
            ttk.Label(col, text=f"Keyword {i + 1}").pack(anchor="w")
            entry = ttk.Entry(col, textvariable=self.keyword_vars[i])
            entry.pack(fill="x")
            entry.bind("<Return>", lambda event: self.run_search())

        # --- Search button and status -------------------------------------------------
        action_frame = ttk.Frame(outer)
        action_frame.grid(row=1, column=0, sticky="ew", pady=(0, 10))

        self.search_button = ttk.Button(
            action_frame, text="Search", command=self.run_search
        )
        self.search_button.pack(side="left")

        clear_button = ttk.Button(action_frame, text="Clear", command=self.clear_all)
        clear_button.pack(side="left", padx=(8, 0))

        self.status_var = tk.StringVar(value=f"{len(self.entries)} entries loaded.")
        ttk.Label(action_frame, textvariable=self.status_var).pack(
            side="left", padx=16
        )

        # --- Results panel (scrollable, copyable) -------------------------------------------------
        results_frame = ttk.LabelFrame(outer, text="Results")
        results_frame.grid(row=2, column=0, sticky="nsew")
        results_frame.rowconfigure(0, weight=1)
        results_frame.columnconfigure(0, weight=1)

        self.results_text = tk.Text(
            results_frame,
            wrap="word",
            font=("TkDefaultFont", 10),
            undo=False,
        )
        self.results_text.grid(row=0, column=0, sticky="nsew")

        scrollbar = ttk.Scrollbar(
            results_frame, orient="vertical", command=self.results_text.yview
        )
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.results_text.configure(yscrollcommand=scrollbar.set)

        # Text stays editable so the user can select and copy (Ctrl+C) freely.
        self._set_results("Enter one or more keywords above, then click Search.")

    # --------------------------------------------------------------- helpers
    def _set_results(self, text):
        self.results_text.delete("1.0", "end")
        self.results_text.insert("1.0", text)

    def clear_all(self):
        for var in self.keyword_vars:
            var.set("")
        self._set_results("Enter one or more keywords above, then click Search.")
        self.status_var.set(f"{len(self.entries)} entries loaded.")

    @staticmethod
    def _searchable_text(entry):
        """Concatenate the fields we search into a single lowercase string."""
        parts = [
            entry.get("title", ""),
            entry.get("authors", ""),
            entry.get("venue", ""),
        ]
        return " ".join(parts).lower()

    # ---------------------------------------------------------------- search
    def run_search(self):
        keywords = [v.get().strip().lower() for v in self.keyword_vars]
        keywords = [k for k in keywords if k]  # drop empty fields

        if not keywords:
            messagebox.showwarning(
                "No keyword", "Please enter at least one keyword before searching."
            )
            return

        matches = []
        for entry in self.entries:
            haystack = self._searchable_text(entry)
            if all(keyword in haystack for keyword in keywords):
                matches.append(entry)

        self._show_results(matches, keywords)

    def _show_results(self, matches, keywords):
        self.results_text.delete("1.0", "end")

        header = f'{len(matches)} result(s) for: {", ".join(keywords)}\n'
        header += "=" * len(header.rstrip("\n")) + "\n\n"
        self.results_text.insert("end", header)

        if not matches:
            self.results_text.insert("end", "No matching entries found.\n")
        else:
            for entry in matches:
                block = (
                    f"[{entry.get('id', '?')}] ({entry.get('year', '?')})\n"
                    f"{entry.get('authors', '')}\n"
                    f"{entry.get('title', '')}\n"
                    f"{entry.get('venue', '')}\n"
                    f"{entry.get('linkLabel', 'Link')}: {entry.get('link', '')}\n"
                    f"{'-' * 70}\n\n"
                )
                self.results_text.insert("end", block)

        self.status_var.set(f"{len(matches)} result(s) out of {len(self.entries)} entries.")


def main():
    root = tk.Tk()
    # Load the data first so a failed load can exit cleanly before the
    # main window is fully built.
    entries = load_bibliography()
    if entries is None:
        root.destroy()
        sys.exit(1)

    app = BibliographySearchApp(root, entries)
    root.mainloop()


if __name__ == "__main__":
    main()
