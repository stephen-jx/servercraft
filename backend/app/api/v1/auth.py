"""Authentication API endpoints."""
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel

from ...core import get_db
from ...core.auth import (
    verify_password, get_password_hash, create_access_token,
    get_current_user, require_auth, require_admin
)
from ...models import User
from ...core.config import settings

router = APIRouter(prefix="/auth", tags=["auth"])


# === Schemas ===
class UserCreate(BaseModel):
    username: str
    password: str
    email: str | None = None


class UserResponse(BaseModel):
    id: int
    username: str
    email: str | None
    is_active: bool
    is_admin: bool
    last_login: datetime | None
    created_at: datetime

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str
    user: UserResponse


class PasswordChange(BaseModel):
    old_password: str
    new_password: str


# === Endpoints ===
@router.post("/login", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db)
):
    """Login and get access token."""
    result = await db.execute(
        select(User).where(User.username == form_data.username)
    )
    user = result.scalar_one_or_none()
    
    if not user or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is disabled"
        )
    
    # Update last login
    user.last_login = datetime.utcnow()
    await db.commit()
    
    # Create token
    access_token = create_access_token(
        data={"sub": user.username},
        expires_delta=None  # Use default
    )
    
    return Token(
        access_token=access_token,
        token_type="bearer",
        user=UserResponse.model_validate(user)
    )


@router.get("/me", response_model=UserResponse)
async def get_me(user: User = Depends(require_auth)):
    """Get current user info."""
    return UserResponse.model_validate(user)


@router.post("/change-password")
async def change_password(
    data: PasswordChange,
    user: User = Depends(require_auth),
    db: AsyncSession = Depends(get_db)
):
    """Change user password."""
    if not verify_password(data.old_password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect old password"
        )
    
    user.password_hash = get_password_hash(data.new_password)
    await db.commit()
    
    return {"success": True, "message": "Password changed"}


@router.post("/register", response_model=UserResponse, status_code=201)
async def register(
    data: UserCreate,
    db: AsyncSession = Depends(get_db)
):
    """Register a new user.
    
    安全策略:
    - 第一个用户自动成为管理员
    - 如果已存在用户，需要管理员邀请码 (未来实现)
    - 当前版本: 仅允许第一个用户注册
    """
    # 检查是否已有用户存在
    result = await db.execute(select(User).limit(1))
    first_user = result.scalar_one_or_none()
    
    # 如果已有用户，禁止公开注册
    if first_user is not None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Registration is disabled. Please contact administrator."
        )
    
    # Check username exists
    result = await db.execute(
        select(User).where(User.username == data.username)
    )
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )
    
    # Create user
    user = User(
        username=data.username,
        password_hash=get_password_hash(data.password),
        email=data.email,
        is_admin=True,  # First user is admin
        is_active=True,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    
    return UserResponse.model_validate(user)


@router.post("/logout")
async def logout(user: User = Depends(require_auth)):
    """Logout (client should discard token)."""
    return {"success": True, "message": "Logged out"}


# === Admin endpoints ===
@router.get("/users", response_model=list[UserResponse])
async def list_users(
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """List all users (admin only)."""
    result = await db.execute(select(User))
    users = result.scalars().all()
    return [UserResponse.model_validate(u) for u in users]


@router.delete("/users/{user_id}")
async def delete_user(
    user_id: int,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """Delete a user (admin only)."""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if user.id == admin.id:
        raise HTTPException(status_code=400, detail="Cannot delete yourself")
    
    await db.delete(user)
    await db.commit()
    
    return {"success": True, "message": "User deleted"}