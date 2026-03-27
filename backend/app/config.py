from pathlib import Path
from pydantic_settings import BaseSettings


BASE_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    app_name: str = "Finance Tracker"
    debug: bool = False
    database_url: str = f"sqlite:///{BASE_DIR}/data/finance.db"
    upload_dir: Path = BASE_DIR / "uploads"
    max_upload_size_mb: int = 50
    allowed_origins: str = "http://localhost:5173"

    class Config:
        env_file = ".env"


settings = Settings()

# Fix Render's postgres:// → postgresql:// (SQLAlchemy 2.x requirement)
if settings.database_url.startswith("postgres://"):
    settings.database_url = settings.database_url.replace("postgres://", "postgresql://", 1)

settings.upload_dir.mkdir(parents=True, exist_ok=True)
