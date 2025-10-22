"""
Domain Events Package

Eventos de domínio para comunicação assíncrona entre componentes.

Padrão Event-Driven:
- Eventos são imutáveis
- Publicados após operações de domínio
- Processados de forma assíncrona
"""

from .base import DomainEvent
from .event_bus import DomainEventBus

# Model Events
from .model_events import (
    ModelDeployed,
    ModelPerformanceDegraded,
    ModelTrainingCompleted,
    ModelTrainingStarted,
)

# Rating Events
from .rating_events import RatingCreated, RatingDeleted, RatingUpdated

# Recommendation Events
from .recommendation_events import RecommendationClicked, RecommendationsGenerated
from .types import ModelStatus, ModelType

# User Events
from .user_events import UserBecameActive, UserBecamePowerUser, UserCreated, UserProfileUpdated

__all__ = [
    # Base
    "DomainEvent",
    "DomainEventBus",
    # Types
    "ModelType",
    "ModelStatus",
    # User Events
    "UserCreated",
    "UserProfileUpdated",
    "UserBecameActive",
    "UserBecamePowerUser",
    # Rating Events
    "RatingCreated",
    "RatingUpdated",
    "RatingDeleted",
    # Recommendation Events
    "RecommendationsGenerated",
    "RecommendationClicked",
    # Model Events
    "ModelTrainingStarted",
    "ModelTrainingCompleted",
    "ModelDeployed",
    "ModelPerformanceDegraded",
]
