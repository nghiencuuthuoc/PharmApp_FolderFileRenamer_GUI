# Folder/File Renamer — Depth, Kind & Themes (PharmApp)

A tiny cross‑platform Tkinter GUI to **bulk rename files and folders** with smart, safe rules:

- `-` → `_`
- *(optional)* space `' '` → `_`
- Remove Vietnamese diacritics (e.g., `đ/Đ → d/D`)
- Convert names to **UPPERCASE**
- Preview before applying, collision‑safe renames (`_1`, `_2`, …), and **Undo** (last batch in session)
- Export rename mapping to **CSV**
- Built‑in **theme switcher**: *PharmApp Light*, *Nord Light*, *Midnight Teal (Dark)*, *Solar Slate*, **macOS Graphite (Dark)**

> UI is bilingual (English–Vietnamese). No external dependencies besides Python’s standard library (Tkinter).

---

## ✨ Features

- **Targets**: rename **Folders**, **Files**, or **Both**
- **Depth control**: 
  - *Level 1 only* (direct children)  
  - *Level 2 only* (grandchildren)  
  - *Up to Level 2* (levels 1 & 2)  
  - *All levels* (full recursive)
- **Transforms**
  - Always: `-` → `_`, remove diacritics, **UPPERCASE**
  - Optional: replace spaces `' '` → `_`
- **Safety**
  - **Preview** table before applying
  - Collision‑safe: if target exists, appends `_1`, `_2`, …
  - **Undo** last batch (session‑level)
  - CSV export of *Current → Intended → Actual* paths
- **Themes**
  - PharmApp Light
  - Nord Light
  - Midnight Teal (Dark)
  - Solar Slate
  - **macOS Graphite (Dark)** (new, close to macOS dark graphite look)

> **Note**: The current implementation uppercases the *entire* filename (including extension). If you prefer preserving the original extension case, open an issue or toggle the code as needed (see *Customize* below).

---

## 📦 Installation

### Requirements
- **Python 3.8+**
- Tkinter (bundled with most Python distributions on Windows/macOS; on some Linux distros, you may need to install `python3-tk`)

### Get the code
```bash
git clone https://github.com/<your-org>/<your-repo>.git
cd <your-repo>
```

No extra packages to install.

---

## ▶️ Run

### Windows
```bash
python FolderFileRenamer_GUI.py
# or
py FolderFileRenamer_GUI.py
```

### macOS / Linux
```bash
python3 FolderFileRenamer_GUI.py
```

You can also double‑click the `.py` file in most environments where Python is registered with the OS.

---

## 🧭 Usage

1. **Base Folder**: Click **Browse…** and select the root directory.
2. **Targets**: tick **Folders**, **Files**, or both.
3. **Depth**: choose *Level 1 only*, *Level 2 only*, *Up to Level 2*, or *All levels*.
4. **Transform**: toggle **Replace space with '_'** if you want spaces turned into underscores.
5. Click **Preview / Xem trước** to see pending changes.
6. Click **Rename / Đổi tên** to apply.  
   - If a name already exists, the app creates a unique target like `NAME_1`.
7. **Undo / Hoàn tác** reverts *the last batch* made in the current session.
8. **Save CSV Map** to export a mapping for audit or manual rollback.

---

## 🎨 Themes

Switch theme from the top right combobox and press **Apply**:

- **PharmApp Light** — warm cream & orange
- **Nord Light** — cool nordic palette
- **Midnight Teal (Dark)** — deep teal dark UI
- **Solar Slate** — minimal light slate
- **macOS Graphite (Dark)** — macOS‑like graphite dark

---

## 🛡️ Tips & Notes

- Always run **Preview** first for large trees.
- Prefer renaming when source files/folders are **not in use** (e.g., not opened by editors).
- On Linux/macOS (case‑sensitive FS), changing only the **case** may still produce a “rename” on disk; behavior is safe but be mindful with VCS or build tools.
- If you use cloud sync (OneDrive/Dropbox/Drive), let the sync complete before running again.

---

## 🧰 Build a Standalone Executable (optional)

> No external libs are required; this is optional for easy distribution.

### Windows (PyInstaller)
```bash
pip install pyinstaller
pyinstaller --noconsole --onefile --name FolderFileRenamer --icon assets/icon.ico FolderFileRenamer_GUI.py
# Output: dist/FolderFileRenamer.exe
```

### macOS (PyInstaller)
```bash
pip install pyinstaller
pyinstaller --windowed --onefile --name FolderFileRenamer FolderFileRenamer_GUI.py
# Output: dist/FolderFileRenamer.app
```

*(On macOS you may need to notarize/sign the app for Gatekeeper.)*

---

## 🛠️ Customize

- **Add a theme**: open `ThemeManager.THEMES` dict, copy an existing palette, tweak colors, and add the key to the combobox list.
- **Preserve extension case**: in `transform_name()`, split name/extension via `Path(name).suffix` or `os.path.splitext`, uppercase only the stem, and re‑append the original extension.

---

## 📚 Localization

- UI labels are **bilingual** (English–Vietnamese).  
- You can adjust labels in the GUI setup section to match your team conventions.

---

## 🧪 Tested On

- Windows 10/11 (Python 3.11)
- macOS 13+ (Ventura) / 14 (Sonoma)
- Ubuntu 20.04+

---

## 📄 License

MIT — See `LICENSE` (you can change it to your preferred license).

---

## 🙌 Credits

- **PharmApp** styles and palette ideas by *Nghiên Cứu Thuốc*  
- Websites: **https://www.pharmapp.vn** • **https://www.nghiencuuthuoc.com**

---

## 🗺️ Roadmap

- Option to **preserve extension case**
- Optional **lowercase** or **Title Case** modes
- Batch **dry‑run report** export without GUI (CLI mode)

---

## 📝 Changelog

- **v1.0 — 2025‑10‑15**  
  Initial public release with themes, depth control, preview/undo, CSV export, and macOS‑like dark theme.
