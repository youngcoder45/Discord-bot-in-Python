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

# Create sessionmaker globally
async_session_maker = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

# Allow hot-reloading of the extension (cog reload via ?load)
SQLModel.__table_args__ = {"extend_existing": True}  # type: ignore

async def init_db():
    """
    Initializes the database by creating all tables.

    This is an idempotent operation, and can be safely called multiple times.
    """
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)


@asynccontextmanager
async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """
    A context manager that yields a session to the database.
    """
    session = async_session_maker()
    try:
        yield session
    except Exception:
        # Only rollback if the session is still active/in transaction
        try:
            await session.rollback()
        except Exception:
            pass # Ignore errors during rollback
        raise
    finally:
        try:
            await session.close()
        except Exception:
            pass # Ignore errors during session closure
