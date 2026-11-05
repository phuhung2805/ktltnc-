"""
ui/eisenhower_view.py
Thành phần hiển thị Ma trận Eisenhower 4 góc phần tư trực quan.
Hỗ trợ phân loại nhiệm vụ tự động dựa trên độ ưu tiên và mức độ khẩn cấp theo mốc thời gian.
"""

import tkinter as tk
from tkinter import ttk
from datetime import datetime
from typing import List, Callable, Optional
from core.models import Task
from core.scheduler_engine import SchedulerEngine
from ui.theme import Theme
from ui.widgets import format_datetime

QUADRANTS = [
    ("Q1", "Làm ngay", "Quan trọng và gấp", Theme.DANGER, 0, 0),
    ("Q2", "Lên kế hoạch", "Quan trọng, chưa gấp", Theme.PRIMARY, 0, 1),
    ("Q3", "Làm nhanh hoặc nhờ người khác", "Gấp, ít quan trọng", Theme.WARNING, 1, 0),
    ("Q4", "Làm khi rảnh", "Không gấp, ít quan trọng", Theme.TEXT_MUTED, 1, 1),
]


class EisenhowerView(tk.Frame):
    def __init__(self, parent: tk.Widget, on_task_double_click: Optional[Callable[[Task], None]] = None):
        super().__init__(parent, bg=Theme.BG)
        self.on_task_double_click = on_task_double_click
        self.current_tasks: List[Task] = []
        self.quadrants = {}
        self._build_ui()

    def _build_ui(self):
        top_bar = tk.Frame(self, bg=Theme.BG)
        top_bar.pack(fill=tk.X, padx=16, pady=(12, 8))

        tk.Label(top_bar, text="Việc nào nên làm trước?", font=Theme.FONT_HEADER, fg=Theme.TEXT, bg=Theme.BG).pack(anchor="w")
        tk.Label(
            top_bar,
            text="Ma trận Eisenhower: \"gấp\" là việc bắt đầu trong 24 giờ tới hoặc đã qua giờ, \"quan trọng\" là ưu tiên Cao trở lên. "
                 "Nháy đúp vào một việc để sửa.",
            font=Theme.FONT_SMALL,
            fg=Theme.TEXT_MUTED,
            bg=Theme.BG
        ).pack(anchor="w")

        grid_container = tk.Frame(self, bg=Theme.BG)
        grid_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))
        for index in range(2):
            grid_container.grid_rowconfigure(index, weight=1, uniform="rows")
            grid_container.grid_columnconfigure(index, weight=1, uniform="cols")

        for key, title, subtitle, color, row, col in QUADRANTS:
            self.quadrants[key] = self._create_quadrant(grid_container, title, subtitle, color, row, col)

    def _create_quadrant(self, parent, title: str, subtitle: str, color: str, row: int, col: int) -> dict:
        container = tk.Frame(parent, bg=Theme.SURFACE, highlightthickness=1, highlightbackground=Theme.BORDER)
        container.grid(row=row, column=col, sticky="nsew", padx=6, pady=6)

        tk.Frame(container, bg=color, height=4).pack(fill=tk.X)

        head = tk.Frame(container, bg=Theme.SURFACE, padx=12, pady=8)
        head.pack(fill=tk.X)
        lbl_count = tk.Label(head, text="0", font=Theme.FONT_HEADER, fg=color, bg=Theme.SURFACE)
        lbl_count.pack(side=tk.RIGHT)
        tk.Label(head, text=title, font=Theme.FONT_SUBHEADER, fg=color, bg=Theme.SURFACE).pack(anchor="w")
        tk.Label(head, text=subtitle, font=Theme.FONT_SMALL, fg=Theme.TEXT_MUTED, bg=Theme.SURFACE).pack(anchor="w")

        list_frame = tk.Frame(container, bg=Theme.SURFACE)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=8, pady=(0, 8))

        listbox = tk.Listbox(
            list_frame,
            font=Theme.FONT_BODY,
            bg=Theme.SURFACE,
            fg=Theme.TEXT,
            selectbackground=Theme.PRIMARY_SOFT,
            selectforeground=Theme.TEXT,
            relief="flat",
            highlightthickness=0,
            activestyle="none",
            height=4
        )
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=listbox.yview)
        listbox.configure(yscrollcommand=scrollbar.set)
        listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        quadrant_info = {"count_label": lbl_count, "listbox": listbox, "tasks": []}

        def _on_double_click(event):
            idx = listbox.curselection()
            if idx and idx[0] < len(quadrant_info["tasks"]) and self.on_task_double_click:
                self.on_task_double_click(quadrant_info["tasks"][idx[0]])

        listbox.bind("<Double-Button-1>", _on_double_click)
        return quadrant_info

    def update_tasks(self, tasks: List[Task]):
        """Cập nhật dữ liệu vào 4 góc phần tư."""
        self.current_tasks = tasks
        now = datetime.now()
        classified = SchedulerEngine.classify_eisenhower(tasks, threshold_hours=24.0, now=now)

        for key, info in self.quadrants.items():
            task_list = sorted(classified[key], key=lambda t: t.start_time)
            info["tasks"] = task_list
            info["count_label"].config(text=str(len(task_list)))
            info["listbox"].delete(0, tk.END)

            for index, t in enumerate(task_list):
                info["listbox"].insert(tk.END, f"{format_datetime(t.start_time)}   {t.title}")
                if t.is_overdue(now):
                    info["listbox"].itemconfig(index, fg=Theme.DANGER)

            if not task_list:
                info["listbox"].insert(tk.END, "Không có việc nào")
                info["listbox"].itemconfig(0, fg=Theme.TEXT_FAINT, selectbackground=Theme.SURFACE, selectforeground=Theme.TEXT_FAINT)
