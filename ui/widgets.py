"""
ui/widgets.py
Các thành phần giao diện dùng chung: nút bấm, chọn ngày, chọn giờ, gợi ý nổi và định dạng ngày giờ tiếng Việt.
"""

import calendar
import tkinter as tk
from tkinter import ttk
from datetime import datetime, date, timedelta
from typing import Callable, Optional

from ui.theme import Theme

WEEKDAY_SHORT = ["T2", "T3", "T4", "T5", "T6", "T7", "CN"]
WEEKDAY_FULL = ["Thứ Hai", "Thứ Ba", "Thứ Tư", "Thứ Năm", "Thứ Sáu", "Thứ Bảy", "Chủ Nhật"]

BUTTON_KINDS = {
    "primary": (Theme.PRIMARY, "white", Theme.PRIMARY_HOVER),
    "success": (Theme.SUCCESS, "white", Theme.SUCCESS_HOVER),
    "danger": (Theme.DANGER, "white", Theme.DANGER_HOVER),
    "secondary": (Theme.BUTTON, Theme.TEXT, Theme.BUTTON_HOVER),
    "warning": (Theme.WARNING_SOFT, Theme.WARNING, "#FDE68A"),
    "calm": (Theme.SUCCESS_SOFT, Theme.SUCCESS, "#A7F3D0"),
}


def format_datetime(value: datetime) -> str:
    """Ví dụ: T5 05/11 14:30."""
    return f"{WEEKDAY_SHORT[value.weekday()]} {value.strftime('%d/%m %H:%M')}"


def format_duration(minutes: int) -> str:
    """Ví dụ: 45 phút, 2 giờ, 1 giờ 30 phút."""
    hours, rest = divmod(minutes, 60)
    if hours and rest:
        return f"{hours} giờ {rest} phút"
    return f"{hours} giờ" if hours else f"{rest} phút"


def make_button(parent, text: str, command: Callable, kind: str = "secondary", font=None, padx: int = 12, pady: int = 6) -> tk.Button:
    """Tạo nút phẳng có hiệu ứng khi rê chuột."""
    bg, fg, hover = BUTTON_KINDS[kind]
    button = tk.Button(
        parent,
        text=text,
        command=command,
        font=font or Theme.FONT_BODY,
        bg=bg,
        fg=fg,
        activebackground=hover,
        activeforeground=fg,
        disabledforeground=Theme.TEXT_FAINT,
        relief="flat",
        bd=0,
        padx=padx,
        pady=pady,
        cursor="hand2",
        highlightthickness=0
    )
    set_button_kind(button, kind)
    return button


def set_button_kind(button: tk.Button, kind: str) -> None:
    """Đổi màu một nút có sẵn theo loại mới và cập nhật hiệu ứng rê chuột."""
    bg, fg, hover = BUTTON_KINDS[kind]
    button.configure(bg=bg, fg=fg, activebackground=hover, activeforeground=fg)
    button.kind_bg = bg
    button.bind("<Enter>", lambda e: button.configure(bg=hover) if button["state"] != "disabled" else None)
    button.bind("<Leave>", lambda e: button.configure(bg=bg) if button["state"] != "disabled" else None)


def set_button_enabled(button: tk.Button, enabled: bool) -> None:
    """Bật hoặc tắt nút; nút tắt có màu nhạt để không bị nhầm là bấm được."""
    button.configure(
        state="normal" if enabled else "disabled",
        bg=button.kind_bg if enabled else Theme.BUTTON_DISABLED,
        cursor="hand2" if enabled else "arrow"
    )


def make_entry(parent, **kwargs) -> tk.Entry:
    return tk.Entry(
        parent,
        font=Theme.FONT_BODY,
        bg=Theme.SURFACE,
        fg=Theme.TEXT,
        insertbackground=Theme.TEXT,
        relief="flat",
        highlightthickness=1,
        highlightbackground=Theme.BORDER,
        highlightcolor=Theme.PRIMARY,
        **kwargs
    )


