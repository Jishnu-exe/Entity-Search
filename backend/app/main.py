import io
import time
from pathlib import Path
from typing import Optional
from urllib.parse import urlparse

from fastapi import Depends, FastAPI, File, Form, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from PIL import Image
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from .config import settings
from .db import get_session, init_db
from .embeddings import get_embedding_model
from .models import Product
from .schemas import ProductListResponse, ProductOut, SearchResponse
from .search import search_similar_products

app = FastAPI(title="Image Search API")
app.mount(
    "/images",
    StaticFiles(directory=settings.image_root, check_dir=False),
    name="images",
)

origins = [origin.strip() for origin in settings.cors_origins.split(",") if origin.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup() -> None:
    Path(settings.image_root).mkdir(parents=True, exist_ok=True)
    init_db()


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


def build_image_url(image_path: str) -> str:
    if not image_path:
        return image_path
    parsed = urlparse(image_path)
    if parsed.scheme in {"http", "https"}:
        return image_path
    base = settings.image_base_url.rstrip("/")
    return f"{base}/{image_path.lstrip('/')}"


@app.post("/search", response_model=SearchResponse)
async def search(
    image: UploadFile = File(...),
    category: Optional[str] = Form(default=None),
    limit: Optional[int] = Form(default=None),
    session: Session = Depends(get_session),
) -> SearchResponse:
    start = time.perf_counter()
    raw = await image.read()
    pil_image = Image.open(io.BytesIO(raw)).convert("RGB")
    model = get_embedding_model()
    query_vector = model.embed_image(pil_image)

    results = search_similar_products(session, query_vector, category, limit)
    payload = []
    for product, distance in results:
        score = max(0.0, 1.0 - distance)
        item = ProductOut.model_validate(product)
        item.score = score
        item.image_path = build_image_url(product.image_path)
        payload.append(item)

    took_ms = int((time.perf_counter() - start) * 1000)
    return SearchResponse(results=payload, took_ms=took_ms)


@app.get("/products", response_model=ProductListResponse)
def list_products(
    limit: int = 50,
    offset: int = 0,
    category: Optional[str] = None,
    session: Session = Depends(get_session),
) -> ProductListResponse:
    safe_limit = max(1, min(limit, 200))
    safe_offset = max(0, offset)

    count_stmt = select(func.count()).select_from(Product)
    if category:
        count_stmt = count_stmt.where(Product.category == category)
    total = session.execute(count_stmt).scalar_one()

    stmt = select(Product)
    if category:
        stmt = stmt.where(Product.category == category)
    stmt = stmt.order_by(Product.id.desc()).limit(safe_limit).offset(safe_offset)

    items = []
    for product in session.execute(stmt).scalars().all():
        item = ProductOut.model_validate(product)
        item.image_path = build_image_url(product.image_path)
        items.append(item)

    return ProductListResponse(items=items, total=total, limit=safe_limit, offset=safe_offset)
