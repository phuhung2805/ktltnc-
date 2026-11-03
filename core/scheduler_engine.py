"""
core/scheduler_engine.py
Module chứa các thuật toán cốt lõi xử lý lịch trình:
1. Sweep-line: Phát hiện xung đột thời gian (Conflict Detection) O(N log N)
2. Interval Merging & Inversion: Tìm khoảng thời gian rảnh tối ưu (Smart Free Slot Finder) O(N log N)
3. Kahn's Algorithm: Lập lịch và phát hiện chu trình phụ thuộc công việc (Topological Sort) O(V + E)
4. Dynamic Programming: Lập lịch tối ưu có trọng số (Weighted Interval Scheduling) O(N log N)
5. Phân loại ma trận Eisenhower & Đánh giá mức độ ưu tiên
"""

from datetime import datetime, timedelta, time
from typing import List, Tuple, Dict, Optional, Set
import bisect
from core.models import Task, Priority, Status


class ConflictResult:
    """Đối tượng lưu trữ thông tin xung đột lịch trình."""
    def __init__(self, task1: Task, task2: Task):
        self.task1 = task1
        self.task2 = task2
        self.overlap_start = max(task1.start_time, task2.start_time)
        self.overlap_end = min(task1.end_time, task2.end_time)
        self.overlap_minutes = int((self.overlap_end - self.overlap_start).total_seconds() / 60)

    def __repr__(self):
        return (f"Conflict between '{self.task1.title}' and '{self.task2.title}' "
                f"from {self.overlap_start.strftime('%H:%M')} to {self.overlap_end.strftime('%H:%M')} "
                f"({self.overlap_minutes} mins)")


class FreeTimeSlot:
    """Đối tượng đại diện cho một khung thời gian rảnh."""
    def __init__(self, start_time: datetime, end_time: datetime):
        self.start_time = start_time
        self.end_time = end_time
        self.duration_minutes = int((end_time - start_time).total_seconds() / 60)

    @property
    def duration_hours(self) -> float:
        return round(self.duration_minutes / 60.0, 2)

    def __repr__(self):
        return f"FreeSlot({self.start_time.strftime('%Y-%m-%d %H:%M')} -> {self.end_time.strftime('%H:%M')}, {self.duration_minutes}m)"


