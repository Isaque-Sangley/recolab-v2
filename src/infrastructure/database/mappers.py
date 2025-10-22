"""
Mappers - Convertem entre Domain Entities e ORM Models

Separa completamente domínio de infraestrutura.
Domain não conhece SQLAlchemy.
"""

from datetime import datetime
from typing import List, Optional

from ...domain.entities import Movie, Rating, Recommendation, RecommendationSource, User
from ...domain.value_objects import MovieId, RatingScore, RecommendationScore, Timestamp, UserId
from .models import MovieModel, RatingModel, RecommendationModel, UserModel


class UserMapper:
    """
    Converte entre User (domain) e UserModel (ORM).
    """

    @staticmethod
    def to_domain(model: UserModel) -> User:
        """
        ORM Model → Domain Entity

        Args:
            model: UserModel do banco

        Returns:
            User entity
        """
        return User(
            id=UserId(model.id),
            created_at=Timestamp(model.created_at),
            n_ratings=model.n_ratings,
            avg_rating=model.avg_rating,
            last_activity=Timestamp(model.last_activity) if model.last_activity else None,
            favorite_genres=model.favorite_genres or [],
        )

    @staticmethod
    def to_model(entity: User) -> UserModel:
        """
        Domain Entity → ORM Model

        Args:
            entity: User domain entity

        Returns:
            UserModel para salvar no banco
        """
        return UserModel(
            id=int(entity.id),
            created_at=entity.created_at.value,
            n_ratings=entity.n_ratings,
            avg_rating=entity.avg_rating,
            last_activity=entity.last_activity.value if entity.last_activity else None,
            favorite_genres=entity.favorite_genres,
        )

    @staticmethod
    def update_model(model: UserModel, entity: User) -> None:
        """
        Atualiza UserModel existente com dados da Entity.

        Args:
            model: UserModel existente
            entity: User com dados novos
        """
        model.n_ratings = entity.n_ratings
        model.avg_rating = entity.avg_rating
        model.last_activity = entity.last_activity.value if entity.last_activity else None
        model.favorite_genres = entity.favorite_genres
        model.updated_at = datetime.now()


class MovieMapper:
    """
    Converte entre Movie (domain) e MovieModel (ORM).
    """

    @staticmethod
    def to_domain(model: MovieModel) -> Movie:
        """ORM Model → Domain Entity"""
        return Movie(
            id=MovieId(model.id),
            title=model.title,
            genres=model.genres or [],
            year=model.year,
            rating_count=model.rating_count,
            avg_rating=model.avg_rating,
            content_features=None,  
        )

    @staticmethod
    def to_model(entity: Movie) -> MovieModel:
        """Domain Entity → ORM Model"""
        return MovieModel(
            id=int(entity.id),
            title=entity.title,
            genres=entity.genres,
            year=entity.year,
            rating_count=entity.rating_count,
            avg_rating=entity.avg_rating,
        )

    @staticmethod
    def update_model(model: MovieModel, entity: Movie) -> None:
        """Atualiza MovieModel com dados da Entity"""
        model.title = entity.title
        model.genres = entity.genres
        model.year = entity.year
        model.rating_count = entity.rating_count
        model.avg_rating = entity.avg_rating
        model.updated_at = datetime.now()


class RatingMapper:
    """
    Converte entre Rating (domain) e RatingModel (ORM).
    """

    @staticmethod
    def to_domain(model: RatingModel) -> Rating:
        """ORM Model → Domain Entity"""
        return Rating(
            user_id=UserId(model.user_id),
            movie_id=MovieId(model.movie_id),
            score=RatingScore(model.score),
            timestamp=Timestamp(model.timestamp),
        )

    @staticmethod
    def to_model(entity: Rating) -> RatingModel:
        """Domain Entity → ORM Model"""
        return RatingModel(
            user_id=int(entity.user_id),
            movie_id=int(entity.movie_id),
            score=float(entity.score),
            timestamp=entity.timestamp.value,
        )

    @staticmethod
    def update_model(model: RatingModel, entity: Rating) -> None:
        """Atualiza RatingModel com dados da Entity"""
        model.score = float(entity.score)
        model.timestamp = entity.timestamp.value
        model.updated_at = datetime.now()


class RecommendationMapper:
    """
    Converte entre Recommendation (domain) e RecommendationModel (ORM).
    """

    @staticmethod
    def to_domain(model: RecommendationModel) -> Recommendation:
        """ORM Model → Domain Entity"""
        return Recommendation(
            user_id=UserId(model.user_id),
            movie_id=MovieId(model.movie_id),
            score=RecommendationScore(model.score),
            source=RecommendationSource(model.source),
            timestamp=Timestamp(model.timestamp),
            rank=model.rank,
            metadata=model.recommendation_metadata or {},
        )

    @staticmethod
    def to_model(entity: Recommendation, recommendation_id: int) -> RecommendationModel:
        """Domain Entity → ORM Model"""
        return RecommendationModel(
            id=recommendation_id,
            user_id=int(entity.user_id),
            movie_id=int(entity.movie_id),
            score=float(entity.score),
            source=entity.source.value,
            rank=entity.rank,
            recommendation_metadata=entity.metadata,
            timestamp=entity.timestamp.value,
        )
