"""
ORM Models

SQLAlchemy ORM models para persistência.
Separado de database/models.py para evitar circular imports.
"""

from datetime import datetime
from typing import List, Optional

from sqlalchemy import JSON, DateTime, Float, ForeignKey, Index, Integer, String
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    """Base class for all ORM models"""

    pass


class UserORM(Base):
    """User ORM model"""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    n_ratings: Mapped[int] = mapped_column(Integer, default=0)
    avg_rating: Mapped[float] = mapped_column(Float, default=0.0)
    last_activity: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    favorite_genres: Mapped[List[str]] = mapped_column(ARRAY(String), default=list)

    # Relationships
    ratings = relationship("RatingORM", back_populates="user", cascade="all, delete-orphan")
    recommendations = relationship(
        "RecommendationORM", back_populates="user", cascade="all, delete-orphan"
    )

    # Indexes
    __table_args__ = (
        Index("idx_user_activity", "last_activity"),
        Index("idx_user_n_ratings", "n_ratings"),
    )


class MovieORM(Base):
    """Movie ORM model"""

    __tablename__ = "movies"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(500))
    genres: Mapped[List[str]] = mapped_column(ARRAY(String), default=list)
    year: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    rating_count: Mapped[int] = mapped_column(Integer, default=0)
    avg_rating: Mapped[float] = mapped_column(Float, default=0.0)

    # Relationships
    ratings = relationship("RatingORM", back_populates="movie", cascade="all, delete-orphan")
    recommendations = relationship("RecommendationORM", back_populates="movie")

    # Indexes
    __table_args__ = (
        Index("idx_movie_title", "title"),
        Index("idx_movie_rating_count", "rating_count"),
        Index("idx_movie_avg_rating", "avg_rating"),
        Index("idx_movie_year", "year"),
    )


class RatingORM(Base):
    """Rating ORM model"""

    __tablename__ = "ratings"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    movie_id: Mapped[int] = mapped_column(ForeignKey("movies.id"), index=True)
    score: Mapped[float] = mapped_column(Float)
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)

    # Relationships
    user = relationship("UserORM", back_populates="ratings")
    movie = relationship("MovieORM", back_populates="ratings")

    # Indexes
    __table_args__ = (
        Index("idx_rating_user_movie", "user_id", "movie_id", unique=True),
        Index("idx_rating_timestamp", "timestamp"),
        Index("idx_rating_score", "score"),
    )


class RecommendationORM(Base):
    """Recommendation ORM model"""

    __tablename__ = "recommendations"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    movie_id: Mapped[int] = mapped_column(ForeignKey("movies.id"), index=True)
    score: Mapped[float]
    source: Mapped[str]
    rank: Mapped[int]
    timestamp: Mapped[datetime]
    recommendation_metadata: Mapped[dict] = mapped_column(JSON, nullable=True)

    # Relationships
    user = relationship("UserORM", back_populates="recommendations")
    movie = relationship("MovieORM", back_populates="recommendations")

    # Indexes
    __table_args__ = (
        Index("idx_recommendation_user", "user_id"),
        Index("idx_recommendation_user_timestamp", "user_id", "timestamp"),
        Index("idx_recommendation_score", "score"),
    )


class ModelMetadataORM(Base):
    """Model Metadata ORM model"""

    __tablename__ = "model_metadata"

    id: Mapped[str] = mapped_column(String(100), primary_key=True)
    model_type: Mapped[str] = mapped_column(String(50), index=True)
    version: Mapped[str] = mapped_column(String(50))
    status: Mapped[str] = mapped_column(String(20))
    metrics: Mapped[dict] = mapped_column(JSON)
    training_config: Mapped[dict] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    deployed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    file_path: Mapped[str] = mapped_column(String(500))

    # Indexes
    __table_args__ = (
        Index("idx_model_type_version", "model_type", "version", unique=True),
        Index("idx_model_status", "status"),
        Index("idx_model_created", "created_at"),
    )
