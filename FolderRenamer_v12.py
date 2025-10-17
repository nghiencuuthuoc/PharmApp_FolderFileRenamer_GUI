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
  * Dir vs dir: recursively merge with overwrite-prefer-destination; identical files deleted from source.
- Undo:
  * Only for rename/move operations performed by this session.
  * Merge deletions are NOT undoable (guarded by explicit status tags).
- Performance:
  * Uses streaming hash (chunk=1MB) for large files.
  * Progress bar shows current folder path + counters.

Copyright: NCT — for educational/internal use.
"""

import csv
import unicodedata
import hashlib
import threading
from pathlib import Path
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

# --- i18n (EN ⇄ VI) -----------------------------------------------------------
SUPPORTED_LANGS = ("vi", "en")
I18N = {
    "vi": {
        "language": "Ngôn ngữ",
        "lang_vi": "Tiếng Việt",
        "lang_en": "English",
        "apply_theme_btn": "Áp dụng [Ctrl+T]",
        "add_path_btn": "Thêm đường dẫn [Ctrl+L]",
        "add_windows_btn": "Chọn thư mục… [Ctrl+O]",
        "add_multi_btn": "Chọn nhiều… [Ctrl+Shift+O]",
        "remove_btn": "Xóa [Del]",
        "clear_btn": "Xóa hết [Ctrl+D]",
        "bulk_btn": "Bulk ▸ [Ctrl+B]",
        "preview_btn": "Xem trước [F5]",
        "rename_btn": "Đổi tên [F9]",
        "undo_btn": "Hoàn tác [Ctrl+Z]",
        "savecsv_btn": "Lưu CSV [Ctrl+S]",
        "add_from_box_btn": "Thêm từ ô [Enter]",
        "collision_label": "Xử lý trùng",
        "collision_merge": "Gộp & khử trùng (SHA-256)",
        "collision_suffix": "Thêm hậu tố _1",
        "status_prefix": "Tập lệnh",
        "status_theme": "Giao diện",
    },
    "en": {
        "language": "Language",
        "lang_vi": "Vietnamese",
        "lang_en": "English",
        "apply_theme_btn": "Apply [Ctrl+T]",
        "add_path_btn": "Add Path [Ctrl+L]",
        "add_windows_btn": "Add Windows… [Ctrl+O]",
        "add_multi_btn": "Add Multi… [Ctrl+Shift+O]",
        "remove_btn": "Remove [Del]",
        "clear_btn": "Clear [Ctrl+D]",
        "bulk_btn": "Bulk ▸ [Ctrl+B]",
        "preview_btn": "Preview [F5]",
        "rename_btn": "Rename [F9]",
        "undo_btn": "Undo [Ctrl+Z]",
        "savecsv_btn": "Save CSV [Ctrl+S]",
        "add_from_box_btn": "Add From Box [Enter]",
        "collision_label": "Collision",
        "collision_merge": "MERGE & de-dup (SHA-256)",
        "collision_suffix": "Add suffix _1",
        "status_prefix": "Script",
        "status_theme": "Theme",
    },
}

# --------- Script name banner ----------
try:
    SCRIPT_NAME = Path(__file__).name
except NameError:
    SCRIPT_NAME = "FolderFileRenamer_GUI.py"
print(f"[INFO] Running: {SCRIPT_NAME}")

# --------- Helpers ----------

def strip_accents(s: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFKD", s) if not unicodedata.combining(c))

def to_upper(s: str) -> str:
    return s.upper()

def replace_space_with_underscore(s: str) -> str:
    return s.replace(" ", "_")

CHUNK_SIZE = 1024 * 1024

def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(CHUNK_SIZE), b""):
            h.update(chunk)
    return h.hexdigest()

# --------- Depth modes ----------
DEPTH_L1 = "Level 1"
DEPTH_L2 = "Level 2"
DEPTH_UP_TO_2 = "Up to Level 2"
DEPTH_ALL = "All levels"

DEPTH_LABEL_TO_CONST = {
    "Level 1": DEPTH_L1,
    "Level 2": DEPTH_L2,
    "Up to Level 2": DEPTH_UP_TO_2,
    "All levels": DEPTH_ALL,
}

# --------- Move plan rows ----------
# base, kind, current, new

# --------- Naming transforms ----------
TRANSFORM_TO_UPPER = True
REPLACE_SPACE = True
REMOVE_ACCENTS = True

# --------- Inspect path kind ----------

def kind_of(p: Path) -> str:
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
        if child.is_dir() and t.exists() and t.is_dir():
            sub = merge_dirs(child, t)
            for k, v in sub.items():
                stats[k] = stats.get(k, 0) + v
        else:
            if child.is_file() and t.exists() and t.is_file():
                # Check duplicates by hash
                try:
                    if sha256_file(child) == sha256_file(t):
                        child.unlink()
                        stats["deleted_dups"] += 1
                        continue
                except Exception:
                    stats["conflicts"] += 1
            # Move/rename
            base_name = t.name
            if t.exists():
                i = 1
                while True:
                    cand = t.with_name(f"{t.stem}_{i}{t.suffix}")
                    if not cand.exists():
                        t = cand
                        break
                    i += 1
            child.rename(t)
            stats["moved"] += 1
    # Remove empty src
    try:
        if not any(src.iterdir()):
            src.rmdir()
    except Exception:
        pass
    return stats

# --------- GUI ----------
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
            "row_alt": "#F5F7FA"
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
            "bg": "#1f1f1f", "fg": "#efefef",
            "button_bg": "#8e8e93", "button_active": "#6e6e73", "button_fg": "#ffffff",
            "accent": "#a1a1a7", "heading_bg": "#3a3a3c",
            "selection_bg": "#2a2a2a", "input_bg": "#2b2b2b", "input_fg": "#f2f2f7",
            "row_alt": "#232323", "table_bg": "#232323"
        },
    }

    def __init__(self, root: tk.Tk):
        self.root = root
        self.style = ttk.Style(root)

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

        self.style.configure("TFrame",
                             background=bg)
        self.style.configure("TLabel",
                             background=bg, foreground=fg)
        self.style.configure("Pharm.TButton",
                             background=btn_bg, foreground=btn_fg, padding=6)
        self.style.map("Pharm.TButton",
                       background=[("active", btn_active)])
        self.style.configure("Treeview",
                             background=table_bg, foreground=fg, fieldbackground=table_bg)
        self.style.configure("Treeview.Heading",
                             background=head_bg, foreground="#ffffff")
        return pal

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
        self.current_lang = tk.StringVar(value="vi")
        self.include_dirs = tk.BooleanVar(value=True)
        self.include_files = tk.BooleanVar(value=False)
        self.replace_space = tk.BooleanVar(value=True)
        self.depth_label = tk.StringVar(value="All levels")

        self.collision_label = tk.StringVar(value="Suffix _1")
        self.collision_mode = COL_SUFFIX

        self.single_path_var = tk.StringVar()
        self.base_dirs: list[Path] = []

        self.preview_rows: list[tuple[Path, Path, Path]] = []

        # Progress state vars
        self.progress_var = tk.DoubleVar(value=0)
        self.progress_total = 1
        self.progress_msg = tk.StringVar(value="Ready")
        self.counter_msg = tk.StringVar(value="0/0")
        self.current_folder_var = tk.StringVar(value="-")

        # Theme manager
        self.tm = ThemeManager(master)
        self.palette = self.tm.apply(self.current_theme.get())

        self._build_ui()
        self._setup_tree_tags()
        self._apply_palette_to_text_and_listbox()
        # Bind shortcuts and apply initial language
        self._bind_shortcuts()
        self._apply_language()
        self._on_collision_mode_change()

    def _tr(self, key: str) -> str:
        lang = getattr(self, "current_lang", None)
        lang = lang.get() if hasattr(lang, "get") else "vi"
        if lang not in SUPPORTED_LANGS:
            lang = "vi"
        return I18N.get(lang, I18N["vi"]).get(key, key)

    def _apply_language(self):
        def safe_set(w, text):
            try:
                if w is not None:
                    w.config(text=text)
            except Exception:
                pass
        # Buttons
        safe_set(getattr(self, "btn_apply_theme", None), self._tr("apply_theme_btn"))
        safe_set(getattr(self, "btn_add_path", None), self._tr("add_path_btn"))
        safe_set(getattr(self, "btn_add_win", None), self._tr("add_windows_btn"))
        safe_set(getattr(self, "btn_add_multi", None), self._tr("add_multi_btn"))
        safe_set(getattr(self, "btn_remove", None), self._tr("remove_btn"))
        safe_set(getattr(self, "btn_clear", None), self._tr("clear_btn"))
        safe_set(getattr(self, "btn_bulk", None), self._tr("bulk_btn"))
        safe_set(getattr(self, "btn_preview", None), self._tr("preview_btn"))
        safe_set(getattr(self, "btn_rename", None), self._tr("rename_btn"))
        safe_set(getattr(self, "btn_undo", None), self._tr("undo_btn"))
        safe_set(getattr(self, "btn_savecsv", None), self._tr("savecsv_btn"))
        # Collision label + values
        try:
            self.collision_text_lbl.config(text=self._tr("collision_label"))
            self.collision_cbb.configure(values=[self._tr("collision_suffix"), self._tr("collision_merge")])
            # keep current selection semantically
            if self.collision_mode == COL_MERGE_HASH:
                self.collision_cbb.set(self._tr("collision_merge"))
            else:
                self.collision_cbb.set(self._tr("collision_suffix"))
        except Exception:
            pass
        # Status bar
        try:
            theme_name = self.current_theme.get()
            script = globals().get("SCRIPT_NAME", "FolderRenamer")
            self.status_lbl.config(text=f"{self._tr('status_prefix')}: {script} • {self._tr('status_theme')}: {theme_name}")
        except Exception:
            pass
        # Language combobox label/value
        try:
            self.lang_cbb.configure(values=[self._tr("lang_vi"), self._tr("lang_en")])
            self.lang_cbb.set(self._tr("lang_vi") if self.current_lang.get()=="vi" else self._tr("lang_en"))
        except Exception:
            pass

    def _on_language_change(self, event=None):
        val = self.lang_cbb.get()
        # Map display back to code
        if val in (I18N["vi"]["lang_vi"], I18N["en"]["lang_vi"]):
            self.current_lang.set("vi")
        else:
            self.current_lang.set("en")
        self._apply_language()

    def _toggle_language(self):
        self.current_lang.set("en" if self.current_lang.get()=="vi" else "vi")
        try:
            self.lang_cbb.set(self._tr("lang_vi") if self.current_lang.get()=="vi" else self._tr("lang_en"))
        except Exception:
            pass
        self._apply_language()

    def _on_collision_mode_change(self, event=None):
        label = (self.collision_cbb.get() or "").lower()
        if ("merge" in label) or ("khử trùng" in label) or ("gộp" in label):
            self.collision_mode = COL_MERGE_HASH
            note = self._tr("collision_merge")
        else:
            self.collision_mode = COL_SUFFIX
            note = self._tr("collision_suffix")
        try:
            theme_name = self.current_theme.get()
            script = globals().get("SCRIPT_NAME", "FolderRenamer")
            self.status_lbl.config(text=f"{self._tr('status_prefix')}: {script} • {self._tr('status_theme')}: {theme_name} • {note}")
        except Exception:
            pass

    def _bind_shortcuts(self):
        root = self.master
        # Primary actions
        root.bind("<F5>",           lambda e: self._preview())
        root.bind("<F9>",           lambda e: self._rename())
        root.bind("<Control-s>",    lambda e: self._save_csv())
        root.bind("<Control-z>",    lambda e: self._undo_last())
        root.bind("<Control-t>",    lambda e: self._apply_theme())
        # Bases management
        root.bind("<Control-o>",        lambda e: self._add_folder_dialog())
        root.bind("<Control-Shift-O>",  lambda e: self._add_many_dialog())
        root.bind("<Control-l>",        lambda e: self._add_path_from_entry())
        root.bind("<Delete>",           lambda e: self._remove_selected_bases())
        root.bind("<Control-d>",        lambda e: self._clear_bases())
        root.bind("<Control-b>",        lambda e: self._toggle_bulk_box())
        # Language toggle
        root.bind("<Control-Shift-L>",  lambda e: self._toggle_language())
        # Accept Enter in single path entry
        try:
            self.single_entry.bind("<Return>", lambda e: self._add_path_from_entry())
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
        self.btn_apply_theme = ttk.Button(top, text=self._tr("apply_theme_btn"), style="Pharm.TButton", command=self._apply_theme)
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

        self.collision_text_lbl = ttk.Label(top, text=self._tr("collision_label"))
        self.collision_text_lbl.grid(row=0, column=7, sticky="e", padx=(16,0))
        self.collision_cbb = ttk.Combobox(top, state="readonly",
                                          values=[self._tr("collision_suffix"), self._tr("collision_merge")],
                                          textvariable=self.collision_label, width=24)
        self.collision_cbb.grid(row=0, column=8, sticky="w", padx=(6,6))
        self.collision_cbb.bind("<<ComboboxSelected>>", self._on_collision_mode_change)
        # Language switch (EN/VI)
        ttk.Label(top, text=self._tr("language")).grid(row=0, column=9, sticky="e", padx=(16,4))
        self.lang_cbb = ttk.Combobox(top, state="readonly", width=12,
                                     values=[self._tr("lang_vi"), self._tr("lang_en")])
        self.lang_cbb.set(self._tr("lang_vi") if self.current_lang.get()=="vi" else self._tr("lang_en"))
        self.lang_cbb.grid(row=0, column=10, sticky="w")
        self.lang_cbb.bind("<<ComboboxSelected>>", self._on_language_change)
        top.grid_columnconfigure(11, weight=1)

        # Row 1: BASE TOOLBAR
        bar = ttk.Frame(self); bar.pack(fill="x", padx=10, pady=(0,6))
        ttk.Label(bar, text="Path:").pack(side="left")
        self.single_entry = ttk.Entry(bar, textvariable=self.single_path_var, width=60)
        self.single_entry.pack(side="left", padx=(6,6))
        self.btn_add_path = ttk.Button(bar, text=self._tr("add_path_btn"), style="Pharm.TButton", command=self._add_path_from_entry)
        self.btn_add_path.pack(side="left", padx=(0,6))
        self.btn_add_win = ttk.Button(bar, text=self._tr("add_windows_btn"), style="Pharm.TButton", command=self._add_folder_dialog)
        self.btn_add_win.pack(side="left", padx=(0,6))
        self.btn_add_multi = ttk.Button(bar, text=self._tr("add_multi_btn"), style="Pharm.TButton", command=self._add_many_dialog)
        self.btn_add_multi.pack(side="left", padx=(0,6))
        self.btn_remove = ttk.Button(bar, text=self._tr("remove_btn"), style="Pharm.TButton", command=self._remove_selected_bases)
        self.btn_remove.pack(side="left", padx=(0,6))
        self.btn_clear = ttk.Button(bar, text=self._tr("clear_btn"), style="Pharm.TButton", command=self._clear_bases)
        self.btn_clear.pack(side="left", padx=(0,12))
        self._bulk_visible = False
        self.btn_bulk = ttk.Button(bar, text=self._tr("bulk_btn"), style="Pharm.TButton", command=self._toggle_bulk_box)
        self.btn_bulk.pack(side="left", padx=(0,18))
        self.btn_preview = ttk.Button(bar, text=self._tr("preview_btn"), style="Pharm.TButton", command=self._preview)
        self.btn_preview.pack(side="left")
        self.btn_rename = ttk.Button(bar, text=self._tr("rename_btn"), style="Pharm.TButton", command=self._rename)
        self.btn_rename.pack(side="left", padx=(6,0))
        self.btn_undo = ttk.Button(bar, text=self._tr("undo_btn"), style="Pharm.TButton", command=self._undo_last)
        self.btn_undo.pack(side="left", padx=(6,0))
        self.btn_savecsv = ttk.Button(bar, text=self._tr("savecsv_btn"), style="Pharm.TButton", command=self._save_csv)
        self.btn_savecsv.pack(side="left", padx=(6,0))

        # Row 2: BULK PASTE (hidden initially)
        bulk_wrap = ttk.Frame(self); bulk_wrap.pack(fill="x", padx=10)
        self.bulk_frame = bulk_wrap
        ttk.Label(bulk_wrap, text="Bulk Paste (one per line or ';'):").grid(row=0, column=0, sticky="w")
        self.bulk_text = tk.Text(bulk_wrap, height=3, width=80)
        self.bulk_text.grid(row=0, column=1, sticky="we", padx=(6,6))
        ttk.Button(bulk_wrap, text=self._tr("add_from_box_btn"), style="Pharm.TButton", command=self._add_paths_from_text)\
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
        self.tree.heading("new", text="New Path")
        self.tree.heading("status", text="Status")
        self.tree.column("base", width=150, anchor="w")
        self.tree.column("kind", width=60, anchor="center")
        self.tree.column("current", width=500, anchor="w")
        self.tree.column("new", width=500, anchor="w")
        self.tree.column("status", width=120, anchor="w")

        self.tree.grid(row=0, column=0, sticky="nsew")
        y_scroll = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        y_scroll.grid(row=0, column=1, sticky="ns")
        self.tree.configure(yscrollcommand=y_scroll.set)
        x_scroll = ttk.Scrollbar(table_frame, orient="horizontal", command=self.tree.xview)
        x_scroll.grid(row=1, column=0, sticky="ew")
        table_frame.grid_rowconfigure(0, weight=1)
        table_frame.grid_columnconfigure(0, weight=1)

        # Footer
        foot = ttk.Frame(self); foot.pack(fill="x", padx=10, pady=(0,6))
        self.status_lbl = ttk.Label(foot, text=f"Script: {SCRIPT_NAME} • Theme: {self.current_theme.get()}")
        self.status_lbl.pack(side="left")

    # ---------- Theme / styling ----------
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
            if busy:
                self.progressbar.start(10)
            else:
                self.progressbar.stop()
        except Exception:
            pass

    def _ask_directory(self, title: str) -> Path | None:
        try:
            p = filedialog.askdirectory(title=title)
            if p:
                return Path(p)
        except Exception:
            pass
        return None

    def _parse_single_path(self) -> Path | None:
        p = self.single_path_var.get()
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
            try:
                self.base_listbox.insert("end", str(p))
            except Exception:
                pass

    def _toggle_bulk_box(self):
        self._bulk_visible = not self._bulk_visible
        if self._bulk_visible:
            self.bulk_frame.pack(fill="x", padx=10)
            try:
                self.btn_bulk.config(text=self._tr("bulk_btn"))
            except Exception:
                pass
        else:
            self.bulk_frame.pack_forget()
            try:
                self.btn_bulk.config(text=self._tr("bulk_btn"))
            except Exception:
                pass

    def _progress_start(self, total: int | None = None, mode: str = "determinate"):
        def _start():
            self.progress_msg.set("Running…")
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

    def _progress_finish(self, msg: str = "Done."):
        def _fin():
            try:
                self.progressbar.stop()
            except Exception:
                pass
            self.progress_msg.set(msg)
            self.current_folder_var.set("-")
        self.after(0, _fin)

    # ---------- Actions ----------
    def _apply_theme(self):
        try:
            self.palette = self.tm.apply(self.current_theme.get())
            self._setup_tree_tags()
            self._apply_palette_to_text_and_listbox()
            theme = self.current_theme.get()
            self.status_lbl.config(text=f"Script: {SCRIPT_NAME} • Theme: {theme}")
        except Exception as e:
            messagebox.showerror("Theme", f"Failed to apply theme: {e}")

    def _add_path_from_entry(self):
        p = self._parse_single_path()
        if not p:
            messagebox.showinfo("Add Path", "Enter a valid base folder path.")
            return
        self.base_dirs.append(p)
        self._refresh_base_listbox()

    def _add_folder_dialog(self):
        p = self._ask_directory("Select base folder…")
        if p:
            self.base_dirs.append(p)
            self._refresh_base_listbox()

    def _add_many_dialog(self):
        # Pick multiple via dialog repeatedly until cancel
        while True:
            p = self._ask_directory("Add another base folder… (Cancel to stop)")
            if not p:
                break
            self.base_dirs.append(p)
            self._refresh_base_listbox()

    def _add_paths_from_text(self):
        raw = self.bulk_text.get("1.0", "end").strip()
        if not raw:
            return
        parts = []
        for line in raw.splitlines():
            for piece in line.split(";"):
                s = piece.strip().strip('"').strip("'")
                if s:
                    parts.append(s)
        ok = 0
        for s in parts:
            try:
                p = Path(s)
                if p.exists() and p.is_dir():
                    self.base_dirs.append(p)
                    ok += 1
            except Exception:
                pass
        self._refresh_base_listbox()
        messagebox.showinfo("Bulk", f"Added {ok} folder(s).")

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

    def _collect_targets(self, base: Path):
        # Collect based on settings
        kinds = []
        if self.include_dirs.get():
            kinds.append("dir")
        if self.include_files.get():
            kinds.append("file")
        depth = DEPTH_LABEL_TO_CONST.get(self.depth_label.get(), DEPTH_ALL)

        items = []
        if depth == DEPTH_L1:
            it = list(base.iterdir())
            for p in it:
                if (p.is_dir() and "dir" in kinds) or (p.is_file() and "file" in kinds):
                    items.append(p)
        elif depth == DEPTH_L2:
            for p in list(base.iterdir()):
                if (p.is_dir() and "dir" in kinds) or (p.is_file() and "file" in kinds):
                    items.append(p)
                if p.is_dir():
                    for q in list(p.iterdir()):
                        if (q.is_dir() and "dir" in kinds) or (q.is_file() and "file" in kinds):
                            items.append(q)
        elif depth == DEPTH_UP_TO_2:
            # Level 1 + Level 2
            for p in list(base.iterdir()):
                if (p.is_dir() and "dir" in kinds) or (p.is_file() and "file" in kinds):
                    items.append(p)
                if p.is_dir():
                    for q in list(p.iterdir()):
                        if (q.is_dir() and "dir" in kinds) or (q.is_file() and "file" in kinds):
                            items.append(q)
        else:
            # All levels
            for p in base.rglob("*"):
                if (p.is_dir() and "dir" in kinds) or (p.is_file() and "file" in kinds):
                    items.append(p)
        return items

    def _transform_name(self, name: str) -> str:
        s = name
        if self.replace_space.get():
            s = replace_space_with_underscore(s)
        if REMOVE_ACCENTS:
            s = strip_accents(s)
        if TRANSFORM_TO_UPPER:
            s = to_upper(s)
        return s

    def _plan_for_path(self, p: Path) -> tuple[Path, Path]:
        new_name = self._transform_name(p.name.replace('-', '_'))
        new_path = p.with_name(new_name)
        if new_path == p:
            return p, p
        # handle collision quickly for plan only
        if new_path.exists():
            if self.collision_mode == COL_SUFFIX:
                i = 1
                while True:
                    cand = new_path.with_name(f"{new_path.stem}_{i}{new_path.suffix}")
                    if not cand.exists():
                        new_path = cand
                        break
                    i += 1
            else:
                # merge target — plan marks as same path (special status during preview)
                pass
        return p, new_path

    def _preview(self):
        if not self.base_dirs:
            messagebox.showinfo("Preview", "Add at least one base folder.")
            return
        self.tree.delete(*self.tree.get_children())
        self.preview_rows.clear()
        total = 0
        for base in self.base_dirs:
            for p in self._collect_targets(base):
                src, dst = self._plan_for_path(p)
                kind = kind_of(p)
                tag = "preview"
                status = "same" if src == dst else ("merge" if self.collision_mode == COL_MERGE_HASH and dst.exists() else "rename")
                self.tree.insert("", "end", values=(str(base), kind, str(src), str(dst), status), tags=(tag,))
                self.preview_rows.append((base, src, dst))
                total += 1
        self.progress_msg.set(f"Preview: {total} items")

    def _rename_worker(self):
        # Execute renames/merges
        ops = self.tree.get_children()
        total = len(ops)
        self._progress_start(total)
        done = 0
        undo_log = []  # list of (dst, original_path)
        try:
            for iid in ops:
                base, kind, cur_s, new_s, status = self.tree.item(iid, "values")
                cur = Path(cur_s)
                new = Path(new_s)
                self._progress_update(done, current_folder=str(cur.parent))
                if status == "same":
                    self.tree.item(iid, tags=("info",))
                elif status == "merge" and self.collision_mode == COL_MERGE_HASH and new.exists():
                    # merge dirs/files
                    if cur.is_dir() and new.is_dir():
                        stats = merge_dirs(cur, new)
                        self.tree.item(iid, tags=("merge",))
                    elif cur.is_file() and new.is_file():
                        try:
                            if sha256_file(cur) == sha256_file(new):
                                cur.unlink()
                                self.tree.item(iid, tags=("dupdel",))
                            else:
                                # keep both by suffix
                                i = 1
                                cand = new
                                while cand.exists():
                                    cand = new.with_name(f"{new.stem}_{i}{new.suffix}")
                                    i += 1
                                cur.rename(cand)
                                undo_log.append((cand, cur))
                                self.tree.item(iid, tags=("renamed",))
                        except Exception:
                            self.tree.item(iid, tags=("conflict",))
                    else:
                        # different kinds — fallback to suffix move
                        i = 1
                        cand = new
                        while cand.exists():
                            cand = new.with_name(f"{new.stem}_{i}{new.suffix}")
                            i += 1
                        try:
                            cur.rename(cand)
                            undo_log.append((cand, cur))
                            self.tree.item(iid, tags=("renamed",))
                        except Exception:
                            self.tree.item(iid, tags=("error",))
                else:
                    # simple rename/move (safe suffix if needed)
                    if new.exists():
                        i = 1
                        cand = new
                        while cand.exists():
                            cand = new.with_name(f"{new.stem}_{i}{new.suffix}")
                            i += 1
                        new = cand
                    try:
                        cur.rename(new)
                        undo_log.append((new, cur))
                        self.tree.item(iid, tags=("renamed",))
                    except Exception:
                        self.tree.item(iid, tags=("error",))
                done += 1
                self._progress_update(done)
        finally:
            self._progress_finish("Rename finished.")
            self._undo_stack = undo_log

    def _rename(self):
        if not self.base_dirs:
            messagebox.showinfo("Rename", "Add at least one base folder.")
            return
        t = threading.Thread(target=self._rename_worker, daemon=True)
        t.start()

    def _undo_last(self):
        log = getattr(self, "_undo_stack", [])
        if not log:
            messagebox.showinfo("Undo", "Nothing to undo.")
            return
        errors = 0
        for dst, original in reversed(log):
            try:
                if dst.exists():
                    dst.rename(original)
            except Exception:
                errors += 1
        self._undo_stack = []
        if errors:
            messagebox.showwarning("Undo", f"Undo finished with {errors} error(s).")
        else:
            messagebox.showinfo("Undo", "Undo finished.")

    def _save_csv(self):
        if not self.tree.get_children():
            messagebox.showinfo("Save CSV", "No rows to export. Run Preview first.")
            return
        try:
            path = filedialog.asksaveasfilename(title="Save preview to CSV…",
                                                defaultextension=".csv",
                                                filetypes=[["CSV", "*.csv"], ["All", "*.*"]])
            if not path:
                return
            with open(path, "w", newline="", encoding="utf-8") as f:
                w = csv.writer(f)
                w.writerow(["Base", "Kind", "Current", "New", "Status"])
                for iid in self.tree.get_children():
                    w.writerow(list(self.tree.item(iid, "values")))
            messagebox.showinfo("Save CSV", f"Saved: {path}")
        except Exception as e:
            messagebox.showerror("Save CSV", f"Failed: {e}")

# ---------- main ----------
def main():
    root = tk.Tk()
    app = App(root)
    root.mainloop()

if __name__ == "__main__":
    main()
