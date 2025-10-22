"""
Recommendation Domain Events
"""

from dataclasses import dataclass

from .base import DomainEvent


@dataclass(frozen=True)
class RecommendationsGenerated(DomainEvent):
    """Evento: Recomendações geradas"""

    user_id: int = 0
    n_recommendations: int = 0
    strategy: str = ""
    generation_time_ms: float = 0.0
    event_type: str = "recommendations.generated"


@dataclass(frozen=True)
class RecommendationClicked(DomainEvent):
    """Evento: Recomendação clicada"""

    user_id: int = 0
    movie_id: int = 0
    rank: int = 0
    event_type: str = "recommendation.clicked"
