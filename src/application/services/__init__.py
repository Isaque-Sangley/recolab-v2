"""
Application Services Package

Application Services orquestram use cases.

Responsabilidades:
- Coordenar Commands e Queries
- Gerenciar transações
- Orquestrar Domain Services
- Expor API limpa para apresentação

NÃO contém lógica de negócio (isso fica no Domain).

Services disponíveis:
- UserApplicationService
- MovieApplicationService
- RatingApplicationService
- RecommendationApplicationService
"""

from .user_service import UserApplicationService
from .movie_service import MovieApplicationService
from .rating_service import RatingApplicationService
from .recommendation_service import RecommendationApplicationService

__all__ = [
    'UserApplicationService',
    'MovieApplicationService',
    'RatingApplicationService',
    'RecommendationApplicationService',
]