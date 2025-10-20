"""
Rating Repository Interface

Define contrato para persistência de avaliações.
"""

from abc import abstractmethod
from typing import List, Optional
from datetime import datetime

from .base import BaseRepository
from ..entities import Rating
from ..value_objects import UserId, MovieId, Timestamp


class IRatingRepository(BaseRepository[Rating, tuple]):
    """
    Interface para repository de ratings.
    
    Nota: Rating tem ID composto (user_id, movie_id)
    Por isso ID type é tuple[UserId, MovieId]
    
    Responsabilidades:
    - CRUD de ratings
    - Queries para collaborative filtering
    - Queries para análise temporal
    """
    
    @abstractmethod
    async def find_by_user(self, user_id: UserId, limit: int = 1000) -> List[Rating]:
        """
        Busca todos os ratings de um usuário.
        
        Args:
            user_id: ID do usuário
            limit: máximo de resultados
        
        Returns:
            Lista de ratings ordenados por timestamp DESC
        """
        pass
    
    @abstractmethod
    async def find_by_movie(self, movie_id: MovieId, limit: int = 1000) -> List[Rating]:
        """
        Busca todos os ratings de um filme.
        
        Args:
            movie_id: ID do filme
            limit: máximo de resultados
        
        Returns:
            Lista de ratings
        """
        pass
    
    @abstractmethod
    async def find_by_user_and_movie(self, user_id: UserId, movie_id: MovieId) -> Optional[Rating]:
        """
        Busca rating específico de user para movie.
        
        Args:
            user_id: ID do usuário
            movie_id: ID do filme
        
        Returns:
            Rating ou None se não existe
        """
        pass
    
    @abstractmethod
    async def find_positive_ratings_by_user(self, user_id: UserId, min_score: float = 4.0) -> List[Rating]:
        """
        Busca ratings positivos de um usuário.
        
        Útil para:
        - Content-based filtering (o que user gostou)
        - Perfil do usuário
        
        Args:
            user_id: ID do usuário
            min_score: score mínimo para considerar positivo
        
        Returns:
            Lista de ratings positivos
        """
        pass
    
    @abstractmethod
    async def find_recent_ratings(self, days: int = 7, limit: int = 1000) -> List[Rating]:
        """
        Busca ratings recentes.
        
        Útil para:
        - Detectar tendências
        - Retreinamento incremental
        
        Args:
            days: últimos N dias
            limit: máximo de resultados
        
        Returns:
            Lista de ratings ordenados por timestamp DESC
        """
        pass
    
    @abstractmethod
    async def get_user_movie_matrix(self) -> dict:
        """
        Retorna matriz user-movie para Collaborative Filtering.
        
        Formato otimizado para treinar modelo.
        
        Returns:
            Dict com:
            - user_ids: List[int]
            - movie_ids: List[int]
            - ratings: List[float]
            - timestamps: List[str]
        """
        pass
    
    @abstractmethod
    async def get_rating_stats(self) -> dict:
        """
        Retorna estatísticas de ratings.
        
        Returns:
            Dict com:
            - total_ratings
            - avg_rating
            - rating_distribution (1-5 stars)
            - sparsity (% de pares user-movie sem rating)
            - most_rated_movies (top 10)
            - most_active_users (top 10)
        """
        pass
    
    @abstractmethod
    async def bulk_save(self, ratings: List[Rating]) -> List[Rating]:
        """
        Salva múltiplos ratings de uma vez.
        
        Args:
            ratings: lista de ratings
        
        Returns:
            Lista de ratings salvos
        """
        pass
    
    @abstractmethod
    async def delete_by_user(self, user_id: UserId) -> int:
        """
        Remove todos os ratings de um usuário.
        
        Args:
            user_id: ID do usuário
        
        Returns:
            Número de ratings removidos
        """
        pass
    
    @abstractmethod
    async def delete_by_movie(self, movie_id: MovieId) -> int:
        """
        Remove todos os ratings de um filme.
        
        Args:
            movie_id: ID do filme
        
        Returns:
            Número de ratings removidos
        """
        pass