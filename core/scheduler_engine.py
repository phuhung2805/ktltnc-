"""
core/scheduler_engine.py
Module chứa các thuật toán cốt lõi xử lý lịch trình:
1. Sắp xếp và quét dừng sớm: Phát hiện xung đột thời gian (Conflict Detection) O(N log N + K)
2. Interval Merging & Inversion: Tìm khoảng thời gian rảnh tối ưu (Smart Free Slot Finder) O(N log N)
3. Kahn's Algorithm: Lập lịch và phát hiện chu trình phụ thuộc công việc (Topological Sort) O(V + E)
4. Dynamic Programming: Lập lịch tối ưu có trọng số (Weighted Interval Scheduling) O(N log N)
5. Phân loại ma trận Eisenhower & Đánh giá mức độ ưu tiên
6. Phân làn khoảng thời gian (Interval Partitioning): Xếp các việc trùng giờ trên lịch tuần O(N log N)
"""

from collections import deque
from datetime import datetime, timedelta
from typing import List, Tuple, Dict, Optional
import bisect
import heapq
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


class RescheduleMove:
    """Phương án dời một công việc sang khung giờ mới; blocked_titles là các việc phụ thuộc bị ảnh hưởng."""
    def __init__(self, task: Task, new_start: datetime, new_end: datetime, blocked_titles: List[str]):
        self.task = task
        self.new_start = new_start
        self.new_end = new_end
        self.blocked_titles = blocked_titles

    def __repr__(self):
        return f"Move('{self.task.title}' -> {self.new_start.strftime('%d/%m %H:%M')})"


