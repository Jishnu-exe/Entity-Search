from sqlalchemy import Column, DateTime, Integer, JSON, String, Text, func
from pgvector.sqlalchemy import Vector

from .config import settings
from .db import Base


class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True)
    sku = Column(String(64), unique=True, index=True, nullable=True)
    title = Column(String(200), index=True, nullable=False)
    description = Column(Text, nullable=True)
    category = Column(String(100), index=True, nullable=True)
    image_path = Column(String(500), nullable=False)
    attributes = Column(JSON, nullable=True)
    embedding = Column(Vector(settings.embedding_dim), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
