import asyncio
import asyncpg

async def create_everything():
    # Подключаемся к postgres
    conn = await asyncpg.connect(user='postgres', password='postgres', database='postgres')
    
    # Создаем базы данных
    try:
        await conn.execute('CREATE DATABASE bank')
        print("✅ База bank создана")
    except:
        print("⚠️ База bank уже существует")
    
    try:
        await conn.execute('CREATE DATABASE secret')
        print("✅ База secret создана")
    except:
        print("⚠️ База secret уже существует")
    
    await conn.close()
    
    # Подключаемся к bank и создаем таблицы
    conn_bank = await asyncpg.connect(user='postgres', password='postgres', database='bank')
    
    tables_bank = """
    CREATE TABLE IF NOT EXISTS users (
        id SERIAL PRIMARY KEY,
        user_id INTEGER UNIQUE NOT NULL,
        sex VARCHAR(3),
        age INTEGER,
        permission INTEGER NOT NULL
    );
    
    CREATE TABLE IF NOT EXISTS mcc (
        id SERIAL PRIMARY KEY,
        name INTEGER NOT NULL
    );
    
    CREATE TABLE IF NOT EXISTS place (
        id SERIAL PRIMARY KEY,
        country VARCHAR,
        region VARCHAR,
        city VARCHAR,
        street VARCHAR
    );
    
    CREATE TABLE IF NOT EXISTS transaction (
        id SERIAL PRIMARY KEY,
        user_id INTEGER REFERENCES users(user_id),
        mcc_id INTEGER REFERENCES mcc(id),
        sum INTEGER NOT NULL,
        place_id INTEGER REFERENCES place(id),
        amount INTEGER,
        date DATE NOT NULL,
        payment_method INTEGER NOT NULL,
        stack INTEGER
    );
    
    CREATE TABLE IF NOT EXISTS support (
        id SERIAL PRIMARY KEY,
        user_id INTEGER REFERENCES users(user_id),
        type VARCHAR NOT NULL,
        UI_version_app VARCHAR NOT NULL
    );
    
    CREATE TABLE IF NOT EXISTS session (
        id SERIAL PRIMARY KEY,
        user_id INTEGER REFERENCES users(user_id),
        session_duration VARCHAR NOT NULL,
        type VARCHAR NOT NULL,
        clicks_on_new_ui INTEGER,
        clicks_on_old_ui INTEGER,
        UI_version_app VARCHAR NOT NULL
    );
    
    CREATE TABLE IF NOT EXISTS stack (
        id SERIAL PRIMARY KEY,
        transaction_id INTEGER REFERENCES transaction(id),
        name VARCHAR NOT NULL,
        conditions TEXT
    );
    """
    
    await conn_bank.execute(tables_bank)
    print("✅ Таблицы в bank созданы")
    await conn_bank.close()
    
    # Подключаемся к secret и создаем таблицу
    conn_secret = await asyncpg.connect(user='postgres', password='postgres', database='secret')
    
    await conn_secret.execute("""
    CREATE TABLE IF NOT EXISTS users_s (
        id SERIAL PRIMARY KEY,
        login TEXT UNIQUE NOT NULL
    )
    """)
    print("✅ Таблица users_s в secret создана")
    await conn_secret.close()
    
    print("\n🎉 ГОТОВО! Все таблицы созданы.")

if __name__ == "__main__":
    asyncio.run(create_everything())