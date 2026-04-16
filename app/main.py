from fastapi import FastAPI, Form, Request, Depends, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse, FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path
from dateutil.relativedelta import relativedelta  
from pydantic import BaseModel
import sys
import os
from sqlalchemy.sql import over
from sqlalchemy.orm import selectinload, joinedload
# Добавляем родительскую директорию в путь
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app.db.database import Base, engine, get_db, engine_secret, get_secret_db
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text, and_, or_, select, func, desc, extract, and_
from fastapi import File, UploadFile
from app import models
from datetime import datetime, timedelta, date, time
from typing import Optional, List, Dict, Any
import json


# uvicorn app.main:app --reload


app = FastAPI()



BASE_DIR = Path(__file__).parent.parent
FRONTEND_DIR = BASE_DIR / "frontend"

app.mount("/css", StaticFiles(directory=FRONTEND_DIR / "css"), name="css")
app.mount("/js", StaticFiles(directory=FRONTEND_DIR / "js"), name="js")


class Filter(BaseModel):
    
    # 📅 даты
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None

    # 👤 пользователь
    sex: Optional[str] = None
    age_from: Optional[int] = None
    age_to: Optional[int] = None

    # 🧠 сессии
    session_type: Optional[str] = None
    min_duration: Optional[int] = None  # секунды
    max_duration: Optional[int] = None

    # 💳 транзакции
    min_sum: Optional[int] = None
    max_sum: Optional[int] = None
    payment_method: Optional[int] = None
    city: Optional[str] = None
    category: Optional[str] = None

    # 📊 сравнение
    comparison_type: Optional[str] = None
    target_date: Optional[datetime] = None


async def get_table_category_comparison(
    db: AsyncSession,
    filter: Optional[Filter] = None
) -> Dict[str, Any]:

    # 🔹 Вспомогательная функция
    async def get_period_data(start_date: datetime, end_date: datetime):

        conditions = [
            models.Ttransaction.date >= start_date,
            models.Ttransaction.date <= end_date,
        ]

        stmt = (
            select(
                models.Mcc.name.label("category"),
                func.count(models.Ttransaction.id).label("count")
            )
            .select_from(models.Ttransaction)
            .join(models.Mcc, models.Ttransaction.mcc_id == models.Mcc.id)
            .join(models.User, models.User.user_id == models.Ttransaction.user_id)
            .outerjoin(models.Place, models.Place.id == models.Ttransaction.place_id)
        )

        # 🔥 ФИЛЬТРЫ
        if filter:
            if filter.sex:
                conditions.append(models.User.sex == filter.sex)

            if filter.age_from:
                conditions.append(models.User.age >= filter.age_from)

            if filter.age_to:
                conditions.append(models.User.age <= filter.age_to)

            if filter.min_sum:
                conditions.append(models.Ttransaction.sum >= filter.min_sum)

            if filter.max_sum:
                conditions.append(models.Ttransaction.sum <= filter.max_sum)

            if filter.payment_method:
                conditions.append(models.Ttransaction.payment_method == filter.payment_method)

            if filter.city:
                conditions.append(models.Place.city == filter.city)

            if filter.category:
                conditions.append(models.Mcc.name == filter.category)

        stmt = stmt.where(and_(*conditions))
        stmt = stmt.group_by(models.Mcc.name)
        stmt = stmt.order_by(desc("count"))

        result = await db.execute(stmt)

        return [
            {"name": row.category, "value": row.count}
            for row in result
        ]

    # 🔥 ЛОГИКА ПЕРИОДОВ
    today = datetime.now()

    if filter and filter.comparison_type == "mom":
        # Month over Month
        target = filter.target_date or today

        current_start = target.replace(day=1)
        current_end = (current_start + relativedelta(months=1)) - timedelta(days=1)

        previous_start = current_start - relativedelta(months=1)
        previous_end = current_start - timedelta(days=1)

        label1 = current_start.strftime("%B %Y")
        label2 = previous_start.strftime("%B %Y")

    elif filter and filter.comparison_type == "yoy":
        # Year over Year
        target = filter.target_date or today

        current_start = target.replace(month=1, day=1)
        current_end = target

        previous_start = current_start.replace(year=current_start.year - 1)
        previous_end = current_end.replace(year=current_end.year - 1)

        label1 = str(current_start.year)
        label2 = str(previous_start.year)

    else:
        # Последние 30 дней
        current_start = today - timedelta(days=30)
        current_end = today

        previous_start = current_start - timedelta(days=30)
        previous_end = current_start - timedelta(days=1)

        label1 = "Последние 30 дней"
        label2 = "Предыдущие 30 дней"

    # 🔥 ПОЛУЧАЕМ ДАННЫЕ
    current_data = await get_period_data(current_start, current_end)
    previous_data = await get_period_data(previous_start, previous_end)

    # 🔥 ОБЪЕДИНЕНИЕ ДЛЯ ГРАФИКОВ
    combined = combine_data_for_charts(current_data, previous_data, label1, label2)

    return {
        "periods": [
            {
                "label": label1,
                "data": current_data[:10]
            },
            {
                "label": label2,
                "data": previous_data[:10]
            }
        ],
        "combined": combined
    }
