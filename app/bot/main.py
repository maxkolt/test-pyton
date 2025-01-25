from aiogram import Bot, Dispatcher, types
from aiogram.types import KeyboardButton, ReplyKeyboardMarkup
from aiogram.utils import executor
from app.core.db import async_session
from app.models.product import Product
from sqlalchemy.future import select  # Импортируем метод select для запросов
import os

API_TOKEN = os.getenv("TELEGRAM_API_TOKEN", "7598413210:AAE_lEjw-X20AT_WQE09Gd_FEqsvVGuoYMA")

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

# Keyboards
button_get_data = KeyboardButton("Get Product Data")
keyboard = ReplyKeyboardMarkup(resize_keyboard=True).add(button_get_data)

@dp.message_handler(commands=["start"])
async def start_handler(message: types.Message):
    await message.answer("Добро пожаловать! Используйте кнопку ниже, чтобы получить данные о продукте.", reply_markup=keyboard)

@dp.message_handler(lambda message: message.text == "Get Product Data")
async def get_data_handler(message: types.Message):
    await message.answer("Пожалуйста, введите артикул продукта:")

@dp.message_handler()
async def fetch_product_data(message: types.Message):
    artikul = message.text.strip()
    if not artikul.isalnum():
        await message.answer("Неверный артикул. Пожалуйста, введите правильный артикул (только буквы и цифры).")
        return

    try:
        async with async_session() as session:
            async with session.begin():
                result = await session.execute(select(Product).where(Product.artikul == artikul))
                product = result.scalars().first()
                if product:
                    response = (f"Product Data:\n"
                                f"Name: {product.name}\n"
                                f"Price: {product.price} RUB\n"
                                f"Rating: {product.rating}\n"
                                f"Stock Quantity: {product.stock_quantity}")
                    await message.answer(response)
                else:
                    await message.answer("Продукт не найден.")
    except Exception as e:
        await message.answer("При обработке вашего запроса произошла ошибка.")
        print(f"Error: {e}")
# Main entry point for the bot
if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)