def make_modal(window: tk.Toplevel, parent: tk.Misc) -> None:
    """Đưa hộp thoại ra giữa cửa sổ cha và giữ quyền tương tác cho đến khi đóng."""
    window.transient(parent)
    window.update_idletasks()
    x = parent.winfo_rootx() + max(0, (parent.winfo_width() - window.winfo_reqwidth()) // 2)
    y = parent.winfo_rooty() + max(0, (parent.winfo_height() - window.winfo_reqheight()) // 3)
    window.geometry(f"+{x}+{y}")
    window.bind("<Escape>", lambda e: window.destroy())

    def _grab():
        # Một số hệ thống từ chối grab khi cửa sổ chưa hiển thị xong
        try:
            if window.winfo_exists():
                window.grab_set()
        except tk.TclError:
            window.after(50, _grab)

    _grab()


class Tooltip:
    """Khung gợi ý nổi hiển thị cạnh con trỏ chuột."""

    def __init__(self, parent: tk.Misc):
        self.parent = parent
        self.window: Optional[tk.Toplevel] = None

    def show(self, text: str, x_root: int, y_root: int) -> None:
        self.hide()
        self.window = tk.Toplevel(self.parent)
        self.window.overrideredirect(True)
        self.window.attributes("-topmost", True)
        tk.Label(
            self.window,
            text=text,
            font=Theme.FONT_SMALL,
            bg=Theme.TEXT,
            fg="white",
            justify="left",
            padx=10,
            pady=6
        ).pack()
        self.window.update_idletasks()
        # Không để khung gợi ý tràn khỏi màn hình
        x = min(x_root + 14, self.window.winfo_screenwidth() - self.window.winfo_reqwidth() - 8)
        y = min(y_root + 14, self.window.winfo_screenheight() - self.window.winfo_reqheight() - 40)
        self.window.geometry(f"+{x}+{y}")

    def hide(self) -> None:
        if self.window is not None:
            self.window.destroy()
            self.window = None


class DatePopup(tk.Toplevel):
    """Lịch tháng dạng bật lên để chọn ngày; bấm ra ngoài hoặc nhấn Esc để đóng."""

    def __init__(self, parent: tk.Misc, value: date, on_pick: Callable[[date], None], x: int, y: int):
        super().__init__(parent)
        self.overrideredirect(True)
        self.configure(bg=Theme.BORDER, padx=1, pady=1)
        self.on_pick = on_pick
        self.value = value
        self.shown_year = value.year
        self.shown_month = value.month
        self.previous_grab = parent.grab_current()

        self.body = tk.Frame(self, bg=Theme.SURFACE, padx=8, pady=8)
        self.body.pack()
        self._render()

        self.update_idletasks()
        y = min(y, self.winfo_screenheight() - self.winfo_reqheight() - 40)
        self.geometry(f"+{x}+{y}")
        self.bind("<Escape>", lambda e: self.close())
        self.bind("<Button-1>", self._on_click)
        self.grab_set()
        self.focus_set()

    def _on_click(self, event) -> None:
        inside = (0 <= event.x_root - self.winfo_rootx() < self.winfo_width()
                  and 0 <= event.y_root - self.winfo_rooty() < self.winfo_height())
        if not inside:
            self.close()

    def close(self) -> None:
        self.grab_release()
        previous = self.previous_grab
        self.destroy()
        if previous is not None and previous.winfo_exists():
            previous.grab_set()

    def _shift_month(self, delta: int) -> None:
        total = self.shown_year * 12 + (self.shown_month - 1) + delta
        self.shown_year, month_index = divmod(total, 12)
        self.shown_month = month_index + 1
        self._render()

    def _pick(self, picked: date) -> None:
        self.close()
        self.on_pick(picked)

    def _render(self) -> None:
        for child in self.body.winfo_children():
            child.destroy()

        nav = tk.Frame(self.body, bg=Theme.SURFACE)
        nav.grid(row=0, column=0, columnspan=7, sticky="ew", pady=(0, 6))
        make_button(nav, "‹", lambda: self._shift_month(-1), padx=8, pady=1).pack(side=tk.LEFT)
        make_button(nav, "›", lambda: self._shift_month(1), padx=8, pady=1).pack(side=tk.RIGHT)
        tk.Label(
            nav,
            text=f"Tháng {self.shown_month}, {self.shown_year}",
            font=Theme.FONT_SUBHEADER,
            bg=Theme.SURFACE,
            fg=Theme.TEXT
        ).pack(expand=True)

        for col, name in enumerate(WEEKDAY_SHORT):
            tk.Label(self.body, text=name, font=Theme.FONT_SMALL, bg=Theme.SURFACE, fg=Theme.TEXT_MUTED, width=4).grid(row=1, column=col)

        today = date.today()
        weeks = calendar.Calendar(firstweekday=0).monthdatescalendar(self.shown_year, self.shown_month)
        for row, week in enumerate(weeks, start=2):
            for col, day in enumerate(week):
                selected = day == self.value
                in_month = day.month == self.shown_month
                button = tk.Button(
                    self.body,
                    text=str(day.day),
                    font=Theme.FONT_SUBHEADER if day == today else Theme.FONT_SMALL,
                    bg=Theme.PRIMARY if selected else Theme.SURFACE,
                    fg="white" if selected else (Theme.PRIMARY if day == today else Theme.TEXT if in_month else Theme.TEXT_FAINT),
                    activebackground=Theme.HOVER,
                    relief="flat",
                    bd=0,
                    width=3,
                    cursor="hand2",
                    command=lambda d=day: self._pick(d)
                )
                button.grid(row=row, column=col, padx=1, pady=1)


class DatePicker(tk.Frame):
    """Nút hiển thị ngày đang chọn, bấm vào để mở lịch tháng."""

    def __init__(self, parent, value: date, on_change: Optional[Callable[[], None]] = None, bg: str = Theme.SURFACE):
        super().__init__(parent, bg=bg)
        self.value = value
        self.on_change = on_change
        self.button = make_button(self, "", self._open, pady=4)
        self.button.pack(fill=tk.X)
        self._update_label()

    def _update_label(self) -> None:
        weekday = WEEKDAY_SHORT[self.value.weekday()]
        self.button.configure(text=f"{weekday}, {self.value.strftime('%d/%m/%Y')}  ▾")

    def _open(self) -> None:
        DatePopup(
            self,
            self.value,
            self._on_picked,
            self.button.winfo_rootx(),
            self.button.winfo_rooty() + self.button.winfo_height() + 2
        )

    def _on_picked(self, picked: date) -> None:
        self.set(picked)
        if self.on_change:
            self.on_change()

    def get(self) -> date:
        return self.value

    def set(self, value: date) -> None:
        self.value = value
        self._update_label()


class DateTimeField(tk.Frame):
    """Ô chọn ngày và giờ:phút. Giờ phút có thể bấm mũi tên, cuộn chuột hoặc gõ trực tiếp."""

    def __init__(self, parent, value: datetime, on_change: Optional[Callable[[], None]] = None, bg: str = Theme.SURFACE):
        super().__init__(parent, bg=bg)
        self.on_change = on_change
        self._suspended = False

        self.date_picker = DatePicker(self, value.date(), self._notify, bg=bg)
        self.date_picker.pack(side=tk.LEFT, padx=(0, 8))

        self.sp_hour = ttk.Spinbox(self, from_=0, to=23, width=3, format="%02.0f", wrap=True, font=Theme.FONT_BODY, command=self._notify)
        self.sp_hour.pack(side=tk.LEFT)
        tk.Label(self, text=":", font=Theme.FONT_SUBHEADER, bg=bg, fg=Theme.TEXT).pack(side=tk.LEFT, padx=2)
        self.sp_minute = ttk.Spinbox(self, from_=0, to=55, increment=5, width=3, format="%02.0f", wrap=True, font=Theme.FONT_BODY, command=self._notify)
        self.sp_minute.pack(side=tk.LEFT)

        for spin in (self.sp_hour, self.sp_minute):
            spin.bind("<KeyRelease>", lambda e: self._notify())

        self.set(value)

    def _notify(self) -> None:
        if not self._suspended and self.on_change:
            self.on_change()

    def get(self) -> Optional[datetime]:
        """Trả về thời điểm đang chọn, hoặc None nếu giờ phút gõ vào không hợp lệ."""
        try:
            hour, minute = int(self.sp_hour.get()), int(self.sp_minute.get())
        except ValueError:
            return None
        if not (0 <= hour <= 23 and 0 <= minute <= 59):
            return None
        chosen = self.date_picker.get()
        return datetime(chosen.year, chosen.month, chosen.day, hour, minute)

    def set(self, value: datetime) -> None:
        self._suspended = True
        self.date_picker.set(value.date())
        self.sp_hour.set(f"{value.hour:02d}")
        self.sp_minute.set(f"{value.minute:02d}")
        self._suspended = False


def next_round_time(now: datetime, step_minutes: int = 5) -> datetime:
    """Làm tròn lên mốc chẵn kế tiếp, ví dụ 18:32 thành 18:35."""
    floored = now.replace(second=0, microsecond=0)
    overshoot = floored.minute % step_minutes
    if overshoot == 0 and floored == now:
        return floored
    return floored + timedelta(minutes=step_minutes - overshoot)
