"""
ui/calendar_view.py
Lịch tuần dạng lưới thời gian vẽ bằng Canvas. Các việc trùng giờ được xếp cạnh nhau theo
thuật toán phân làn (Interval Partitioning) và viền đỏ để dễ nhận ra.
"""

import tkinter as tk
import tkinter.font as tkfont
from tkinter import ttk
from datetime import datetime, date, timedelta
from typing import Callable, List, Optional, Tuple

from core.models import Task, Priority, Status, Category
from core.scheduler_engine import SchedulerEngine
from ui.theme import Theme
from ui.widgets import WEEKDAY_FULL, WEEKDAY_SHORT, Tooltip, format_duration, make_button

HOUR_HEIGHT = 46
GUTTER_WIDTH = 54
HEADER_HEIGHT = 46
DEFAULT_SCROLL_HOUR = 7


class WeekCalendarView(tk.Frame):
    def __init__(
        self,
        parent: tk.Widget,
        on_edit: Optional[Callable[[Task], None]] = None,
        on_add: Optional[Callable[[datetime], None]] = None
    ):
        super().__init__(parent, bg=Theme.SURFACE)
        self.on_edit = on_edit
        self.on_add = on_add
        self.tasks: List[Task] = []
        self.week_start = self._monday_of(date.today())
        self.font_title = tkfont.Font(font=Theme.FONT_SMALL)
        self.font_time = tkfont.Font(family="Segoe UI", size=8)
        self.tooltip = Tooltip(self)
        self._scroll_pending = True
        self._build_ui()

    @staticmethod
    def _monday_of(day: date) -> date:
        return day - timedelta(days=day.weekday())

    def _build_ui(self):
        toolbar = tk.Frame(self, bg=Theme.SURFACE, padx=12, pady=10)
        toolbar.pack(fill=tk.X)

        make_button(toolbar, "‹", lambda: self.shift_week(-1), font=Theme.FONT_SUBHEADER, pady=3).pack(side=tk.LEFT)
        make_button(toolbar, "Hôm nay", self.go_today, pady=4).pack(side=tk.LEFT, padx=4)
        make_button(toolbar, "›", lambda: self.shift_week(1), font=Theme.FONT_SUBHEADER, pady=3).pack(side=tk.LEFT)

        self.lbl_range = tk.Label(toolbar, font=Theme.FONT_HEADER, bg=Theme.SURFACE, fg=Theme.TEXT)
        self.lbl_range.pack(side=tk.LEFT, padx=14)

        tk.Label(
            toolbar,
            text="Bấm vào công việc để sửa  ·  Nháy đúp vào ô trống để thêm việc",
            font=Theme.FONT_SMALL,
            bg=Theme.SURFACE,
            fg=Theme.TEXT_MUTED
        ).pack(side=tk.RIGHT)

        grid = tk.Frame(self, bg=Theme.SURFACE)
        grid.pack(fill=tk.BOTH, expand=True)
        grid.rowconfigure(1, weight=1)
        grid.columnconfigure(0, weight=1)

        self.header = tk.Canvas(grid, height=HEADER_HEIGHT, bg=Theme.SURFACE, highlightthickness=0)
        self.header.grid(row=0, column=0, sticky="ew")

        self.body = tk.Canvas(grid, bg=Theme.SURFACE, highlightthickness=0, scrollregion=(0, 0, 0, 24 * HOUR_HEIGHT))
        self.body.grid(row=1, column=0, sticky="nsew")

        scrollbar = ttk.Scrollbar(grid, orient=tk.VERTICAL, command=self.body.yview)
        scrollbar.grid(row=1, column=1, sticky="ns")
        self.body.configure(yscrollcommand=scrollbar.set)

        self.body.bind("<Configure>", lambda e: self.redraw())
        self.body.bind("<Double-Button-1>", self._on_double_click)
        self.body.bind("<MouseWheel>", lambda e: self.body.yview_scroll(-1 if e.delta > 0 else 1, "units"))
        self.body.configure(yscrollincrement=HOUR_HEIGHT // 2)

    def update_tasks(self, tasks: List[Task]) -> None:
        self.tasks = tasks
        self.redraw()

    def shift_week(self, weeks: int) -> None:
        self.week_start += timedelta(days=7 * weeks)
        self._scroll_pending = True
        self.redraw()

    def go_today(self) -> None:
        self.week_start = self._monday_of(date.today())
        self._scroll_pending = True
        self.redraw()

    def _column_width(self) -> float:
        return max(1, self.body.winfo_width() - GUTTER_WIDTH) / 7

    def redraw(self) -> None:
        self.tooltip.hide()
        if self.body.winfo_width() <= 1:
            return

        week_end = self.week_start + timedelta(days=6)
        self.lbl_range.configure(text=f"{self.week_start.strftime('%d/%m')} – {week_end.strftime('%d/%m/%Y')}")
        self._draw_header()
        self._draw_grid()
        self._draw_tasks()
        self._draw_now_line()
        if self._scroll_pending:
            self._scroll_to_first_task()
            self._scroll_pending = False

    def _draw_header(self) -> None:
        self.header.delete("all")
        col_w = self._column_width()
        today = date.today()
        for i in range(7):
            day = self.week_start + timedelta(days=i)
            cx = GUTTER_WIDTH + col_w * i + col_w / 2
            is_today = day == today
            if is_today:
                self.header.create_oval(cx - 13, 21, cx + 13, 45, fill=Theme.PRIMARY, outline="")
            self.header.create_text(cx, 11, text=WEEKDAY_SHORT[i], font=Theme.FONT_SMALL, fill=Theme.PRIMARY if is_today else Theme.TEXT_MUTED)
            self.header.create_text(cx, 33, text=str(day.day), font=Theme.FONT_SUBHEADER, fill="white" if is_today else Theme.TEXT)
        self.header.create_line(0, HEADER_HEIGHT - 1, self.header.winfo_width(), HEADER_HEIGHT - 1, fill=Theme.BORDER)

    def _draw_grid(self) -> None:
        self.body.delete("all")
        width = self.body.winfo_width()
        total_h = 24 * HOUR_HEIGHT
        col_w = self._column_width()

        today_offset = (date.today() - self.week_start).days
        if 0 <= today_offset < 7:
            x0 = GUTTER_WIDTH + col_w * today_offset
            self.body.create_rectangle(x0, 0, x0 + col_w, total_h, fill=Theme.TODAY, outline="", tags="cell")

        for hour in range(24):
            y = hour * HOUR_HEIGHT
            self.body.create_line(GUTTER_WIDTH, y, width, y, fill=Theme.GRID_LINE, tags="cell")
            if hour:
                self.body.create_text(GUTTER_WIDTH - 8, y + 2, text=f"{hour:02d}:00", anchor="ne", font=self.font_time, fill=Theme.TEXT_MUTED)

        for i in range(8):
            x = GUTTER_WIDTH + col_w * i
            self.body.create_line(x, 0, x, total_h, fill=Theme.GRID_LINE, tags="cell")

    def _segments_of_day(self, day: date) -> List[Tuple[Task, datetime, datetime]]:
        """Phần giao của từng công việc với một ngày; việc kéo dài qua đêm được vẽ ở cả hai ngày."""
        day_start = datetime(day.year, day.month, day.day)
        day_end = day_start + timedelta(days=1)
        return [
            (t, max(t.start_time, day_start), min(t.end_time, day_end))
            for t in self.tasks
            if t.start_time < day_end and t.end_time > day_start
        ]

    def _draw_tasks(self) -> None:
        conflict_ids = set()
        for conflict in SchedulerEngine.detect_all_conflicts(self.tasks):
            conflict_ids.update((conflict.task1.id, conflict.task2.id))

        col_w = self._column_width()
        for i in range(7):
            day = self.week_start + timedelta(days=i)
            segments = self._segments_of_day(day)
            lanes = SchedulerEngine.assign_overlap_lanes([s[0] for s in segments])
            midnight = datetime(day.year, day.month, day.day)
            for task, seg_start, seg_end in segments:
                lane, lane_count = lanes[task.id]
                lane_w = (col_w - 6) / lane_count
                x0 = GUTTER_WIDTH + col_w * i + 2 + lane * lane_w
                y0 = (seg_start - midnight).total_seconds() / 3600 * HOUR_HEIGHT + 1
                y1 = (seg_end - midnight).total_seconds() / 3600 * HOUR_HEIGHT - 1
                self._draw_task_block(task, x0, y0, x0 + lane_w - 1, max(y1, y0 + 16), task.id in conflict_ids)

    def _draw_task_block(self, task: Task, x0: float, y0: float, x1: float, y1: float, in_conflict: bool) -> None:
        color = Category.from_string(task.category).color
        inactive = not task.is_active
        if inactive:
            color = Theme.TEXT_FAINT
        fill = Theme.mix_with_white(color, 0.9 if inactive else 0.82)
        text_color = Theme.TEXT_MUTED if inactive else Theme.TEXT
        tag = f"task_{task.id}"

        self.body.create_rectangle(
            x0, y0, x1, y1,
            fill=fill,
            outline=Theme.DANGER if in_conflict else fill,
            width=2 if in_conflict else 1,
            tags=(tag,)
        )
        self.body.create_rectangle(x0, y0, x0 + 4, y1, fill=color, outline="", tags=(tag,))

        prefix = {Status.COMPLETED: "✓ ", Status.CANCELLED: "✕ "}.get(task.status, "")
        if task.priority == Priority.URGENT and not inactive:
            prefix = "! "
        inner_w = max(10, x1 - x0 - 10)
        line_h = self.font_title.metrics("linespace")
        max_lines = max(1, int((y1 - y0 - 4) // line_h))
        has_time_line = max_lines >= 2

        lines = self._wrap_text(prefix + task.title, inner_w, max_lines - 1 if has_time_line else 1)
        y = y0 + 2
        for line in lines:
            self.body.create_text(x0 + 8, y, text=line, anchor="nw", font=self.font_title, fill=text_color, tags=(tag,))
            y += line_h
        if has_time_line:
            time_text = f"{task.start_time.strftime('%H:%M')}–{task.end_time.strftime('%H:%M')}"
            if self.font_time.measure(time_text) <= inner_w:
                self.body.create_text(x0 + 8, y, text=time_text, anchor="nw", font=self.font_time, fill=Theme.TEXT_MUTED, tags=(tag,))

        self.body.tag_bind(tag, "<Button-1>", lambda e, t=task: self._open_task(t))
        self.body.tag_bind(tag, "<Enter>", lambda e, t=task, c=in_conflict: self._on_task_enter(e, t, c))
        self.body.tag_bind(tag, "<Leave>", lambda e: self._on_task_leave())

    def _wrap_text(self, text: str, width: float, max_lines: int) -> List[str]:
        """Ngắt dòng theo từ cho vừa chiều rộng, thêm dấu … nếu vượt quá số dòng cho phép."""
        lines: List[str] = []
        current = ""
        words = text.split()
        for index, word in enumerate(words):
            candidate = f"{current} {word}".strip()
            if self.font_title.measure(candidate) <= width:
                current = candidate
                continue
            if current:
                lines.append(current)
            current = word
            if len(lines) == max_lines:
                current = " ".join([lines.pop()] + words[index:])
                break
        lines.append(current)

        truncated = len(lines) > max_lines or self.font_title.measure(lines[-1]) > width
        lines = lines[:max_lines]
        if truncated:
            last = lines[-1]
            while last and self.font_title.measure(last + "…") > width:
                last = last[:-1]
            lines[-1] = last.rstrip() + "…"
        return lines

    def _draw_now_line(self) -> None:
        now = datetime.now()
        offset = (now.date() - self.week_start).days
        if not 0 <= offset < 7:
            return
        col_w = self._column_width()
        x0 = GUTTER_WIDTH + col_w * offset
        y = (now.hour + now.minute / 60) * HOUR_HEIGHT
        self.body.create_line(x0, y, x0 + col_w, y, fill=Theme.DANGER, width=2)
        self.body.create_oval(x0 - 4, y - 4, x0 + 4, y + 4, fill=Theme.DANGER, outline="")

    def _scroll_to_first_task(self) -> None:
        week_starts = [
            t.start_time.hour for t in self.tasks
            if self.week_start <= t.start_time.date() < self.week_start + timedelta(days=7)
        ]
        hour = max(0, min(week_starts) - 1) if week_starts else DEFAULT_SCROLL_HOUR
        self.body.yview_moveto(min(hour, DEFAULT_SCROLL_HOUR) / 24)

    def _open_task(self, task: Task) -> None:
        self._on_task_leave()
        if self.on_edit:
            self.on_edit(task)

    def _on_task_enter(self, event, task: Task, in_conflict: bool) -> None:
        self.body.configure(cursor="hand2")
        lines = [
            task.title,
            f"{WEEKDAY_FULL[task.start_time.weekday()]} {task.start_time.strftime('%d/%m')}, "
            f"{task.start_time.strftime('%H:%M')}–{task.end_time.strftime('%H:%M')} ({format_duration(task.duration_minutes)})",
            f"{task.category} · Ưu tiên {task.priority.label} · {task.status.label}"
        ]
        if in_conflict:
            lines.append("Đang trùng giờ với việc khác")
        self.tooltip.show("\n".join(lines), event.x_root, event.y_root)

    def _on_task_leave(self) -> None:
        self.body.configure(cursor="")
        self.tooltip.hide()

    def _on_double_click(self, event) -> None:
        if not self.on_add or event.x < GUTTER_WIDTH:
            return
        x, y = self.body.canvasx(event.x), self.body.canvasy(event.y)
        for item in self.body.find_overlapping(x, y, x, y):
            if any(tag.startswith("task_") for tag in self.body.gettags(item)):
                return

        day_index = min(6, int((x - GUTTER_WIDTH) // self._column_width()))
        minutes = int(y / HOUR_HEIGHT * 60) // 30 * 30
        day = self.week_start + timedelta(days=day_index)
        self.on_add(datetime(day.year, day.month, day.day) + timedelta(minutes=min(minutes, 23 * 60 + 30)))
