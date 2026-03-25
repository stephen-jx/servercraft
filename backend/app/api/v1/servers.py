"""Server API endpoints."""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, WebSocket, WebSocketDisconnect
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from datetime import datetime

from ...core import get_db
from ...core.auth import require_auth, require_admin
from ...models import Server, ServerStatus, ServerComponent, Task, TaskType, TaskStatus, User
from ...services.ssh_executor import SSHExecutor
from ...services.task_runner import run_task_background

router = APIRouter(prefix="/servers", tags=["servers"])


# === Schemas ===
class ServerCreate(BaseModel):
    name: str
    ip_address: str
    port: int = 22
    username: str = "root"
    password: Optional[str] = None
    ssh_key: Optional[str] = None
    description: Optional[str] = None
    tags: Optional[str] = None


class ServerUpdate(BaseModel):
    name: Optional[str] = None
    port: Optional[int] = None
    username: Optional[str] = None
    password: Optional[str] = None
    ssh_key: Optional[str] = None
    description: Optional[str] = None
    tags: Optional[str] = None


class ServerResponse(BaseModel):
    id: int
    name: str
    ip_address: str
    port: int
    username: str
    os_type: Optional[str]
    os_version: Optional[str]
    arch: Optional[str]
    cpu_cores: Optional[int]
    memory_mb: Optional[int]
    disk_gb: Optional[int]
    status: str
    description: Optional[str]
    tags: Optional[str]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class InstallRequest(BaseModel):
    components: list[str]
    options: Optional[dict] = None  # component-specific options


class InstallResponse(BaseModel):
    task_id: int
    status: str
    message: str


# === Endpoints ===
@router.post("", response_model=ServerResponse, status_code=201)
async def create_server(
    data: ServerCreate,
    user: User = Depends(require_auth),
    db: AsyncSession = Depends(get_db)
):
    """Add a new server."""
    # Check duplicate IP
    result = await db.execute(
        select(Server).where(Server.ip_address == data.ip_address)
    )
    if result.scalar_one_or_none():
        raise HTTPException(400, "Server with this IP already exists")
    
    server = Server(**data.model_dump())
    server.status = ServerStatus.PENDING
    db.add(server)
    await db.commit()
    await db.refresh(server)
    return server


@router.get("", response_model=dict)
async def list_servers(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    status: Optional[str] = None,
    search: Optional[str] = None,
    user: User = Depends(require_auth),
    db: AsyncSession = Depends(get_db)
):
    """List all servers."""
    query = select(Server)
    count_query = select(func.count(Server.id))
    
    if status:
        query = query.where(Server.status == status)
        count_query = count_query.where(Server.status == status)
    
    if search:
        from sqlalchemy import or_
        query = query.where(or_(
            Server.name.ilike(f"%{search}%"),
            Server.ip_address.ilike(f"%{search}%")
        ))
        count_query = count_query.where(or_(
            Server.name.ilike(f"%{search}%"),
            Server.ip_address.ilike(f"%{search}%")
        ))
    
    # Get total
    total = (await db.execute(count_query)).scalar()
    
    # Get paginated
    query = query.order_by(Server.created_at.desc()).offset(skip).limit(limit)
    servers = (await db.execute(query)).scalars().all()
    
    return {"total": total, "items": servers}


@router.get("/{server_id}", response_model=ServerResponse)
async def get_server(
    server_id: int, 
    user: User = Depends(require_auth),
    db: AsyncSession = Depends(get_db)
):
    """Get server details."""
    result = await db.execute(
        select(Server).where(Server.id == server_id)
    )
    server = result.scalar_one_or_none()
    if not server:
        raise HTTPException(404, "Server not found")
    return server


@router.put("/{server_id}", response_model=ServerResponse)
async def update_server(
    server_id: int,
    data: ServerUpdate,
    user: User = Depends(require_auth),
    db: AsyncSession = Depends(get_db)
):
    """Update server."""
    result = await db.execute(
        select(Server).where(Server.id == server_id)
    )
    server = result.scalar_one_or_none()
    if not server:
        raise HTTPException(404, "Server not found")
    
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(server, key, value)
    
    await db.commit()
    await db.refresh(server)
    return server


@router.delete("/{server_id}", status_code=204)
async def delete_server(
    server_id: int, 
    user: User = Depends(require_auth),
    db: AsyncSession = Depends(get_db)
):
    """Delete a server."""
    result = await db.execute(
        select(Server).where(Server.id == server_id)
    )
    server = result.scalar_one_or_none()
    if not server:
        raise HTTPException(404, "Server not found")
    
    await db.delete(server)
    await db.commit()


