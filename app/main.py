from fastapi import FastAPI, Form, Request, Depends, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse, FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path
import sys
import os
from sqlalchemy.sql import over
from sqlalchemy.orm import selectinload, joinedload
# Добавляем родительскую директорию в путь
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app.db.database import Base, engine, get_db, engine_secret, get_secret_db
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text, and_, or_, select, func, desc
from fastapi import File, UploadFile
from app import models
from datetime import datetime, timedelta, date
from typing import Dict, List, Optional
import json


# uvicorn app.main:app --reload


app = FastAPI()


BASE_DIR = Path(__file__).parent.parent
FRONTEND_DIR = BASE_DIR / "frontend"

app.mount("/css", StaticFiles(directory=FRONTEND_DIR / "css"), name="css")
app.mount("/js", StaticFiles(directory=FRONTEND_DIR / "js"), name="js")





# @app.get("/")
# async def show_top_most_category_region(db: AsyncSession = Depends(get_db)):
#     subq = (
#         select(
#             models.Ttransaction.place_id,
#             models.Ttransaction.mcc_id,
#             func.count().label("cnt"),
#             func.row_number().over(
#                 partition_by=models.Ttransaction.place_id,
#                 order_by=desc(func.count())
#             ).label("rn")
#         )
#         .group_by(models.Ttransaction.place_id, models.Ttransaction.mcc_id)
#         .subquery()
#     )

#     query = (
#         select(
#             models.Place.city,
#             models.Mcc.name,
#             subq.c.cnt
#         )
#         .join(models.Place, models.Place.id == subq.c.place_id)
#         .join(models.Mcc, models.Mcc.id == subq.c.mcc_id)
#         .where(subq.c.rn <= 5)
#         .order_by(models.Place.city, subq.c.cnt.desc())
#     )

#     result = await db.execute(query)

#     return [
#         {
#             "city": row.city,
#             "category": row.name,
#             "count": row.cnt
#         }
#         for row in result
#     ]

@app.get("/")
async def show_trend_by_sex(db: AsyncSession = Depends(get_db)):
    query_1 = (
        select(
            models.User.sex,
            models.Ttransaction.mcc_id,
            func.count().label('cnt'),
            func.row_number().over(
                partition_by=models.User.sex,
                order_by=desc(func.count())).label('rn')
                )
            .join(models.User, models.User.user_id == models.Ttransaction.user_id)
            .group_by(models.User.sex, models.Ttransaction.mcc_id).subquery()
            )

    users = (
        select(
            query_1.c.sex,
            query_1.c.cnt,
            models.Mcc.name,
            query_1.c.rn,

        )
        .join(models.Mcc,models.Mcc.id==query_1.c.mcc_id)
        .where(query_1.c.rn <= 5)
        .order_by(query_1.c.sex, query_1.c.cnt.desc())
    )
    user = await db.execute(users)

    return [
        {
            "sex": row.sex,
            "category": row.name,
            "count": row.cnt
        }
        for row in user
    ]

# #api.post("/api/User")
# async def parce_json_Mms(link : json):
# #api.post("/api/User")
# async def parce_json_Place(link : json):
# async def parce_json_Stack(link : json):
# async def parce_json_Ttransaction(link : json):
# async def parce_json_Support(link : json):
# async def parce_json_Session(link : json):

    