class SchedulerEngine:
    """
    Bộ máy thực thi các thuật toán lập lịch nâng cao.
    """

    @staticmethod
    def detect_conflicts_for_task(candidate: Task, tasks: List[Task]) -> List[ConflictResult]:
        """
        Kiểm tra xung đột giữa một công việc ứng viên với danh sách các công việc hiện có.
        Chỉ các công việc còn phải làm mới chiếm chỗ; việc đã hoàn thành hoặc đã hủy được bỏ qua.
        Độ phức tạp: O(N)
        """
        if not candidate.is_active:
            return []

        conflicts = []
        for task in tasks:
            if task.is_active and task.id != candidate.id and candidate.is_overlapping_with(task):
                conflicts.append(ConflictResult(candidate, task))
        return conflicts

    @staticmethod
    def detect_all_conflicts(tasks: List[Task]) -> List[ConflictResult]:
        """
        Phát hiện toàn bộ các cặp công việc xung đột bằng cách sắp xếp rồi quét, dừng sớm (kiểu Sweep-Line).
        Ý tưởng:
        1. Sắp xếp các công việc theo start_time: O(N log N).
        2. Với mỗi công việc i, chỉ xét các công việc kế tiếp cho đến công việc đầu tiên bắt đầu
           từ end_time của i trở đi. Mỗi bước không dừng đều tạo ra đúng một cặp xung đột.
        Độ phức tạp: O(N log N + K) với K là số cặp xung đột thực tế.
        Lưu ý: K có thể lên tới N(N-1)/2, nên trường hợp xấu nhất vẫn là O(N^2).
        """
        if len(tasks) < 2:
            return []

        # Chỉ xét các công việc còn phải làm
        valid_tasks = [t for t in tasks if t.is_active]
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
        min_duration_minutes: int = 30,
        not_before: Optional[datetime] = None
    ) -> List[FreeTimeSlot]:
        """
        Thuật toán tìm các khoảng thời gian trống (Free Slots) trong một ngày cụ thể.
        Phương pháp:
        1. Lọc ra các công việc nằm trong ngày chỉ định và thuộc khung giờ làm việc.
        2. Hợp nhất các khoảng thời gian bận (busy intervals).
        3. Thực hiện phép bù (Inversion) so với toàn bộ khung giờ làm việc [day_start, day_end].
        4. Lọc các khe có độ dài >= min_duration_minutes.
        Tham số not_before bỏ qua phần thời gian đã trôi qua. day_end_hour = 24 nghĩa là hết ngày.
        Việc đã hoàn thành vẫn tính là bận vì khoảng thời gian đó đã được dùng; chỉ việc đã hủy mới trả lại chỗ.
        Độ phức tạp: O(N log N)
        """
        midnight = datetime(target_date.year, target_date.month, target_date.day)
        day_start = midnight + timedelta(hours=day_start_hour)
        day_end = midnight + timedelta(hours=day_end_hour)

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
        current_cursor = max(day_start, not_before) if not_before else day_start

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

    @staticmethod
    def pick_slot(slots: List[FreeTimeSlot], duration_minutes: int, strategy: str = "earliest") -> Optional[FreeTimeSlot]:
        """
        Chọn khe rảnh theo chiến lược trong các khe đủ dài:
        - 'earliest': Khe sớm nhất.
        - 'best_fit': Khe có phần dư (độ dài - duration_minutes) nhỏ nhất; nếu bằng nhau lấy khe sớm hơn.
        """
        fitting = [s for s in slots if s.duration_minutes >= duration_minutes]
        if not fitting:
            return None
        if strategy == "best_fit":
            return min(fitting, key=lambda s: s.duration_minutes - duration_minutes)
        return fitting[0]

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

        best_slot = cls.pick_slot(free_slots, duration_minutes, strategy)
        if best_slot is None:
            return None
        return (best_slot.start_time, best_slot.start_time + timedelta(minutes=duration_minutes))

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
        queue = deque(tid for tid, deg in in_degree.items() if deg == 0)
        sorted_task_ids = []

        while queue:
            current_id = queue.popleft()
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
    def validate_dependencies(task: Task, tasks: List[Task]) -> List[str]:
        """
        Kiểm tra các công việc tiên quyết của task trước khi lưu: tự phụ thuộc, mã không tồn tại
        và chu trình (duyệt DFS từ task theo cạnh tiên quyết xem có quay lại chính nó không).
        Trả về danh sách lỗi, rỗng nếu hợp lệ. Độ phức tạp: O(V + E).
        """
        task_map = {t.id: t for t in tasks}
        errors: List[str] = []

        if task.id in task.dependencies:
            errors.append(f"Công việc '{task.title}' không thể là tiên quyết của chính nó.")

        missing = [d for d in task.dependencies if d not in task_map and d != task.id]
        if missing:
            errors.append(f"Không tìm thấy công việc tiên quyết có mã: {', '.join(missing)}.")

        visited = set()
        stack = [d for d in task.dependencies if d != task.id]
        while stack:
            current_id = stack.pop()
            if current_id == task.id:
                errors.append(f"Lựa chọn này tạo chu trình phụ thuộc: '{task.title}' đang là tiên quyết của một việc trong danh sách.")
                break
            if current_id in visited or current_id not in task_map:
                continue
            visited.add(current_id)
            stack.extend(task_map[current_id].dependencies)

        return errors

    @staticmethod
    def unfinished_prerequisites(task: Task, tasks: List[Task]) -> List[Task]:
        """Danh sách các công việc tiên quyết của task chưa hoàn thành (việc đã hủy không còn chặn)."""
        task_map = {t.id: t for t in tasks}
        prerequisites = [task_map[d] for d in task.dependencies if d in task_map]
        return [t for t in prerequisites if t.is_active]

    @staticmethod
    def task_weight(task: Task) -> float:
        """
        Trọng số của công việc trong bài toán WIS: w = 10 * 3^(p - 1) + max(1, 120 / max(30, d)).
        Phần đầu tăng theo cấp số nhân để một việc ưu tiên cao không bị nhiều việc ưu tiên thấp hơn
        một bậc lấn át (1 việc Khẩn cấp thắng 2 việc Cao); phần sau (từ 1 đến 4) nhỉnh hơn cho việc ngắn.
        """
        base = 10.0 * 3 ** (task.priority.level - 1)
        duration_factor = max(1.0, 120.0 / max(30, task.duration_minutes))
        return round(base + duration_factor, 2)

    @staticmethod
    def weighted_interval_scheduling(tasks: List[Task]) -> Tuple[float, List[Task]]:
        """
        Thuật toán Quy hoạch động (Dynamic Programming) giải bài toán Weighted Interval Scheduling:
        Cho N công việc có khung giờ [si, ei) và trọng số vi (dựa trên Priority & Urgency).
        Chọn tập công việc tương thích (không xung đột thời gian) sao cho tổng trọng số là lớn nhất.
        Chỉ xét các công việc còn phải làm, vì việc đã xong hoặc đã hủy không cần giành chỗ nữa.

        Công thức truy hồi:
        OPT(j) = max(v_j + OPT(p(j)), OPT(j - 1))
        Trong đó p(j) là chỉ số lớn nhất i < j sao cho e_i <= s_j (tìm bằng Binary Search O(log N)).
        Độ phức tạp: O(N log N), Không gian: O(N).
        """
        if not tasks:
            return 0.0, []

        valid_tasks = [t for t in tasks if t.is_active]
        if not valid_tasks:
            return 0.0, []

        compute_weight = SchedulerEngine.task_weight

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

    @classmethod
    def plan_conflict_resolution(
        cls,
        tasks: List[Task],
        now: Optional[datetime] = None,
        day_start_hour: int = 8,
        day_end_hour: int = 21,
        horizon_days: int = 14
    ) -> Tuple[List[RescheduleMove], List[Task]]:
        """
        Lập phương án gỡ trùng lịch, kết hợp quy hoạch động với tìm khe rảnh:
        1. Dùng WIS để xác định các việc được giữ nguyên giờ.
        2. Duyệt các việc còn lại theo ưu tiên giảm dần, đặt mỗi việc vào khe rảnh sớm nhất
           không trước giờ cũ, không trước thời điểm hiện tại và sau khi các việc tiên quyết kết thúc.
        Đầu ra: danh sách phương án dời và các việc không xếp được trong horizon_days ngày.
        Độ phức tạp: O(D * H * N log N) với D là số việc phải dời, H là số ngày tìm kiếm.
        """
        now = now or datetime.now()
        _, kept = cls.weighted_interval_scheduling(tasks)
        kept_ids = {t.id for t in kept}
        task_map = {t.id: t for t in tasks}
        dropped = sorted(
            (t for t in tasks if t.is_active and t.id not in kept_ids),
            key=lambda t: (-t.priority.level, t.start_time)
        )

        # Việc đã hoàn thành không chiếm chỗ trong tương lai nên chỉ các việc được giữ mới tính là bận
        busy = list(kept)
        planned_end: Dict[str, datetime] = {}
        moves: List[RescheduleMove] = []
        unplaced: List[Task] = []

        for task in dropped:
            earliest = max(task.start_time, now)
            for dep_id in task.dependencies:
                dep = task_map.get(dep_id)
                if dep is not None and dep.is_active:
                    earliest = max(earliest, planned_end.get(dep_id, dep.end_time))

            placed = None
            for offset in range(horizon_days):
                day = earliest + timedelta(days=offset)
                slots = cls.find_free_slots(
                    busy, day, day_start_hour, day_end_hour,
                    min_duration_minutes=task.duration_minutes, not_before=earliest
                )
                placed = cls.pick_slot(slots, task.duration_minutes, "earliest")
                if placed is not None:
                    break

            if placed is None:
                unplaced.append(task)
                continue

            new_end = placed.start_time + timedelta(minutes=task.duration_minutes)
            busy.append(Task(title=task.title, id=task.id, start_time=placed.start_time, end_time=new_end))
            planned_end[task.id] = new_end
            blocked = [t.title for t in tasks if task.id in t.dependencies and t.is_active and t.start_time < new_end]
            moves.append(RescheduleMove(task, placed.start_time, new_end, blocked))

        return moves, unplaced

    @staticmethod
    def assign_overlap_lanes(tasks: List[Task]) -> Dict[str, Tuple[int, int]]:
        """
        Phân làn để vẽ các việc trùng giờ cạnh nhau trên lịch (Interval Partitioning):
        duyệt theo start_time, dùng min-heap theo end_time để tái sử dụng làn sớm rảnh nhất.
        Các việc nối nhau bằng quan hệ trùng giờ tạo thành một cụm và chia chung số làn.
        Đầu ra: task.id -> (chỉ số làn, tổng số làn của cụm). Độ phức tạp: O(N log N).
        """
        result: Dict[str, Tuple[int, int]] = {}
        cluster: List[Tuple[str, int]] = []
        cluster_end: Optional[datetime] = None
        heap: List[Tuple[datetime, int]] = []
        lane_count = 0

        def _flush():
            for task_id, lane in cluster:
                result[task_id] = (lane, lane_count)

        for t in sorted(tasks, key=lambda t: (t.start_time, t.end_time)):
            if cluster and t.start_time >= cluster_end:
                _flush()
                cluster, heap, lane_count, cluster_end = [], [], 0, None

            if heap and heap[0][0] <= t.start_time:
                _, lane = heapq.heappop(heap)
            else:
                lane = lane_count
                lane_count += 1

            heapq.heappush(heap, (t.end_time, lane))
            cluster.append((t.id, lane))
            cluster_end = t.end_time if cluster_end is None else max(cluster_end, t.end_time)

        _flush()
        return result

    @staticmethod
    def classify_eisenhower(
        tasks: List[Task],
        threshold_hours: float = 24.0,
        now: Optional[datetime] = None
    ) -> Dict[str, List[Task]]:
        """
        Phân loại công việc theo Ma trận Eisenhower (4 Góc phần tư):
        - Q1 (Khẩn cấp & Quan trọng): Priority >= HIGH và thời gian bắt đầu trong vòng `threshold_hours` giờ.
        - Q2 (Không khẩn cấp & Quan trọng): Priority >= HIGH và thời gian bắt đầu > `threshold_hours`.
        - Q3 (Khẩn cấp & Ít quan trọng): Priority < HIGH và thời gian bắt đầu trong vòng `threshold_hours`.
        - Q4 (Không khẩn cấp & Ít quan trọng): Priority < HIGH và thời gian bắt đầu > `threshold_hours`.
        """
        now = now or datetime.now()
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
