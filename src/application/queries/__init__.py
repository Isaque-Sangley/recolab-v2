"""
Queries Package

Queries são operações de READ (não modificam estado).

CQRS Pattern:
- Queries: read operations (este package)
- Commands: write operations

Benefícios:
- Otimização de leitura
- Cache agressivo
- Denormalização quando necessário
"""

# User Queries
from .user_queries import (
    GetUserByIdQuery,
    GetUserProfileQuery,
    ListUsersQuery,
    GetUserStatsQuery
)

# Movie Queries
from .movie_queries import (
    GetMovieByIdQuery,
    GetMovieDetailsQuery,
    SearchMoviesQuery,
    FilterMoviesQuery,
    GetPopularMoviesQuery,
    GetAllGenresQuery
)

# Recommendation Queries
from .recommendation_queries import (
    GetRecommendationsQuery,
    ExplainRecommendationQuery
)

__all__ = [
    # User
    'GetUserByIdQuery',
    'GetUserProfileQuery',
    'ListUsersQuery',
    'GetUserStatsQuery',
    
    # Movie
    'GetMovieByIdQuery',
    'GetMovieDetailsQuery',
    'SearchMoviesQuery',
    'FilterMoviesQuery',
    'GetPopularMoviesQuery',
    'GetAllGenresQuery',
    
    # Recommendation
    'GetRecommendationsQuery',
    'ExplainRecommendationQuery',
]