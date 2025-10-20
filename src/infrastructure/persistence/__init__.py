"""
Persistence Package

Implementações concretas dos repositories usando PostgreSQL.

Componentes:
- UserRepository: persistência de usuários
- MovieRepository: persistência de filmes
- RatingRepository: persistência de ratings
- RecommendationRepository: persistência de recomendações
- ModelRepository: persistência de modelos ML

Padrão:
- Implementam interfaces do domínio
- Usam SQLAlchemy async
- Usam mappers para conversão
"""

from .user_repository import UserRepository
from .movie_repository import MovieRepository
from .rating_repository import RatingRepository
from .recommendation_repository import RecommendationRepository
from .model_repository import ModelRepository

__all__ = [
    'UserRepository',
    'MovieRepository',
    'RatingRepository',
    'RecommendationRepository',
    'ModelRepository',
]
