"""
tests/test_scheduler.py
Bộ kiểm thử tự động (Unit Tests) cho toàn bộ hệ thống quản lý lịch trình và các thuật toán.
"""

import unittest
from datetime import datetime, timedelta
import itertools
import json
import os
import random
import sqlite3
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


class TestStatusRules(unittest.TestCase):
    """Việc đã hoàn thành hoặc đã hủy không còn giành chỗ trong lịch."""

    def setUp(self):
        self.base = datetime(2026, 11, 4, 8, 0)

    def _task(self, task_id, start_min, end_min, **kwargs):
        return Task(
            title=task_id, id=task_id,
            start_time=self.base + timedelta(minutes=start_min),
            end_time=self.base + timedelta(minutes=end_min),
            **kwargs
        )

    def test_candidate_ignores_cancelled_and_completed(self):
        cancelled = self._task("huy", 0, 60, status=Status.CANCELLED)
        done = self._task("xong", 0, 60, status=Status.COMPLETED)
        pending = self._task("cho", 0, 60)
        candidate = self._task("moi", 0, 60)
        conflicts = SchedulerEngine.detect_conflicts_for_task(candidate, [cancelled, done, pending])
        self.assertEqual([c.task2.id for c in conflicts], ["cho"])

    def test_inactive_candidate_has_no_conflict(self):
        pending = self._task("cho", 0, 60)
        candidate = self._task("huy", 0, 60, status=Status.CANCELLED)
        self.assertEqual(SchedulerEngine.detect_conflicts_for_task(candidate, [pending]), [])

    def test_completed_pair_is_not_a_conflict(self):
        a = self._task("a", 0, 60, status=Status.COMPLETED)
        b = self._task("b", 30, 90, status=Status.COMPLETED)
        self.assertEqual(SchedulerEngine.detect_all_conflicts([a, b]), [])

    def test_cancelled_task_is_not_overdue(self):
        later = self.base + timedelta(days=1)
        self.assertFalse(self._task("huy", 0, 60, status=Status.CANCELLED).is_overdue(later))
        self.assertTrue(self._task("cho", 0, 60).is_overdue(later))

    def test_wis_ignores_completed_tasks(self):
        done = self._task("xong", 0, 60, priority=Priority.URGENT, status=Status.COMPLETED)
        pending = self._task("cho", 0, 60, priority=Priority.HIGH)
        _, selected = SchedulerEngine.weighted_interval_scheduling([done, pending])
        self.assertEqual([t.id for t in selected], ["cho"])

    def test_wis_urgent_beats_two_medium_tasks(self):
        urgent = self._task("gap", 0, 180, priority=Priority.URGENT)
        short1 = self._task("vua1", 0, 30)
        short2 = self._task("vua2", 60, 90)
        _, selected = SchedulerEngine.weighted_interval_scheduling([urgent, short1, short2])
        self.assertEqual([t.id for t in selected], ["gap"])

    def test_wis_matches_exhaustive_search(self):
        rng = random.Random(7)
        weight = SchedulerEngine.task_weight
        for _ in range(200):
            tasks = []
            for i in range(rng.randint(1, 9)):
                start = rng.randrange(0, 600, 15)
                tasks.append(self._task(str(i), start, start + rng.choice([15, 30, 60, 120, 240]),
                                        priority=rng.choice(list(Priority))))
            best = 0.0
            for size in range(len(tasks) + 1):
                for subset in itertools.combinations(tasks, size):
                    if not any(a.is_overlapping_with(b) for a, b in itertools.combinations(subset, 2)):
                        best = max(best, sum(weight(t) for t in subset))
            value, selected = SchedulerEngine.weighted_interval_scheduling(tasks)
            self.assertAlmostEqual(value, best, places=6)
            self.assertAlmostEqual(sum(weight(t) for t in selected), best, places=6)


class TestFreeSlotOptions(unittest.TestCase):
    def setUp(self):
        self.base = datetime(2026, 11, 4)
        self.t1 = Task(title="T1", id="1", start_time=self.base.replace(hour=9), end_time=self.base.replace(hour=10))

    def test_day_end_hour_24_means_end_of_day(self):
        slots = SchedulerEngine.find_free_slots([], self.base, 22, 24)
        self.assertEqual(slots[0].end_time, self.base + timedelta(days=1))

    def test_not_before_skips_elapsed_time(self):
        slots = SchedulerEngine.find_free_slots(
            [self.t1], self.base, 8, 12, not_before=self.base.replace(hour=9, minute=30)
        )
        self.assertEqual([s.start_time.hour for s in slots], [10])

    def test_not_before_after_day_end_returns_nothing(self):
        slots = SchedulerEngine.find_free_slots([], self.base, 8, 12, not_before=self.base.replace(hour=13))
        self.assertEqual(slots, [])

    def test_best_fit_prefers_smallest_leftover(self):
        slots = SchedulerEngine.find_free_slots([self.t1], self.base, 8, 12, min_duration_minutes=60)
        self.assertEqual(SchedulerEngine.pick_slot(slots, 60, "earliest").start_time.hour, 8)
        self.assertEqual(SchedulerEngine.pick_slot(slots, 60, "best_fit").start_time.hour, 8)
        self.assertEqual(SchedulerEngine.pick_slot(slots, 90, "best_fit").start_time.hour, 10)
        self.assertIsNone(SchedulerEngine.pick_slot(slots, 300, "best_fit"))


