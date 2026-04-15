import asyncio
import sys
import os

# Добавляем родительскую директорию в путь
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Замени относительный импорт на абсолютный
from app.db.database import async_session_maker_1, async_session_maker_2
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import User_s, User, Mcc, Place, Stack, Ttransaction, Support, Session
import random
from datetime import date, timedelta
from faker import Faker
import hashlib

fake = Faker()

# --- справочники ---
SESSION_TYPES = [
    "перевод денег",
    "оплата ЖКХ",
    "оплата мобильной связи",
    "просмотр акции",
    "оформление кредита",
    "оформление карты",
    "открытие вклада"
]

PAYMENT_METHODS = [1, 2, 3]  # карта, сбп, наличные
UI_VERSIONS = ["v1", "v2"]

def generate_users_s(users):
    users_s = []
    for user in users:
        login = str(user.user_id)
        login_hash = hashlib.sha256(login.encode()).hexdigest()
        users_s.append(User_s(login=login_hash))
    return users_s

# --- генерация пользователей ---
def generate_users(n=100):
    users = []
    for i in range(n):
        users.append(User(
            user_id=1000 + i,
            sex=random.choice(["M", "F"]),
            age=random.randint(14, 70),
            permission=random.choice([1, 2, 3, 4])
        ))
    return users

# --- генерация мест ---
def generate_places(n=20):
    places = []
    for _ in range(n):
        places.append(Place(
            country="Russia",
            region=fake.state(),
            city=fake.city(),
            street=fake.street_name()
        ))
    return places

# --- генерация mcc ---
def generate_mcc(n=20):
    mccs = []
    for _ in range(n):
        mccs.append(Mcc(name=random.randint(5000, 6000)))
    return mccs

# --- генерация транзакций ---
def generate_transactions(users, places, mccs, n=1000):
    transactions = []
    for _ in range(n):
        user = random.choice(users)
        place = random.choice(places)
        mcc = random.choice(mccs)

        transactions.append(Ttransaction(
            user_id=user.user_id,
            mcc_id=mcc.id,
            sum=random.randint(100, 50000),
            place_id=place.id,
            amount=random.randint(1, 5),
            date=date.today() - timedelta(days=random.randint(0, 30)),
            payment_method=random.choice(PAYMENT_METHODS)
        ))
    return transactions

# --- генерация сессий ---
def generate_sessions(users, n=1500):
    sessions = []
    for _ in range(n):
        user = random.choice(users)

        # длительность в HH:MM
        hours = random.randint(0, 2)
        minutes = random.randint(0, 59)
        duration = f"{hours:02}:{minutes:02}"

        sessions.append(Session(
            user_id=user.user_id,
            session_duration=duration,
            type=random.choice(SESSION_TYPES),
            clicks_on_new_ui=random.randint(0, 30),
            clicks_on_old_ui=random.randint(0, 20),
            ui_version_app=random.choices(UI_VERSIONS, weights=[0.3, 0.7])[0]  # чаще v2
        ))
    return sessions

# --- генерация support ---
def generate_support(users, n=200):
    types = ["жалоба", "вопрос", "ошибка", "благодарность"]

    support_list = []
    for _ in range(n):
        user = random.choice(users)

        support_list.append(Support(
            user_id=user.user_id,
            type=random.choice(types),
            ui_version_app=random.choice(UI_VERSIONS)
        ))
    return support_list

# --- генерация stack (акции) ---
def generate_stack(transactions, n=500):
    names = ["Кэшбэк 5%", "Скидка 10%", "Бонус 300", "Кэшбэк 2%"]
    conditions = [
        "Оплата картой",
        "Сумма > 1000",
        "Первый платеж",
        "Только в приложении"
    ]

    stacks = []
    for _ in range(n):
        tx = random.choice(transactions)

        stacks.append(Stack(
            transaction_id=tx.id,
            name=random.choice(names),
            conditions=random.choice(conditions)
        ))
    return stacks

async def seed_data_s(db_s: AsyncSession, users):
    users_s = generate_users_s(users)
    db_s.add_all(users_s)
    await db_s.commit()
    print(f"✅ Добавлено {len(users_s)} записей в users_s")

# --- запуск ---
async def seed_data(db: AsyncSession):
    # Генерируем пользователей
    users = generate_users(100)
    db.add_all(users)
    await db.commit()
    print(f"✅ Добавлено {len(users)} пользователей")
    
    # Обновляем ID пользователей
    for user in users:
        await db.refresh(user)

    # Генерируем места
    places = generate_places(20)
    db.add_all(places)
    await db.commit()
    print(f"✅ Добавлено {len(places)} мест")
    
    for place in places:
        await db.refresh(place)

    # Генерируем MCC
    mcc = generate_mcc(20)
    db.add_all(mcc)
    await db.commit()
    print(f"✅ Добавлено {len(mcc)} MCC кодов")
    
    for m in mcc:
        await db.refresh(m)

    # Генерируем транзакции
    transactions = generate_transactions(users, places, mcc, 1000)
    db.add_all(transactions)
    await db.commit()
    print(f"✅ Добавлено {len(transactions)} транзакций")
    
    for tx in transactions:
        await db.refresh(tx)

    # Генерируем сессии
    sessions = generate_sessions(users, 1500)
    db.add_all(sessions)
    await db.commit()
    print(f"✅ Добавлено {len(sessions)} сессий")

    # Генерируем support
    support = generate_support(users, 200)
    db.add_all(support)
    await db.commit()
    print(f"✅ Добавлено {len(support)} обращений в поддержку")

    # Генерируем stacks
    stacks = generate_stack(transactions, 500)
    db.add_all(stacks)
    await db.commit()
    print(f"✅ Добавлено {len(stacks)} стеков")

    print("🔥 Данные успешно сгенерированы в основной БД")
    return users

async def main():
    # Заполняем основную БД
    async with async_session_maker_1() as db:
        users = await seed_data(db)
    
    # Заполняем секретную БД (users_s)
    async with async_session_maker_2() as db_s:
        await seed_data_s(db_s, users)
    
    print("🎉 Все данные успешно сгенерированы в обеих базах данных!")

if __name__ == "__main__":
    asyncio.run(main())