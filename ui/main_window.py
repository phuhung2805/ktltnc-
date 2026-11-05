"""
ui/main_window.py
Cửa sổ chính của Hệ thống Quản lý Lịch Làm việc Cá nhân.
Tích hợp các tab:
1. Lịch tuần (Interval Partitioning)
2. Danh sách công việc
3. Mức ưu tiên (Ma trận Eisenhower)
4. Thống kê
5. Thứ tự làm (Kahn's Topological Sort)
6. Khi trùng lịch (Dynamic Programming - Weighted Interval Scheduling)
"""

import json
import sqlite3
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import datetime, timedelta
from typing import List, Optional

from core.models import Task, Priority, Status, Category
from core.scheduler_engine import SchedulerEngine
from core.storage import StorageManager
from ui.theme import Theme
from ui.task_dialog import TaskDialog
from ui.smart_slot_dialog import SmartSlotDialog
from ui.calendar_view import WeekCalendarView
from ui.eisenhower_view import EisenhowerView
from ui.analytics_view import AnalyticsView
from ui.planning_views import DependencyView, OptimizeView
from ui.widgets import (
    WEEKDAY_FULL, format_datetime, format_duration, make_button, make_entry, make_modal,
    set_button_enabled, set_button_kind
)

STATUS_FILTER_ALL = "Tất cả"
STATUS_FILTER_OPEN = "Chưa xong"
STATUS_FILTER_OVERDUE = "Quá hạn"
SUMMARY_REFRESH_MS = 60_000


