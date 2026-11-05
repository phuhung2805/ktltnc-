"""
benchmark.py
Chương trình đo lường và đánh giá độ phức tạp thực nghiệm (Empirical Complexity Analysis)
của các thuật toán lập lịch chính:
1. Phát hiện xung đột: Sắp xếp và quét dừng sớm O(N log N + K) vs Brute-Force O(N^2)
2. Interval Merging & Free Slot Finder O(N log N)
3. Weighted Interval Scheduling via Dynamic Programming O(N log N)
4. Topological Sort Kahn's Algorithm O(V + E)

Dữ liệu sinh với seed cố định, mỗi phép đo lấy trung vị của nhiều lần chạy để kết quả ổn định và lặp lại được.
Phát hiện xung đột được đo ở hai mật độ vì thời gian chạy phụ thuộc vào K (số cặp xung đột).
"""

import platform
import random
import statistics
import sys
import time
from datetime import datetime, timedelta
from typing import Callable, List, Optional
from core.models import Task, Priority, Status
from core.scheduler_engine import SchedulerEngine, ConflictResult

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

SEED = 42
REPEATS = 5
BRUTE_FORCE_LIMIT = 5000
TASKS_PER_DAY_REALISTIC = 8
DENSE_SPAN_DAYS = 5


def generate_random_tasks(n: int, base_date: datetime, span_days: int = 7) -> List[Task]:
    """Sinh ngẫu nhiên n công việc trong khoảng span_days ngày."""
    tasks = []
    categories = ["Công việc", "Học tập", "Cá nhân", "Sức khỏe", "Họp hành"]
    priorities = list(Priority)

    for i in range(n):
        day_offset = random.randint(0, span_days - 1)
        start_hour = random.randint(7, 20)
        start_minute = random.choice([0, 15, 30, 45])
        duration_minutes = random.choice([30, 45, 60, 90, 120])

        start_time = base_date + timedelta(days=day_offset, hours=start_hour, minutes=start_minute)
        end_time = start_time + timedelta(minutes=duration_minutes)

        task = Task(
            id=f"T{i:05d}",
            title=f"Công việc thử nghiệm #{i+1}",
            start_time=start_time,
            end_time=end_time,
            category=random.choice(categories),
            priority=random.choice(priorities),
            status=Status.PENDING
        )
        tasks.append(task)
    return tasks


def generate_dag_tasks(n: int, base_date: datetime) -> List[Task]:
    """Sinh danh sách n công việc có phụ thuộc theo mô hình DAG không chu trình."""
    tasks = []
    for i in range(n):
        start = base_date + timedelta(minutes=i * 15)
        end = start + timedelta(minutes=30)
        deps = []
        # Mỗi task có xác suất phụ thuộc vào 1-3 task trước đó
        if i > 0 and random.random() < 0.6:
            num_deps = random.randint(1, min(3, i))
            deps = [f"DAG_{j:05d}" for j in random.sample(range(i), num_deps)]

        task = Task(
            id=f"DAG_{i:05d}",
            title=f"DAG Task #{i+1}",
            start_time=start,
            end_time=end,
            dependencies=deps
        )
        tasks.append(task)
    return tasks


def brute_force_conflict_detection(tasks: List[Task]) -> List[ConflictResult]:
    """Thuật toán Brute-Force O(N^2) kiểm tra từng cặp; tạo cùng kết quả với thuật toán chính để so sánh công bằng."""
    conflicts = []
    n = len(tasks)
    for i in range(n):
        for j in range(i + 1, n):
            if tasks[i].is_overlapping_with(tasks[j]):
                conflicts.append(ConflictResult(tasks[i], tasks[j]))
    return conflicts


def measure_ms(func: Callable[[], object], repeats: int = REPEATS) -> float:
    """Trung vị thời gian chạy (ms) của func qua nhiều lần đo."""
    samples = []
    for _ in range(repeats):
        t0 = time.perf_counter()
        func()
        samples.append((time.perf_counter() - t0) * 1000.0)
    return statistics.median(samples)


def format_ms(value: Optional[float]) -> str:
    return "không đo" if value is None else f"{value:,.2f}"


def format_growth(current: float, previous: Optional[float]) -> str:
    return "-" if previous is None else f"x{current / previous:.1f}"


