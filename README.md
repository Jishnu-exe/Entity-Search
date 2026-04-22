# Entity Search Web Application

## Overview
This project provides image-to-image product search using deep visual embeddings. Users upload an inspiration image to discover visually similar products based on textures, patterns, and shapes. The system bridges a Python-based embedding pipeline with a React frontend and stores both relational metadata and high-dimensional vectors in PostgreSQL using pgvector.

## Features
- Image-to-image similarity search using EfficientNet-B0 embeddings.
- FastAPI backend with upload search and product listing endpoints.
- PostgreSQL + pgvector for vector search and metadata filtering.
- Batch ingestion pipeline for CSV + image folders.
- React frontend for upload, filters, and results display.
- Static image serving for local datasets.

## Architecture
1. Ingestion pipeline reads `products.csv`, loads images from disk, generates embeddings, and stores them in Postgres.
2. The backend computes an embedding for the query image and runs a cosine similarity query against pgvector.
3. The frontend uploads the query image and renders ranked matches.

## Repository Layout
```
backend/          FastAPI app, ingestion, embedding code
frontend/         React (Vite) client
infra/            Docker Compose for Postgres + backend
data/             Local datasets (not committed)
```

## Requirements
- Python 3.11
- Node.js 18+
- Docker Desktop (for Postgres + pgvector)
- Windows: Microsoft Visual C++ Redistributable (required by PyTorch)

## Quick Start (recommended)
### 1) Start Postgres with pgvector
```
cd <repo-root>
docker compose -f infra/docker-compose.yml up -d db
```

### 2) Create and activate a virtual environment
```
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### 3) Set runtime environment variables
```
$env:DATABASE_URL="postgresql+psycopg://postgres:postgres@localhost:5432/imagesearch"
$env:IMAGE_ROOT="<repo-root>/data/images"
$env:IMAGE_BASE_URL="http://localhost:8000/images"
$env:CORS_ORIGINS="http://localhost:5173"
```

### 4) Prepare data and ingest
Place your dataset under `data/images` and create `data/products.csv`.

If your dataset needs a CSV conversion step, run a converter script that outputs `data/products.csv`.
Example:
```
cd <repo-root>/backend
python -m app.prepare_dataset --csv ../data/source.csv --image-root ../data/images --output ../data/products.csv
```

Then ingest:
```
python -m app.ingest --csv ../data/products.csv --image-root ../data/images
```

### 5) Run the backend
```
cd <repo-root>/backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 6) Run the frontend
```
cd <repo-root>/frontend
npm install
npm run dev
```

Open the app at `http://localhost:5173`.

## Data Format
The ingestion pipeline requires a CSV with at least:
- `title`
- `image_path` (relative to `data/images`)

Optional columns:
- `sku`, `category`, `description`, `attributes`

Example row:
```
sku,title,category,description,image_path,attributes
sku-1001,Textured knit hoodie,Apparel,Hoodie,apparel/men/1001.jpg,"{\"color\": \"navy\"}"
```

## API Endpoints
- `GET /health`
- `POST /search` (multipart form)
  - `image` (file), `category` (optional), `limit` (optional)
- `GET /products?limit=50&offset=0&category=Apparel`

Example search request:
```
curl -X POST "http://localhost:8000/search" \
  -F "image=@data/images/apparel/sample.jpg" \
  -F "category=Apparel" \
  -F "limit=12"
```

## Configuration
These can be set via environment variables or a `.env` file in `backend/`.
- `DATABASE_URL` (default: `postgresql+psycopg://postgres:postgres@db:5432/imagesearch`)
- `CORS_ORIGINS` (default: `http://localhost:5173`)
- `IMAGE_ROOT` (default: `/data/images`)
- `IMAGE_BASE_URL` (default: `http://localhost:8000/images`)
- `EMBEDDING_MODEL` (default: `efficientnet_b0`)
- `EMBEDDING_DIM` (default: `1280`)
- `MAX_RESULTS` (default: `24`)

## Troubleshooting
- PyTorch on Windows requires the Microsoft Visual C++ Redistributable.
- If PyTorch fails with NumPy 2.x, pin NumPy to 1.26.x:
  ```
  pip install "numpy==1.26.4"
  ```
- If the backend cannot connect to Postgres, confirm Docker is running and port 5432 is free.

## Production Notes
- Use a managed Postgres with pgvector (Supabase, Neon, Render).
- Store images in object storage and save full URLs in `image_path`.
- Set `CORS_ORIGINS` to your production frontend URL.
