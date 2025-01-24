from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.db import async_session
from app.models.product import Product
import httpx

router = APIRouter()

WILDBERRIES_API = "https://card.wb.ru/cards/v1/detail?appType=1&curr=rub&dest=-1257786&spp=30&nm="

async def get_db():
    async with async_session() as session:
        yield session

@router.post("/api/v1/products")
async def create_product(data: dict, db: AsyncSession = Depends(get_db)):
    artikul = data.get("artikul")
    if not artikul:
        raise HTTPException(status_code=400, detail="Artikul is required")

    # Fetch product data from Wildberries API
    async with httpx.AsyncClient() as client:
        response = await client.get(WILDBERRIES_API + artikul)
        if response.status_code != 200:
            raise HTTPException(status_code=404, detail="Product not found")

        product_data = response.json()
        card_data = product_data.get("data", {}).get("products", [])[0]

        if not card_data:
            raise HTTPException(status_code=404, detail="Product data is missing")

        # Extract required fields
        name = card_data.get("name")
        price = card_data.get("priceU", 0) / 100
        rating = card_data.get("rating")
        stock_quantity = sum([sizes.get("qty", 0) for sizes in card_data.get("sizes", [])])

        # Save to database
        new_product = Product(
            artikul=artikul,
            name=name,
            price=price,
            rating=rating,
            stock_quantity=stock_quantity
        )
        db.add(new_product)
        await db.commit()

    return {"message": "Product added successfully", "product": new_product}
