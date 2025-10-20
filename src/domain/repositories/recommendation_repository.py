"""
Recommendation Repository Interface

Define contrato para persistência de recomendações.
"""

from abc import abstractmethod
from typing import List, Optional

from .base import BaseRepository
from ..entities import Recommendation, RecommendationSource
from ..value_objects import UserId, MovieId, Timestamp


class IRecommendationRepository(BaseRepository[Recommendation, str]):
    """
    Interface para repository de recomendações.
    
    Responsabilidades:
    - Armazenar recomendações geradas
    - Cache de recomendações
    - Analytics de recomendações
    """
    
    @abstractmethod
    async def find_by_user(self, user_id: UserId, limit: int = 100) -> List[Recommendation]:
        """
        Busca recomendações de um usuário.
        
        Args:
            user_id: ID do usuário
            limit: máximo de resultados
        
        Returns:
            Lista de recomendações ordenadas por timestamp DESC
        """
        pass
    
    @abstractmethod
    async def find_latest_by_user(self, user_id: UserId, n: int = 10) -> List[Recommendation]:
        """
        Busca últimas N recomendações de um usuário.
        
        Args:
            user_id: ID do usuário
            n: número de recomendações
        
        Returns:
            Lista de recomendações mais recentes
        """
        pass
    
    @abstractmethod
    async def find_by_source(self, source: RecommendationSource, limit: int = 100) -> List[Recommendation]:
        """
        Busca recomendações por fonte.
        
        Args:
            source: fonte da recomendação
            limit: máximo de resultados
        
        Returns:
            Lista de recomendações
        """
        pass
    
    @abstractmethod
    async def find_high_confidence(self, threshold: float = 0.7, limit: int = 100) -> List[Recommendation]:
        """
        Busca recomendações de alta confiança.
        
        Args:
            threshold: score mínimo
            limit: máximo de resultados
        
        Returns:
            Lista de recomendações com score >= threshold
        """
        pass
    
    @abstractmethod
    async def save_batch(self, user_id: UserId, recommendations: List[Recommendation]) -> List[Recommendation]:
        """
        Salva lote de recomendações para um usuário.
        
        Estratégia:
        - Remove recomendações antigas do usuário
        - Salva novas recomendações
        
        Args:
            user_id: ID do usuário
            recommendations: lista de recomendações
        
        Returns:
            Lista de recomendações salvas
        """
        pass
    
    @abstractmethod
    async def delete_by_user(self, user_id: UserId) -> int:
        """
        Remove todas as recomendações de um usuário.
        
        Útil para:
        - Invalidar cache quando perfil muda
        - Retreinamento
        
        Args:
            user_id: ID do usuário
        
        Returns:
            Número de recomendações removidas
        """
        pass
    
    @abstractmethod
    async def get_recommendation_stats(self) -> dict:
        """
        Retorna estatísticas de recomendações.
        
        Returns:
            Dict com:
            - total_recommendations
            - recommendations_by_source
            - avg_score_by_source
            - high_confidence_percentage
        """
        pass