# Đổi Tên File/Folder — Theo Cấp, Loại & Chủ Đề (PharmApp)

Ứng dụng GUI nhỏ gọn (Tkinter) giúp **đổi tên hàng loạt file và thư mục** theo Quy tắc an toàn, xem trước, có hoàn tác:

- `-` → `_`
- *(tuỳ chọn)* khoảng trắng `' '` → `_`
- Loại bỏ dấu tiếng Việt (ví dụ `đ/Đ → d/D`)
- Chuyển tên sang **CHỮ HOA**
- **Preview** trước khi áp dụng, tự tránh trùng tên (`_1`, `_2`, …), và **Hoàn tác** (batch gần nhất)
- Xuất bảng ánh xạ đổi tên ra **CSV**
- Bộ **chủ đề giao diện** tích hợp: *PharmApp Light*, *Nord Light*, *Midnight Teal (Dark)*, *Solar Slate*, **macOS Graphite (Dark)**

> Giao diện **song ngữ** (EN–VI). Không cần cài thêm thư viện ngoài Tkinter của Python.

---

## ✨ Tính năng

- **Đối tượng**: đổi tên **Thư mục**, **Tập tin**, hoặc **Cả hai**
- **Giới hạn cấp (Depth)**: 
  - *Chỉ Cấp 1* (con trực tiếp)  
  - *Chỉ Cấp 2* (cháu – con của cấp 1)  
  - *Tới Cấp 2* (gồm cấp 1 & 2)  
  - *Tất cả cấp* (toàn bộ đệ quy)
- **Quy tắc đổi tên**
  - Mặc định: `-` → `_`, bỏ dấu, **CHỮ HOA**
  - Tuỳ chọn: thay khoảng trắng `' '` → `_`
- **An toàn**
  - **Preview** bảng thay đổi trước khi áp dụng
  - Tránh trùng tên: nếu đã tồn tại, tự thêm `_1`, `_2`, …
  - **Hoàn tác** batch gần nhất trong phiên
  - Xuất CSV: *Current → Intended → Actual*
- **Chủ đề (Themes)**
  - PharmApp Light
  - Nord Light
  - Midnight Teal (Dark)
  - Solar Slate
  - **macOS Graphite (Dark)** (tương tự dark graphite trên macOS)

> **Lưu ý**: Ứng dụng hiện **viết hoa toàn bộ tên** (kể cả đuôi file). Nếu muốn **giữ nguyên chữ hoa/thường của phần đuôi file (extension)**, xem mục *Tuỳ biến* bên dưới.

---

## 📦 Cài đặt

### Yêu cầu
- **Python 3.8+**
- Tkinter (có sẵn trên Windows/macOS; Linux có thể cần `python3-tk`)

### Tải mã nguồn
```bash
git clone https://github.com/<your-org>/<your-repo>.git
cd <your-repo>
```
Không cần cài thêm package.

---

## ▶️ Chạy ứng dụng

### Windows
```bash
python FolderFileRenamer_GUI.py
# hoặc
py FolderFileRenamer_GUI.py
```

### macOS / Linux
```bash
python3 FolderFileRenamer_GUI.py
```

Bạn cũng có thể **double‑click** file `.py` (nếu hệ điều hành đã liên kết Python).

---

## 🧭 Cách dùng nhanh

1. **Chọn thư mục gốc** bằng **Browse…**.  
2. Chọn **Thư mục**, **Tập tin** hoặc **Cả hai**.  
3. Chọn **Cấp**: *Chỉ Cấp 1* / *Chỉ Cấp 2* / *Tới Cấp 2* / *Tất cả*.  
4. **Transform**: bật **Replace space with '_'** nếu muốn đổi khoảng trắng.  
5. Bấm **Preview / Xem trước** để xem thay đổi.  
6. Bấm **Rename / Đổi tên** để áp dụng.  
   - Nếu tên mới đã tồn tại, chương trình sẽ tạo tên duy nhất như `NAME_1`.  
7. **Undo / Hoàn tác** khôi phục **batch gần nhất** trong phiên hiện tại.  
8. **Save CSV Map** để lưu nhật ký đổi tên (phục vụ audit/rollback thủ công).

---

## 🎨 Chủ đề (Themes)

Đổi **Theme** ở combobox góc phải trên và bấm **Apply**:

- **PharmApp Light** — kem & cam ấm áp
- **Nord Light** — tông xanh băng dịu
- **Midnight Teal (Dark)** — teal tối sâu
- **Solar Slate** — tối giản, sáng nhẹ
- **macOS Graphite (Dark)** — gần giống macOS dark graphite

---

## 🛡️ Mẹo & Lưu ý

- Với cây thư mục lớn, **nên Preview trước**.  
- Tránh đổi tên khi file/thư mục **đang mở** bởi ứng dụng khác.  
- Trên Linux/macOS (FS phân biệt hoa/thường), đổi **chỉ khác mỗi chữ hoa/thường** vẫn tính là rename—an toàn nhưng lưu ý với VCS/build.  
- Nếu dùng đồng bộ đám mây (OneDrive/Dropbox/Drive), chờ sync xong trước khi chạy tiếp.

---

## 🧰 Đóng gói file chạy độc lập (tuỳ chọn)

> Ứng dụng không dùng thư viện ngoài; phần này chỉ để tiện phát hành.

### Windows (PyInstaller)
```bash
pip install pyinstaller
pyinstaller --noconsole --onefile --name FolderFileRenamer --icon assets/icon.ico FolderFileRenamer_GUI.py
# Kết quả: dist/FolderFileRenamer.exe
```

### macOS (PyInstaller)
```bash
pip install pyinstaller
pyinstaller --windowed --onefile --name FolderFileRenamer FolderFileRenamer_GUI.py
# Kết quả: dist/FolderFileRenamer.app
```
*(macOS có thể cần ký ứng dụng/notarize để vượt Gatekeeper).*

---

## 🛠️ Tuỳ biến

- **Thêm chủ đề**: mở dict `ThemeManager.THEMES`, sao chép palette có sẵn, chỉnh màu, thêm vào danh sách combobox.  
- **Giữ nguyên chữ hoa/thường của đuôi file**: trong `transform_name()`, tách *stem* và *suffix* (dùng `os.path.splitext`), **viết hoa chỉ phần stem**, sau đó nối lại suffix gốc.

---

## 🌐 Ngôn ngữ

- Giao diện **song ngữ** (EN–VI). Có thể đổi text trong phần thiết lập GUI theo chuẩn nội bộ.

---

## 🧪 Môi trường đã thử

- Windows 10/11 (Python 3.11)  
- macOS 13+ (Ventura) / 14 (Sonoma)  
- Ubuntu 20.04+

---

## 📄 Giấy phép

MIT — Xem `LICENSE` (tuỳ chọn đổi theo nhu cầu của bạn).

---

## 🙌 Ghi công

- Phong cách **PharmApp** & ý tưởng bảng màu: *Nghiên Cứu Thuốc*  
- Website: **https://www.pharmapp.vn** • **https://www.nghiencuuthuoc.com**

---

## 🗺️ Lộ trình

- Tuỳ chọn **giữ nguyên extension case**
- Chế độ **lowercase** hoặc **Title Case**
- Xuất **báo cáo dry‑run** dạng batch không GUI (CLI mode)

---

## 📝 Nhật ký thay đổi

- **v1.0 — 2025‑10‑15**  
  Phát hành đầu tiên: themes, depth control, preview/undo, CSV, và macOS‑like dark theme.

---

## 🔗 Ngôn ngữ khác

- English: `README.md`
