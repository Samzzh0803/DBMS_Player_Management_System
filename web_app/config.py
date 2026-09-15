import os


def normalize_database_url(url: str) -> str:
    if url.startswith("postgres://"):
        return url.replace("postgres://", "postgresql+psycopg://", 1)
    if url.startswith("postgresql://"):
        return url.replace("postgresql://", "postgresql+psycopg://", 1)
    return url


class Config:
    DATABASE_URL = normalize_database_url(
        os.getenv("DATABASE_URL", "sqlite:///player_management.db")
    )
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key-change-me")
    INIT_DB_ON_START = os.getenv("INIT_DB_ON_START", "false").lower() == "true"
