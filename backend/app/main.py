from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import engine
from app.routers import health, screener, analysis, readiness, portfolio, journal, config
from app.utils.error_handlers import register_error_handlers


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: verify DB connection
    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))
    yield
    # Shutdown: dispose engine
    engine.dispose()


from sqlalchemy import text

app = FastAPI(
    title="MOSI API",
    description="Margin of Safety Investing — 3-layer stock evaluation system for Indian equities",
    version=settings.API_VERSION,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

register_error_handlers(app)

app.include_router(health.router, prefix="/api/v1/health")
app.include_router(screener.router, prefix="/api/v1/screener")
app.include_router(analysis.router, prefix="/api/v1/analysis")
app.include_router(readiness.router, prefix="/api/v1/readiness")
app.include_router(portfolio.router, prefix="/api/v1/portfolio")
app.include_router(journal.router, prefix="/api/v1/journal")
app.include_router(config.router, prefix="/api/v1/config")
