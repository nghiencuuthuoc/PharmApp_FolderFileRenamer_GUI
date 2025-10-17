#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FolderFileRenamer_GUI.py — Multi Base Folders, Themes, Depth, Files/Folders
Rules:
  * '-' -> '_'
  * (optional) ' ' -> '_'
  * Remove Vietnamese diacritics (đ/Đ -> D)
  * Uppercase all letters

Features:
  - Multiple Base Folders (list): Add Path, Add From Box, Add Windows…, Add Multi…, Remove, Clear
  - Targets: Folders, Files, or Both
  - Depth options: Level 1 only, Level 2 only, Up to Level 2, All levels
  - Theme switcher: PharmApp Light, Nord Light, Midnight Teal (Dark), Solar Slate, macOS Graphite (Dark)
  - Preview before apply, collision-safe (_1, _2, ...)
  - Undo last batch (this session)
  - Save mapping to CSV (Base/Kind/Current/Intended/Actual)

UI: bilingual (EN/VI)
"""

import csv
import unicodedata
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

        # Window background
        self.root.configure(bg=bg)
        # Tk options
        self.root.option_add("*Foreground", fg)
        self.root.option_add("*Background", bg)

        # Base widgets
        self.style.configure("TFrame", background=bg)
        self.style.configure("TLabelframe", background=bg, foreground=fg, font=("Arial", 11, "bold"))
        self.style.configure("TLabelframe.Label", background=bg, foreground=fg)
        self.style.configure("TLabel", background=bg, foreground=fg, font=("Arial", 11))
        self.style.configure("Pharm.TButton", font=("Arial", 10, "bold"), padding=6)
        self.style.map("Pharm.TButton",
                       background=[("active", btn_active), ("pressed", btn_active)],
                       foreground=[("disabled", "#888888")])
        self.style.configure("Pharm.TButton", background=btn_bg, foreground=btn_fg)

        # Inputs
        self.style.configure("TEntry", fieldbackground=input_bg, foreground=input_fg, padding=4)
        self.style.configure("TCombobox", fieldbackground=input_bg, foreground=input_fg, padding=2)
        self.style.map("TCombobox",
                       fieldbackground=[("readonly", input_bg)],
                       foreground=[("readonly", input_fg)])
        self.style.configure("TCheckbutton", background=bg, foreground=fg)
        self.style.configure("TRadiobutton", background=bg, foreground=fg)

        # Treeview
        self.style.configure("Treeview",
                             background=table_bg,
                             fieldbackground=table_bg,
                             foreground=fg,
                             rowheight=25,
                             font=("Arial", 10))
        self.style.configure("Treeview.Heading",
                             font=("Arial", 10, "bold"),
                             foreground="#FFFFFF",
                             background=head_bg)
        self.style.map("Treeview.Heading",
                       background=[("active", head_bg), ("pressed", head_bg)])

        # Accent separators (where supported)
        self.style.configure("TSeparator", background=pal["accent"])

        # Combobox dropdown / listbox colors
        try:
            self.root.option_add("*Listbox*Background", input_bg)
            self.root.option_add("*Listbox*Foreground", input_fg)
            self.root.option_add("*Listbox*selectBackground", sel_bg)
        except Exception:
            pass

        return pal  # return palette to allow tag coloring


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

def _rel_depth(base: Path, p: Path) -> int:
    return len(p.relative_to(base).parts)

def collect_paths_for_bases(base_dirs: list[Path], depth_mode: str,
                            include_dirs: bool, include_files: bool) -> list[tuple[Path, Path]]:
    """
    Return list of (base, path) for all base_dirs, filtered by depth & kind.
    Sorted deepest-first overall so children rename before parents.
    """
    results: list[tuple[Path, Path]] = []
    for base_dir in base_dirs:
        if not base_dir.exists() or not base_dir.is_dir():
            continue
        all_paths = list(base_dir.rglob("*"))  # includes files & dirs
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
            # DEPTH_ALL: accept all with d>=1
            results.append((base_dir, p))
    # Deepest-first overall
    results.sort(key=lambda t: len(t[1].parts), reverse=True)
    return results

def compute_plan(items: list[tuple[Path, Path]], replace_space: bool) -> list[tuple[Path, Path, Path]]:
    """
    items: list of (base, current_path)
    returns: list of (base, old_path, intended_new_path)
    """
    plan = []
    for base, p in items:
        new_name = transform_name(p.name, replace_space)
        if new_name != p.name:
            plan.append((base, p, p.with_name(new_name)))
    return plan

def apply_renames(plan: list[tuple[Path, Path, Path]]) -> list[tuple[Path, Path, Path, Path]]:
    """
    plan: (base, old, intended)
    return applied: (base, old, intended, actual)
    """
    applied = []
    for base, old, intended_new in plan:
        try:
            actual_target = intended_new if not intended_new.exists() else unique_target_path(intended_new)
            old.rename(actual_target)
            applied.append((base, old, intended_new, actual_target))
        except Exception as e:
            print(f"[ERROR] Failed to rename '{old}' -> '{intended_new}': {e}")
    return applied

def undo_renames(applied: list[tuple[Path, Path, Path, Path]]) -> list[tuple[Path, Path]]:
    """
    Undo safely: rename deepest items first, then parents.
    Returns list of (src_actual, dst_back)
    """
    undone = []
    for base, old, intended, actual in sorted(applied, key=lambda t: len(t[3].parts), reverse=True):
        try:
            back_target = old if not old.exists() else unique_target_path(old)
            actual.rename(back_target)
            undone.append((actual, back_target))
        except Exception as e:
            print(f"[ERROR] Undo failed '{actual}' -> '{old}': {e}")
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
        self.master.title("Folder/File Renamer — Multi Base Folders, Depth, Kind & Themes (PharmApp)")
        self.pack(fill="both", expand=True)

        # State
        self.depth_mode = tk.StringVar(value=DEPTH_ALL)
        self.include_dirs = tk.BooleanVar(value=True)   # default: folders
        self.include_files = tk.BooleanVar(value=False) # default: not files
        self.replace_space = tk.BooleanVar(value=True)  # default: replace ' ' -> '_'
        self.current_theme = tk.StringVar(value="macOS Graphite (Dark)")  # default dark
        self.single_path_var = tk.StringVar()

        self.base_dirs: list[Path] = []  # list of Path
        self.preview_rows: list[tuple[Path, Path, Path]] = []            # (base, old, intended)
        self.applied_rows: list[tuple[Path, Path, Path, Path]] = []      # (base, old, intended, actual)

        # Theme manager
        self.tm = ThemeManager(master)
        pal = self.tm.apply(self.current_theme.get())
        self.palette = pal

        self._build_ui()
        self._setup_tree_tags()
        self._apply_palette_to_text_and_listbox()

    # ---------- UI ----------
    def _build_ui(self):
        # Top bar: Theme switcher
        top = ttk.Frame(self); top.pack(fill="x", padx=10, pady=10)

        ttk.Label(top, text="Theme:").grid(row=0, column=0, sticky="e")
        self.theme_cbb = ttk.Combobox(top, state="readonly", values=list(ThemeManager.THEMES.keys()),
                                      textvariable=self.current_theme, width=26)
        self.theme_cbb.grid(row=0, column=1, sticky="w", padx=(6,6))
        ttk.Button(top, text="Apply", style="Pharm.TButton", command=self._apply_theme).grid(row=0, column=2, sticky="w")
        top.grid_columnconfigure(3, weight=1)

        # Base folders manager
        base_frame = ttk.Labelframe(self, text="Base Folders / Thư mục gốc (multi)"); base_frame.pack(fill="x", padx=10, pady=(0,8))

        # Row 1: Single path entry + Add Path
        ttk.Label(base_frame, text="Single Path:").grid(row=0, column=0, sticky="w", padx=(8,4), pady=(6,2))
        self.single_entry = ttk.Entry(base_frame, textvariable=self.single_path_var, width=70)
        self.single_entry.grid(row=0, column=1, sticky="we", padx=(0,6), pady=(6,2))
        ttk.Button(base_frame, text="Add Path", style="Pharm.TButton", command=self._add_path_from_entry)\
            .grid(row=0, column=2, sticky="w", padx=(0,6), pady=(6,2))

        # Row 2: Bulk paste box + Add From Box
        ttk.Label(base_frame, text="Bulk Paste (one/line or ';'):").grid(row=1, column=0, sticky="nw", padx=(8,4))
        self.bulk_text = tk.Text(base_frame, height=4, width=70)
        self.bulk_text.grid(row=1, column=1, sticky="we", padx=(0,6))
        ttk.Button(base_frame, text="Add From Box", style="Pharm.TButton", command=self._add_paths_from_text)\
            .grid(row=1, column=2, sticky="nw", padx=(0,6))

        # Row 3: Buttons Add Windows…, Add Multi…, Remove, Clear
        btns = ttk.Frame(base_frame); btns.grid(row=2, column=0, columnspan=3, sticky="w", padx=8, pady=(6,6))
        ttk.Button(btns, text="Add Windows…", style="Pharm.TButton", command=self._add_folder_dialog).pack(side="left", padx=(0,6))
        ttk.Button(btns, text="Add Multi…", style="Pharm.TButton", command=self._add_many_dialog).pack(side="left", padx=(0,6))
        ttk.Button(btns, text="Remove", style="Pharm.TButton", command=self._remove_selected_bases).pack(side="left", padx=(0,6))
        ttk.Button(btns, text="Clear", style="Pharm.TButton", command=self._clear_bases).pack(side="left", padx=(0,6))

        # Row 4: Listbox of base dirs + scrollbar
        self.base_listbox = tk.Listbox(base_frame, height=6, selectmode="extended")
        self.base_listbox.grid(row=3, column=0, columnspan=3, sticky="nsew", padx=8, pady=(0,8))
        base_scroll = ttk.Scrollbar(base_frame, orient="vertical", command=self.base_listbox.yview)
        base_scroll.grid(row=3, column=3, sticky="ns", pady=(0,8))
        self.base_listbox.configure(yscrollcommand=base_scroll.set)

        base_frame.grid_columnconfigure(1, weight=1)
        base_frame.grid_rowconfigure(3, weight=1)

        # Target Kind
        kind_frame = ttk.Labelframe(self, text="Target / Đối tượng đổi tên"); kind_frame.pack(fill="x", padx=10)
        ttk.Checkbutton(kind_frame, text="Folders / Thư mục", variable=self.include_dirs).pack(side="left", padx=(6,12))
        ttk.Checkbutton(kind_frame, text="Files / Tập tin", variable=self.include_files).pack(side="left", padx=(0,12))

        # Depth options
        depth_frame = ttk.Labelframe(self, text="Depth / Cấp thư mục"); depth_frame.pack(fill="x", padx=10, pady=(6,0))
        ttk.Radiobutton(depth_frame, text="Level 1 only (Chỉ Cấp 1)", value=DEPTH_LEVEL1_ONLY,
                        variable=self.depth_mode).pack(side="left", padx=(6,12))
        ttk.Radiobutton(depth_frame, text="Level 2 only (Chỉ Cấp 2)", value=DEPTH_LEVEL2_ONLY,
                        variable=self.depth_mode).pack(side="left", padx=(0,12))
        ttk.Radiobutton(depth_frame, text="Up to Level 2 (Tới Cấp 2)", value=DEPTH_UP_TO_LEVEL2,
                        variable=self.depth_mode).pack(side="left", padx=(0,12))
        ttk.Radiobutton(depth_frame, text="All levels (Tất cả cấp)", value=DEPTH_ALL,
                        variable=self.depth_mode).pack(side="left", padx=(0,12))

        # Transform options
        tx_frame = ttk.Labelframe(self, text="Transform / Quy tắc đổi tên"); tx_frame.pack(fill="x", padx=10, pady=(6,0))
        ttk.Label(tx_frame, text="Always: '-' → '_' • Remove accents • Uppercase").pack(side="left", padx=(6,12))
        ttk.Checkbutton(tx_frame, text="Replace space with '_' (Thay khoảng trắng bằng '_')",
                        variable=self.replace_space).pack(side="left")

        # Actions
        actions = ttk.Frame(self); actions.pack(fill="x", padx=10, pady=(8,6))
        ttk.Button(actions, text="Preview / Xem trước", style="Pharm.TButton",
                   command=self._preview).pack(side="left")
        ttk.Button(actions, text="Rename / Đổi tên", style="Pharm.TButton",
                   command=self._rename).pack(side="left", padx=(6,0))
        ttk.Button(actions, text="Undo Last / Hoàn tác", style="Pharm.TButton",
                   command=self._undo_last).pack(side="left", padx=(6,0))
        ttk.Button(actions, text="Save CSV Map", style="Pharm.TButton",
                   command=self._save_csv).pack(side="left", padx=(6,0))

        # Table
        table_frame = ttk.Frame(self); table_frame.pack(fill="both", expand=True, padx=10, pady=(6,10))
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
        foot = ttk.Frame(self); foot.pack(fill="x", padx=10, pady=(0,10))
        self.status_lbl = ttk.Label(foot, text=f"Script: {SCRIPT_NAME} • Theme: {self.current_theme.get()}")
        self.status_lbl.pack(side="left")

    def _apply_theme(self):
        pal = self.tm.apply(self.current_theme.get())
        self.palette = pal
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
        if path is None:
            return
        if path in self.base_dirs:
            return
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
        # remove from end to start
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
    def _preview(self):
        if not self.base_dirs:
            messagebox.showwarning("Warning", "Please add at least one base folder.")
            return
        if not self.include_dirs.get() and not self.include_files.get():
            messagebox.showwarning("Warning", "Select at least one target: Folders or Files.")
            return

        self._clear_tree()
        items = collect_paths_for_bases(self.base_dirs,
                                        self.depth_mode.get(),
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
        applied = apply_renames(self.preview_rows)
        self.applied_rows = applied
        self._clear_tree()
        if not applied:
            self.tree.insert("", "end", values=("", "", "", "Nothing renamed", ""), tags=("info",))
            return
        for base, old, intended, actual in sorted(applied, key=lambda t: (str(t[0]).lower(), str(t[1]).lower())):
            status = "Renamed" if actual == intended else "Renamed (conflict ➜ unique path)"
            tag = "renamed" if actual == intended else "conflict"
            self.tree.insert("", "end",
                             values=(str(base), _kind_of(old), str(old), str(actual), status),
                             tags=(tag,))
        messagebox.showinfo("Done", f"Renamed {len(applied)} item(s).")

    def _confirm_scan_then_rename(self) -> bool:
        if not self.base_dirs:
            messagebox.showwarning("Warning", "Please add at least one base folder.")
            return False
        if not self.include_dirs.get() and not self.include_files.get():
            messagebox.showwarning("Warning", "Select at least one target: Folders or Files.")
            return False
        items = collect_paths_for_bases(self.base_dirs,
                                        self.depth_mode.get(),
                                        self.include_dirs.get(),
                                        self.include_files.get())
        plan = compute_plan(items, self.replace_space.get())
        self.preview_rows = plan
        if not plan:
            messagebox.showinfo("Info", "No items need renaming.")
            return False
        return messagebox.askyesno("Confirm", f"Found {len(plan)} item(s) to rename across {len(self.base_dirs)} base folder(s). Proceed?")

    def _undo_last(self):
        if not self.applied_rows:
            messagebox.showinfo("Undo", "Nothing to undo in this session.")
            return
        undone = undo_renames(self.applied_rows)
        count = len(undone)
        self._clear_tree()
        for src, dst in sorted(undone, key=lambda t: str(t[0]).lower()):
            self.tree.insert("", "end",
                             values=("", _kind_of(dst), str(src), str(dst), "Undone"),
                             tags=("undo",))
        self.applied_rows.clear()
        messagebox.showinfo("Undo", f"Undone {count} item(s).")

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
        headers = ["base", "kind", "current_path", "intended_new_path", "actual_new_path_or_preview"]
        rows = []
        if self.applied_rows:
            for base, old, intended, actual in self.applied_rows:
                rows.append((str(base), _kind_of(old), str(old), str(intended), str(actual)))
        else:
            for base, old, intended in self.preview_rows:
                rows.append((str(base), _kind_of(old), str(old), str(intended), "(preview)"))
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
    root.minsize(1180, 680)
    root.mainloop()

if __name__ == "__main__":
    main()
