"""
Base Repository Interface

Define contrato base para todos os repositories.
"""

from abc import ABC, abstractmethod
from typing import Generic, TypeVar, Optional, List

# Generic types para tornar repositories type-safe
T = TypeVar('T')  # Entity type
ID = TypeVar('ID')  # ID type


class BaseRepository(ABC, Generic[T, ID]):
    """
    Interface base para repositories.
    
    Por que Repository Pattern?
    - Abstrai persistência (pode trocar DB sem mudar domínio)
    - Facilita testes (mock repositories)
    - Centraliza queries
    - Segue Dependency Inversion Principle
    
    Generic types:
    - T: tipo da entidade (User, Movie, etc)
    - ID: tipo do identificador (UserId, MovieId, etc)
    """
    
    @abstractmethod
    async def save(self, entity: T) -> T:
        """
        Salva ou atualiza entidade.
        
        Se entidade já existe (por ID), atualiza.
        Se não existe, cria nova.
        
        Returns:
            Entidade salva (pode ter campos atualizados como timestamps)
        """
        pass
    
    @abstractmethod
    async def find_by_id(self, entity_id: ID) -> Optional[T]:
        """
        Busca entidade por ID.
        
        Returns:
            Entidade encontrada ou None
        """
        pass
    
    @abstractmethod
    async def find_all(self, limit: int = 100, offset: int = 0) -> List[T]:
        """
        Lista todas as entidades (com paginação).
        
        Args:
            limit: número máximo de resultados
            offset: quantos pular (para paginação)
        
        Returns:
            Lista de entidades
        """
        pass
    
    @abstractmethod
    async def delete(self, entity_id: ID) -> bool:
        """
        Remove entidade por ID.
        
        Returns:
            True se removeu, False se não encontrou
        """
        pass
    
    @abstractmethod
    async def exists(self, entity_id: ID) -> bool:
        """
        Verifica se entidade existe.
        
        Returns:
            True se existe, False caso contrário
        """
        pass
    
    @abstractmethod
    async def count(self) -> int:
        """
        Conta total de entidades.
        
        Returns:
            Número total de entidades
        """
        pass