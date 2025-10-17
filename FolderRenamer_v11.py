#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FolderFileRenamer_GUI.py — v9
- Progress bar + current folder monitor for large directories
- Multi base folders (add/paste/multi-select)
- Targets: Folders / Files
- Depth: Level 1 / Level 2 / Up to Level 2 / All levels
- Transform: '-'->'_', optional ' '->'_', remove accents, UPPERCASE
- Themes: PharmApp Light (default), Nord Light, Midnight Teal (Dark), Solar Slate, macOS Graphite (Dark)
- Collision: Suffix _1 (safe) OR Merge & de-duplicate (SHA-256)
- Preview / Rename (with progress) / Undo (rename/move only) / Save CSV

Notes:
- In Merge mode:
  * File vs file: same SHA-256 -> delete source duplicate; different -> keep both via suffix.
  * Dir vs dir: recursively merge, de-dup by hash; source dir removed if empty.
- Undo reverts rename/move from this session; deletions by de-duplication are not undoable.
"""

import csv
import unicodedata
import hashlib
import threading
from pathlib import Path
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

# --------- Script name banner ----------
try:
    SCRIPT_NAME = Path(__file__).name
except NameError:
    SCRIPT_NAME = "FolderFileRenamer_GUI.py"
print(f"[INFO] Running: {SCRIPT_NAME}")

# --------- Theme Manager ----------
class ThemeManager:
    THEMES = {
        "PharmApp Light": {
            "bg": "#fdf5e6", "fg": "#2a2a2a",
            "button_bg": "#f4a261", "button_active": "#e76f51", "button_fg": "#000000",
            "accent": "#e9c46a", "heading_bg": "#b5838d",
            "selection_bg": "#e9c46a", "input_bg": "#ffffff", "input_fg": "#2a2a2a",
            "row_alt": "#fff9f0", "table_bg": "#FFFFFF"
        },
        "Nord Light": {
            "bg": "#ECEFF4", "fg": "#2E3440",
            "button_bg": "#81A1C1", "button_active": "#5E81AC", "button_fg": "#FFFFFF",
            "accent": "#88C0D0", "heading_bg": "#5E81AC",
            "selection_bg": "#D8DEE9", "input_bg": "#FFFFFF", "input_fg": "#2E3440",
            "row_alt": "#F5F7FA", "table_bg": "#FFFFFF"
        },
        "Midnight Teal (Dark)": {
            "bg": "#0f172a", "fg": "#e2e8f0",
            "button_bg": "#0ea5e9", "button_active": "#0284c7", "button_fg": "#FFFFFF",
            "accent": "#14b8a6", "heading_bg": "#0ea5e9",
            "selection_bg": "#334155", "input_bg": "#111827", "input_fg": "#e5e7eb",
            "row_alt": "#0b1224", "table_bg": "#0b1224"
        },
        "Solar Slate": {
            "bg": "#f6f7f9", "fg": "#1f2937",
            "button_bg": "#f59e0b", "button_active": "#d97706", "button_fg": "#000000",
            "accent": "#fbbf24", "heading_bg": "#374151",
            "selection_bg": "#e5e7eb", "input_bg": "#ffffff", "input_fg": "#1f2937",
            "row_alt": "#f3f4f6", "table_bg": "#FFFFFF"
        },
        "macOS Graphite (Dark)": {
            "bg": "#1C1C1E", "fg": "#F2F2F7",
            "button_bg": "#0A84FF", "button_active": "#0060DF", "button_fg": "#FFFFFF",
            "accent": "#2C2C2E", "heading_bg": "#0A84FF",
            "selection_bg": "#2C2C2E", "input_bg": "#2C2C2E", "input_fg": "#F2F2F7",
            "row_alt": "#1F1F21", "table_bg": "#1F1F21"
        },
    }

    def __init__(self, root: tk.Tk):
        self.root = root
        self.style = ttk.Style(root)
        try:
            self.style.theme_use("default")
        except tk.TclError:
            pass

    def apply(self, theme_name: str):
        pal = self.THEMES.get(theme_name, self.THEMES["PharmApp Light"])
        bg, fg = pal["bg"], pal["fg"]
        head_bg = pal["heading_bg"]
        btn_bg = pal["button_bg"]
        btn_active = pal["button_active"]
        btn_fg = pal.get("button_fg", "#000000")
        sel_bg = pal["selection_bg"]
        input_bg, input_fg = pal["input_bg"], pal["input_fg"]
        table_bg = pal.get("table_bg", "#FFFFFF")

        self.root.configure(bg=bg)
        self.root.option_add("*Foreground", fg)
        self.root.option_add("*Background", bg)

        self.style.configure("TFrame", background=bg)
        self.style.configure("TLabelframe", background=bg, foreground=fg, font=("Arial", 11, "bold"))
        self.style.configure("TLabelframe.Label", background=bg, foreground=fg)
        self.style.configure("TLabel", background=bg, foreground=fg, font=("Arial", 11))
        self.style.configure("Pharm.TButton", font=("Arial", 10, "bold"), padding=6)
        self.style.map("Pharm.TButton",
                       background=[("active", btn_active), ("pressed", btn_active)],
                       foreground=[("disabled", "#888888")])
        self.style.configure("Pharm.TButton", background=btn_bg, foreground=btn_fg)

        self.style.configure("TEntry", fieldbackground=input_bg, foreground=input_fg, padding=4)
        self.style.configure("TCombobox", fieldbackground=input_bg, foreground=input_fg, padding=2)
        self.style.configure("TCheckbutton", background=bg, foreground=fg)
        self.style.configure("TRadiobutton", background=bg, foreground=fg)

        self.style.configure("Treeview",
                             background=table_bg,
                             fieldbackground=table_bg,
                             foreground=fg,
                             rowheight=24,
                             font=("Arial", 10))
        self.style.configure("Treeview.Heading",
                             font=("Arial", 10, "bold"),
                             foreground="#FFFFFF",
                             background=head_bg)
        self.style.map("Treeview.Heading",
                       background=[("active", head_bg), ("pressed", head_bg)])
        self.style.configure("TSeparator", background=pal["accent"])
        return pal

# --------- Helpers ----------
def remove_vietnamese_diacritics(s: str) -> str:
    s = s.replace("đ", "d").replace("Đ", "D")
    nfkd = unicodedata.normalize("NFD", s)
    return "".join(ch for ch in nfkd if not unicodedata.combining(ch))

def transform_name(name: str, replace_space: bool) -> str:
    s = name.replace("-", "_")
    if replace_space:
        s = s.replace(" ", "_")
    s = remove_vietnamese_diacritics(s)
    s = s.upper()
    return s

def unique_target_path(target: Path) -> Path:
    if not target.exists():
        return target
    stem = target.name
    base = target.parent
    i = 1
    while True:
        candidate = base / f"{stem}_{i}"
        if not candidate.exists():
            return candidate
        i += 1

def file_sha256(p: Path, chunk: int = 1 << 20) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        while True:
            b = f.read(chunk)
            if not b:
                break
            h.update(b)
    return h.hexdigest()

# --------- Depth options ----------
DEPTH_LEVEL1_ONLY = "LEVEL1_ONLY"
DEPTH_LEVEL2_ONLY = "LEVEL2_ONLY"
DEPTH_UP_TO_LEVEL2 = "UP_TO_LEVEL2"
DEPTH_ALL = "ALL"

DEPTH_LABEL_TO_CONST = {
    "Level 1 only": DEPTH_LEVEL1_ONLY,
    "Level 2 only": DEPTH_LEVEL2_ONLY,
    "Up to Level 2": DEPTH_UP_TO_LEVEL2,
    "All levels": DEPTH_ALL,
}
DEPTH_CONST_TO_LABEL = {v: k for k, v in DEPTH_LABEL_TO_CONST.items()}

def _rel_depth(base: Path, p: Path) -> int:
    return len(p.relative_to(base).parts)

def _kind_of(p: Path) -> str:
    if p.is_dir():
        return "DIR"
    if p.is_file():
        return "FILE"
    return "OTHER"

# --------- Collision modes ----------
COL_SUFFIX = "SUFFIX"
COL_MERGE_HASH = "MERGE_HASH"

def merge_dirs(src: Path, dst: Path) -> dict:
    stats = {"moved": 0, "deleted_dups": 0, "conflicts": 0}
    if not dst.exists():
        src.rename(dst)
        stats["moved"] += 1
        return stats
    for child in list(src.iterdir()):
        t = dst / child.name
        if child.is_dir():
            if t.exists() and t.is_dir():
                sub = merge_dirs(child, t)
                for k in stats:
                    stats[k] += sub.get(k, 0)
            elif not t.exists():
                child.rename(t)
                stats["moved"] += 1
            else:
                t_unique = unique_target_path(t)
                child.rename(t_unique)
                stats["conflicts"] += 1
        else:
            if t.exists() and t.is_file():
                try:
                    if file_sha256(child) == file_sha256(t):
                        child.unlink()
                        stats["deleted_dups"] += 1
                    else:
                        t_unique = unique_target_path(t)
                        child.rename(t_unique)
                        stats["conflicts"] += 1
                except Exception:
                    t_unique = unique_target_path(t)
                    child.rename(t_unique)
                    stats["conflicts"] += 1
            elif not t.exists():
                child.rename(t)
                stats["moved"] += 1
            else:
                t_unique = unique_target_path(t)
                child.rename(t_unique)
                stats["conflicts"] += 1
    try:
        src.rmdir()
    except Exception:
        pass
    return stats

# --------- GUI ----------
class App(ttk.Frame):
    def __init__(self, master):
        super().__init__(master)
        self.master.title("Folder/File Renamer — Compact Toolbar (PharmApp)")
        self.pack(fill="both", expand=True)

        try:
            self.master.rowconfigure(0, weight=1)
            self.master.columnconfigure(0, weight=1)
        except Exception:
            pass

        # State
        self.current_theme = tk.StringVar(value="PharmApp Light")  # default
        self.include_dirs = tk.BooleanVar(value=True)
        self.include_files = tk.BooleanVar(value=False)
        self.replace_space = tk.BooleanVar(value=True)
        self.depth_label = tk.StringVar(value="All levels")

        self.collision_label = tk.StringVar(value="Suffix _1")
        self.collision_mode = COL_SUFFIX

        self.single_path_var = tk.StringVar()
        self.base_dirs: list[Path] = []

        self.preview_rows: list[tuple[Path, Path, Path]] = []
        self.applied_rows: list[tuple[Path, Path, Path, Path]] = []
        self.applied_info_rows: list[tuple[Path, str, str, str, str]] = []

        # Progress state
        self._busy = False
        self.progress_var = tk.DoubleVar(value=0.0)
        self.progress_total = 100.0
        self.progress_mode = tk.StringVar(value="")  # "indeterminate"/"determinate"
        self.progress_msg = tk.StringVar(value="Idle")
        self.current_folder_var = tk.StringVar(value="-")
        self.counter_msg = tk.StringVar(value="0/0")

        # Theme manager
        self.tm = ThemeManager(master)
        self.palette = self.tm.apply(self.current_theme.get())

        self._build_ui()
        self._setup_tree_tags()
        self._apply_palette_to_text_and_listbox()



    # Trong class App, sau các hàm UI utils:
    def _on_collision_mode_change(self, event=None):
        """Update collision mode from the combobox label."""
        label = (self.collision_label.get() or "").lower()
        if "merge" in label:
            self.collision_mode = COL_MERGE_HASH
            note = "Collision: MERGE & de-dup (SHA-256)"
        else:
            self.collision_mode = COL_SUFFIX
            note = "Collision: add suffix _1"
        try:
            # Cập nhật footer cho dễ thấy trạng thái
            self.status_lbl.config(text=f"Script: {SCRIPT_NAME} • Theme: {self.current_theme.get()} • {note}")
        except Exception:
            pass

    # ---------- UI ----------
    def _build_ui(self):
        # Row 0: TOP BAR
        top = ttk.Frame(self); top.pack(fill="x", padx=10, pady=6)

        ttk.Label(top, text="Theme:").grid(row=0, column=0, sticky="e")
        self.theme_cbb = ttk.Combobox(top, state="readonly",
                                      values=list(ThemeManager.THEMES.keys()),
                                      textvariable=self.current_theme, width=24)
        self.theme_cbb.grid(row=0, column=1, sticky="w", padx=(6,6))
        self.btn_apply_theme = ttk.Button(top, text="Apply", style="Pharm.TButton", command=self._apply_theme)
        self.btn_apply_theme.grid(row=0, column=2, sticky="w")

        tgt = ttk.Frame(top); tgt.grid(row=0, column=3, sticky="w", padx=(16, 0))
        ttk.Checkbutton(tgt, text="Folders", variable=self.include_dirs).pack(side="left")
        ttk.Checkbutton(tgt, text="Files", variable=self.include_files).pack(side="left", padx=(8,0))

        ttk.Label(top, text="Depth:").grid(row=0, column=4, sticky="e", padx=(16,0))
        self.depth_cbb = ttk.Combobox(top, state="readonly",
                                      values=list(DEPTH_LABEL_TO_CONST.keys()),
                                      textvariable=self.depth_label, width=16)
        self.depth_cbb.grid(row=0, column=5, sticky="w", padx=(6,6))

        ttk.Checkbutton(top, text="Space → '_'",
                        variable=self.replace_space).grid(row=0, column=6, sticky="w", padx=(12,0))

        ttk.Label(top, text="Collision:").grid(row=0, column=7, sticky="e", padx=(16,0))
        self.collision_cbb = ttk.Combobox(top, state="readonly",
                                          values=["Suffix _1", "Merge & de-duplicate (hash)"],
                                          textvariable=self.collision_label, width=24)
        self.collision_cbb.grid(row=0, column=8, sticky="w", padx=(6,6))
        self.collision_cbb.bind("<<ComboboxSelected>>", self._on_collision_mode_change)
        top.grid_columnconfigure(9, weight=1)

        # Row 1: BASE TOOLBAR
        bar = ttk.Frame(self); bar.pack(fill="x", padx=10, pady=(0,6))
        ttk.Label(bar, text="Path:").pack(side="left")
        self.single_entry = ttk.Entry(bar, textvariable=self.single_path_var, width=60)
        self.single_entry.pack(side="left", padx=(6,6))
        self.btn_add_path = ttk.Button(bar, text="Add Path", style="Pharm.TButton", command=self._add_path_from_entry)
        self.btn_add_path.pack(side="left", padx=(0,6))
        self.btn_add_win = ttk.Button(bar, text="Add Windows…", style="Pharm.TButton", command=self._add_folder_dialog)
        self.btn_add_win.pack(side="left", padx=(0,6))
        self.btn_add_multi = ttk.Button(bar, text="Add Multi…", style="Pharm.TButton", command=self._add_many_dialog)
        self.btn_add_multi.pack(side="left", padx=(0,6))
        self.btn_remove = ttk.Button(bar, text="Remove", style="Pharm.TButton", command=self._remove_selected_bases)
        self.btn_remove.pack(side="left", padx=(0,6))
        self.btn_clear = ttk.Button(bar, text="Clear", style="Pharm.TButton", command=self._clear_bases)
        self.btn_clear.pack(side="left", padx=(0,12))
        self._bulk_visible = False
        self.btn_bulk = ttk.Button(bar, text="Bulk ▸", style="Pharm.TButton", command=self._toggle_bulk_box)
        self.btn_bulk.pack(side="left", padx=(0,18))
        self.btn_preview = ttk.Button(bar, text="Preview", style="Pharm.TButton", command=self._preview)
        self.btn_preview.pack(side="left")
        self.btn_rename = ttk.Button(bar, text="Rename", style="Pharm.TButton", command=self._rename)
        self.btn_rename.pack(side="left", padx=(6,0))
        self.btn_undo = ttk.Button(bar, text="Undo", style="Pharm.TButton", command=self._undo_last)
        self.btn_undo.pack(side="left", padx=(6,0))
        self.btn_savecsv = ttk.Button(bar, text="Save CSV", style="Pharm.TButton", command=self._save_csv)
        self.btn_savecsv.pack(side="left", padx=(6,0))

        # Row 2: BULK PASTE (hidden initially)
        bulk_wrap = ttk.Frame(self); bulk_wrap.pack(fill="x", padx=10)
        self.bulk_frame = bulk_wrap
        ttk.Label(bulk_wrap, text="Bulk Paste (one per line or ';'):").grid(row=0, column=0, sticky="w")
        self.bulk_text = tk.Text(bulk_wrap, height=3, width=80)
        self.bulk_text.grid(row=0, column=1, sticky="we", padx=(6,6))
        ttk.Button(bulk_wrap, text="Add From Box", style="Pharm.TButton", command=self._add_paths_from_text)\
            .grid(row=0, column=2, sticky="w")
        bulk_wrap.grid_columnconfigure(1, weight=1)
        self.bulk_frame.pack_forget()

        # Row 2.5: PROGRESS + CURRENT FOLDER + RUN LOG
        prog = ttk.Frame(self); prog.pack(fill="x", padx=10, pady=(6,2))
        self.progressbar = ttk.Progressbar(prog, orient="horizontal", mode="determinate",
                                           variable=self.progress_var, maximum=100)
        self.progressbar.grid(row=0, column=0, columnspan=3, sticky="we")
        prog.grid_columnconfigure(0, weight=1)
        ttk.Label(prog, textvariable=self.progress_msg).grid(row=1, column=0, sticky="w", pady=(2,0))
        ttk.Label(prog, textvariable=self.counter_msg).grid(row=1, column=1, sticky="e", padx=(6,0))
        ttk.Label(prog, text="Now processing:").grid(row=2, column=0, sticky="w")
        self.lbl_current_folder = ttk.Label(prog, textvariable=self.current_folder_var)
        self.lbl_current_folder.grid(row=2, column=1, columnspan=2, sticky="we")

        run = ttk.Frame(self); run.pack(fill="x", padx=10, pady=(2,6))
        ttk.Label(run, text="Run log (folders):").grid(row=0, column=0, sticky="nw")
        self.run_log = tk.Listbox(run, height=3, selectmode="browse")
        self.run_log.grid(row=0, column=1, sticky="nsew", padx=(6,6))
        run_scroll = ttk.Scrollbar(run, orient="vertical", command=self.run_log.yview)
        run_scroll.grid(row=0, column=2, sticky="ns")
        self.run_log.configure(yscrollcommand=run_scroll.set)
        run.grid_columnconfigure(1, weight=1)

        # Row 3: BASE LIST
        base_frame = ttk.Frame(self); base_frame.pack(fill="x", padx=10, pady=(6,6))
        ttk.Label(base_frame, text="Base Folders:").grid(row=0, column=0, sticky="nw")
        self.base_listbox = tk.Listbox(base_frame, height=4, selectmode="extended")
        self.base_listbox.grid(row=0, column=1, sticky="nsew", padx=(6,6))
        base_scroll = ttk.Scrollbar(base_frame, orient="vertical", command=self.base_listbox.yview)
        base_scroll.grid(row=0, column=2, sticky="ns")
        self.base_listbox.configure(yscrollcommand=base_scroll.set)
        base_frame.grid_columnconfigure(1, weight=1)

        # Row 4: RESULTS TABLE
        table_frame = ttk.Frame(self); table_frame.pack(fill="both", expand=True, padx=10, pady=(6,8))
        cols = ("base", "kind", "current", "new", "status")
        self.tree = ttk.Treeview(table_frame, columns=cols, show="headings", selectmode="browse")
        self.tree.heading("base", text="Base")
        self.tree.heading("kind", text="Kind")
        self.tree.heading("current", text="Current Path")
        self.tree.heading("new", text="New Path (Preview/Actual)")
        self.tree.heading("status", text="Status")
        y_scroll = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        x_scroll = ttk.Scrollbar(table_frame, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=y_scroll.set, xscrollcommand=x_scroll.set)
        self.tree.grid(row=0, column=0, sticky="nsew")
        y_scroll.grid(row=0, column=1, sticky="ns")
        x_scroll.grid(row=1, column=0, sticky="ew")
        table_frame.grid_rowconfigure(0, weight=1)
        table_frame.grid_columnconfigure(0, weight=1)

        # Footer
        foot = ttk.Frame(self); foot.pack(fill="x", padx=10, pady=(0,6))
        self.status_lbl = ttk.Label(foot, text=f"Script: {SCRIPT_NAME} • Theme: {self.current_theme.get()}")
        self.status_lbl.pack(side="left")

    # ---------- Theme / styling ----------
    def _apply_theme(self):
        self.palette = self.tm.apply(self.current_theme.get())
        self._setup_tree_tags()
        self._apply_palette_to_text_and_listbox()
        self.status_lbl.config(text=f"Script: {SCRIPT_NAME} • Theme: {self.current_theme.get()}")

    def _setup_tree_tags(self):
        pal = self.palette
        try:
            self.tree.tag_configure("preview", background=pal["row_alt"])
            self.tree.tag_configure("renamed", background=pal["accent"])
            self.tree.tag_configure("conflict", background=pal["selection_bg"])
            self.tree.tag_configure("undo", background=pal["row_alt"])
            self.tree.tag_configure("info", background=pal["row_alt"])
            self.tree.tag_configure("merge", background=pal["row_alt"])
            self.tree.tag_configure("dupdel", background=pal["row_alt"])
            self.tree.tag_configure("error", background=pal["row_alt"])
        except Exception:
            pass

    def _apply_palette_to_text_and_listbox(self):
        pal = self.palette
        try:
            self.bulk_text.configure(bg=pal["input_bg"], fg=pal["input_fg"], insertbackground=pal["input_fg"])
            self.base_listbox.configure(bg=pal["input_bg"], fg=pal["input_fg"],
                                        selectbackground=pal["selection_bg"])
            self.run_log.configure(bg=pal["input_bg"], fg=pal["input_fg"],
                                   selectbackground=pal["selection_bg"])
        except Exception:
            pass

    # ---------- UI utils ----------
    def _set_busy(self, busy: bool):
        self._busy = busy
        state = ("disabled" if busy else "normal")
        for btn in [self.btn_apply_theme, self.btn_add_path, self.btn_add_win, self.btn_add_multi,
                    self.btn_remove, self.btn_clear, self.btn_bulk, self.btn_preview,
                    self.btn_rename, self.btn_undo, self.btn_savecsv]:
            try:
                btn.config(state=state)
            except Exception:
                pass
        try:
            self.theme_cbb.config(state="disabled" if busy else "readonly")
            self.collision_cbb.config(state="disabled" if busy else "readonly")
            self.depth_cbb.config(state="disabled" if busy else "readonly")
        except Exception:
            pass

    def _progress_start(self, mode: str, msg: str, total: int | None = None):
        def _start():
            self.progress_msg.set(msg)
            self.current_folder_var.set("-")
            if mode == "indeterminate":
                self.progressbar.config(mode="indeterminate", maximum=100)
                self.progress_var.set(0)
                self.counter_msg.set("-")
                self.progressbar.start(12)
            else:
                total = 0 if total is None else total
                self.progressbar.config(mode="determinate", maximum=max(total, 1))
                self.progress_total = max(total, 1)
                self.progress_var.set(0)
                self.counter_msg.set(f"0/{self.progress_total}")
        self.after(0, _start)

    def _progress_update(self, step: int | None = None, msg: str | None = None, current_folder: str | None = None):
        def _upd():
            if msg is not None:
                self.progress_msg.set(msg)
            if current_folder is not None:
                self.current_folder_var.set(current_folder)
                # also log the folder (only when it changes)
                if (not self.run_log.size()) or (self.run_log.get("end") != current_folder):
                    self.run_log.insert("end", current_folder)
                    self.run_log.yview_moveto(1.0)
            if self.progressbar["mode"] == "determinate" and step is not None:
                self.progress_var.set(step)
                self.counter_msg.set(f"{step}/{int(self.progress_total)}")
        self.after(0, _upd)

    def _progress_stop(self, final_msg: str | None = None):
        def _stop():
            if self.progressbar["mode"] == "indeterminate":
                self.progressbar.stop()
            if final_msg:
                self.progress_msg.set(final_msg)
        self.after(0, _stop)

    def _log(self, text: str):
        def _w():
            self.run_log.insert("end", text)
            self.run_log.yview_moveto(1.0)
        self.after(0, _w)

    # ---------- Bulk panel toggle ----------
    def _toggle_bulk_box(self):
        self._bulk_visible = not self._bulk_visible
        if self._bulk_visible:
            self.bulk_frame.pack(fill="x", padx=10, pady=(0,0))
        else:
            self.bulk_frame.pack_forget()

    # ---------- Base folder handlers ----------
    def _normalize_path(self, p: str) -> Path | None:
        p = p.strip().strip('"').strip("'")
        if not p:
            return None
        try:
            path = Path(p).expanduser()
            if path.exists() and path.is_dir():
                return path
        except Exception:
            return None
        return None

    def _refresh_base_listbox(self):
        self.base_listbox.delete(0, "end")
        for p in self.base_dirs:
            self.base_listbox.insert("end", str(p))

    def _add_base(self, path: Path):
        if path and path not in self.base_dirs:
            self.base_dirs.append(path)
            self._refresh_base_listbox()

    def _add_path_from_entry(self):
        p = self._normalize_path(self.single_path_var.get())
        if p:
            self._add_base(p)
            self.single_path_var.set("")
        else:
            messagebox.showwarning("Warning", "Invalid folder path.")

    def _add_paths_from_text(self):
        raw = self.bulk_text.get("1.0", "end")
        parts = []
        for line in raw.splitlines():
            parts += [seg for seg in line.split(";")]
        added = 0
        for seg in parts:
            path = self._normalize_path(seg)
            if path:
                self._add_base(path)
                added += 1
        if added == 0:
            messagebox.showinfo("Info", "No valid folders found in Bulk Paste.")

    def _add_folder_dialog(self):
        d = filedialog.askdirectory(title="Select a folder")
        if d:
            p = self._normalize_path(d)
            if p:
                self._add_base(p)

    def _add_many_dialog(self):
        messagebox.showinfo("Add Many…", "Select folders repeatedly. Press Cancel to stop.")
        while True:
            d = filedialog.askdirectory(title="Select folder (Cancel to finish)")
            if not d:
                break
            p = self._normalize_path(d)
            if p:
                self._add_base(p)

    def _remove_selected_bases(self):
        sel = list(self.base_listbox.curselection())
        if not sel:
            messagebox.showinfo("Remove", "Select one or more folders in the list to remove.")
            return
        for idx in reversed(sel):
            try:
                del self.base_dirs[idx]
            except Exception:
                pass
        self._refresh_base_listbox()

    def _clear_bases(self):
        self.base_dirs.clear()
        self._refresh_base_listbox()

    # ---------- Table ----------
    def _clear_tree(self):
        for iid in self.tree.get_children():
            self.tree.delete(iid)

    # ---------- Depth ----------
    def _depth_mode(self) -> str:
        return DEPTH_LABEL_TO_CONST.get(self.depth_label.get(), DEPTH_ALL)

    # ---------- Preview with progress ----------
    def _preview(self):
        if self._busy:
            return
        if not self.base_dirs:
            messagebox.showwarning("Warning", "Please add at least one base folder.")
            return
        if not self.include_dirs.get() and not self.include_files.get():
            messagebox.showwarning("Warning", "Select at least one target: Folders or Files.")
            return

        self._set_busy(True)
        self._clear_tree()
        self.run_log.delete(0, "end")
        self._progress_start("indeterminate", "Scanning folders…")

        def worker():
            items: list[tuple[Path, Path]] = []
            depth_mode = self._depth_mode()
            include_dirs = self.include_dirs.get()
            include_files = self.include_files.get()

            for base in list(self.base_dirs):
                if not base.exists() or not base.is_dir():
                    continue
                self._progress_update(msg="Scanning…", current_folder=str(base))
                # Walk this base
                for p in base.rglob("*"):
                    try:
                        d = _rel_depth(base, p)
                    except ValueError:
                        continue
                    if d < 1:
                        continue
                    if p.is_dir() and not include_dirs:
                        continue
                    if p.is_file() and not include_files:
                        continue
                    if depth_mode == DEPTH_LEVEL1_ONLY and d != 1:
                        continue
                    if depth_mode == DEPTH_LEVEL2_ONLY and d != 2:
                        continue
                    if depth_mode == DEPTH_UP_TO_LEVEL2 and d not in (1, 2):
                        continue
                    items.append((base, p))
                # Log at base level finish
                self._log(f"Scanned: {base}")

            # compute plan
            plan = []
            replace_space = self.replace_space.get()
            for base, p in items:
                new_name = transform_name(p.name, replace_space)
                if new_name != p.name:
                    plan.append((base, p, p.with_name(new_name)))
            self.preview_rows = plan

            # Update table on UI thread
            def done_ui():
                self._progress_stop("Scan complete.")
                self._set_busy(False)
                if not plan:
                    self.tree.insert("", "end", values=("", "", "(unchanged)", "No changes", ""), tags=("info",))
                    return
                for base, old, new in sorted(plan, key=lambda t: (str(t[0]).lower(), str(t[1]).lower())):
                    self.tree.insert("", "end",
                                     values=(str(base), _kind_of(old), str(old), str(new), "Preview"),
                                     tags=("preview",))
            self.after(0, done_ui)

        threading.Thread(target=worker, daemon=True).start()

    # ---------- Rename with progress ----------
    def _rename(self):
        if self._busy:
            return
        if not self.preview_rows:
            # Build plan quickly (same checks as _preview path)
            if not self.base_dirs:
                messagebox.showwarning("Warning", "Please add at least one base folder.")
                return
            if not self.include_dirs.get() and not self.include_files.get():
                messagebox.showwarning("Warning", "Select at least one target: Folders or Files.")
                return
            if not messagebox.askyesno("Confirm", "No Preview found. Scan & proceed?"):
                return
            self._preview()
            return

        if self.collision_mode == COL_MERGE_HASH:
            ok = messagebox.askyesno(
                "Confirm Merge & De-duplicate",
                "Merge mode may delete exact duplicate files (same SHA-256) and merge directories.\n"
                "These deletions cannot be undone via the Undo button.\n\nProceed?"
            )
            if not ok:
                return

        self._set_busy(True)
        self._clear_tree()
        self.run_log.delete(0, "end")

        total = len(self.preview_rows)
        self._progress_start("determinate", "Renaming…", total=total)

        applied = []
        info_rows = []

        def worker():
            step = 0
            for base, old, intended_new in self.preview_rows:
                step += 1
                self._progress_update(step=step, msg="Renaming…", current_folder=str(base))

                try:
                    if not intended_new.exists():
                        old.rename(intended_new)
                        applied.append((base, old, intended_new, intended_new))
                        continue

                    # conflict
                    if self.collision_mode == COL_SUFFIX:
                        actual_target = unique_target_path(intended_new)
                        old.rename(actual_target)
                        applied.append((base, old, intended_new, actual_target))
                    else:
                        if old.is_file() and intended_new.is_file():
                            try:
                                if file_sha256(old) == file_sha256(intended_new):
                                    old.unlink()
                                    info_rows.append((base, "FILE", str(old), str(intended_new),
                                                      "Duplicate removed (same hash)"))
                                else:
                                    actual_target = unique_target_path(intended_new)
                                    old.rename(actual_target)
                                    applied.append((base, old, intended_new, actual_target))
                            except Exception:
                                actual_target = unique_target_path(intended_new)
                                old.rename(actual_target)
                                applied.append((base, old, intended_new, actual_target))
                        elif old.is_dir() and intended_new.is_dir():
                            stats = merge_dirs(old, intended_new)
                            note = f"Merged dir (moved:{stats['moved']}, dups:{stats['deleted_dups']}, kept_both:{stats['conflicts']})"
                            info_rows.append((base, "DIR", str(old), str(intended_new), note))
                        else:
                            actual_target = unique_target_path(intended_new)
                            old.rename(actual_target)
                            applied.append((base, old, intended_new, actual_target))

                except Exception as e:
                    info_rows.append((base, "OTHER", str(old), str(intended_new), f"ERROR: {e}"))

            # Finish UI update
            def done_ui():
                self._progress_stop("Rename done.")
                self._set_busy(False)
                self.applied_rows[:] = applied
                self.applied_info_rows[:] = info_rows

                any_rows = False
                if applied:
                    any_rows = True
                    for base, old, intended, actual in sorted(applied, key=lambda t: (str(t[0]).lower(), str(t[1]).lower())):
                        status = "Renamed" if actual == intended else "Renamed (conflict ➜ unique path)"
                        tag = "renamed" if actual == intended else "conflict"
                        self.tree.insert("", "end",
                                         values=(str(base), _kind_of(old), str(old), str(actual), status),
                                         tags=(tag,))
                if info_rows:
                    any_rows = True
                    for base, kind, src, dst, status in info_rows:
                        tag = "merge" if "Merged" in status else ("dupdel" if "Duplicate removed" in status else "info")
                        self.tree.insert("", "end",
                                         values=(str(base), kind, src, dst, status),
                                         tags=(tag,))
                if not any_rows:
                    self.tree.insert("", "end", values=("", "", "", "Nothing renamed", ""), tags=("info",))
                    messagebox.showinfo("Done", "No changes executed.")
                else:
                    messagebox.showinfo("Done", f"Processed {len(applied)} rename(s) and {len(info_rows)} merge/de-dupe action(s).")
            self.after(0, done_ui)

        threading.Thread(target=worker, daemon=True).start()

    # ---------- Undo ----------
    def _undo_last(self):
        if self._busy:
            return
        if not self.applied_rows and not self.applied_info_rows:
            messagebox.showinfo("Undo", "Nothing to undo in this session.")
            return
        if self.applied_info_rows and self.collision_mode == COL_MERGE_HASH:
            messagebox.showwarning(
                "Undo notice",
                "Undo will only revert rename/move operations.\n"
                "Merges and de-duplication deletions cannot be undone."
            )

        self._set_busy(True)
        self._clear_tree()
        self._progress_start("determinate", "Undoing…", total=len(self.applied_rows))

        undone = []

        def worker():
            from itertools import count
            for i, (base, old, intended, actual) in zip(count(1), sorted(self.applied_rows, key=lambda t: len(t[3].parts), reverse=True)):
                self._progress_update(step=i, msg="Undoing…", current_folder=str(base))
                try:
                    back_target = old if not old.exists() else unique_target_path(old)
                    actual.rename(back_target)
                    undone.append((actual, back_target))
                except Exception as e:
                    print(f"[ERROR] Undo failed '{actual}' -> '{old}': {e}")

            def done_ui():
                self._progress_stop("Undo done.")
                self._set_busy(False)
                for src, dst in sorted(undone, key=lambda t: str(t[0]).lower()):
                    self.tree.insert("", "end",
                                     values=("", _kind_of(dst), str(src), str(dst), "Undone"),
                                     tags=("undo",))
                for base, kind, src, dst, status in self.applied_info_rows:
                    self.tree.insert("", "end",
                                     values=(str(base), kind, src, dst, status + " (not undoable)"),
                                     tags=("info",))
                self.applied_rows.clear()
                messagebox.showinfo("Undo", f"Undone {len(undone)} item(s).")
            self.after(0, done_ui)

        threading.Thread(target=worker, daemon=True).start()

    # ---------- Save CSV ----------
    def _save_csv(self):
        if self._busy:
            return
        if not self.preview_rows and not self.applied_rows and not self.applied_info_rows:
            messagebox.showinfo("Save CSV", "No data to save. Run Preview or Rename first.")
            return
        fp = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv")],
            title="Save mapping CSV"
        )
        if not fp:
            return
        headers = ["base", "kind", "current_path", "intended_new_path", "actual_new_path_or_note", "status"]
        rows = []
        if self.applied_rows or self.applied_info_rows:
            for base, old, intended, actual in self.applied_rows:
                rows.append((str(base), _kind_of(old), str(old), str(intended), str(actual), "RENAMED"))
            for base, kind, src, dst, status in self.applied_info_rows:
                rows.append((str(base), kind, src, "(merge/de-dupe)", dst, status))
        else:
            for base, old, intended in self.preview_rows:
                rows.append((str(base), _kind_of(old), str(old), str(intended), "(preview)", "PREVIEW"))
        try:
            with open(fp, "w", newline="", encoding="utf-8") as f:
                w = csv.writer(f)
                w.writerow(headers)
                w.writerows(rows)
            messagebox.showinfo("Saved", f"CSV saved:\n{fp}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save CSV:\n{e}")





def main():
    root = tk.Tk()
    app = App(root)
    root.minsize(1100, 680)
    try:
        app.grid(sticky="nsew")
    except Exception:
        pass
    root.mainloop()

if __name__ == "__main__":
    main()
