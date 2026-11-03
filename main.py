"""
main.py
Điểm khởi chạy chương trình Quản lý Lịch làm việc Cá nhân.
"""

import sys
from ui.main_window import MainWindow

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

def main():
    app = MainWindow()
    app.mainloop()

if __name__ == "__main__":
    main()
