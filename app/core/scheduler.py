from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.core.db import async_session
from app.models.product import Product
from fastapi import APIRouter, HTTPException
import httpx
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Wildberries API URL
WILDBERRIES_API = "https://card.wb.ru/cards/v1/detail?appType=1&curr=rub&dest=-1257786&spp=30&nm="

router = APIRouter()

async def update_product_data(artikul: str):
    try:
        async with async_session() as session:
            async with session.begin():
                product = await session.get(Product, artikul)
                if not product:
                    logger.warning(f"Продукт с артикулом {artikul} не найден")
                    return

                async with httpx.AsyncClient() as client:
                    response = await client.get(WILDBERRIES_API + artikul)
                    if response.status_code != 200:
                        logger.error(f"Ошибка при запросе Wildberries API: {response.status_code}")
                        return

                    product_data = response.json()
                    card_data = product_data.get("data", {}).get("products", [])[0]

                    if card_data:
                        product.price = card_data.get("priceU", 0) / 100
                        product.rating = card_data.get("rating")
                        product.stock_quantity = sum(
                            [sizes.get("qty", 0) for sizes in card_data.get("sizes", [])]
                        )
                        await session.commit()
                        logger.info(f"Обновлены данные продукта: {artikul}")
    except Exception as e:
        logger.error(f"Ошибка при обновлении продукта {artikul}: {e}")

scheduler = AsyncIOScheduler()

@router.get("/api/v1/subscribe/{artikul}")
async def subscribe_product(artikul: str):
    try:
        # Добавление задачи в планировщик
        scheduler.add_job(
            update_product_data,
            IntervalTrigger(minutes=30),
            args=[artikul],
            id=f"update_{artikul}",
            replace_existing=True,
        )
        logger.info(f"Задача для обновления продукта {artikul} добавлена в планировщик")
        return {"message": f"Subscribed to updates for product {artikul}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error subscribing to product: {e}")

async def start_scheduler():
    try:
        scheduler.start()
        logger.info("Планировщик запущен")

        # Запуск задач для всех продуктов в базе данных
        async with async_session() as session:
            async with session.begin():
                result = await session.execute(select(Product))
                products = result.scalars().all()
                for product in products:
                    scheduler.add_job(
                        update_product_data,
                        IntervalTrigger(minutes=30),
                        args=[product.artikul],
                        id=f"update_{product.artikul}",
                        replace_existing=True,
                    )
                    logger.info(f"Добавлена задача для обновления продукта {product.artikul}")
    except Exception as e:
        logger.error(f"Ошибка при запуске планировщика: {e}")

# Остановка планировщика при завершении приложения
async def shutdown_scheduler():
    try:
        scheduler.shutdown()
        logger.info("Планировщик остановлен")
    except Exception as e:
        logger.error(f"Ошибка при остановке планировщика: {e}")
