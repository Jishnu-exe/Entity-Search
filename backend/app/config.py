from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str = "postgresql+psycopg://postgres:postgres@db:5432/imagesearch"
    embedding_model: str = "efficientnet_b0"
    embedding_dim: int = 1280
    max_results: int = 24
    cors_origins: str = "http://localhost:5173"
    image_root: str = "/data/images"
    image_base_url: str = "http://localhost:8000/images"

    model_config = SettingsConfigDict(env_prefix="", env_file=".env", extra="ignore")


settings = Settings()
