from fastapi import FastAPI, Form, Request, Depends, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse, FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path
from dateutil.relativedelta import relativedelta  
from pydantic import BaseModel
import sys
from prophet import Prophet
import os
from sqlalchemy.sql import over
from sqlalchemy.orm import selectinload, joinedload
# Добавляем родительскую директорию в путь
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app.db.database import Base, engine, get_db
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text, and_, or_, select, func, desc, extract, and_
from fastapi import File, UploadFile
from app import models
from datetime import datetime, timedelta, date, time
from typing import Optional, List, Dict, Any
import json
import pandas as pd

# uvicorn app.main:app --reload


app = FastAPI()



BASE_DIR = Path(__file__).parent.parent
FRONTEND_DIR = BASE_DIR / "frontend"

app.mount("/css", StaticFiles(directory=FRONTEND_DIR / "css"), name="css")
app.mount("/js", StaticFiles(directory=FRONTEND_DIR / "js"), name="js")


class Filter(BaseModel):
    
    # даты
    date_from: Optional[date] = None
    date_to: Optional[date] = None
    #  пользователь
    sex: Optional[str] = None
    age_from: Optional[int] = None
    age_to: Optional[int] = None

    # сессии
    session_type: Optional[str] = None
    min_duration: Optional[int] = None  # секунды
    max_duration: Optional[int] = None

    # транзакции
    min_sum: Optional[int] = None
    max_sum: Optional[int] = None
    payment_method: Optional[int] = None
    city: Optional[str] = None
    category: Optional[str] = None

    # сравнение
    comparison_type: Optional[str] = None
    target_date: Optional[datetime] = None


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



async def get_table_ui(db: AsyncSession,filter: Optional[Filter] = None):

    conditions = []

    stmt = (
        select(
            models.Session.type.label("type"),
            func.sum(models.Session.clicks_on_old_ui).label("old"),
            func.sum(models.Session.clicks_on_new_ui).label("new"),
            func.avg(func.extract('epoch', models.Session.session_duration)).label("avg_duration"),
        )
        .join(models.User, models.User.user_id == models.Session.user_id)
    )

    # ФИЛЬТРЫ
    if filter:
        if filter.date_from:
            conditions.append(models.Session.date_start >= filter.date_from)
        if filter.date_to:
            conditions.append(models.Session.date_start <= filter.date_to)
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

    stmt = stmt.group_by(models.Session.type)

    result = await db.execute(stmt)

    return [
        {
            "type": row.type,
            "clicks_old": row.old,
            "clicks_new": row.new,
            "avg_duration": int(row.avg_duration) if row.avg_duration else 0
        }
        for row in result
    ]


async def get_table_age(db: AsyncSession, filter: Optional[Filter] = None):
    """Получение популярных категорий товаров для подростков (14-18 лет)"""
    
    conditions = []
    
    stmt = (
        select(
            models.Mcc.category_name.label("category"),
            func.count(models.Ttransaction.id).label("count")
        )
        .select_from(models.Ttransaction)
        .join(models.User, models.User.user_id == models.Ttransaction.user_id)
        .join(models.Mcc, models.Mcc.id == models.Ttransaction.mcc_id)
    )
    
    # Применяем фильтры
    if filter:
        if filter.date_from:
            conditions.append(models.Ttransaction.date >= filter.date_from)
        if filter.date_to:
            conditions.append(models.Ttransaction.date <= filter.date_to)
        if filter.sex:
            conditions.append(models.User.sex == filter.sex)
        if filter.city:
            conditions.append(models.Place.city == filter.city)
        if filter.payment_method:
            conditions.append(models.Ttransaction.payment_method == filter.payment_method)
        if filter.min_sum:
            conditions.append(models.Ttransaction.sum >= filter.min_sum)
        if filter.max_sum:
            conditions.append(models.Ttransaction.sum <= filter.max_sum)
    
    # Фильтр по возрасту (подростки 14-18)
    conditions.append(models.User.age >= 14)
    conditions.append(models.User.age <= 18)
    
    # Применяем все условия
    if conditions:
        stmt = stmt.where(and_(*conditions))
    
    # Группируем и сортируем
    stmt = stmt.group_by(models.Mcc.category_name)
    stmt = stmt.order_by(desc("count"))
    stmt = stmt.limit(9)  # Лимит до выполнения
    
    result = await db.execute(stmt)
    
    # Возвращаем данные в едином формате
    return [
        {
            "category": row.category,
            "count": row.count
        }
        for row in result
    ]
