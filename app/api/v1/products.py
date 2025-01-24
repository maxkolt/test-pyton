from fastapi import APIRouter, HTTPException, Depends
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.core.db import async_session
from app.models.product import Product
import httpx

router = APIRouter()
scheduler = AsyncIOScheduler()

WILDBERRIES_API = "https://card.wb.ru/cards/v1/detail?appType=1&curr=rub&dest=-1257786&spp=30&nm={artikul}"

async def fetch_product_data(artikul: str):
    """
    Функция для получения данных товара с Wildberries API.
    """
    url = WILDBERRIES_API.format(artikul=artikul)
    async with httpx.AsyncClient() as client:
        response = await client.get(url)
        if response.status_code == 200:
            data = response.json()
            product_info = data.get("data", {}).get("products", [])[0]
            return {
                "artikul": product_info.get("id"),
                "name": product_info.get("name"),
                "price": product_info.get("salePriceU", 0) / 100,  # Цена может быть в копейках
                "rating": product_info.get("rating", 0),
                "stock_quantity": product_info.get("quantity", 0)  # Заменяем null на 0
            }
        else:
            raise HTTPException(status_code=response.status_code, detail=f"Ошибка: {response.text}")

async def get_db():
    async with async_session() as session:
        yield session

@router.get("/api/v1/subscribe/{artikul}")
async def subscribe_product(artikul: str, db: AsyncSession = Depends(get_db)):
    """
    Эндпоинт для подписки на обновление данных товара с указанным артикулом каждые 30 минут.
    """
    # Проверяем, существует ли уже задача с таким ID
    job_id = f"update-{artikul}"
    if scheduler.get_job(job_id):
        raise HTTPException(status_code=409, detail="Subscription for this artikul already exists.")

    async def update_task():
        """
        Задача для обновления данных товара.
        """
        try:
            product_data = await fetch_product_data(artikul)
            result = await db.execute(select(Product).where(Product.artikul == artikul))
            existing_product = result.scalars().first()

            if existing_product:
                # Обновляем данные продукта
                existing_product.name = product_data["name"]
                existing_product.price = product_data["price"]
                existing_product.rating = product_data["rating"]
                existing_product.stock_quantity = product_data["stock_quantity"]
                db.add(existing_product)
                await db.commit()
                print(f"Updated product {artikul} successfully.")
            else:
                # Если продукта нет, создаём новый
                new_product = Product(**product_data)
                db.add(new_product)
                await db.commit()
                print(f"Created new product {artikul} successfully.")
        except Exception as e:
            print(f"Error updating product {artikul}: {e}")

    # Добавляем задачу в планировщик
    scheduler.add_job(update_task, "interval", minutes=30, id=job_id)
    scheduler.start()

    return {"message": f"Subscribed to updates for artikul {artikul}"}