def run_conflict_benchmark(title: str, sizes: List[int], make_tasks: Callable[[int], List[Task]]) -> List[dict]:
    print(f"\n{title}")
    print(f"{'N':>7} {'K (cặp xung đột)':>17} {'Quét (ms)':>12} {'Tăng':>6} {'Brute-Force (ms)':>18} {'Tăng':>6} {'Nhanh hơn':>10}")
    print("-" * 84)
    results = []
    prev_scan = prev_brute = None
    for n in sizes:
        tasks = make_tasks(n)
        k = len(SchedulerEngine.detect_all_conflicts(tasks))
        scan_ms = measure_ms(lambda: SchedulerEngine.detect_all_conflicts(tasks))
        brute_ms = None
        if n <= BRUTE_FORCE_LIMIT:
            # Brute-Force chạy lâu nên chỉ đo một lần
            brute_ms = measure_ms(lambda: brute_force_conflict_detection(tasks), repeats=1)
        ratio = f"{brute_ms / scan_ms:.1f} lần" if brute_ms else "-"
        print(f"{n:>7} {k:>17,} {scan_ms:>12,.2f} {format_growth(scan_ms, prev_scan):>6} "
              f"{format_ms(brute_ms):>18} {format_growth(brute_ms, prev_brute) if brute_ms else '-':>6} {ratio:>10}")
        results.append({"n": n, "k": k, "scan_ms": scan_ms, "brute_force_ms": brute_ms})
        prev_scan, prev_brute = scan_ms, brute_ms
    return results


def run_algorithm_benchmark(sizes: List[int], base_date: datetime) -> List[dict]:
    print("\nCÁC THUẬT TOÁN CÒN LẠI (dữ liệu gồm N công việc, nhân đôi N để xem tốc độ tăng)")
    print(f"{'N':>7} {'Free Slot (ms)':>15} {'Tăng':>6} {'WIS DP (ms)':>13} {'Tăng':>6} {'Kahn Topo (ms)':>15} {'Tăng':>6}")
    print("-" * 74)
    results = []
    prev_fs = prev_wis = prev_topo = None
    for n in sizes:
        tasks = generate_random_tasks(n, base_date, span_days=DENSE_SPAN_DAYS)
        # Xếp mọi công việc vào cùng một ngày để Free Slot phải xử lý đủ N khoảng bận
        same_day = generate_random_tasks(n, base_date, span_days=1)
        dag_tasks = generate_dag_tasks(n, base_date)

        fs_ms = measure_ms(lambda: SchedulerEngine.find_free_slots(same_day, target_date=base_date, day_start_hour=7, day_end_hour=22))
        wis_ms = measure_ms(lambda: SchedulerEngine.weighted_interval_scheduling(tasks))
        topo_ms = measure_ms(lambda: SchedulerEngine.topological_sort(dag_tasks))

        print(f"{n:>7} {fs_ms:>15,.2f} {format_growth(fs_ms, prev_fs):>6} {wis_ms:>13,.2f} {format_growth(wis_ms, prev_wis):>6} "
              f"{topo_ms:>15,.2f} {format_growth(topo_ms, prev_topo):>6}")
        results.append({"n": n, "free_slot_ms": fs_ms, "wis_dp_ms": wis_ms, "topo_sort_ms": topo_ms})
        prev_fs, prev_wis, prev_topo = fs_ms, wis_ms, topo_ms
    return results


def run_benchmark():
    random.seed(SEED)
    base_date = datetime(2026, 11, 4, 0, 0)

    print("=" * 84)
    print("      ĐÁNH GIÁ ĐỘ PHỨC TẠP THỰC NGHIỆM - BENCHMARK THUẬT TOÁN LẬP LỊCH")
    print("=" * 84)
    print(f"Môi trường: Python {platform.python_version()}, {platform.system()} {platform.release()}, {platform.processor()}")
    print(f"Seed = {SEED}, mỗi phép đo lấy trung vị của {REPEATS} lần chạy (Brute-Force đo 1 lần).")

    sizes = [1000, 2000, 4000, 8000, 16000]
    realistic = run_conflict_benchmark(
        f"PHÁT HIỆN XUNG ĐỘT - Mật độ thực tế (~{TASKS_PER_DAY_REALISTIC} việc/ngày, K tăng tuyến tính theo N)",
        sizes,
        lambda n: generate_random_tasks(n, base_date, span_days=max(1, n // TASKS_PER_DAY_REALISTIC))
    )
    dense = run_conflict_benchmark(
        f"PHÁT HIỆN XUNG ĐỘT - Mật độ cao (mọi việc dồn vào {DENSE_SPAN_DAYS} ngày, K tăng theo N^2)",
        sizes,
        lambda n: generate_random_tasks(n, base_date, span_days=DENSE_SPAN_DAYS)
    )
    others = run_algorithm_benchmark(sizes, base_date)

    print("\n" + "=" * 84)
    print("CÁCH ĐỌC KẾT QUẢ:")
    print("- Khi N tăng gấp đôi: O(N log N) tăng khoảng 2 lần, O(N^2) tăng khoảng 4 lần.")
    print("- Phát hiện xung đột là O(N log N + K): thời gian gần tuyến tính khi K nhỏ, nhưng tiến về O(N^2) khi K ~ N^2.")
    print("=" * 84)
    return {"realistic": realistic, "dense": dense, "others": others}


if __name__ == "__main__":
    run_benchmark()