async def get_table_age_2(db: AsyncSession, filter: Optional[Filter] = None):
   
    
    conditions = []
    
    stmt = (
        select(
            models.Mcc.category_name.label("category"),
            func.count(models.Ttransaction.id).label("count")
        )
        .select_from(models.Ttransaction)
        .join(models.User, models.User.user_id == models.Ttransaction.user_id)
        .join(models.Mcc, models.Mcc.id == models.Ttransaction.mcc_id)
    )
    
    # Применяем фильтры
    if filter:
        if filter.date_from:
            conditions.append(models.Ttransaction.date >= filter.date_from)
        if filter.date_to:
            conditions.append(models.Ttransaction.date <= filter.date_to)
        if filter.sex:
            conditions.append(models.User.sex == filter.sex)
        if filter.city:
            conditions.append(models.Place.city == filter.city)
        if filter.payment_method:
            conditions.append(models.Ttransaction.payment_method == filter.payment_method)
        if filter.min_sum:
            conditions.append(models.Ttransaction.sum >= filter.min_sum)
        if filter.max_sum:
            conditions.append(models.Ttransaction.sum <= filter.max_sum)
    
    # Фильтр по возрасту (подростки 14-18)
    conditions.append(models.User.age >= 18)
    conditions.append(models.User.age <= 35)
    
    # Применяем все условия
    if conditions:
        stmt = stmt.where(and_(*conditions))
    
    # Группируем и сортируем
    stmt = stmt.group_by(models.Mcc.category_name)
    stmt = stmt.order_by(desc("count"))
    stmt = stmt.limit(9)  # Лимит до выполнения
    
    result = await db.execute(stmt)
    
    # Возвращаем данные в едином формате
    return [
        {
            "category": row.category,
            "count": row.count
        }
        for row in result
    ]
# изанчальная таблица представленна средняя сумма покупок по категориям. Есть кнопки чтобы отфильтровать транзакции по возрасту покупаетля, цене, региону, 
# по способам оплаты (1 - наличка, 2 - карта, 3 - qr оплата) и подключить сюда категории товаров.
async def get_table_transtions(db: AsyncSession, filter: Optional[Filter] = None):

    conditions = []

    stmt = (
        select(
            models.Mcc.category_name.label("category"),
            func.avg(models.Ttransaction.sum).label("avg_sum"),
            func.count(models.Ttransaction.id).label("count")
        )
        .select_from(models.Ttransaction)
        .join(models.Mcc, models.Mcc.id == models.Ttransaction.mcc_id)
        .join(models.User, models.User.user_id == models.Ttransaction.user_id)
        .outerjoin(models.Place, models.Place.id == models.Ttransaction.place_id)
    )

    # ФИЛЬТРЫ
    if filter:
        if filter.date_from:
            conditions.append(models.Ttransaction.date >= filter.date_from)

        if filter.date_to:
            conditions.append(models.Ttransaction.date <= filter.date_to)
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
            conditions.append(models.Mcc.category_name == filter.category)

    if conditions:
        stmt = stmt.where(and_(*conditions))

    stmt = stmt.group_by(models.Mcc.category_name)
    stmt = stmt.order_by(desc("avg_sum"))
    stmt = stmt.limit(10)
    result = await db.execute(stmt)

    return [
        {
            "category": row.category,
            "avg_sum": float(row.avg_sum) if row.avg_sum else 0,
            "count": row.count
        }
        for row in result
    ]