class TestDependencyValidation(unittest.TestCase):
    def setUp(self):
        base = datetime(2026, 11, 4, 8, 0)
        self.make = lambda task_id, deps=None, status=Status.PENDING: Task(
            title=task_id, id=task_id, start_time=base, end_time=base + timedelta(hours=1),
            dependencies=deps, status=status
        )

    def test_valid_chain_has_no_error(self):
        a, b = self.make("A"), self.make("B", ["A"])
        self.assertEqual(SchedulerEngine.validate_dependencies(b, [a, b]), [])

    def test_self_dependency_is_rejected(self):
        a = self.make("A", ["A"])
        self.assertEqual(len(SchedulerEngine.validate_dependencies(a, [a])), 1)

    def test_unknown_dependency_is_rejected(self):
        a = self.make("A", ["KHONG_CO"])
        self.assertIn("KHONG_CO", SchedulerEngine.validate_dependencies(a, [a])[0])

    def test_cycle_is_rejected(self):
        a = self.make("A", ["C"])
        b, c = self.make("B", ["A"]), self.make("C", ["B"])
        errors = SchedulerEngine.validate_dependencies(a, [self.make("A"), b, c])
        self.assertEqual(len(errors), 1)
        self.assertIn("chu trình", errors[0])

    def test_unfinished_prerequisites(self):
        done = self.make("X", status=Status.COMPLETED)
        cancelled = self.make("Y", status=Status.CANCELLED)
        pending = self.make("Z")
        task = self.make("T", ["X", "Y", "Z"])
        result = SchedulerEngine.unfinished_prerequisites(task, [done, cancelled, pending, task])
        self.assertEqual([t.id for t in result], ["Z"])


class TestOverlapLanes(unittest.TestCase):
    def setUp(self):
        self.base = datetime(2026, 11, 4, 8, 0)

    def _task(self, task_id, start_min, end_min):
        return Task(title=task_id, id=task_id, start_time=self.base + timedelta(minutes=start_min),
                    end_time=self.base + timedelta(minutes=end_min))

    def test_overlapping_tasks_never_share_a_lane(self):
        rng = random.Random(3)
        for _ in range(100):
            tasks = []
            for i in range(rng.randint(1, 12)):
                start = rng.randrange(0, 600, 15)
                tasks.append(self._task(str(i), start, start + rng.choice([15, 30, 60, 120])))
            lanes = SchedulerEngine.assign_overlap_lanes(tasks)
            self.assertEqual(len(lanes), len(tasks))
            for a, b in itertools.combinations(tasks, 2):
                if a.is_overlapping_with(b):
                    self.assertNotEqual(lanes[a.id][0], lanes[b.id][0])

    def test_separate_clusters_do_not_share_lane_count(self):
        lanes = SchedulerEngine.assign_overlap_lanes([
            self._task("a", 0, 60), self._task("b", 30, 90), self._task("c", 200, 260)
        ])
        self.assertEqual(lanes["a"], (0, 2))
        self.assertEqual(lanes["b"], (1, 2))
        self.assertEqual(lanes["c"], (0, 1))


