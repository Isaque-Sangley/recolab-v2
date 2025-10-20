"""
Routers Package

FastAPI routers para diferentes recursos.

Routers disponíveis:
- users: usuários
- movies: filmes
- ratings: avaliações
- recommendations: recomendações (CORE!)
"""

from . import users
from . import movies
from . import ratings
from . import recommendations

__all__ = [
    'users',
    'movies',
    'ratings',
    'recommendations',
]