"""Application configuration."""
import os
import secrets
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings."""
    
    # Application
    APP_NAME: str = "ServerCraft"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    
    # Database
    DATABASE_URL: str = "sqlite+aiosqlite:///./servercraft.db"
    
    # Redis (for Celery)
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # Security
    # 生产环境必须设置 SECRET_KEY 环境变量
    SECRET_KEY: str = os.environ.get("SECRET_KEY") or secrets.token_urlsafe(32)
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24
    
    # SSH defaults
    SSH_TIMEOUT: int = 30
    SSH_PORT: int = 22
    
    # Ansible
    ANSIBLE_TIMEOUT: int = 3600  # 1 hour
    
    # Paths
    ANSIBLE_PLAYBOOKS_PATH: str = "./ansible/playbooks"
    ANSIBLE_ROLES_PATH: str = "./ansible/roles"
    
    class Config:
        env_file = ".env"
        case_sensitive = True
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # 检查生产环境
        if not self.DEBUG and self.SECRET_KEY == "change-this-in-production":
            import warnings
            warnings.warn(
                "使用默认 SECRET_KEY 在生产环境不安全！请设置 SECRET_KEY 环境变量。"
            )


settings = Settings()