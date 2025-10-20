"""
DTOs Package

Data Transfer Objects para comunicação entre camadas.

Padrão:
- Imutáveis (dataclasses)
- Sem lógica de negócio
- Validação simples
- Serialização fácil (to_dict)

Tipos:
- Entity DTOs: representam entities
- Request DTOs: requests de API
- Response DTOs: respostas enriquecidas
"""

# User DTOs
from .user_dtos import (
    UserDTO,
    UserProfileDTO,
    CreateUserRequest,
    UpdateUserRequest
)

# Movie DTOs
from .movie_dtos import (
    MovieDTO,
    MovieDetailDTO,
    SearchMoviesRequest,
    FilterMoviesRequest
)

# Rating DTOs
from .rating_dtos import (
    RatingDTO,
    CreateRatingRequest,
    UpdateRatingRequest,
    DeleteRatingRequest
)

# Recommendation DTOs
from .recommendation_dtos import (
    RecommendationDTO,
    RecommendationListDTO,
    GetRecommendationsRequest,
    ExplainRecommendationRequest,
    ExplanationDTO
)

__all__ = [
    # User
    'UserDTO',
    'UserProfileDTO',
    'CreateUserRequest',
    'UpdateUserRequest',
    
    # Movie
    'MovieDTO',
    'MovieDetailDTO',
    'SearchMoviesRequest',
    'FilterMoviesRequest',
    
    # Rating
    'RatingDTO',
    'CreateRatingRequest',
    'UpdateRatingRequest',
    'DeleteRatingRequest',
    
    # Recommendation
    'RecommendationDTO',
    'RecommendationListDTO',
    'GetRecommendationsRequest',
    'ExplainRecommendationRequest',
    'ExplanationDTO',
]