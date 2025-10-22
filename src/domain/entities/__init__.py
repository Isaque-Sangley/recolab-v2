"""
Domain Entities Package

Entities são objetos com identidade única que podem mudar ao longo do tempo.
Diferente de Value Objects, são comparadas por ID, não por valores.

Características:
- Identidade única (ID)
- Mutáveis (estado pode mudar)
- Encapsulam regras de negócio
- Comparação por identidade

Entities neste domínio:
- User: usuário do sistema
- Movie: filme/item do catálogo
- Rating: avaliação user→movie
- Recommendation: sugestão gerada pelo sistema
"""

from .movie import Movie
from .rating import Rating
from .recommendation import Recommendation, RecommendationSource
from .user import User

__all__ = [
    "User",
    "Movie",
    "Rating",
    "Recommendation",
    "RecommendationSource",
]
