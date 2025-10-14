#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FolderRenamer_GUI.py (Files/Folders + Space->Underscore options)
Rules:
- '-' -> '_'
- (Optional) ' ' -> '_'
- Remove Vietnamese diacritics (đ/Đ -> D)
- Uppercase all letters

New:
- Choose targets: Folders, Files, or Both
- Depth options: Level 1 only, Level 2 only, Up to Level 2, All levels

Features:
- Choose base directory
- Preview before apply
- Collision-safe renames (_1, _2, ...)
- Undo last batch (this session)
- Save mapping to CSV
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
    SCRIPT_NAME = "FolderRenamer_GUI.py"
print(f"[INFO] Running: {SCRIPT_NAME}")

# --------- PharmApp Theme ----------
def apply_pharmapp_theme(root: tk.Tk):
    root.configure(bg="#fdf5e6")
    style = ttk.Style(root)
    try:
        style.theme_use("default")
    except tk.TclError:
        pass

    bg = "#fdf5e6"
    fg = "#2a2a2a"
    head_bg = "#b5838d"

    root.option_add("*Foreground", fg)
    root.option_add("*Background", bg)

    style.configure("TFrame", background=bg)
    style.configure("TLabel", background=bg, foreground=fg, font=("Arial", 11))
    style.configure("Pharm.TButton", font=("Arial", 10, "bold"))
    style.map("Pharm.TButton", background=[("active", "#e76f51")])

    style.configure("Treeview",
                    background="white",
                    fieldbackground="white",
                    foreground=fg,
                    rowheight=25,
                    font=("Arial", 10))
    style.configure("Treeview.Heading",
                    font=("Arial", 10, "bold"),
                    foreground="white",
                    background=head_bg)
    style.map("Treeview.Heading",
              background=[("active", head_bg), ("pressed", head_bg)])

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
    # rglob("*") includes both files and dirs
    all_paths = list(base_dir.rglob("*"))
    filtered = []
    for p in all_paths:
        try:
            d = _rel_depth(base_dir, p)
        except ValueError:
            continue
        if d < 1:
            continue
        # Kind filter
        if p.is_dir() and not include_dirs:
            continue
        if p.is_file() and not include_files:
            continue
        # Depth filter
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
    undone = []
    # Shallow-first when undoing (rename parents earlier to restore tree paths)
    for old, intended, actual in sorted(applied, key=lambda t: len(t[2].parts)):
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
        self.master.title("Folder/File Renamer — Cấp & Tuỳ chọn (PharmApp)")
        self.pack(fill="both", expand=True)

        self.selected_dir = tk.StringVar()
        self.depth_mode = tk.StringVar(value=DEPTH_ALL)
        self.include_dirs = tk.BooleanVar(value=True)   # default: folders
        self.include_files = tk.BooleanVar(value=False) # default: not files
        self.replace_space = tk.BooleanVar(value=True)  # default: replace space -> underscore

        self.preview_rows: list[tuple[Path, Path]] = []
        self.applied_rows: list[tuple[Path, Path, Path]] = []

        self._build_ui()

    def _build_ui(self):
        top = ttk.Frame(self); top.pack(fill="x", padx=10, pady=10)
        ttk.Label(top, text="Base Folder / Thư mục gốc:").grid(row=0, column=0, sticky="w")
        e = ttk.Entry(top, textvariable=self.selected_dir, width=60)
        e.grid(row=0, column=1, sticky="we", padx=(6,6))
        ttk.Button(top, text="Browse…", style="Pharm.TButton", command=self._browse).grid(row=0, column=2, sticky="w")
        top.grid_columnconfigure(1, weight=1)

        # What to rename
        kind_frame = ttk.LabelFrame(self, text="Target / Đối tượng đổi tên"); kind_frame.pack(fill="x", padx=10)
        ttk.Checkbutton(kind_frame, text="Folders / Thư mục", variable=self.include_dirs).pack(side="left", padx=(6,12))
        ttk.Checkbutton(kind_frame, text="Files / Tập tin", variable=self.include_files).pack(side="left", padx=(0,12))

        # Depth options
        depth_frame = ttk.LabelFrame(self, text="Depth / Cấp thư mục"); depth_frame.pack(fill="x", padx=10, pady=(6,0))
        ttk.Radiobutton(depth_frame, text="Level 1 only (Chỉ Cấp 1)", value=DEPTH_LEVEL1_ONLY,
                        variable=self.depth_mode).pack(side="left", padx=(6,12))
        ttk.Radiobutton(depth_frame, text="Level 2 only (Chỉ Cấp 2)", value=DEPTH_LEVEL2_ONLY,
                        variable=self.depth_mode).pack(side="left", padx=(0,12))
        ttk.Radiobutton(depth_frame, text="Up to Level 2 (Tới Cấp 2)", value=DEPTH_UP_TO_LEVEL2,
                        variable=self.depth_mode).pack(side="left", padx=(0,12))
        ttk.Radiobutton(depth_frame, text="All levels (Tất cả cấp)", value=DEPTH_ALL,
                        variable=self.depth_mode).pack(side="left", padx=(0,12))

        # Transform options
        tx_frame = ttk.LabelFrame(self, text="Transform / Quy tắc đổi tên"); tx_frame.pack(fill="x", padx=10, pady=(6,0))
        ttk.Label(tx_frame, text="Always: '-' → '_' • Remove accents • Uppercase").pack(side="left", padx=(6,12))
        ttk.Checkbutton(tx_frame, text="Replace space with '_' (Thay khoảng trắng bằng '_')",
                        variable=self.replace_space).pack(side="left")

        actions = ttk.Frame(self); actions.pack(fill="x", padx=10, pady=(8,6))
        ttk.Button(actions, text="Preview / Xem trước", style="Pharm.TButton",
                   command=self._preview).pack(side="left")
        ttk.Button(actions, text="Rename / Đổi tên", style="Pharm.TButton",
                   command=self._rename).pack(side="left", padx=(6,0))
        ttk.Button(actions, text="Undo Last / Hoàn tác", style="Pharm.TButton",
                   command=self._undo_last).pack(side="left", padx=(6,0))
        ttk.Button(actions, text="Save CSV Map", style="Pharm.TButton",
                   command=self._save_csv).pack(side="left", padx=(6,0))

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

        foot = ttk.Frame(self); foot.pack(fill="x", padx=10, pady=(0,10))
        ttk.Label(foot, text=f"Script: {SCRIPT_NAME}").pack(side="left")

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
            self.tree.insert("", "end", values=("", str(base), "(unchanged)", "No changes"))
            return
        for old, new in sorted(plan, key=lambda t: str(t[0]).lower()):
            self.tree.insert("", "end", values=(_kind_of(old), str(old), str(new), "Preview"))

    def _rename(self):
        if not self.preview_rows:
            if not self._confirm_scan_then_rename():
                return
        applied = apply_renames(self.preview_rows)
        self.applied_rows = applied
        self._clear_tree()
        if not applied:
            self.tree.insert("", "end", values=("", "", "", "Nothing renamed"))
            return
        for old, intended, actual in sorted(applied, key=lambda t: str(t[0]).lower()):
            status = "Renamed" if actual == intended else "Renamed (conflict ➜ unique path)"
            self.tree.insert("", "end", values=(_kind_of(old), str(old), str(actual), status))
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
            self.tree.insert("", "end", values=(_kind_of(dst), str(src), str(dst), "Undone"))
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
    apply_pharmapp_theme(root)
    app = App(root)
    root.minsize(1000, 580)
    root.mainloop()

if __name__ == "__main__":
    main()