def combine_data_for_charts(current_data, previous_data, label1, label2):

    all_categories = set()

    current_dict = {}
    previous_dict = {}

    for item in current_data:
        all_categories.add(item["name"])
        current_dict[item["name"]] = item["value"]

    for item in previous_data:
        all_categories.add(item["name"])
        previous_dict[item["name"]] = item["value"]

    categories = list(all_categories)

    return {
        "labels": categories,
        "datasets": [
            {
                "label": label1,
                "data": [current_dict.get(cat, 0) for cat in categories],
            },
            {
                "label": label2,
                "data": [previous_dict.get(cat, 0) for cat in categories],
            }
        ]
    }


#напиши тут такую же функцию как и для прошлой функции подсчета резуьтативных данных 
# исходжя из заданного промежутка времени. Основная идея как бы сранвить 
# поток поступаемых ошибок системы споставив их с деплоями версий приложения 
async def get_table_ui(db: AsyncSession,filter: Optional[Filter] = None):

    conditions = []

    stmt = (
        select(
            models.Session.type.label("type"),
            models.Session.ui_version_app,
            func.sum(models.Session.clicks_on_old_ui).label("old"),
            func.sum(models.Session.clicks_on_new_ui).label("new"),
            func.avg(func.extract('epoch', models.Session.session_duration)).label("avg_duration"),
            func.count(models.Support.id).label("errors_count")
        )
        .join(models.User, models.User.user_id == models.Session.user_id)
        .outerjoin(models.Support, models.Support.user_id == models.User.user_id)
    )

    # 🔥 ФИЛЬТРЫ
    if filter:
        if filter.age_from:
            conditions.append(models.User.age >= filter.age_from)

        if filter.age_to:
            conditions.append(models.User.age <= filter.age_to)

        if filter.sex:
            conditions.append(models.User.sex == filter.sex)

        if filter.session_type:
            conditions.append(models.Session.type == filter.session_type)



    if conditions:
        stmt = stmt.where(and_(*conditions))

    stmt = stmt.group_by(models.Session.type, models.Session.ui_version_app)

    result = await db.execute(stmt)

    return [
        {
            "type": row.type,
            "ui_version": row.ui_version_app,
            "clicks_old": row.old,
            "clicks_new": row.new,
            "avg_duration": int(row.avg_duration) if row.avg_duration else 0,
            "errors": row.errors_count
        }
        for row in result
    ]
# изанчальная таблица представленна средняя сумма покупок по категориям. Есть кнопки чтобы отфильтровать транзакции по возрасту покупаетля, цене, региону, 
# по способам оплаты (1 - наличка, 2 - карта, 3 - qr оплата) и подключить сюда категории товаров.
async def get_table_transtions(db: AsyncSession, filter: Optional[Filter] = None):

    conditions = []

    stmt = (
        select(
            models.Mcc.name.label("category"),
            func.avg(models.Ttransaction.sum).label("avg_sum"),
            func.count(models.Ttransaction.id).label("count")
        )
        .select_from(models.Ttransaction)
        .join(models.Mcc, models.Mcc.id == models.Ttransaction.mcc_id)
        .join(models.User, models.User.user_id == models.Ttransaction.user_id)
        .outerjoin(models.Place, models.Place.id == models.Ttransaction.place_id)
    )

    # 🔥 ФИЛЬТРЫ
    if filter:
        if filter.sex:
            conditions.append(models.User.sex == filter.sex)

        if filter.age_from:
            conditions.append(models.User.age >= filter.age_from)

        if filter.age_to:
            conditions.append(models.User.age <= filter.age_to)

        if filter.min_sum:
            conditions.append(models.Ttransaction.sum >= filter.min_sum)

        if filter.max_sum:
            conditions.append(models.Ttransaction.sum <= filter.max_sum)

        if filter.payment_method:
            conditions.append(models.Ttransaction.payment_method == filter.payment_method)

        if filter.city:
            conditions.append(models.Place.city == filter.city)

        if filter.category:
            conditions.append(models.Mcc.name == filter.category)

    if conditions:
        stmt = stmt.where(and_(*conditions))

    stmt = stmt.group_by(models.Mcc.name)
    stmt = stmt.order_by(desc("avg_sum"))

    result = await db.execute(stmt)

    return [
        {
            "category": row.category,
            "avg_sum": float(row.avg_sum) if row.avg_sum else 0,
            "count": row.count
        }
        for row in result
    ]

# 🔥 Эндпоинт для отдачи HTML-страницы
@app.get("/", response_class=HTMLResponse)
async def read_root():
    """Отдаёт index.html"""
    index_path = FRONTEND_DIR / "index.html"
    if index_path.exists():
        return FileResponse(index_path)
    return HTMLResponse("<h1>index.html not found</h1>", status_code=404)


# ✅ API для данных (GET)
@app.get('/api/data/')
async def get_data(db: AsyncSession = Depends(get_db)):
    return {
        'category': await get_table_category_comparison(db),
        'ui': await get_table_ui(db),
        'transtions': await get_table_transtions(db)
    }


# ✅ API для данных с фильтрами (POST)
@app.post('/api/')
async def filter_data(filter: Filter, db: AsyncSession = Depends(get_db)):
    return {
        'category': await get_table_category_comparison(db, filter),
        'ui': await get_table_ui(db, filter),
        'transtions': await get_table_transtions(db, filter)
    }




