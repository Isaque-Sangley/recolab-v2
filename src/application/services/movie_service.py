"""
Movie Application Service
"""

from typing import List, Optional

from ...domain.repositories import IMovieRepository
from ..dtos import FilterMoviesRequest, MovieDetailDTO, MovieDTO, SearchMoviesRequest
from ..queries import (
    FilterMoviesQuery,
    GetAllGenresQuery,
    GetMovieByIdQuery,
    GetMovieDetailsQuery,
    GetPopularMoviesQuery,
    SearchMoviesQuery,
)


class MovieApplicationService:
    """
    Movie Application Service.

    Orquestra use cases relacionados a filmes.
    """

    def __init__(self, movie_repository: IMovieRepository):
        self.movie_repository = movie_repository

        # Queries
        self.get_movie_query = GetMovieByIdQuery(movie_repository)
        self.get_details_query = GetMovieDetailsQuery(movie_repository)
        self.search_query = SearchMoviesQuery(movie_repository)
        self.filter_query = FilterMoviesQuery(movie_repository)
        self.get_popular_query = GetPopularMoviesQuery(movie_repository)
        self.get_genres_query = GetAllGenresQuery(movie_repository)

    async def get_movie(self, movie_id: int) -> Optional[MovieDTO]:
        """
        Obtém filme por ID.

        Args:
            movie_id: ID do filme

        Returns:
            MovieDTO ou None
        """
        return await self.get_movie_query.execute(movie_id)

    async def get_movie_details(self, movie_id: int) -> Optional[MovieDetailDTO]:
        """
        Obtém detalhes completos do filme.

        Inclui filmes similares.

        Args:
            movie_id: ID do filme

        Returns:
            MovieDetailDTO ou None
        """
        return await self.get_details_query.execute(movie_id)

    async def search_movies(self, query: str, limit: int = 50) -> List[MovieDTO]:
        """
        Busca filmes por título.

        Args:
            query: termo de busca
            limit: limite de resultados

        Returns:
            Lista de MovieDTO
        """
        request = SearchMoviesRequest(query=query, limit=limit)
        return await self.search_query.execute(request)

    async def filter_movies(self, request: FilterMoviesRequest) -> List[MovieDTO]:
        """
        Filtra filmes por múltiplos critérios.

        Args:
            request: request com filtros

        Returns:
            Lista de MovieDTO
        """
        return await self.filter_query.execute(request)

    async def get_popular_movies(self, limit: int = 40) -> List[MovieDTO]:
        """
        Obtém filmes populares.

        Args:
            limit: limite de resultados

        Returns:
            Lista de MovieDTO
        """
        return await self.get_popular_query.execute(limit)

    async def get_all_genres(self) -> List[str]:
        """
        Obtém todos os gêneros disponíveis.

        Returns:
            Lista de gêneros
        """
        return await self.get_genres_query.execute()

    async def get_movies_by_genre(self, genre: str, limit: int = 40) -> List[MovieDTO]:
        """
        Obtém filmes de um gênero específico.

        Args:
            genre: gênero
            limit: limite de resultados

        Returns:
            Lista de MovieDTO
        """
        from ...domain.value_objects import MovieId

        movies = await self.movie_repository.find_by_genre(genre, limit)

        return [
            MovieDTO(
                id=int(m.id),
                title=m.title,
                genres=m.genres,
                year=m.year,
                rating_count=m.rating_count,
                avg_rating=m.avg_rating,
                popularity_score=m.calculate_popularity_score(),
                is_popular=m.is_popular(),
                is_well_rated=m.is_well_rated(),
            )
            for m in movies
        ]

    async def movie_exists(self, movie_id: int) -> bool:
        """
        Verifica se filme existe.

        Args:
            movie_id: ID do filme

        Returns:
            True se existe
        """
        from ...domain.value_objects import MovieId

        return await self.movie_repository.exists(MovieId(movie_id))
