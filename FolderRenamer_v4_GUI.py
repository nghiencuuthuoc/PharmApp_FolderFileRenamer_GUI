#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FolderFileRenamer_GUI.py
- Rename FOLDERS/FILES with rules:
  * '-' -> '_'
  * (optional) ' ' -> '_'
  * Remove Vietnamese diacritics (đ/Đ -> D)
  * Uppercase all letters

Features:
- Choose targets: Folders, Files, or Both
- Depth options: Level 1 only, Level 2 only, Up to Level 2, All levels
- Theme switcher: PharmApp Light, Nord Light, Midnight Teal (Dark), Solar Slate
- Preview before apply, collision-safe (_1, _2, ...)
- Undo last batch (this session)
- Save mapping to CSV (Kind/Current/Intended/Actual)

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
            "button_bg": "#f4a261", "button_active": "#e76f51",
            "accent": "#e9c46a", "heading_bg": "#b5838d",
            "selection_bg": "#e9c46a", "input_bg": "#ffffff", "input_fg": "#2a2a2a",
            "row_alt": "#fff9f0"
        },
        "Nord Light": {
            "bg": "#ECEFF4", "fg": "#2E3440",
            "button_bg": "#81A1C1", "button_active": "#5E81AC",
            "accent": "#88C0D0", "heading_bg": "#5E81AC",
            "selection_bg": "#D8DEE9", "input_bg": "#FFFFFF", "input_fg": "#2E3440",
            "row_alt": "#F5F7FA"
        },
        "Midnight Teal (Dark)": {
            "bg": "#0f172a", "fg": "#e2e8f0",
            "button_bg": "#0ea5e9", "button_active": "#0284c7",
            "accent": "#14b8a6", "heading_bg": "#0ea5e9",
            "selection_bg": "#334155", "input_bg": "#111827", "input_fg": "#e5e7eb",
            "row_alt": "#0b1224"
        },
        "Solar Slate": {
            "bg": "#f6f7f9", "fg": "#1f2937",
            "button_bg": "#f59e0b", "button_active": "#d97706",
            "accent": "#fbbf24", "heading_bg": "#374151",
            "selection_bg": "#e5e7eb", "input_bg": "#ffffff", "input_fg": "#1f2937",
            "row_alt": "#f3f4f6"
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
        sel_bg = pal["selection_bg"]
        input_bg, input_fg = pal["input_bg"], pal["input_fg"]

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
        self.style.configure("Pharm.TButton", background=btn_bg, foreground="#000000")

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
                             background="#FFFFFF" if theme_name != "Midnight Teal (Dark)" else "#0b1224",
                             fieldbackground="#FFFFFF" if theme_name != "Midnight Teal (Dark)" else "#0b1224",
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

        # For users using dark theme: force listbox colors (combobox dropdown)
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

def collect_paths_by_depth(base_dir: Path, depth_mode: str,
                           include_dirs: bool, include_files: bool) -> list[Path]:
    """
    Returns selected paths under base_dir filtered by depth:
    - LEVEL1_ONLY: depth == 1
    - LEVEL2_ONLY: depth == 2
    - UP_TO_LEVEL2: depth in {1, 2}
    - ALL: depth >= 1
    Also filters by kind: dirs/files.
    Sorted deepest-first so children (files/subdirs) rename before parents.
    """
    if not base_dir.exists() or not base_dir.is_dir():
        return []
    all_paths = list(base_dir.rglob("*"))  # includes both files and dirs
    filtered = []
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
        filtered.append(p)

    # Deepest-first
    return sorted(filtered, key=lambda p: len(p.parts), reverse=True)

def compute_plan(paths: list[Path], replace_space: bool) -> list[tuple[Path, Path]]:
    plan = []
    for p in paths:
        new_name = transform_name(p.name, replace_space)
        if new_name != p.name:
            plan.append((p, p.with_name(new_name)))
    return plan

def apply_renames(plan: list[tuple[Path, Path]]) -> list[tuple[Path, Path, Path]]:
    applied = []
    for old, intended_new in plan:
        try:
            actual_target = intended_new if not intended_new.exists() else unique_target_path(intended_new)
            old.rename(actual_target)
            applied.append((old, intended_new, actual_target))
        except Exception as e:
            print(f"[ERROR] Failed to rename '{old}' -> '{intended_new}': {e}")
    return applied

def undo_renames(applied: list[tuple[Path, Path, Path]]) -> list[tuple[Path, Path]]:
    """
    Undo safely: rename deepest items first, then parents.
    """
    undone = []
    for old, intended, actual in sorted(applied, key=lambda t: len(t[2].parts), reverse=True):
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
        self.master.title("Folder/File Renamer — Depth, Kind & Themes (PharmApp)")
        self.pack(fill="both", expand=True)

        # State
        self.selected_dir = tk.StringVar()
        self.depth_mode = tk.StringVar(value=DEPTH_ALL)
        self.include_dirs = tk.BooleanVar(value=True)   # default: folders
        self.include_files = tk.BooleanVar(value=False) # default: not files
        self.replace_space = tk.BooleanVar(value=True)  # default: replace ' ' -> '_'
        self.current_theme = tk.StringVar(value="PharmApp Light")

        self.preview_rows: list[tuple[Path, Path]] = []
        self.applied_rows: list[tuple[Path, Path, Path]] = []

        # Theme manager must be created before building UI, so styles exist
        self.tm = ThemeManager(master)
        pal = self.tm.apply(self.current_theme.get())
        self.palette = pal  # store for tag colors

        self._build_ui()
        self._setup_tree_tags()

    def _build_ui(self):
        # Top bar: Base folder + Theme switcher
        top = ttk.Frame(self); top.pack(fill="x", padx=10, pady=10)

        ttk.Label(top, text="Base Folder / Thư mục gốc:").grid(row=0, column=0, sticky="w")
        e = ttk.Entry(top, textvariable=self.selected_dir, width=60)
        e.grid(row=0, column=1, sticky="we", padx=(6,6))
        ttk.Button(top, text="Browse…", style="Pharm.TButton", command=self._browse).grid(row=0, column=2, sticky="w", padx=(0,10))

        ttk.Label(top, text="Theme:").grid(row=0, column=3, sticky="e")
        self.theme_cbb = ttk.Combobox(top, state="readonly", values=list(ThemeManager.THEMES.keys()),
                                      textvariable=self.current_theme, width=20)
        self.theme_cbb.grid(row=0, column=4, sticky="w", padx=(6,6))
        ttk.Button(top, text="Apply", style="Pharm.TButton", command=self._apply_theme).grid(row=0, column=5, sticky="w")

        top.grid_columnconfigure(1, weight=1)

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
        cols = ("kind", "current", "new", "status")
        self.tree = ttk.Treeview(table_frame, columns=cols, show="headings", selectmode="browse")
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
        self.status_lbl.config(text=f"Script: {SCRIPT_NAME} • Theme: {self.current_theme.get()}")

    def _setup_tree_tags(self):
        # Color-coded rows by status using theme palette
        pal = self.palette
        try:
            self.tree.tag_configure("preview", background=pal["row_alt"])
            self.tree.tag_configure("renamed", background=pal["accent"])
            self.tree.tag_configure("conflict", background=pal["selection_bg"])
            self.tree.tag_configure("undo", background=pal["row_alt"])
            self.tree.tag_configure("info", background=pal["row_alt"])
        except Exception:
            pass

    # ---- Actions ----
    def _browse(self):
        d = filedialog.askdirectory(title="Select base folder")
        if d:
            self.selected_dir.set(d)

    def _clear_tree(self):
        for iid in self.tree.get_children():
            self.tree.delete(iid)

    def _preview(self):
        base = Path(self.selected_dir.get().strip())
        if not base.exists() or not base.is_dir():
            messagebox.showwarning("Warning", "Please choose a valid base folder / Chọn thư mục hợp lệ.")
            return
        if not self.include_dirs.get() and not self.include_files.get():
            messagebox.showwarning("Warning", "Select at least one target: Folders or Files.")
            return

        self._clear_tree()
        paths = collect_paths_by_depth(base,
                                       self.depth_mode.get(),
                                       self.include_dirs.get(),
                                       self.include_files.get())
        plan = compute_plan(paths, self.replace_space.get())
        self.preview_rows = plan
        if not plan:
            self.tree.insert("", "end", values=("", str(base), "(unchanged)", "No changes"), tags=("info",))
            return
        for old, new in sorted(plan, key=lambda t: str(t[0]).lower()):
            self.tree.insert("", "end",
                             values=(_kind_of(old), str(old), str(new), "Preview"),
                             tags=("preview",))

    def _rename(self):
        if not self.preview_rows:
            if not self._confirm_scan_then_rename():
                return
        applied = apply_renames(self.preview_rows)
        self.applied_rows = applied
        self._clear_tree()
        if not applied:
            self.tree.insert("", "end", values=("", "", "", "Nothing renamed"), tags=("info",))
            return
        for old, intended, actual in sorted(applied, key=lambda t: str(t[0]).lower()):
            status = "Renamed" if actual == intended else "Renamed (conflict ➜ unique path)"
            tag = "renamed" if actual == intended else "conflict"
            self.tree.insert("", "end", values=(_kind_of(old), str(old), str(actual), status), tags=(tag,))
        messagebox.showinfo("Done", f"Renamed {len(applied)} item(s).")

    def _confirm_scan_then_rename(self) -> bool:
        base = Path(self.selected_dir.get().strip())
        if not base.exists() or not base.is_dir():
            messagebox.showwarning("Warning", "Please choose a valid base folder / Chọn thư mục hợp lệ.")
            return False
        if not self.include_dirs.get() and not self.include_files.get():
            messagebox.showwarning("Warning", "Select at least one target: Folders or Files.")
            return False
        paths = collect_paths_by_depth(base,
                                       self.depth_mode.get(),
                                       self.include_dirs.get(),
                                       self.include_files.get())
        plan = compute_plan(paths, self.replace_space.get())
        self.preview_rows = plan
        if not plan:
            messagebox.showinfo("Info", "No items need renaming.")
            return False
        msg = f"Found {len(plan)} item(s) to rename at selected depth. Proceed?"
        return messagebox.askyesno("Confirm", msg)

    def _undo_last(self):
        if not self.applied_rows:
            messagebox.showinfo("Undo", "Nothing to undo in this session.")
            return
        undone = undo_renames(self.applied_rows)
        count = len(undone)
        self._clear_tree()
        for src, dst in sorted(undone, key=lambda t: str(t[0]).lower()):
            self.tree.insert("", "end",
                             values=(_kind_of(dst), str(src), str(dst), "Undone"),
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
        headers = ["kind", "current_path", "intended_new_path", "actual_new_path_or_preview"]
        rows = []
        if self.applied_rows:
            for old, intended, actual in self.applied_rows:
                rows.append((_kind_of(old), str(old), str(intended), str(actual)))
        else:
            for old, intended in self.preview_rows:
                rows.append((_kind_of(old), str(old), str(intended), "(preview)"))
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
    root.minsize(1040, 600)
    root.mainloop()

if __name__ == "__main__":
    main()
