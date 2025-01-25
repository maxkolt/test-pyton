from fastapi import FastAPI, Request
from aiogram import types, Bot, Dispatcher
import os

app = FastAPI()  # Создание экземпляра FastAPI

TELEGRAM_API_TOKEN = os.getenv("TELEGRAM_API_TOKEN")
bot = Bot(token=TELEGRAM_API_TOKEN)
dp = Dispatcher(bot)

@app.post("/webhook")
async def webhook(request: Request):
    json_data = await request.json()
    update = types.Update(**json_data)  # Преобразуем данные в объект Update
    await dp.process_update(update)  # Обработка обновлений через aiogram
    return {"status": "ok"}

@app.get("/")
async def root():
    return {"message": "Webhook is active"}
