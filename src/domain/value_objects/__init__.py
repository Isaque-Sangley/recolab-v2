"""
Value Objects Package

Value Objects são objetos imutáveis definidos por seus valores.
Dois Value Objects com o mesmo valor são considerados iguais.

Exemplos:
- UserId(1) == UserId(1)  # True
- RatingScore(4.5) == RatingScore(4.5)  # True

Características:
- Imutáveis (frozen=True)
- Validados na criação
- Comparáveis por valor
- Thread-safe
"""

from .movie_id import MovieId
from .rating_score import RatingScore
from .recommendation_score import RecommendationScore
from .timestamp import Timestamp
from .user_id import UserId

__all__ = [
    "UserId",
    "MovieId",
    "RatingScore",
    "RecommendationScore",
    "Timestamp",
]
