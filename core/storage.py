"""
core/storage.py
Quản lý lưu trữ bền vững lịch làm việc sử dụng SQLite và hỗ trợ nhập/xuất JSON.
"""

import sqlite3
import json
import os
from datetime import datetime, timedelta
from typing import List, Optional
from core.models import Task, Priority, Status, Category


class StorageManager:
    """
    Quản lý dữ liệu lưu trữ SQLite và tệp JSON.
    """
    def __init__(self, db_path: str = "schedule.db"):
        self.db_path = db_path
        self._init_db()

    def _execute_write(self, func):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            with conn:
                return func(conn)
        finally:
            conn.close()

    def _execute_read(self, func):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            return func(conn)
        finally:
            conn.close()

    def _init_db(self):
        """Khởi tạo cấu trúc bảng SQLite nếu chưa tồn tại."""
        def _action(conn):
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS tasks (
                    id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    description TEXT,
                    category TEXT NOT NULL,
                    priority TEXT NOT NULL,
                    status TEXT NOT NULL,
                    start_time TEXT NOT NULL,
                    end_time TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS task_dependencies (
                    task_id TEXT NOT NULL,
                    prerequisite_id TEXT NOT NULL,
                    PRIMARY KEY (task_id, prerequisite_id),
                    FOREIGN KEY (task_id) REFERENCES tasks(id) ON DELETE CASCADE,
                    FOREIGN KEY (prerequisite_id) REFERENCES tasks(id) ON DELETE CASCADE
                )
            """)
        self._execute_write(_action)

    def save_task(self, task: Task) -> bool:
        """Thêm mới hoặc cập nhật một công việc."""
        def _action(conn):
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO tasks 
                (id, title, description, category, priority, status, start_time, end_time, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                task.id,
                task.title,
                task.description,
                task.category,
                task.priority.name,
                task.status.name,
                task.start_time.strftime("%Y-%m-%d %H:%M"),
                task.end_time.strftime("%Y-%m-%d %H:%M"),
                task.created_at.strftime("%Y-%m-%d %H:%M:%S")
            ))

            cursor.execute("DELETE FROM task_dependencies WHERE task_id = ?", (task.id,))
            for dep_id in task.dependencies:
                cursor.execute("""
                    INSERT OR IGNORE INTO task_dependencies (task_id, prerequisite_id)
                    VALUES (?, ?)
                """, (task.id, dep_id))
            return True
        return self._execute_write(_action)

    def delete_task(self, task_id: str) -> bool:
        """Xóa một công việc theo ID."""
        def _action(conn):
            cursor = conn.cursor()
            cursor.execute("DELETE FROM task_dependencies WHERE task_id = ? OR prerequisite_id = ?", (task_id, task_id))
            cursor.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
            return cursor.rowcount > 0
        return self._execute_write(_action)

    def get_task_by_id(self, task_id: str) -> Optional[Task]:
        """Lấy công việc theo ID."""
        def _action(conn):
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM tasks WHERE id = ?", (task_id,))
            row = cursor.fetchone()
            if not row:
                return None

            cursor.execute("SELECT prerequisite_id FROM task_dependencies WHERE task_id = ?", (task_id,))
            dep_rows = cursor.fetchall()
            dependencies = [r[0] for r in dep_rows]

            return Task(
                id=row["id"],
                title=row["title"],
                description=row["description"] or "",
                category=row["category"],
                priority=Priority.from_string(row["priority"]),
                status=Status.from_string(row["status"]),
                start_time=datetime.strptime(row["start_time"], "%Y-%m-%d %H:%M"),
                end_time=datetime.strptime(row["end_time"], "%Y-%m-%d %H:%M"),
                created_at=datetime.strptime(row["created_at"], "%Y-%m-%d %H:%M:%S"),
                dependencies=dependencies
            )
        return self._execute_read(_action)

    def load_all_tasks(self) -> List[Task]:
        """Tải toàn bộ công việc từ cơ sở dữ liệu."""
        def _action(conn):
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM tasks ORDER BY start_time ASC")
            task_rows = cursor.fetchall()

            cursor.execute("SELECT task_id, prerequisite_id FROM task_dependencies")
            dep_rows = cursor.fetchall()

            dep_map: dict[str, list[str]] = {}
            for t_id, p_id in dep_rows:
                if t_id not in dep_map:
                    dep_map[t_id] = []
                dep_map[t_id].append(p_id)

            tasks = []
            for r in task_rows:
                task = Task(
                    id=r["id"],
                    title=r["title"],
                    description=r["description"] or "",
                    category=r["category"],
                    priority=Priority.from_string(r["priority"]),
                    status=Status.from_string(r["status"]),
                    start_time=datetime.strptime(r["start_time"], "%Y-%m-%d %H:%M"),
                    end_time=datetime.strptime(r["end_time"], "%Y-%m-%d %H:%M"),
                    created_at=datetime.strptime(r["created_at"], "%Y-%m-%d %H:%M:%S"),
                    dependencies=dep_map.get(r["id"], [])
                )
                tasks.append(task)
            return tasks
        return self._execute_read(_action)

    def export_to_json(self, file_path: str) -> bool:
        """Xuất toàn bộ dữ liệu ra tệp JSON."""
        dir_name = os.path.dirname(file_path)
        if dir_name:
            os.makedirs(dir_name, exist_ok=True)
        tasks = self.load_all_tasks()
        data = [t.to_dict() for t in tasks]
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True

    def import_from_json(self, file_path: str, clear_existing: bool = False) -> int:
        """Nhập danh sách công việc từ tệp JSON."""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Tệp không tồn tại: {file_path}")

        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        if clear_existing:
            def _clear(conn):
                conn.execute("DELETE FROM task_dependencies")
                conn.execute("DELETE FROM tasks")
            self._execute_write(_clear)

        count = 0
        for item in data:
            task = Task.from_dict(item)
            self.save_task(task)
            count += 1
        return count

    def seed_sample_data(self, base_date: Optional[datetime] = None) -> List[Task]:
        """Tạo dữ liệu thử nghiệm phong phú phản ánh thực tế học tập và làm việc."""
        today = base_date or datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        day1 = today
        day2 = today + timedelta(days=1)
        day3 = today + timedelta(days=2)

        sample_tasks = [
            # Ngày 1: Lịch làm việc & học tập
            Task(
                id="T01",
                title="Họp Standup đầu tuần nhóm KTLTNC",
                description="Báo cáo tiến độ đề tài và phân công công việc tuần mới",
                category="Họp hành",
                priority=Priority.HIGH,
                status=Status.COMPLETED,
                start_time=day1.replace(hour=8, minute=30),
                end_time=day1.replace(hour=9, minute=30)
            ),
            Task(
                id="T02",
                title="Nghiên cứu cơ sở lý thuyết Lập lịch (Scheduling)",
                description="Đọc tài liệu về Interval Scheduling, thuật toán Sweep-Line và Kahn DAG",
                category="Học tập",
                priority=Priority.HIGH,
                status=Status.COMPLETED,
                start_time=day1.replace(hour=10, minute=0),
                end_time=day1.replace(hour=12, minute=0),
                dependencies=["T01"]
            ),
            # Tạo 1 xung đột có chủ đích giữa T03 và T04 để kiểm thử thuật toán phát hiện xung đột
            Task(
                id="T03",
                title="Họp với giảng viên hướng dẫn",
                description="Thảo luận về mô hình kiến trúc và thuật toán quy hoạch động",
                category="Họp hành",
                priority=Priority.URGENT,
                status=Status.IN_PROGRESS,
                start_time=day1.replace(hour=14, minute=0),
                end_time=day1.replace(hour=15, minute=30)
            ),
            Task(
                id="T04",
                title="Seminar Trực tuyến Công nghệ Python",
                description="Tham gia webinar nâng cao kiến thức Tkinter UI và async programming",
                category="Học tập",
                priority=Priority.MEDIUM,
                status=Status.PENDING,
                start_time=day1.replace(hour=15, minute=0),
                end_time=day1.replace(hour=16, minute=30)
            ),
            Task(
                id="T05",
                title="Tập thể dục / Chạy bộ buổi chiều",
                description="Chạy 5km công viên duy trì sức khỏe",
                category="Sức khỏe",
                priority=Priority.LOW,
                status=Status.PENDING,
                start_time=day1.replace(hour=17, minute=30),
                end_time=day1.replace(hour=18, minute=30)
            ),

            # Ngày 2: Lập trình và kiểm thử hệ thống (có quan hệ phụ thuộc liên hoàn)
            Task(
                id="T06",
                title="Cài đặt thuật toán cốt lõi Scheduler Engine",
                description="Viết các hàm phát hiện xung đột, tìm free slot và quy hoạch động",
                category="Công việc",
                priority=Priority.URGENT,
                status=Status.PENDING,
                start_time=day2.replace(hour=8, minute=30),
                end_time=day2.replace(hour=11, minute=30),
                dependencies=["T02"]
            ),
            Task(
                id="T07",
                title="Thiết kế giao diện người dùng GUI Tkinter",
                description="Xây dựng bảng Kanban, ma trận Eisenhower và biểu đồ thống kê",
                category="Công việc",
                priority=Priority.HIGH,
                status=Status.PENDING,
                start_time=day2.replace(hour=13, minute=30),
                end_time=day2.replace(hour=16, minute=30),
                dependencies=["T06"]
            ),
            Task(
                id="T08",
                title="Học ngoại ngữ (Tiếng Anh giao tiếp)",
                description="Luyện nghe podcast và học 20 từ vựng chuyên ngành CNTT",
                category="Cá nhân",
                priority=Priority.MEDIUM,
                status=Status.PENDING,
                start_time=day2.replace(hour=19, minute=30),
                end_time=day2.replace(hour=20, minute=30)
            ),

            # Ngày 3: Kiểm thử, Benchmark và Viết báo cáo
            Task(
                id="T09",
                title="Chạy Benchmark đánh giá độ phức tạp thực nghiệm",
                description="Đo thời gian thực thi với N từ 100 đến 10,000 công việc",
                category="Học tập",
                priority=Priority.HIGH,
                status=Status.PENDING,
                start_time=day3.replace(hour=9, minute=0),
                end_time=day3.replace(hour=11, minute=30),
                dependencies=["T06", "T07"]
            ),
            Task(
                id="T10",
                title="Hoàn thiện báo cáo đề tài KTLTNC",
                description="Tổng hợp cơ sở lý thuyết, phân tích thuật toán và hình ảnh thực nghiệm",
                category="Học tập",
                priority=Priority.URGENT,
                status=Status.PENDING,
                start_time=day3.replace(hour=14, minute=0),
                end_time=day3.replace(hour=17, minute=0),
                dependencies=["T09"]
            ),
            Task(
                id="T11",
                title="Xem phim giải trí cuối tuần",
                description="Thư giãn cùng bạn bè sau tuần học tập căng thẳng",
                category="Cá nhân",
                priority=Priority.LOW,
                status=Status.PENDING,
                start_time=day3.replace(hour=20, minute=0),
                end_time=day3.replace(hour=22, minute=0)
            )
        ]

        for t in sample_tasks:
            self.save_task(t)

        return sample_tasks
