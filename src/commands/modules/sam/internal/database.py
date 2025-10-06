from contextlib import asynccontextmanager
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import (AsyncEngine, AsyncSession,
                                    create_async_engine)
from sqlalchemy.orm import sessionmaker
from sqlmodel import SQLModel

from ..config import config
from ..internal import logger_config

logger = logger_config.logger.getChild("database")

engine: AsyncEngine = create_async_engine(
    str(config.database_uri), echo=False, future=True
)

if ":memory:" in str(config.database_uri):
    logger.warning("Database is in-memory, data will be lost on restart!")

# Dirty hack to enable hot-reloading
try:
    if not SQLModel.__table_args__.get("extend_existing", False):  # type: ignore
        logger.warning("Performing dirty hack for SQLModel hot reloading for models...")
except AttributeError:
    logger.warning(
        "Performing dirty hack for SQLModel to enable hot reloading of the extension."
    )
SQLModel.__table_args__ = {"extend_existing": True}


async def init_db():
    """
    Initializes the database by creating all tables.

    This is an idempotent operation, and can be safely called multiple times.
    """
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)


async def drop_db():
    """
    Drops all tables in the database.

    This is a destructive operation and will cause data loss.

    Use with caution.
    """
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.drop_all)


@asynccontextmanager
async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """
    A context manager that yields a session to the database. This session will be automatically rolled back if an exception occurs.

    Yields:
        AsyncGenerator[AsyncSession, None]: A generator that yields a session to the database.
    """
    async_session: sessionmaker = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)  # type: ignore
    async with async_session() as session:
        session: AsyncSession
        try:
            yield session
        finally:
            await session.rollback()