async def get_table_transtions_type(db : AsyncSession, filter : Optional[Filter] = None):
    async def get_period_data(start_date: datetime, end_date: datetime):
        stmt = (
            select(
                models.Stack.name.label('stack'),
                func.count(models.Ttransaction.id).label('count')
            )
            .select_from(models.Ttransaction)
            .join(models.Stack, models.Ttransaction.stack == models.Stack.id) 
            .join(models.User, models.Ttransaction.user_id == models.User.user_id)  
            .outerjoin(models.Place, models.Ttransaction.place_id == models.Place.id)
        )
        conditions = []
        # ФИЛЬТРЫ
        if filter and (filter.date_from or filter.date_to):

            if filter.date_from:
                conditions.append(models.Ttransaction.date >= filter.date_from)

            if filter.date_to:
                conditions.append(models.Ttransaction.date <= filter.date_to)
        else:
            conditions = [
                models.Ttransaction.date >= start_date,
                models.Ttransaction.date <= end_date,
            ]

        # 2. ОСТАЛЬНЫЕ ФИЛЬТРЫ (ВСЕГДА ДОБАВЛЯЕМ)
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
            

        stmt = stmt.where(and_(*conditions))
        stmt = stmt.group_by(models.Stack.name)
        stmt = stmt.order_by(desc("count"))

        result = await db.execute(stmt)
        
        return [
            {"name": row.stack, "value": row.count}
            for row in result
        ]
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

    # ПОЛУЧАЕМ ДАННЫЕ
    current_data = await get_period_data(current_start, current_end)
    previous_data = await get_period_data(previous_start, previous_end)
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
async def get_table_transtions_by_city(db: AsyncSession, filter: Optional[Filter] = None):
    """Получение ТОП-10 городов с их самыми популярными категориями"""
    
    conditions = []
    
    # Подзапрос для получения ТОП-10 городов по сумме транзакций
    top_cities_subquery = (
        select(
            models.Place.city.label("city"),
            func.sum(models.Ttransaction.sum).label("total_sum")
        )
        .select_from(models.Ttransaction)
        .join(models.User, models.User.user_id == models.Ttransaction.user_id)
        .outerjoin(models.Place, models.Place.id == models.Ttransaction.place_id)
    )
    
    # Применяем фильтры к подзапросу
    if filter:
        if filter.date_from:
            conditions.append(models.Ttransaction.date >= filter.date_from)
        if filter.date_to:
            conditions.append(models.Ttransaction.date <= filter.date_to)
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
    
    if conditions:
        top_cities_subquery = top_cities_subquery.where(and_(*conditions))
    
    top_cities_subquery = (
        top_cities_subquery
        .where(models.Place.city.isnot(None))
        .group_by(models.Place.city)
        .order_by(desc("total_sum"))
        .limit(13)
    ).subquery()
    
    # Основной запрос для получения топ-3 категорий в каждом из топ-10 городов
    stmt = (
        select(
            models.Place.city.label("city"),
            models.Mcc.category_name.label("category"),
            func.count(models.Ttransaction.id).label("count"),
            func.avg(models.Ttransaction.sum).label("avg_sum")
        )
        .select_from(models.Ttransaction)
        .join(models.User, models.User.user_id == models.Ttransaction.user_id)
        .join(models.Mcc, models.Mcc.id == models.Ttransaction.mcc_id)
        .join(models.Place, models.Place.id == models.Ttransaction.place_id)
        .where(models.Place.city.in_(select(top_cities_subquery.c.city)))
    )
    
    # Применяем те же фильтры
    if conditions:
        stmt = stmt.where(and_(*conditions))
    
    stmt = stmt.group_by(models.Place.city, models.Mcc.category_name)
    stmt = stmt.order_by(models.Place.city, desc("count"))
    
    result = await db.execute(stmt)
    
    # Группируем данные по городам и берем топ-3 категории для каждого
    city_data = {}
    for row in result:
        if row.city not in city_data:
            city_data[row.city] = []
        
        if len(city_data[row.city]) < 1:  # Берем только топ-3 категории
            city_data[row.city].append({
                "category": row.category,
                "count": row.count,
                "avg_sum": float(row.avg_sum) if row.avg_sum else 0
            })
    
    return city_data

