#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FolderRenamer_GUI.py
Rename folders with rules:
- Replace '-' with '_'
- Uppercase all letters
- Remove Vietnamese diacritics (đ/Đ -> D)
Features:
- Choose base directory
- Preview before apply
- Recursive option
- Rename with collision-safe suffixes
- Undo last rename batch (this session)
- Save mapping to CSV
"""
import os
import sys
import csv
import unicodedata
from pathlib import Path
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

# --------- Script name banner (helpful for logs) ----------
try:
    SCRIPT_NAME = Path(__file__).name
except NameError:
    SCRIPT_NAME = "FolderRenamer_GUI.py"
print(f"[INFO] Running: {SCRIPT_NAME}")

# --------- PharmApp Theme (light) ----------
def apply_pharmapp_theme(root: tk.Tk):
    root.configure(bg="#fdf5e6")
    style = ttk.Style(root)
    try:
        style.theme_use("default")
    except tk.TclError:
        pass

    # Base colors
    bg = "#fdf5e6"
    fg = "#2a2a2a"
    btn_bg = "#f4a261"
    sel_bg = "#e9c46a"
    head_bg = "#b5838d"

    root.option_add("*Foreground", fg)
    root.option_add("*Background", bg)

    style.configure("TFrame", background=bg)
    style.configure("TLabel", background=bg, foreground=fg, font=("Arial", 11))
    style.configure("Pharm.TButton", font=("Arial", 10, "bold"))
    style.map("Pharm.TButton",
              background=[("active", "#e76f51")])

    # Treeview
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
    # Heading color patch (works on many ttk themes)
    style.map("Treeview.Heading",
              background=[("active", head_bg), ("pressed", head_bg)])

# --------- Name transform helpers ----------
def remove_vietnamese_diacritics(s: str) -> str:
    # Normalize + drop combining marks; convert đ/Đ to d/D first
    s = s.replace("đ", "d").replace("Đ", "D")
    nfkd = unicodedata.normalize("NFD", s)
    return "".join(ch for ch in nfkd if not unicodedata.combining(ch))

def transform_folder_name(name: str) -> str:
    # 1) '-' -> '_'
    s = name.replace("-", "_")
    # 2) remove diacritics
    s = remove_vietnamese_diacritics(s)
    # 3) to UPPER
    s = s.upper()
    return s

# Safe unique path if target exists (append _1, _2, ...)
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

# --------- Core logic ----------
def collect_folders(base_dir: Path, recursive: bool) -> list[Path]:
    if not base_dir.exists() or not base_dir.is_dir():
        return []
    if recursive:
        # all subdirs (excluding base itself)
        return sorted([p for p in base_dir.rglob("*") if p.is_dir()],
                      key=lambda p: len(p.parts), reverse=True)  # deepest first (for renaming)
    else:
        # only direct children dirs
        return [p for p in base_dir.iterdir() if p.is_dir()]

def compute_plan(base_dir: Path, folders: list[Path]) -> list[tuple[Path, Path]]:
    plan = []
    for p in folders:
        new_name = transform_folder_name(p.name)
        if new_name != p.name:
            plan.append((p, p.with_name(new_name)))
    return plan

def apply_renames(plan: list[tuple[Path, Path]]) -> list[tuple[Path, Path, Path]]:
    """
    Execute renames. Returns applied list of (old, intended_new, actual_new)
    using collision-safe targets.
    """
    applied = []
    # Important: deepest-first already ensured by collect_folders when recursive.
    for old, intended_new in plan:
        try:
            actual_target = intended_new
            if actual_target.exists():
                actual_target = unique_target_path(intended_new)
            old.rename(actual_target)
            applied.append((old, intended_new, actual_target))
        except Exception as e:
            print(f"[ERROR] Failed to rename '{old}' -> '{intended_new}': {e}")
    return applied

def undo_renames(applied: list[tuple[Path, Path, Path]]) -> list[tuple[Path, Path]]:
    """
    Undo by renaming actual_new back to original old.
    Must rename shallow-first to avoid conflicts: rename parents before children is unsafe,
    so we go from shallow to deep by sorting by path depth ascending for targets (reverse of apply).
    """
    undone = []
    # Sort by parts length ascending on actual_new to move higher dirs first
    for old, intended, actual in sorted(applied, key=lambda t: len(t[2].parts)):
        try:
            back_target = old
            if back_target.exists():
                back_target = unique_target_path(back_target)
            actual.rename(back_target)
            undone.append((actual, back_target))
        except Exception as e:
            print(f"[ERROR] Undo failed '{actual}' -> '{old}': {e}")
    return undone

# --------- GUI ----------
class App(ttk.Frame):
    def __init__(self, master):
        super().__init__(master)
        self.master.title("Folder Renamer — Replace '-'→'_', UPPERCASE, Remove Accents")
        self.pack(fill="both", expand=True)

        self.selected_dir = tk.StringVar()
        self.recursive = tk.BooleanVar(value=True)

        # Stored state
        self.preview_rows: list[tuple[Path, Path]] = []
        self.applied_rows: list[tuple[Path, Path, Path]] = []

        self._build_ui()

    def _build_ui(self):
        top = ttk.Frame(self); top.pack(fill="x", padx=10, pady=10)

        ttk.Label(top, text="Base Folder / Thư mục gốc:").grid(row=0, column=0, sticky="w")
        e = ttk.Entry(top, textvariable=self.selected_dir, width=60)
        e.grid(row=0, column=1, sticky="we", padx=(6,6))
        b = ttk.Button(top, text="Browse…", style="Pharm.TButton", command=self._browse)
        b.grid(row=0, column=2, sticky="w")

        top.grid_columnconfigure(1, weight=1)

        options = ttk.Frame(self); options.pack(fill="x", padx=10)
        ttk.Checkbutton(options, text="Recursive / Quét đệ quy", variable=self.recursive).pack(side="left")

        actions = ttk.Frame(self); actions.pack(fill="x", padx=10, pady=(6,6))
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
        cols = ("current", "new", "status")
        self.tree = ttk.Treeview(table_frame, columns=cols, show="headings", selectmode="browse")
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
        self._clear_tree()
        folders = collect_folders(base, self.recursive.get())
        plan = compute_plan(base, folders)
        self.preview_rows = plan
        if not plan:
            self.tree.insert("", "end", values=(str(base), "(unchanged)", "No changes"))
            return
        for old, new in sorted(plan, key=lambda t: str(t[0]).lower()):
            self.tree.insert("", "end", values=(str(old), str(new), "Preview"))

    def _rename(self):
        if not self.preview_rows:
            if not self._confirm_scan_then_rename():
                return
        # Apply renames
        applied = apply_renames(self.preview_rows)
        self.applied_rows = applied  # keep last batch for undo
        # Refresh table with actual results
        self._clear_tree()
        if not applied:
            self.tree.insert("", "end", values=("", "", "Nothing renamed"))
            return
        for old, intended, actual in sorted(applied, key=lambda t: str(t[0]).lower()):
            status = "Renamed"
            if actual != intended:
                status = "Renamed (conflict ➜ used unique path)"
            self.tree.insert("", "end", values=(str(old), str(actual), status))
        messagebox.showinfo("Done", f"Renamed {len(applied)} folder(s).")

    def _confirm_scan_then_rename(self) -> bool:
        base = Path(self.selected_dir.get().strip())
        if not base.exists() or not base.is_dir():
            messagebox.showwarning("Warning", "Please choose a valid base folder / Chọn thư mục hợp lệ.")
            return False
        folders = collect_folders(base, self.recursive.get())
        plan = compute_plan(base, folders)
        self.preview_rows = plan
        if not plan:
            messagebox.showinfo("Info", "No folders need renaming.")
            return False
        msg = f"Found {len(plan)} folder(s) to rename. Proceed?"
        return messagebox.askyesno("Confirm", msg)

    def _undo_last(self):
        if not self.applied_rows:
            messagebox.showinfo("Undo", "Nothing to undo in this session.")
            return
        undone = undo_renames(self.applied_rows)
        count = len(undone)
        self._clear_tree()
        for src, dst in sorted(undone, key=lambda t: str(t[0]).lower()):
            self.tree.insert("", "end", values=(str(src), str(dst), "Undone"))
        self.applied_rows.clear()
        messagebox.showinfo("Undo", f"Undone {count} folder(s).")

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
        # If we have applied rows, prefer actual results; else use preview
        headers = ["current_path", "intended_new_path", "actual_new_path_or_preview"]
        rows = []
        if self.applied_rows:
            for old, intended, actual in self.applied_rows:
                rows.append((str(old), str(intended), str(actual)))
        else:
            for old, intended in self.preview_rows:
                rows.append((str(old), str(intended), "(preview)"))
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
    root.minsize(900, 520)
    root.mainloop()

if __name__ == "__main__":
    main()