class SchedulerEngine:
    """
    Bộ máy thực thi các thuật toán lập lịch nâng cao.
    """

    @staticmethod
    def detect_conflicts_for_task(candidate: Task, tasks: List[Task]) -> List[ConflictResult]:
        """
        Kiểm tra xung đột giữa một công việc ứng viên với danh sách các công việc hiện có.
        Độ phức tạp: O(N)
        """
        conflicts = []
        for task in tasks:
            if task.id != candidate.id and candidate.is_overlapping_with(task):
                conflicts.append(ConflictResult(candidate, task))
        return conflicts

    @staticmethod
    def detect_all_conflicts(tasks: List[Task]) -> List[ConflictResult]:
        """
        Thuật toán Sweep-Line (Đường quét) phát hiện toàn bộ các cặp công việc xung đột.
        Ý tưởng:
        1. Sắp xếp các sự kiện bắt đầu và kết thúc của các công việc theo mốc thời gian O(N log N).
        2. Duyệt qua các công việc đã sắp xếp theo start_time, sử dụng danh sách active intervals.
        Độ phức tạp: O(N log N + K) với K là số lượng xung đột thực tế.
        """
        if len(tasks) < 2:
            return []

        # Chỉ xét các công việc chưa bị hủy
        valid_tasks = [t for t in tasks if t.status != Status.CANCELLED]
        # Sắp xếp theo start_time
        sorted_tasks = sorted(valid_tasks, key=lambda t: t.start_time)

        conflicts: List[ConflictResult] = []
        n = len(sorted_tasks)

        for i in range(n):
            t1 = sorted_tasks[i]
            for j in range(i + 1, n):
                t2 = sorted_tasks[j]
                # Nếu start_time của t2 >= end_time của t1 thì không thể xung đột với t1 và các task sau đó
                if t2.start_time >= t1.end_time:
                    break
                # Ngược lại, vì t2.start_time < t1.end_time và t2.start_time >= t1.start_time => có giao thoa
                conflicts.append(ConflictResult(t1, t2))

        return conflicts

    @staticmethod
    def merge_intervals(intervals: List[Tuple[datetime, datetime]]) -> List[Tuple[datetime, datetime]]:
        """
        Thuật toán Hợp nhất các khoảng thời gian giao nhau (Merge Intervals).
        Đầu vào: Danh sách các khoảng [start, end]
        Đầu ra: Danh sách các khoảng rời rạc liên tục đã được gộp.
        Độ phức tạp: O(N log N)
        """
        if not intervals:
            return []

        # Sắp xếp theo thời điểm bắt đầu
        sorted_intervals = sorted(intervals, key=lambda x: x[0])
        merged = [sorted_intervals[0]]

        for current_start, current_end in sorted_intervals[1:]:
            last_start, last_end = merged[-1]
            if current_start <= last_end:
                # Có giao thoa hoặc nối tiếp => mở rộng mốc kết thúc
                merged[-1] = (last_start, max(last_end, current_end))
            else:
                merged.append((current_start, current_end))

        return merged

    @classmethod
    def find_free_slots(
        cls,
        tasks: List[Task],
        target_date: datetime,
        day_start_hour: int = 8,
        day_end_hour: int = 21,
        min_duration_minutes: int = 30
    ) -> List[FreeTimeSlot]:
        """
        Thuật toán tìm các khoảng thời gian trống (Free Slots) trong một ngày cụ thể.
        Phương pháp:
        1. Lọc ra các công việc nằm trong ngày chỉ định và thuộc khung giờ làm việc.
        2. Hợp nhất các khoảng thời gian bận (busy intervals).
        3. Thực hiện phép bù (Inversion) so với toàn bộ khung giờ làm việc [day_start, day_end].
        4. Lọc các khe có độ dài >= min_duration_minutes.
        Độ phức tạp: O(N log N)
        """
        day_start = datetime(target_date.year, target_date.month, target_date.day, day_start_hour, 0)
        day_end = datetime(target_date.year, target_date.month, target_date.day, day_end_hour, 0)

        # Trích xuất các khoảng bận rộn nằm trong ngày
        busy_intervals: List[Tuple[datetime, datetime]] = []
        for t in tasks:
            if t.status == Status.CANCELLED:
                continue
            # Kiểm tra xem task có cắt qua ngày target không
            if t.end_time <= day_start or t.start_time >= day_end:
                continue
            # Giới hạn mốc trong khung giờ làm việc của ngày
            clamped_start = max(t.start_time, day_start)
            clamped_end = min(t.end_time, day_end)
            if clamped_start < clamped_end:
                busy_intervals.append((clamped_start, clamped_end))

        merged_busy = cls.merge_intervals(busy_intervals)

        # Đảo ngược khoảng bận để lấy khoảng rảnh
        free_slots: List[FreeTimeSlot] = []
        current_cursor = day_start

        for busy_start, busy_end in merged_busy:
            if busy_start > current_cursor:
                duration = int((busy_start - current_cursor).total_seconds() / 60)
                if duration >= min_duration_minutes:
                    free_slots.append(FreeTimeSlot(current_cursor, busy_start))
            current_cursor = max(current_cursor, busy_end)

        if current_cursor < day_end:
            duration = int((day_end - current_cursor).total_seconds() / 60)
            if duration >= min_duration_minutes:
                free_slots.append(FreeTimeSlot(current_cursor, day_end))

        return free_slots

    @classmethod
    def suggest_optimal_slot(
        cls,
        tasks: List[Task],
        duration_minutes: int,
        target_date: datetime,
        strategy: str = "earliest",
        day_start_hour: int = 8,
        day_end_hour: int = 21
    ) -> Optional[Tuple[datetime, datetime]]:
        """
        Thuật toán gợi ý khung giờ tối ưu cho công việc mới:
        - strategy = 'earliest': Chọn khung giờ sớm nhất thỏa mãn độ dài.
        - strategy = 'best_fit': Chọn khung giờ có độ dài gần nhất với duration_minutes để giảm thiểu phân mảnh thời gian.
        """
        free_slots = cls.find_free_slots(
            tasks,
            target_date,
            day_start_hour,
            day_end_hour,
            min_duration_minutes=duration_minutes
        )

        if not free_slots:
            return None

        if strategy == "best_fit":
            # Best fit: Khe rảnh có (duration - required) nhỏ nhất nhưng >= 0
            best_slot = min(free_slots, key=lambda s: s.duration_minutes - duration_minutes)
            slot_start = best_slot.start_time
            slot_end = slot_start + timedelta(minutes=duration_minutes)
            return (slot_start, slot_end)
        else:
            # Earliest: Khe đầu tiên
            best_slot = free_slots[0]
            slot_start = best_slot.start_time
            slot_end = slot_start + timedelta(minutes=duration_minutes)
            return (slot_start, slot_end)

    @staticmethod
    def topological_sort(tasks: List[Task]) -> Tuple[List[Task], List[str]]:
        """
        Thuật toán Kahn (BFS) sắp xếp topo thứ tự thực hiện các công việc có phụ thuộc (Dependencies).
        Phát hiện chu trình (Deadlock / Circular dependency).
        Đầu ra:
        - Thứ tự thực hiện hợp lệ (List[Task])
        - Danh sách các cảnh báo vi phạm thứ tự thời gian (ví dụ task con bắt đầu trước khi task cha kết thúc).
        Ném ngoại lệ ValueError nếu phát hiện chu trình.
        Độ phức tạp: O(V + E) với V là số công việc, E là số lượng ràng buộc phụ thuộc.
        """
        task_map = {t.id: t for t in tasks}
        in_degree: Dict[str, int] = {t.id: 0 for t in tasks}
        adj_list: Dict[str, List[str]] = {t.id: [] for t in tasks}

        for task in tasks:
            for dep_id in task.dependencies:
                if dep_id in task_map:
                    adj_list[dep_id].append(task.id)
                    in_degree[task.id] += 1

        # Hàng đợi các đỉnh có bán bậc vào (in_degree) = 0
        queue = [tid for tid, deg in in_degree.items() if deg == 0]
        sorted_task_ids = []

        while queue:
            # Có thể ưu tiên lấy task theo độ ưu tiên cao trước
            current_id = queue.pop(0)
            sorted_task_ids.append(current_id)

            for neighbor_id in adj_list[current_id]:
                in_degree[neighbor_id] -= 1
                if in_degree[neighbor_id] == 0:
                    queue.append(neighbor_id)

        if len(sorted_task_ids) != len(tasks):
            # Số đỉnh duyệt được < V => tồn tại chu trình
            unresolved = [t.title for t in tasks if in_degree[t.id] > 0]
            raise ValueError(f"Phát hiện chu trình phụ thuộc (Circular Dependency) giữa các công việc: {', '.join(unresolved)}")

        sorted_tasks = [task_map[tid] for tid in sorted_task_ids]

        # Kiểm tra tính hợp lệ về mặt thời gian (start_time của task con >= end_time của task cha)
        warnings = []
        for task in sorted_tasks:
            for dep_id in task.dependencies:
                if dep_id in task_map:
                    parent_task = task_map[dep_id]
                    if task.start_time < parent_task.end_time:
                        warnings.append(
                            f"Cảnh báo: Công việc '{task.title}' bắt đầu ({task.start_time.strftime('%H:%M %d/%m')}) "
                            f"trước khi công việc tiên quyết '{parent_task.title}' hoàn thành ({parent_task.end_time.strftime('%H:%M %d/%m')})."
                        )

        return sorted_tasks, warnings

    @staticmethod
    def weighted_interval_scheduling(tasks: List[Task]) -> Tuple[float, List[Task]]:
        """
        Thuật toán Quy hoạch động (Dynamic Programming) giải bài toán Weighted Interval Scheduling:
        Cho N công việc có khung giờ [si, ei) và trọng số vi (dựa trên Priority & Urgency).
        Chọn tập công việc tương thích (không xung đột thời gian) sao cho tổng trọng số là lớn nhất.

        Công thức truy hồi:
        OPT(j) = max(v_j + OPT(p(j)), OPT(j - 1))
        Trong đó p(j) là chỉ số lớn nhất i < j sao cho e_i <= s_j (tìm bằng Binary Search O(log N)).
        Độ phức tạp: O(N log N), Không gian: O(N).
        """
        if not tasks:
            return 0.0, []

        valid_tasks = [t for t in tasks if t.status != Status.CANCELLED]
        if not valid_tasks:
            return 0.0, []

        # Tính trọng số cho từng công việc: Trọng số = Priority * 10 + (24 / duration)
        # Ưu tiên công việc quan trọng và gọn gàng
        def compute_weight(t: Task) -> float:
            base = t.priority.level * 10.0
            duration_factor = max(1.0, 120.0 / max(30, t.duration_minutes))
            return round(base + duration_factor, 2)

        # 1. Sắp xếp các công việc theo thời gian kết thúc tăng dần
        sorted_tasks = sorted(valid_tasks, key=lambda t: t.end_time)
        n = len(sorted_tasks)

        end_times = [t.end_time for t in sorted_tasks]

        # 2. Tiền xử lý tìm p(j) bằng Binary Search (bisect_right)
        p = [0] * (n + 1)
        for j in range(1, n + 1):
            curr_task = sorted_tasks[j - 1]
            # Tìm công việc i có end_time <= curr_task.start_time
            idx = bisect.bisect_right(end_times, curr_task.start_time)
            p[j] = idx

        # 3. Mảng lưu giá trị tối ưu OPT[0..n]
        dp = [0.0] * (n + 1)
        for j in range(1, n + 1):
            weight_j = compute_weight(sorted_tasks[j - 1])
            take = weight_j + dp[p[j]]
            dont_take = dp[j - 1]
            dp[j] = max(take, dont_take)

        # 4. Truy vết tìm tập công việc được chọn
        selected_tasks: List[Task] = []
        curr = n
        while curr > 0:
            weight_curr = compute_weight(sorted_tasks[curr - 1])
            if weight_curr + dp[p[curr]] >= dp[curr - 1]:
                selected_tasks.append(sorted_tasks[curr - 1])
                curr = p[curr]
            else:
                curr -= 1

        selected_tasks.reverse()
        return dp[n], selected_tasks

    @staticmethod
    def classify_eisenhower(tasks: List[Task], threshold_hours: float = 24.0) -> Dict[str, List[Task]]:
        """
        Phân loại công việc theo Ma trận Eisenhower (4 Góc phần tư):
        - Q1 (Khẩn cấp & Quan trọng): Priority >= HIGH và thời gian bắt đầu trong vòng `threshold_hours` giờ.
        - Q2 (Không khẩn cấp & Quan trọng): Priority >= HIGH và thời gian bắt đầu > `threshold_hours`.
        - Q3 (Khẩn cấp & Ít quan trọng): Priority < HIGH và thời gian bắt đầu trong vòng `threshold_hours`.
        - Q4 (Không khẩn cấp & Ít quan trọng): Priority < HIGH và thời gian bắt đầu > `threshold_hours`.
        """
        now = datetime.now()
        quadrants: Dict[str, List[Task]] = {
            "Q1": [],  # Làm ngay
            "Q2": [],  # Lên kế hoạch
            "Q3": [],  # Ủy quyền / Giảm thiểu
            "Q4": []   # Loại bỏ / Lúc rảnh
        }

        for task in tasks:
            if task.status == Status.COMPLETED or task.status == Status.CANCELLED:
                continue

            time_diff = (task.start_time - now).total_seconds() / 3600.0
            is_urgent = time_diff <= threshold_hours
            is_important = task.priority in (Priority.HIGH, Priority.URGENT)

            if is_important and is_urgent:
                quadrants["Q1"].append(task)
            elif is_important and not is_urgent:
                quadrants["Q2"].append(task)
            elif not is_important and is_urgent:
                quadrants["Q3"].append(task)
            else:
                quadrants["Q4"].append(task)

        return quadrants
