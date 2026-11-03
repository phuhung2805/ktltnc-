"""
ui/analytics_view.py
Bảng điều khiển trực quan hóa dữ liệu lịch trình (Analytics & Dashboard).
Vẽ trực tiếp biểu đồ tròn (Donut Chart) và biểu đồ cột (Bar Chart) bằng Tkinter Canvas
giúp chương trình chạy độc lập, siêu nhẹ và không phụ thuộc thư viện ngoài.
"""

import tkinter as tk
from tkinter import ttk
from typing import List, Dict
import math
from collections import Counter
from core.models import Task, Priority, Status, Category
from core.scheduler_engine import SchedulerEngine
from ui.theme import Theme


class AnalyticsView(tk.Frame):
    def __init__(self, parent: tk.Widget):
        super().__init__(parent, bg=Theme.BG_DARK)
        self.current_tasks: List[Task] = []
        self._build_ui()

    def _build_ui(self):
        container = tk.Frame(self, bg=Theme.BG_DARK, padx=20, pady=16)
        container.pack(fill=tk.BOTH, expand=True)

        # Tiêu đề
        tk.Label(
            container,
            text="📊 THỐNG KÊ & PHÂN TÍCH HIỆU SUẤT CÔNG VIỆC",
            font=Theme.FONT_TITLE,
            fg=Theme.PRIMARY,
            bg=Theme.BG_DARK
        ).pack(anchor="w", pady=(0, 14))

        # 4 Thẻ chỉ số tổng quan (KPI Metric Cards)
        kpi_frame = tk.Frame(container, bg=Theme.BG_DARK)
        kpi_frame.pack(fill=tk.X, pady=(0, 16))
        for i in range(4):
            kpi_frame.columnconfigure(i, weight=1)

        self.card_total = self._create_kpi_card(kpi_frame, "TỔNG CÔNG VIỆC", "0", Theme.PRIMARY, 0)
        self.card_completed = self._create_kpi_card(kpi_frame, "HOÀN THÀNH", "0%", Theme.SUCCESS, 1)
        self.card_pending = self._create_kpi_card(kpi_frame, "CHƯA HOÀN THÀNH", "0", Theme.WARNING, 2)
        self.card_conflicts = self._create_kpi_card(kpi_frame, "XUNG ĐỘT LỊCH", "0", Theme.DANGER, 3)

        # Khu vực biểu đồ (2 cột Canvas)
        charts_frame = tk.Frame(container, bg=Theme.BG_DARK)
        charts_frame.pack(fill=tk.BOTH, expand=True)
        charts_frame.columnconfigure(0, weight=1)
        charts_frame.columnconfigure(1, weight=1)

        # Cột trái: Biểu đồ phân bổ theo Danh mục (Donut Chart)
        left_box = tk.Frame(charts_frame, bg=Theme.BG_CARD, highlightthickness=1, highlightbackground=Theme.BORDER, padx=12, pady=12)
        left_box.grid(row=0, column=0, sticky="nsew", padx=(0, 8))

        tk.Label(left_box, text="PHÂN BỔ THEO DANH MỤC", font=Theme.FONT_SUBHEADER, fg=Theme.TEXT_MAIN, bg=Theme.BG_CARD).pack(anchor="w")
        self.canvas_donut = tk.Canvas(left_box, bg=Theme.BG_CARD, highlightthickness=0, height=260)
        self.canvas_donut.pack(fill=tk.BOTH, expand=True, pady=6)

        # Cột phải: Biểu đồ mức độ ưu tiên & tải công việc theo ngày (Bar Chart)
        right_box = tk.Frame(charts_frame, bg=Theme.BG_CARD, highlightthickness=1, highlightbackground=Theme.BORDER, padx=12, pady=12)
        right_box.grid(row=0, column=1, sticky="nsew", padx=(8, 0))

        tk.Label(right_box, text="PHÂN BỔ THEO ĐỘ ƯU TIÊN (PRIORITY)", font=Theme.FONT_SUBHEADER, fg=Theme.TEXT_MAIN, bg=Theme.BG_CARD).pack(anchor="w")
        self.canvas_bars = tk.Canvas(right_box, bg=Theme.BG_CARD, highlightthickness=0, height=260)
        self.canvas_bars.pack(fill=tk.BOTH, expand=True, pady=6)

    def _create_kpi_card(self, parent, title: str, value: str, color: str, col: int) -> dict:
        card = tk.Frame(parent, bg=Theme.BG_CARD, highlightthickness=1, highlightbackground=Theme.BORDER, padx=14, pady=12)
        card.grid(row=0, column=col, sticky="nsew", padx=6)

        lbl_t = tk.Label(card, text=title, font=Theme.FONT_SMALL, fg=Theme.TEXT_MUTED, bg=Theme.BG_CARD)
        lbl_t.pack(anchor="w")

        lbl_v = tk.Label(card, text=value, font=("Segoe UI", 20, "bold"), fg=color, bg=Theme.BG_CARD)
        lbl_v.pack(anchor="w", pady=(4, 0))

        return {"card": card, "val_lbl": lbl_v}

    def update_tasks(self, tasks: List[Task]):
        self.current_tasks = tasks
        total = len(tasks)
        completed = sum(1 for t in tasks if t.status == Status.COMPLETED)
        pending = total - completed
        rate = round((completed / total * 100), 1) if total > 0 else 0.0

        conflicts = SchedulerEngine.detect_all_conflicts(tasks)

        # Cập nhật KPI
        self.card_total["val_lbl"].config(text=str(total))
        self.card_completed["val_lbl"].config(text=f"{rate}% ({completed})")
        self.card_pending["val_lbl"].config(text=str(pending))
        self.card_conflicts["val_lbl"].config(text=f"{len(conflicts)} cặp")

        # Vẽ lại đồ họa
        self._draw_donut_chart(tasks)
        self._draw_priority_bars(tasks)

    def _draw_donut_chart(self, tasks: List[Task]):
        self.canvas_donut.delete("all")
        w = self.canvas_donut.winfo_width() or 340
        h = self.canvas_donut.winfo_height() or 260

        if not tasks:
            self.canvas_donut.create_text(w // 2, h // 2, text="Chưa có dữ liệu", fill=Theme.TEXT_MUTED, font=Theme.FONT_BODY)
            return

        cat_counts = Counter(t.category for t in tasks)
        total = len(tasks)

        # Bảng màu cho từng danh mục
        cat_colors = {
            "Công việc": "#6366F1",
            "Học tập": "#8B5CF6",
            "Cá nhân": "#EC4899",
            "Sức khỏe": "#14B8A6",
            "Họp hành": "#F97316",
            "Khác": "#94A3B8"
        }

        # Tọa độ hình tròn
        cx, cy = 110, h // 2
        radius = 85
        inner_radius = 45

        start_angle = 0.0
        legend_y = 35

        for cat, count in cat_counts.most_common():
            extent = (count / total) * 360.0
            color = cat_colors.get(cat, "#3B82F6")

            # Vẽ cung bánh ngoài
            self.canvas_donut.create_arc(
                cx - radius, cy - radius, cx + radius, cy + radius,
                start=start_angle, extent=extent, fill=color, outline=Theme.BG_CARD, width=2
            )

            # Vẽ chú thích (Legend)
            lx = 220
            self.canvas_donut.create_rectangle(lx, legend_y, lx + 12, legend_y + 12, fill=color, outline="")
            percent = round(count / total * 100, 1)
            self.canvas_donut.create_text(
                lx + 20, legend_y + 6,
                text=f"{cat}: {count} ({percent}%)",
                fill=Theme.TEXT_MAIN, font=Theme.FONT_SMALL, anchor="w"
            )
            legend_y += 24
            start_angle += extent

        # Vẽ hình tròn nhỏ ở giữa để tạo hiệu ứng Donut
        self.canvas_donut.create_oval(
            cx - inner_radius, cy - inner_radius, cx + inner_radius, cy + inner_radius,
            fill=Theme.BG_CARD, outline=""
        )
        self.canvas_donut.create_text(cx, cy, text=f"{total}\nviệc", fill=Theme.TEXT_MAIN, font=Theme.FONT_SUBHEADER, justify="center")

    def _draw_priority_bars(self, tasks: List[Task]):
        self.canvas_bars.delete("all")
        w = self.canvas_bars.winfo_width() or 340
        h = self.canvas_bars.winfo_height() or 260

        if not tasks:
            self.canvas_bars.create_text(w // 2, h // 2, text="Chưa có dữ liệu", fill=Theme.TEXT_MUTED, font=Theme.FONT_BODY)
            return

        prio_counts = Counter(t.priority for t in tasks)
        max_val = max(prio_counts.values()) if prio_counts else 1

        priorities = [Priority.URGENT, Priority.HIGH, Priority.MEDIUM, Priority.LOW]
        bar_height = 24
        start_y = 30
        left_pad = 100
        max_bar_width = w - left_pad - 70

        for prio in priorities:
            count = prio_counts.get(prio, 0)
            bar_w = (count / max_val) * max_bar_width if max_val > 0 else 0

            # Nhãn tên mức ưu tiên
            self.canvas_bars.create_text(
                left_pad - 10, start_y + bar_height // 2,
                text=prio.label, fill=Theme.TEXT_MAIN, font=Theme.FONT_BODY, anchor="e"
            )

            # Vẽ thanh nền xám mờ
            self.canvas_bars.create_rectangle(
                left_pad, start_y, left_pad + max_bar_width, start_y + bar_height,
                fill=Theme.BG_INPUT, outline=""
            )

            # Vẽ thanh dữ liệu màu
            if bar_w > 0:
                self.canvas_bars.create_rectangle(
                    left_pad, start_y, left_pad + bar_w, start_y + bar_height,
                    fill=prio.color, outline=""
                )

            # Số lượng hiển thị bên phải thanh
            self.canvas_bars.create_text(
                left_pad + bar_w + 10, start_y + bar_height // 2,
                text=str(count), fill=Theme.TEXT_MAIN, font=Theme.FONT_SMALL, anchor="w"
            )

            start_y += 48
