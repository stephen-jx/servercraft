"""Database configuration."""
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from .config import settings

# Handle SQLite vs PostgreSQL
_sqlite_args = {"check_same_thread": False} if "sqlite" in settings.DATABASE_URL else {}
_pool_args = {} if "sqlite" in settings.DATABASE_URL else {"pool_pre_ping": True, "pool_size": 10}

engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    connect_args=_sqlite_args,
    **_pool_args
)

async_session_maker = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    pass


async def get_db():
    async with async_session_maker() as session:
        try:
            yield session
        finally:
            await session.close()


async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)