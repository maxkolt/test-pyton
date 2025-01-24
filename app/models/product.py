from app.core.base import Base  # Импорт базового класса
from sqlalchemy import Column, Integer, String, Float

class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    artikul = Column(String, unique=True, nullable=False)
    name = Column(String, nullable=False)
    price = Column(Float, nullable=False)
    rating = Column(Float, nullable=True)
    stock_quantity = Column(Integer, nullable=False)
