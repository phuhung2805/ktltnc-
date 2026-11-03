"""
ui/smart_slot_dialog.py
Hộp thoại gợi ý khung thời gian rảnh thông minh (Smart Free Slot Finder).
Cho phép người dùng chọn tiêu chí (Sớm nhất / Tối ưu diện tích Best-Fit) và áp dụng ngay.
"""

import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime, timedelta
from typing import List, Callable, Optional, Tuple
from core.models import Task
from core.scheduler_engine import SchedulerEngine, FreeTimeSlot
from ui.theme import Theme


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

        self.title("⚡ Gợi ý khung giờ rảnh thông minh")
        self.geometry("620x580")
        self.resizable(False, False)
        self.configure(bg=Theme.BG_DARK)

        self.transient(parent)
        self.grab_set()

        self._build_ui()

    def _build_ui(self):
        container = tk.Frame(self, bg=Theme.BG_DARK, padx=20, pady=16)
        container.pack(fill=tk.BOTH, expand=True)

        # Tiêu đề
        tk.Label(
            container,
            text="TÌM & GỢI Ý KHUNG GIỜ LÀM VIỆC TỐI ƯU",
            font=Theme.FONT_TITLE,
            fg=Theme.PRIMARY,
            bg=Theme.BG_DARK
        ).pack(anchor="w", pady=(0, 12))

        tk.Label(
            container,
            text="Thuật toán sẽ tự động phân tích các khoảng bận và tìm khe thời gian rảnh thích hợp nhất.",
            font=Theme.FONT_SMALL,
            fg=Theme.TEXT_MUTED,
            bg=Theme.BG_DARK
        ).pack(anchor="w", pady=(0, 14))

        # Panel thông số đầu vào
        param_frame = tk.Frame(container, bg=Theme.BG_CARD, padx=14, pady=12, highlightthickness=1, highlightbackground=Theme.BORDER)
        param_frame.pack(fill=tk.X, pady=(0, 14))

        # Hàng 1: Ngày cần tìm & Thời lượng
        r1 = tk.Frame(param_frame, bg=Theme.BG_CARD)
        r1.pack(fill=tk.X, pady=(0, 8))

        c1 = tk.Frame(r1, bg=Theme.BG_CARD)
        c1.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 6))
        tk.Label(c1, text="Ngày làm việc (YYYY-MM-DD):", font=Theme.FONT_SUBHEADER, fg=Theme.TEXT_MAIN, bg=Theme.BG_CARD).pack(anchor="w")
        self.ent_date = tk.Entry(c1, font=Theme.FONT_BODY, bg=Theme.BG_INPUT, fg=Theme.TEXT_MAIN, insertbackground=Theme.TEXT_MAIN, relief="flat")
        self.ent_date.pack(fill=tk.X, pady=(4, 0), ipady=3)
        self.ent_date.insert(0, datetime.now().strftime("%Y-%m-%d"))

        c2 = tk.Frame(r1, bg=Theme.BG_CARD)
        c2.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(6, 0))
        tk.Label(c2, text="Thời lượng cần (phút):", font=Theme.FONT_SUBHEADER, fg=Theme.TEXT_MAIN, bg=Theme.BG_CARD).pack(anchor="w")
        self.ent_dur = tk.Entry(c2, font=Theme.FONT_BODY, bg=Theme.BG_INPUT, fg=Theme.TEXT_MAIN, insertbackground=Theme.TEXT_MAIN, relief="flat")
        self.ent_dur.pack(fill=tk.X, pady=(4, 0), ipady=3)
        self.ent_dur.insert(0, "60")

        # Hàng 2: Khung giờ & Chiến lược
        r2 = tk.Frame(param_frame, bg=Theme.BG_CARD)
        r2.pack(fill=tk.X)

        c3 = tk.Frame(r2, bg=Theme.BG_CARD)
        c3.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 6))
        tk.Label(c3, text="Khung giờ trong ngày (Từ - Đến):", font=Theme.FONT_SUBHEADER, fg=Theme.TEXT_MAIN, bg=Theme.BG_CARD).pack(anchor="w")
        sub_r = tk.Frame(c3, bg=Theme.BG_CARD)
        sub_r.pack(fill=tk.X, pady=(4, 0))
        self.sp_start_hr = ttk.Spinbox(sub_r, from_=6, to=12, width=5)
        self.sp_start_hr.pack(side=tk.LEFT)
        self.sp_start_hr.set(8)
        tk.Label(sub_r, text="h -> ", font=Theme.FONT_BODY, fg=Theme.TEXT_MAIN, bg=Theme.BG_CARD).pack(side=tk.LEFT, padx=4)
        self.sp_end_hr = ttk.Spinbox(sub_r, from_=13, to=23, width=5)
        self.sp_end_hr.pack(side=tk.LEFT)
        self.sp_end_hr.set(21)
        tk.Label(sub_r, text="h", font=Theme.FONT_BODY, fg=Theme.TEXT_MAIN, bg=Theme.BG_CARD).pack(side=tk.LEFT)

        c4 = tk.Frame(r2, bg=Theme.BG_CARD)
        c4.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(6, 0))
        tk.Label(c4, text="Chiến lược chọn:", font=Theme.FONT_SUBHEADER, fg=Theme.TEXT_MAIN, bg=Theme.BG_CARD).pack(anchor="w")
        self.cb_strat = ttk.Combobox(
            c4,
            values=["Sớm nhất có thể (Earliest)", "Vừa vặn nhất (Best-Fit / Giảm phân mảnh)"],
            state="readonly",
            font=Theme.FONT_BODY
        )
        self.cb_strat.pack(fill=tk.X, pady=(4, 0), ipady=2)
        self.cb_strat.set("Sớm nhất có thể (Earliest)")

        # Nút tìm kiếm
        btn_find = tk.Button(
            container,
            text="⚡ Phân tích & Tìm kiếm khung giờ rảnh",
            font=Theme.FONT_HEADER,
            bg=Theme.PRIMARY,
            fg="white",
            relief="flat",
            pady=6,
            command=self._find_slots
        )
        btn_find.pack(fill=tk.X, pady=(0, 12))

        # Bảng danh sách các khe rảnh tìm được
        tk.Label(container, text="Danh sách các khe rảnh phù hợp:", font=Theme.FONT_SUBHEADER, fg=Theme.TEXT_MAIN, bg=Theme.BG_DARK).pack(anchor="w", pady=(0, 4))

        tree_frame = tk.Frame(container, bg=Theme.BG_DARK)
        tree_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        cols = ("slot_id", "start", "end", "duration", "rating")
        self.tree = ttk.Treeview(tree_frame, columns=cols, show="headings", height=6)
        self.tree.heading("slot_id", text="STT")
        self.tree.heading("start", text="Bắt đầu")
        self.tree.heading("end", text="Kết thúc")
        self.tree.heading("duration", text="Tổng rảnh")
        self.tree.heading("rating", text="Đánh giá phù hợp")

        self.tree.column("slot_id", width=45, anchor="center")
        self.tree.column("start", width=120, anchor="center")
        self.tree.column("end", width=120, anchor="center")
        self.tree.column("duration", width=110, anchor="center")
        self.tree.column("rating", width=160, anchor="w")

        scroll = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scroll.set)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)

        # Hàng nút Áp dụng
        b_bar = tk.Frame(container, bg=Theme.BG_DARK)
        b_bar.pack(fill=tk.X)

        self.btn_apply = tk.Button(
            b_bar,
            text="✅ Chọn khe này & Tạo công việc",
            font=Theme.FONT_HEADER,
            bg=Theme.SUCCESS,
            fg="white",
            relief="flat",
            pady=6,
            state="disabled",
            command=self._apply_slot
        )
        self.btn_apply.pack(side=tk.RIGHT)

        self.tree.bind("<<TreeviewSelect>>", lambda e: self.btn_apply.config(state="normal"))

        # Chạy tìm kiếm mặc định
        self._find_slots()

    def _find_slots(self):
        try:
            target_date = datetime.strptime(self.ent_date.get().strip(), "%Y-%m-%d")
        except ValueError:
            messagebox.showerror("Lỗi", "Ngày không đúng định dạng YYYY-MM-DD", parent=self)
            return

        try:
            duration = int(self.ent_dur.get().strip())
            if duration <= 0:
                raise ValueError()
        except ValueError:
            messagebox.showerror("Lỗi", "Thời lượng phải là số nguyên dương (phút)", parent=self)
            return

        try:
            sh = int(self.sp_start_hr.get())
            eh = int(self.sp_end_hr.get())
            if sh >= eh:
                raise ValueError()
        except Exception:
            messagebox.showerror("Lỗi", "Giờ bắt đầu ngày phải nhỏ hơn giờ kết thúc ngày", parent=self)
            return

        # Gọi thuật toán
        slots = SchedulerEngine.find_free_slots(
            self.all_tasks,
            target_date=target_date,
            day_start_hour=sh,
            day_end_hour=eh,
            min_duration_minutes=duration
        )

        for row in self.tree.get_children():
            self.tree.delete(row)

        self.found_slots = slots
        if not slots:
            self.btn_apply.config(state="disabled")
            messagebox.showinfo("Kết quả", "Không tìm thấy khung giờ rảnh nào đủ độ dài trong ngày này!", parent=self)
            return

        is_best_fit = "Best-Fit" in self.cb_strat.get()
        # Tính điểm đánh giá
        for idx, s in enumerate(slots):
            waste = s.duration_minutes - duration
            if is_best_fit and waste == min(s.duration_minutes - duration for s in slots):
                eval_str = "⭐ Tối ưu Best-Fit (Ít dư nhất)"
            elif idx == 0:
                eval_str = "🚀 Sớm nhất trong ngày"
            else:
                eval_str = f"Dư {waste} phút rảnh"

            self.tree.insert("", "end", iid=str(idx), values=(
                idx + 1,
                s.start_time.strftime("%H:%M"),
                s.end_time.strftime("%H:%M"),
                f"{s.duration_minutes} phút ({s.duration_hours}h)",
                eval_str
            ))

        # Tự động chọn dòng đầu tiên
        self.tree.selection_set("0")
        self.btn_apply.config(state="normal")

    def _apply_slot(self):
        selected = self.tree.selection()
        if not selected:
            return
        idx = int(selected[0])
        slot = self.found_slots[idx]
        duration = int(self.ent_dur.get().strip())
        slot_end = slot.start_time + timedelta(minutes=duration)

        if self.on_slot_selected:
            self.on_slot_selected(slot.start_time, slot_end, duration)
        self.destroy()
