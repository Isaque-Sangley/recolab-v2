"""
Mappers

Converte entre Domain Entities e ORM Models.
Camada de tradução entre domínio e persistência.
"""

from typing import List
from datetime import datetime

from ...domain.entities import User, Movie, Rating, Recommendation
from ...domain.value_objects import (
    UserId,
    MovieId,
    RatingScore,
    RecommendationScore,
    Timestamp
)
from ...domain.entities.recommendation import RecommendationSource
from .orm_models import UserORM, MovieORM, RatingORM, RecommendationORM


class UserMapper:
    """Mapper para User entity"""
    
    @staticmethod
    def to_entity(orm_obj: UserORM) -> User:
        """Converte UserORM para User entity"""
        return User(
            id=UserId(orm_obj.id),
            created_at=Timestamp(orm_obj.created_at),
            n_ratings=orm_obj.n_ratings,
            avg_rating=orm_obj.avg_rating,
            last_activity=Timestamp(orm_obj.last_activity) if orm_obj.last_activity else None,
            favorite_genres=orm_obj.favorite_genres or []
        )
    
    @staticmethod
    def to_orm(entity: User) -> UserORM:
        """Converte User entity para UserORM"""
        return UserORM(
            id=int(entity.id),
            created_at=entity.created_at.value,
            n_ratings=entity.n_ratings,
            avg_rating=entity.avg_rating,
            last_activity=entity.last_activity.value if entity.last_activity else None,
            favorite_genres=entity.favorite_genres
        )
    
    @staticmethod
    def update_orm(orm_obj: UserORM, entity: User) -> None:
        """Atualiza UserORM com dados da entity"""
        orm_obj.n_ratings = entity.n_ratings
        orm_obj.avg_rating = entity.avg_rating
        orm_obj.last_activity = entity.last_activity.value if entity.last_activity else None
        orm_obj.favorite_genres = entity.favorite_genres


class MovieMapper:
    """Mapper para Movie entity"""
    
    @staticmethod
    def to_entity(orm_obj: MovieORM) -> Movie:
        """Converte MovieORM para Movie entity"""
        return Movie(
            id=MovieId(orm_obj.id),
            title=orm_obj.title,
            genres=orm_obj.genres or [],
            year=orm_obj.year,
            rating_count=orm_obj.rating_count,
            avg_rating=orm_obj.avg_rating
        )
    
    @staticmethod
    def to_orm(entity: Movie) -> MovieORM:
        """Converte Movie entity para MovieORM"""
        return MovieORM(
            id=int(entity.id),
            title=entity.title,
            genres=entity.genres,
            year=entity.year,
            rating_count=entity.rating_count,
            avg_rating=entity.avg_rating
        )
    
    @staticmethod
    def update_orm(orm_obj: MovieORM, entity: Movie) -> None:
        """Atualiza MovieORM com dados da entity"""
        orm_obj.title = entity.title
        orm_obj.genres = entity.genres
        orm_obj.year = entity.year
        orm_obj.rating_count = entity.rating_count
        orm_obj.avg_rating = entity.avg_rating


class RatingMapper:
    """Mapper para Rating entity"""
    
    @staticmethod
    def to_entity(orm_obj: RatingORM) -> Rating:
        """Converte RatingORM para Rating entity"""
        return Rating(
            user_id=UserId(orm_obj.user_id),
            movie_id=MovieId(orm_obj.movie_id),
            score=RatingScore(orm_obj.score),
            timestamp=Timestamp(orm_obj.timestamp)
        )
    
    @staticmethod
    def to_orm(entity: Rating) -> RatingORM:
        """Converte Rating entity para RatingORM"""
        return RatingORM(
            user_id=int(entity.user_id),
            movie_id=int(entity.movie_id),
            score=float(entity.score),
            timestamp=entity.timestamp.value
        )
    
    @staticmethod
    def update_orm(orm_obj: RatingORM, entity: Rating) -> None:
        """Atualiza RatingORM com dados da entity"""
        orm_obj.score = float(entity.score)
        orm_obj.timestamp = entity.timestamp.value


class RecommendationMapper:
    """Mapper para Recommendation entity"""
    
    @staticmethod
    def to_entity(orm_obj: RecommendationORM) -> Recommendation:
        """Converte RecommendationORM para Recommendation entity"""
        return Recommendation(
            user_id=UserId(orm_obj.user_id),
            movie_id=MovieId(orm_obj.movie_id),
            score=RecommendationScore(orm_obj.score),
            source=RecommendationSource(orm_obj.source),
            timestamp=Timestamp(orm_obj.timestamp),
            rank=orm_obj.rank,
            metadata=orm_obj.recommendation_metadata or {}  # CORRIGIDO!
        )
    
    @staticmethod
    def to_orm(entity: Recommendation) -> RecommendationORM:
        """Converte Recommendation entity para RecommendationORM"""
        return RecommendationORM(
            user_id=int(entity.user_id),
            movie_id=int(entity.movie_id),
            score=float(entity.score),
            source=entity.source.value,
            rank=entity.rank,
            timestamp=entity.timestamp.value,
            recommendation_metadata=entity.metadata  # CORRIGIDO!
        )
    
    @staticmethod
    def to_entity_list(orm_list: List[RecommendationORM]) -> List[Recommendation]:
        """Converte lista de RecommendationORM para lista de Recommendation"""
        return [RecommendationMapper.to_entity(orm_obj) for orm_obj in orm_list]
    
    @staticmethod
    def to_orm_list(entity_list: List[Recommendation]) -> List[RecommendationORM]:
        """Converte lista de Recommendation para lista de RecommendationORM"""
        return [RecommendationMapper.to_orm(entity) for entity in entity_list]