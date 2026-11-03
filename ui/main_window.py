"""
ui/main_window.py
Cửa sổ chính của Hệ thống Quản lý Lịch Làm việc Cá nhân.
Tích hợp các tab:
1. Danh sách & Lịch trình (Schedule & Tasks)
2. Ma trận Eisenhower (4 Quadrants)
3. Thống kê & Bảng điều khiển (Analytics & Charts)
4. Đồ thị Phụ thuộc & Thứ tự thực hiện (DAG & Kahn's Topological Sort)
5. Lập lịch Tối ưu có trọng số (Dynamic Programming - Weighted Interval Scheduling)
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import datetime, timedelta
from typing import List, Optional

from core.models import Task, Priority, Status, Category
from core.scheduler_engine import SchedulerEngine
from core.storage import StorageManager
from ui.theme import Theme
from ui.task_dialog import TaskDialog
from ui.smart_slot_dialog import SmartSlotDialog
from ui.eisenhower_view import EisenhowerView
from ui.analytics_view import AnalyticsView


class MainWindow(tk.Tk):
    def __init__(self, db_path: str = "schedule.db"):
        super().__init__()
        self.storage = StorageManager(db_path=db_path)
        self.tasks: List[Task] = []

        self.title("Hệ thống Quản lý Lịch làm việc Cá nhân - Personal Scheduler")
        self.geometry("1180x760")
        self.minsize(980, 640)
        self.configure(bg=Theme.BG_DARK)

        self._configure_styles()
        self._build_ui()
        self._load_data()

    def _configure_styles(self):
        style = ttk.Style()
        style.theme_use("clam")

        # Cấu hình Notebook Tabs
        style.configure("TNotebook", background=Theme.BG_DARK, borderwidth=0)
        style.configure(
            "TNotebook.Tab",
            background=Theme.BG_CARD,
            foreground=Theme.TEXT_MUTED,
            padding=[16, 8],
            font=Theme.FONT_SUBHEADER,
            borderwidth=0
        )
        style.map(
            "TNotebook.Tab",
            background=[("selected", Theme.PRIMARY)],
            foreground=[("selected", "white")]
        )

        # Cấu hình Treeview
        style.configure(
            "Treeview",
            background=Theme.BG_CARD,
            foreground=Theme.TEXT_MAIN,
            fieldbackground=Theme.BG_CARD,
            rowheight=32,
            font=Theme.FONT_BODY,
            borderwidth=0
        )
        style.configure(
            "Treeview.Heading",
            background=Theme.BG_SIDEBAR,
            foreground=Theme.TEXT_MAIN,
            font=Theme.FONT_SUBHEADER,
            relief="flat",
            padding=[6, 6]
        )
        style.map(
            "Treeview",
            background=[("selected", Theme.BG_CARD_HOVER)],
            foreground=[("selected", Theme.PRIMARY)]
        )

        # Scrollbar
        style.configure("Vertical.TScrollbar", background=Theme.BG_CARD, bordercolor=Theme.BORDER, arrowcolor=Theme.TEXT_MUTED)

    def _build_ui(self):
        # 1. Thanh tiêu đề và công cụ trên cùng (Header & Action Bar)
        header_frame = tk.Frame(self, bg=Theme.BG_SIDEBAR, padx=20, pady=12)
        header_frame.pack(fill=tk.X)

        # Logo & Tên ứng dụng
        title_box = tk.Frame(header_frame, bg=Theme.BG_SIDEBAR)
        title_box.pack(side=tk.LEFT)

        tk.Label(
            title_box,
            text="📅 LỊCH LÀM VIỆC CÁ NHÂN",
            font=("Segoe UI", 16, "bold"),
            fg=Theme.PRIMARY,
            bg=Theme.BG_SIDEBAR
        ).pack(anchor="w")

        self.lbl_header_sub = tk.Label(
            title_box,
            text="Hệ thống hỗ trợ lập lịch thông minh & tối ưu hóa thuật toán",
            font=Theme.FONT_SMALL,
            fg=Theme.TEXT_MUTED,
            bg=Theme.BG_SIDEBAR
        )
        self.lbl_header_sub.pack(anchor="w")

        # Nút thao tác nhanh bên phải
        btn_box = tk.Frame(header_frame, bg=Theme.BG_SIDEBAR)
        btn_box.pack(side=tk.RIGHT)

        btn_add = tk.Button(
            btn_box,
            text="➕ Thêm công việc",
            font=Theme.FONT_SUBHEADER,
            bg=Theme.PRIMARY,
            fg="white",
            relief="flat",
            padx=12,
            pady=6,
            command=self._open_add_dialog
        )
        btn_add.pack(side=tk.LEFT, padx=4)

        btn_smart = tk.Button(
            btn_box,
            text="⚡ Gợi ý khung giờ",
            font=Theme.FONT_SUBHEADER,
            bg=Theme.INFO,
            fg="white",
            relief="flat",
            padx=12,
            pady=6,
            command=self._open_smart_slot_dialog
        )
        btn_smart.pack(side=tk.LEFT, padx=4)

        btn_conflict = tk.Button(
            btn_box,
            text="⚠️ Quét xung đột",
            font=Theme.FONT_SUBHEADER,
            bg=Theme.WARNING,
            fg="black",
            relief="flat",
            padx=12,
            pady=6,
            command=self._show_conflicts_modal
        )
        btn_conflict.pack(side=tk.LEFT, padx=4)

        btn_seed = tk.Button(
            btn_box,
            text="🌱 Nạp mẫu",
            font=Theme.FONT_BODY,
            bg=Theme.BG_CARD,
            fg=Theme.TEXT_MAIN,
            relief="flat",
            padx=10,
            pady=6,
            command=self._seed_sample_action
        )
        btn_seed.pack(side=tk.LEFT, padx=4)

        # 2. Hệ thống Tabs chính (Notebook)
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=16, pady=12)

        # Tab 1: Danh sách công việc
        self.tab_tasks = tk.Frame(self.notebook, bg=Theme.BG_DARK)
        self.notebook.add(self.tab_tasks, text="📋 Danh sách & Lịch")
        self._build_tasks_tab(self.tab_tasks)

        # Tab 2: Ma trận Eisenhower
        self.tab_eisenhower = EisenhowerView(self.notebook, on_task_double_click=self._open_edit_dialog)
        self.notebook.add(self.tab_eisenhower, text="🧭 Ma trận Eisenhower")

        # Tab 3: Thống kê & Dashboard
        self.tab_analytics = AnalyticsView(self.notebook)
        self.notebook.add(self.tab_analytics, text="📊 Thống kê & Hiệu suất")

        # Tab 4: Đồ thị Phụ thuộc (DAG & Kahn)
        self.tab_topo = tk.Frame(self.notebook, bg=Theme.BG_DARK)
        self.notebook.add(self.tab_topo, text="🔀 Phụ thuộc (Kahn DAG)")
        self._build_topo_tab(self.tab_topo)

        # Tab 5: Lập lịch Tối ưu (DP)
        self.tab_wis = tk.Frame(self.notebook, bg=Theme.BG_DARK)
        self.notebook.add(self.tab_wis, text="🎯 Tối ưu hóa (Quy hoạch động)")
        self._build_wis_tab(self.tab_wis)

        # Khi chuyển tab, tự động cập nhật
        self.notebook.bind("<<NotebookTabChanged>>", self._on_tab_changed)

        # 3. Thanh trạng thái phía dưới (Status Bar)
        status_bar = tk.Frame(self, bg=Theme.BG_SIDEBAR, padx=16, pady=6)
        status_bar.pack(fill=tk.X, side=tk.BOTTOM)

        self.lbl_status = tk.Label(
            status_bar,
            text="Sẵn sàng",
            font=Theme.FONT_SMALL,
            fg=Theme.TEXT_MUTED,
            bg=Theme.BG_SIDEBAR
        )
        self.lbl_status.pack(side=tk.LEFT)

        self.lbl_clock = tk.Label(
            status_bar,
            text=datetime.now().strftime("%Y-%m-%d %H:%M"),
            font=Theme.FONT_SMALL,
            fg=Theme.TEXT_MUTED,
            bg=Theme.BG_SIDEBAR
        )
        self.lbl_clock.pack(side=tk.RIGHT)

    def _build_tasks_tab(self, parent):
        # Bộ lọc và tìm kiếm
        filter_bar = tk.Frame(parent, bg=Theme.BG_DARK, pady=8)
        filter_bar.pack(fill=tk.X)

        # Tìm kiếm
        tk.Label(filter_bar, text="🔍 Tìm:", font=Theme.FONT_BODY, fg=Theme.TEXT_MAIN, bg=Theme.BG_DARK).pack(side=tk.LEFT, padx=(0, 4))
        self.ent_search = tk.Entry(filter_bar, font=Theme.FONT_BODY, bg=Theme.BG_INPUT, fg=Theme.TEXT_MAIN, insertbackground=Theme.TEXT_MAIN, relief="flat", width=20)
        self.ent_search.pack(side=tk.LEFT, padx=(0, 12), ipady=3)
        self.ent_search.bind("<KeyRelease>", lambda e: self._apply_filters())

        # Lọc danh mục
        tk.Label(filter_bar, text="Danh mục:", font=Theme.FONT_BODY, fg=Theme.TEXT_MAIN, bg=Theme.BG_DARK).pack(side=tk.LEFT, padx=(0, 4))
        self.cb_filter_cat = ttk.Combobox(filter_bar, values=["Tất cả"] + [c.value[0] for c in Category], state="readonly", width=12)
        self.cb_filter_cat.set("Tất cả")
        self.cb_filter_cat.pack(side=tk.LEFT, padx=(0, 12), ipady=2)
        self.cb_filter_cat.bind("<<ComboboxSelected>>", lambda e: self._apply_filters())

        # Lọc trạng thái
        tk.Label(filter_bar, text="Trạng thái:", font=Theme.FONT_BODY, fg=Theme.TEXT_MAIN, bg=Theme.BG_DARK).pack(side=tk.LEFT, padx=(0, 4))
        self.cb_filter_status = ttk.Combobox(filter_bar, values=["Tất cả"] + [s.label for s in Status], state="readonly", width=14)
        self.cb_filter_status.set("Tất cả")
        self.cb_filter_status.pack(side=tk.LEFT, padx=(0, 12), ipady=2)
        self.cb_filter_status.bind("<<ComboboxSelected>>", lambda e: self._apply_filters())

        # Nút thao tác nhanh trên task
        action_bar = tk.Frame(filter_bar, bg=Theme.BG_DARK)
        action_bar.pack(side=tk.RIGHT)

        btn_done = tk.Button(action_bar, text="✔ Hoàn thành", font=Theme.FONT_SMALL, bg=Theme.SUCCESS, fg="white", relief="flat", padx=8, pady=3, command=self._mark_selected_completed)
        btn_done.pack(side=tk.LEFT, padx=3)

        btn_edit = tk.Button(action_bar, text="✏️ Sửa", font=Theme.FONT_SMALL, bg=Theme.PRIMARY, fg="white", relief="flat", padx=8, pady=3, command=self._edit_selected_task)
        btn_edit.pack(side=tk.LEFT, padx=3)

        btn_del = tk.Button(action_bar, text="🗑️ Xóa", font=Theme.FONT_SMALL, bg=Theme.DANGER, fg="white", relief="flat", padx=8, pady=3, command=self._delete_selected_task)
        btn_del.pack(side=tk.LEFT, padx=3)

        # Bảng hiển thị danh sách (Treeview)
        tree_container = tk.Frame(parent, bg=Theme.BG_DARK)
        tree_container.pack(fill=tk.BOTH, expand=True)

        cols = ("id", "title", "category", "priority", "start", "end", "duration", "status", "deps")
        self.tree_tasks = ttk.Treeview(tree_container, columns=cols, show="headings", selectmode="browse")

        self.tree_tasks.heading("id", text="ID")
        self.tree_tasks.heading("title", text="Tiêu đề công việc")
        self.tree_tasks.heading("category", text="Danh mục")
        self.tree_tasks.heading("priority", text="Mức ưu tiên")
        self.tree_tasks.heading("start", text="Bắt đầu")
        self.tree_tasks.heading("end", text="Kết thúc")
        self.tree_tasks.heading("duration", text="Thời lượng")
        self.tree_tasks.heading("status", text="Trạng thái")
        self.tree_tasks.heading("deps", text="Tiên quyết")

        self.tree_tasks.column("id", width=65, anchor="center")
        self.tree_tasks.column("title", width=250, anchor="w")
        self.tree_tasks.column("category", width=100, anchor="center")
        self.tree_tasks.column("priority", width=105, anchor="center")
        self.tree_tasks.column("start", width=130, anchor="center")
        self.tree_tasks.column("end", width=130, anchor="center")
        self.tree_tasks.column("duration", width=85, anchor="center")
        self.tree_tasks.column("status", width=120, anchor="center")
        self.tree_tasks.column("deps", width=90, anchor="center")

        scrollbar_y = ttk.Scrollbar(tree_container, orient=tk.VERTICAL, command=self.tree_tasks.yview)
        self.tree_tasks.configure(yscrollcommand=scrollbar_y.set)

        self.tree_tasks.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar_y.pack(side=tk.RIGHT, fill=tk.Y)

        self.tree_tasks.bind("<Double-Button-1>", lambda e: self._edit_selected_task())

        # Cấu hình màu sắc hàng dựa trên priority
        self.tree_tasks.tag_configure("urgent", foreground="#F87171")
        self.tree_tasks.tag_configure("high", foreground="#FBBF24")
        self.tree_tasks.tag_configure("completed", foreground="#34D399")
        self.tree_tasks.tag_configure("normal", foreground=Theme.TEXT_MAIN)

    def _build_topo_tab(self, parent):
        box = tk.Frame(parent, bg=Theme.BG_DARK, padx=20, pady=16)
        box.pack(fill=tk.BOTH, expand=True)

        tk.Label(
            box,
            text="🔀 LẬP LỊCH THEO RÀNG BUỘC PHỤ THUỘC (TOPOLOGICAL SORT)",
            font=Theme.FONT_TITLE,
            fg=Theme.PRIMARY,
            bg=Theme.BG_DARK
        ).pack(anchor="w", pady=(0, 8))

        tk.Label(
            box,
            text="Sử dụng Thuật toán Kahn (BFS) để xác định thứ tự thực hiện hợp lệ và phát hiện chu trình phụ thuộc (Deadlock).",
            font=Theme.FONT_BODY,
            fg=Theme.TEXT_MUTED,
            bg=Theme.BG_DARK
        ).pack(anchor="w", pady=(0, 14))

        # Nút chạy lại
        top_btn_bar = tk.Frame(box, bg=Theme.BG_DARK)
        top_btn_bar.pack(fill=tk.X, pady=(0, 10))

        btn_run_topo = tk.Button(
            top_btn_bar,
            text="🔄 Chạy thuật toán Kahn Topo",
            font=Theme.FONT_SUBHEADER,
            bg=Theme.PRIMARY,
            fg="white",
            relief="flat",
            padx=12,
            pady=6,
            command=self._refresh_topo_view
        )
        btn_run_topo.pack(side=tk.LEFT)

        self.lbl_topo_status = tk.Label(top_btn_bar, text="", font=Theme.FONT_SUBHEADER, fg=Theme.SUCCESS, bg=Theme.BG_DARK)
        self.lbl_topo_status.pack(side=tk.LEFT, padx=16)

        # Danh sách kết quả Topo
        tree_frame = tk.Frame(box, bg=Theme.BG_DARK)
        tree_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 12))

        cols = ("step", "id", "title", "category", "start", "end", "deps")
        self.tree_topo = ttk.Treeview(tree_frame, columns=cols, show="headings", height=8)
        self.tree_topo.heading("step", text="Thứ tự")
        self.tree_topo.heading("id", text="Mã Task")
        self.tree_topo.heading("title", text="Tên công việc")
        self.tree_topo.heading("category", text="Danh mục")
        self.tree_topo.heading("start", text="Thời gian bắt đầu")
        self.tree_topo.heading("end", text="Thời gian kết thúc")
        self.tree_topo.heading("deps", text="Điều kiện tiên quyết")

        self.tree_topo.column("step", width=65, anchor="center")
        self.tree_topo.column("id", width=80, anchor="center")
        self.tree_topo.column("title", width=280, anchor="w")
        self.tree_topo.column("category", width=120, anchor="center")
        self.tree_topo.column("start", width=140, anchor="center")
        self.tree_topo.column("end", width=140, anchor="center")
        self.tree_topo.column("deps", width=160, anchor="center")

        self.tree_topo.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Hộp cảnh báo vi phạm thứ tự thời gian
        tk.Label(box, text="Cảnh báo mâu thuẫn thời gian giữa các công việc phụ thuộc:", font=Theme.FONT_SUBHEADER, fg=Theme.WARNING, bg=Theme.BG_DARK).pack(anchor="w", pady=(4, 4))
        self.txt_topo_warnings = tk.Text(
            box,
            height=4,
            font=Theme.FONT_BODY,
            bg=Theme.BG_INPUT,
            fg=Theme.WARNING,
            relief="flat",
            highlightthickness=1,
            highlightbackground=Theme.BORDER
        )
        self.txt_topo_warnings.pack(fill=tk.X)

    def _build_wis_tab(self, parent):
        box = tk.Frame(parent, bg=Theme.BG_DARK, padx=20, pady=16)
        box.pack(fill=tk.BOTH, expand=True)

        tk.Label(
            box,
            text="🎯 LẬP LỊCH TỐI ƯU CÓ TRỌNG SỐ (WEIGHTED INTERVAL SCHEDULING)",
            font=Theme.FONT_TITLE,
            fg=Theme.PRIMARY,
            bg=Theme.BG_DARK
        ).pack(anchor="w", pady=(0, 6))

        tk.Label(
            box,
            text="Thuật toán Quy hoạch động (Dynamic Programming - O(N log N)) tìm tập hợp các công việc KHÔNG XUNG ĐỘT có tổng điểm trọng số (Priority & Duration) lớn nhất.",
            font=Theme.FONT_BODY,
            fg=Theme.TEXT_MUTED,
            bg=Theme.BG_DARK
        ).pack(anchor="w", pady=(0, 12))

        # Thanh nút bấm và điểm tối ưu
        top_bar = tk.Frame(box, bg=Theme.BG_DARK)
        top_bar.pack(fill=tk.X, pady=(0, 10))

        btn_run_wis = tk.Button(
            top_bar,
            text="⚡ Tính toán Lập lịch Tối ưu",
            font=Theme.FONT_SUBHEADER,
            bg=Theme.PRIMARY,
            fg="white",
            relief="flat",
            padx=12,
            pady=6,
            command=self._refresh_wis_view
        )
        btn_run_wis.pack(side=tk.LEFT)

        self.lbl_wis_summary = tk.Label(
            top_bar,
            text="",
            font=Theme.FONT_SUBHEADER,
            fg=Theme.SUCCESS,
            bg=Theme.BG_DARK
        )
        self.lbl_wis_summary.pack(side=tk.LEFT, padx=16)

        # Bảng kết quả tập công việc được chọn
        tree_frame = tk.Frame(box, bg=Theme.BG_DARK)
        tree_frame.pack(fill=tk.BOTH, expand=True)

        cols = ("id", "title", "category", "priority", "start", "end", "duration", "status")
        self.tree_wis = ttk.Treeview(tree_frame, columns=cols, show="headings")

        self.tree_wis.heading("id", text="ID")
        self.tree_wis.heading("title", text="Tiêu đề công việc được chọn")
        self.tree_wis.heading("category", text="Danh mục")
        self.tree_wis.heading("priority", text="Mức ưu tiên")
        self.tree_wis.heading("start", text="Bắt đầu")
        self.tree_wis.heading("end", text="Kết thúc")
        self.tree_wis.heading("duration", text="Thời lượng")
        self.tree_wis.heading("status", text="Trạng thái")

        self.tree_wis.column("id", width=65, anchor="center")
        self.tree_wis.column("title", width=280, anchor="w")
        self.tree_wis.column("category", width=120, anchor="center")
        self.tree_wis.column("priority", width=110, anchor="center")
        self.tree_wis.column("start", width=140, anchor="center")
        self.tree_wis.column("end", width=140, anchor="center")
        self.tree_wis.column("duration", width=95, anchor="center")
        self.tree_wis.column("status", width=120, anchor="center")

        self.tree_wis.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

    def _load_data(self):
        self.tasks = self.storage.load_all_tasks()
        if not self.tasks:
            self.tasks = self.storage.seed_sample_data()
        self._apply_filters()
        self._update_all_views()

    def _apply_filters(self):
        query = self.ent_search.get().strip().lower()
        cat_filter = self.cb_filter_cat.get()
        status_filter = self.cb_filter_status.get()

        for row in self.tree_tasks.get_children():
            self.tree_tasks.delete(row)

        for t in self.tasks:
            # Lọc theo từ khóa
            if query and query not in t.title.lower() and query not in t.description.lower():
                continue
            # Lọc danh mục
            if cat_filter != "Tất cả" and t.category != cat_filter:
                continue
            # Lọc trạng thái
            if status_filter != "Tất cả" and t.status.label != status_filter:
                continue

            tag = "normal"
            if t.status == Status.COMPLETED:
                tag = "completed"
            elif t.priority == Priority.URGENT:
                tag = "urgent"
            elif t.priority == Priority.HIGH:
                tag = "high"

            deps_str = ", ".join(t.dependencies) if t.dependencies else "-"

            self.tree_tasks.insert(
                "",
                "end",
                iid=t.id,
                values=(
                    t.id,
                    t.title,
                    t.category,
                    t.priority.label,
                    t.start_time.strftime("%d/%m %H:%M"),
                    t.end_time.strftime("%d/%m %H:%M"),
                    f"{t.duration_minutes}m",
                    t.status.label,
                    deps_str
                ),
                tags=(tag,)
            )

        # Cập nhật thanh trạng thái
        conflicts = SchedulerEngine.detect_all_conflicts(self.tasks)
        self.lbl_status.config(text=f"Tổng số công việc: {len(self.tasks)} | Số xung đột thời gian: {len(conflicts)}")

    def _update_all_views(self):
        self.tab_eisenhower.update_tasks(self.tasks)
        self.tab_analytics.update_tasks(self.tasks)
        self._refresh_topo_view()
        self._refresh_wis_view()

    def _on_tab_changed(self, event):
        tab_idx = self.notebook.index(self.notebook.select())
        if tab_idx == 1:
            self.tab_eisenhower.update_tasks(self.tasks)
        elif tab_idx == 2:
            self.tab_analytics.update_tasks(self.tasks)
        elif tab_idx == 3:
            self._refresh_topo_view()
        elif tab_idx == 4:
            self._refresh_wis_view()

    def _open_add_dialog(self, default_start: Optional[datetime] = None):
        def _on_save(new_task: Task):
            self.storage.save_task(new_task)
            self._load_data()
            messagebox.showinfo("Thành công", f"Đã lưu công việc: '{new_task.title}'", parent=self)

        TaskDialog(self, all_tasks=self.tasks, on_save=_on_save, default_start=default_start)

    def _open_edit_dialog(self, task: Task):
        def _on_save(updated_task: Task):
            self.storage.save_task(updated_task)
            self._load_data()
            messagebox.showinfo("Thành công", f"Đã cập nhật công việc: '{updated_task.title}'", parent=self)

        TaskDialog(self, all_tasks=self.tasks, task=task, on_save=_on_save)

    def _edit_selected_task(self):
        selected = self.tree_tasks.selection()
        if not selected:
            messagebox.showwarning("Chưa chọn", "Vui lòng chọn một công việc trong bảng để chỉnh sửa!", parent=self)
            return
        task_id = selected[0]
        task = self.storage.get_task_by_id(task_id)
        if task:
            self._open_edit_dialog(task)

    def _delete_selected_task(self):
        selected = self.tree_tasks.selection()
        if not selected:
            messagebox.showwarning("Chưa chọn", "Vui lòng chọn một công việc để xóa!", parent=self)
            return
        task_id = selected[0]
        confirm = messagebox.askyesno("Xác nhận xóa", f"Bạn có chắc muốn xóa công việc có mã '{task_id}'?", parent=self)
        if confirm:
            self.storage.delete_task(task_id)
            self._load_data()

    def _mark_selected_completed(self):
        selected = self.tree_tasks.selection()
        if not selected:
            messagebox.showwarning("Chưa chọn", "Vui lòng chọn một công việc để đánh dấu hoàn thành!", parent=self)
            return
        task_id = selected[0]
        task = self.storage.get_task_by_id(task_id)
        if task:
            task.status = Status.COMPLETED
            self.storage.save_task(task)
            self._load_data()

    def _open_smart_slot_dialog(self):
        def _on_slot_selected(start_time: datetime, end_time: datetime, duration: int):
            self._open_add_dialog(default_start=start_time)

        SmartSlotDialog(self, all_tasks=self.tasks, on_slot_selected=_on_slot_selected)

    def _show_conflicts_modal(self):
        conflicts = SchedulerEngine.detect_all_conflicts(self.tasks)
        if not conflicts:
            messagebox.showinfo("Kiểm tra xung đột", "Tuyệt vời! Không phát hiện bất kỳ xung đột lịch trình nào.", parent=self)
            return

        # Tạo modal hiển thị chi tiết các xung đột
        modal = tk.Toplevel(self)
        modal.title(f"⚠️ Phát hiện {len(conflicts)} xung đột lịch trình")
        modal.geometry("640x450")
        modal.configure(bg=Theme.BG_DARK)
        modal.transient(self)
        modal.grab_set()

        p = tk.Frame(modal, bg=Theme.BG_DARK, padx=16, pady=14)
        p.pack(fill=tk.BOTH, expand=True)

        tk.Label(p, text="DANH SÁCH CÁC CẶP CÔNG VIỆC XUNG ĐỘT THỜI GIAN", font=Theme.FONT_SUBHEADER, fg=Theme.DANGER, bg=Theme.BG_DARK).pack(anchor="w", pady=(0, 10))

        tree_f = tk.Frame(p, bg=Theme.BG_DARK)
        tree_f.pack(fill=tk.BOTH, expand=True, pady=(0, 12))

        cols = ("task1", "task2", "overlap", "duration")
        tree = ttk.Treeview(tree_f, columns=cols, show="headings")
        tree.heading("task1", text="Công việc 1")
        tree.heading("task2", text="Công việc 2")
        tree.heading("overlap", text="Khung giờ trùng")
        tree.heading("duration", text="Số phút trùng")

        tree.column("task1", width=180, anchor="w")
        tree.column("task2", width=180, anchor="w")
        tree.column("overlap", width=140, anchor="center")
        tree.column("duration", width=90, anchor="center")

        for c in conflicts:
            overlap_str = f"{c.overlap_start.strftime('%d/%m %H:%M')} - {c.overlap_end.strftime('%H:%M')}"
            tree.insert("", "end", values=(c.task1.title, c.task2.title, overlap_str, f"{c.overlap_minutes}m"))

        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        tk.Button(p, text="Đóng", font=Theme.FONT_BODY, bg=Theme.BG_CARD, fg=Theme.TEXT_MAIN, relief="flat", padx=16, pady=6, command=modal.destroy).pack(side=tk.RIGHT)

    def _refresh_topo_view(self):
        for row in self.tree_topo.get_children():
            self.tree_topo.delete(row)
        self.txt_topo_warnings.delete("1.0", tk.END)

        if not self.tasks:
            return

        try:
            sorted_tasks, warnings = SchedulerEngine.topological_sort(self.tasks)
            self.lbl_topo_status.config(text=f"✅ Hợp lệ (DAG không chu trình - {len(sorted_tasks)} công việc)", fg=Theme.SUCCESS)

            for idx, t in enumerate(sorted_tasks):
                deps_str = ", ".join(t.dependencies) if t.dependencies else "Không (Gốc)"
                self.tree_topo.insert("", "end", values=(
                    idx + 1,
                    t.id,
                    t.title,
                    t.category,
                    t.start_time.strftime("%d/%m %H:%M"),
                    t.end_time.strftime("%d/%m %H:%M"),
                    deps_str
                ))

            if warnings:
                self.txt_topo_warnings.insert("1.0", "\n".join(warnings))
            else:
                self.txt_topo_warnings.insert("1.0", "Không có vi phạm thứ tự thời gian giữa các công việc phụ thuộc.")
        except ValueError as e:
            self.lbl_topo_status.config(text="❌ PHÁT HIỆN CHU TRÌNH PHỤ THUỘC (DEADLOCK)", fg=Theme.DANGER)
            self.txt_topo_warnings.insert("1.0", f"LỖI: {str(e)}")

    def _refresh_wis_view(self):
        for row in self.tree_wis.get_children():
            self.tree_wis.delete(row)

        if not self.tasks:
            return

        max_weight, optimal_tasks = SchedulerEngine.weighted_interval_scheduling(self.tasks)
        self.lbl_wis_summary.config(
            text=f"Tối ưu: Đã chọn {len(optimal_tasks)}/{len(self.tasks)} công việc không xung đột (Tổng điểm trọng số: {max_weight:.1f})",
            fg=Theme.SUCCESS
        )

        for t in optimal_tasks:
            self.tree_wis.insert("", "end", values=(
                t.id,
                t.title,
                t.category,
                t.priority.label,
                t.start_time.strftime("%d/%m %H:%M"),
                t.end_time.strftime("%d/%m %H:%M"),
                f"{t.duration_minutes}m",
                t.status.label
            ))

    def _seed_sample_action(self):
        confirm = messagebox.askyesno("Nạp dữ liệu mẫu", "Thao tác này sẽ nạp thêm bộ công việc mẫu thực tế vào cơ sở dữ liệu. Bạn có muốn tiếp tục?", parent=self)
        if confirm:
            self.storage.seed_sample_data()
            self._load_data()
            messagebox.showinfo("Thành công", "Đã nạp thành công bộ dữ liệu mẫu!", parent=self)
