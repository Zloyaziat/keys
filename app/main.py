from fastapi import FastAPI, Form, Request, Depends, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse, FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path
import sys
import os

# Добавляем родительскую директорию в путь
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from .db.database import Base, engine, get_db, engine_secret, get_secret_db
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text, and_, or_, select, func
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

@app.get("/")
async def Show_top_most_category_region(db: AsyncSession = Depends(get_db)):
    users = await db.execute(select(models.Ttransaction).where())
    return{"message": "API is working", "status": "active"}





# #api.post("/api/User")
# async def parce_json_Mms(link : json):
# #api.post("/api/User")
# async def parce_json_Place(link : json):
# async def parce_json_Stack(link : json):
# async def parce_json_Ttransaction(link : json):
# async def parce_json_Support(link : json):
# async def parce_json_Session(link : json):

    