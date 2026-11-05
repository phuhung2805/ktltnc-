# 📅 HỆ THỐNG QUẢN LÝ LỊCH LÀM VIỆC CÁ NHÂN
### (PERSONAL SCHEDULE & TASK MANAGEMENT SYSTEM)

[![Python 3.8+](https://img.shields.io/badge/python-3.8%20%7C%203.10%20%7C%203.12-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![GUI: Tkinter](https://img.shields.io/badge/GUI-Tkinter-purple.svg)](https://docs.python.org/3/library/tkinter.html)
[![Database: SQLite3](https://img.shields.io/badge/Database-SQLite3-orange.svg)](https://docs.python.org/3/library/sqlite3.html)
[![Tests: 62 Passed](https://img.shields.io/badge/Tests-62%20Passed-brightgreen.svg)](tests/)
[![Dependencies: Zero](https://img.shields.io/badge/Dependencies-Zero%20External-success.svg)](#)

> **Môn học:** Kỹ thuật Lập trình Nâng cao (KTLTNC)  
> **Sinh viên thực hiện:** Nguyễn Phú Hưng ([@phuhung2805](https://github.com/phuhung2805)), MSSV K235480106091  
> **Giảng viên hướng dẫn:** Nghiêm Văn Tính  
> **Trường:** Đại học Kỹ thuật Công nghiệp Thái Nguyên  
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
| **🗓️ Lịch tuần** | Lưới thời gian theo tuần: các việc trùng giờ xếp cạnh nhau và viền đỏ, có vạch giờ hiện tại. Bấm vào việc để sửa, nháy đúp vào ô trống để thêm việc đúng giờ đó. |
| **📋 Danh sách** | Tìm kiếm tức thì, lọc theo danh mục và trạng thái (kể cả "Chưa xong", "Quá hạn"), bấm tiêu đề cột để sắp xếp. |
| **📝 Thêm/Sửa công việc** | Chọn ngày bằng lịch tháng, chọn giờ bằng ô tăng giảm, nút thời lượng nhanh, chọn việc tiên quyết từ danh sách; báo trùng giờ và chu trình ngay khi đang nhập. |
| **⚡ Tìm giờ rảnh** | Tìm các khoảng trống trong ngày, bỏ qua phần giờ đã qua; chọn sẵn khe theo chiến lược **Earliest** (sớm nhất) hoặc **Best-Fit** (vừa khít nhất) và điền đúng giờ đó vào công việc mới. |
| **🧭 Mức ưu tiên (Eisenhower)** | Lưới 2x2: Làm ngay, Lên kế hoạch, Làm nhanh hoặc nhờ người khác, Làm khi rảnh. |
| **📊 Thống kê** | Thẻ tổng quan; biểu đồ **Donut** theo danh mục và biểu đồ cột theo mức ưu tiên, vẽ bằng Canvas và tự co giãn theo cửa sổ. |
| **🔀 Thứ tự làm (DAG)** | Sắp xếp thứ tự thực hiện bằng thuật toán Kahn, cho biết việc nào làm được ngay, việc nào đang chờ. Chu trình phụ thuộc bị chặn ngay khi lưu. |
| **🎯 Khi trùng lịch (DP)** | Quy hoạch động chọn tập việc không trùng giờ có tổng điểm lớn nhất trong các việc còn phải làm, và chỉ ra việc nên dời; bấm một nút để tự dời các việc đó vào khe rảnh sớm nhất sau khi xem trước phương án. |
| **💾 Lưu trữ & Nhập/Xuất** | SQLite có bật khóa ngoại và chỉ mục, ghi theo giao dịch; nhập/xuất JSON từ menu Tệp, tệp lỗi được từ chối mà không làm đổi dữ liệu đang có. |
| **⌨️ Phím tắt** | Ctrl+N thêm việc, Ctrl+G tìm giờ rảnh, Ctrl+F tìm kiếm, Ctrl+S lưu, Esc đóng hộp thoại, F5 tải lại. |

---

## 🧠 3. Cơ sở lý thuyết & Bộ thuật toán cốt lõi

### 3.1. Mô hình hóa bài toán
Mỗi công việc $T_i$ được biểu diễn bằng bộ giá trị toán học:
$$T_i = \langle id_i, \text{title}_i, s_i, e_i, d_i, p_i, st_i, c_i, Dep_i \rangle$$
Trong đó $s_i, e_i$ là mốc bắt đầu và kết thúc ($e_i > s_i$), $d_i = e_i - s_i$ là thời lượng, $p_i \in \{1: \text{LOW}, 2: \text{MEDIUM}, 3: \text{HIGH}, 4: \text{URGENT}\}$, $Dep_i$ là tập mã công việc tiên quyết.

### 3.2. Thuật toán 1: Sắp xếp và quét dừng sớm phát hiện xung đột ($O(N \log N + K)$)
- **Định lý giao thoa:** Hai khoảng thời gian $[s_a, e_a)$ và $[s_b, e_b)$ giao nhau khi và chỉ khi: $\max(s_a, s_b) < \min(e_a, e_b)$.
- **Phương pháp:** Sắp xếp danh sách công việc theo `start_time`. Khi duyệt công việc $i$, chỉ xét các công việc $j > i$ và dừng ngay khi $s_j \ge e_i$, nên mỗi lần so sánh không dừng đều tạo ra một cặp xung đột. Độ phức tạp là $O(N \log N + K)$ với $K$ là số cặp xung đột; $K$ có thể lên tới $N(N-1)/2$ nên trường hợp xấu nhất vẫn là $O(N^2)$.

### 3.3. Thuật toán 2: Hợp nhất khoảng bận & Tìm khe rảnh Best-Fit ($O(N \log N)$)
1. **Merge Intervals:** Hợp nhất các khoảng bận giao nhau liên tiếp.
2. **Inversion:** Lấy phần bù trong khung giờ làm việc $[T_{start}, T_{end}]$ với các khoảng bận.
3. **Best-Fit Selection:** Chọn khe rảnh có $(L_{slot} - d_{need})$ nhỏ nhất nhưng $\ge 0$, giúp giữ lại các khoảng trống dài.

### 3.4. Thuật toán 3: Sắp xếp Topo & Bắt chu trình (Kahn's BFS - $O(V + E)$)
- Tính bán bậc vào (`in_degree`) cho từng công việc.
- Duyệt hàng đợi BFS bắt đầu từ các công việc có `in_degree == 0` (công việc độc lập).
- Nếu số đỉnh duyệt được $< V$, phát hiện chu trình bế tắc (**Deadlock**) và ném ngoại lệ `ValueError`.

### 3.5. Thuật toán 4: Lập lịch tối ưu có trọng số (Weighted Interval Scheduling DP - $O(N \log N)$)
- Sắp xếp công việc theo thời gian kết thúc: $e_1 \le e_2 \le \dots \le e_n$.
- Tìm chỉ số $p(j) = \max \{i < j \mid e_i \le s_j\}$ bằng tìm kiếm nhị phân `bisect_right` trong $O(\log N)$.
- Công thức truy hồi Quy hoạch động:
  $$OPT(j) = \max\Big(w_j + OPT(p(j)), \; OPT(j-1)\Big), \quad \text{với } OPT(0) = 0$$
- Trọng số: $w_j = 10 \times 3^{p_j - 1} + \max\left(1, \frac{120}{\max(30, d_j)}\right)$. Phần đầu tăng theo cấp số nhân để một việc Khẩn cấp thắng hai việc Cao; phần sau nhỉnh hơn cho việc ngắn. Chỉ xét các việc còn phải làm.

### 3.6. Thuật toán 5: Phân làn cho lịch tuần (Interval Partitioning - $O(N \log N)$)
- Duyệt công việc theo $s_i$, dùng min-heap theo $e_i$ để tái sử dụng làn sớm rảnh nhất, nhờ đó các việc trùng giờ được vẽ cạnh nhau mà không chồng lên nhau.

---

## 📊 4. Đánh giá độ phức tạp lý thuyết

| Thuật toán / Thao tác | Cấu trúc dữ liệu | Thời gian tốt nhất | Thời gian trung bình | Thời gian xấu nhất | Bộ nhớ (Space) |
| :--- | :--- | :---: | :---: | :---: | :---: |
| **Tra cứu công việc theo ID** | Hash Map / SQLite Index | $O(1)$ | $O(1)$ | $O(1)$ | $O(1)$ |
| **Quét xung đột** | Sorted List | $O(N \log N)$ | $O(N \log N + K)$ | $O(N^2)$ *(khi mọi cặp đều trùng)* | $O(N)$ |
| **So sánh cặp (Brute-Force)** | Nested Loop | $O(N^2)$ | $O(N^2)$ | $O(N^2)$ | $O(1)$ |
| **Hợp nhất khoảng bận (Merge)** | Sorted List | $O(N \log N)$ | $O(N \log N)$ | $O(N \log N)$ | $O(N)$ |
| **Tìm khe rảnh (Best-Fit)** | Interval List | $O(N \log N)$ | $O(N \log N)$ | $O(N \log N)$ | $O(N)$ |
| **Sắp xếp Topo (Kahn BFS)** | Adjacency List + Queue | $O(V + E)$ | $O(V + E)$ | $O(V + E)$ | $O(V + E)$ |
| **Lập lịch tối ưu có trọng số (DP)**| Sorted Array + Bisect | $O(N \log N)$ | $O(N \log N)$ | $O(N \log N)$ | $O(N)$ |
| **Phân loại Eisenhower** | Linear Scan | $O(N)$ | $O(N)$ | $O(N)$ | $O(N)$ |

---

## 📈 5. Kết quả đo kiểm hiệu năng thực tế (Benchmark)

Kết quả chạy `python benchmark.py` một lần trên Python 3.12, Windows 11, seed cố định, mỗi phép đo lấy trung vị 5 lần chạy (Brute-Force đo 1 lần, chỉ đo đến $N = 4,000$). Thời gian tuyệt đối thay đổi theo máy và có nhiễu giữa các lần chạy.

**Phát hiện xung đột, mật độ thực tế (khoảng 8 việc/ngày):**

| $N$ | $K$ | Quét (ms) | Brute-Force (ms) |
| :---: | :---: | :---: | :---: |
| 1,000 | 559 | 1.90 | 501.19 |
| 2,000 | 1,103 | 4.75 | 2,346.97 |
| 4,000 | 2,204 | 17.42 | 8,873.20 |
| 8,000 | 4,546 | 19.39 | không đo |
| 16,000 | 8,972 | 61.39 | không đo |

**Phát hiện xung đột, mật độ cao (mọi việc dồn vào 5 ngày):**

| $N$ | $K$ | Quét (ms) | Brute-Force (ms) |
| :---: | :---: | :---: | :---: |
| 1,000 | 13,861 | 30.66 | 516.67 |
| 2,000 | 56,781 | 161.71 | 2,274.59 |
| 4,000 | 225,270 | 612.94 | 11,969.21 |
| 8,000 | 895,044 | 3,052.14 | không đo |
| 16,000 | 3,582,291 | 14,137.27 | không đo |

**Các thuật toán còn lại:**

| $N$ | Free Slot (ms) | WIS DP (ms) | Kahn Topo (ms) |
| :---: | :---: | :---: | :---: |
| 1,000 | 1.76 | 5.34 | 2.03 |
| 2,000 | 3.79 | 12.29 | 3.18 |
| 4,000 | 9.40 | 23.39 | 9.25 |
| 8,000 | 20.81 | 46.43 | 27.66 |
| 16,000 | 59.37 | 118.52 | 82.48 |

> [!NOTE]
> **Nhận xét:**
> - Thời gian quét phụ thuộc vào $K$. Ở mật độ cao, $K$ tăng theo $N^2$ nên $N$ gấp đôi thì thời gian tăng khoảng 4–5 lần, tức vẫn gần bậc hai, dù nhanh hơn Brute-Force khoảng 14–20 lần.
> - Ở mật độ thực tế, $K$ nhỏ nên quét nhanh hơn Brute-Force hàng trăm lần.
> - Với lịch cá nhân vài nghìn việc, các thuật toán đều chạy trong khoảng vài chục mili-giây trở xuống.

---

## 📂 6. Cấu trúc mã nguồn dự án

```text
d:\ktltnc\
│
├── core\                                    # Bộ máy thuật toán và mô hình cốt lõi
│   ├── __init__.py
│   ├── models.py                            # Thực thể Task, Priority, Status, Category
│   ├── scheduler_engine.py                  # Phát hiện xung đột, Best-Fit, Kahn Topo, WIS DP, phân làn
│   └── storage.py                           # Quản lý SQLite & JSON
│
├── ui\                                      # Giao diện đồ họa người dùng (Tkinter)
│   ├── __init__.py
│   ├── theme.py                             # Bảng màu, typography và kiểu dáng ttk
│   ├── widgets.py                           # Nút bấm, chọn ngày giờ, gợi ý nổi dùng chung
│   ├── calendar_view.py                     # Lịch tuần dạng lưới thời gian
│   ├── task_dialog.py                       # Form Thêm/Sửa task với kiểm tra xung đột trực tiếp
│   ├── smart_slot_dialog.py                 # Hộp thoại tìm giờ rảnh
│   ├── planning_views.py                    # Thứ tự làm (Kahn) và Khi trùng lịch (DP)
│   ├── eisenhower_view.py                   # Ma trận trực quan 4 góc phần tư Eisenhower
│   ├── analytics_view.py                    # Dashboard thống kê KPI, Donut Chart & Bar Chart
│   └── main_window.py                       # Cửa sổ chính đa tab
│
├── tests\                                   # Kiểm thử tự động (Unit Tests)
│   ├── __init__.py
│   ├── test_scheduler.py                    # Kiểm thử thuật toán và lưu trữ
│   └── test_ui.py                           # Kiểm thử giao diện trên cửa sổ thật
│
├── data\                                    # Dữ liệu kiểm thử
│   └── sample_schedule.json                 # 11 công việc mẫu thực tế
│
├── benchmark.py                             # Đo kiểm thời gian thực thi (N = 1,000 .. 16,000)
├── experiments.py                           # Đối chiếu với vét cạn, so sánh với tham lam, đo hàng đợi Kahn
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

### 3. Chạy toàn bộ 62 bài kiểm thử tự động:
```bash
python -m unittest discover -s tests -t .
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
