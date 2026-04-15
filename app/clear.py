import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from app.db.database import async_session_maker_1, async_session_maker_2

async def clear_main_db():
    """Очищает все таблицы в основной БД (bank)"""
    async with async_session_maker_1() as db:
        # Отключаем проверку внешних ключей
        await db.execute(text("SET session_replication_role = 'replica';"))
        
        # Очищаем таблицы в правильном порядке (сначала зависимые, потом основные)
        await db.execute(text("TRUNCATE TABLE stack CASCADE;"))
        await db.execute(text("TRUNCATE TABLE transaction CASCADE;"))
        await db.execute(text("TRUNCATE TABLE session CASCADE;"))
        await db.execute(text("TRUNCATE TABLE support CASCADE;"))
        await db.execute(text("TRUNCATE TABLE mcc CASCADE;"))
        await db.execute(text("TRUNCATE TABLE place CASCADE;"))
        await db.execute(text("TRUNCATE TABLE users CASCADE;"))
        
        # Включаем обратно проверку внешних ключей
        await db.execute(text("SET session_replication_role = 'origin';"))
        
        await db.commit()
        print("✅ Все таблицы в основной БД (bank) очищены")

async def clear_secret_db():
    """Очищает таблицы в секретной БД (secret)"""
    async with async_session_maker_2() as db:
        await db.execute(text("TRUNCATE TABLE users_s CASCADE;"))
        await db.commit()
        print("✅ Таблицы в секретной БД (secret) очищены")

async def clear_all():
    """Очищает все таблицы в обеих БД"""
    await clear_main_db()
    await clear_secret_db()
    print("\n🎉 Все данные удалены! Теперь можно запускать y.py")

if __name__ == "__main__":
    asyncio.run(clear_all())