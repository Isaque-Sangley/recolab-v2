"""
Routers Package

FastAPI routers para diferentes recursos.

Routers disponíveis:
- users: usuários
- movies: filmes
- ratings: avaliações
- recommendations: recomendações (CORE!)
"""

from . import movies, ratings, recommendations, users

__all__ = [
    "users",
    "movies",
    "ratings",
    "recommendations",
]
