"""
ui/smart_slot_dialog.py
Hộp thoại tìm khung giờ rảnh (Smart Free Slot Finder).
Kết quả cập nhật ngay khi đổi điều kiện, dòng được chọn sẵn là khe theo chiến lược người dùng chọn.
"""

import tkinter as tk
from tkinter import ttk
from datetime import datetime, timedelta
from typing import List, Callable, Optional
from core.models import Task
from core.scheduler_engine import SchedulerEngine
from ui.theme import Theme
from ui.widgets import DatePicker, make_button, make_modal, next_round_time, format_duration, set_button_enabled

DURATION_VALUES = ["15", "30", "45", "60", "90", "120", "180"]
STRATEGIES = [
    ("earliest", "Sớm nhất có thể"),
    ("best_fit", "Vừa khít nhất (giữ lại các khoảng trống dài)")
]


class SmartSlotDialog(tk.Toplevel):
    def __init__(
        self,
        parent: tk.Tk,
        all_tasks: List[Task],
        on_slot_selected: Optional[Callable[[datetime, datetime, int], None]] = None
    ):
        super().__init__(parent)
        self.parent = parent
        self.all_tasks = all_tasks
        self.on_slot_selected = on_slot_selected
        self.found_slots = []
        self.duration = 60

        self.title("Tìm giờ rảnh")
        self.resizable(False, False)
        self.configure(bg=Theme.SURFACE)

        self._build_ui()
        make_modal(self, parent)

    def _build_ui(self):
        container = tk.Frame(self, bg=Theme.SURFACE, padx=22, pady=18)
        container.pack(fill=tk.BOTH, expand=True)

        tk.Label(container, text="Tìm giờ rảnh", font=Theme.FONT_TITLE, fg=Theme.TEXT, bg=Theme.SURFACE).pack(anchor="w")
        tk.Label(
            container,
            text="Cho biết ngày và thời lượng cần, chương trình sẽ tìm các khoảng còn trống.",
            font=Theme.FONT_SMALL,
            fg=Theme.TEXT_MUTED,
            bg=Theme.SURFACE
        ).pack(anchor="w", pady=(2, 12))

        params = tk.Frame(container, bg=Theme.SURFACE)
        params.pack(fill=tk.X)

        self._param_label(params, "Ngày", 0)
        self.date_picker = DatePicker(params, datetime.now().date(), self._find_slots)
        self.date_picker.grid(row=0, column=1, sticky="w", pady=3)

        self._param_label(params, "Thời lượng", 1)
        dur_row = tk.Frame(params, bg=Theme.SURFACE)
        dur_row.grid(row=1, column=1, sticky="w", pady=3)
        self.cb_duration = ttk.Combobox(dur_row, values=DURATION_VALUES, width=6, font=Theme.FONT_BODY)
        self.cb_duration.set("60")
        self.cb_duration.pack(side=tk.LEFT)
        tk.Label(dur_row, text="phút", font=Theme.FONT_BODY, fg=Theme.TEXT, bg=Theme.SURFACE).pack(side=tk.LEFT, padx=6)
        self.cb_duration.bind("<<ComboboxSelected>>", lambda e: self._find_slots())
        self.cb_duration.bind("<KeyRelease>", lambda e: self._find_slots())

        self._param_label(params, "Trong khung", 2)
        hour_row = tk.Frame(params, bg=Theme.SURFACE)
        hour_row.grid(row=2, column=1, sticky="w", pady=3)
        self.sp_start_hr = ttk.Spinbox(hour_row, from_=0, to=23, width=4, font=Theme.FONT_BODY, command=self._find_slots)
        self.sp_start_hr.set(8)
        self.sp_start_hr.pack(side=tk.LEFT)
        tk.Label(hour_row, text="giờ  đến", font=Theme.FONT_BODY, fg=Theme.TEXT, bg=Theme.SURFACE).pack(side=tk.LEFT, padx=6)
        self.sp_end_hr = ttk.Spinbox(hour_row, from_=1, to=24, width=4, font=Theme.FONT_BODY, command=self._find_slots)
        self.sp_end_hr.set(21)
        self.sp_end_hr.pack(side=tk.LEFT)
        tk.Label(hour_row, text="giờ", font=Theme.FONT_BODY, fg=Theme.TEXT, bg=Theme.SURFACE).pack(side=tk.LEFT, padx=6)
        for spin in (self.sp_start_hr, self.sp_end_hr):
            spin.bind("<KeyRelease>", lambda e: self._find_slots())

        self._param_label(params, "Ưu tiên chọn", 3)
        strat_col = tk.Frame(params, bg=Theme.SURFACE)
        strat_col.grid(row=3, column=1, sticky="w", pady=3)
        self.var_strategy = tk.StringVar(value="earliest")
        for value, text in STRATEGIES:
            ttk.Radiobutton(strat_col, text=text, value=value, variable=self.var_strategy, command=self._find_slots).pack(anchor="w")

        self.lbl_result = tk.Label(container, font=Theme.FONT_SUBHEADER, fg=Theme.TEXT, bg=Theme.SURFACE, anchor="w", wraplength=480, justify="left")
        self.lbl_result.pack(fill=tk.X, pady=(14, 4))

        tree_frame = tk.Frame(container, bg=Theme.SURFACE, highlightthickness=1, highlightbackground=Theme.BORDER)
        tree_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 12))

        cols = ("start", "end", "duration", "note")
        self.tree = ttk.Treeview(tree_frame, columns=cols, show="headings", height=5, selectmode="browse")
        for col, text, width, anchor in (
            ("start", "Từ", 70, "center"),
            ("end", "Đến", 70, "center"),
            ("duration", "Còn trống", 120, "center"),
            ("note", "Nhận xét", 220, "w")
        ):
            self.tree.heading(col, text=text)
            self.tree.column(col, width=width, anchor=anchor)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.tree.bind("<<TreeviewSelect>>", lambda e: self._update_apply_button())
        self.tree.bind("<Double-Button-1>", lambda e: self._apply_slot())

        b_bar = tk.Frame(container, bg=Theme.SURFACE)
        b_bar.pack(fill=tk.X)
        self.btn_apply = make_button(b_bar, "Tạo công việc vào giờ này", self._apply_slot, "primary", font=Theme.FONT_SUBHEADER, padx=16)
        self.btn_apply.pack(side=tk.RIGHT)
        make_button(b_bar, "Đóng", self.destroy, padx=14).pack(side=tk.RIGHT, padx=(0, 8))

        self._find_slots()

    def _param_label(self, parent, text: str, row: int) -> None:
        tk.Label(parent, text=text, font=Theme.FONT_SUBHEADER, fg=Theme.TEXT, bg=Theme.SURFACE, width=12, anchor="nw").grid(row=row, column=0, sticky="nw", pady=5)

    def _update_apply_button(self) -> None:
        set_button_enabled(self.btn_apply, bool(self.tree.selection()))

    def _show_message(self, text: str, color: str = Theme.DANGER) -> None:
        self.tree.delete(*self.tree.get_children())
        self.found_slots = []
        self.lbl_result.configure(text=text, fg=color)
        self._update_apply_button()

    def _find_slots(self) -> None:
        try:
            duration = int(self.cb_duration.get().strip())
            if duration <= 0:
                raise ValueError()
        except ValueError:
            self._show_message("Thời lượng phải là số phút lớn hơn 0.")
            return

        try:
            start_hour, end_hour = int(self.sp_start_hr.get()), int(self.sp_end_hr.get())
            if not (0 <= start_hour < end_hour <= 24):
                raise ValueError()
        except ValueError:
            self._show_message("Giờ bắt đầu phải nhỏ hơn giờ kết thúc, trong khoảng từ 0 đến 24.")
            return

        day = self.date_picker.get()
        target = datetime(day.year, day.month, day.day)
        now = datetime.now()
        # Với ngày hôm nay, phần thời gian đã qua không còn dùng được
        not_before = next_round_time(now) if day == now.date() else None

        slots = SchedulerEngine.find_free_slots(
            self.all_tasks,
            target_date=target,
            day_start_hour=start_hour,
            day_end_hour=end_hour,
            min_duration_minutes=duration,
            not_before=not_before
        )

        self.duration = duration
        self.tree.delete(*self.tree.get_children())
        self.found_slots = slots
        if not slots:
            self._show_message(f"Không còn khoảng trống nào đủ {format_duration(duration)} trong khung giờ này.", Theme.WARNING)
            return

        strategy = self.var_strategy.get()
        recommended = SchedulerEngine.pick_slot(slots, duration, strategy)
        for idx, slot in enumerate(slots):
            leftover = slot.duration_minutes - duration
            if slot is recommended:
                note = "Nên chọn"
            elif leftover == 0:
                note = "Vừa khít"
            else:
                note = f"Còn dư {format_duration(leftover)}"
            self.tree.insert("", "end", iid=str(idx), values=(
                slot.start_time.strftime("%H:%M"),
                slot.end_time.strftime("%H:%M"),
                format_duration(slot.duration_minutes),
                note
            ))

        self.tree.selection_set(str(slots.index(recommended)))
        self.lbl_result.configure(
            text=f"Tìm thấy {len(slots)} khoảng trống. Nên chọn {recommended.start_time.strftime('%H:%M')}.",
            fg=Theme.SUCCESS
        )
        self._update_apply_button()

    def _apply_slot(self) -> None:
        selected = self.tree.selection()
        if not selected:
            return
        slot = self.found_slots[int(selected[0])]
        slot_end = slot.start_time + timedelta(minutes=self.duration)
        self.destroy()
        if self.on_slot_selected:
            self.on_slot_selected(slot.start_time, slot_end, self.duration)
