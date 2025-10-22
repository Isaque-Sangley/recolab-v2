"""
FastAPI Application

Aplicação principal do RecoLab.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from ..infrastructure.database import get_database_config
from .config import get_settings
from .error_handlers import register_error_handlers
from .routers import movies, ratings, recommendations, users


# Lifespan events (startup/shutdown)
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager.

    Executa código no startup e shutdown da aplicação.
    """

    print("🚀 Starting RecoLab API...")

    # Inicializa banco de dados
    db_config = get_database_config()

    # TODO: Criar tabelas (em produção, usar migrations)
    # await db_config.create_tables()

    print("Database initialized")
    print("RecoLab API ready!")

    yield

    # Shutdown
    print("Shutting down RecoLab API...")

    # Fecha conexões do banco
    await db_config.close()

    print("Database connections closed")
    print("RecoLab API stopped")


# Create app
def create_app() -> FastAPI:
    """
    Factory function para criar aplicação FastAPI.

    Returns:
        FastAPI app configurado
    """
    settings = get_settings()

    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description=settings.app_description,
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
    )

    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=settings.cors_allow_credentials,
        allow_methods=settings.cors_allow_methods,
        allow_headers=settings.cors_allow_headers,
    )

    # Error handlers
    register_error_handlers(app)

    # Routers
    app.include_router(users.router, prefix=settings.api_prefix)
    app.include_router(movies.router, prefix=settings.api_prefix)
    app.include_router(ratings.router, prefix=settings.api_prefix)
    app.include_router(recommendations.router, prefix=settings.api_prefix)

    # Health check
    @app.get("/health")
    async def health_check():
        """Health check endpoint"""
        return {"status": "healthy", "app": settings.app_name, "version": settings.app_version}

    # Root
    @app.get("/")
    async def root():
        """Root endpoint"""
        return {
            "message": f"Welcome to {settings.app_name}!",
            "version": settings.app_version,
            "docs": "/docs",
            "redoc": "/redoc",
        }

    return app


# Create app instance
app = create_app()


if __name__ == "__main__":
    import uvicorn

    settings = get_settings()

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=settings.debug, log_level="info")
