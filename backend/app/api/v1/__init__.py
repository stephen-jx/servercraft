"""API v1 routes."""
from fastapi import APIRouter
from .servers import router as servers_router
from .components import router as components_router
from .tasks import router as tasks_router
from .auth import router as auth_router

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(auth_router)
api_router.include_router(servers_router)
api_router.include_router(components_router)
api_router.include_router(tasks_router)