async def get_transactions_trend(db: AsyncSession, filter: Optional[Filter] = None):
    """
    Прогноз суммы транзакций на 14 дней с учетом всех фильтров.
    Если категория не указана, берется самая популярная категория.
    """
    
    conditions = []
    
    # Базовый запрос с джойнами для фильтрации
    stmt = (
        select(
            func.date(models.Ttransaction.date).label("date"),
            func.sum(models.Ttransaction.sum).label("total")
        )
        .select_from(models.Ttransaction)
        .join(models.User, models.User.user_id == models.Ttransaction.user_id)
        .join(models.Mcc, models.Mcc.id == models.Ttransaction.mcc_id)
        .outerjoin(models.Place, models.Place.id == models.Ttransaction.place_id)
    )

    # Применяем ВСЕ фильтры
    if filter:
        if filter.sex:
            conditions.append(models.User.sex == filter.sex)
        if filter.age_from:
            conditions.append(models.User.age >= filter.age_from)
        if filter.age_to:
            conditions.append(models.User.age <= filter.age_to)
        if filter.city:
            conditions.append(models.Place.city == filter.city)
        if filter.payment_method:
            conditions.append(models.Ttransaction.payment_method == filter.payment_method)
        

    # Определяем категорию для прогноза
    selected_category = None
    if filter and filter.category:
        selected_category = filter.category
    else:
        # Если категория не выбрана, находим самую популярную
        popular_stmt = (
            select(models.Mcc.category_name, func.count(models.Ttransaction.id).label("cnt"))
            .select_from(models.Ttransaction)
            .join(models.Mcc, models.Mcc.id == models.Ttransaction.mcc_id)
        )
        if conditions:
            popular_stmt = popular_stmt.where(and_(*conditions))
        popular_stmt = popular_stmt.group_by(models.Mcc.category_name).order_by(desc("cnt")).limit(1)
        
        popular_result = await db.execute(popular_stmt)
        popular_row = popular_result.first()
        if popular_row:
            selected_category = popular_row.category_name
        else:
            return {"history": [], "forecast": [], "category": None, "message": "Нет данных"}

    # Добавляем фильтр по категории
    conditions.append(models.Mcc.category_name == selected_category)

    # Применяем все условия
    if conditions:
        stmt = stmt.where(and_(*conditions))

    stmt = stmt.group_by(func.date(models.Ttransaction.date))
    stmt = stmt.order_by("date")

    result = await db.execute(stmt)
    
    data = [{"ds": row.date, "y": float(row.total) if row.total else 0} for row in result]

    if len(data) < 5:
        return {
            "history": data, 
            "forecast": [], 
            "category": selected_category,
            "message": "Недостаточно данных для прогноза (нужно минимум 5 дней)"
        }

    # Прогнозирование с помощью Prophet
    df = pd.DataFrame(data)
    df['ds'] = pd.to_datetime(df['ds'])
    
    model = Prophet(
        yearly_seasonality=False,
        weekly_seasonality=True,
        daily_seasonality=False,
        changepoint_prior_scale=0.05
    )
    model.fit(df)

    future = model.make_future_dataframe(periods=14)
    forecast = model.predict(future)

    forecast_data = forecast[['ds', 'yhat', 'yhat_lower', 'yhat_upper']].tail(14)
    
    # Конвертируем даты в строки для JSON
    forecast_data['ds'] = forecast_data['ds'].dt.strftime('%Y-%m-%d')

    return {
        "history": [{"ds": d["ds"].strftime("%Y-%m-%d") if isinstance(d["ds"], (pd.Timestamp, datetime, date)) else d["ds"], 
                     "y": d["y"]} for d in data],
        "forecast": forecast_data.to_dict(orient="records"),
        "category": selected_category
    }

