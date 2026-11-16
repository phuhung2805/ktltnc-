"""
tests/test_ui.py
Kiểm thử giao diện trên cửa sổ thật với CSDL tạm. Tự bỏ qua nếu máy không có màn hình.
"""

import os
import tempfile
import tkinter as tk
import unittest
from datetime import date, datetime, timedelta
from types import SimpleNamespace
from unittest import mock

from core.models import Task, Priority, Status
from ui.main_window import MainWindow
from ui.smart_slot_dialog import SmartSlotDialog
from ui.task_dialog import TaskDialog
from ui.widgets import DatePopup


class UITestCase(unittest.TestCase):
    def setUp(self):
        handle, self.db_path = tempfile.mkstemp(suffix=".db")
        os.close(handle)
        try:
            self.app = MainWindow(db_path=self.db_path)
        except tk.TclError as e:
            os.remove(self.db_path)
            self.skipTest(f"Không có màn hình: {e}")
        self.app.update()

    def tearDown(self):
        self.app.destroy()
        os.remove(self.db_path)

    def _seed(self):
        self.app.storage.seed_sample_data()
        self.app._load_data()
        self.app.update()

    def _visit_tab(self, tab):
        self.app.notebook.select(tab)
        self.app.update()

    def test_empty_database_stays_empty_after_deleting_everything(self):
        self.assertEqual(self.app.tasks, [])
        self._seed()
        for task in list(self.app.tasks):
            self.app.storage.delete_task(task.id)
        self.app._load_data()
        self.assertEqual(self.app.tasks, [])
        self.assertTrue(self.app.btn_seed.winfo_manager())

    def test_charts_are_correct_on_first_visit(self):
        self._seed()
        self._visit_tab(self.app.tab_analytics)
        canvas = self.app.tab_analytics.canvas_bars
        rectangles = [canvas.coords(i) for i in canvas.find_all() if canvas.type(i) == "rectangle"]
        widest = max(c[2] - c[0] for c in rectangles)
        self.assertGreater(widest, 100)
        donut = self.app.tab_analytics.canvas_donut
        arcs = [donut.coords(i) for i in donut.find_all() if donut.type(i) == "arc"]
        self.assertTrue(arcs)
        self.assertGreaterEqual(min(c[1] for c in arcs), 0)

    def test_dialog_keeps_exact_slot_time(self):
        start, end = datetime(2026, 11, 5, 16, 30), datetime(2026, 11, 5, 18, 0)
        dialog = TaskDialog(self.app, all_tasks=[], default_start=start, default_end=end)
        self.assertEqual(dialog.field_start.get(), start)
        self.assertEqual(dialog.field_end.get(), end)
        dialog.destroy()

    def test_moving_start_keeps_duration(self):
        start = datetime(2026, 11, 5, 9, 0)
        dialog = TaskDialog(self.app, all_tasks=[], default_start=start, default_end=start + timedelta(minutes=90))
        dialog.field_start.sp_hour.set("10")
        dialog._on_start_changed()
        self.assertEqual(dialog.field_end.get(), datetime(2026, 11, 5, 11, 30))
        dialog.destroy()

    def test_conflict_hint_updates_while_editing(self):
        day = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        other = Task(title="Họp", id="h", start_time=day.replace(hour=9), end_time=day.replace(hour=10))
        dialog = TaskDialog(self.app, all_tasks=[other], default_start=day.replace(hour=12))
        self.assertIn("Không trùng", dialog.lbl_time_status.cget("text"))
        dialog.field_start.sp_hour.set("09")
        dialog._on_start_changed()
        self.assertIn("Trùng giờ", dialog.lbl_time_status.cget("text"))
        dialog.destroy()

    def test_dialog_blocks_dependency_cycle(self):
        day = datetime(2026, 11, 5)
        parent = Task(title="Cha", id="cha", start_time=day.replace(hour=8), end_time=day.replace(hour=9))
        child = Task(title="Con", id="con", start_time=day.replace(hour=9), end_time=day.replace(hour=10), dependencies=["cha"])
        saved = []
        dialog = TaskDialog(self.app, all_tasks=[parent, child], task=parent, on_save=saved.append)
        dialog.lst_deps.selection_set(0)
        dialog._save_action()
        self.assertEqual(saved, [])
        self.assertIn("chu trình", dialog.lbl_error.cget("text"))
        dialog.destroy()

    def test_empty_title_is_rejected_inline(self):
        saved = []
        dialog = TaskDialog(self.app, all_tasks=[], on_save=saved.append)
        dialog._save_action()
        self.assertEqual(saved, [])
        self.assertTrue(dialog.lbl_error.cget("text"))
        dialog.destroy()

    def test_best_fit_preselects_best_slot_and_passes_exact_time(self):
        day = datetime.now() + timedelta(days=2)
        day = day.replace(hour=0, minute=0, second=0, microsecond=0)
        busy = [
            Task(title="A", id="a", start_time=day.replace(hour=9), end_time=day.replace(hour=11)),
            Task(title="B", id="b", start_time=day.replace(hour=12), end_time=day.replace(hour=21)),
        ]
        chosen = []
        dialog = SmartSlotDialog(self.app, all_tasks=busy, on_slot_selected=lambda *a: chosen.append(a))
        dialog.date_picker.set(day.date())
        dialog.var_strategy.set("best_fit")
        dialog._find_slots()
        slot = dialog.found_slots[int(dialog.tree.selection()[0])]
        self.assertEqual(slot.start_time.hour, 8)

        dialog.var_strategy.set("earliest")
        dialog.cb_duration.set("30")
        dialog.sp_start_hr.set(9)
        dialog.sp_end_hr.set(24)
        dialog._find_slots()
        dialog._apply_slot()
        self.assertEqual(chosen, [(day.replace(hour=11), day.replace(hour=11, minute=30), 30)])

    def test_slot_search_today_skips_elapsed_time(self):
        dialog = SmartSlotDialog(self.app, all_tasks=[])
        dialog.sp_start_hr.set(0)
        dialog.sp_end_hr.set(24)
        dialog._find_slots()
        for slot in dialog.found_slots:
            self.assertGreaterEqual(slot.start_time, datetime.now().replace(second=0, microsecond=0))
        dialog.destroy()

    def test_all_tabs_render_with_sample_data(self):
        self._seed()
        for tab in self.app.notebook.tabs():
            self.app.notebook.select(tab)
            self.app.update()
        self.assertIn("trùng giờ", self.app.btn_conflict.cget("text"))
        self.assertEqual(len(self.app.tree_tasks.get_children()), 11)

    def test_list_filters_and_sorting(self):
        self._seed()
        self.app.cb_filter_status.set("Chưa xong")
        self.app._apply_filters()
        self.assertEqual(len(self.app.tree_tasks.get_children()), 9)
        self.app.cb_filter_status.set("Tất cả")
        self.app.ent_search.insert(0, "không tồn tại xyz")
        self.app._apply_filters()
        self.assertEqual(self.app.tree_tasks.get_children(), ())
        self.assertTrue(self.app.lbl_empty.winfo_manager())
        self.app.ent_search.delete(0, tk.END)
        self.app._sort_by("priority")
        self.app._apply_filters()
        first = self.app.tree_tasks.get_children()[0]
        self.assertEqual(self.app.storage.get_task_by_id(first).priority.label, "Khẩn cấp")

    def test_calendar_draws_conflict_tasks_side_by_side(self):
        self._seed()
        self._visit_tab(self.app.tab_calendar)
        body = self.app.tab_calendar.body
        first = body.coords(body.find_withtag("task_T03")[0])
        second = body.coords(body.find_withtag("task_T04")[0])
        self.assertLessEqual(first[2], second[0] + 1)

    def _dialogs(self):
        return [w for w in self.app.winfo_children() if isinstance(w, TaskDialog)]

    def test_clicking_calendar_task_opens_edit_dialog(self):
        self._seed()
        self._visit_tab(self.app.tab_calendar)
        calendar = self.app.tab_calendar
        calendar.body.yview_moveto(0)
        self.app.update()
        x0, y0, x1, y1 = calendar.body.coords(calendar.body.find_withtag("task_T03")[0])
        x = int(x0 + (x1 - x0) / 2)
        calendar.body.yview_moveto(y0 / (24 * 46))
        self.app.update()
        y = int(y0 - calendar.body.canvasy(0) + 8)
        calendar.body.event_generate("<Motion>", x=x, y=y)
        calendar.body.event_generate("<Button-1>", x=x, y=y)
        self.app.update()
        dialogs = self._dialogs()
        self.assertEqual(len(dialogs), 1)
        self.assertEqual(dialogs[0].task.id, "T03")
        dialogs[0].destroy()

    def test_double_clicking_empty_cell_opens_add_dialog_at_that_time(self):
        self._visit_tab(self.app.tab_calendar)
        calendar = self.app.tab_calendar
        calendar.body.yview_moveto(0)
        self.app.update()
        col_w = calendar._column_width()
        x = int(54 + col_w * 2 + col_w / 2)
        # Tk không cho sinh trực tiếp sự kiện nháy đúp, nên gọi thẳng hàm xử lý với tọa độ tương ứng
        calendar._on_double_click(SimpleNamespace(x=x, y=46 * 3 + 30))
        self.app.update()
        dialogs = self._dialogs()
        self.assertEqual(len(dialogs), 1)
        expected = datetime.combine(calendar.week_start + timedelta(days=2), datetime.min.time()) + timedelta(hours=3, minutes=30)
        self.assertEqual(dialogs[0].field_start.get(), expected)
        dialogs[0].destroy()

    def test_week_navigation(self):
        calendar = self.app.tab_calendar
        start = calendar.week_start
        calendar.shift_week(1)
        self.assertEqual(calendar.week_start, start + timedelta(days=7))
        calendar.go_today()
        self.assertEqual(calendar.week_start, start)

    def test_date_popup_picks_day_and_restores_dialog_grab(self):
        start = datetime(2026, 11, 5, 9, 0)
        dialog = TaskDialog(self.app, all_tasks=[], default_start=start)
        self.app.update()
        picker = dialog.field_start.date_picker
        picker._open()
        self.app.update()
        popup = [w for w in picker.winfo_children() if isinstance(w, DatePopup)][0]
        popup._shift_month(1)
        popup._pick(date(2026, 12, 25))
        self.app.update()
        self.assertEqual(dialog.field_start.get(), datetime(2026, 12, 25, 9, 0))
        self.assertEqual(dialog.field_end.get(), datetime(2026, 12, 25, 10, 0))
        self.assertEqual(str(dialog.grab_current()), str(dialog))
        dialog.destroy()

    def test_action_buttons_follow_selection(self):
        self._seed()
        self.assertEqual(str(self.app.btn_edit["state"]), "disabled")
        self.app.tree_tasks.selection_set("T07")
        self.app.update()
        self.assertEqual(str(self.app.btn_edit["state"]), "normal")

    def test_conflict_modal_opens_and_edits_second_task(self):
        self._seed()
        self.app._show_conflicts_modal()
        self.app.update()
        modals = [w for w in self.app.winfo_children() if isinstance(w, tk.Toplevel)]
        self.assertEqual(len(modals), 1)
        modals[0].destroy()

    def test_minimum_window_size_keeps_buttons_visible(self):
        self._seed()
        self.app.geometry("980x640")
        self.app.update()
        button = self.app.btn_conflict
        self.assertGreater(button.winfo_width(), 50)
        self.assertLessEqual(button.winfo_rootx() + button.winfo_width(), self.app.winfo_rootx() + self.app.winfo_width())

    def test_resolve_button_moves_task_and_clears_conflict(self):
        future = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=3)
        self.app.storage.save_task(Task(title="Gấp", id="a", start_time=future.replace(hour=9), end_time=future.replace(hour=11), priority=Priority.URGENT))
        self.app.storage.save_task(Task(title="Thường", id="b", start_time=future.replace(hour=10), end_time=future.replace(hour=11)))
        self.app._load_data()
        self._visit_tab(self.app.tab_wis)
        self.assertTrue(self.app.tab_wis.btn_resolve.winfo_manager())
        with mock.patch("ui.main_window.messagebox.askyesno", return_value=True):
            self.app.tab_wis.btn_resolve.invoke()
        self.assertIn("Không trùng", self.app.btn_conflict.cget("text"))
        self.assertEqual(self.app.storage.get_task_by_id("b").start_time, future.replace(hour=11))
        self.assertFalse(self.app.tab_wis.btn_resolve.winfo_manager())

    def test_completing_task_warns_about_unfinished_prerequisite(self):
        self._seed()
        self.app.tree_tasks.selection_set("T07")
        with mock.patch("ui.main_window.messagebox.askyesno", return_value=False) as ask:
            self.app._mark_selected_completed()
        self.assertTrue(ask.called)
        self.assertEqual(self.app.storage.get_task_by_id("T07").status, Status.PENDING)

    def test_add_and_delete_through_dialog_flow(self):
        self.app._persist_task(
            Task(title="Mới", id="moi", start_time=datetime(2026, 11, 5, 8), end_time=datetime(2026, 11, 5, 9)),
            "Đã thêm"
        )
        self.assertEqual([t.id for t in self.app.tasks], ["moi"])
        self.app.tree_tasks.selection_set("moi")
        with mock.patch("ui.main_window.messagebox.askyesno", return_value=True):
            self.app._delete_selected_task()
        self.assertEqual(self.app.tasks, [])


if __name__ == "__main__":
    unittest.main()