class TestConflictResolution(unittest.TestCase):
    def setUp(self):
        self.day = datetime(2026, 11, 4)
        self.now = self.day.replace(hour=7)

    def _task(self, task_id, start_hour, end_hour, **kwargs):
        return Task(title=task_id, id=task_id, start_time=self.day.replace(hour=start_hour),
                    end_time=self.day.replace(hour=end_hour), **kwargs)

    def _apply(self, tasks, moves):
        moved = {m.task.id: m for m in moves}
        return [
            Task(title=t.title, id=t.id, start_time=moved[t.id].new_start, end_time=moved[t.id].new_end,
                 priority=t.priority, dependencies=t.dependencies) if t.id in moved else t
            for t in tasks
        ]

    def test_low_priority_task_moves_to_next_free_slot(self):
        high = self._task("cao", 9, 11, priority=Priority.HIGH)
        low = self._task("thap", 10, 12, priority=Priority.LOW)
        moves, unplaced = SchedulerEngine.plan_conflict_resolution([high, low], now=self.now)
        self.assertEqual(unplaced, [])
        self.assertEqual([m.task.id for m in moves], ["thap"])
        self.assertEqual(moves[0].new_start, self.day.replace(hour=11))
        self.assertEqual(moves[0].new_end, self.day.replace(hour=13))

    def test_plan_leaves_no_conflict_on_random_data(self):
        rng = random.Random(11)
        for _ in range(100):
            tasks = []
            for i in range(rng.randint(2, 15)):
                start = self.day + timedelta(hours=8) + timedelta(minutes=rng.randrange(0, 600, 15))
                tasks.append(Task(title=str(i), id=str(i), start_time=start,
                                  end_time=start + timedelta(minutes=rng.choice([30, 60, 90, 120])),
                                  priority=rng.choice(list(Priority))))
            moves, unplaced = SchedulerEngine.plan_conflict_resolution(tasks, now=self.now)
            self.assertEqual(unplaced, [])
            self.assertEqual(SchedulerEngine.detect_all_conflicts(self._apply(tasks, moves)), [])
            for move in moves:
                self.assertGreaterEqual(move.new_start, move.task.start_time)
                self.assertLessEqual(move.new_end.hour * 60 + move.new_end.minute, 21 * 60)

    def test_moved_task_waits_for_prerequisite(self):
        parent = self._task("cha", 14, 16, priority=Priority.URGENT)
        blocker = self._task("chan", 9, 11, priority=Priority.URGENT)
        child = self._task("con", 10, 11, priority=Priority.LOW, dependencies=["cha"])
        moves, _ = SchedulerEngine.plan_conflict_resolution([parent, blocker, child], now=self.now)
        self.assertEqual(moves[0].new_start, self.day.replace(hour=16))

    def test_too_long_task_is_reported_as_unplaced(self):
        high = self._task("cao", 9, 23, priority=Priority.URGENT)
        low = self._task("thap", 9, 23, priority=Priority.LOW)
        moves, unplaced = SchedulerEngine.plan_conflict_resolution([high, low], now=self.now)
        self.assertEqual(moves, [])
        self.assertEqual([t.id for t in unplaced], ["thap"])


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

    def test_updating_prerequisite_keeps_dependents(self):
        now = datetime(2026, 11, 4, 9, 0)
        parent = Task(title="Cha", start_time=now, end_time=now + timedelta(hours=1), id="cha")
        child = Task(title="Con", start_time=now + timedelta(hours=1), end_time=now + timedelta(hours=2),
                     id="con", dependencies=["cha"])
        self.storage.save_task(parent)
        self.storage.save_task(child)

        parent.title = "Cha đã sửa"
        self.storage.save_task(parent)

        self.assertEqual(self.storage.get_task_by_id("con").dependencies, ["cha"])

    def test_foreign_key_is_enforced(self):
        now = datetime(2026, 11, 4, 9, 0)
        task = Task(title="Lỗi", start_time=now, end_time=now + timedelta(hours=1), id="a", dependencies=["khong_co"])
        with self.assertRaises(sqlite3.IntegrityError):
            self.storage.save_task(task)
        self.assertIsNone(self.storage.get_task_by_id("a"))

    def _write_json(self, items) -> str:
        path = self.temp_db.name + ".json"
        self.addCleanup(lambda: os.path.exists(path) and os.remove(path))
        with open(path, "w", encoding="utf-8") as f:
            json.dump(items, f)
        return path

    @staticmethod
    def _item(task_id, deps=None):
        return {"id": task_id, "title": task_id, "start_time": "2026-11-04 08:00",
                "end_time": "2026-11-04 09:00", "dependencies": deps or []}

    def test_json_round_trip(self):
        self.storage.seed_sample_data(datetime(2026, 11, 4))
        path = self.temp_db.name + ".json"
        self.addCleanup(lambda: os.path.exists(path) and os.remove(path))
        self.storage.export_to_json(path)
        self.assertEqual(self.storage.import_from_json(path, clear_existing=True), 11)
        self.assertEqual(self.storage.get_task_by_id("T09").dependencies, ["T06", "T07"])

    def test_import_accepts_dependency_listed_later(self):
        path = self._write_json([self._item("con", ["cha"]), self._item("cha")])
        self.assertEqual(self.storage.import_from_json(path), 2)

    def test_import_rejects_cycle_and_writes_nothing(self):
        path = self._write_json([self._item("a", ["b"]), self._item("b", ["a"])])
        with self.assertRaises(ValueError):
            self.storage.import_from_json(path)
        self.assertEqual(self.storage.load_all_tasks(), [])

    def test_import_rejects_unknown_dependency_and_keeps_existing_data(self):
        self.storage.seed_sample_data(datetime(2026, 11, 4))
        path = self._write_json([self._item("a", ["khong_co"])])
        with self.assertRaises(ValueError):
            self.storage.import_from_json(path, clear_existing=True)
        self.assertEqual(len(self.storage.load_all_tasks()), 11)

    def test_import_rejects_malformed_file(self):
        path = self._write_json([{"title": "Thiếu thời gian"}])
        with self.assertRaises(ValueError):
            self.storage.import_from_json(path)


if __name__ == "__main__":
    unittest.main()
