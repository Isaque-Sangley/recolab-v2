"""
Domain Repositories Package

Repositories são ABSTRAÇÕES (interfaces) que definem como acessar dados.
Seguem o Dependency Inversion Principle: domínio depende de abstrações,
não de implementações concretas.

Benefícios:
- Testabilidade: fácil criar mocks
- Flexibilidade: pode trocar DB sem mudar domínio
- Clean Architecture: domínio isolado de infraestrutura
- Type Safety: contratos bem definidos

Repositories disponíveis:
- IUserRepository: persistência de usuários
- IMovieRepository: persistência de filmes
- IRatingRepository: persistência de avaliações
- IRecommendationRepository: persistência de recomendações
- IModelRepository: persistência de modelos ML

Nota: O "I" no nome indica Interface (convenção C#/Java)
Em Python usamos ABC (Abstract Base Class) para isso.
"""

from .base import BaseRepository
from .user_repository import IUserRepository
from .movie_repository import IMovieRepository
from .rating_repository import IRatingRepository
from .recommendation_repository import IRecommendationRepository
from .model_repository import IModelRepository, ModelMetadata

__all__ = [
    'BaseRepository',
    'IUserRepository',
    'IMovieRepository',
    'IRatingRepository',
    'IRecommendationRepository',
    'IModelRepository',
    'ModelMetadata',
]