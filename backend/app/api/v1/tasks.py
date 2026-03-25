"""Task API endpoints."""
from fastapi import APIRouter, Depends, HTTPException, Query, WebSocket, WebSocketDisconnect
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime
import json

from ...core import get_db
from ...core.auth import require_auth
from ...models import Task, TaskStatus, SubTask, User

router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.get("")
async def list_tasks(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    server_id: int = None,
    status: str = None,
    user: User = Depends(require_auth),
    db: AsyncSession = Depends(get_db)
):
    """List all tasks."""
    query = select(Task)
    
    if server_id:
        query = query.where(Task.server_id == server_id)
    if status:
        query = query.where(Task.status == status)
    
    query = query.order_by(Task.created_at.desc()).offset(skip).limit(limit)
    result = await db.execute(query)
    tasks = result.scalars().all()
    
    return {"items": tasks}


@router.get("/{task_id}")
async def get_task(
    task_id: int, 
    user: User = Depends(require_auth),
    db: AsyncSession = Depends(get_db)
):
    """Get task details."""
    result = await db.execute(
        select(Task).where(Task.id == task_id)
    )
    task = result.scalar_one_or_none()
    
    if not task:
        raise HTTPException(404, "Task not found")
    
    # Get subtasks
    subtasks = []
    for st in task.subtasks:
        subtasks.append({
            "id": st.id,
            "component_name": st.component_name,
            "status": st.status.value,
            "started_at": st.started_at.isoformat() if st.started_at else None,
            "completed_at": st.completed_at.isoformat() if st.completed_at else None,
            "error_message": st.error_message,
        })
    
    return {
        "id": task.id,
        "task_type": task.task_type.value,
        "server_id": task.server_id,
        "component_names": json.loads(task.component_names) if task.component_names else [],
        "status": task.status.value,
        "progress": task.progress,
        "current_step": task.current_step,
        "started_at": task.started_at.isoformat() if task.started_at else None,
        "completed_at": task.completed_at.isoformat() if task.completed_at else None,
        "duration_seconds": task.duration_seconds,
        "output": task.output,
        "error_message": task.error_message,
        "options": task.options,
        "subtasks": subtasks,
        "created_at": task.created_at.isoformat(),
    }


@router.get("/{task_id}/logs")
async def get_task_logs(
    task_id: int, 
    user: User = Depends(require_auth),
    db: AsyncSession = Depends(get_db)
):
    """Get task logs."""
    result = await db.execute(
        select(Task).where(Task.id == task_id)
    )
    task = result.scalar_one_or_none()
    
    if not task:
        raise HTTPException(404, "Task not found")
    
    return {
        "task_id": task_id,
        "output": task.output or "",
        "error": task.error_message,
    }


@router.post("/{task_id}/cancel")
async def cancel_task(
    task_id: int, 
    user: User = Depends(require_auth),
    db: AsyncSession = Depends(get_db)
):
    """Cancel a running task."""
    result = await db.execute(
        select(Task).where(Task.id == task_id)
    )
    task = result.scalar_one_or_none()
    
    if not task:
        raise HTTPException(404, "Task not found")
    
    if task.status not in [TaskStatus.PENDING, TaskStatus.RUNNING]:
        raise HTTPException(400, "Task is not cancellable")
    
    task.status = TaskStatus.CANCELLED
    task.completed_at = datetime.utcnow()
    await db.commit()
    
    return {"success": True, "message": "Task cancelled"}


@router.websocket("/ws/{task_id}")
async def task_websocket(websocket: WebSocket, task_id: int):
    """WebSocket for real-time task updates."""
    await websocket.accept()
    
    try:
        while True:
            # In a real implementation, you would:
            # 1. Subscribe to task updates from Celery/Redis
            # 2. Push updates to websocket
            
            # For now, just keep connection alive
            data = await websocket.receive_text()
            if data == "close":
                break
                
    except WebSocketDisconnect:
        pass
    finally:
        await websocket.close()