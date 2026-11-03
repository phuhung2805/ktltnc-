# HỆ THỐNG QUẢN LÝ LỊCH LÀM VIỆC CÁ NHÂN (PERSONAL SCHEDULER SYSTEM)

> Đề tài: Xây dựng chương trình quản lý lịch làm việc cá nhân  
> Môn học: Kỹ thuật Lập trình Nâng cao (KTLTNC)  
> Ngôn ngữ: Python 3 (Tkinter GUI, SQLite, Thuật toán Lập lịch nâng cao)

---

## 📌 1. Giới thiệu tổng quan
Chương trình là một giải pháp hoàn chỉnh hỗ trợ cá nhân quản lý lịch làm việc, sự kiện và nhiệm vụ thông minh. Hệ thống không chỉ cung cấp các thao tác CRUD truyền thống mà còn tích hợp các cơ sở lý thuyết khoa học máy tính và thuật toán tối ưu hóa:
- **Phát hiện và cảnh báo xung đột thời gian (Conflict Detection)** qua thuật toán Đường quét (Sweep-Line).
- **Gợi ý khung giờ rảnh tối ưu (Smart Free Slot Finder)** theo chiến lược Sớm nhất (Earliest) hoặc Vừa vặn nhất (Best-Fit / Giảm phân mảnh).
- **Lập lịch theo quan hệ phụ thuộc (Task Dependency DAG)** bằng thuật toán Kahn (Topological Sort) và phát hiện chu trình (Deadlock Detection).
- **Lập lịch tối ưu hóa có trọng số (Weighted Interval Scheduling)** sử dụng Quy hoạch động (Dynamic Programming - $O(N \log N)$).
- **Phân loại Ma trận Eisenhower (4 Góc phần tư)** tự động dựa trên mức độ quan trọng và thời hạn khẩn cấp.
- **Trực quan hóa thống kê (Analytics Dashboard)** với biểu đồ tròn Donut và biểu đồ cột được vẽ trực tiếp bằng Canvas siêu nhẹ.

---

## 📂 2. Cấu trúc thư mục dự án
```text
d:\ktltnc\
│
├── core\                          # Bộ máy thuật toán và mô hình dữ liệu cốt lõi
│   ├── __init__.py
│   ├── models.py                  # Thực thể Task, Priority, Status, Category
│   ├── scheduler_engine.py        # Các thuật toán Sweep-Line, Kahn Topo, WIS DP, Free Slot Finder
│   └── storage.py                 # Lưu trữ bền vững SQLite và xuất/nhập JSON
│
├── ui\                            # Giao diện người dùng đồ họa (Tkinter Modern Dark GUI)
│   ├── __init__.py
│   ├── theme.py                   # Bảng màu, typography và kiểu dáng hiện đại
│   ├── task_dialog.py             # Hộp thoại Thêm/Sửa công việc với kiểm tra xung đột trực tiếp
│   ├── smart_slot_dialog.py       # Hộp thoại phân tích và tự động chọn khung giờ rảnh
│   ├── eisenhower_view.py         # Trực quan hóa ma trận 4 góc phần tư Eisenhower
│   ├── analytics_view.py          # Dashboard thống kê vẽ bằng Tkinter Canvas
│   └── main_window.py             # Cửa sổ chính tích hợp đa tab
│
├── tests\                         # Bộ kiểm thử tự động (Unit Tests)
│   ├── __init__.py
│   └── test_scheduler.py          # 11 ca kiểm thử toàn diện
│
├── data\                          # Thư mục chứa dữ liệu
│   └── sample_schedule.json       # Tệp dữ liệu mẫu JSON
│
├── benchmark.py                   # Đo lường và đánh giá độ phức tạp thực nghiệm (N = 100 .. 10,000)
├── demo_experiments.py            # Chạy toàn bộ kịch bản thực nghiệm với dữ liệu mẫu (Console CLI)
├── main.py                        # Điểm khởi chạy ứng dụng GUI
└── README.md                      # Tài liệu hướng dẫn
```

---

## 🚀 3. Hướng dẫn cài đặt và sử dụng

### Yêu cầu hệ thống:
- Python 3.8+ (khuyến nghị Python 3.10 - 3.12).
- Sử dụng hoàn toàn thư viện chuẩn (`tkinter`, `sqlite3`, `json`, `datetime`, `bisect`, `heapq`), **không yêu cầu cài đặt thêm bất kỳ thư viện bên ngoài (no pip dependencies required)**.

### Cách chạy:
1. **Khởi chạy ứng dụng đồ họa (GUI):**
   ```bash
   python main.py
   ```
2. **Chạy kịch bản thực nghiệm tự động với dữ liệu mẫu:**
   ```bash
   python demo_experiments.py
   ```
3. **Chạy kiểm thử tự động (Unit Tests):**
   ```bash
   python -m unittest tests/test_scheduler.py
   ```
4. **Chạy đo kiểm hiệu năng và độ phức tạp thực nghiệm (Benchmark):**
   ```bash
   python benchmark.py
   ```
