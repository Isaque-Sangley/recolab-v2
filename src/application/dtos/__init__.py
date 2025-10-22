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

# Movie DTOs
from .movie_dtos import FilterMoviesRequest, MovieDetailDTO, MovieDTO, SearchMoviesRequest

# Rating DTOs
from .rating_dtos import CreateRatingRequest, DeleteRatingRequest, RatingDTO, UpdateRatingRequest

# Recommendation DTOs
from .recommendation_dtos import (
    ExplainRecommendationRequest,
    ExplanationDTO,
    GetRecommendationsRequest,
    RecommendationDTO,
    RecommendationListDTO,
)

# User DTOs
from .user_dtos import CreateUserRequest, UpdateUserRequest, UserDTO, UserProfileDTO

__all__ = [
    # User
    "UserDTO",
    "UserProfileDTO",
    "CreateUserRequest",
    "UpdateUserRequest",
    # Movie
    "MovieDTO",
    "MovieDetailDTO",
    "SearchMoviesRequest",
    "FilterMoviesRequest",
    # Rating
    "RatingDTO",
    "CreateRatingRequest",
    "UpdateRatingRequest",
    "DeleteRatingRequest",
    # Recommendation
    "RecommendationDTO",
    "RecommendationListDTO",
    "GetRecommendationsRequest",
    "ExplainRecommendationRequest",
    "ExplanationDTO",
]
