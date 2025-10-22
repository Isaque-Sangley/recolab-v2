"""
User Repository Interface

Define contrato para persistência de usuários.
"""

from abc import abstractmethod
from typing import List, Optional

from ..entities import User
from ..value_objects import UserId
from .base import BaseRepository


class IUserRepository(BaseRepository[User, UserId]):
    """
    Interface para repository de usuários.

    Responsabilidades:
    - CRUD de usuários
    - Queries específicas de usuário
    - Não conhece detalhes de implementação (PostgreSQL, MongoDB, etc)
    """

    @abstractmethod
    async def find_by_type(self, user_type: str, limit: int = 100) -> List[User]:
        """
        Busca usuários por tipo.

        Args:
            user_type: "cold_start", "new", "casual", "active", "power_user"
            limit: máximo de resultados

        Returns:
            Lista de usuários do tipo especificado
        """
        pass

    @abstractmethod
    async def find_active_users(self, days: int = 30, limit: int = 100) -> List[User]:
        """
        Busca usuários ativos (com atividade recente).

        Args:
            days: considera ativo se teve atividade nos últimos N dias
            limit: máximo de resultados

        Returns:
            Lista de usuários ativos
        """
        pass

    @abstractmethod
    async def find_by_favorite_genre(self, genre: str, limit: int = 100) -> List[User]:
        """
        Busca usuários que têm determinado gênero como favorito.

        Args:
            genre: nome do gênero (ex: "Action", "Comedy")
            limit: máximo de resultados

        Returns:
            Lista de usuários
        """
        pass

    @abstractmethod
    async def find_with_min_ratings(self, min_ratings: int, limit: int = 100) -> List[User]:
        """
        Busca usuários com pelo menos N ratings.

        Útil para:
        - Filtrar usuários para treinar modelo CF
        - Análise de usuários engajados

        Args:
            min_ratings: mínimo de ratings
            limit: máximo de resultados

        Returns:
            Lista de usuários
        """
        pass

    @abstractmethod
    async def get_user_stats(self) -> dict:
        """
        Retorna estatísticas gerais de usuários.

        Returns:
            Dict com:
            - total_users
            - users_by_type
            - avg_ratings_per_user
            - active_users_last_30_days
        """
        pass

    @abstractmethod
    async def bulk_save(self, users: List[User]) -> List[User]:
        """
        Salva múltiplos usuários de uma vez (bulk insert/update).

        Otimização para:
        - Importação de dados
        - Atualização em lote após treinamento

        Args:
            users: lista de usuários

        Returns:
            Lista de usuários salvos
        """
        pass
