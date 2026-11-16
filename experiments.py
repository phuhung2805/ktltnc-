"""
experiments.py
Các thực nghiệm phục vụ báo cáo, bổ sung cho benchmark.py. Seed cố định nên kết quả (trừ thời gian đo) lặp lại được:
1. Đối chiếu kết quả các thuật toán với nghiệm vét cạn trên dữ liệu ngẫu nhiên.
2. Quy hoạch động so với vét cạn 2^N về thời gian.
3. Quy hoạch động so với tham lam về chất lượng nghiệm.
4. Hiệu quả của cấu trúc hàng đợi trong thuật toán Kahn.
5. Gỡ trùng lịch tự động trên dữ liệu ngẫu nhiên.
Kết quả được in ra màn hình và ghi vào tệp JSON nếu truyền đường dẫn.
"""

import itertools
import json
import random
import statistics
import sys
import time
from datetime import datetime, timedelta
from typing import List, Tuple

from core.models import Task, Priority
from core.scheduler_engine import SchedulerEngine

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

SEED = 2026
BASE = datetime(2026, 11, 2)


def random_day_tasks(rng: random.Random, n: int, span_minutes: int = 780) -> List[Task]:
    """Sinh n công việc trong một ngày làm việc (bắt đầu từ 08:00, mặc định dài 13 giờ)."""
    tasks = []
    for i in range(n):
        start = BASE + timedelta(hours=8, minutes=rng.randrange(0, span_minutes, 15))
        tasks.append(Task(
            title=str(i), id=str(i), start_time=start,
            end_time=start + timedelta(minutes=rng.choice([30, 45, 60, 90, 120, 180])),
            priority=rng.choice(list(Priority))
        ))
    return tasks


def exhaustive_best(tasks: List[Task]) -> float:
    """Vét cạn mọi tập con, giữ lại tập không xung đột có tổng trọng số lớn nhất. O(2^N * N^2)."""
    weight = SchedulerEngine.task_weight
    best = 0.0
    for size in range(len(tasks) + 1):
        for subset in itertools.combinations(tasks, size):
            if all(not a.is_overlapping_with(b) for a, b in itertools.combinations(subset, 2)):
                best = max(best, sum(weight(t) for t in subset))
    return best


def greedy_by_weight(tasks: List[Task]) -> float:
    """Tham lam: duyệt theo trọng số giảm dần, nhận việc nếu không xung đột với các việc đã nhận."""
    weight = SchedulerEngine.task_weight
    chosen: List[Task] = []
    for task in sorted(tasks, key=weight, reverse=True):
        if not any(task.is_overlapping_with(c) for c in chosen):
            chosen.append(task)
    return sum(weight(t) for t in chosen)


def greedy_by_end_time(tasks: List[Task]) -> float:
    """Tham lam: chọn việc kết thúc sớm nhất, tối ưu về số việc nhưng bỏ qua trọng số."""
    chosen: List[Task] = []
    for task in sorted(tasks, key=lambda t: t.end_time):
        if not chosen or task.start_time >= chosen[-1].end_time:
            chosen.append(task)
    return sum(SchedulerEngine.task_weight(t) for t in chosen)


