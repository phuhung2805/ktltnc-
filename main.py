"""
main.py
Điểm khởi chạy chương trình Quản lý Lịch làm việc Cá nhân.
"""

import os
import sys
from ui.main_window import MainWindow

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

# Đặt CSDL cạnh mã nguồn để chạy từ thư mục nào cũng dùng chung một lịch
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "schedule.db")

def main():
    app = MainWindow(db_path=DB_PATH)
    app.mainloop()

if __name__ == "__main__":
    main()
