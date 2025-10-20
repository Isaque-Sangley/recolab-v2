"""
Rating Repository Implementation (PostgreSQL)
"""

from typing import List, Optional
from sqlalchemy import select, func, and_, or_, delete as sql_delete
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timedelta

from ...domain.repositories import IRatingRepository
from ...domain.entities import Rating
from ...domain.value_objects import UserId, MovieId, Timestamp
from ..database.models import RatingModel
from ..database.mappers import RatingMapper


class RatingRepository(IRatingRepository):
    """Implementação PostgreSQL do IRatingRepository"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
        self.mapper = RatingMapper()
    
    async def save(self, entity: Rating) -> Rating:
        """
        Salva ou atualiza rating.
        
        Rating tem composite key (user_id, movie_id).
        """
        stmt = select(RatingModel).where(
            and_(
                RatingModel.user_id == int(entity.user_id),
                RatingModel.movie_id == int(entity.movie_id)
            )
        )
        result = await self.session.execute(stmt)
        existing = result.scalar_one_or_none()
        
        if existing:
            self.mapper.update_model(existing, entity)
            await self.session.flush()
            return self.mapper.to_domain(existing)
        else:
            model = self.mapper.to_model(entity)
            self.session.add(model)
            await self.session.flush()
            return self.mapper.to_domain(model)
    
    async def find_by_id(self, entity_id: tuple) -> Optional[Rating]:
        """
        Busca rating por ID composto (user_id, movie_id).
        
        Args:
            entity_id: tupla (UserId, MovieId)
        """
        user_id, movie_id = entity_id
        
        stmt = select(RatingModel).where(
            and_(
                RatingModel.user_id == int(user_id),
                RatingModel.movie_id == int(movie_id)
            )
        )
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        
        return self.mapper.to_domain(model) if model else None
    
    async def find_all(self, limit: int = 100, offset: int = 0) -> List[Rating]:
        """Lista todos os ratings (paginado)"""
        stmt = (
            select(RatingModel)
            .order_by(RatingModel.timestamp.desc())
            .limit(limit)
            .offset(offset)
        )
        result = await self.session.execute(stmt)
        models = result.scalars().all()
        
        return [self.mapper.to_domain(m) for m in models]
    
    async def delete(self, entity_id: tuple) -> bool:
        """Remove rating"""
        user_id, movie_id = entity_id
        
        stmt = select(RatingModel).where(
            and_(
                RatingModel.user_id == int(user_id),
                RatingModel.movie_id == int(movie_id)
            )
        )
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        
        if model:
            await self.session.delete(model)
            await self.session.flush()
            return True
        
        return False
    
    async def exists(self, entity_id: tuple) -> bool:
        """Verifica se rating existe"""
        user_id, movie_id = entity_id
        
        stmt = select(func.count()).select_from(RatingModel).where(
            and_(
                RatingModel.user_id == int(user_id),
                RatingModel.movie_id == int(movie_id)
            )
        )
        result = await self.session.execute(stmt)
        return result.scalar() > 0
    
    async def count(self) -> int:
        """Conta total de ratings"""
        stmt = select(func.count()).select_from(RatingModel)
        result = await self.session.execute(stmt)
        return result.scalar()
    
    # Métodos específicos do IRatingRepository
    
    async def find_by_user(self, user_id: UserId, limit: int = 1000) -> List[Rating]:
        """Busca todos os ratings de um usuário"""
        stmt = (
            select(RatingModel)
            .where(RatingModel.user_id == int(user_id))
            .order_by(RatingModel.timestamp.desc())
            .limit(limit)
        )
        
        result = await self.session.execute(stmt)
        models = result.scalars().all()
        
        return [self.mapper.to_domain(m) for m in models]
    
    async def find_by_movie(self, movie_id: MovieId, limit: int = 1000) -> List[Rating]:
        """Busca todos os ratings de um filme"""
        stmt = (
            select(RatingModel)
            .where(RatingModel.movie_id == int(movie_id))
            .order_by(RatingModel.timestamp.desc())
            .limit(limit)
        )
        
        result = await self.session.execute(stmt)
        models = result.scalars().all()
        
        return [self.mapper.to_domain(m) for m in models]
    
    async def find_by_user_and_movie(
        self,
        user_id: UserId,
        movie_id: MovieId
    ) -> Optional[Rating]:
        """Busca rating específico"""
        stmt = select(RatingModel).where(
            and_(
                RatingModel.user_id == int(user_id),
                RatingModel.movie_id == int(movie_id)
            )
        )
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        
        return self.mapper.to_domain(model) if model else None
    
    async def find_positive_ratings_by_user(
        self,
        user_id: UserId,
        min_score: float = 4.0
    ) -> List[Rating]:
        """Busca ratings positivos de um usuário"""
        stmt = (
            select(RatingModel)
            .where(
                and_(
                    RatingModel.user_id == int(user_id),
                    RatingModel.score >= min_score
                )
            )
            .order_by(RatingModel.score.desc())
        )
        
        result = await self.session.execute(stmt)
        models = result.scalars().all()
        
        return [self.mapper.to_domain(m) for m in models]
    
    async def find_recent_ratings(self, days: int = 7, limit: int = 1000) -> List[Rating]:
        """Busca ratings recentes"""
        cutoff_date = datetime.now() - timedelta(days=days)
        
        stmt = (
            select(RatingModel)
            .where(RatingModel.timestamp >= cutoff_date)
            .order_by(RatingModel.timestamp.desc())
            .limit(limit)
        )
        
        result = await self.session.execute(stmt)
        models = result.scalars().all()
        
        return [self.mapper.to_domain(m) for m in models]
    
    async def get_user_movie_matrix(self) -> dict:
        """
        Retorna matriz user-movie para Collaborative Filtering.
        
        Formato otimizado para pandas/numpy.
        """
        stmt = select(
            RatingModel.user_id,
            RatingModel.movie_id,
            RatingModel.score,
            RatingModel.timestamp
        ).order_by(RatingModel.timestamp)
        
        result = await self.session.execute(stmt)
        rows = result.all()
        
        user_ids = []
        movie_ids = []
        ratings = []
        timestamps = []
        
        for row in rows:
            user_ids.append(row.user_id)
            movie_ids.append(row.movie_id)
            ratings.append(row.score)
            timestamps.append(row.timestamp.isoformat())
        
        return {
            "user_ids": user_ids,
            "movie_ids": movie_ids,
            "ratings": ratings,
            "timestamps": timestamps
        }
    
    async def get_rating_stats(self) -> dict:
        """Retorna estatísticas de ratings"""
        # Total de ratings
        total_stmt = select(func.count()).select_from(RatingModel)
        total_result = await self.session.execute(total_stmt)
        total_ratings = total_result.scalar()
        
        # Média geral
        avg_stmt = select(func.avg(RatingModel.score))
        avg_result = await self.session.execute(avg_stmt)
        avg_rating = avg_result.scalar() or 0.0
        
        # Distribuição (1-5 estrelas)
        distribution = {}
        for star in range(1, 6):
            dist_stmt = select(func.count()).select_from(RatingModel).where(
                RatingModel.score.between(star - 0.5, star + 0.49)
            )
            dist_result = await self.session.execute(dist_stmt)
            distribution[star] = dist_result.scalar()
        
        # Filmes mais avaliados
        from sqlalchemy import desc
        
        most_rated_stmt = (
            select(
                RatingModel.movie_id,
                func.count(RatingModel.movie_id).label('count')
            )
            .group_by(RatingModel.movie_id)
            .order_by(desc('count'))
            .limit(10)
        )
        most_rated_result = await self.session.execute(most_rated_stmt)
        most_rated_movies = [
            {"movie_id": row.movie_id, "count": row.count}
            for row in most_rated_result
        ]
        
        # Usuários mais ativos
        most_active_stmt = (
            select(
                RatingModel.user_id,
                func.count(RatingModel.user_id).label('count')
            )
            .group_by(RatingModel.user_id)
            .order_by(desc('count'))
            .limit(10)
        )
        most_active_result = await self.session.execute(most_active_stmt)
        most_active_users = [
            {"user_id": row.user_id, "count": row.count}
            for row in most_active_result
        ]
        
        # Calcula sparsity
        users_stmt = select(func.count(func.distinct(RatingModel.user_id)))
        users_result = await self.session.execute(users_stmt)
        n_users = users_result.scalar()
        
        movies_stmt = select(func.count(func.distinct(RatingModel.movie_id)))
        movies_result = await self.session.execute(movies_stmt)
        n_movies = movies_result.scalar()
        
        possible_ratings = n_users * n_movies
        sparsity = 1 - (total_ratings / possible_ratings) if possible_ratings > 0 else 0
        
        return {
            "total_ratings": total_ratings,
            "avg_rating": round(float(avg_rating), 2),
            "rating_distribution": distribution,
            "sparsity": round(sparsity, 4),
            "most_rated_movies": most_rated_movies,
            "most_active_users": most_active_users
        }
    
    async def bulk_save(self, ratings: List[Rating]) -> List[Rating]:
        """Salva múltiplos ratings de uma vez"""
        saved_ratings = []
        
        for rating in ratings:
            saved = await self.save(rating)
            saved_ratings.append(saved)
        
        await self.session.flush()
        
        return saved_ratings
    
    async def delete_by_user(self, user_id: UserId) -> int:
        """Remove todos os ratings de um usuário"""
        stmt = sql_delete(RatingModel).where(RatingModel.user_id == int(user_id))
        result = await self.session.execute(stmt)
        await self.session.flush()
        
        return result.rowcount
    
    async def delete_by_movie(self, movie_id: MovieId) -> int:
        """Remove todos os ratings de um filme"""
        stmt = sql_delete(RatingModel).where(RatingModel.movie_id == int(movie_id))
        result = await self.session.execute(stmt)
        await self.session.flush()
        
        return result.rowcount