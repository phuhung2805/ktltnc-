"""
core/models.py
Định nghĩa các mô hình dữ liệu chính cho hệ thống quản lý lịch làm việc cá nhân.
"""

from datetime import datetime
from enum import Enum
import uuid
from typing import List, Dict, Any, Optional


class Priority(Enum):
    LOW = (1, "Thấp", "#10B981")       # Xanh lá
    MEDIUM = (2, "Vừa", "#3B82F6")     # Xanh dương
    HIGH = (3, "Cao", "#F59E0B")       # Vàng cam
    URGENT = (4, "Khẩn cấp", "#EF4444")# Đỏ

    def __init__(self, level: int, label: str, color: str):
        self.level = level
        self.label = label
        self.color = color

    @classmethod
    def from_string(cls, value: str):
        for item in cls:
            if item.name.lower() == value.lower() or item.label.lower() == value.lower() or str(item.level) == str(value):
                return item
        return cls.MEDIUM


class Status(Enum):
    PENDING = ("Chưa bắt đầu", "#94A3B8")
    IN_PROGRESS = ("Đang thực hiện", "#3B82F6")
    COMPLETED = ("Đã hoàn thành", "#10B981")
    CANCELLED = ("Đã hủy", "#64748B")

    def __init__(self, label: str, color: str):
        self.label = label
        self.color = color

    @classmethod
    def from_string(cls, value: str):
        for item in cls:
            if item.name.lower() == value.lower() or item.label.lower() == value.lower():
                return item
        return cls.PENDING


class Category(Enum):
    WORK = ("Công việc", "#6366F1")
    STUDY = ("Học tập", "#8B5CF6")
    PERSONAL = ("Cá nhân", "#EC4899")
    HEALTH = ("Sức khỏe", "#14B8A6")
    MEETING = ("Họp hành", "#F97316")
    OTHER = ("Khác", "#64748B")

    def __init__(self, label: str, color: str):
        self.label = label
        self.color = color

    @classmethod
    def from_string(cls, value: str):
        for item in cls:
            if item.name.lower() == value.lower() or item.label.lower() == value.lower():
                return item
        return cls.OTHER


class Task:
    """
    Thực thể công việc / sự kiện trong lịch trình cá nhân.
    """
    def __init__(
        self,
        title: str,
        start_time: datetime,
        end_time: datetime,
        id: Optional[str] = None,
        description: str = "",
        category: str = "Công việc",
        priority: Priority = Priority.MEDIUM,
        status: Status = Status.PENDING,
        dependencies: Optional[List[str]] = None,
        created_at: Optional[datetime] = None
    ):
        if end_time <= start_time:
            raise ValueError("Thời gian kết thúc phải lớn hơn thời gian bắt đầu.")

        self.id = id or str(uuid.uuid4())[:8]
        self.title = title.strip()
        self.description = description.strip()
        self.start_time = start_time
        self.end_time = end_time
        self.category = category
        self.priority = priority if isinstance(priority, Priority) else Priority.from_string(str(priority))
        self.status = status if isinstance(status, Status) else Status.from_string(str(status))
        self.dependencies = dependencies or []
        self.created_at = created_at or datetime.now()

    @property
    def duration_minutes(self) -> int:
        """Thời lượng công việc tính theo phút."""
        return int((self.end_time - self.start_time).total_seconds() / 60)

    @property
    def duration_hours(self) -> float:
        """Thời lượng tính theo giờ."""
        return round(self.duration_minutes / 60.0, 2)

    @property
    def is_active(self) -> bool:
        """Công việc còn phải làm (chưa hoàn thành và chưa bị hủy)."""
        return self.status in (Status.PENDING, Status.IN_PROGRESS)

    def is_overlapping_with(self, other: 'Task') -> bool:
        """
        Kiểm tra 2 công việc có giao thoa về mặt thời gian hay không.
        Hai khoảng thời gian [S1, E1) và [S2, E2) giao thoa khi và chỉ khi:
            max(S1, S2) < min(E1, E2)
        """
        if self.id == other.id:
            return False
        return max(self.start_time, other.start_time) < min(self.end_time, other.end_time)

    def is_overdue(self, current_time: Optional[datetime] = None) -> bool:
        """Kiểm tra công việc đã quá hạn chưa."""
        now = current_time or datetime.now()
        return self.is_active and self.end_time < now

    def to_dict(self) -> Dict[str, Any]:
        """Chuyển đổi thành từ điển JSON-serializable."""
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "start_time": self.start_time.strftime("%Y-%m-%d %H:%M"),
            "end_time": self.end_time.strftime("%Y-%m-%d %H:%M"),
            "category": self.category,
            "priority": self.priority.name,
            "status": self.status.name,
            "dependencies": self.dependencies,
            "created_at": self.created_at.strftime("%Y-%m-%d %H:%M:%S")
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Task':
        """Khởi tạo đối tượng từ từ điển."""
        return cls(
            id=data.get("id"),
            title=data.get("title", "Không có tiêu đề"),
            description=data.get("description", ""),
            start_time=datetime.strptime(data["start_time"], "%Y-%m-%d %H:%M"),
            end_time=datetime.strptime(data["end_time"], "%Y-%m-%d %H:%M"),
            category=data.get("category", "Công việc"),
            priority=Priority.from_string(data.get("priority", "MEDIUM")),
            status=Status.from_string(data.get("status", "PENDING")),
            dependencies=data.get("dependencies", []),
            created_at=datetime.strptime(data["created_at"], "%Y-%m-%d %H:%M:%S") if "created_at" in data else None
        )

    def __repr__(self) -> str:
        return f"<Task {self.id}: '{self.title}' ({self.start_time.strftime('%H:%M')} - {self.end_time.strftime('%H:%M')})>"
