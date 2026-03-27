from pathlib import Path
from pydantic_settings import BaseSettings


BASE_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    app_name: str = "Finance Tracker"
    debug: bool = True
    database_url: str = f"sqlite:///{BASE_DIR}/data/finance.db"
    upload_dir: Path = BASE_DIR / "uploads"
    max_upload_size_mb: int = 50

    class Config:
        env_file = ".env"


settings = Settings()
settings.upload_dir.mkdir(parents=True, exist_ok=True)
