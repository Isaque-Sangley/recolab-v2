"""
Application Layer Package

Camada de aplicação - orquestra use cases.

Componentes:
- DTOs: Data Transfer Objects
- Commands: operações de write (CQRS)
- Queries: operações de read (CQRS)
- Services: orquestração de use cases

Padrão CQRS (Command Query Responsibility Segregation):
- Commands: modificam estado (write)
- Queries: leem estado (read)
- Services: orquestram ambos

Arquitetura:
┌─────────────────────────────┐
│   Presentation Layer        │ (FastAPI)
└────────────┬────────────────┘
             │
┌────────────▼────────────────┐
│   Application Services      │ ← Você está aqui
│   - UserService             │
│   - MovieService            │
│   - RatingService           │
│   - RecommendationService   │
└────┬─────────────────┬──────┘
     │                 │
┌────▼────┐      ┌─────▼──────┐
│Commands │      │  Queries   │
└────┬────┘      └─────┬──────┘
     │                 │
┌────▼─────────────────▼──────┐
│      Domain Layer            │
└──────────────────────────────┘
"""

# DTOs
from .dtos import (
    # User
    UserDTO,
    UserProfileDTO,
    CreateUserRequest,
    UpdateUserRequest,
    
    # Movie
    MovieDTO,
    MovieDetailDTO,
    SearchMoviesRequest,
    FilterMoviesRequest,
    
    # Rating
    RatingDTO,
    CreateRatingRequest,
    UpdateRatingRequest,
    DeleteRatingRequest,
    
    # Recommendation
    RecommendationDTO,
    RecommendationListDTO,
    GetRecommendationsRequest,
    ExplainRecommendationRequest,
    ExplanationDTO,
)

# Commands
from .commands import (
    CreateRatingCommand,
    UpdateRatingCommand,
    DeleteRatingCommand,
)

# Queries
from .queries import (
    # User
    GetUserByIdQuery,
    GetUserProfileQuery,
    ListUsersQuery,
    GetUserStatsQuery,
    
    # Movie
    GetMovieByIdQuery,
    GetMovieDetailsQuery,
    SearchMoviesQuery,
    FilterMoviesQuery,
    GetPopularMoviesQuery,
    GetAllGenresQuery,
    
    # Recommendation
    GetRecommendationsQuery,
    ExplainRecommendationQuery,
)

# Services
from .services import (
    UserApplicationService,
    MovieApplicationService,
    RatingApplicationService,
    RecommendationApplicationService,
)

__all__ = [
    # DTOs - User
    'UserDTO',
    'UserProfileDTO',
    'CreateUserRequest',
    'UpdateUserRequest',
    
    # DTOs - Movie
    'MovieDTO',
    'MovieDetailDTO',
    'SearchMoviesRequest',
    'FilterMoviesRequest',
    
    # DTOs - Rating
    'RatingDTO',
    'CreateRatingRequest',
    'UpdateRatingRequest',
    'DeleteRatingRequest',
    
    # DTOs - Recommendation
    'RecommendationDTO',
    'RecommendationListDTO',
    'GetRecommendationsRequest',
    'ExplainRecommendationRequest',
    'ExplanationDTO',
    
    # Commands
    'CreateRatingCommand',
    'UpdateRatingCommand',
    'DeleteRatingCommand',
    
    # Queries - User
    'GetUserByIdQuery',
    'GetUserProfileQuery',
    'ListUsersQuery',
    'GetUserStatsQuery',
    
    # Queries - Movie
    'GetMovieByIdQuery',
    'GetMovieDetailsQuery',
    'SearchMoviesQuery',
    'FilterMoviesQuery',
    'GetPopularMoviesQuery',
    'GetAllGenresQuery',
    
    # Queries - Recommendation
    'GetRecommendationsQuery',
    'ExplainRecommendationQuery',
    
    # Services
    'UserApplicationService',
    'MovieApplicationService',
    'RatingApplicationService',
    'RecommendationApplicationService',
]
