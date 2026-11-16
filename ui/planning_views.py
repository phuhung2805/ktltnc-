"""
ui/planning_views.py
Hai màn hình lập kế hoạch dựa trên thuật toán:
- DependencyView: thứ tự làm việc theo quan hệ tiên quyết (Thuật toán Kahn).
- OptimizeView: nên giữ việc nào khi không thể làm hết (Quy hoạch động Weighted Interval Scheduling).
"""

import tkinter as tk
from tkinter import ttk
from typing import Callable, List, Optional
from core.models import Task, Status
from core.scheduler_engine import SchedulerEngine
from ui.theme import Theme
from ui.widgets import format_datetime, format_duration, make_button


def _make_tree(parent, columns) -> ttk.Treeview:
    """Tạo bảng có thanh cuộn từ danh sách (mã cột, tiêu đề, độ rộng, căn lề)."""
    frame = tk.Frame(parent, bg=Theme.SURFACE, highlightthickness=1, highlightbackground=Theme.BORDER)
    frame.pack(fill=tk.BOTH, expand=True)
    tree = ttk.Treeview(frame, columns=[c[0] for c in columns], show="headings", selectmode="browse")
    for col, text, width, anchor in columns:
        tree.heading(col, text=text)
        tree.column(col, width=width, anchor=anchor, stretch=col == "title")
    scrollbar = ttk.Scrollbar(frame, orient=tk.VERTICAL, command=tree.yview)
    tree.configure(yscrollcommand=scrollbar.set)
    tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    return tree


class _PlanningView(tk.Frame):
    """Khung chung: tiêu đề, dòng giải thích, dòng kết quả và bảng; nháy đúp một dòng để sửa việc."""

    def __init__(self, parent, title: str, subtitle: str, columns, on_edit: Optional[Callable[[Task], None]] = None):
        super().__init__(parent, bg=Theme.BG)
        self.on_edit = on_edit
        self.task_by_row = {}

        box = tk.Frame(self, bg=Theme.BG, padx=16, pady=12)
        box.pack(fill=tk.BOTH, expand=True)

        tk.Label(box, text=title, font=Theme.FONT_HEADER, fg=Theme.TEXT, bg=Theme.BG).pack(anchor="w")
        tk.Label(box, text=subtitle, font=Theme.FONT_SMALL, fg=Theme.TEXT_MUTED, bg=Theme.BG).pack(anchor="w")
        self.lbl_summary = tk.Label(box, font=Theme.FONT_SUBHEADER, bg=Theme.BG, anchor="w", justify="left", wraplength=1050)
        self.lbl_summary.pack(fill=tk.X, pady=(8, 8))

        self.tree = _make_tree(box, columns)
        self.tree.bind("<Double-Button-1>", self._on_double_click)
        self.lower_box = box

    def _clear(self) -> None:
        self.tree.delete(*self.tree.get_children())
        self.task_by_row = {}

    def _insert(self, task: Task, values, tags=()) -> None:
        row = self.tree.insert("", "end", values=values, tags=tags)
        self.task_by_row[row] = task

    def _on_double_click(self, event) -> None:
        task = self.task_by_row.get(self.tree.identify_row(event.y))
        if task and self.on_edit:
            self.on_edit(task)


