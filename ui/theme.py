"""
ui/theme.py
Bộ thiết lập giao diện: bảng màu sáng dễ đọc, typography và kiểu dáng các thành phần ttk.
"""

from tkinter import ttk


class Theme:
    # Màu nền
    BG = "#F3F5FA"               # Nền chính ứng dụng
    SURFACE = "#FFFFFF"          # Nền thẻ, bảng, ô nhập liệu
    SURFACE_ALT = "#F8FAFC"      # Dòng xen kẽ trong bảng
    HOVER = "#EAF0FB"            # Khi rê chuột, ô đang chọn nhẹ
    BUTTON = "#E9EDF5"           # Nền nút phụ
    BUTTON_HOVER = "#DCE2EE"
    BUTTON_DISABLED = "#EEF1F6"  # Nền nút đang tắt
    TODAY = "#F5F8FF"            # Cột ngày hôm nay trên lịch

    # Màu chữ
    TEXT = "#1F2937"             # Chữ chính
    TEXT_MUTED = "#64748B"       # Chữ phụ
    TEXT_FAINT = "#94A3B8"       # Việc đã hủy, ghi chú mờ

    # Màu điểm nhấn
    PRIMARY = "#2563EB"
    PRIMARY_HOVER = "#1D4ED8"
    PRIMARY_SOFT = "#DBEAFE"
    SUCCESS = "#047857"
    SUCCESS_HOVER = "#065F46"
    SUCCESS_SOFT = "#D1FAE5"
    WARNING = "#B45309"
    WARNING_SOFT = "#FEF3C7"
    DANGER = "#DC2626"
    DANGER_HOVER = "#B91C1C"
    DANGER_SOFT = "#FEE2E2"

    # Viền và ngăn cách
    BORDER = "#D8DEE9"
    GRID_LINE = "#E8ECF3"

    # Font chữ
    FONT_TITLE = ("Segoe UI", 15, "bold")
    FONT_HEADER = ("Segoe UI", 12, "bold")
    FONT_SUBHEADER = ("Segoe UI", 10, "bold")
    FONT_BODY = ("Segoe UI", 10)
    FONT_SMALL = ("Segoe UI", 9)
    FONT_KPI = ("Segoe UI", 20, "bold")

    @staticmethod
    def mix_with_white(color: str, amount: float = 0.82) -> str:
        """Pha màu với trắng để lấy màu nền nhạt của cùng một sắc độ."""
        r, g, b = (int(color[i:i + 2], 16) for i in (1, 3, 5))
        r, g, b = (round(c + (255 - c) * amount) for c in (r, g, b))
        return f"#{r:02x}{g:02x}{b:02x}"

    @classmethod
    def apply_styles(cls, root) -> None:
        """Cấu hình kiểu dáng ttk dùng chung cho toàn ứng dụng."""
        style = ttk.Style(root)
        style.theme_use("clam")

        style.configure(
            "TNotebook",
            background=cls.BG,
            bordercolor=cls.BORDER,
            lightcolor=cls.SURFACE,
            darkcolor=cls.SURFACE,
            tabmargins=[0, 0, 0, 0]
        )
        style.configure(
            "TNotebook.Tab",
            background=cls.BG,
            foreground=cls.TEXT_MUTED,
            padding=[16, 8],
            font=cls.FONT_SUBHEADER,
            bordercolor=cls.BORDER,
            lightcolor=cls.BG,
            darkcolor=cls.BG
        )
        style.map(
            "TNotebook.Tab",
            background=[("selected", cls.SURFACE), ("active", cls.HOVER)],
            foreground=[("selected", cls.PRIMARY)],
            lightcolor=[("selected", cls.SURFACE)],
            darkcolor=[("selected", cls.SURFACE)],
            expand=[("selected", (0, 0, 0, 0))]
        )

        style.configure(
            "Treeview",
            background=cls.SURFACE,
            foreground=cls.TEXT,
            fieldbackground=cls.SURFACE,
            rowheight=32,
            font=cls.FONT_BODY,
            bordercolor=cls.BORDER,
            lightcolor=cls.SURFACE,
            darkcolor=cls.SURFACE,
            borderwidth=0
        )
        style.layout("Treeview", [("Treeview.treearea", {"sticky": "nswe"})])
        style.configure(
            "Treeview.Heading",
            background=cls.SURFACE_ALT,
            foreground=cls.TEXT_MUTED,
            font=cls.FONT_SUBHEADER,
            relief="flat",
            bordercolor=cls.BORDER,
            lightcolor=cls.SURFACE_ALT,
            darkcolor=cls.SURFACE_ALT,
            padding=[6, 7]
        )
        style.map("Treeview.Heading", background=[("active", cls.HOVER)])
        style.map(
            "Treeview",
            background=[("selected", cls.PRIMARY_SOFT)],
            foreground=[("selected", cls.TEXT)]
        )

        field = dict(
            fieldbackground=cls.SURFACE,
            background=cls.SURFACE,
            foreground=cls.TEXT,
            bordercolor=cls.BORDER,
            lightcolor=cls.BORDER,
            darkcolor=cls.BORDER,
            arrowcolor=cls.TEXT_MUTED,
            padding=4
        )
        style.configure("TCombobox", **field)
        style.map(
            "TCombobox",
            fieldbackground=[("readonly", cls.SURFACE)],
            background=[("readonly", cls.SURFACE), ("active", cls.HOVER)],
            selectbackground=[("readonly", cls.SURFACE)],
            selectforeground=[("readonly", cls.TEXT)],
            bordercolor=[("focus", cls.PRIMARY)]
        )
        style.configure("TSpinbox", **field)
        style.map("TSpinbox", bordercolor=[("focus", cls.PRIMARY)], background=[("active", cls.HOVER)])
        root.option_add("*TCombobox*Listbox.font", cls.FONT_BODY)
        root.option_add("*TCombobox*Listbox.background", cls.SURFACE)
        root.option_add("*TCombobox*Listbox.foreground", cls.TEXT)
        root.option_add("*TCombobox*Listbox.selectBackground", cls.PRIMARY_SOFT)
        root.option_add("*TCombobox*Listbox.selectForeground", cls.TEXT)

        style.configure(
            "TScrollbar",
            background=cls.BORDER,
            troughcolor=cls.BG,
            bordercolor=cls.BG,
            lightcolor=cls.BORDER,
            darkcolor=cls.BORDER,
            arrowcolor=cls.TEXT_MUTED
        )
        style.map(
            "TScrollbar",
            background=[("disabled", cls.BG), ("active", cls.TEXT_FAINT)],
            lightcolor=[("disabled", cls.BG)],
            darkcolor=[("disabled", cls.BG)],
            bordercolor=[("disabled", cls.BG)],
            arrowcolor=[("disabled", cls.BORDER)]
        )
        style.configure("TRadiobutton", background=cls.SURFACE, foreground=cls.TEXT, font=cls.FONT_BODY)
        style.map("TRadiobutton", background=[("active", cls.SURFACE)])