class MainWindow(tk.Tk):
    def __init__(self, db_path: str = "schedule.db"):
        super().__init__()
        self.storage = StorageManager(db_path=db_path)
        self.tasks: List[Task] = []
        self.sort_column = "start"
        self.sort_reverse = False
        self.toast_label: Optional[tk.Label] = None
        self.toast_job = None

        self.title("Lịch làm việc cá nhân")
        self.geometry("1180x760")
        self.minsize(980, 640)
        self.configure(bg=Theme.BG)

        Theme.apply_styles(self)
        self._build_menu()
        self._build_ui()
        self._bind_shortcuts()
        self._load_data()
        self.after(SUMMARY_REFRESH_MS, self._tick)

    # ------------------------------------------------------------------ Dựng giao diện

    def _build_menu(self):
        menubar = tk.Menu(self)

        file_menu = tk.Menu(menubar, tearoff=False)
        file_menu.add_command(label="Thêm công việc", accelerator="Ctrl+N", command=self._open_add_dialog)
        file_menu.add_command(label="Tìm giờ rảnh", accelerator="Ctrl+G", command=self._open_smart_slot_dialog)
        file_menu.add_separator()
        file_menu.add_command(label="Nhập từ tệp JSON...", command=self._import_json)
        file_menu.add_command(label="Xuất ra tệp JSON...", command=self._export_json)
        file_menu.add_separator()
        file_menu.add_command(label="Nạp dữ liệu mẫu", command=self._seed_sample_action)
        file_menu.add_separator()
        file_menu.add_command(label="Thoát", command=self.destroy)
        menubar.add_cascade(label="Tệp", menu=file_menu)

        help_menu = tk.Menu(menubar, tearoff=False)
        help_menu.add_command(label="Phím tắt", command=self._show_shortcuts)
        menubar.add_cascade(label="Trợ giúp", menu=help_menu)

        self.configure(menu=menubar)

    def _build_ui(self):
        # Thanh tiêu đề
        header = tk.Frame(self, bg=Theme.SURFACE, padx=18, pady=10, highlightthickness=1, highlightbackground=Theme.BORDER)
        header.pack(fill=tk.X)

        # Xếp nút trước để dòng tóm tắt dài chỉ bị cắt chữ chứ không đẩy mất nút
        btn_box = tk.Frame(header, bg=Theme.SURFACE)
        btn_box.pack(side=tk.RIGHT)

        title_box = tk.Frame(header, bg=Theme.SURFACE)
        title_box.pack(side=tk.LEFT, fill=tk.X, expand=True)
        tk.Label(title_box, text="Lịch làm việc cá nhân", font=Theme.FONT_TITLE, fg=Theme.TEXT, bg=Theme.SURFACE).pack(anchor="w")
        self.lbl_summary = tk.Label(title_box, font=Theme.FONT_SMALL, fg=Theme.TEXT_MUTED, bg=Theme.SURFACE, anchor="w")
        self.lbl_summary.pack(anchor="w")

        self.btn_seed = make_button(btn_box, "Nạp dữ liệu mẫu", self._seed_sample_action)
        self.btn_conflict = make_button(btn_box, "", self._show_conflicts_modal, "calm", font=Theme.FONT_SUBHEADER)
        self.btn_conflict.pack(side=tk.LEFT, padx=4)
        make_button(btn_box, "Tìm giờ rảnh", self._open_smart_slot_dialog, font=Theme.FONT_SUBHEADER).pack(side=tk.LEFT, padx=4)
        make_button(btn_box, "+ Thêm công việc", self._open_add_dialog, "primary", font=Theme.FONT_SUBHEADER).pack(side=tk.LEFT, padx=(4, 0))

        # Các tab
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=12, pady=(10, 12))

        self.tab_calendar = WeekCalendarView(self.notebook, on_edit=self._open_edit_dialog, on_add=self._open_add_dialog)
        self.notebook.add(self.tab_calendar, text="Lịch tuần")

        self.tab_tasks = tk.Frame(self.notebook, bg=Theme.BG)
        self.notebook.add(self.tab_tasks, text="Danh sách")
        self._build_tasks_tab(self.tab_tasks)

        self.tab_eisenhower = EisenhowerView(self.notebook, on_task_double_click=self._open_edit_dialog)
        self.notebook.add(self.tab_eisenhower, text="Mức ưu tiên")

        self.tab_analytics = AnalyticsView(self.notebook)
        self.notebook.add(self.tab_analytics, text="Thống kê")

        self.tab_topo = DependencyView(self.notebook, on_edit=self._open_edit_dialog)
        self.notebook.add(self.tab_topo, text="Thứ tự làm")

        self.tab_wis = OptimizeView(self.notebook, on_edit=self._open_edit_dialog, on_resolve=self._resolve_conflicts)
        self.notebook.add(self.tab_wis, text="Khi trùng lịch")

    def _build_tasks_tab(self, parent):
        filter_bar = tk.Frame(parent, bg=Theme.BG, pady=10, padx=4)
        filter_bar.pack(fill=tk.X)

        tk.Label(filter_bar, text="Tìm", font=Theme.FONT_BODY, fg=Theme.TEXT, bg=Theme.BG).pack(side=tk.LEFT, padx=(0, 4))
        self.ent_search = make_entry(filter_bar, width=22)
        self.ent_search.pack(side=tk.LEFT, padx=(0, 12), ipady=4)
        self.ent_search.bind("<KeyRelease>", lambda e: self._apply_filters())

        tk.Label(filter_bar, text="Danh mục", font=Theme.FONT_BODY, fg=Theme.TEXT, bg=Theme.BG).pack(side=tk.LEFT, padx=(0, 4))
        self.cb_filter_cat = ttk.Combobox(filter_bar, values=[STATUS_FILTER_ALL] + [c.label for c in Category], state="readonly", width=11, font=Theme.FONT_BODY)
        self.cb_filter_cat.set(STATUS_FILTER_ALL)
        self.cb_filter_cat.pack(side=tk.LEFT, padx=(0, 12))
        self.cb_filter_cat.bind("<<ComboboxSelected>>", lambda e: self._apply_filters())

        tk.Label(filter_bar, text="Trạng thái", font=Theme.FONT_BODY, fg=Theme.TEXT, bg=Theme.BG).pack(side=tk.LEFT, padx=(0, 4))
        status_values = [STATUS_FILTER_ALL, STATUS_FILTER_OPEN, STATUS_FILTER_OVERDUE] + [s.label for s in Status]
        self.cb_filter_status = ttk.Combobox(filter_bar, values=status_values, state="readonly", width=14, font=Theme.FONT_BODY)
        self.cb_filter_status.set(STATUS_FILTER_ALL)
        self.cb_filter_status.pack(side=tk.LEFT)
        self.cb_filter_status.bind("<<ComboboxSelected>>", lambda e: self._apply_filters())

        action_bar = tk.Frame(filter_bar, bg=Theme.BG)
        action_bar.pack(side=tk.RIGHT)
        self.btn_done = make_button(action_bar, "Hoàn thành", self._mark_selected_completed, "success", padx=10, pady=4)
        self.btn_done.pack(side=tk.LEFT, padx=3)
        self.btn_edit = make_button(action_bar, "Sửa", self._edit_selected_task, padx=10, pady=4)
        self.btn_edit.pack(side=tk.LEFT, padx=3)
        self.btn_delete = make_button(action_bar, "Xóa", self._delete_selected_task, "danger", padx=10, pady=4)
        self.btn_delete.pack(side=tk.LEFT, padx=(3, 0))

        tree_container = tk.Frame(parent, bg=Theme.SURFACE, highlightthickness=1, highlightbackground=Theme.BORDER)
        tree_container.pack(fill=tk.BOTH, expand=True, padx=4, pady=(0, 4))

        self.columns = [
            ("title", "Công việc", 280, "w", lambda t: t.title.lower()),
            ("category", "Danh mục", 95, "center", lambda t: t.category),
            ("priority", "Ưu tiên", 85, "center", lambda t: -t.priority.level),
            ("start", "Bắt đầu", 120, "center", lambda t: t.start_time),
            ("duration", "Thời lượng", 105, "center", lambda t: t.duration_minutes),
            ("status", "Trạng thái", 120, "center", lambda t: self._status_text(t)),
            ("deps", "Cần xong trước", 130, "center", lambda t: len(t.dependencies)),
        ]
        self.sort_keys = {c[0]: c[4] for c in self.columns}
        self.tree_tasks = ttk.Treeview(tree_container, columns=[c[0] for c in self.columns], show="headings", selectmode="browse")
        for col, text, width, anchor, _ in self.columns:
            self.tree_tasks.heading(col, text=text, command=lambda c=col: self._sort_by(c))
            self.tree_tasks.column(col, width=width, anchor=anchor, stretch=col == "title")

        scrollbar_y = ttk.Scrollbar(tree_container, orient=tk.VERTICAL, command=self.tree_tasks.yview)
        self.tree_tasks.configure(yscrollcommand=scrollbar_y.set)
        self.tree_tasks.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar_y.pack(side=tk.RIGHT, fill=tk.Y)

        self.tree_tasks.bind("<Double-Button-1>", self._on_tree_double_click)
        self.tree_tasks.bind("<Return>", lambda e: self._edit_selected_task())
        self.tree_tasks.bind("<Delete>", lambda e: self._delete_selected_task())
        self.tree_tasks.bind("<<TreeviewSelect>>", lambda e: self._update_action_buttons())

        self.tree_tasks.tag_configure("stripe", background=Theme.SURFACE_ALT)
        self.tree_tasks.tag_configure("overdue", foreground=Theme.DANGER)
        self.tree_tasks.tag_configure("completed", foreground=Theme.TEXT_MUTED)
        self.tree_tasks.tag_configure("cancelled", foreground=Theme.TEXT_FAINT)

        # Dòng thông báo khi bảng trống
        self.lbl_empty = tk.Label(self.tree_tasks, font=Theme.FONT_BODY, fg=Theme.TEXT_MUTED, bg=Theme.SURFACE)

    def _bind_shortcuts(self):
        self.bind("<Control-n>", lambda e: self._open_add_dialog())
        self.bind("<Control-g>", lambda e: self._open_smart_slot_dialog())
        self.bind("<Control-f>", lambda e: self._focus_search())
        self.bind("<F5>", lambda e: self._load_data())

    # ------------------------------------------------------------------ Dữ liệu và cập nhật

    def _load_data(self):
        self.tasks = self.storage.load_all_tasks()
        self._apply_filters()
        self._update_all_views()
        self._update_header()

    def _update_all_views(self):
        self.tab_calendar.update_tasks(self.tasks)
        self.tab_eisenhower.update_tasks(self.tasks)
        self.tab_analytics.update_tasks(self.tasks)
        self.tab_topo.update_tasks(self.tasks)
        self.tab_wis.update_tasks(self.tasks)

    def _tick(self):
        """Cập nhật các nội dung phụ thuộc vào giờ hiện tại mỗi phút."""
        self._update_header()
        self.tab_calendar.redraw()
        self.after(SUMMARY_REFRESH_MS, self._tick)

    def _update_header(self):
        now = datetime.now()
        date_text = f"{WEEKDAY_FULL[now.weekday()]}, {now.strftime('%d/%m/%Y')}"

        if not self.tasks:
            self.lbl_summary.configure(text=f"{date_text}  ·  Chưa có công việc nào. Hãy thêm việc đầu tiên hoặc nạp dữ liệu mẫu.")
            self.btn_seed.pack(side=tk.LEFT, padx=4, before=self.btn_conflict)
        else:
            self.btn_seed.pack_forget()
            active = [t for t in self.tasks if t.is_active]
            today_count = sum(1 for t in active if t.start_time.date() == now.date())
            overdue = sum(1 for t in active if t.is_overdue(now))
            upcoming = [t for t in active if t.start_time >= now]
            parts = [date_text, f"Hôm nay: {today_count} việc"]
            if upcoming:
                nearest = min(upcoming, key=lambda t: t.start_time)
                parts.append(f"Tiếp theo: {nearest.title} ({format_datetime(nearest.start_time)})")
            if overdue:
                parts.append(f"{overdue} việc quá hạn")
            self.lbl_summary.configure(text="  ·  ".join(parts))

        conflict_count = len(SchedulerEngine.detect_all_conflicts(self.tasks))
        if conflict_count:
            self.btn_conflict.configure(text=f"Có {conflict_count} cặp trùng giờ")
            set_button_kind(self.btn_conflict, "warning")
        else:
            self.btn_conflict.configure(text="Không trùng giờ")
            set_button_kind(self.btn_conflict, "calm")

    @staticmethod
    def _status_text(task: Task) -> str:
        return "Quá hạn" if task.is_overdue() else task.status.label

    def _matches_filters(self, task: Task) -> bool:
        query = self.ent_search.get().strip().lower()
        if query and query not in task.title.lower() and query not in task.description.lower():
            return False

        category = self.cb_filter_cat.get()
        if category != STATUS_FILTER_ALL and task.category != category:
            return False

        status_filter = self.cb_filter_status.get()
        if status_filter == STATUS_FILTER_OPEN:
            return task.is_active
        if status_filter == STATUS_FILTER_OVERDUE:
            return task.is_overdue()
        return status_filter == STATUS_FILTER_ALL or task.status.label == status_filter

    def _apply_filters(self):
        self.tree_tasks.delete(*self.tree_tasks.get_children())

        rows = [t for t in self.tasks if self._matches_filters(t)]
        rows.sort(key=self.sort_keys[self.sort_column], reverse=self.sort_reverse)

        for index, t in enumerate(rows):
            tags = ["stripe"] if index % 2 else []
            if t.status == Status.COMPLETED:
                tags.append("completed")
            elif t.status == Status.CANCELLED:
                tags.append("cancelled")
            elif t.is_overdue():
                tags.append("overdue")

            self.tree_tasks.insert(
                "",
                "end",
                iid=t.id,
                values=(
                    t.title,
                    t.category,
                    t.priority.label,
                    format_datetime(t.start_time),
                    format_duration(t.duration_minutes),
                    self._status_text(t),
                    f"{len(t.dependencies)} việc" if t.dependencies else "-"
                ),
                tags=tags
            )

        self._update_sort_headings()
        self._update_action_buttons()

        if rows:
            self.lbl_empty.place_forget()
        else:
            message = "Không có việc nào khớp bộ lọc." if self.tasks else "Chưa có công việc nào. Bấm \"+ Thêm công việc\" để bắt đầu."
            self.lbl_empty.configure(text=message)
            self.lbl_empty.place(relx=0.5, rely=0.4, anchor="center")

    def _sort_by(self, column: str):
        if self.sort_column == column:
            self.sort_reverse = not self.sort_reverse
        else:
            self.sort_column, self.sort_reverse = column, False
        self._apply_filters()

    def _update_sort_headings(self):
        for col, text, *_ in self.columns:
            arrow = (" ▼" if self.sort_reverse else " ▲") if col == self.sort_column else ""
            self.tree_tasks.heading(col, text=text + arrow)

    def _update_action_buttons(self):
        enabled = bool(self.tree_tasks.selection())
        for button in (self.btn_done, self.btn_edit, self.btn_delete):
            set_button_enabled(button, enabled)

    def _selected_task(self) -> Optional[Task]:
        selected = self.tree_tasks.selection()
        return self.storage.get_task_by_id(selected[0]) if selected else None

    def _focus_search(self):
        self.notebook.select(self.tab_tasks)
        self.ent_search.focus_set()

    # ------------------------------------------------------------------ Thông báo

    def _toast(self, message: str, color: str = Theme.SUCCESS):
        """Hiện thông báo ngắn ở góc cửa sổ rồi tự ẩn, không bắt người dùng bấm OK."""
        if self.toast_job:
            self.after_cancel(self.toast_job)
        if self.toast_label is None:
            self.toast_label = tk.Label(self, font=Theme.FONT_SUBHEADER, fg="white", padx=16, pady=8)
        self.toast_label.configure(text=message, bg=color)
        self.toast_label.place(relx=0.5, rely=1.0, y=-24, anchor="s")
        self.toast_label.lift()
        self.toast_job = self.after(3000, self.toast_label.place_forget)

    def _show_shortcuts(self):
        messagebox.showinfo(
            "Phím tắt",
            "Ctrl+N: Thêm công việc\n"
            "Ctrl+G: Tìm giờ rảnh\n"
            "Ctrl+F: Tìm trong danh sách\n"
            "F5: Tải lại dữ liệu\n"
            "Ctrl+S: Lưu trong hộp thoại công việc\n"
            "Esc: Đóng hộp thoại\n"
            "Enter / Delete: Sửa / Xóa việc đang chọn trong danh sách",
            parent=self
        )

    # ------------------------------------------------------------------ Thao tác công việc

    def _persist_task(self, task: Task, message: str):
        try:
            self.storage.save_task(task)
        except sqlite3.IntegrityError:
            messagebox.showerror("Không lưu được", "Công việc tiên quyết đã chọn không còn tồn tại. Vui lòng kiểm tra lại.", parent=self)
            self._load_data()
            return
        self._load_data()
        self._toast(message)

    def _open_add_dialog(self, default_start: Optional[datetime] = None, default_end: Optional[datetime] = None):
        TaskDialog(
            self,
            all_tasks=self.tasks,
            on_save=lambda task: self._persist_task(task, f"Đã thêm: {task.title}"),
            default_start=default_start,
            default_end=default_end
        )

    def _open_edit_dialog(self, task: Task):
        TaskDialog(self, all_tasks=self.tasks, task=task, on_save=lambda t: self._persist_task(t, f"Đã cập nhật: {t.title}"))

    def _on_tree_double_click(self, event):
        if self.tree_tasks.identify_row(event.y):
            self._edit_selected_task()

    def _edit_selected_task(self):
        task = self._selected_task()
        if task:
            self._open_edit_dialog(task)

    def _delete_selected_task(self):
        task = self._selected_task()
        if not task:
            return
        dependents = [t.title for t in self.tasks if task.id in t.dependencies]
        message = f"Xóa công việc '{task.title}'?"
        if dependents:
            message += "\n\nCác việc sau đang cần việc này xong trước và sẽ bỏ ràng buộc đó:\n- " + "\n- ".join(dependents)
        if messagebox.askyesno("Xác nhận xóa", message, parent=self):
            self.storage.delete_task(task.id)
            self._load_data()
            self._toast(f"Đã xóa: {task.title}", Theme.TEXT_MUTED)

    def _mark_selected_completed(self):
        task = self._selected_task()
        if not task:
            return
        blocking = SchedulerEngine.unfinished_prerequisites(task, self.tasks)
        if blocking:
            names = "\n- ".join(t.title for t in blocking)
            if not messagebox.askyesno("Chưa xong việc trước đó", f"Các việc sau cần xong trước nhưng chưa xong:\n- {names}\n\nVẫn đánh dấu hoàn thành?", parent=self):
                return
        task.status = Status.COMPLETED
        self._persist_task(task, f"Đã hoàn thành: {task.title}")

    def _open_smart_slot_dialog(self):
        def _on_slot_selected(start_time: datetime, end_time: datetime, duration: int):
            self._open_add_dialog(default_start=start_time, default_end=end_time)

        SmartSlotDialog(self, all_tasks=self.tasks, on_slot_selected=_on_slot_selected)

    def _show_conflicts_modal(self):
        conflicts = SchedulerEngine.detect_all_conflicts(self.tasks)
        if not conflicts:
            self._toast("Lịch của bạn không có việc nào trùng giờ.")
            return

        modal = tk.Toplevel(self)
        modal.title("Các việc trùng giờ")
        modal.configure(bg=Theme.SURFACE)

        body = tk.Frame(modal, bg=Theme.SURFACE, padx=18, pady=16)
        body.pack(fill=tk.BOTH, expand=True)

        tk.Label(body, text=f"Có {len(conflicts)} cặp việc trùng giờ", font=Theme.FONT_HEADER, fg=Theme.TEXT, bg=Theme.SURFACE).pack(anchor="w")
        tk.Label(body, text="Nháy đúp vào một dòng để sửa việc thứ hai trong cặp.", font=Theme.FONT_SMALL, fg=Theme.TEXT_MUTED, bg=Theme.SURFACE).pack(anchor="w", pady=(0, 10))

        tree_frame = tk.Frame(body, bg=Theme.SURFACE, highlightthickness=1, highlightbackground=Theme.BORDER)
        tree_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 12))
        cols = (("task1", "Việc thứ nhất", 210, "w"), ("task2", "Việc thứ hai", 210, "w"), ("overlap", "Trùng lúc", 150, "center"), ("minutes", "Trùng", 80, "center"))
        tree = ttk.Treeview(tree_frame, columns=[c[0] for c in cols], show="headings", height=8, selectmode="browse")
        for col, text, width, anchor in cols:
            tree.heading(col, text=text)
            tree.column(col, width=width, anchor=anchor)
        scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        row_task = {}
        for c in conflicts:
            overlap = f"{format_datetime(c.overlap_start)}–{c.overlap_end.strftime('%H:%M')}"
            row = tree.insert("", "end", values=(c.task1.title, c.task2.title, overlap, format_duration(c.overlap_minutes)))
            row_task[row] = c.task2

        def _on_double_click(event):
            task = row_task.get(tree.identify_row(event.y))
            if task:
                modal.destroy()
                self._open_edit_dialog(task)

        tree.bind("<Double-Button-1>", _on_double_click)
        make_button(body, "Đóng", modal.destroy, padx=16).pack(side=tk.RIGHT)
        make_modal(modal, self)

    def _resolve_conflicts(self):
        """Xem trước phương án dời việc, người dùng đồng ý thì lưu tất cả trong một giao dịch."""
        moves, unplaced = SchedulerEngine.plan_conflict_resolution(self.tasks)
        if not moves:
            messagebox.showinfo("Tự dời việc", "Không tìm được khung giờ trống trong 14 ngày tới để dời các việc này.", parent=self)
            return

        lines = [f"- {m.task.title}: {format_datetime(m.task.start_time)} → {format_datetime(m.new_start)}" for m in moves]
        for move in moves:
            if move.blocked_titles:
                lines.append(f"Lưu ý: '{move.blocked_titles[0]}' đang cần '{move.task.title}' xong trước, hãy xem lại giờ của việc đó.")
        if unplaced:
            lines.append("Chưa xếp được: " + ", ".join(t.title for t in unplaced))
        if not messagebox.askyesno("Tự dời việc", "Chương trình đề xuất:\n\n" + "\n".join(lines) + "\n\nÁp dụng phương án này?", parent=self):
            return

        for move in moves:
            move.task.start_time, move.task.end_time = move.new_start, move.new_end
        self.storage.save_tasks([m.task for m in moves])
        self._load_data()
        self._toast(f"Đã dời {len(moves)} công việc.")

    def _seed_sample_action(self):
        confirm = messagebox.askyesno(
            "Nạp dữ liệu mẫu",
            "Thêm 11 công việc mẫu (mã T01 đến T11) bắt đầu từ hôm nay? Nếu đã có việc mang các mã này thì chúng sẽ bị ghi đè.",
            parent=self
        )
        if confirm:
            self.storage.seed_sample_data()
            self._load_data()
            self._toast("Đã nạp 11 công việc mẫu.")

    def _export_json(self):
        path = filedialog.asksaveasfilename(
            parent=self,
            title="Xuất lịch ra tệp JSON",
            defaultextension=".json",
            initialfile="lich_lam_viec.json",
            filetypes=[("Tệp JSON", "*.json")]
        )
        if not path:
            return
        try:
            self.storage.export_to_json(path)
        except OSError as e:
            messagebox.showerror("Không xuất được tệp", str(e), parent=self)
            return
        self._toast(f"Đã xuất {len(self.tasks)} công việc.")

    def _import_json(self):
        path = filedialog.askopenfilename(parent=self, title="Nhập lịch từ tệp JSON", filetypes=[("Tệp JSON", "*.json")])
        if not path:
            return
        replace = messagebox.askyesnocancel(
            "Nhập dữ liệu",
            "Thay thế toàn bộ lịch hiện tại bằng dữ liệu trong tệp?\n\n"
            "Có: xóa lịch hiện tại rồi nhập.\nKhông: gộp vào lịch hiện tại.",
            parent=self
        )
        if replace is None:
            return
        try:
            count = self.storage.import_from_json(path, clear_existing=replace)
        except (OSError, ValueError) as e:  # json.JSONDecodeError là lớp con của ValueError
            messagebox.showerror("Không nhập được tệp", f"Dữ liệu hiện tại không thay đổi.\n\n{e}", parent=self)
            return
        self._load_data()
        self._toast(f"Đã nhập {count} công việc.")
