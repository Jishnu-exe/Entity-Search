from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict


class ProductOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    sku: Optional[str]
    title: str
    description: Optional[str]
    category: Optional[str]
    image_path: str
    attributes: Optional[Dict[str, Any]]
    score: Optional[float] = None


class SearchResponse(BaseModel):
    results: List[ProductOut]
    took_ms: int


class ProductListResponse(BaseModel):
    items: List[ProductOut]
    total: int
    limit: int
    offset: int
