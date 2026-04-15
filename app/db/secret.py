from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import hashlib
import sys
sys.path.append('D:\keys\app')
from models import User_s


async def get_or_create_user_id(
    login: str,
    db : AsyncSession
    ):
    
    login_hash = hashlib.sha256(login.lower().encode("utf-8")).hexdigest()

    # ищем по login_hash
    stmt = select(User_s).where(User_s.login == login_hash)
    result = await db.execute(stmt)
    user = result.scalars().first()

    if user:
        return user.id
    
    user =  User_s(login = login_hash)
    db.add(user)
    await db.flush()
    return user.id
    

