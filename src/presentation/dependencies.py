"""
Dependency Injection

Container de dependências para FastAPI.
Injeta repositories, services, etc nos endpoints.
"""

from fastapi import Depends
from functools import lru_cache
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession

from ..infrastructure.database import get_session, get_database_config
from ..infrastructure.persistence import (
    UserRepository,
    MovieRepository,
    RatingRepository,
    RecommendationRepository,
    ModelRepository
)
from ..infrastructure.ml import (
    ModelServer,
    ModelRegistry,
    FeatureStore,
    ModelTrainer
)
from ..domain.events import DomainEventBus
from ..application.services import (
    UserApplicationService,
    MovieApplicationService,
    RatingApplicationService,
    RecommendationApplicationService
)


# ============================================================================
# DATABASE SESSION
# ============================================================================

async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency para obter sessão do banco.
    
    Usage:
        @app.get("/users")
        async def get_users(session: AsyncSession = Depends(get_db_session)):
            ...
    """
    async for session in get_session():
        yield session


# ============================================================================
# REPOSITORIES
# ============================================================================

async def get_user_repository(
    session: AsyncSession = Depends(get_db_session)
) -> UserRepository:
    """Dependency: UserRepository"""
    return UserRepository(session)


async def get_movie_repository(
    session: AsyncSession = Depends(get_db_session)
) -> MovieRepository:
    """Dependency: MovieRepository"""
    return MovieRepository(session)


async def get_rating_repository(
    session: AsyncSession = Depends(get_db_session)
) -> RatingRepository:
    """Dependency: RatingRepository"""
    return RatingRepository(session)


async def get_recommendation_repository(
    session: AsyncSession = Depends(get_db_session)
) -> RecommendationRepository:
    """Dependency: RecommendationRepository"""
    return RecommendationRepository(session)


async def get_model_repository(
    session: AsyncSession = Depends(get_db_session)
) -> ModelRepository:
    """Dependency: ModelRepository"""
    return ModelRepository(session, models_path="models")


# ============================================================================
# DOMAIN SERVICES
# ============================================================================

@lru_cache()
def get_event_bus() -> DomainEventBus:
    """
    Dependency: DomainEventBus (singleton).
    
    Singleton porque queremos uma única instância do event bus.
    """
    return DomainEventBus()


# ============================================================================
# ML INFRASTRUCTURE
# ============================================================================

@lru_cache()
def get_feature_store() -> FeatureStore:
    """Dependency: FeatureStore (singleton)"""
    return FeatureStore()


async def get_model_registry(
    model_repository: ModelRepository = Depends(get_model_repository),
    event_bus: DomainEventBus = Depends(get_event_bus)
) -> ModelRegistry:
    """Dependency: ModelRegistry"""
    return ModelRegistry(model_repository, event_bus)


async def get_model_server(
    model_registry: ModelRegistry = Depends(get_model_registry)
) -> ModelServer:
    """Dependency: ModelServer"""
    return ModelServer(
        model_registry=model_registry,
        cache_ttl=3600,  # 1 hora
        enable_batching=False
    )


async def get_model_trainer(
    event_bus: DomainEventBus = Depends(get_event_bus)
) -> ModelTrainer:
    """Dependency: ModelTrainer"""
    return ModelTrainer(event_bus)


# ============================================================================
# APPLICATION SERVICES
# ============================================================================

async def get_user_service(
    user_repository: UserRepository = Depends(get_user_repository),
    rating_repository: RatingRepository = Depends(get_rating_repository)
) -> UserApplicationService:
    """Dependency: UserApplicationService"""
    return UserApplicationService(user_repository, rating_repository)


async def get_movie_service(
    movie_repository: MovieRepository = Depends(get_movie_repository)
) -> MovieApplicationService:
    """Dependency: MovieApplicationService"""
    return MovieApplicationService(movie_repository)


async def get_rating_service(
    rating_repository: RatingRepository = Depends(get_rating_repository),
    user_repository: UserRepository = Depends(get_user_repository),
    movie_repository: MovieRepository = Depends(get_movie_repository),
    event_bus: DomainEventBus = Depends(get_event_bus)
) -> RatingApplicationService:
    """Dependency: RatingApplicationService"""
    return RatingApplicationService(
        rating_repository,
        user_repository,
        movie_repository,
        event_bus
    )


async def get_recommendation_service(
    user_repository: UserRepository = Depends(get_user_repository),
    movie_repository: MovieRepository = Depends(get_movie_repository),
    rating_repository: RatingRepository = Depends(get_rating_repository),
    recommendation_repository: RecommendationRepository = Depends(get_recommendation_repository),
    model_server: ModelServer = Depends(get_model_server),
    feature_store: FeatureStore = Depends(get_feature_store)
) -> RecommendationApplicationService:
    """Dependency: RecommendationApplicationService"""
    return RecommendationApplicationService(
        user_repository,
        movie_repository,
        rating_repository,
        recommendation_repository,
        model_server,
        feature_store
    )