@router.post("/{server_id}/test")
async def test_connection(
    server_id: int, 
    user: User = Depends(require_auth),
    db: AsyncSession = Depends(get_db)
):
    """Test server connection."""
    result = await db.execute(
        select(Server).where(Server.id == server_id)
    )
    server = result.scalar_one_or_none()
    if not server:
        raise HTTPException(404, "Server not found")
    
    try:
        executor = SSHExecutor(
            host=server.ip_address,
            port=server.port,
            username=server.username,
            password=server.password,
            ssh_key=server.ssh_key
        )
        await executor.connect()
        
        # Get system info
        info = await executor.get_system_info()
        
        # Update server
        server.os_type = info["os_type"]
        server.os_version = info["os_version"]
        server.arch = info["arch"]
        server.cpu_cores = info["cpu_cores"]
        server.memory_mb = info["memory_mb"]
        server.disk_gb = info["disk_gb"]
        server.status = ServerStatus.CONNECTED
        server.last_check_at = datetime.utcnow()
        server.error_message = None
        
        await executor.disconnect()
        await db.commit()
        
        return {"success": True, "system_info": info}
        
    except Exception as e:
        server.status = ServerStatus.FAILED
        server.error_message = str(e)
        await db.commit()
        return {"success": False, "error": str(e)}


@router.post("/{server_id}/detect")
async def detect_environment(
    server_id: int, 
    user: User = Depends(require_auth),
    db: AsyncSession = Depends(get_db)
):
    """Detect server environment and installed software."""
    result = await db.execute(
        select(Server).where(Server.id == server_id)
    )
    server = result.scalar_one_or_none()
    if not server:
        raise HTTPException(404, "Server not found")
    
    executor = SSHExecutor(
        host=server.ip_address,
        port=server.port,
        username=server.username,
        password=server.password,
        ssh_key=server.ssh_key
    )
    
    try:
        await executor.connect()
        
        # Detect installed software
        installed = {}
        
        # Check common tools
        checks = [
            ("docker", "docker --version"),
            ("nginx", "nginx -v 2>&1"),
            ("mysql", "mysql --version"),
            ("redis", "redis-server --version"),
            ("node", "node --version"),
            ("python", "python3 --version"),
            ("go", "go version"),
            ("git", "git --version"),
        ]
        
        for name, cmd in checks:
            r = await executor.execute(cmd)
            if r.success:
                installed[name] = r.stdout.strip()
        
        await executor.disconnect()
        
        return {
            "success": True,
            "installed": installed,
            "os": {
                "type": server.os_type,
                "version": server.os_version,
                "arch": server.arch
            }
        }
        
    except Exception as e:
        return {"success": False, "error": str(e)}


@router.post("/{server_id}/install", response_model=InstallResponse)
async def install_components(
    server_id: int,
    data: InstallRequest,
    user: User = Depends(require_auth),
    db: AsyncSession = Depends(get_db)
):
    """Install components on server (parallel)."""
    result = await db.execute(
        select(Server).where(Server.id == server_id)
    )
    server = result.scalar_one_or_none()
    if not server:
        raise HTTPException(404, "Server not found")
    
    # Create task
    import json
    task = Task(
        task_type=TaskType.INSTALL,
        server_id=server_id,
        component_names=json.dumps(data.components),
        options=data.options,
        status=TaskStatus.PENDING
    )
    db.add(task)
    await db.commit()
    await db.refresh(task)
    
    # Run task in background
    from ..services.task_runner import run_task_background
    await run_task_background(db, task.id)
    
    return InstallResponse(
        task_id=task.id,
        status="pending",
        message=f"Installing {len(data.components)} components in parallel"
    )


@router.get("/{server_id}/components")
async def get_installed_components(server_id: int, db: AsyncSession = Depends(get_db)):
    """Get installed components on server."""
    result = await db.execute(
        select(ServerComponent).where(ServerComponent.server_id == server_id)
    )
    components = result.scalars().all()
    return {"items": components}


@router.get("/{server_id}/tasks")
async def get_server_tasks(
    server_id: int,
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
):
    """Get task history for server."""
    result = await db.execute(
        select(Task)
        .where(Task.server_id == server_id)
        .order_by(Task.created_at.desc())
        .limit(limit)
    )
    tasks = result.scalars().all()
    return {"items": tasks}