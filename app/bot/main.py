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
    await message.answer("Welcome! Use the button below to get product data.", reply_markup=keyboard)

@dp.message_handler(lambda message: message.text == "Get Product Data")
async def get_data_handler(message: types.Message):
    await message.answer("Please enter the product artikul:")

@dp.message_handler()
async def fetch_product_data(message: types.Message):
    artikul = message.text
    async with async_session() as session:
        async with session.begin():
            # Используем select для выполнения запроса
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
                await message.answer("Product not found.")

# Main entry point for the bot
if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)