def experiment_correctness(rng: random.Random, rounds: int = 1500) -> dict:
    """Đối chiếu phát hiện xung đột, tìm khe rảnh và quy hoạch động với nghiệm vét cạn."""
    conflict_errors = dp_errors = trace_errors = slot_errors = 0
    for _ in range(rounds):
        tasks = random_day_tasks(rng, rng.randint(0, 11), span_minutes=600)

        pairs = sum(a.is_overlapping_with(b) for a, b in itertools.combinations(tasks, 2))
        conflict_errors += pairs != len(SchedulerEngine.detect_all_conflicts(tasks))

        value, selected = SchedulerEngine.weighted_interval_scheduling(tasks)
        dp_errors += abs(exhaustive_best(tasks) - value) > 1e-6
        trace_errors += (
            abs(sum(SchedulerEngine.task_weight(t) for t in selected) - value) > 1e-6
            or any(a.is_overlapping_with(b) for a, b in itertools.combinations(selected, 2))
        )

        minute = lambda moment: int((moment - BASE).total_seconds() // 60)
        free = set()
        for slot in SchedulerEngine.find_free_slots(tasks, BASE, 0, 24, 1):
            free.update(range(minute(slot.start_time), minute(slot.end_time)))
        busy = set()
        for t in tasks:
            busy.update(range(minute(t.start_time), minute(t.end_time)))
        slot_errors += free != set(range(24 * 60)) - busy

    return {"rounds": rounds, "conflict_errors": conflict_errors, "dp_errors": dp_errors,
            "trace_errors": trace_errors, "slot_errors": slot_errors}


def experiment_dp_vs_exhaustive(rng: random.Random) -> List[dict]:
    rows = []
    for n in (10, 12, 14, 16, 18, 20):
        tasks = random_day_tasks(rng, n)
        t0 = time.perf_counter()
        best = exhaustive_best(tasks)
        exhaustive_ms = (time.perf_counter() - t0) * 1000
        samples = []
        for _ in range(21):
            t0 = time.perf_counter()
            value, _ = SchedulerEngine.weighted_interval_scheduling(tasks)
            samples.append((time.perf_counter() - t0) * 1000)
        rows.append({"n": n, "exhaustive_ms": exhaustive_ms, "dp_ms": statistics.median(samples), "equal": abs(best - value) < 1e-6})
    return rows


def experiment_dp_vs_greedy(rng: random.Random, rounds: int = 1000) -> List[dict]:
    rows = []
    for n in (10, 20, 50, 100):
        gaps_weight, gaps_end = [], []
        hits_weight = hits_end = 0
        for _ in range(rounds):
            tasks = random_day_tasks(rng, n)
            best, _ = SchedulerEngine.weighted_interval_scheduling(tasks)
            by_weight, by_end = greedy_by_weight(tasks), greedy_by_end_time(tasks)
            gaps_weight.append((best - by_weight) / best * 100)
            gaps_end.append((best - by_end) / best * 100)
            hits_weight += abs(best - by_weight) < 1e-6
            hits_end += abs(best - by_end) < 1e-6
        rows.append({
            "n": n, "rounds": rounds,
            "greedy_weight_gap": statistics.mean(gaps_weight), "greedy_weight_worst": max(gaps_weight),
            "greedy_weight_optimal_pct": hits_weight / rounds * 100,
            "greedy_end_gap": statistics.mean(gaps_end), "greedy_end_worst": max(gaps_end),
            "greedy_end_optimal_pct": hits_end / rounds * 100
        })
    return rows


def kahn_order(tasks: List[Task], use_list: bool) -> Tuple[float, int]:
    """Chạy riêng vòng lặp Kahn với hàng đợi kiểu list.pop(0) hoặc collections.deque, trả về thời gian (ms)."""
    from collections import deque
    in_degree = {t.id: 0 for t in tasks}
    adjacency = {t.id: [] for t in tasks}
    for t in tasks:
        for dep in t.dependencies:
            adjacency[dep].append(t.id)
            in_degree[t.id] += 1
    roots = [k for k, d in in_degree.items() if d == 0]
    queue = list(roots) if use_list else deque(roots)
    pop = (lambda: queue.pop(0)) if use_list else queue.popleft
    t0 = time.perf_counter()
    visited = 0
    while queue:
        current = pop()
        visited += 1
        for neighbor in adjacency[current]:
            in_degree[neighbor] -= 1
            if in_degree[neighbor] == 0:
                queue.append(neighbor)
    return (time.perf_counter() - t0) * 1000, visited


def experiment_kahn_queue() -> List[dict]:
    rows = []
    for n in (50000, 100000, 200000, 400000):
        tasks = [Task(title=str(i), id=str(i), start_time=BASE, end_time=BASE + timedelta(minutes=30)) for i in range(n)]
        list_ms, _ = kahn_order(tasks, use_list=True)
        deque_ms, _ = kahn_order(tasks, use_list=False)
        rows.append({"v": n, "list_ms": list_ms, "deque_ms": deque_ms})
    return rows


def experiment_resolution(rng: random.Random, rounds: int = 500) -> dict:
    now = BASE.replace(hour=7)
    conflicts_before = conflicts_after = moved_total = unplaced_total = tasks_total = 0
    delays = []
    for _ in range(rounds):
        tasks = random_day_tasks(rng, rng.randint(5, 20), span_minutes=600)
        tasks_total += len(tasks)
        conflicts_before += len(SchedulerEngine.detect_all_conflicts(tasks))
        moves, unplaced = SchedulerEngine.plan_conflict_resolution(tasks, now=now)
        moved = {m.task.id: m for m in moves}
        unplaced_ids = {t.id for t in unplaced}
        final = [
            Task(title=t.title, id=t.id, start_time=moved[t.id].new_start, end_time=moved[t.id].new_end) if t.id in moved else t
            for t in tasks if t.id not in unplaced_ids
        ]
        conflicts_after += len(SchedulerEngine.detect_all_conflicts(final))
        moved_total += len(moves)
        unplaced_total += len(unplaced)
        delays.extend((m.new_start - m.task.start_time).total_seconds() / 3600 for m in moves)
    return {"rounds": rounds, "tasks": tasks_total, "conflicts_before": conflicts_before, "conflicts_after": conflicts_after,
            "moved": moved_total, "unplaced": unplaced_total, "mean_delay_hours": statistics.mean(delays), "max_delay_hours": max(delays)}


def run_all() -> dict:
    results = {
        "correctness": experiment_correctness(random.Random(SEED)),
        "dp_vs_exhaustive": experiment_dp_vs_exhaustive(random.Random(SEED + 1)),
        "dp_vs_greedy": experiment_dp_vs_greedy(random.Random(SEED + 2)),
        "kahn_queue": experiment_kahn_queue(),
        "resolution": experiment_resolution(random.Random(SEED + 3)),
    }
    print(json.dumps(results, ensure_ascii=False, indent=2))
    return results


if __name__ == "__main__":
    output = run_all()
    if len(sys.argv) > 1:
        with open(sys.argv[1], "w", encoding="utf-8") as f:
            json.dump(output, f, ensure_ascii=False, indent=2)
