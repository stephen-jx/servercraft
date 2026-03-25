"""Task model for installation tasks."""
from datetime import datetime
from sqlalchemy import String, Text, Boolean, DateTime, Integer, ForeignKey, Enum as SQLEnum, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import Optional, List, Any
import enum

from ..core.database import Base


class TaskStatus(str, enum.Enum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TaskType(str, enum.Enum):
    INSTALL = "install"
    UNINSTALL = "uninstall"
    CONFIGURE = "configure"
    START = "start"
    STOP = "stop"
    RESTART = "restart"
    UPGRADE = "upgrade"


class Task(Base):
    """Task model."""
    __tablename__ = "tasks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    
    # Task info
    task_type: Mapped[TaskType] = mapped_column(SQLEnum(TaskType), nullable=False)
    component_names: Mapped[Optional[str]] = mapped_column(String(500))  # JSON list for parallel install
    
    # Server
    server_id: Mapped[int] = mapped_column(Integer, ForeignKey("servers.id", ondelete="CASCADE"))
    
    # Status
    status: Mapped[TaskStatus] = mapped_column(SQLEnum(TaskStatus), default=TaskStatus.PENDING)
    progress: Mapped[int] = mapped_column(Integer, default=0)  # 0-100
    current_step: Mapped[Optional[str]] = mapped_column(String(255))
    
    # Timing
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    duration_seconds: Mapped[Optional[int]] = mapped_column(Integer)
    
    # Results
    output: Mapped[Optional[str]] = mapped_column(Text)
    error_message: Mapped[Optional[str]] = mapped_column(Text)
    
    # Options (JSON)
    options: Mapped[Optional[str]] = mapped_column(JSON)  # component-specific options
    
    # Celery task
    celery_task_id: Mapped[Optional[str]] = mapped_column(String(100))
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    server: Mapped["Server"] = relationship("Server", back_populates="tasks")
    subtasks: Mapped[List["SubTask"]] = relationship("SubTask", back_populates="task", cascade="all, delete-orphan")


class SubTask(Base):
    """Sub-task for parallel component installation."""
    __tablename__ = "subtasks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    task_id: Mapped[int] = mapped_column(Integer, ForeignKey("tasks.id", ondelete="CASCADE"))
    
    component_name: Mapped[str] = mapped_column(String(100), nullable=False)
    status: Mapped[TaskStatus] = mapped_column(SQLEnum(TaskStatus), default=TaskStatus.PENDING)
    
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    
    output: Mapped[Optional[str]] = mapped_column(Text)
    error_message: Mapped[Optional[str]] = mapped_column(Text)
    
    # Relationship
    task: Mapped["Task"] = relationship("Task", back_populates="subtasks")