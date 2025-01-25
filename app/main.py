from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.security import OAuth2PasswordBearer
from app.api.v1.products import router as products_router
from app.core.scheduler import start_scheduler
from aiogram import Bot, Dispatcher
from aiogram.types import Update
import asyncio
import os

# OAuth2 configuration
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
TELEGRAM_API_TOKEN = os.getenv("TELEGRAM_API_TOKEN", "7598413210:AAE_lEjw-X20AT_WQE09Gd_FEqsvVGuoYMA")
WEBHOOK_PATH = "/webhook"
WEBHOOK_URL = "https://test-pyton-production.up.railway.app/webhook"  # Замените на URL вашего Railway приложения

bot = Bot(token=TELEGRAM_API_TOKEN)
dp = Dispatcher(bot)

def fake_decode_token(token: str):
    if token == "secrettoken":
        return {"sub": "authorized_user"}
    else:
        raise HTTPException(status_code=401, detail="Invalid token")

def get_current_user(token: str = Depends(oauth2_scheme)):
    return fake_decode_token(token)

app = FastAPI()

app.include_router(products_router, dependencies=[Depends(get_current_user)])

@app.on_event("startup")
async def startup_event():
    """
    Настройка планировщика и регистрация вебхука.
    """
    asyncio.create_task(start_scheduler())
    await bot.set_webhook(WEBHOOK_URL)

@app.on_event("shutdown")
async def shutdown_event():
    """
    Удаление вебхука при выключении приложения.
    """
    await bot.delete_webhook()

@app.post(WEBHOOK_PATH, response_model=None)  # Убираем response_model
async def process_webhook(update: Update):
    """
    Обработка обновлений, поступающих через вебхук.
    """
    await dp.process_update(update)
