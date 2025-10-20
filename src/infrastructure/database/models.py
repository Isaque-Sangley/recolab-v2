"""
Database Models (SQLAlchemy ORM)

Modelos do banco de dados usando SQLAlchemy 2.0.
"""

from datetime import datetime
from typing import Optional, List

from sqlalchemy import String, Integer, Float, DateTime, JSON, ForeignKey, Index, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import ARRAY


class Base(DeclarativeBase):
    """Base class for all models"""
    pass


class UserModel(Base):
    """
    User table
    
    Armazena dados de usuários.
    """
    __tablename__ = "users"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    n_ratings: Mapped[int] = mapped_column(Integer, default=0)
    avg_rating: Mapped[float] = mapped_column(Float, default=0.0)
    last_activity: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    favorite_genres: Mapped[List[str]] = mapped_column(ARRAY(String), default=list)
    
    # Relationships
    ratings = relationship("RatingModel", back_populates="user", cascade="all, delete-orphan")
    recommendations = relationship("RecommendationModel", back_populates="user", cascade="all, delete-orphan")
    
    # Indexes
    __table_args__ = (
        Index('idx_user_activity', 'last_activity'),
        Index('idx_user_n_ratings', 'n_ratings'),
    )


class MovieModel(Base):
    """
    Movie table
    
    Armazena dados de filmes.
    """
    __tablename__ = "movies"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(500))
    genres: Mapped[List[str]] = mapped_column(ARRAY(String), default=list)
    year: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    rating_count: Mapped[int] = mapped_column(Integer, default=0)
    avg_rating: Mapped[float] = mapped_column(Float, default=0.0)
    
    # Relationships
    ratings = relationship("RatingModel", back_populates="movie", cascade="all, delete-orphan")
    recommendations = relationship("RecommendationModel", back_populates="movie")
    
    # Indexes
    __table_args__ = (
        Index('idx_movie_title', 'title'),
        Index('idx_movie_rating_count', 'rating_count'),
        Index('idx_movie_avg_rating', 'avg_rating'),
        Index('idx_movie_year', 'year'),
    )


class RatingModel(Base):
    """
    Rating table
    
    Armazena avaliações de usuários sobre filmes.
    """
    __tablename__ = "ratings"
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    movie_id: Mapped[int] = mapped_column(ForeignKey("movies.id"), index=True)
    score: Mapped[float] = mapped_column(Float)
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    
    # Relationships
    user = relationship("UserModel", back_populates="ratings")
    movie = relationship("MovieModel", back_populates="ratings")
    
    # Indexes
    __table_args__ = (
        Index('idx_rating_user_movie', 'user_id', 'movie_id', unique=True),
        Index('idx_rating_timestamp', 'timestamp'),
        Index('idx_rating_score', 'score'),
    )


class RecommendationModel(Base):
    """
    Recommendation table
    
    Armazena recomendações geradas para usuários.
    """
    __tablename__ = "recommendations"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    movie_id: Mapped[int] = mapped_column(ForeignKey("movies.id"), index=True)
    score: Mapped[float]
    source: Mapped[str]  # "collaborative", "content_based", "hybrid", etc
    rank: Mapped[int]
    timestamp: Mapped[datetime]
    recommendation_metadata: Mapped[dict] = mapped_column(JSON, nullable=True)  # CORRIGIDO!
    
    # Relationships
    user = relationship("UserModel", back_populates="recommendations")
    movie = relationship("MovieModel", back_populates="recommendations")
    
    # Indexes
    __table_args__ = (
        Index('idx_recommendation_user', 'user_id'),
        Index('idx_recommendation_user_timestamp', 'user_id', 'timestamp'),
        Index('idx_recommendation_score', 'score'),
    )


class ModelMetadataModel(Base):
    """
    Model Metadata table
    
    Armazena metadata de modelos ML treinados.
    """
    __tablename__ = "model_metadata"
    
    id: Mapped[str] = mapped_column(String(100), primary_key=True)
    model_type: Mapped[str] = mapped_column(String(50), index=True)
    version: Mapped[str] = mapped_column(String(50))
    status: Mapped[str] = mapped_column(String(20))  # "trained", "deployed", "archived"
    metrics: Mapped[dict] = mapped_column(JSON)
    training_config: Mapped[dict] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    deployed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    file_path: Mapped[str] = mapped_column(String(500))
    
    # Indexes
    __table_args__ = (
        Index('idx_model_type_version', 'model_type', 'version', unique=True),
        Index('idx_model_status', 'status'),
        Index('idx_model_created', 'created_at'),
    )