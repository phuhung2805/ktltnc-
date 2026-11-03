"""
tests/test_scheduler.py
Bộ kiểm thử tự động (Unit Tests) cho toàn bộ hệ thống quản lý lịch trình và các thuật toán.
"""

import unittest
from datetime import datetime, timedelta
import os
import tempfile
from core.models import Task, Priority, Status, Category
from core.scheduler_engine import SchedulerEngine
from core.storage import StorageManager


class TestScheduleModels(unittest.TestCase):
    def setUp(self):
        self.now = datetime(2026, 11, 4, 8, 0)

    def test_task_creation_valid(self):
        t = Task(
            title="Học Python",
            start_time=self.now,
            end_time=self.now + timedelta(hours=2),
            priority=Priority.HIGH,
            category="Học tập"
        )
        self.assertEqual(t.duration_minutes, 120)
        self.assertEqual(t.duration_hours, 2.0)
        self.assertFalse(t.is_overdue(self.now))

    def test_task_creation_invalid_time(self):
        with self.assertRaises(ValueError):
            Task(
                title="Sai thời gian",
                start_time=self.now + timedelta(hours=1),
                end_time=self.now
            )

    def test_is_overlapping(self):
        t1 = Task(title="Task 1", start_time=self.now, end_time=self.now + timedelta(hours=2), id="1")
        # t2 trùng hoàn toàn một phần [08:30 - 09:30]
        t2 = Task(title="Task 2", start_time=self.now + timedelta(minutes=30), end_time=self.now + timedelta(minutes=90), id="2")
        # t3 nối tiếp ngay sau t1 [10:00 - 11:00] -> Không trùng
        t3 = Task(title="Task 3", start_time=self.now + timedelta(hours=2), end_time=self.now + timedelta(hours=3), id="3")

        self.assertTrue(t1.is_overlapping_with(t2))
        self.assertTrue(t2.is_overlapping_with(t1))
        self.assertFalse(t1.is_overlapping_with(t3))
        self.assertFalse(t1.is_overlapping_with(t1))  # Cùng ID không trùng chính mình


