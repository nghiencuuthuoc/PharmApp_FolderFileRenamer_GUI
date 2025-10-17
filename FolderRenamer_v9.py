#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FolderFileRenamer_GUI.py — Compact Toolbar Layout (save vertical space)
- Multi base folders (add path, bulk paste, windows picker, remove, clear)
- Targets: Folders / Files
- Depth combobox: Level 1, Level 2, Up to Level 2, All levels
- Transform: '-'->'_', optional ' '->'_', remove accents, UPPERCASE
- Themes: PharmApp Light, Nord Light, Midnight Teal (Dark), Solar Slate, macOS Graphite (Dark)
- Preview / Rename (collision-safe) / Undo / Save CSV
- Conflict handling: Keep _1 (suffix), Delete existing, Merge into existing (NEW)
UI: bilingual (EN/VI)
"""

import csv
import hashlib
import unicodedata
import shutil
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
        self.style.map("TCombobox",
                       fieldbackground=[("readonly", input_bg)],
                       foreground=[("readonly", input_fg)])
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

        try:
            self.root.option_add("*Listbox*Background", input_bg)
            self.root.option_add("*Listbox*Foreground", input_fg)
            self.root.option_add("*Listbox*selectBackground", sel_bg)
        except Exception:
            pass
        return pal


# --------- Name transform helpers ----------
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
    """Keep current behavior: suffix after the full name (even after extension)."""
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

def collect_paths_for_bases(base_dirs: list[Path], depth_mode: str,
                            include_dirs: bool, include_files: bool) -> list[tuple[Path, Path]]:
    results: list[tuple[Path, Path]] = []
    for base_dir in base_dirs:
        if not base_dir.exists() or not base_dir.is_dir():
            continue
        all_paths = list(base_dir.rglob("*"))
        for p in all_paths:
            try:
                d = _rel_depth(base_dir, p)
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
            results.append((base_dir, p))
    results.sort(key=lambda t: len(t[1].parts), reverse=True)  # deepest-first
    return results

def compute_plan(items: list[tuple[Path, Path]], replace_space: bool) -> list[tuple[Path, Path, Path]]:
    plan = []
    for base, p in items:
        new_name = transform_name(p.name, replace_space)
        if new_name != p.name:
            plan.append((base, p, p.with_name(new_name))
                        )
    return plan

# --------- Conflict handling ----------
CONFLICT_SUFFIX = "SUFFIX"   # keep both by adding _1, _2...
CONFLICT_DELETE = "DELETE"   # delete existing target then rename
CONFLICT_MERGE  = "MERGE"    # merge into existing (NEW)

def _sha256_file(fp: Path) -> str:
    h = hashlib.sha256()
    with open(fp, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

def _files_identical(a: Path, b: Path) -> bool:
    try:
        if a.stat().st_size != b.stat().st_size:
            return False
        return _sha256_file(a) == _sha256_file(b)
    except Exception:
        return False

def _unique_in_dir(dst_dir: Path, name: str) -> Path:
    return unique_target_path(dst_dir / name)

def _merge_move(src_dir: Path, dst_dir: Path, stats: dict):
    """Merge contents of src_dir INTO dst_dir."""
    dst_dir.mkdir(parents=True, exist_ok=True)
    try:
        for item in list(src_dir.iterdir()):
            tgt = dst_dir / item.name
            if not tgt.exists():
                try:
                    item.rename(tgt)
                    stats["moved"] += 1
                except Exception:
                    # fallback copy if rename fails across devices
                    try:
                        if item.is_dir():
                            shutil.copytree(item, tgt, dirs_exist_ok=True)
                            shutil.rmtree(item, ignore_errors=True)
                        else:
                            shutil.copy2(item, tgt)
                            item.unlink(missing_ok=True)
                        stats["copied"] += 1
                    except Exception:
                        stats["errors"] += 1
                continue

            # Conflict inside merge
            if item.is_dir() and tgt.is_dir():
                _merge_move(item, tgt, stats)
                try:
                    item.rmdir()
                except Exception:
                    pass
            elif item.is_file() and tgt.is_file():
                if _files_identical(item, tgt):
                    # skip duplicate
                    try:
                        item.unlink()
                        stats["skipped_identical"] += 1
                    except Exception:
                        stats["errors"] += 1
                else:
                    # keep both: make unique name next to tgt
                    new_tgt = unique_target_path(tgt)
                    try:
                        item.rename(new_tgt)
                        stats["renamed_conflict"] += 1
                    except Exception:
                        try:
                            shutil.copy2(item, new_tgt)
                            item.unlink(missing_ok=True)
                            stats["copied"] += 1
                        except Exception:
                            stats["errors"] += 1
            else:
                # dir vs file: just place with unique name in dst
                new_tgt = _unique_in_dir(dst_dir, item.name)
                try:
                    item.rename(new_tgt)
                    stats["renamed_conflict"] += 1
                except Exception:
                    try:
                        if item.is_dir():
                            shutil.copytree(item, new_tgt, dirs_exist_ok=True)
                            shutil.rmtree(item, ignore_errors=True)
                        else:
                            shutil.copy2(item, new_tgt)
                            item.unlink(missing_ok=True)
                        stats["copied"] += 1
                    except Exception:
                        stats["errors"] += 1
    finally:
        # try to clean src_dir if empty
        try:
            src_dir.rmdir()
        except Exception:
            pass

def apply_renames(plan: list[tuple[Path, Path, Path]], conflict_mode: str = CONFLICT_SUFFIX
                 ) -> list[tuple[Path, Path, Path, Path, str]]:
    """
    Returns list of tuples: (base, old, intended_new, actual_target, op)
    op in {"rename","conflict_unique","delete_then_rename","merge","merge_skip_identical","merge_unique","error"}
    """
    applied = []
    for base, old, intended_new in plan:
        try:
            if conflict_mode == CONFLICT_DELETE and intended_new.exists():
                # delete existing target before renaming
                if intended_new.is_dir():
                    shutil.rmtree(intended_new)
                else:
                    intended_new.unlink()
                actual_target = intended_new
                try:
                    old.rename(actual_target)
                    applied.append((base, old, intended_new, actual_target, "delete_then_rename"))
                except Exception:
                    # fallback
                    unique = unique_target_path(intended_new)
                    old.rename(unique)
                    applied.append((base, old, intended_new, unique, "conflict_unique"))
                continue

            if conflict_mode == CONFLICT_MERGE and intended_new.exists():
                # directory ↔ directory
                if old.is_dir() and intended_new.is_dir():
                    stats = {"moved":0, "copied":0, "renamed_conflict":0, "skipped_identical":0, "errors":0}
                    _merge_move(old, intended_new, stats)
                    # after merging, mark as merge
                    applied.append((base, old, intended_new, intended_new, "merge"))
                    continue
                # file ↔ file
                if old.is_file() and intended_new.is_file():
                    if _files_identical(old, intended_new):
                        # drop duplicate source
                        old.unlink(missing_ok=True)
                        applied.append((base, old, intended_new, intended_new, "merge_skip_identical"))
                    else:
                        unique = unique_target_path(intended_new)
                        old.rename(unique)
                        applied.append((base, old, intended_new, unique, "merge_unique"))
                    continue
                # mixed types → just place uniquely
                unique = unique_target_path(intended_new)
                old.rename(unique)
                applied.append((base, old, intended_new, unique, "conflict_unique"))
                continue

            # default and SUFFIX mode
            if intended_new.exists():
                unique = unique_target_path(intended_new)
                old.rename(unique)
                applied.append((base, old, intended_new, unique, "conflict_unique"))
            else:
                old.rename(intended_new)
                applied.append((base, old, intended_new, intended_new, "rename"))
        except Exception as e:
            print(f"[ERROR] Failed to process '{old}' -> '{intended_new}': {e}")
            applied.append((base, old, intended_new, old, "error"))
    return applied

def undo_renames(applied: list[tuple[Path, Path, Path, Path, str]]) -> list[tuple[Path, Path, str]]:
    """
    Returns list of tuples: (from_path, to_path, result)
    Only undoes ops that are safe single renames (no MERGE).
    """
    undone = []
    for base, old, intended, actual, op in sorted(applied, key=lambda t: len(t[3].parts), reverse=True):
        if op in {"merge", "merge_skip_identical", "merge_unique"}:
            undone.append((actual, actual, "skip_merge"))
            continue
        try:
            back_target = old if not old.exists() else unique_target_path(old)
            if actual.exists():
                actual.rename(back_target)
                undone.append((actual, back_target, "undone"))
            else:
                undone.append((actual, back_target, "missing_actual"))
        except Exception as e:
            print(f"[ERROR] Undo failed '{actual}' -> '{old}': {e}")
            undone.append((actual, old, "error"))
    return undone

def _kind_of(p: Path) -> str:
    if p.is_dir():
        return "DIR"
    if p.is_file():
        return "FILE"
    return "OTHER"


# --------- GUI ----------
class App(ttk.Frame):
    def __init__(self, master):
        super().__init__(master)
        self.master.title("Folder/File Renamer — Compact Toolbar (PharmApp)")
        self.pack(fill="both", expand=True)

        # State
        self.current_theme = tk.StringVar(value="macOS Graphite (Dark)")
        self.include_dirs = tk.BooleanVar(value=True)
        self.include_files = tk.BooleanVar(value=False)
        self.replace_space = tk.BooleanVar(value=True)
        self.depth_label = tk.StringVar(value="All levels")

        # Conflict handling mode
        self.conflict_label = tk.StringVar(value="Keep _1")
        self._deleted_targets_set: set[Path] = set()
        self._merge_targets_set: set[Path] = set()

        self.single_path_var = tk.StringVar()
        self.base_dirs: list[Path] = []

        self.preview_rows: list[tuple[Path, Path, Path]] = []
        self.applied_rows: list[tuple[Path, Path, Path, Path, str]] = []

        # Theme manager
        self.tm = ThemeManager(master)
        self.palette = self.tm.apply(self.current_theme.get())

        self._build_ui()
        self._setup_tree_tags()
        self._apply_palette_to_text_and_listbox()

    # ---------- UI ----------
    def _build_ui(self):
        # Row 0: TOP COMPACT BAR (Theme • Targets • Depth • Transform • Conflict)
        top = ttk.Frame(self); top.pack(fill="x", padx=10, pady=6)

        # Theme
        ttk.Label(top, text="Theme:").grid(row=0, column=0, sticky="e")
        self.theme_cbb = ttk.Combobox(top, state="readonly",
                                      values=list(ThemeManager.THEMES.keys()),
                                      textvariable=self.current_theme, width=24)
        self.theme_cbb.grid(row=0, column=1, sticky="w", padx=(6,6))
        ttk.Button(top, text="Apply", style="Pharm.TButton", command=self._apply_theme)\
            .grid(row=0, column=2, sticky="w")

        # Targets (Folders/Files)
        tgt = ttk.Frame(top); tgt.grid(row=0, column=3, sticky="w", padx=(16, 0))
        ttk.Checkbutton(tgt, text="Folders", variable=self.include_dirs).pack(side="left")
        ttk.Checkbutton(tgt, text="Files", variable=self.include_files).pack(side="left", padx=(8,0))

        # Depth combobox
        ttk.Label(top, text="Depth:").grid(row=0, column=4, sticky="e", padx=(16,0))
        self.depth_cbb = ttk.Combobox(top, state="readonly",
                                      values=list(DEPTH_LABEL_TO_CONST.keys()),
                                      textvariable=self.depth_label, width=16)
        self.depth_cbb.grid(row=0, column=5, sticky="w", padx=(6,6))

        # Transform checkbox
        ttk.Checkbutton(top, text="Space → '_'",
                        variable=self.replace_space).grid(row=0, column=6, sticky="w", padx=(12,0))

        # Conflict handling combobox (3 options)
        ttk.Label(top, text="On conflict:").grid(row=0, column=7, sticky="e", padx=(16,0))
        self.conflict_cbb = ttk.Combobox(
            top, state="readonly",
            values=["Keep _1", "Delete existing", "Merge into existing"],
            textvariable=self.conflict_label, width=20
        )
        self.conflict_cbb.grid(row=0, column=8, sticky="w", padx=(6,6))

        top.grid_columnconfigure(9, weight=1)

        # Row 1: BASE TOOLBAR (one line)
        bar = ttk.Frame(self); bar.pack(fill="x", padx=10, pady=(0,6))
        ttk.Label(bar, text="Path:").pack(side="left")
        self.single_entry = ttk.Entry(bar, textvariable=self.single_path_var, width=60)
        self.single_entry.pack(side="left", padx=(6,6))
        ttk.Button(bar, text="Add Path", style="Pharm.TButton", command=self._add_path_from_entry).pack(side="left", padx=(0,6))
        ttk.Button(bar, text="Add Windows…", style="Pharm.TButton", command=self._add_folder_dialog).pack(side="left", padx=(0,6))
        ttk.Button(bar, text="Add Multi…", style="Pharm.TButton", command=self._add_many_dialog).pack(side="left", padx=(0,6))
        ttk.Button(bar, text="Remove", style="Pharm.TButton", command=self._remove_selected_bases).pack(side="left", padx=(0,6))
        ttk.Button(bar, text="Clear", style="Pharm.TButton", command=self._clear_bases).pack(side="left", padx=(0,12))
        # Toggle Bulk Paste panel
        self._bulk_visible = False
        ttk.Button(bar, text="Bulk ▸", style="Pharm.TButton", command=self._toggle_bulk_box).pack(side="left", padx=(0,18))
        # Actions on same line
        ttk.Button(bar, text="Preview", style="Pharm.TButton", command=self._preview).pack(side="left")
        ttk.Button(bar, text="Rename", style="Pharm.TButton", command=self._rename).pack(side="left", padx=(6,0))
        ttk.Button(bar, text="Undo", style="Pharm.TButton", command=self._undo_last).pack(side="left", padx=(6,0))
        ttk.Button(bar, text="Save CSV", style="Pharm.TButton", command=self._save_csv).pack(side="left", padx=(6,0))

        # Row 2: BULK PASTE (hidden by default)
        bulk_wrap = ttk.Frame(self); bulk_wrap.pack(fill="x", padx=10)
        self.bulk_frame = bulk_wrap  # store
        ttk.Label(bulk_wrap, text="Bulk Paste (one per line or ';'):").grid(row=0, column=0, sticky="w")
        self.bulk_text = tk.Text(bulk_wrap, height=3, width=80)
        self.bulk_text.grid(row=0, column=1, sticky="we", padx=(6,6))
        ttk.Button(bulk_wrap, text="Add From Box", style="Pharm.TButton", command=self._add_paths_from_text)\
            .grid(row=0, column=2, sticky="w")
        bulk_wrap.grid_columnconfigure(1, weight=1)
        self.bulk_frame.pack_forget()  # Hide initially

        # Row 3: BASE LIST (compact)
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

        # Footer (compact)
        foot = ttk.Frame(self); foot.pack(fill="x", padx=10, pady=(0,6))
        self.status_lbl = ttk.Label(foot, text=f"Script: {SCRIPT_NAME} • Theme: {self.current_theme.get()}")
        self.status_lbl.pack(side="left")

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
            self.tree.tag_configure("deleted", background=pal["selection_bg"])
            self.tree.tag_configure("merged", background=pal["selection_bg"])
        except Exception:
            pass

    def _apply_palette_to_text_and_listbox(self):
        pal = self.palette
        try:
            self.bulk_text.configure(bg=pal["input_bg"], fg=pal["input_fg"], insertbackground=pal["input_fg"])
            self.base_listbox.configure(bg=pal["input_bg"], fg=pal["input_fg"],
                                        selectbackground=pal["selection_bg"])
        except Exception:
            pass

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

    # ---------- Tree helpers ----------
    def _clear_tree(self):
        for iid in self.tree.get_children():
            self.tree.delete(iid)

    # ---------- Preview / Rename / Undo / CSV ----------
    def _depth_mode(self) -> str:
        return DEPTH_LABEL_TO_CONST.get(self.depth_label.get(), DEPTH_ALL)

    def _conflict_mode(self) -> str:
        val = self.conflict_label.get()
        if val == "Delete existing":
            return CONFLICT_DELETE
        if val == "Merge into existing":
            return CONFLICT_MERGE
        return CONFLICT_SUFFIX  # Keep _1

    def _preview(self):
        if not self.base_dirs:
            messagebox.showwarning("Warning", "Please add at least one base folder.")
            return
        if not self.include_dirs.get() and not self.include_files.get():
            messagebox.showwarning("Warning", "Select at least one target: Folders or Files.")
            return

        self._clear_tree()
        items = collect_paths_for_bases(self.base_dirs,
                                        self._depth_mode(),
                                        self.include_dirs.get(),
                                        self.include_files.get())
        plan = compute_plan(items, self.replace_space.get())
        self.preview_rows = plan
        if not plan:
            self.tree.insert("", "end", values=("", "", "(unchanged)", "No changes", ""), tags=("info",))
            return
        for base, old, new in sorted(plan, key=lambda t: (str(t[0]).lower(), str(t[1]).lower())):
            self.tree.insert("", "end",
                             values=(str(base), _kind_of(old), str(old), str(new), "Preview"),
                             tags=("preview",))

    def _rename(self):
        if not self.preview_rows:
            if not self._confirm_scan_then_rename():
                return

        # Pre-count for confirmations
        self._deleted_targets_set = set()
        self._merge_targets_set = set()
        mode = self._conflict_mode()
        conflicts = [intended for _, _, intended in self.preview_rows if intended.exists()]
        if conflicts and mode == CONFLICT_DELETE:
            msg = (f"Detected {len(conflicts)} existing path(s) that will be DELETED "
                   f"before renaming.\n\nProceed?")
            if not messagebox.askyesno("Confirm delete on conflict", msg):
                return
            self._deleted_targets_set = set(conflicts)
        if conflicts and mode == CONFLICT_MERGE:
            msg = (f"Detected {len(conflicts)} existing path(s) that will be MERGED into.\n"
                   f"- Folders: contents merged recursively\n"
                   f"- Files: identical skipped, different keep both (_1)\n\nProceed?")
            if not messagebox.askyesno("Confirm merge on conflict", msg):
                return
            self._merge_targets_set = set(conflicts)

        applied = apply_renames(self.preview_rows, conflict_mode=mode)
        self.applied_rows = applied
        self._clear_tree()
        if not applied:
            self.tree.insert("", "end", values=("", "", "", "Nothing renamed", ""), tags=("info",))
            return

        merged_cnt = 0
        deleted_cnt = len(self._deleted_targets_set)
        renamed_cnt = 0
        unique_cnt = 0
        skipped_identical = 0

        for base, old, intended, actual, op in sorted(applied, key=lambda t: (str(t[0]).lower(), str(t[1]).lower())):
            if op == "merge":
                status = "Merged into existing (folder)"
                tag = "merged"; merged_cnt += 1
            elif op == "merge_skip_identical":
                status = "Skipped (identical file, merge)"
                tag = "merged"; skipped_identical += 1
            elif op == "merge_unique":
                status = "Kept both (file → _1, merge)"
                tag = "conflict"; unique_cnt += 1
            elif op == "delete_then_rename":
                status = "Renamed (deleted existing target)"
                tag = "deleted"; renamed_cnt += 1
            elif op == "conflict_unique":
                status = "Renamed (conflict ➜ unique path)"
                tag = "conflict"; unique_cnt += 1
            elif op == "rename":
                status = "Renamed"
                tag = "renamed"; renamed_cnt += 1
            else:
                status = "Error"
                tag = "conflict"
            self.tree.insert("", "end",
                             values=(str(base), _kind_of(old), str(old), str(actual), status),
                             tags=(tag,))

        summary = (f"Renamed: {renamed_cnt} • Unique(_1): {unique_cnt} • "
                   f"Merged: {merged_cnt} • Deleted-before-rename: {deleted_cnt} • "
                   f"Skipped identical: {skipped_identical}")
        messagebox.showinfo("Done", summary)

    def _confirm_scan_then_rename(self) -> bool:
        if not self.base_dirs:
            messagebox.showwarning("Warning", "Please add at least one base folder.")
            return False
        if not self.include_dirs.get() and not self.include_files.get():
            messagebox.showwarning("Warning", "Select at least one target: Folders or Files.")
            return False
        items = collect_paths_for_bases(self.base_dirs,
                                        self._depth_mode(),
                                        self.include_dirs.get(),
                                        self.include_files.get())
        plan = compute_plan(items, self.replace_space.get())
        self.preview_rows = plan
        if not plan:
            messagebox.showinfo("Info", "No items need renaming.")
            return False
        return messagebox.askyesno("Confirm",
                                   f"Found {len(plan)} item(s) to rename across {len(self.base_dirs)} base folder(s). Proceed?")

    def _undo_last(self):
        if not self.applied_rows:
            messagebox.showinfo("Undo", "Nothing to undo in this session.")
            return
        undone = undo_renames(self.applied_rows)
        count_undone = sum(1 for _, _, res in undone if res == "undone")
        count_skips = sum(1 for _, _, res in undone if res == "skip_merge")
        self._clear_tree()
        for src, dst, res in sorted(undone, key=lambda t: str(t[0]).lower()):
            label = "Undone" if res == "undone" else ("Skip (merge)" if res == "skip_merge" else res)
            self.tree.insert("", "end",
                             values=("", _kind_of(dst), str(src), str(dst), label),
                             tags=("undo",))
        messagebox.showinfo("Undo", f"Undone {count_undone} item(s). Merged items cannot be fully undone ({count_skips} skipped).")
        self.applied_rows.clear()

    def _save_csv(self):
        if not self.preview_rows and not self.applied_rows:
            messagebox.showinfo("Save CSV", "No data to save. Run Preview or Rename first.")
            return
        fp = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv")],
            title="Save mapping CSV"
        )
        if not fp:
            return
        headers = ["base", "kind", "current_path", "intended_new_path", "actual_new_path_or_preview", "op"]
        rows = []
        if self.applied_rows:
            for base, old, intended, actual, op in self.applied_rows:
                rows.append((str(base), _kind_of(old), str(old), str(intended), str(actual), op))
        else:
            for base, old, intended in self.preview_rows:
                rows.append((str(base), _kind_of(old), str(old), str(intended), "(preview)", "preview"))
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
    root.minsize(1100, 620)
    root.mainloop()

if __name__ == "__main__":
    main()
