"""
ui/theme.py
Bộ thiết lập giao diện đồ họa hiện đại, màu sắc và typography.
Phong cách giao diện Clean Modern Dark / Light phối màu tối ưu.
"""

class Theme:
    # Bảng màu chủ đạo (Modern Dark Palette)
    BG_DARK = "#1E1E2E"          # Nền chính ứng dụng
    BG_SIDEBAR = "#181825"       # Nền sidebar / thanh công cụ
    BG_CARD = "#252538"          # Nền các thẻ card, container
    BG_CARD_HOVER = "#2F2F45"    # Khi rê chuột vào card
    BG_INPUT = "#313244"         # Nền ô nhập liệu
    
    # Màu chữ
    TEXT_MAIN = "#F8FAFC"        # Chữ sáng chính (gần trắng)
    TEXT_MUTED = "#94A3B8"       # Chữ phụ mờ (xám nhạt)
    TEXT_DARK = "#1E293B"        # Chữ tối khi dùng trên nền sáng
    
    # Màu điểm nhấn (Accents)
    PRIMARY = "#3B82F6"          # Xanh dương hiện đại (Blue-500)
    PRIMARY_HOVER = "#2563EB"
    SUCCESS = "#10B981"          # Xanh lá ngọc (Emerald-500)
    WARNING = "#F59E0B"          # Vàng hổ phách (Amber-500)
    DANGER = "#EF4444"           # Đỏ san hô (Red-500)
    PURPLE = "#8B5CF6"           # Tím thạch anh (Purple-500)
    INFO = "#06B6D4"             # Xanh lam (Cyan-500)
    
    # Viền và ngăn cách
    BORDER = "#3E3F59"
    BORDER_LIGHT = "#4B4C68"

    # Font chữ hệ thống
    FONT_FAMILY = "Segoe UI"
    FONT_TITLE = ("Segoe UI", 16, "bold")
    FONT_HEADER = ("Segoe UI", 12, "bold")
    FONT_SUBHEADER = ("Segoe UI", 11, "bold")
    FONT_BODY = ("Segoe UI", 10)
    FONT_SMALL = ("Segoe UI", 9)
    FONT_CODE = ("Consolas", 10)
