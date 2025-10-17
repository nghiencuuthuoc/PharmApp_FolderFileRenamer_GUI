#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Folder/File Renamer — v6 (EN/VI toggle switch)
- Rename FOLDERS/FILES with rules:
  * '-' -> '_'
  * (optional) ' ' -> '_'
  * Remove Vietnamese diacritics (đ/Đ -> D)
  * Uppercase all letters

New in v6:
- Full bilingual UI with a switch (EN <-> VI)
- All labels/buttons/table headings/messages update instantly

Themes:
- PharmApp Light, Nord Light, Midnight Teal (Dark), Solar Slate, macOS Graphite (Dark)
"""

import csv
import unicodedata
from pathlib import Path
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

# --------- SCRIPT NAME ----------
try:
    SCRIPT_NAME = Path(__file__).name
except NameError:
    SCRIPT_NAME = "FolderRenamer_v6.py"
print(f"[INFO] Running: {SCRIPT_NAME}")

# --------- THEME MANAGER ----------
class ThemeManager:
    THEMES = {
        "PharmApp Light": {
            "bg": "#fdf5e6", "fg": "#2a2a2a",
            "button_bg": "#f4a261", "button_active": "#e76f51", "button_fg": "#000000",
            "accent": "#e9c46a", "heading_bg": "#b5838d",
            "selection_bg": "#e5e7eb", "input_bg": "#ffffff", "input_fg": "#2a2a2a",
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
                             rowheight=25,
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

# --------- HELPERS ----------
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

# --------- DEPTH ----------
DEPTH_LEVEL1_ONLY = "LEVEL1_ONLY"
DEPTH_LEVEL2_ONLY = "LEVEL2_ONLY"
DEPTH_UP_TO_LEVEL2 = "UP_TO_LEVEL2"
DEPTH_ALL = "ALL"

def _rel_depth(base: Path, p: Path) -> int:
    return len(p.relative_to(base).parts)

def collect_paths_by_depth(base_dir: Path, depth_mode: str,
                           include_dirs: bool, include_files: bool) -> list[Path]:
    if not base_dir.exists() or not base_dir.is_dir():
        return []
    all_paths = list(base_dir.rglob("*"))
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
        filtered.append(p)
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

# --------- LANGUAGE PACKS ----------
LANG = {
    "EN": {
        "title": "Folder/File Renamer — Depth, Kind & Themes (PharmApp)",
        "base_folder": "Base Folder",
        "browse": "Browse…",
        "theme": "Theme",
        "apply": "Apply",
        "target": "Target",
        "folders": "Folders",
        "files": "Files",
        "depth": "Depth",
        "level1": "Level 1 only",
        "level2": "Level 2 only",
        "upto2": "Up to Level 2",
        "all": "All levels",
        "transform": "Transform",
        "rule_hint": "Always: '-' → '_' • Remove accents • Uppercase",
        "replace_space": "Replace spaces with '_'",
        "preview": "Preview",
        "rename": "Rename",
        "undo": "Undo Last",
        "save_csv": "Save CSV Map",
        "col_kind": "Kind",
        "col_current": "Current Path",
        "col_new": "New Path (Preview/Actual)",
        "col_status": "Status",
        "msg_warn": "Warning",
        "msg_confirm": "Confirm",
        "msg_info": "Info",
        "warn_choose_folder": "Please choose a valid base folder.",
        "warn_select_target": "Select at least one target: Folders or Files.",
        "no_changes": "No items need renaming.",
        "confirm_rename": "Found {n} item(s) to rename at selected depth. Proceed?",
        "renamed_n": "Renamed {n} item(s).",
        "nothing_renamed": "Nothing renamed",
        "undo_none": "Nothing to undo in this session.",
        "undone_n": "Undone {n} item(s).",
        "csv_no_data": "No data to save. Run Preview or Rename first.",
        "csv_saved": "CSV saved:\n{fp}",
        "csv_error": "Failed to save CSV:\n{err}",
        "status_script": "Script",
        "status_theme": "Theme",
        "switch_label_left": "VI",
        "switch_label_right": "EN",
    },
    "VI": {
        "title": "Đổi tên Thư mục/Tập tin — Chọn cấp, loại & Theme (PharmApp)",
        "base_folder": "Thư mục gốc",
        "browse": "Chọn…",
        "theme": "Giao diện",
        "apply": "Áp dụng",
        "target": "Đối tượng đổi tên",
        "folders": "Thư mục",
        "files": "Tập tin",
        "depth": "Cấp thư mục",
        "level1": "Chỉ Cấp 1",
        "level2": "Chỉ Cấp 2",
        "upto2": "Tới Cấp 2",
        "all": "Tất cả cấp",
        "transform": "Quy tắc đổi tên",
        "rule_hint": "Luôn: '-' → '_' • Bỏ dấu • Viết HOA",
        "replace_space": "Thay khoảng trắng bằng '_'",
        "preview": "Xem trước",
        "rename": "Đổi tên",
        "undo": "Hoàn tác",
        "save_csv": "Lưu CSV ánh xạ",
        "col_kind": "Loại",
        "col_current": "Đường dẫn hiện tại",
        "col_new": "Đường dẫn mới (Xem trước/Thực tế)",
        "col_status": "Trạng thái",
        "msg_warn": "Cảnh báo",
        "msg_confirm": "Xác nhận",
        "msg_info": "Thông báo",
        "warn_choose_folder": "Hãy chọn thư mục gốc hợp lệ.",
        "warn_select_target": "Chọn ít nhất một loại: Thư mục hoặc Tập tin.",
        "no_changes": "Không có mục nào cần đổi tên.",
        "confirm_rename": "Có {n} mục sẽ đổi tên theo cấp đã chọn. Tiếp tục?",
        "renamed_n": "Đã đổi tên {n} mục.",
        "nothing_renamed": "Không có mục nào được đổi tên",
        "undo_none": "Không có gì để hoàn tác trong phiên này.",
        "undone_n": "Đã hoàn tác {n} mục.",
        "csv_no_data": "Chưa có dữ liệu để lưu. Hãy Xem trước hoặc Đổi tên trước.",
        "csv_saved": "Đã lưu CSV:\n{fp}",
        "csv_error": "Lỗi khi lưu CSV:\n{err}",
        "status_script": "Tập lệnh",
        "status_theme": "Giao diện",
        "switch_label_left": "VI",
        "switch_label_right": "EN",
    }
}

# --------- TOGGLE SWITCH (Canvas) ----------
class LanguageSwitch(ttk.Frame):
    """A small canvas-based switch: left=VI, right=EN (or generic off/on)."""
    def __init__(self, master, get_palette, variable: tk.StringVar, onvalue="EN", offvalue="VI", command=None):
        super().__init__(master)
        self.get_palette = get_palette
        self.var = variable
        self.onvalue = onvalue
        self.offvalue = offvalue
        self.command = command
        self.width, self.height = 74, 28
        self.pad = 3
        self.canvas = tk.Canvas(self, width=self.width, height=self.height, highlightthickness=0, bd=0)
        self.canvas.pack()
        self.canvas.bind("<Button-1>", self._toggle)
        # self.canvas.bind("<Space>", self._toggle)
        self.canvas.bind("<space>", self._toggle)        # đơn giản, đúng trên mọi nền tảng
        # hoặc
        self.canvas.bind("<Key-space>", self._toggle)    # tương đương

        self.canvas.configure(cursor="hand2")
        self.var.trace_add("write", lambda *args: self.draw())
        self.draw()

    def _toggle(self, *_):
        self.var.set(self.onvalue if self.var.get() == self.offvalue else self.offvalue)
        if self.command:
            self.command()

    def draw(self):
        pal = self.get_palette()
        bg = pal["bg"]
        knob_on = pal["button_bg"]
        knob_off = pal["accent"]
        txt_fg = pal["fg"]
        self.canvas.delete("all")
        self.canvas.configure(bg=bg)

        r = (self.height//2)
        x0, y0, x1, y1 = self.pad, self.pad, self.width-self.pad, self.height-self.pad
        # Track
        self._rounded_rect(x0, y0, x1, y1, r-2, fill=pal["selection_bg"], outline=pal["selection_bg"])

        is_on = (self.var.get() == self.onvalue)
        # Labels
        left_txt = LANG[self.var.get()]["switch_label_left"]
        right_txt = LANG[self.var.get()]["switch_label_right"]
        self.canvas.create_text(self.width*0.24, self.height*0.5, text=left_txt, fill=txt_fg, font=("Arial", 9, "bold"))
        self.canvas.create_text(self.width*0.76, self.height*0.5, text=right_txt, fill=txt_fg, font=("Arial", 9, "bold"))

        # Knob
        knob_r = r-3
        cx = self.width - r if is_on else r
        self.canvas.create_oval(cx-knob_r, r-knob_r, cx+knob_r, r+knob_r,
                                fill=(knob_on if is_on else knob_off), outline="")

    def _rounded_rect(self, x1, y1, x2, y2, r, **kwargs):
        points = [
            x1+r, y1, x2-r, y1, x2, y1, x2, y1+r,
            x2, y2-r, x2, y2, x2-r, y2, x1+r, y2,
            x1, y2, x1, y2-r, x1, y1+r, x1, y1
        ]
        return self.canvas.create_polygon(points, smooth=True, **kwargs)

# --------- GUI ----------
class App(ttk.Frame):
    def __init__(self, master):
        super().__init__(master)
        # Language state
        self.lang = tk.StringVar(value="EN")  # default EN; toggle to "VI" with switch
        self.L = lambda: LANG[self.lang.get()]

        self.master.title(self.L()["title"])
        self.pack(fill="both", expand=True)

        # State
        self.selected_dir = tk.StringVar()
        self.depth_mode = tk.StringVar(value=DEPTH_ALL)
        self.include_dirs = tk.BooleanVar(value=True)
        self.include_files = tk.BooleanVar(value=False)
        self.replace_space = tk.BooleanVar(value=True)
        self.current_theme = tk.StringVar(value="macOS Graphite (Dark)")

        self.preview_rows: list[tuple[Path, Path]] = []
        self.applied_rows: list[tuple[Path, Path, Path]] = []

        # Theme manager
        self.tm = ThemeManager(master)
        pal = self.tm.apply(self.current_theme.get())
        self._palette = pal
        self.get_palette = lambda: self._palette

        # UI text variables (so we can live-update)
        self.t = {k: tk.StringVar() for k in [
            "base_folder", "browse", "theme", "apply", "target", "folders", "files",
            "depth", "level1", "level2", "upto2", "all", "transform", "rule_hint",
            "replace_space", "preview", "rename", "undo", "save_csv",
            "col_kind", "col_current", "col_new", "col_status"
        ]}
        self._build_ui()
        self._setup_tree_tags()
        self._apply_language()  # set initial texts

    # ---------- UI ----------
    def _build_ui(self):
        # Top bar
        top = ttk.Frame(self); top.pack(fill="x", padx=10, pady=10)

        # Language switch on the far left
        self.lang_switch = LanguageSwitch(
            top, get_palette=self.get_palette,
            variable=self.lang, onvalue="EN", offvalue="VI",
            command=self._apply_language
        )
        self.lang_switch.grid(row=0, column=0, sticky="w", padx=(0,10))

        ttk.Label(top, textvariable=self.t["base_folder"]).grid(row=0, column=1, sticky="w")
        e = ttk.Entry(top, textvariable=self.selected_dir, width=58)
        e.grid(row=0, column=2, sticky="we", padx=(6,6))
        ttk.Button(top, textvariable=self.t["browse"], style="Pharm.TButton", command=self._browse).grid(row=0, column=3, sticky="w", padx=(0,10))

        ttk.Label(top, textvariable=self.t["theme"]).grid(row=0, column=4, sticky="e")
        self.theme_cbb = ttk.Combobox(top, state="readonly",
                                      values=list(ThemeManager.THEMES.keys()),
                                      textvariable=self.current_theme, width=24)
        self.theme_cbb.grid(row=0, column=5, sticky="w", padx=(6,6))
        ttk.Button(top, textvariable=self.t["apply"], style="Pharm.TButton", command=self._apply_theme).grid(row=0, column=6, sticky="w")

        top.grid_columnconfigure(2, weight=1)

        # Target Kind
        self.kind_frame = ttk.Labelframe(self, labelanchor="nw"); self.kind_frame.pack(fill="x", padx=10)
        self.chk_dirs = ttk.Checkbutton(self.kind_frame, variable=self.include_dirs)
        self.chk_files = ttk.Checkbutton(self.kind_frame, variable=self.include_files)
        self.chk_label_dirs = ttk.Label(self.kind_frame)  # for text next to checkbox
        self.chk_label_files = ttk.Label(self.kind_frame)

        self.chk_dirs.pack(side="left", padx=(6,4))
        self.chk_label_dirs.pack(side="left", padx=(0,12))
        self.chk_files.pack(side="left", padx=(0,4))
        self.chk_label_files.pack(side="left", padx=(0,12))

        # Depth
        self.depth_frame = ttk.Labelframe(self, labelanchor="nw"); self.depth_frame.pack(fill="x", padx=10, pady=(6,0))
        self.rb_l1 = ttk.Radiobutton(self.depth_frame, value=DEPTH_LEVEL1_ONLY, variable=self.depth_mode)
        self.rb_l2 = ttk.Radiobutton(self.depth_frame, value=DEPTH_LEVEL2_ONLY, variable=self.depth_mode)
        self.rb_u2 = ttk.Radiobutton(self.depth_frame, value=DEPTH_UP_TO_LEVEL2, variable=self.depth_mode)
        self.rb_all = ttk.Radiobutton(self.depth_frame, value=DEPTH_ALL, variable=self.depth_mode)

        # Depth labels (separate labels so we can localize cleanly)
        self.rb_l1_lbl = ttk.Label(self.depth_frame)
        self.rb_l2_lbl = ttk.Label(self.depth_frame)
        self.rb_u2_lbl = ttk.Label(self.depth_frame)
        self.rb_all_lbl = ttk.Label(self.depth_frame)

        for w, lbl, pad in [
            (self.rb_l1, self.rb_l1_lbl, (6,12)),
            (self.rb_l2, self.rb_l2_lbl, (0,12)),
            (self.rb_u2, self.rb_u2_lbl, (0,12)),
            (self.rb_all, self.rb_all_lbl, (0,12)),
        ]:
            w.pack(side="left", padx=(pad[0],4))
            lbl.pack(side="left", padx=(0,pad[1]))

        # Transform
        self.tx_frame = ttk.Labelframe(self, labelanchor="nw"); self.tx_frame.pack(fill="x", padx=10, pady=(6,0))
        self.rule_hint_lbl = ttk.Label(self.tx_frame)
        self.rule_hint_lbl.pack(side="left", padx=(6,12))
        self.chk_replace = ttk.Checkbutton(self.tx_frame, variable=self.replace_space)
        self.chk_replace_lbl = ttk.Label(self.tx_frame)
        self.chk_replace.pack(side="left")
        self.chk_replace_lbl.pack(side="left", padx=(6,0))

        # Actions
        actions = ttk.Frame(self); actions.pack(fill="x", padx=10, pady=(8,6))
        self.btn_preview = ttk.Button(actions, style="Pharm.TButton", command=self._preview)
        self.btn_rename  = ttk.Button(actions, style="Pharm.TButton", command=self._rename)
        self.btn_undo    = ttk.Button(actions, style="Pharm.TButton", command=self._undo_last)
        self.btn_csv     = ttk.Button(actions, style="Pharm.TButton", command=self._save_csv)
        for i, b in enumerate([self.btn_preview, self.btn_rename, self.btn_undo, self.btn_csv]):
            b.pack(side="left", padx=(6 if i else 0,0))

        # Table
        table_frame = ttk.Frame(self); table_frame.pack(fill="both", expand=True, padx=10, pady=(6,10))
        cols = ("kind", "current", "new", "status")
        self.tree = ttk.Treeview(table_frame, columns=cols, show="headings", selectmode="browse")
        self.tree.heading("kind", text="")
        self.tree.heading("current", text="")
        self.tree.heading("new", text="")
        self.tree.heading("status", text="")
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
        self.status_lbl = ttk.Label(foot, text="")
        self.status_lbl.pack(side="left")
        self._update_status()

    def _apply_theme(self):
        self._palette = self.tm.apply(self.current_theme.get())
        self._setup_tree_tags()
        self._update_status()
        # redraw switch to adapt to new palette
        self.lang_switch.draw()

    def _setup_tree_tags(self):
        pal = self._palette
        try:
            self.tree.tag_configure("preview", background=pal["row_alt"])
            self.tree.tag_configure("renamed", background=pal["accent"])
            self.tree.tag_configure("conflict", background=pal["selection_bg"])
            self.tree.tag_configure("undo", background=pal["row_alt"])
            self.tree.tag_configure("info", background=pal["row_alt"])
        except Exception:
            pass

    # ---------- LANGUAGE APPLY ----------
    def _apply_language(self):
        L = self.L()
        self.master.title(L["title"])

        # top bar
        self.t["base_folder"].set(f"{L['base_folder']}:")
        self.t["browse"].set(L["browse"])
        self.t["theme"].set(f"{L['theme']}:")
        self.t["apply"].set(L["apply"])

        # frames titles
        self.kind_frame.config(text=L["target"])
        self.depth_frame.config(text=L["depth"])
        self.tx_frame.config(text=L["transform"])

        # check/radio labels (as separate labels for clean localization)
        self.chk_label_dirs.config(text=L["folders"])
        self.chk_label_files.config(text=L["files"])

        self.rb_l1_lbl.config(text=L["level1"])
        self.rb_l2_lbl.config(text=L["level2"])
        self.rb_u2_lbl.config(text=L["upto2"])
        self.rb_all_lbl.config(text=L["all"])

        self.rule_hint_lbl.config(text=L["rule_hint"])
        self.chk_replace_lbl.config(text=L["replace_space"])

        # buttons
        self.btn_preview.config(text=L["preview"])
        self.btn_rename.config(text=L["rename"])
        self.btn_undo.config(text=L["undo"])
        self.btn_csv.config(text=L["save_csv"])

        # table headings
        self.tree.heading("kind", text=L["col_kind"])
        self.tree.heading("current", text=L["col_current"])
        self.tree.heading("new", text=L["col_new"])
        self.tree.heading("status", text=L["col_status"])

        self._update_status()
        self.lang_switch.draw()

    def _update_status(self):
        L = self.L()
        self.status_lbl.config(
            text=f"{L['status_script']}: {SCRIPT_NAME} • {L['status_theme']}: {self.current_theme.get()} • Lang: {self.lang.get()}"
        )

    # ---------- ACTIONS ----------
    def _browse(self):
        d = filedialog.askdirectory(title=self.L()["base_folder"])
        if d:
            self.selected_dir.set(d)

    def _clear_tree(self):
        for iid in self.tree.get_children():
            self.tree.delete(iid)

    def _preview(self):
        L = self.L()
        base = Path(self.selected_dir.get().strip())
        if not base.exists() or not base.is_dir():
            messagebox.showwarning(L["msg_warn"], L["warn_choose_folder"])
            return
        if not self.include_dirs.get() and not self.include_files.get():
            messagebox.showwarning(L["msg_warn"], L["warn_select_target"])
            return

        self._clear_tree()
        paths = collect_paths_by_depth(base,
                                       self.depth_mode.get(),
                                       self.include_dirs.get(),
                                       self.include_files.get())
        plan = compute_plan(paths, self.replace_space.get())
        self.preview_rows = plan
        if not plan:
            self.tree.insert("", "end", values=("", str(base), "(unchanged)", L["no_changes"]), tags=("info",))
            return
        for old, new in sorted(plan, key=lambda t: str(t[0]).lower()):
            self.tree.insert("", "end",
                             values=(_kind_of(old), str(old), str(new), "Preview"),
                             tags=("preview",))

    def _confirm_scan_then_rename(self) -> bool:
        L = self.L()
        base = Path(self.selected_dir.get().strip())
        if not base.exists() or not base.is_dir():
            messagebox.showwarning(L["msg_warn"], L["warn_choose_folder"])
            return False
        if not self.include_dirs.get() and not self.include_files.get():
            messagebox.showwarning(L["msg_warn"], L["warn_select_target"])
            return False
        paths = collect_paths_by_depth(base,
                                       self.depth_mode.get(),
                                       self.include_dirs.get(),
                                       self.include_files.get())
        plan = compute_plan(paths, self.replace_space.get())
        self.preview_rows = plan
        if not plan:
            messagebox.showinfo(L["msg_info"], L["no_changes"])
            return False
        msg = L["confirm_rename"].format(n=len(plan))
        return messagebox.askyesno(L["msg_confirm"], msg)

    def _rename(self):
        L = self.L()
        if not self.preview_rows:
            if not self._confirm_scan_then_rename():
                return
        applied = apply_renames(self.preview_rows)
        self.applied_rows = applied
        self._clear_tree()
        if not applied:
            self.tree.insert("", "end", values=("", "", "", L["nothing_renamed"]), tags=("info",))
            return
        for old, intended, actual in sorted(applied, key=lambda t: str(t[0]).lower()):
            status = "Renamed" if actual == intended else "Renamed (conflict ➜ unique path)"
            tag = "renamed" if actual == intended else "conflict"
            self.tree.insert("", "end", values=(_kind_of(old), str(old), str(actual), status), tags=(tag,))
        messagebox.showinfo(L["msg_info"], L["renamed_n"].format(n=len(applied)))

    def _undo_last(self):
        L = self.L()
        if not self.applied_rows:
            messagebox.showinfo(L["msg_info"], L["undo_none"])
            return
        undone = undo_renames(self.applied_rows)
        count = len(undone)
        self._clear_tree()
        for src, dst in sorted(undone, key=lambda t: str(t[0]).lower()):
            self.tree.insert("", "end",
                             values=(_kind_of(dst), str(src), str(dst), "Undone"),
                             tags=("undo",))
        self.applied_rows.clear()
        messagebox.showinfo(L["msg_info"], L["undone_n"].format(n=count))

    def _save_csv(self):
        L = self.L()
        if not self.preview_rows and not self.applied_rows:
            messagebox.showinfo(L["msg_info"], L["csv_no_data"])
            return
        fp = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv")],
            title=L["save_csv"]
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
            messagebox.showinfo(L["msg_info"], L["csv_saved"].format(fp=fp))
        except Exception as e:
            messagebox.showerror(L["msg_warn"], L["csv_error"].format(err=e))

def main():
    root = tk.Tk()
    app = App(root)
    root.minsize(1040, 600)
    root.mainloop()

if __name__ == "__main__":
    main()
