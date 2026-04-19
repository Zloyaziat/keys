from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.ext.asyncio import AsyncSession
from pathlib import Path
import os
from dotenv import load_dotenv
env_path = Path(__file__).parent.parent.parent / ".env"  # поднимаемся на 3 уровня до D:\keys
load_dotenv(env_path)

DATABASE_URL = os.getenv("DATABASE_URL")
# SECRET_DATABASE_URL = os.getenv("SECRET_DATABASE_URL")
# Загружаем .env файл
load_dotenv()
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

# engine_secret = create_async_engine(SECRET_DATABASE_URL, echo=False, future=True)
# BaseSecret = declarative_base()
# async_session_maker_2 = async_sessionmaker(
#     bind=engine_secret,
#     class_=AsyncSession,
#     expire_on_commit=False,
# )

# async def get_secret_db() -> AsyncSession:
#     async with async_session_maker_2() as db_s:
#         yield db_s
