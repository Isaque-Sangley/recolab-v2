"""
Pytest Fixtures

Fixtures compartilhadas entre todos os testes.
"""

import pytest
from datetime import datetime, timedelta
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import NullPool

from src.infrastructure.database.models import Base
from src.domain.entities import User, Movie, Rating
from src.domain.value_objects import UserId, MovieId, RatingScore, Timestamp


# ============================================================================
# DATABASE FIXTURES
# ============================================================================

@pytest.fixture(scope="session")
async def test_engine():
    """Create test database engine (in-memory SQLite)"""
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        echo=False,
        poolclass=NullPool
    )
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    yield engine
    
    await engine.dispose()


@pytest.fixture
async def db_session(test_engine) -> AsyncGenerator[AsyncSession, None]:
    """Create database session for tests"""
    async_session = async_sessionmaker(
        test_engine,
        class_=AsyncSession,
        expire_on_commit=False
    )
    
    async with async_session() as session:
        yield session
        await session.rollback()


# ============================================================================
# ENTITY FIXTURES
# ============================================================================

@pytest.fixture
def sample_user() -> User:
    """Create sample user entity"""
    return User(
        id=UserId(1),
        created_at=Timestamp(datetime(2024, 1, 1)),
        n_ratings=10,
        avg_rating=4.2,
        last_activity=Timestamp.now(),
        favorite_genres=["Action", "Sci-Fi"]
    )


@pytest.fixture
def sample_movie() -> Movie:
    """Create sample movie entity"""
    return Movie(
        id=MovieId(1),
        title="The Matrix",
        genres=["Action", "Sci-Fi"],
        year=1999,
        rating_count=100,
        avg_rating=4.5
    )


@pytest.fixture
def sample_rating(sample_user, sample_movie) -> Rating:
    """Create sample rating entity"""
    return Rating(
        user_id=sample_user.id,
        movie_id=sample_movie.id,
        score=RatingScore(4.5),
        timestamp=Timestamp.now()
    )


@pytest.fixture
def cold_start_user() -> User:
    """User with 0 ratings (cold start)"""
    return User(
        id=UserId(100),
        created_at=Timestamp.now(),
        n_ratings=0,
        avg_rating=0.0,
        favorite_genres=[]
    )


@pytest.fixture
def power_user() -> User:
    """User with 150 ratings (power user)"""
    return User(
        id=UserId(200),
        created_at=Timestamp(datetime(2023, 1, 1)),
        n_ratings=150,
        avg_rating=4.0,
        last_activity=Timestamp.now(),
        favorite_genres=["Drama", "Thriller", "Action"]
    )


@pytest.fixture
def popular_movie() -> Movie:
    """Popular movie (300+ ratings)"""
    return Movie(
        id=MovieId(500),
        title="Inception",
        genres=["Action", "Sci-Fi", "Thriller"],
        year=2010,
        rating_count=350,
        avg_rating=4.7
    )


@pytest.fixture
def niche_movie() -> Movie:
    """Niche movie (few ratings)"""
    return Movie(
        id=MovieId(600),
        title="Indie Film",
        genres=["Drama", "Independent"],
        year=2020,
        rating_count=15,
        avg_rating=4.3
    )