from typing import List, Optional

from sqlalchemy import Select, select
from sqlalchemy.orm import Session

from .config import settings
from .models import Product


def build_search_query(
    query_vector: List[float],
    category: Optional[str],
    limit: int,
) -> Select:
    distance = Product.embedding.cosine_distance(query_vector).label("distance")
    stmt = select(Product, distance)

    if category:
        stmt = stmt.where(Product.category == category)

    return stmt.order_by(distance).limit(limit)


def search_similar_products(
    session: Session,
    query_vector: List[float],
    category: Optional[str] = None,
    limit: Optional[int] = None,
) -> List[tuple[Product, float]]:
    final_limit = limit or settings.max_results
    stmt = build_search_query(query_vector, category, final_limit)
    results = session.execute(stmt).all()

    return [(row[0], float(row[1])) for row in results]
