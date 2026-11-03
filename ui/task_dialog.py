"""
ui/task_dialog.py
Hộp thoại thêm mới hoặc chỉnh sửa công việc trong lịch trình.
Tích hợp kiểm tra xung đột thời gian thực và gợi ý khung giờ thông minh.
"""

import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime, timedelta
from typing import Optional, List, Callable
from core.models import Task, Priority, Status, Category
from core.scheduler_engine import SchedulerEngine
from ui.theme import Theme


class TaskDialog(tk.Toplevel):
    def __init__(
        self,
        parent: tk.Tk,
        all_tasks: List[Task],
        task: Optional[Task] = None,
        on_save: Optional[Callable[[Task], None]] = None,
        default_start: Optional[datetime] = None
    ):
        super().__init__(parent)
        self.parent = parent
        self.all_tasks = all_tasks
        self.task = task
        self.on_save = on_save
        self.is_edit_mode = task is not None

        self.title("✏️ Chỉnh sửa công việc" if self.is_edit_mode else "➕ Thêm công việc mới")
        self.geometry("540x680")
        self.resizable(False, False)
        self.configure(bg=Theme.BG_DARK)

        # Đặt làm cửa sổ modal
        self.transient(parent)
        self.grab_set()

        self._build_ui(default_start)

    def _build_ui(self, default_start: Optional[datetime]):
        main_frame = tk.Frame(self, bg=Theme.BG_DARK, padx=24, pady=20)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Tiêu đề Header
        header_text = "CẬP NHẬT CÔNG VIỆC" if self.is_edit_mode else "THÊM CÔNG VIỆC MỚI"
        lbl_head = tk.Label(
            main_frame,
            text=header_text,
            font=Theme.FONT_TITLE,
            fg=Theme.PRIMARY,
            bg=Theme.BG_DARK
        )
        lbl_head.pack(anchor="w", pady=(0, 16))

        # Tiêu đề task
        lbl_title = tk.Label(main_frame, text="Tiêu đề công việc (*):", font=Theme.FONT_SUBHEADER, fg=Theme.TEXT_MAIN, bg=Theme.BG_DARK)
        lbl_title.pack(anchor="w")
        self.ent_title = tk.Entry(
            main_frame,
            font=Theme.FONT_BODY,
            bg=Theme.BG_INPUT,
            fg=Theme.TEXT_MAIN,
            insertbackground=Theme.TEXT_MAIN,
            relief="flat",
            highlightthickness=1,
            highlightbackground=Theme.BORDER,
            highlightcolor=Theme.PRIMARY
        )
        self.ent_title.pack(fill=tk.X, pady=(4, 12), ipady=4)

        # Hàng 2: Danh mục & Mức độ ưu tiên
        row2 = tk.Frame(main_frame, bg=Theme.BG_DARK)
        row2.pack(fill=tk.X, pady=(0, 12))

        # Danh mục
        col_cat = tk.Frame(row2, bg=Theme.BG_DARK)
        col_cat.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 8))
        tk.Label(col_cat, text="Danh mục:", font=Theme.FONT_SUBHEADER, fg=Theme.TEXT_MAIN, bg=Theme.BG_DARK).pack(anchor="w")
        self.cb_category = ttk.Combobox(
            col_cat,
            values=[c.value[0] for c in Category],
            state="readonly",
            font=Theme.FONT_BODY
        )
        self.cb_category.pack(fill=tk.X, pady=(4, 0), ipady=3)
        self.cb_category.set(self.task.category if self.task else Category.WORK.value[0])

        # Độ ưu tiên
        col_prio = tk.Frame(row2, bg=Theme.BG_DARK)
        col_prio.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(8, 0))
        tk.Label(col_prio, text="Mức độ ưu tiên:", font=Theme.FONT_SUBHEADER, fg=Theme.TEXT_MAIN, bg=Theme.BG_DARK).pack(anchor="w")
        self.cb_priority = ttk.Combobox(
            col_prio,
            values=[f"{p.level} - {p.label}" for p in Priority],
            state="readonly",
            font=Theme.FONT_BODY
        )
        self.cb_priority.pack(fill=tk.X, pady=(4, 0), ipady=3)
        if self.task:
            self.cb_priority.set(f"{self.task.priority.level} - {self.task.priority.label}")
        else:
            self.cb_priority.set(f"{Priority.MEDIUM.level} - {Priority.MEDIUM.label}")

        # Hàng 3: Thời gian bắt đầu và kết thúc
        row3 = tk.Frame(main_frame, bg=Theme.BG_DARK)
        row3.pack(fill=tk.X, pady=(0, 8))

        # Khởi tạo giá trị mặc định cho thời gian
        now = default_start or datetime.now()
        start_def = self.task.start_time if self.task else now.replace(minute=0, second=0, microsecond=0) + timedelta(hours=1)
        end_def = self.task.end_time if self.task else start_def + timedelta(hours=1)

        # Bắt đầu
        col_start = tk.Frame(row3, bg=Theme.BG_DARK)
        col_start.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 8))
        tk.Label(col_start, text="Bắt đầu (YYYY-MM-DD HH:MM):", font=Theme.FONT_SUBHEADER, fg=Theme.TEXT_MAIN, bg=Theme.BG_DARK).pack(anchor="w")
        self.ent_start = tk.Entry(col_start, font=Theme.FONT_BODY, bg=Theme.BG_INPUT, fg=Theme.TEXT_MAIN, insertbackground=Theme.TEXT_MAIN, relief="flat", highlightthickness=1, highlightbackground=Theme.BORDER)
        self.ent_start.pack(fill=tk.X, pady=(4, 0), ipady=4)
        self.ent_start.insert(0, start_def.strftime("%Y-%m-%d %H:%M"))

        # Kết thúc
        col_end = tk.Frame(row3, bg=Theme.BG_DARK)
        col_end.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(8, 0))
        tk.Label(col_end, text="Kết thúc (YYYY-MM-DD HH:MM):", font=Theme.FONT_SUBHEADER, fg=Theme.TEXT_MAIN, bg=Theme.BG_DARK).pack(anchor="w")
        self.ent_end = tk.Entry(col_end, font=Theme.FONT_BODY, bg=Theme.BG_INPUT, fg=Theme.TEXT_MAIN, insertbackground=Theme.TEXT_MAIN, relief="flat", highlightthickness=1, highlightbackground=Theme.BORDER)
        self.ent_end.pack(fill=tk.X, pady=(4, 0), ipady=4)
        self.ent_end.insert(0, end_def.strftime("%Y-%m-%d %H:%M"))

        # Trạng thái kiểm tra xung đột thời gian thực
        self.btn_check_conflict = tk.Button(
            main_frame,
            text="🔍 Kiểm tra xung đột thời gian",
            font=Theme.FONT_SMALL,
            bg=Theme.BG_CARD,
            fg=Theme.INFO,
            relief="flat",
            activebackground=Theme.BG_CARD_HOVER,
            command=self._check_conflict_action
        )
        self.btn_check_conflict.pack(anchor="w", pady=(2, 6))

        self.lbl_conflict_status = tk.Label(
            main_frame,
            text="Chưa phát hiện xung đột thời gian",
            font=Theme.FONT_SMALL,
            fg=Theme.SUCCESS,
            bg=Theme.BG_DARK
        )
        self.lbl_conflict_status.pack(anchor="w", pady=(0, 10))

        # Hàng 4: Trạng thái & Công việc tiên quyết (Dependencies)
        row4 = tk.Frame(main_frame, bg=Theme.BG_DARK)
        row4.pack(fill=tk.X, pady=(0, 12))

        # Trạng thái
        col_st = tk.Frame(row4, bg=Theme.BG_DARK)
        col_st.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 8))
        tk.Label(col_st, text="Trạng thái:", font=Theme.FONT_SUBHEADER, fg=Theme.TEXT_MAIN, bg=Theme.BG_DARK).pack(anchor="w")
        self.cb_status = ttk.Combobox(
            col_st,
            values=[s.label for s in Status],
            state="readonly",
            font=Theme.FONT_BODY
        )
        self.cb_status.pack(fill=tk.X, pady=(4, 0), ipady=3)
        self.cb_status.set(self.task.status.label if self.task else Status.PENDING.label)

        # Tiên quyết (Dependencies)
        col_dep = tk.Frame(row4, bg=Theme.BG_DARK)
        col_dep.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(8, 0))
        tk.Label(col_dep, text="ID Tiên quyết (cách nhau dấu phẩy):", font=Theme.FONT_SUBHEADER, fg=Theme.TEXT_MAIN, bg=Theme.BG_DARK).pack(anchor="w")
        self.ent_dep = tk.Entry(col_dep, font=Theme.FONT_BODY, bg=Theme.BG_INPUT, fg=Theme.TEXT_MAIN, insertbackground=Theme.TEXT_MAIN, relief="flat", highlightthickness=1, highlightbackground=Theme.BORDER)
        self.ent_dep.pack(fill=tk.X, pady=(4, 0), ipady=4)
        if self.task and self.task.dependencies:
            self.ent_dep.insert(0, ", ".join(self.task.dependencies))

        # Mô tả chi tiết
        tk.Label(main_frame, text="Mô tả / Ghi chú:", font=Theme.FONT_SUBHEADER, fg=Theme.TEXT_MAIN, bg=Theme.BG_DARK).pack(anchor="w")
        self.txt_desc = tk.Text(
            main_frame,
            height=4,
            font=Theme.FONT_BODY,
            bg=Theme.BG_INPUT,
            fg=Theme.TEXT_MAIN,
            insertbackground=Theme.TEXT_MAIN,
            relief="flat",
            highlightthickness=1,
            highlightbackground=Theme.BORDER
        )
        self.txt_desc.pack(fill=tk.BOTH, expand=True, pady=(4, 16))

        # Đổ dữ liệu cũ nếu đang sửa
        if self.task:
            self.ent_title.insert(0, self.task.title)
            self.txt_desc.insert("1.0", self.task.description)

        # Hàng nút bấm Hành động
        btn_bar = tk.Frame(main_frame, bg=Theme.BG_DARK)
        btn_bar.pack(fill=tk.X)

        btn_cancel = tk.Button(
            btn_bar,
            text="Hủy bỏ",
            font=Theme.FONT_BODY,
            bg=Theme.BG_CARD,
            fg=Theme.TEXT_MUTED,
            relief="flat",
            padx=16,
            pady=6,
            command=self.destroy
        )
        btn_cancel.pack(side=tk.RIGHT, padx=(8, 0))

        btn_save = tk.Button(
            btn_bar,
            text="Lưu công việc",
            font=Theme.FONT_BODY,
            bg=Theme.PRIMARY,
            fg="white",
            relief="flat",
            padx=20,
            pady=6,
            command=self._save_action
        )
        btn_save.pack(side=tk.RIGHT)

        # Chạy kiểm tra xung đột ban đầu
        self._check_conflict_action()

    def _parse_inputs(self) -> Optional[Task]:
        title = self.ent_title.get().strip()
        if not title:
            messagebox.showerror("Thiếu thông tin", "Vui lòng nhập tiêu đề công việc!", parent=self)
            return None

        # Đọc thời gian
        try:
            start_time = datetime.strptime(self.ent_start.get().strip(), "%Y-%m-%d %H:%M")
        except ValueError:
            messagebox.showerror("Lỗi định dạng", "Thời gian bắt đầu không hợp lệ (Định dạng: YYYY-MM-DD HH:MM)", parent=self)
            return None

        try:
            end_time = datetime.strptime(self.ent_end.get().strip(), "%Y-%m-%d %H:%M")
        except ValueError:
            messagebox.showerror("Lỗi định dạng", "Thời gian kết thúc không hợp lệ (Định dạng: YYYY-MM-DD HH:MM)", parent=self)
            return None

        if end_time <= start_time:
            messagebox.showerror("Lỗi logic", "Thời gian kết thúc phải diễn ra sau thời gian bắt đầu!", parent=self)
            return None

        # Priority
        prio_str = self.cb_priority.get().split(" - ")[-1]
        priority = Priority.from_string(prio_str)

        # Status
        status_str = self.cb_status.get()
        status = Status.from_string(status_str)

        # Category
        cat_str = self.cb_category.get()

        # Dependencies
        raw_deps = self.ent_dep.get().strip()
        deps = [d.strip() for d in raw_deps.split(",") if d.strip()] if raw_deps else []

        description = self.txt_desc.get("1.0", tk.END).strip()

        task_id = self.task.id if self.task else None
        created_at = self.task.created_at if self.task else None

        return Task(
            id=task_id,
            title=title,
            start_time=start_time,
            end_time=end_time,
            category=cat_str,
            priority=priority,
            status=status,
            dependencies=deps,
            description=description,
            created_at=created_at
        )

    def _check_conflict_action(self):
        try:
            start_time = datetime.strptime(self.ent_start.get().strip(), "%Y-%m-%d %H:%M")
            end_time = datetime.strptime(self.ent_end.get().strip(), "%Y-%m-%d %H:%M")
            if end_time <= start_time:
                self.lbl_conflict_status.config(text="⚠️ Giờ kết thúc <= giờ bắt đầu", fg=Theme.DANGER)
                return

            candidate = Task(
                id=self.task.id if self.task else "TEMP",
                title="Temp",
                start_time=start_time,
                end_time=end_time
            )
            conflicts = SchedulerEngine.detect_conflicts_for_task(candidate, self.all_tasks)
            if conflicts:
                msg = f"⚠️ Xung đột với {len(conflicts)} việc: " + ", ".join([f"'{c.task2.title}'" for c in conflicts[:2]])
                if len(conflicts) > 2:
                    msg += f" và {len(conflicts)-2} việc khác"
                self.lbl_conflict_status.config(text=msg, fg=Theme.WARNING)
            else:
                self.lbl_conflict_status.config(text="✅ Không phát hiện xung đột thời gian", fg=Theme.SUCCESS)
        except Exception:
            self.lbl_conflict_status.config(text="ℹ️ Hãy nhập đúng định dạng ngày giờ để kiểm tra", fg=Theme.TEXT_MUTED)

    def _save_action(self):
        task = self._parse_inputs()
        if not task:
            return

        # Cảnh báo nếu vẫn còn xung đột
        conflicts = SchedulerEngine.detect_conflicts_for_task(task, self.all_tasks)
        if conflicts:
            confirm = messagebox.askyesno(
                "Xác nhận xung đột",
                f"Công việc này đang bị trùng lịch với {len(conflicts)} công việc khác.\n"
                f"Ví dụ: '{conflicts[0].task2.title}' ({conflicts[0].overlap_minutes} phút trùng).\n\n"
                f"Bạn có chắc chắn muốn lưu lại không?",
                parent=self
            )
            if not confirm:
                return

        if self.on_save:
            self.on_save(task)
        self.destroy()
