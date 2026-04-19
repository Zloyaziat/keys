from fastapi import FastAPI, Depends
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app.db.database import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from pydantic import BaseModel
from datetime import date, datetime
from typing import Optional

app = FastAPI()

BASE_DIR = Path(__file__).parent.parent
FRONTEND_DIR = BASE_DIR / "frontend"

app.mount("/css", StaticFiles(directory=FRONTEND_DIR / "css"), name="css")
app.mount("/js", StaticFiles(directory=FRONTEND_DIR / "js"), name="js")

class Filter(BaseModel):
    date_from: Optional[date] = None
    date_to: Optional[date] = None
    sex: Optional[str] = None
    age_from: Optional[int] = None
    age_to: Optional[int] = None
    min_sum: Optional[int] = None
    max_sum: Optional[int] = None
    payment_method: Optional[int] = None
    city: Optional[str] = None
    category: Optional[str] = None
    comparison_type: Optional[str] = None
    target_date: Optional[datetime] = None

@app.get("/", response_class=HTMLResponse)
async def index():
    index_path = FRONTEND_DIR / "index.html"
    if index_path.exists():
        return FileResponse(index_path)
    return HTMLResponse("<h1>index.html not found</h1>", status_code=404)

@app.get('/api/data/')
async def get_data(db: AsyncSession = Depends(get_db)):
    try:
        # Простейшие запросы к БД
        users = await db.execute(text("SELECT COUNT(*) FROM users"))
        users_count = users.scalar()
        
        trans = await db.execute(text("SELECT COUNT(*) FROM transaction"))
        trans_count = trans.scalar()
        
        mcc = await db.execute(text("SELECT COUNT(*) FROM mcc"))
        mcc_count = mcc.scalar()
        
        # Получаем несколько транзакций
        sample = await db.execute(text("SELECT * FROM transaction LIMIT 3"))
        sample_data = [dict(row._mapping) for row in sample]
        
        return {
            "status": "ok",
            "counts": {
                "users": users_count,
                "transactions": trans_count,
                "mcc": mcc_count
            },
            "sample_transactions": sample_data,
            "ui": [],
            "age_categories": [],
            "age_categories_2": [],
            "transtions": [],
            "transtions_type": {"combined": {"labels": [], "datasets": []}},
            "transtions_by_city": {},
            "trend": {"history": [], "forecast": [], "category": None},
            "payment_trend": {"all_methods": {}}
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }

@app.post('/api/')
async def filter_data(filter: Filter, db: AsyncSession = Depends(get_db)):
    return await get_data(db)