"""
Movie Repository Implementation (PostgreSQL)
"""

from typing import List, Optional
from sqlalchemy import select, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession

from ...domain.repositories import IMovieRepository
from ...domain.entities import Movie
from ...domain.value_objects import MovieId
from ..database.models import MovieModel
from ..database.mappers import MovieMapper


class MovieRepository(IMovieRepository):
    """Implementação PostgreSQL do IMovieRepository"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
        self.mapper = MovieMapper()
    
    async def save(self, entity: Movie) -> Movie:
        """Salva ou atualiza filme"""
        stmt = select(MovieModel).where(MovieModel.id == int(entity.id))
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
    
    async def find_by_id(self, entity_id: MovieId) -> Optional[Movie]:
        """Busca filme por ID"""
        stmt = select(MovieModel).where(MovieModel.id == int(entity_id))
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        
        return self.mapper.to_domain(model) if model else None
    
    async def find_all(self, limit: int = 100, offset: int = 0) -> List[Movie]:
        """Lista todos os filmes (paginado)"""
        stmt = (
            select(MovieModel)
            .order_by(MovieModel.title)
            .limit(limit)
            .offset(offset)
        )
        result = await self.session.execute(stmt)
        models = result.scalars().all()
        
        return [self.mapper.to_domain(m) for m in models]
    
    async def delete(self, entity_id: MovieId) -> bool:
        """Remove filme"""
        stmt = select(MovieModel).where(MovieModel.id == int(entity_id))
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        
        if model:
            await self.session.delete(model)
            await self.session.flush()
            return True
        
        return False
    
    async def exists(self, entity_id: MovieId) -> bool:
        """Verifica se filme existe"""
        stmt = select(func.count()).select_from(MovieModel).where(
            MovieModel.id == int(entity_id)
        )
        result = await self.session.execute(stmt)
        return result.scalar() > 0
    
    async def count(self) -> int:
        """Conta total de filmes"""
        stmt = select(func.count()).select_from(MovieModel)
        result = await self.session.execute(stmt)
        return result.scalar()
    
    # Métodos específicos do IMovieRepository
    
    async def find_by_genre(self, genre: str, limit: int = 100) -> List[Movie]:
        """
        Busca filmes por gênero.
        
        Usa PostgreSQL array contains.
        """
        stmt = (
            select(MovieModel)
            .where(MovieModel.genres.contains([genre]))
            .order_by(MovieModel.rating_count.desc())
            .limit(limit)
        )
        
        result = await self.session.execute(stmt)
        models = result.scalars().all()
        
        return [self.mapper.to_domain(m) for m in models]
    
    async def find_by_genres(self, genres: List[str], limit: int = 100) -> List[Movie]:
        """
        Busca filmes que contêm QUALQUER UM dos gêneros.
        
        Usa PostgreSQL array overlap operator (&&).
        """
        stmt = (
            select(MovieModel)
            .where(MovieModel.genres.overlap(genres))
            .order_by(MovieModel.rating_count.desc())
            .limit(limit)
        )
        
        result = await self.session.execute(stmt)
        models = result.scalars().all()
        
        return [self.mapper.to_domain(m) for m in models]
    
    async def find_popular(self, min_rating_count: int = 50, limit: int = 100) -> List[Movie]:
        """Busca filmes populares"""
        stmt = (
            select(MovieModel)
            .where(MovieModel.rating_count >= min_rating_count)
            .order_by(MovieModel.rating_count.desc())
            .limit(limit)
        )
        
        result = await self.session.execute(stmt)
        models = result.scalars().all()
        
        return [self.mapper.to_domain(m) for m in models]
    
    async def find_well_rated(
        self,
        min_avg_rating: float = 4.0,
        min_rating_count: int = 10,
        limit: int = 100
    ) -> List[Movie]:
        """Busca filmes bem avaliados"""
        stmt = (
            select(MovieModel)
            .where(
                and_(
                    MovieModel.avg_rating >= min_avg_rating,
                    MovieModel.rating_count >= min_rating_count
                )
            )
            .order_by(MovieModel.avg_rating.desc())
            .limit(limit)
        )
        
        result = await self.session.execute(stmt)
        models = result.scalars().all()
        
        return [self.mapper.to_domain(m) for m in models]
    
    async def search_by_title(self, query: str, limit: int = 50) -> List[Movie]:
        """
        Busca filmes por título (busca parcial).
        
        Usa ILIKE para case-insensitive search.
        """
        search_pattern = f"%{query}%"
        
        stmt = (
            select(MovieModel)
            .where(MovieModel.title.ilike(search_pattern))
            .order_by(MovieModel.rating_count.desc())
            .limit(limit)
        )
        
        result = await self.session.execute(stmt)
        models = result.scalars().all()
        
        return [self.mapper.to_domain(m) for m in models]
    
    async def find_by_year_range(
        self,
        start_year: int,
        end_year: int,
        limit: int = 100
    ) -> List[Movie]:
        """Busca filmes por faixa de ano"""
        stmt = (
            select(MovieModel)
            .where(
                and_(
                    MovieModel.year >= start_year,
                    MovieModel.year <= end_year
                )
            )
            .order_by(MovieModel.year.desc())
            .limit(limit)
        )
        
        result = await self.session.execute(stmt)
        models = result.scalars().all()
        
        return [self.mapper.to_domain(m) for m in models]
    
    async def get_all_genres(self) -> List[str]:
        """
        Retorna lista de todos os gêneros únicos.
        
        Usa PostgreSQL unnest para extrair elementos de arrays.
        """
        from sqlalchemy import text
        
        # Query SQL puro para unnest (mais eficiente)
        query = text("""
            SELECT DISTINCT unnest(genres) as genre
            FROM movies
            WHERE genres IS NOT NULL
            ORDER BY genre
        """)
        
        result = await self.session.execute(query)
        genres = [row[0] for row in result]
        
        return genres
    
    async def get_movie_stats(self) -> dict:
        """Retorna estatísticas gerais do catálogo"""
        # Total de filmes
        total_stmt = select(func.count()).select_from(MovieModel)
        total_result = await self.session.execute(total_stmt)
        total_movies = total_result.scalar()
        
        # Média de avaliações por filme
        avg_stmt = select(func.avg(MovieModel.rating_count))
        avg_result = await self.session.execute(avg_stmt)
        avg_rating_count = avg_result.scalar() or 0.0
        
        # Gêneros únicos
        all_genres = await self.get_all_genres()
        
        # Top 10 mais populares
        popular_stmt = (
            select(MovieModel)
            .order_by(MovieModel.rating_count.desc())
            .limit(10)
        )
        popular_result = await self.session.execute(popular_stmt)
        popular_models = popular_result.scalars().all()
        
        most_popular = [
            {
                "id": m.id,
                "title": m.title,
                "rating_count": m.rating_count,
                "avg_rating": round(m.avg_rating, 2)
            }
            for m in popular_models
        ]
        
        return {
            "total_movies": total_movies,
            "unique_genres": len(all_genres),
            "avg_rating_count": round(float(avg_rating_count), 2),
            "most_popular_movies": most_popular
        }
    
    async def bulk_save(self, movies: List[Movie]) -> List[Movie]:
        """Salva múltiplos filmes de uma vez"""
        saved_movies = []
        
        for movie in movies:
            saved = await self.save(movie)
            saved_movies.append(saved)
        
        await self.session.flush()
        
        return saved_movies