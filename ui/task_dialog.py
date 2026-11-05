"""
ui/task_dialog.py
Hộp thoại thêm mới hoặc chỉnh sửa công việc trong lịch trình.
Chọn ngày bằng lịch tháng, chọn việc tiên quyết bằng danh sách, tự kiểm tra xung đột ngay khi đổi thời gian.
"""

import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime, timedelta
from typing import Optional, List, Callable
from core.models import Task, Priority, Status, Category
from core.scheduler_engine import SchedulerEngine
from ui.theme import Theme
from ui.widgets import DateTimeField, make_button, make_entry, make_modal, format_datetime

DURATION_CHOICES = [("30 phút", 30), ("1 giờ", 60), ("2 giờ", 120), ("3 giờ", 180)]


class TaskDialog(tk.Toplevel):
    def __init__(
        self,
        parent: tk.Tk,
        all_tasks: List[Task],
        task: Optional[Task] = None,
        on_save: Optional[Callable[[Task], None]] = None,
        default_start: Optional[datetime] = None,
        default_end: Optional[datetime] = None
    ):
        super().__init__(parent)
        self.parent = parent
        self.all_tasks = all_tasks
        self.task = task
        self.on_save = on_save
        self.is_edit_mode = task is not None

        self.title("Sửa công việc" if self.is_edit_mode else "Thêm công việc")
        self.resizable(False, False)
        self.configure(bg=Theme.SURFACE)

        self._build_ui(default_start, default_end)
        make_modal(self, parent)
        self.bind("<Control-s>", lambda e: self._save_action())
        self.ent_title.focus_set()

    def _default_times(self, default_start: Optional[datetime], default_end: Optional[datetime]):
        if self.task:
            return self.task.start_time, self.task.end_time
        # Thời điểm người dùng đã chọn được giữ nguyên; nếu không chọn thì lấy đầu giờ kế tiếp
        start = default_start or datetime.now().replace(minute=0, second=0, microsecond=0) + timedelta(hours=1)
        return start, default_end or start + timedelta(hours=1)

    def _label(self, parent, text: str) -> tk.Label:
        label = tk.Label(parent, text=text, font=Theme.FONT_SUBHEADER, fg=Theme.TEXT, bg=Theme.SURFACE)
        label.pack(anchor="w")
        return label

    def _build_ui(self, default_start: Optional[datetime], default_end: Optional[datetime]):
        main_frame = tk.Frame(self, bg=Theme.SURFACE, padx=24, pady=18)
        main_frame.pack(fill=tk.BOTH, expand=True)

        tk.Label(
            main_frame,
            text="Sửa công việc" if self.is_edit_mode else "Thêm công việc mới",
            font=Theme.FONT_TITLE,
            fg=Theme.TEXT,
            bg=Theme.SURFACE
        ).pack(anchor="w", pady=(0, 12))

        # Tiêu đề
        self._label(main_frame, "Tên công việc")
        self.ent_title = make_entry(main_frame, width=58)
        self.ent_title.pack(fill=tk.X, pady=(4, 12), ipady=5)
        if self.task:
            self.ent_title.insert(0, self.task.title)

        # Thời gian
        start_def, end_def = self._default_times(default_start, default_end)
        self.previous_start = start_def

        time_grid = tk.Frame(main_frame, bg=Theme.SURFACE)
        time_grid.pack(fill=tk.X)
        tk.Label(time_grid, text="Bắt đầu", font=Theme.FONT_SUBHEADER, fg=Theme.TEXT, bg=Theme.SURFACE, width=8, anchor="w").grid(row=0, column=0, sticky="w")
        self.field_start = DateTimeField(time_grid, start_def, self._on_start_changed)
        self.field_start.grid(row=0, column=1, sticky="w", pady=2)
        tk.Label(time_grid, text="Kết thúc", font=Theme.FONT_SUBHEADER, fg=Theme.TEXT, bg=Theme.SURFACE, width=8, anchor="w").grid(row=1, column=0, sticky="w")
        self.field_end = DateTimeField(time_grid, end_def, self._refresh_hints)
        self.field_end.grid(row=1, column=1, sticky="w", pady=2)

        chips = tk.Frame(main_frame, bg=Theme.SURFACE)
        chips.pack(anchor="w", pady=(6, 4))
        tk.Label(chips, text="Thời lượng nhanh:", font=Theme.FONT_SMALL, fg=Theme.TEXT_MUTED, bg=Theme.SURFACE).pack(side=tk.LEFT, padx=(0, 6))
        for text, minutes in DURATION_CHOICES:
            make_button(chips, text, lambda m=minutes: self._set_duration(m), font=Theme.FONT_SMALL, padx=8, pady=2).pack(side=tk.LEFT, padx=2)

        self.lbl_time_status = tk.Label(main_frame, font=Theme.FONT_SMALL, bg=Theme.SURFACE, justify="left", anchor="w", wraplength=500)
        self.lbl_time_status.pack(fill=tk.X, pady=(2, 10))

        # Danh mục, ưu tiên, trạng thái
        row = tk.Frame(main_frame, bg=Theme.SURFACE)
        row.pack(fill=tk.X, pady=(0, 12))
        for col in range(3):
            row.columnconfigure(col, weight=1, uniform="fields")

        self.cb_category = self._combobox(row, 0, "Danh mục", [c.label for c in Category],
                                          self.task.category if self.task else Category.WORK.label)
        self.cb_priority = self._combobox(row, 1, "Mức ưu tiên", [p.label for p in Priority],
                                          self.task.priority.label if self.task else Priority.MEDIUM.label)
        self.cb_status = self._combobox(row, 2, "Trạng thái", [s.label for s in Status],
                                        self.task.status.label if self.task else Status.PENDING.label)
        self.cb_status.bind("<<ComboboxSelected>>", lambda e: self._refresh_hints(), add="+")

        # Việc tiên quyết
        self._label(main_frame, "Cần xong trước (bấm để chọn, có thể chọn nhiều)")
        dep_frame = tk.Frame(main_frame, bg=Theme.SURFACE)
        dep_frame.pack(fill=tk.X, pady=(4, 4))
        self.lst_deps = tk.Listbox(
            dep_frame,
            selectmode=tk.MULTIPLE,
            exportselection=False,
            height=4,
            font=Theme.FONT_SMALL,
            bg=Theme.SURFACE,
            fg=Theme.TEXT,
            selectbackground=Theme.PRIMARY_SOFT,
            selectforeground=Theme.TEXT,
            relief="flat",
            highlightthickness=1,
            highlightbackground=Theme.BORDER,
            activestyle="none"
        )
        dep_scroll = ttk.Scrollbar(dep_frame, orient=tk.VERTICAL, command=self.lst_deps.yview)
        self.lst_deps.configure(yscrollcommand=dep_scroll.set)
        self.lst_deps.pack(side=tk.LEFT, fill=tk.X, expand=True)
        dep_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self._fill_dependency_list()
        self.lst_deps.bind("<<ListboxSelect>>", lambda e: self._refresh_hints())

        self.lbl_dep_status = tk.Label(main_frame, font=Theme.FONT_SMALL, bg=Theme.SURFACE, justify="left", anchor="w", wraplength=500)
        self.lbl_dep_status.pack(fill=tk.X, pady=(0, 10))

        # Ghi chú
        self._label(main_frame, "Ghi chú")
        self.txt_desc = tk.Text(
            main_frame,
            height=3,
            width=10,
            font=Theme.FONT_BODY,
            bg=Theme.SURFACE,
            fg=Theme.TEXT,
            insertbackground=Theme.TEXT,
            relief="flat",
            wrap="word",
            highlightthickness=1,
            highlightbackground=Theme.BORDER,
            highlightcolor=Theme.PRIMARY
        )
        self.txt_desc.pack(fill=tk.X, pady=(4, 14))
        if self.task:
            self.txt_desc.insert("1.0", self.task.description)

        # Hàng nút
        btn_bar = tk.Frame(main_frame, bg=Theme.SURFACE)
        btn_bar.pack(fill=tk.X)
        self.lbl_error = tk.Label(btn_bar, font=Theme.FONT_SMALL, fg=Theme.DANGER, bg=Theme.SURFACE, anchor="w", wraplength=300, justify="left")
        self.lbl_error.pack(side=tk.LEFT, fill=tk.X, expand=True)
        make_button(btn_bar, "Lưu công việc", self._save_action, "primary", font=Theme.FONT_SUBHEADER, padx=18).pack(side=tk.RIGHT)
        make_button(btn_bar, "Hủy bỏ", self.destroy, padx=14).pack(side=tk.RIGHT, padx=(0, 8))

        self._refresh_hints()

    def _combobox(self, parent, col: int, label: str, values: List[str], current: str) -> ttk.Combobox:
        frame = tk.Frame(parent, bg=Theme.SURFACE)
        frame.grid(row=0, column=col, sticky="ew", padx=(0 if col == 0 else 6, 0))
        self._label(frame, label)
        combo = ttk.Combobox(frame, values=values, state="readonly", font=Theme.FONT_BODY, width=12)
        combo.pack(fill=tk.X, pady=(4, 0))
        combo.set(current)
        return combo

    def _fill_dependency_list(self) -> None:
        current = set(self.task.dependencies) if self.task else set()
        candidates = [
            t for t in sorted(self.all_tasks, key=lambda t: t.start_time)
            if (not self.task or t.id != self.task.id) and (t.status.name != "CANCELLED" or t.id in current)
        ]
        self.dep_candidates = candidates
        for index, t in enumerate(candidates):
            self.lst_deps.insert(tk.END, f"{format_datetime(t.start_time)}  ·  {t.title}")
            if t.id in current:
                self.lst_deps.selection_set(index)

    def _selected_dependencies(self) -> List[str]:
        return [self.dep_candidates[i].id for i in self.lst_deps.curselection()]

    def _on_start_changed(self) -> None:
        """Dời giờ bắt đầu thì giữ nguyên thời lượng công việc."""
        new_start = self.field_start.get()
        end = self.field_end.get()
        if new_start and end and self.previous_start:
            self.field_end.set(end + (new_start - self.previous_start))
        if new_start:
            self.previous_start = new_start
        self._refresh_hints()

    def _set_duration(self, minutes: int) -> None:
        start = self.field_start.get()
        if start:
            self.field_end.set(start + timedelta(minutes=minutes))
            self._refresh_hints()

    def _build_candidate(self) -> Optional[Task]:
        """Tạo đối tượng công việc từ dữ liệu đang nhập; trả về None nếu thời gian chưa hợp lệ."""
        start, end = self.field_start.get(), self.field_end.get()
        if not start or not end or end <= start:
            return None
        return Task(
            id=self.task.id if self.task else None,
            title=self.ent_title.get().strip() or "Công việc này",
            start_time=start,
            end_time=end,
            category=self.cb_category.get(),
            priority=Priority.from_string(self.cb_priority.get()),
            status=Status.from_string(self.cb_status.get()),
            dependencies=self._selected_dependencies(),
            description=self.txt_desc.get("1.0", tk.END).strip(),
            created_at=self.task.created_at if self.task else None
        )

    def _refresh_hints(self) -> None:
        """Cập nhật thông báo về thời gian và việc tiên quyết ngay khi người dùng thay đổi."""
        self.lbl_error.configure(text="")
        candidate = self._build_candidate()
        if candidate is None:
            start, end = self.field_start.get(), self.field_end.get()
            text = "Giờ hoặc phút chưa hợp lệ." if not start or not end else "Giờ kết thúc phải sau giờ bắt đầu."
            self.lbl_time_status.configure(text=text, fg=Theme.DANGER)
            self.lbl_dep_status.configure(text="")
            return

        conflicts = SchedulerEngine.detect_conflicts_for_task(candidate, self.all_tasks)
        if conflicts:
            names = ", ".join(f"'{c.task2.title}'" for c in conflicts[:2])
            more = f" và {len(conflicts) - 2} việc khác" if len(conflicts) > 2 else ""
            self.lbl_time_status.configure(text=f"Trùng giờ với {names}{more}.", fg=Theme.WARNING)
        else:
            self.lbl_time_status.configure(text="Không trùng giờ với việc nào.", fg=Theme.SUCCESS)

        errors = SchedulerEngine.validate_dependencies(candidate, self.all_tasks)
        if errors:
            self.lbl_dep_status.configure(text=errors[0], fg=Theme.DANGER)
            return
        task_map = {t.id: t for t in self.all_tasks}
        early = [task_map[d].title for d in candidate.dependencies if candidate.start_time < task_map[d].end_time]
        if early:
            self.lbl_dep_status.configure(text=f"Lưu ý: việc này bắt đầu trước khi '{early[0]}' kết thúc.", fg=Theme.WARNING)
        else:
            self.lbl_dep_status.configure(text="")

    def _save_action(self):
        if not self.ent_title.get().strip():
            self.lbl_error.configure(text="Vui lòng nhập tên công việc.")
            self.ent_title.focus_set()
            return

        task = self._build_candidate()
        if task is None:
            self.lbl_error.configure(text="Vui lòng sửa lại thời gian.")
            return

        errors = SchedulerEngine.validate_dependencies(task, self.all_tasks)
        if errors:
            self.lbl_error.configure(text=errors[0])
            return

        conflicts = SchedulerEngine.detect_conflicts_for_task(task, self.all_tasks)
        if conflicts:
            first = conflicts[0]
            confirm = messagebox.askyesno(
                "Trùng lịch",
                f"Công việc này trùng giờ với {len(conflicts)} việc khác, "
                f"ví dụ '{first.task2.title}' ({first.overlap_minutes} phút).\n\nVẫn lưu chứ?",
                parent=self
            )
            if not confirm:
                return

        if self.on_save:
            self.on_save(task)
        self.destroy()