class DependencyView(_PlanningView):
    def __init__(self, parent, on_edit: Optional[Callable[[Task], None]] = None):
        super().__init__(
            parent,
            "Nên làm theo thứ tự nào?",
            "Sắp xếp theo quan hệ \"cần xong trước\" bằng thuật toán Kahn (Topological Sort), đồng thời phát hiện vòng lặp phụ thuộc.",
            [
                ("step", "Bước", 55, "center"),
                ("title", "Công việc", 280, "w"),
                ("start", "Bắt đầu", 120, "center"),
                ("status", "Trạng thái", 120, "center"),
                ("ready", "Có thể làm chưa?", 300, "w"),
            ],
            on_edit
        )
        self.tree.tag_configure("done", foreground=Theme.TEXT_FAINT)
        self.tree.tag_configure("blocked", foreground=Theme.TEXT_MUTED)
        self.tree.tag_configure("ready", foreground=Theme.SUCCESS)

        tk.Label(self.lower_box, text="Lưu ý về thời gian", font=Theme.FONT_SUBHEADER, fg=Theme.TEXT, bg=Theme.BG).pack(anchor="w", pady=(10, 4))
        self.txt_warnings = tk.Text(
            self.lower_box,
            height=3,
            font=Theme.FONT_SMALL,
            bg=Theme.SURFACE,
            fg=Theme.TEXT,
            relief="flat",
            wrap="word",
            state="disabled",
            highlightthickness=1,
            highlightbackground=Theme.BORDER,
            padx=8,
            pady=6
        )
        self.txt_warnings.pack(fill=tk.X)

    def _set_warnings(self, text: str, color: str) -> None:
        self.txt_warnings.configure(state="normal", fg=color)
        self.txt_warnings.delete("1.0", tk.END)
        self.txt_warnings.insert("1.0", text)
        self.txt_warnings.configure(state="disabled")

    def update_tasks(self, tasks: List[Task]) -> None:
        self._clear()
        try:
            ordered, warnings = SchedulerEngine.topological_sort(tasks)
        except ValueError as e:
            self.lbl_summary.configure(text="Có vòng lặp phụ thuộc, không thể sắp xếp thứ tự. Hãy sửa lại các việc được nêu bên dưới.", fg=Theme.DANGER)
            self._set_warnings(str(e), Theme.DANGER)
            return

        ready_count = 0
        for index, t in enumerate(ordered, start=1):
            blocking = SchedulerEngine.unfinished_prerequisites(t, tasks)
            if not t.is_active:
                ready, tag = "Đã xong" if t.status == Status.COMPLETED else "Đã hủy", "done"
            elif blocking:
                ready, tag = f"Chờ: {blocking[0].title}", "blocked"
            else:
                ready, tag = "Làm được ngay", "ready"
                ready_count += 1
            self._insert(t, (index, t.title, format_datetime(t.start_time), t.status.label, ready), (tag,))

        self.lbl_summary.configure(text=f"Không có vòng lặp phụ thuộc. Có {ready_count} việc làm được ngay.", fg=Theme.SUCCESS)
        if warnings:
            self._set_warnings("\n".join(warnings), Theme.WARNING)
        else:
            self._set_warnings("Thời gian các việc đều khớp với thứ tự phụ thuộc.", Theme.TEXT_MUTED)


class OptimizeView(_PlanningView):
    def __init__(self, parent, on_edit: Optional[Callable[[Task], None]] = None, on_resolve: Optional[Callable[[], None]] = None):
        super().__init__(
            parent,
            "Không thể làm hết thì giữ việc nào?",
            "Chọn tập việc không trùng giờ có tổng điểm lớn nhất bằng quy hoạch động (Weighted Interval Scheduling). "
            "Điểm phụ thuộc chủ yếu vào mức ưu tiên.",
            [
                ("advice", "Đề xuất", 85, "center"),
                ("title", "Công việc", 310, "w"),
                ("priority", "Ưu tiên", 90, "center"),
                ("start", "Bắt đầu", 120, "center"),
                ("duration", "Thời lượng", 110, "center"),
                ("score", "Điểm", 70, "center"),
            ],
            on_edit
        )
        self.on_resolve = on_resolve
        self.tree.tag_configure("keep", foreground=Theme.TEXT)
        self.tree.tag_configure("move", foreground=Theme.DANGER)
        self.btn_resolve = make_button(self.lower_box, "Tự dời các việc này", self._on_resolve_click, "primary", font=Theme.FONT_SUBHEADER)

    def _on_resolve_click(self) -> None:
        if self.on_resolve:
            self.on_resolve()

    def update_tasks(self, tasks: List[Task]) -> None:
        self._clear()
        self.btn_resolve.pack_forget()
        active = [t for t in tasks if t.is_active]
        if not active:
            self.lbl_summary.configure(text="Không có việc nào đang chờ làm.", fg=Theme.TEXT_MUTED)
            return

        total, selected = SchedulerEngine.weighted_interval_scheduling(tasks)
        selected_ids = {t.id for t in selected}
        dropped = len(active) - len(selected)

        if dropped:
            text = f"Nên giữ {len(selected)}/{len(active)} việc (tổng {total:.1f} điểm) và dời {dropped} việc đang trùng giờ."
            self.lbl_summary.configure(text=text, fg=Theme.WARNING)
            self.btn_resolve.pack(anchor="e", pady=(10, 0))
        else:
            self.lbl_summary.configure(text=f"Làm được cả {len(active)} việc, không có việc nào phải dời.", fg=Theme.SUCCESS)

        # Đưa các việc nên dời lên đầu để người dùng thấy ngay
        for t in sorted(active, key=lambda t: (t.id in selected_ids, t.start_time)):
            keep = t.id in selected_ids
            self._insert(t, (
                "Giữ" if keep else "Nên dời",
                t.title,
                t.priority.label,
                format_datetime(t.start_time),
                format_duration(t.duration_minutes),
                f"{SchedulerEngine.task_weight(t):.1f}"
            ), ("keep" if keep else "move",))
