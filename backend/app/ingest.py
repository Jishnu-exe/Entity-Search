import argparse
import json
from pathlib import Path
from typing import Any, Dict, Optional
from urllib.parse import urlparse

import pandas as pd
from PIL import Image
from sqlalchemy import select
from sqlalchemy.orm import Session
from tqdm import tqdm

from .db import SessionLocal, init_db
from .embeddings import get_embedding_model
from .models import Product


def parse_attributes(raw: Any) -> Optional[Dict[str, Any]]:
    if raw is None or (isinstance(raw, float) and pd.isna(raw)):
        return None
    if isinstance(raw, dict):
        return raw
    if isinstance(raw, str) and raw.strip():
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            return {"raw": raw}
    return None


def resolve_image_path(image_root: Path, image_path: str) -> Path:
    candidate = Path(image_path)
    if candidate.is_absolute():
        return candidate
    return image_root / candidate


def normalize_value(raw: Any) -> Optional[str]:
    if raw is None or (isinstance(raw, float) and pd.isna(raw)):
        return None
    return str(raw)


def normalize_image_path(image_root: Path, raw: Any) -> str:
    text = str(raw)
    parsed = urlparse(text)
    if parsed.scheme in {"http", "https"}:
        return text

    resolved = resolve_image_path(image_root, text).resolve()
    root = image_root.resolve()
    try:
        return resolved.relative_to(root).as_posix()
    except ValueError:
        return text


def upsert_product(session: Session, data: Dict[str, Any]) -> None:
    sku = data.get("sku")
    existing = None
    if sku:
        existing = session.execute(select(Product).where(Product.sku == sku)).scalar_one_or_none()

    if existing:
        for key, value in data.items():
            setattr(existing, key, value)
    else:
        session.add(Product(**data))


def ingest(csv_path: Path, image_root: Path) -> None:
    init_db()
    df = pd.read_csv(csv_path)
    model = get_embedding_model()

    required = {"title", "image_path"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Missing required columns: {', '.join(sorted(missing))}")

    session = SessionLocal()
    try:
        for _, row in tqdm(df.iterrows(), total=len(df), desc="Embedding"):
            raw_path = str(row["image_path"])
            resolved_path = resolve_image_path(image_root, raw_path)
            image = Image.open(resolved_path).convert("RGB")
            embedding = model.embed_image(image)

            payload = {
                "sku": normalize_value(row.get("sku")) if "sku" in row else None,
                "title": str(row.get("title")),
                "description": normalize_value(row.get("description")) if "description" in row else None,
                "category": normalize_value(row.get("category")) if "category" in row else None,
                "image_path": normalize_image_path(image_root, raw_path),
                "attributes": parse_attributes(row.get("attributes")),
                "embedding": embedding,
            }
            upsert_product(session, payload)

        session.commit()
    finally:
        session.close()


def main() -> None:
    parser = argparse.ArgumentParser(description="Batch ingest product images into pgvector")
    parser.add_argument("--csv", required=True, help="Path to CSV file")
    parser.add_argument("--image-root", required=True, help="Root folder for image files")
    args = parser.parse_args()

    ingest(Path(args.csv), Path(args.image_root))


if __name__ == "__main__":
    main()
