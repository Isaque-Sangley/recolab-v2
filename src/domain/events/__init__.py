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
from .types import ModelType, ModelStatus

# User Events
from .user_events import (
    UserCreated,
    UserProfileUpdated,
    UserBecameActive,
    UserBecamePowerUser
)

# Rating Events
from .rating_events import (
    RatingCreated,
    RatingUpdated,
    RatingDeleted
)

# Recommendation Events
from .recommendation_events import (
    RecommendationsGenerated,
    RecommendationClicked
)

# Model Events
from .model_events import (
    ModelTrainingStarted,
    ModelTrainingCompleted,
    ModelDeployed,
    ModelPerformanceDegraded
)

__all__ = [
    # Base
    'DomainEvent',
    'DomainEventBus',
    
    # Types
    'ModelType',
    'ModelStatus',
    
    # User Events
    'UserCreated',
    'UserProfileUpdated',
    'UserBecameActive',
    'UserBecamePowerUser',
    
    # Rating Events
    'RatingCreated',
    'RatingUpdated',
    'RatingDeleted',
    
    # Recommendation Events
    'RecommendationsGenerated',
    'RecommendationClicked',
    
    # Model Events
    'ModelTrainingStarted',
    'ModelTrainingCompleted',
    'ModelDeployed',
    'ModelPerformanceDegraded',
]