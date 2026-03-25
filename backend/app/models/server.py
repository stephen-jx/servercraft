"""Server model."""
from datetime import datetime
from sqlalchemy import String, Text, Boolean, DateTime, Integer, Enum as SQLEnum, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import Optional, List
import enum

from ..core.database import Base


class ServerStatus(str, enum.Enum):
    PENDING = "pending"
    CONNECTED = "connected"
    FAILED = "failed"
    BUSY = "busy"


class Server(Base):
    """Server model."""
    __tablename__ = "servers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    
    # Basic info
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    ip_address: Mapped[str] = mapped_column(String(45), nullable=False, unique=True)
    port: Mapped[int] = mapped_column(Integer, default=22)
    
    # Authentication
    auth_type: Mapped[str] = mapped_column(String(20), default="password")  # password, key
    username: Mapped[str] = mapped_column(String(255), default="root")
    password: Mapped[Optional[str]] = mapped_column(String(255))
    ssh_key: Mapped[Optional[str]] = mapped_column(Text)
    
    # System info (detected)
    os_type: Mapped[Optional[str]] = mapped_column(String(50))  # ubuntu, centos, debian
    os_version: Mapped[Optional[str]] = mapped_column(String(50))
    arch: Mapped[Optional[str]] = mapped_column(String(20))
    cpu_cores: Mapped[Optional[int]] = mapped_column(Integer)
    memory_mb: Mapped[Optional[int]] = mapped_column(Integer)
    disk_gb: Mapped[Optional[int]] = mapped_column(Integer)
    
    # Status
    status: Mapped[ServerStatus] = mapped_column(SQLEnum(ServerStatus), default=ServerStatus.PENDING)
    last_check_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    error_message: Mapped[Optional[str]] = mapped_column(Text)
    
    # Metadata
    description: Mapped[Optional[str]] = mapped_column(Text)
    tags: Mapped[Optional[str]] = mapped_column(String(500))
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    tasks: Mapped[List["Task"]] = relationship("Task", back_populates="server", cascade="all, delete-orphan")
    installed_components: Mapped[List["ServerComponent"]] = relationship("ServerComponent", back_populates="server", cascade="all, delete-orphan")


class ServerComponent(Base):
    """Installed components on a server."""
    __tablename__ = "server_components"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    server_id: Mapped[int] = mapped_column(Integer, ForeignKey("servers.id"), nullable=False, index=True)
    component_name: Mapped[str] = mapped_column(String(100), nullable=False)
    component_version: Mapped[Optional[str]] = mapped_column(String(50))
    status: Mapped[str] = mapped_column(String(20), default="installed")  # installed, running, stopped, failed
    install_path: Mapped[Optional[str]] = mapped_column(String(500))
    config_path: Mapped[Optional[str]] = mapped_column(String(500))
    installed_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    # Relationship
    server: Mapped["Server"] = relationship("Server", back_populates="installed_components")