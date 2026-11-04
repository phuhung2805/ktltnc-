# 📅 HỆ THỐNG QUẢN LÝ LỊCH LÀM VIỆC CÁ NHÂN
### (PERSONAL SCHEDULE & TASK MANAGEMENT SYSTEM)

[![Python 3.8+](https://img.shields.io/badge/python-3.8%20%7C%203.10%20%7C%203.12-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![GUI: Tkinter](https://img.shields.io/badge/GUI-Tkinter%20Modern%20Dark-purple.svg)](https://docs.python.org/3/library/tkinter.html)
[![Database: SQLite3](https://img.shields.io/badge/Database-SQLite3-orange.svg)](https://docs.python.org/3/library/sqlite3.html)
[![Tests: 11/11 Passed](https://img.shields.io/badge/Tests-11%2F11%20Passed-brightgreen.svg)](tests/test_scheduler.py)
[![Dependencies: Zero](https://img.shields.io/badge/Dependencies-Zero%20External-success.svg)](#)

> **Môn học:** Kỹ thuật Lập trình Nâng cao (KTLTNC)  
> **Sinh viên thực hiện:** Nguyễn Phú Hưng ([@phuhung2805](https://github.com/phuhung2805))  
> **Báo cáo chuyên môn (Word & Markdown):**
> - 📄 **Tệp Báo cáo Word hoàn chỉnh (.docx):** [`BAO_CAO_MON_HOC_KTLTNC_QUAN_LY_LICH.docx`](BAO_CAO_MON_HOC_KTLTNC_QUAN_LY_LICH.docx)
> - 📝 **Tệp Báo cáo Lý thuyết & Thực nghiệm (.md):** [`BAO_CAO_LY_THUYET_VA_THUC_NGHIEM.md`](BAO_CAO_LY_THUYET_VA_THUC_NGHIEM.md)

---

## 📑 MỤC LỤC
1. [Giới thiệu tổng quan](#-1-giới-thiệu-tổng-quan)
2. [Các tính năng nổi bật](#-2-các-tính-năng-nổi-bật)
3. [Cơ sở lý thuyết & Bộ thuật toán cốt lõi](#-3-cơ-sở-lý-thuyết--bộ-thuật-toán-cốt-lõi)
4. [Đánh giá độ phức tạp lý thuyết (Complexity Analysis)](#-4-đánh-giá-độ-phức-tạp-lý-thuyết)
5. [Kết quả đo kiểm hiệu năng thực tế (Benchmark)](#-5-kết-quả-đo-kiểm-hiệu-năng-thực-tế-benchmark)
6. [Cấu trúc mã nguồn dự án](#-6-cấu-trúc-mã-nguồn-dự-án)
7. [Hướng dẫn cài đặt & Khởi chạy](#-7-hướng-dẫn-cài-đặt--khởi-chạy)
8. [Tài liệu học thuật đính kèm](#-8-tài-liệu-học-thuật-đính-kèm)

---

## 📌 1. Giới thiệu tổng quan

Chương trình **Quản lý Lịch làm việc Cá nhân** là một giải pháp công nghệ toàn diện hỗ trợ sinh viên và người đi làm tối ưu hóa quỹ thời gian hàng ngày. Thay vì chỉ dừng lại ở các thao tác CRUD cơ bản như các ứng dụng To-Do thông thường, hệ thống tích hợp sâu các mô hình khoa học máy tính kinh điển và giải thuật tối ưu:
- **Xử lý xung đột thời gian (Interval Conflict Detection):** Không cho phép hoặc cảnh báo ngay khi các công việc bị trùng khung giờ.
- **Khắc phục phân mảnh thời gian (Time Fragmentation):** Tìm kiếm và gợi ý các khoảng rảnh thích hợp nhất theo nguyên lý **Best-Fit**.
- **Giải quyết bài toán phụ thuộc (Prerequisite Dependencies):** Mô hình hóa theo Đồ thị có hướng không chu trình (**DAG**) và phát hiện bế tắc lặp (**Deadlock**).
- **Lập lịch tối ưu khi có mâu thuẫn:** Áp dụng **Quy hoạch động (Weighted Interval Scheduling)** để tìm ra tập công việc đem lại giá trị năng suất cao nhất.
- **Phân loại chiến lược Eisenhower:** Phân nhóm 4 góc phần tư theo mức độ khẩn cấp và tầm quan trọng.

---

## ✨ 2. Các tính năng nổi bật

| Phân hệ / Tính năng | Mô tả chi tiết |
| :--- | :--- |
| **📋 Lịch biểu & Danh sách** | Giao diện Treeview hiện đại, lọc nhanh theo từ khóa, danh mục, trạng thái; gán mã màu trực quan theo độ ưu tiên (Khẩn cấp: đỏ, Cao: vàng, Hoàn thành: xanh ngọc). |
| **🧭 Ma trận Eisenhower** | Bố cục lưới 2x2 thể hiện 4 góc phần tư: **Q1** (Làm ngay), **Q2** (Lên kế hoạch), **Q3** (Ủy quyền/Giảm thiểu), **Q4** (Giải trí/Loại bỏ). |
| **📊 Thống kê & Dashboard** | Thẻ KPI tổng quan; biểu đồ tròn **Donut Chart** phân bổ theo danh mục và biểu đồ cột **Bar Chart** phân bổ theo độ ưu tiên được vẽ trực tiếp bằng Canvas siêu nhẹ. |
| **⚡ Gợi ý khe rảnh thông minh** | Tự động phân tích các khoảng bận trong ngày và đề xuất khung giờ tối ưu theo chiến lược **Earliest** (sớm nhất) hoặc **Best-Fit** (vừa vặn nhất). |
| **⚠️ Quét & Cảnh báo xung đột** | Kiểm tra xung đột thời gian thực ngay khi người dùng gõ ngày giờ trong form, modal cảnh báo toàn bộ các cặp công việc giao thoa. |
| **🔀 Đồ thị Phụ thuộc (DAG)** | Sắp xếp thứ tự thực thi hợp lệ và phát hiện chu trình lặp (Deadlock/Circular Dependency) bằng thuật toán Kahn. |
| **🎯 Lập lịch Tối ưu (DP)** | Giải thuật Quy hoạch động chọn tập công việc tương thích có tổng trọng số điểm lớn nhất. |
| **💾 Lưu trữ bền vững & Nhập/Xuất** | Cơ sở dữ liệu SQLite cục bộ bền vững với Transaction an toàn; hỗ trợ Nhập/Xuất tệp JSON tiện lợi. |

---

## 🧠 3. Cơ sở lý thuyết & Bộ thuật toán cốt lõi

### 3.1. Mô hình hóa bài toán
Mỗi công việc $T_i$ được biểu diễn bằng bộ giá trị toán học:
$$T_i = \langle id_i, \text{title}_i, s_i, e_i, d_i, p_i, st_i, c_i, Dep_i \rangle$$
Trong đó $s_i, e_i$ là mốc bắt đầu và kết thúc ($e_i > s_i$), $d_i = e_i - s_i$ là thời lượng, $p_i \in \{1: \text{LOW}, 2: \text{MEDIUM}, 3: \text{HIGH}, 4: \text{URGENT}\}$, $Dep_i$ là tập mã công việc tiên quyết.

### 3.2. Thuật toán 1: Quét đường thẳng phát hiện xung đột (Sweep-Line - $O(N \log N)$)
- **Định lý giao thoa:** Hai khoảng thời gian $[s_a, e_a)$ và $[s_b, e_b)$ giao nhau khi và chỉ khi: $\max(s_a, s_b) < \min(e_a, e_b)$.
- **Phương pháp Sweep-Line:** Sắp xếp danh sách công việc theo `start_time`. Khi duyệt công việc $i$, chỉ xét các công việc $j > i$ và dừng ngay lập tức khi $s_j \ge e_i$. Giảm thiểu số phép so sánh từ $O(N^2)$ xuống $O(N \log N + K)$.

### 3.3. Thuật toán 2: Hợp nhất khoảng bận & Tìm khe rảnh Best-Fit ($O(N \log N)$)
1. **Merge Intervals:** Hợp nhất các khoảng bận giao nhau liên tiếp.
2. **Inversion:** Lấy phần bù trong khung giờ làm việc $[T_{start}, T_{end}]$ với các khoảng bận.
3. **Best-Fit Selection:** Chọn khe rảnh có $(L_{slot} - d_{need})$ nhỏ nhất nhưng $\ge 0$, triệt tiêu sự phân mảnh thời gian.

### 3.4. Thuật toán 3: Sắp xếp Topo & Bắt chu trình (Kahn's BFS - $O(V + E)$)
- Tính bán bậc vào (`in_degree`) cho từng công việc.
- Duyệt hàng đợi BFS bắt đầu từ các công việc có `in_degree == 0` (công việc độc lập).
- Nếu số đỉnh duyệt được $< V$, phát hiện chu trình bế tắc (**Deadlock**) và ném ngoại lệ `ValueError`.

### 3.5. Thuật toán 4: Lập lịch tối ưu có trọng số (Weighted Interval Scheduling DP - $O(N \log N)$)
- Sắp xếp công việc theo thời gian kết thúc: $e_1 \le e_2 \le \dots \le e_n$.
- Tìm chỉ số $p(j) = \max \{i < j \mid e_i \le s_j\}$ bằng tìm kiếm nhị phân `bisect_right` trong $O(\log N)$.
- Công thức truy hồi Quy hoạch động:
  $$OPT(j) = \max\Big(w_j + OPT(p(j)), \; OPT(j-1)\Big), \quad \text{với } OPT(0) = 0$$
- Trọng số tối ưu hóa: $w_j = p_j \times 10 + \max\left(1.0, \frac{120}{\max(30, d_j)}\right)$.

---

## 📊 4. Đánh giá độ phức tạp lý thuyết

| Thuật toán / Thao tác | Cấu trúc dữ liệu | Thời gian tốt nhất | Thời gian trung bình | Thời gian xấu nhất | Bộ nhớ (Space) |
| :--- | :--- | :---: | :---: | :---: | :---: |
| **Tra cứu công việc theo ID** | Hash Map / SQLite Index | $O(1)$ | $O(1)$ | $O(1)$ | $O(1)$ |
| **Quét xung đột (Sweep-Line)** | Sorted List | $O(N \log N)$ | $O(N \log N + K)$ | $O(N^2)$ *(nếu trùng 100%)* | $O(N)$ |
| **So sánh cặp (Brute-Force)** | Nested Loop | $O(N^2)$ | $O(N^2)$ | $O(N^2)$ | $O(1)$ |
| **Hợp nhất khoảng bận (Merge)** | Sorted List | $O(N \log N)$ | $O(N \log N)$ | $O(N \log N)$ | $O(N)$ |
| **Tìm khe rảnh (Best-Fit)** | Interval List | $O(N \log N)$ | $O(N \log N)$ | $O(N \log N)$ | $O(N)$ |
| **Sắp xếp Topo (Kahn BFS)** | Adjacency List + Queue | $O(V + E)$ | $O(V + E)$ | $O(V + E)$ | $O(V + E)$ |
| **Lập lịch tối ưu có trọng số (DP)**| Sorted Array + Bisect | $O(N \log N)$ | $O(N \log N)$ | $O(N \log N)$ | $O(N)$ |
| **Phân loại Eisenhower** | Linear Scan | $O(N)$ | $O(N)$ | $O(N)$ | $O(N)$ |

---

## 📈 5. Kết quả đo kiểm hiệu năng thực tế (Benchmark)

Thực nghiệm đo thời gian thực thi (mili-giây) trên cùng phần cứng với quy mô từ $N = 100$ đến $N = 10,000$ công việc:

| Quy mô dữ liệu ($N$) | Sweep-Line ($O(N \log N)$) | Brute-Force ($O(N^2)$) | Free Slot Finder | WIS DP ($O(N \log N)$) | Kahn Topo ($O(V+E)$) |
| :---: | :---: | :---: | :---: | :---: | :---: |
| **$N = 100$** | **0.36 ms** | 3.42 ms | 0.06 ms | 0.49 ms | 0.28 ms |
| **$N = 500$** | **7.16 ms** | 107.62 ms | 0.19 ms | 2.34 ms | 1.38 ms |
| **$N = 1,000$** | **28.46 ms** | 411.89 ms | 0.35 ms | 3.82 ms | 2.46 ms |
| **$N = 2,500$** | **183.03 ms** | 2,940.37 ms | 1.19 ms | 23.63 ms | 8.46 ms |
| **$N = 5,000$** | **1,090.89 ms** | *Quá tải (> 12s)* | 1.58 ms | 25.38 ms | 11.48 ms |
| **$N = 10,000$** | **8,134.86 ms** | *Không khả thi* | 9.28 ms | 223.46 ms | 75.00 ms |

> [!TIP]
> **Nhận xét thực nghiệm:**
> - Ở quy mô $N = 2,500$, thuật toán Sweep-Line chạy nhanh hơn Brute-Force **hơn 16 lần**.
> - Tìm kiếm khe rảnh cho $10,000$ công việc chỉ mất **9.28 ms**; duyệt sắp xếp Topo mạng lưới $10,000$ công việc có phụ thuộc chỉ mất **75 ms**. Hệ thống hoàn toàn đáp ứng khả năng phản hồi tức thời (Real-time).

---

## 📂 6. Cấu trúc mã nguồn dự án

```text
d:\ktltnc\
│
├── core\                                    # Bộ máy thuật toán và mô hình cốt lõi
│   ├── __init__.py
│   ├── models.py                            # Thực thể Task, Priority, Status, Category
│   ├── scheduler_engine.py                  # Sweep-Line, Best-Fit, Kahn Topo, WIS DP
│   └── storage.py                           # Quản lý SQLite & JSON
│
├── ui\                                      # Giao diện đồ họa người dùng (Tkinter Modern Dark)
│   ├── __init__.py
│   ├── theme.py                             # Thiết lập bảng màu Dark & Typography
│   ├── task_dialog.py                       # Form Thêm/Sửa task với kiểm tra xung đột trực tiếp
│   ├── smart_slot_dialog.py                 # Modal phân tích & tự động chọn khung giờ rảnh
│   ├── eisenhower_view.py                   # Ma trận trực quan 4 góc phần tư Eisenhower
│   ├── analytics_view.py                    # Dashboard thống kê KPI, Donut Chart & Bar Chart
│   └── main_window.py                       # Cửa sổ chính đa tab
│
├── tests\                                   # Kiểm thử tự động (Unit Tests)
│   ├── __init__.py
│   └── test_scheduler.py                    # 11 ca kiểm thử toàn diện (Passed 100%)
│
├── data\                                    # Dữ liệu kiểm thử
│   └── sample_schedule.json                 # 11 công việc mẫu thực tế
│
├── benchmark.py                             # Đo kiểm thời gian thực thi (N = 100 .. 10,000)
├── demo_experiments.py                      # Chạy toàn bộ kịch bản thực nghiệm mẫu
├── generate_docx_report.py                  # Script sinh tệp báo cáo Word chuẩn OpenXML
├── main.py                                  # Điểm khởi chạy ứng dụng GUI
├── BAO_CAO_MON_HOC_KTLTNC_QUAN_LY_LICH.docx # Tệp Báo cáo Word chính thức
├── BAO_CAO_LY_THUYET_VA_THUC_NGHIEM.md      # Tệp Báo cáo Markdown chi tiết
├── README.md                                # Tài liệu giới thiệu dự án
└── LICENSE                                  # Giấy phép nguồn mở MIT
```

---

## 🚀 7. Hướng dẫn cài đặt & Khởi chạy

### Yêu cầu hệ thống:
- Cài đặt sẵn **Python 3.8+** (khuyến nghị Python 3.10 - 3.12).
- Sử dụng hoàn toàn thư viện chuẩn (`tkinter`, `sqlite3`, `json`, `datetime`, `bisect`, `heapq`), **không cần cài đặt bất kỳ gói pip bên ngoài nào**!

### 1. Khởi chạy ứng dụng đồ họa (GUI):
```bash
python main.py
```

### 2. Chạy kịch bản thực nghiệm mẫu và xem kết quả:
```bash
python demo_experiments.py
```

### 3. Chạy 11 bài kiểm thử tự động (Unit Tests):
```bash
python -m unittest tests/test_scheduler.py
```

### 4. Chạy kiểm chứng hiệu năng Benchmark:
```bash
python benchmark.py
```

### 5. Biên dịch lại tệp Báo cáo Word (.docx):
```bash
python generate_docx_report.py
```

---

## 📚 8. Tài liệu học thuật đính kèm

Trong kho lưu trữ đã bao gồm đầy đủ 2 tài liệu báo cáo học thuật:
1. **[BAO_CAO_MON_HOC_KTLTNC_QUAN_LY_LICH.docx](BAO_CAO_MON_HOC_KTLTNC_QUAN_LY_LICH.docx):**  
   Tệp Word hoàn chỉnh với Trang bìa, Lời cam đoan, Lời cảm ơn, Mục lục có số trang, Danh mục từ viết tắt, 5 Chương nội dung (có kết luận từng chương), Kết luận chung, Tài liệu tham khảo chuẩn IEEE và Phụ lục.
2. **[BAO_CAO_LY_THUYET_VA_THUC_NGHIEM.md](BAO_CAO_LY_THUYET_VA_THUC_NGHIEM.md):**  
   Báo cáo Markdown chi tiết với công thức toán học KaTeX, lưu đồ Mermaid và phân tích thuật toán chuyên sâu.

---

## 📄 Bản quyền & Giấy phép
Dự án được phát hành theo giấy phép **[MIT License](LICENSE)**. Toàn bộ mã nguồn mở tự do sử dụng cho mục đích học tập và nghiên cứu.
