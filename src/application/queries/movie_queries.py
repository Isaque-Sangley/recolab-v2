"""
Movie Queries
"""

from typing import List, Optional

from ...domain.repositories import IMovieRepository
from ...domain.value_objects import MovieId
from ..dtos import FilterMoviesRequest, MovieDetailDTO, MovieDTO, SearchMoviesRequest


class GetMovieByIdQuery:
    """Query: Buscar filme por ID"""

    def __init__(self, movie_repository: IMovieRepository):
        self.movie_repository = movie_repository

    async def execute(self, movie_id: int) -> Optional[MovieDTO]:
        """Executa query"""
        movie = await self.movie_repository.find_by_id(MovieId(movie_id))

        if not movie:
            return None

        return self._to_dto(movie)

    def _to_dto(self, movie) -> MovieDTO:
        """Converte Movie entity para DTO"""
        return MovieDTO(
            id=int(movie.id),
            title=movie.title,
            genres=movie.genres,
            year=movie.year,
            rating_count=movie.rating_count,
            avg_rating=movie.avg_rating,
            popularity_score=movie.calculate_popularity_score(),
            is_popular=movie.is_popular(),
            is_well_rated=movie.is_well_rated(),
        )


class GetMovieDetailsQuery:
    """Query: Buscar detalhes completos do filme"""

    def __init__(self, movie_repository: IMovieRepository):
        self.movie_repository = movie_repository

    async def execute(self, movie_id: int) -> Optional[MovieDetailDTO]:
        """
        Executa query.

        Retorna filme + filmes similares.
        """
        movie = await self.movie_repository.find_by_id(MovieId(movie_id))

        if not movie:
            return None

        # Busca filmes similares (mesmo gênero)
        similar_movies = []
        if movie.genres:
            similar = await self.movie_repository.find_by_genres(movie.genres, limit=10)
            # Remove o próprio filme
            similar_movies = [m for m in similar if int(m.id) != movie_id][:5]

        # Converte para DTOs
        movie_dto = self._to_dto(movie)
        similar_dtos = [self._to_dto(m) for m in similar_movies]

        return MovieDetailDTO(
            movie=movie_dto,
            similar_movies=similar_dtos,
            genre_distribution={},  # TODO: calcular distribuição
        )

    def _to_dto(self, movie) -> MovieDTO:
        return MovieDTO(
            id=int(movie.id),
            title=movie.title,
            genres=movie.genres,
            year=movie.year,
            rating_count=movie.rating_count,
            avg_rating=movie.avg_rating,
            popularity_score=movie.calculate_popularity_score(),
            is_popular=movie.is_popular(),
            is_well_rated=movie.is_well_rated(),
        )


class SearchMoviesQuery:
    """Query: Buscar filmes por título"""

    def __init__(self, movie_repository: IMovieRepository):
        self.movie_repository = movie_repository

    async def execute(self, request: SearchMoviesRequest) -> List[MovieDTO]:
        """Executa query"""
        movies = await self.movie_repository.search_by_title(request.query, limit=request.limit)

        return [self._to_dto(m) for m in movies]

    def _to_dto(self, movie) -> MovieDTO:
        return MovieDTO(
            id=int(movie.id),
            title=movie.title,
            genres=movie.genres,
            year=movie.year,
            rating_count=movie.rating_count,
            avg_rating=movie.avg_rating,
            popularity_score=movie.calculate_popularity_score(),
            is_popular=movie.is_popular(),
            is_well_rated=movie.is_well_rated(),
        )


class FilterMoviesQuery:
    """Query: Filtrar filmes"""

    def __init__(self, movie_repository: IMovieRepository):
        self.movie_repository = movie_repository

    async def execute(self, request: FilterMoviesRequest) -> List[MovieDTO]:
        """Executa query com múltiplos filtros"""
        # Por simplicidade, aplica filtros sequencialmente
        # Em produção, faria query SQL otimizada

        movies = []

        if request.genres:
            movies = await self.movie_repository.find_by_genres(request.genres, limit=request.limit)
        elif request.min_rating:
            movies = await self.movie_repository.find_well_rated(
                min_avg_rating=request.min_rating,
                min_rating_count=request.min_rating_count or 10,
                limit=request.limit,
            )
        else:
            movies = await self.movie_repository.find_popular(
                min_rating_count=50, limit=request.limit
            )

        # Aplica filtros de ano (se houver)
        if request.min_year or request.max_year:
            movies = [
                m
                for m in movies
                if (not request.min_year or (m.year and m.year >= request.min_year))
                and (not request.max_year or (m.year and m.year <= request.max_year))
            ]

        return [self._to_dto(m) for m in movies]

    def _to_dto(self, movie) -> MovieDTO:
        return MovieDTO(
            id=int(movie.id),
            title=movie.title,
            genres=movie.genres,
            year=movie.year,
            rating_count=movie.rating_count,
            avg_rating=movie.avg_rating,
            popularity_score=movie.calculate_popularity_score(),
            is_popular=movie.is_popular(),
            is_well_rated=movie.is_well_rated(),
        )


class GetPopularMoviesQuery:
    """Query: Filmes populares"""

    def __init__(self, movie_repository: IMovieRepository):
        self.movie_repository = movie_repository

    async def execute(self, limit: int = 40) -> List[MovieDTO]:
        """Executa query"""
        movies = await self.movie_repository.find_popular(min_rating_count=50, limit=limit)

        return [self._to_dto(m) for m in movies]

    def _to_dto(self, movie) -> MovieDTO:
        return MovieDTO(
            id=int(movie.id),
            title=movie.title,
            genres=movie.genres,
            year=movie.year,
            rating_count=movie.rating_count,
            avg_rating=movie.avg_rating,
            popularity_score=movie.calculate_popularity_score(),
            is_popular=movie.is_popular(),
            is_well_rated=movie.is_well_rated(),
        )


class GetAllGenresQuery:
    """Query: Todos os gêneros"""

    def __init__(self, movie_repository: IMovieRepository):
        self.movie_repository = movie_repository

    async def execute(self) -> List[str]:
        """Executa query"""
        return await self.movie_repository.get_all_genres()
