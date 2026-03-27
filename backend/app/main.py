from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import create_tables


def _seed():
    try:
        from app.database import SessionLocal
        from app.services.seed_service import seed_default_data
        db = SessionLocal()
        try:
            seed_default_data(db)
        finally:
            db.close()
    except Exception as exc:
        print(f"[WARNING] seed_default_data() failed or not yet available: {exc}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    create_tables()
    _seed()
    yield
    # Shutdown (nothing to do for now)


app = FastAPI(
    title=settings.app_name,
    version="1.0.0",
    lifespan=lifespan,
)

# ---------------------------------------------------------------------------
# CORS
# ---------------------------------------------------------------------------
_origins = [o.strip() for o in settings.allowed_origins.split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Routers  (imported lazily so missing modules don't crash startup)
# ---------------------------------------------------------------------------
def _include_router(module_path: str, prefix: str, tags: list[str]):
    try:
        import importlib
        module = importlib.import_module(module_path)
        app.include_router(module.router, prefix=prefix, tags=tags)
    except Exception as exc:
        print(f"[WARNING] Could not load router '{module_path}': {exc}")


_include_router("app.api.v1.accounts",     prefix="/api/v1/accounts",     tags=["accounts"])
_include_router("app.api.v1.transactions", prefix="/api/v1/transactions", tags=["transactions"])
_include_router("app.api.v1.categories",   prefix="/api/v1/categories",   tags=["categories"])
_include_router("app.api.v1.upload",       prefix="/api/v1/upload",       tags=["upload"])
_include_router("app.api.v1.reports",      prefix="/api/v1/reports",      tags=["reports"])
_include_router("app.api.v1.budgets",      prefix="/api/v1/budgets",      tags=["budgets"])


# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------
@app.get("/", tags=["health"])
async def health_check():
    return {"status": "ok", "app": settings.app_name}
