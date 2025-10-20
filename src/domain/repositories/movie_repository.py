"""
Movie Repository Interface

Define contrato para persistência de filmes.
"""

from abc import abstractmethod
from typing import List, Optional

from .base import BaseRepository
from ..entities import Movie
from ..value_objects import MovieId


class IMovieRepository(BaseRepository[Movie, MovieId]):
    """
    Interface para repository de filmes.
    
    Responsabilidades:
    - CRUD de filmes
    - Queries específicas de filmes
    - Busca por gênero, popularidade, etc
    """
    
    @abstractmethod
    async def find_by_genre(self, genre: str, limit: int = 100) -> List[Movie]:
        """
        Busca filmes por gênero.
        
        Args:
            genre: nome do gênero
            limit: máximo de resultados
        
        Returns:
            Lista de filmes
        """
        pass
    
    @abstractmethod
    async def find_by_genres(self, genres: List[str], limit: int = 100) -> List[Movie]:
        """
        Busca filmes que contêm QUALQUER UM dos gêneros listados.
        
        Args:
            genres: lista de gêneros
            limit: máximo de resultados
        
        Returns:
            Lista de filmes
        """
        pass
    
    @abstractmethod
    async def find_popular(self, min_rating_count: int = 50, limit: int = 100) -> List[Movie]:
        """
        Busca filmes populares (muitas avaliações).
        
        Args:
            min_rating_count: mínimo de avaliações para considerar popular
            limit: máximo de resultados
        
        Returns:
            Lista de filmes ordenados por popularidade (rating_count DESC)
        """
        pass
    
    @abstractmethod
    async def find_well_rated(self, min_avg_rating: float = 4.0, min_rating_count: int = 10, limit: int = 100) -> List[Movie]:
        """
        Busca filmes bem avaliados.
        
        Args:
            min_avg_rating: nota mínima
            min_rating_count: mínimo de avaliações (evita viés de poucos ratings)
            limit: máximo de resultados
        
        Returns:
            Lista de filmes ordenados por avg_rating DESC
        """
        pass
    
    @abstractmethod
    async def search_by_title(self, query: str, limit: int = 50) -> List[Movie]:
        """
        Busca filmes por título (busca parcial).
        
        Args:
            query: texto para buscar no título
            limit: máximo de resultados
        
        Returns:
            Lista de filmes que contêm query no título
        """
        pass
    
    @abstractmethod
    async def find_by_year_range(self, start_year: int, end_year: int, limit: int = 100) -> List[Movie]:
        """
        Busca filmes por faixa de ano.
        
        Args:
            start_year: ano inicial
            end_year: ano final
            limit: máximo de resultados
        
        Returns:
            Lista de filmes
        """
        pass
    
    @abstractmethod
    async def get_all_genres(self) -> List[str]:
        """
        Retorna lista de todos os gêneros únicos no catálogo.
        
        Returns:
            Lista de gêneros (ex: ["Action", "Comedy", "Drama"])
        """
        pass
    
    @abstractmethod
    async def get_movie_stats(self) -> dict:
        """
        Retorna estatísticas gerais do catálogo.
        
        Returns:
            Dict com:
            - total_movies
            - movies_by_genre
            - avg_rating_count
            - most_popular_movies (top 10)
        """
        pass
    
    @abstractmethod
    async def bulk_save(self, movies: List[Movie]) -> List[Movie]:
        """
        Salva múltiplos filmes de uma vez.
        
        Args:
            movies: lista de filmes
        
        Returns:
            Lista de filmes salvos
        """
        pass