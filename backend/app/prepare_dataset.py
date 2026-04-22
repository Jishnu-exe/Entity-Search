import argparse
import json
from pathlib import Path
from typing import Dict, Optional

import pandas as pd


def build_image_index(image_root: Path) -> Dict[str, str]:
    index: Dict[str, str] = {}
    for path in image_root.rglob("*"):
        if not path.is_file():
            continue
        if path.suffix.lower() not in {".jpg", ".jpeg", ".png"}:
            continue
        index[path.name] = path.relative_to(image_root).as_posix()
    return index


def normalize_image_value(value: str) -> str:
    text = value.replace("\\", "/").strip()
    suffix = Path(text).suffix.lower()
    if suffix:
        return text
    return f"{text}.jpg"


def resolve_image_relative(
    image_root: Path, value: str, image_index: Dict[str, str]
) -> Optional[str]:
    if not value:
        return None

    normalized = normalize_image_value(value)
    if "/" in normalized:
        candidate = (image_root / normalized).resolve()
        if candidate.exists():
            return candidate.relative_to(image_root).as_posix()

    filename = Path(normalized).name
    return image_index.get(filename)


def build_attributes(row: pd.Series) -> Dict[str, str]:
    fields = {
        "gender": row.get("Gender"),
        "sub_category": row.get("SubCategory"),
        "product_type": row.get("ProductType"),
        "color": row.get("Colour"),
        "usage": row.get("Usage"),
    }

    return {key: str(value) for key, value in fields.items() if value and str(value).strip()}


def prepare(csv_path: Path, image_root: Path, output_path: Path) -> None:
    df = pd.read_csv(csv_path)
    image_index = build_image_index(image_root)

    rows = []
    for _, row in df.iterrows():
        image_value = str(row.get("Image") or "").strip()
        image_rel = resolve_image_relative(image_root, image_value, image_index)
        if not image_rel:
            continue

        attributes = build_attributes(row)
        payload = {
            "sku": row.get("ProductId"),
            "title": row.get("ProductTitle"),
            "description": row.get("ProductType"),
            "category": row.get("Category"),
            "image_path": image_rel,
            "attributes": json.dumps(attributes) if attributes else None,
        }
        rows.append(payload)

    output_df = pd.DataFrame(rows)
    output_df.to_csv(output_path, index=False)


def main() -> None:
    parser = argparse.ArgumentParser(description="Prepare products.csv for ingestion")
    parser.add_argument("--csv", required=True, help="Path to fanshin.csv")
    parser.add_argument("--image-root", required=True, help="Root folder containing apparel/ and footwear/")
    parser.add_argument("--output", required=True, help="Path to write products.csv")
    args = parser.parse_args()

    prepare(Path(args.csv), Path(args.image_root), Path(args.output))


if __name__ == "__main__":
    main()
