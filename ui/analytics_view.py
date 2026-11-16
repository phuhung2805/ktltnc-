"""
ui/analytics_view.py
Bảng điều khiển trực quan hóa dữ liệu lịch trình (Analytics & Dashboard).
Vẽ trực tiếp biểu đồ tròn (Donut Chart) và biểu đồ cột (Bar Chart) bằng Tkinter Canvas
giúp chương trình chạy độc lập, siêu nhẹ và không phụ thuộc thư viện ngoài.
"""

import tkinter as tk
from typing import List
from collections import Counter
from datetime import datetime
from core.models import Task, Priority, Status, Category
from core.scheduler_engine import SchedulerEngine
from ui.theme import Theme


class AnalyticsView(tk.Frame):
    def __init__(self, parent: tk.Widget):
        super().__init__(parent, bg=Theme.BG)
        self.current_tasks: List[Task] = []
        self._build_ui()

    def _build_ui(self):
        container = tk.Frame(self, bg=Theme.BG, padx=16, pady=12)
        container.pack(fill=tk.BOTH, expand=True)

        tk.Label(container, text="Tình hình công việc", font=Theme.FONT_HEADER, fg=Theme.TEXT, bg=Theme.BG).pack(anchor="w", pady=(0, 10))

        # 4 Thẻ chỉ số tổng quan (KPI Metric Cards)
        kpi_frame = tk.Frame(container, bg=Theme.BG)
        kpi_frame.pack(fill=tk.X, pady=(0, 12))
        for i in range(4):
            kpi_frame.columnconfigure(i, weight=1, uniform="kpi")

        self.card_completed = self._create_kpi_card(kpi_frame, "Đã hoàn thành", Theme.SUCCESS, 0)
        self.card_pending = self._create_kpi_card(kpi_frame, "Còn phải làm", Theme.PRIMARY, 1)
        self.card_overdue = self._create_kpi_card(kpi_frame, "Quá hạn", Theme.DANGER, 2)
        self.card_conflicts = self._create_kpi_card(kpi_frame, "Cặp việc trùng giờ", Theme.WARNING, 3)

        # Khu vực biểu đồ (2 cột Canvas)
        charts_frame = tk.Frame(container, bg=Theme.BG)
        charts_frame.pack(fill=tk.BOTH, expand=True)
        charts_frame.rowconfigure(0, weight=1)
        charts_frame.columnconfigure(0, weight=1, uniform="charts")
        charts_frame.columnconfigure(1, weight=1, uniform="charts")

        self.canvas_donut = self._create_chart_box(charts_frame, "Theo danh mục", 0)
        self.canvas_bars = self._create_chart_box(charts_frame, "Theo mức ưu tiên", 1)

        # Biểu đồ vẽ theo kích thước thật, nên phải vẽ lại khi Canvas được bố trí hoặc đổi cỡ
        self.canvas_donut.bind("<Configure>", lambda e: self._draw_donut_chart(self.current_tasks))
        self.canvas_bars.bind("<Configure>", lambda e: self._draw_priority_bars(self.current_tasks))

    def _create_chart_box(self, parent, title: str, col: int) -> tk.Canvas:
        box = tk.Frame(parent, bg=Theme.SURFACE, highlightthickness=1, highlightbackground=Theme.BORDER, padx=14, pady=12)
        box.grid(row=0, column=col, sticky="nsew", padx=6)
        tk.Label(box, text=title, font=Theme.FONT_SUBHEADER, fg=Theme.TEXT, bg=Theme.SURFACE).pack(anchor="w")
        canvas = tk.Canvas(box, bg=Theme.SURFACE, highlightthickness=0, height=240)
        canvas.pack(fill=tk.BOTH, expand=True, pady=(6, 0))
        return canvas

    def _create_kpi_card(self, parent, title: str, color: str, col: int) -> dict:
        card = tk.Frame(parent, bg=Theme.SURFACE, highlightthickness=1, highlightbackground=Theme.BORDER, padx=14, pady=10)
        card.grid(row=0, column=col, sticky="nsew", padx=6)

        tk.Label(card, text=title, font=Theme.FONT_SMALL, fg=Theme.TEXT_MUTED, bg=Theme.SURFACE).pack(anchor="w")
        lbl_v = tk.Label(card, text="0", font=Theme.FONT_KPI, fg=color, bg=Theme.SURFACE)
        lbl_v.pack(anchor="w", pady=(2, 0))
        return {"card": card, "val_lbl": lbl_v}

    def update_tasks(self, tasks: List[Task]):
        self.current_tasks = tasks
        now = datetime.now()
        # Việc đã hủy không tính vào tỷ lệ hoàn thành
        counted = [t for t in tasks if t.status != Status.CANCELLED]
        completed = sum(1 for t in counted if t.status == Status.COMPLETED)
        rate = round(completed / len(counted) * 100) if counted else 0

        self.card_completed["val_lbl"].config(text=f"{completed}/{len(counted)} ({rate}%)")
        self.card_pending["val_lbl"].config(text=str(len(counted) - completed))
        self.card_overdue["val_lbl"].config(text=str(sum(1 for t in counted if t.is_overdue(now))))
        self.card_conflicts["val_lbl"].config(text=str(len(SchedulerEngine.detect_all_conflicts(tasks))))

        self._draw_donut_chart(tasks)
        self._draw_priority_bars(tasks)

    def _draw_empty(self, canvas: tk.Canvas, w: int, h: int) -> None:
        canvas.create_text(w // 2, h // 2, text="Chưa có dữ liệu", fill=Theme.TEXT_FAINT, font=Theme.FONT_BODY)

    def _draw_donut_chart(self, tasks: List[Task]):
        canvas = self.canvas_donut
        canvas.delete("all")
        w, h = canvas.winfo_width(), canvas.winfo_height()
        if w <= 1 or h <= 1:
            return
        if not tasks:
            self._draw_empty(canvas, w, h)
            return

        cat_counts = Counter(t.category for t in tasks)
        total = len(tasks)

        radius = min(95, (h - 20) // 2, (w - 190) // 2)
        radius = max(radius, 40)
        inner_radius = int(radius * 0.58)
        cx, cy = radius + 10, h // 2

        start_angle = 90.0
        lx = cx + radius + 28
        legend_y = cy - len(cat_counts) * 13

        for cat, count in cat_counts.most_common():
            extent = (count / total) * 360.0
            color = Category.from_string(cat).color

            # Canvas không vẽ được cung đúng 360 độ nên giới hạn ngay dưới mức đó
            canvas.create_arc(
                cx - radius, cy - radius, cx + radius, cy + radius,
                start=start_angle, extent=-min(extent, 359.9), fill=color, outline=Theme.SURFACE, width=2
            )

            canvas.create_rectangle(lx, legend_y + 3, lx + 12, legend_y + 15, fill=color, outline="")
            percent = round(count / total * 100)
            canvas.create_text(
                lx + 20, legend_y + 9,
                text=f"{cat}: {count} ({percent}%)",
                fill=Theme.TEXT, font=Theme.FONT_SMALL, anchor="w"
            )
            legend_y += 26
            start_angle -= extent

        # Vẽ hình tròn nhỏ ở giữa để tạo hiệu ứng Donut
        canvas.create_oval(
            cx - inner_radius, cy - inner_radius, cx + inner_radius, cy + inner_radius,
            fill=Theme.SURFACE, outline=""
        )
        canvas.create_text(cx, cy, text=f"{total}\nviệc", fill=Theme.TEXT, font=Theme.FONT_SUBHEADER, justify="center")

    def _draw_priority_bars(self, tasks: List[Task]):
        canvas = self.canvas_bars
        canvas.delete("all")
        w, h = canvas.winfo_width(), canvas.winfo_height()
        if w <= 1 or h <= 1:
            return
        if not tasks:
            self._draw_empty(canvas, w, h)
            return

        prio_counts = Counter(t.priority for t in tasks)
        max_val = max(prio_counts.values())

        priorities = [Priority.URGENT, Priority.HIGH, Priority.MEDIUM, Priority.LOW]
        bar_height = 22
        gap = 22
        start_y = max(4, (h - (bar_height + gap) * len(priorities) + gap) // 2)
        left_pad = 80
        max_bar_width = max(20, w - left_pad - 40)

        for prio in priorities:
            count = prio_counts.get(prio, 0)
            bar_w = (count / max_val) * max_bar_width

            canvas.create_text(
                left_pad - 10, start_y + bar_height // 2,
                text=prio.label, fill=Theme.TEXT, font=Theme.FONT_BODY, anchor="e"
            )
            canvas.create_rectangle(
                left_pad, start_y, left_pad + max_bar_width, start_y + bar_height,
                fill=Theme.SURFACE_ALT, outline=""
            )
            if bar_w > 0:
                canvas.create_rectangle(
                    left_pad, start_y, left_pad + bar_w, start_y + bar_height,
                    fill=prio.color, outline=""
                )
            canvas.create_text(
                left_pad + bar_w + 8, start_y + bar_height // 2,
                text=str(count), fill=Theme.TEXT, font=Theme.FONT_SUBHEADER, anchor="w"
            )
            start_y += bar_height + gap