async def get_payment_methods_trend(db: AsyncSession, filter: Optional[Filter] = None):
    
    
    conditions = []
    
    # Базовый запрос с джойнами
    stmt = (
        select(
            func.date(models.Ttransaction.date).label("date"),
            models.Ttransaction.payment_method.label("payment_method"),
            func.count(models.Ttransaction.id).label("count"),
            func.sum(models.Ttransaction.sum).label("total_sum")
        )
        .select_from(models.Ttransaction)
        .join(models.User, models.User.user_id == models.Ttransaction.user_id)
        .join(models.Mcc, models.Mcc.id == models.Ttransaction.mcc_id)
        .outerjoin(models.Place, models.Place.id == models.Ttransaction.place_id)
    )

    # Применяем ВСЕ фильтры
    if filter:
        
        if filter.sex:
            conditions.append(models.User.sex == filter.sex)
        if filter.age_from:
            conditions.append(models.User.age >= filter.age_from)
        if filter.age_to:
            conditions.append(models.User.age <= filter.age_to)
        if filter.city:
            conditions.append(models.Place.city == filter.city)
        if filter.category:  
            conditions.append(models.Mcc.category_name == filter.category)
        

    # Определяем, какой метод оплаты анализировать
    selected_payment = None
    if filter and filter.payment_method:
        selected_payment = filter.payment_method
        conditions.append(models.Ttransaction.payment_method == selected_payment)

    # Применяем условия
    if conditions:
        stmt = stmt.where(and_(*conditions))

    # Группируем по дате и методу оплаты
    stmt = stmt.group_by(
        func.date(models.Ttransaction.date),
        models.Ttransaction.payment_method
    )
    stmt = stmt.order_by("date", "payment_method")

    result = await db.execute(stmt)
    
    # Словарь для маппинга методов оплаты
    payment_names = {
        1: "Наличные",
        2: "Карта", 
        3: "QR-оплата"
    }
    
    # Группируем данные по методам оплаты
    payment_data = {}
    for row in result:
        method = row.payment_method
        if method not in payment_data:
            payment_data[method] = []
        
        payment_data[method].append({
            "ds": row.date,
            "y": float(row.total_sum) if row.total_sum else 0,
            "count": row.count
        })

    # Формируем информацию о контексте для отображения в UI
    context_info = {
        "has_category_filter": bool(filter and filter.category),
        "category_name": filter.category if filter and filter.category else None,
        "has_payment_filter": bool(filter and filter.payment_method),
        "payment_name": payment_names.get(filter.payment_method) if filter and filter.payment_method else None
    }

    # Если выбран конкретный метод - прогнозируем только его
    if selected_payment and selected_payment in payment_data:
        data = payment_data[selected_payment]
        
        if len(data) < 5:
            return {
                "payment_method": selected_payment,
                "payment_name": payment_names.get(selected_payment, str(selected_payment)),
                "history": data,
                "forecast": [],
                "message": "Недостаточно данных для прогноза (нужно минимум 5 дней)",
                "context": context_info
            }
        
        df = pd.DataFrame(data)
        df['ds'] = pd.to_datetime(df['ds'])
        
        model = Prophet(
            yearly_seasonality=False,
            weekly_seasonality=True,
            daily_seasonality=False
        )
        model.fit(df)
        
        future = model.make_future_dataframe(periods=14)
        forecast = model.predict(future)
        
        forecast_data = forecast[['ds', 'yhat', 'yhat_lower', 'yhat_upper']].tail(14)
        forecast_data['ds'] = forecast_data['ds'].dt.strftime('%Y-%m-%d')
        
        return {
            "payment_method": selected_payment,
            "payment_name": payment_names.get(selected_payment, str(selected_payment)),
            "history": [{"ds": d["ds"].strftime("%Y-%m-%d") if isinstance(d["ds"], (pd.Timestamp, datetime, date)) else d["ds"],
                        "y": d["y"], "count": d["count"]} for d in data],
            "forecast": forecast_data.to_dict(orient="records"),
            "context": context_info
        }
    
    # Если метод не выбран - показываем тренды для всех методов
    all_forecasts = {}
    for method, data in payment_data.items():
        if len(data) >= 5:
            df = pd.DataFrame(data)
            df['ds'] = pd.to_datetime(df['ds'])
            
            model = Prophet(
                yearly_seasonality=False,
                weekly_seasonality=True,
                daily_seasonality=False
            )
            model.fit(df)
            
            future = model.make_future_dataframe(periods=14)
            forecast = model.predict(future)
            
            forecast_data = forecast[['ds', 'yhat']].tail(14)
            forecast_data['ds'] = forecast_data['ds'].dt.strftime('%Y-%m-%d')
            
            all_forecasts[method] = {
                "method_name": payment_names.get(method, str(method)),
                "history": [{"ds": d["ds"].strftime("%Y-%m-%d") if isinstance(d["ds"], (pd.Timestamp, datetime, date)) else d["ds"],
                            "y": d["y"], "count": d["count"]} for d in data],
                "forecast": forecast_data.to_dict(orient="records")
            }
    
    return {
        "all_methods": all_forecasts,
        "payment_names": payment_names,
        "context": context_info
    }
# Эндпоинт для отдачи HTML-страницы
@app.get("/", response_class=HTMLResponse)
async def index():
    index_path = FRONTEND_DIR / "index.html"
    if index_path.exists():
        return FileResponse(index_path)
    return HTMLResponse("<h1>index.html not found</h1>", status_code=404)


# API для данных (GET)
@app.get('/api/data/')
async def get_data(db: AsyncSession = Depends(get_db)):
    return {
        'ui': await get_table_ui(db),
        'age_categories': await get_table_age(db),
        'age_categories_2': await get_table_age_2(db),
        'transtions': await get_table_transtions(db),
        'transtions_type': await get_table_transtions_type(db),
        'transtions_by_city': await get_table_transtions_by_city(db),
        'trend': await get_transactions_trend(db),
        'payment_trend': await get_payment_methods_trend(db)
    }





# --- ОБНОВИТЬ POST API ---
@app.post('/api/')
async def filter_data(filter: Filter, db: AsyncSession = Depends(get_db)):
    return {
        'ui': await get_table_ui(db, filter),
        'age_categories': await get_table_age(db, filter),
        'age_categories_2': await get_table_age_2(db, filter),
        'transtions': await get_table_transtions(db, filter),
        'transtions_type': await get_table_transtions_type(db,filter),
        'transtions_by_city': await get_table_transtions_by_city(db, filter),
        'trend': await get_transactions_trend(db, filter),
        'payment_trend': await get_payment_methods_trend(db, filter)
    }