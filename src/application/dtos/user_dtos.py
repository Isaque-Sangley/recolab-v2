"""
User DTOs

Data Transfer Objects para comunicação entre camadas.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional


@dataclass
class UserDTO:
    """
    DTO de usuário.

    Representa dados do usuário para transporte entre camadas.
    Diferente da Entity - sem lógica de negócio.
    """

    id: int
    created_at: str
    n_ratings: int
    avg_rating: float
    last_activity: Optional[str]
    favorite_genres: List[str]

    # Campos computados
    user_type: str  # "cold_start", "new", "casual", etc
    activity_score: float
    is_active: bool

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "created_at": self.created_at,
            "n_ratings": self.n_ratings,
            "avg_rating": self.avg_rating,
            "last_activity": self.last_activity,
            "favorite_genres": self.favorite_genres,
            "user_type": self.user_type,
            "activity_score": self.activity_score,
            "is_active": self.is_active,
        }


@dataclass
class UserProfileDTO:
    """
    DTO de perfil completo do usuário.

    Inclui dados agregados e estatísticas.
    """

    user: UserDTO

    # Estatísticas detalhadas
    rating_distribution: dict  # {1: count, 2: count, ...}
    rating_variance: float
    is_generous_rater: bool
    is_critical_rater: bool

    # Scores
    diversity_score: float
    engagement_level: str  # "low", "medium", "high"

    # Recomendação de estratégia
    recommended_strategy: str
    cf_weight: float
    cb_weight: float

    def to_dict(self) -> dict:
        return {
            "user": self.user.to_dict(),
            "rating_distribution": self.rating_distribution,
            "rating_variance": self.rating_variance,
            "is_generous_rater": self.is_generous_rater,
            "is_critical_rater": self.is_critical_rater,
            "diversity_score": self.diversity_score,
            "engagement_level": self.engagement_level,
            "recommended_strategy": self.recommended_strategy,
            "cf_weight": self.cf_weight,
            "cb_weight": self.cb_weight,
        }


@dataclass
class CreateUserRequest:
    """Request para criar usuário"""

    # Usuários criados automaticamente
    # Futuro: email, name, etc
    pass


@dataclass
class UpdateUserRequest:
    """Request para atualizar usuário"""

    user_id: int
    favorite_genres: Optional[List[str]] = None
