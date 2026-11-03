"""
ui/eisenhower_view.py
Thành phần hiển thị Ma trận Eisenhower 4 góc phần tư trực quan.
Hỗ trợ phân loại nhiệm vụ tự động dựa trên độ ưu tiên và mức độ khẩn cấp theo mốc thời gian.
"""

import tkinter as tk
from tkinter import ttk
from typing import List, Callable, Optional
from core.models import Task, Priority, Status
from core.scheduler_engine import SchedulerEngine
from ui.theme import Theme


class EisenhowerView(tk.Frame):
    def __init__(self, parent: tk.Widget, on_task_double_click: Optional[Callable[[Task], None]] = None):
        super().__init__(parent, bg=Theme.BG_DARK)
        self.on_task_double_click = on_task_double_click
        self.current_tasks: List[Task] = []
        self._build_ui()

    def _build_ui(self):
        # Header giải thích
        top_bar = tk.Frame(self, bg=Theme.BG_DARK, pady=10)
        top_bar.pack(fill=tk.X, padx=16)

        tk.Label(
            top_bar,
            text="🧭 MA TRẬN QUẢN LÝ THỜI GIAN EISENHOWER",
            font=Theme.FONT_TITLE,
            fg=Theme.PRIMARY,
            bg=Theme.BG_DARK
        ).pack(side=tk.LEFT)

        tk.Label(
            top_bar,
            text="(Phân loại tự động theo Mức độ quan trọng & Thời hạn khẩn cấp)",
            font=Theme.FONT_SMALL,
            fg=Theme.TEXT_MUTED,
            bg=Theme.BG_DARK
        ).pack(side=tk.LEFT, padx=12)

        # Lưới 2x2 cho 4 góc phần tư
        grid_container = tk.Frame(self, bg=Theme.BG_DARK)
        grid_container.pack(fill=tk.BOTH, expand=True, padx=16, pady=(0, 16))

        grid_container.grid_rowconfigure(0, weight=1)
        grid_container.grid_rowconfigure(1, weight=1)
        grid_container.grid_columnconfigure(0, weight=1)
        grid_container.grid_columnconfigure(1, weight=1)

        # Q1: Khẩn cấp & Quan trọng (Làm ngay)
        self.frame_q1 = self._create_quadrant(
            grid_container,
            title="Q1: KHẨN CẤP & QUAN TRỌNG (DO FIRST)",
            subtitle="Hành động ngay lập tức - Ưu tiên hàng đầu",
            header_color=Theme.DANGER,
            row=0, col=0
        )

        # Q2: Quan trọng & Không khẩn cấp (Lên kế hoạch)
        self.frame_q2 = self._create_quadrant(
            grid_container,
            title="Q2: QUAN TRỌNG & KHÔNG KHẨN CẤP (SCHEDULE)",
            subtitle="Phát triển dài hạn - Lên kế hoạch thực hiện",
            header_color=Theme.PRIMARY,
            row=0, col=1
        )

        # Q3: Khẩn cấp & Ít quan trọng (Ủy quyền / Giảm thiểu)
        self.frame_q3 = self._create_quadrant(
            grid_container,
            title="Q3: KHẨN CẤP & ÍT QUAN TRỌNG (DELEGATE)",
            subtitle="Việc gấp phát sinh - Xử lý nhanh hoặc ủy quyền",
            header_color=Theme.WARNING,
            row=1, col=0
        )

        # Q4: Không khẩn cấp & Không quan trọng (Loại bỏ / Thư giãn)
        self.frame_q4 = self._create_quadrant(
            grid_container,
            title="Q4: KHÔNG KHẨN CẤP & KHÔNG QUAN TRỌNG (ELIMINATE)",
            subtitle="Giải trí, việc nhỏ - Thực hiện khi rảnh rỗi",
            header_color="#64748B",
            row=1, col=1
        )

    def _create_quadrant(self, parent, title: str, subtitle: str, header_color: str, row: int, col: int) -> dict:
        container = tk.Frame(parent, bg=Theme.BG_CARD, highlightthickness=1, highlightbackground=Theme.BORDER)
        container.grid(row=row, column=col, sticky="nsew", padx=6, pady=6)

        # Banner Header
        banner = tk.Frame(container, bg=header_color, pady=6, padx=10)
        banner.pack(fill=tk.X)

        lbl_t = tk.Label(banner, text=title, font=Theme.FONT_SUBHEADER, fg="white", bg=header_color)
        lbl_t.pack(side=tk.LEFT)

        lbl_count = tk.Label(banner, text="0", font=Theme.FONT_SMALL, fg="white", bg=header_color, padx=6)
        lbl_count.pack(side=tk.RIGHT)

        sub_lbl = tk.Label(container, text=subtitle, font=Theme.FONT_SMALL, fg=Theme.TEXT_MUTED, bg=Theme.BG_CARD, pady=4)
        sub_lbl.pack(anchor="w", padx=10)

        # Listbox / Canvas hiển thị các task
        list_frame = tk.Frame(container, bg=Theme.BG_CARD)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=8, pady=(0, 8))

        listbox = tk.Listbox(
            list_frame,
            font=Theme.FONT_BODY,
            bg=Theme.BG_INPUT,
            fg=Theme.TEXT_MAIN,
            selectbackground=Theme.PRIMARY,
            selectforeground="white",
            relief="flat",
            highlightthickness=0
        )
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=listbox.yview)
        listbox.configure(yscrollcommand=scrollbar.set)

        listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        def _on_double_click(event):
            idx = listbox.curselection()
            if idx:
                task_obj = quadrant_info["tasks"][idx[0]]
                if self.on_task_double_click:
                    self.on_task_double_click(task_obj)

        listbox.bind("<Double-Button-1>", _on_double_click)

        quadrant_info = {
            "container": container,
            "count_label": lbl_count,
            "listbox": listbox,
            "tasks": []
        }
        return quadrant_info

    def update_tasks(self, tasks: List[Task]):
        """Cập nhật dữ liệu vào 4 góc phần tư."""
        self.current_tasks = tasks
        quadrants = SchedulerEngine.classify_eisenhower(tasks, threshold_hours=24.0)

        mapping = [
            ("Q1", self.frame_q1),
            ("Q2", self.frame_q2),
            ("Q3", self.frame_q3),
            ("Q4", self.frame_q4)
        ]

        for q_key, q_dict in mapping:
            task_list = quadrants[q_key]
            q_dict["tasks"] = task_list
            q_dict["count_label"].config(text=f"{len(task_list)} việc")
            q_dict["listbox"].delete(0, tk.END)

            for t in task_list:
                item_str = f"• [{t.start_time.strftime('%d/%m %H:%M')}] {t.title} ({t.category})"
                q_dict["listbox"].insert(tk.END, item_str)
