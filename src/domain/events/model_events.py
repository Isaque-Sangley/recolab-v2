"""
Model Domain Events
"""

from dataclasses import dataclass, field
from typing import Any, Dict, Optional

from .base import DomainEvent
from .types import ModelStatus, ModelType


@dataclass(frozen=True)
class ModelTrainingStarted(DomainEvent):
    """Evento: Treinamento iniciado"""

    model_type: ModelType = ModelType.NEURAL_CF
    model_version: str = ""
    n_training_samples: int = 0
    training_config: Dict[str, Any] = field(default_factory=dict)
    event_type: str = "model.training_started"


@dataclass(frozen=True)
class ModelTrainingCompleted(DomainEvent):
    """Evento: Treinamento completo"""

    model_type: ModelType = ModelType.NEURAL_CF
    model_version: str = ""
    status: ModelStatus = ModelStatus.TRAINED
    training_duration_seconds: float = 0.0
    metrics: Dict[str, float] = field(default_factory=dict)
    error_message: Optional[str] = None
    event_type: str = "model.training_completed"


@dataclass(frozen=True)
class ModelDeployed(DomainEvent):
    """Evento: Modelo deployed"""

    model_type: ModelType = ModelType.NEURAL_CF
    model_version: str = ""
    previous_version: Optional[str] = None
    deployment_strategy: str = "full_rollout"
    event_type: str = "model.deployed"


@dataclass(frozen=True)
class ModelPerformanceDegraded(DomainEvent):
    """Evento: Performance degradou"""

    model_type: ModelType = ModelType.NEURAL_CF
    model_version: str = ""
    metric_name: str = ""
    current_value: float = 0.0
    threshold_value: float = 0.0
    degradation_percentage: float = 0.0
    event_type: str = "model.performance_degraded"
