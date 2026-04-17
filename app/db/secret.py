from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import hashlib
import os
import sys
import hmac
sys.path.append('D:\\keys\\app')
from models import User_s

from pathlib import Path
from dotenv import load_dotenv
env_path = Path(__file__).parent.parent.parent / ".env"  # поднимаемся на 3 уровня до D:\keys
load_dotenv(env_path)

SECRET_KEY = os.getenv("SECRET_KEY", "dev_secret")



def hash_login(login: str) -> str:
    return hmac.new(
        SECRET_KEY.encode(),
        login.lower().encode(),
        hashlib.sha256
    ).hexdigest()


async def get_or_create_user_id(
    login: str,
    db: AsyncSession
):
    login_hash = hash_login(login)

    stmt = select(User_s).where(User_s.login == login_hash)
    result = await db.execute(stmt)
    user = result.scalars().first()

    if user:
        return user.id

    user = User_s(login=login_hash)
    db.add(user)
    await db.flush()
    return user.id