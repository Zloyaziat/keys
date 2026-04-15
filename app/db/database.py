from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.ext.asyncio import AsyncSession
import os
DATABASE_URL = "postgresql+asyncpg://postgres:postgres@localhost/bank"
SECRET_DATABASE_URL = "postgresql+asyncpg://postgres:postgres@localhost/secret"
Base = declarative_base()
engine = create_async_engine(DATABASE_URL, echo=False, future=True)

async_session_maker_1 = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

async def get_db() -> AsyncSession:
    async with async_session_maker_1() as db:
        yield db

engine_secret = create_async_engine(SECRET_DATABASE_URL, echo=False, future=True)
BaseSecret = declarative_base()
async_session_maker_2 = async_sessionmaker(
    bind=engine_secret,
    class_=AsyncSession,
    expire_on_commit=False,
)

async def get_secret_db() -> AsyncSession:
    async with async_session_maker_2() as db_s:
        yield db_s