class TestSchedulerEngine(unittest.TestCase):
    def setUp(self):
        self.base = datetime(2026, 11, 4, 8, 0)

    def test_conflict_detection_all_pairs(self):
        t1 = Task(title="T1", start_time=self.base, end_time=self.base + timedelta(hours=2), id="1")
        t2 = Task(title="T2", start_time=self.base + timedelta(hours=1), end_time=self.base + timedelta(hours=3), id="2")
        t3 = Task(title="T3", start_time=self.base + timedelta(hours=4), end_time=self.base + timedelta(hours=5), id="3")

        conflicts = SchedulerEngine.detect_all_conflicts([t1, t2, t3])
        self.assertEqual(len(conflicts), 1)
        self.assertEqual(conflicts[0].overlap_minutes, 60)
        self.assertEqual(conflicts[0].task1.id, "1")
        self.assertEqual(conflicts[0].task2.id, "2")

    def test_merge_intervals(self):
        intervals = [
            (self.base, self.base + timedelta(hours=2)),
            (self.base + timedelta(hours=1), self.base + timedelta(hours=3)),
            (self.base + timedelta(hours=4), self.base + timedelta(hours=5))
        ]
        merged = SchedulerEngine.merge_intervals(intervals)
        self.assertEqual(len(merged), 2)
        self.assertEqual(merged[0], (self.base, self.base + timedelta(hours=3)))
        self.assertEqual(merged[1], (self.base + timedelta(hours=4), self.base + timedelta(hours=5)))

    def test_find_free_slots_and_suggestion(self):
        # Ngày làm việc từ 08:00 đến 18:00 (10 tiếng = 600 phút)
        # Task 1: 09:00 - 11:00
        # Task 2: 13:00 - 15:00
        t1 = Task(title="T1", start_time=self.base.replace(hour=9), end_time=self.base.replace(hour=11), id="1")
        t2 = Task(title="T2", start_time=self.base.replace(hour=13), end_time=self.base.replace(hour=15), id="2")

        free_slots = SchedulerEngine.find_free_slots(
            [t1, t2],
            target_date=self.base,
            day_start_hour=8,
            day_end_hour=18,
            min_duration_minutes=30
        )
        # Khe 1: 08:00 - 09:00 (60m)
        # Khe 2: 11:00 - 13:00 (120m)
        # Khe 3: 15:00 - 18:00 (180m)
        self.assertEqual(len(free_slots), 3)
        self.assertEqual(free_slots[0].duration_minutes, 60)
        self.assertEqual(free_slots[1].duration_minutes, 120)
        self.assertEqual(free_slots[2].duration_minutes, 180)

        # Gợi ý sớm nhất cho công việc 90 phút => Khe 2 (11:00 - 12:30)
        sugg = SchedulerEngine.suggest_optimal_slot(
            [t1, t2],
            duration_minutes=90,
            target_date=self.base,
            strategy="earliest",
            day_start_hour=8,
            day_end_hour=18
        )
        self.assertIsNotNone(sugg)
        start, end = sugg
        self.assertEqual(start.hour, 11)
        self.assertEqual(end.hour, 12)
        self.assertEqual(end.minute, 30)

    def test_topological_sort_success(self):
        # A -> B -> C
        t_a = Task(title="A", start_time=self.base, end_time=self.base + timedelta(hours=1), id="A")
        t_b = Task(title="B", start_time=self.base + timedelta(hours=1), end_time=self.base + timedelta(hours=2), id="B", dependencies=["A"])
        t_c = Task(title="C", start_time=self.base + timedelta(hours=2), end_time=self.base + timedelta(hours=3), id="C", dependencies=["B"])

        sorted_tasks, warnings = SchedulerEngine.topological_sort([t_c, t_a, t_b])
        ordered_ids = [t.id for t in sorted_tasks]
        self.assertEqual(ordered_ids, ["A", "B", "C"])
        self.assertEqual(len(warnings), 0)

    def test_topological_sort_cycle_detection(self):
        # A -> B -> A (Chu trình)
        t_a = Task(title="A", start_time=self.base, end_time=self.base + timedelta(hours=1), id="A", dependencies=["B"])
        t_b = Task(title="B", start_time=self.base + timedelta(hours=1), end_time=self.base + timedelta(hours=2), id="B", dependencies=["A"])

        with self.assertRaises(ValueError):
            SchedulerEngine.topological_sort([t_a, t_b])

    def test_weighted_interval_scheduling(self):
        # Ba công việc:
        # t1: 08:00 - 11:00, Priority LOW
        # t2: 09:00 - 10:00, Priority URGENT (trọng số cao hơn nhiều)
        # t3: 10:30 - 12:00, Priority HIGH
        # t2 và t3 không xung đột với nhau, nhưng cả 2 đều xung đột với t1
        t1 = Task(title="T1", start_time=self.base.replace(hour=8), end_time=self.base.replace(hour=11), priority=Priority.LOW, id="1")
        t2 = Task(title="T2", start_time=self.base.replace(hour=9), end_time=self.base.replace(hour=10), priority=Priority.URGENT, id="2")
        t3 = Task(title="T3", start_time=self.base.replace(hour=10, minute=30), end_time=self.base.replace(hour=12), priority=Priority.HIGH, id="3")

        max_weight, selected = SchedulerEngine.weighted_interval_scheduling([t1, t2, t3])
        # Thuật toán DP nên chọn [t2, t3] vì tổng giá trị lớn hơn t1
        selected_ids = [t.id for t in selected]
        self.assertIn("2", selected_ids)
        self.assertIn("3", selected_ids)
        self.assertNotIn("1", selected_ids)


class TestStorageManager(unittest.TestCase):
    def setUp(self):
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix=".db")
        self.temp_db.close()
        self.storage = StorageManager(db_path=self.temp_db.name)

    def tearDown(self):
        if os.path.exists(self.temp_db.name):
            os.remove(self.temp_db.name)

    def test_crud_task(self):
        now = datetime(2026, 11, 4, 9, 0)
        task = Task(title="Kiểm thử CRUD", start_time=now, end_time=now + timedelta(hours=1), id="test1")

        # Lưu
        self.assertTrue(self.storage.save_task(task))

        # Đọc
        fetched = self.storage.get_task_by_id("test1")
        self.assertIsNotNone(fetched)
        self.assertEqual(fetched.title, "Kiểm thử CRUD")

        # Cập nhật
        fetched.title = "Đã cập nhật tiêu đề"
        self.storage.save_task(fetched)
        updated = self.storage.get_task_by_id("test1")
        self.assertEqual(updated.title, "Đã cập nhật tiêu đề")

        # Xóa
        self.assertTrue(self.storage.delete_task("test1"))
        self.assertIsNone(self.storage.get_task_by_id("test1"))

    def test_seed_sample_data(self):
        tasks = self.storage.seed_sample_data()
        self.assertGreater(len(tasks), 5)
        all_loaded = self.storage.load_all_tasks()
        self.assertEqual(len(tasks), len(all_loaded))


if __name__ == "__main__":
    unittest.main()
