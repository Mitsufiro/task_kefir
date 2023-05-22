import logging
import os

from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlmodel import SQLModel
from sqlmodel.ext.asyncio.session import AsyncSession

logger = logging.getLogger(__name__)

print("DB", os.environ["DATABASE_URL"])

async_engine = create_async_engine(os.environ["DATABASE_URL"], echo=True, future=True)


async def init_db():
    """
    Method to initialize database creating missing tables if required.
    """
    async with async_engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)


async def get_async_session() -> AsyncSession:
    """
    Method to get database session.

    :return: sqlalchemy session
    :rtype: AsyncSession
    """
    async_session = sessionmaker(
        bind=async_engine, class_=AsyncSession, expire_on_commit=False
    )
    async with async_session() as session:
        yield session
