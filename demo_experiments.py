"""
demo_experiments.py
Chương trình chạy thử nghiệm tự động với dữ liệu mẫu (Automated Test & Experiment Runner).
In ra kết quả chi tiết từng thuật toán và minh họa hoạt động của hệ thống.
"""

import sys
from datetime import datetime, timedelta
from core.models import Task, Priority, Status, Category
from core.scheduler_engine import SchedulerEngine
from core.storage import StorageManager

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')


def print_section(title: str):
    print("\n" + "=" * 80)
    print(f" {title.upper()}")
    print("=" * 80)


def run_all_experiments():
    storage = StorageManager("demo_schedule.db")
    
    # 1. Nạp dữ liệu mẫu
    print_section("1. KHỞI TẠO VÀ NẠP DỮ LIỆU MẪU (11 CÔNG VIỆC THỰC TẾ)")
    base_date = datetime(2026, 11, 4, 0, 0)
    tasks = storage.seed_sample_data(base_date=base_date)
    print(f"-> Đã nạp thành công {len(tasks)} công việc vào cơ sở dữ liệu SQLite.")
    print(f"{'Mã':<6}{'Tiêu đề':<35}{'Danh mục':<12}{'Ưu tiên':<10}{'Bắt đầu':<14}{'Kết thúc':<14}")
    print("-" * 90)
    for t in tasks:
        print(f"{t.id:<6}{t.title[:33]:<35}{t.category:<12}{t.priority.label:<10}{t.start_time.strftime('%d/%m %H:%M'):<14}{t.end_time.strftime('%d/%m %H:%M'):<14}")

    # 2. Thực nghiệm Phát hiện Xung đột Lịch trình
    print_section("2. THỬ NGHIỆM PHÁT HIỆN XUNG ĐỘT (SWEEP-LINE CONFLICT DETECTION)")
    conflicts = SchedulerEngine.detect_all_conflicts(tasks)
    print(f"-> Thuật toán quét và phát hiện thấy {len(conflicts)} cặp công việc xung đột thời gian:")
    for idx, c in enumerate(conflicts, 1):
        print(f"   [{idx}] Xung đột giữa:")
        print(f"       + Task A: '{c.task1.title}' ({c.task1.start_time.strftime('%H:%M')} -> {c.task1.end_time.strftime('%H:%M')})")
        print(f"       + Task B: '{c.task2.title}' ({c.task2.start_time.strftime('%H:%M')} -> {c.task2.end_time.strftime('%H:%M')})")
        print(f"       => Giao thoa: {c.overlap_start.strftime('%H:%M')} đến {c.overlap_end.strftime('%H:%M')} (Trùng {c.overlap_minutes} phút)")

    # 3. Thực nghiệm Gợi ý Khung giờ rảnh thông minh
    print_section("3. THỬ NGHIỆM TÌM KHE THỜI GIAN RẢNH & GỢI Ý THÔNG MINH (FREE SLOT FINDER)")
    target_day = base_date
    duration_test = 60  # cần 60 phút
    print(f"-> Tìm các khung giờ rảnh trong ngày {target_day.strftime('%d/%m/%Y')} (từ 08:00 đến 21:00) cho việc kéo dài {duration_test} phút:")
    free_slots = SchedulerEngine.find_free_slots(tasks, target_date=target_day, day_start_hour=8, day_end_hour=21, min_duration_minutes=duration_test)
    for idx, slot in enumerate(free_slots, 1):
        print(f"   Khe #{idx}: {slot.start_time.strftime('%H:%M')} -> {slot.end_time.strftime('%H:%M')} (Độ dài: {slot.duration_minutes} phút / {slot.duration_hours} giờ)")

    # Gợi ý Earliest vs Best-Fit
    earliest = SchedulerEngine.suggest_optimal_slot(tasks, duration_minutes=duration_test, target_date=target_day, strategy="earliest")
    best_fit = SchedulerEngine.suggest_optimal_slot(tasks, duration_minutes=duration_test, target_date=target_day, strategy="best_fit")
    if earliest:
        print(f"\n   -> Gợi ý theo chiến lược SỚM NHẤT (Earliest): {earliest[0].strftime('%H:%M')} -> {earliest[1].strftime('%H:%M')}")
    if best_fit:
        print(f"   -> Gợi ý theo chiến lược VỪA VẶN NHẤT (Best-Fit): {best_fit[0].strftime('%H:%M')} -> {best_fit[1].strftime('%H:%M')}")

    # 4. Thực nghiệm Sắp xếp Topo & Kiểm tra Chu trình (Kahn's DAG)
    print_section("4. THỬ NGHIỆM LẬP LỊCH PHỤ THUỘC CÔNG VIỆC (KAHN'S TOPOLOGICAL SORT)")
    sorted_tasks, warnings = SchedulerEngine.topological_sort(tasks)
    print("-> Thứ tự thực hiện hợp lệ theo chuỗi phụ thuộc (Topological Order):")
    for idx, t in enumerate(sorted_tasks, 1):
        deps_info = f"[Tiên quyết: {', '.join(t.dependencies)}]" if t.dependencies else "[Gốc / Độc lập]"
        print(f"   Bước {idx:2d}: [{t.id}] {t.title:<45} {deps_info}")

    if warnings:
        print("\n   [CẢNH BÁO VI PHẠM THỜI GIAN TRONG CHUỖI PHỤ THUỘC]:")
        for w in warnings:
            print(f"   - {w}")
    else:
        print("\n   => Không có vi phạm logic thời gian.")

    # Thử nghiệm tạo chu trình để kiểm chứng phát hiện Deadlock
    print("\n-> Kiểm chứng khả năng phát hiện Chu trình (Deadlock / Circular Dependency):")
    cyclical_tasks = [
        Task(id="CYC_1", title="Nhiệm vụ 1", start_time=base_date.replace(hour=8), end_time=base_date.replace(hour=9), dependencies=["CYC_3"]),
        Task(id="CYC_2", title="Nhiệm vụ 2", start_time=base_date.replace(hour=9), end_time=base_date.replace(hour=10), dependencies=["CYC_1"]),
        Task(id="CYC_3", title="Nhiệm vụ 3", start_time=base_date.replace(hour=10), end_time=base_date.replace(hour=11), dependencies=["CYC_2"]),
    ]
    try:
        SchedulerEngine.topological_sort(cyclical_tasks)
    except ValueError as e:
        print(f"   => BẮT NGOẠI LỆ THÀNH CÔNG: {e}")

    # 5. Thực nghiệm Quy hoạch động Lập lịch tối ưu có trọng số (Weighted Interval Scheduling)
    print_section("5. THỬ NGHIỆM QUY HOẠCH ĐỘNG LẬP LỊCH TỐI ƯU CÓ TRỌNG SỐ (WIS - DP)")
    max_weight, optimal_subset = SchedulerEngine.weighted_interval_scheduling(tasks)
    print(f"-> Đã tìm được tập con công việc KHÔNG XUNG ĐỘT tối ưu với tổng trọng số: {max_weight:.2f}")
    print(f"   Số lượng công việc được chọn: {len(optimal_subset)} / {len(tasks)} công việc ban đầu.")
    print(f"   {'Mã':<6}{'Tiêu đề':<38}{'Ưu tiên':<12}{'Khung giờ':<22}{'Thời lượng'}")
    print("   " + "-" * 85)
    for t in optimal_subset:
        time_str = f"{t.start_time.strftime('%d/%m %H:%M')} - {t.end_time.strftime('%H:%M')}"
        print(f"   {t.id:<6}{t.title[:36]:<38}{t.priority.label:<12}{time_str:<22}{t.duration_minutes}m")

    # 6. Thực nghiệm Phân loại Ma trận Eisenhower
    print_section("6. THỬ NGHIỆM PHÂN LOẠI MA TRẬN EISENHOWER (4 GÓC PHẦN TƯ)")
    quadrants = SchedulerEngine.classify_eisenhower(tasks, threshold_hours=24.0)
    names = {
        "Q1": "Góc Q1: Khẩn cấp & Quan trọng (Làm ngay)",
        "Q2": "Góc Q2: Quan trọng & Không khẩn cấp (Lên kế hoạch)",
        "Q3": "Góc Q3: Khẩn cấp & Ít quan trọng (Ủy quyền / Rút ngắn)",
        "Q4": "Góc Q4: Không khẩn cấp & Ít quan trọng (Giải trí / Loại bỏ)"
    }
    for q_key, q_tasks in quadrants.items():
        print(f"\n   [{names[q_key]}] - {len(q_tasks)} công việc:")
        for t in q_tasks:
            print(f"     • [{t.id}] {t.title} ({t.category}, Ưu tiên: {t.priority.label})")

    print("\n" + "=" * 80)
    print("      TẤT CẢ CÁC BƯỚC THỬ NGHIỆM ĐÃ HOÀN THÀNH XUẤT SẮC!")
    print("=" * 80)


if __name__ == "__main__":
    run_all_experiments()
