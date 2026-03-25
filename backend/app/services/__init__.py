"""Services package."""
from .components import get_component, list_components, get_categories, COMPONENT_REGISTRY
from .ssh_executor import SSHExecutor, SSHResult
from .task_runner import TaskRunner

__all__ = [
    "get_component", "list_components", "get_categories", "COMPONENT_REGISTRY",
    "SSHExecutor", "SSHResult", "TaskRunner"
]


async def run_task_background(db, task_id: int):
    """Run a task in background."""
    from .task_runner import TaskRunner
    from sqlalchemy import select
    from ..models import Task
    
    result = await db.execute(select(Task).where(Task.id == task_id))
    task = result.scalar_one_or_none()
    
    if task:
        runner = TaskRunner(db, task)
        # In production, this would be a Celery task
        # For now, we'll run it directly
        import asyncio
        asyncio.create_task(runner.run())