"""
Event Types

Enums e tipos usados nos eventos.
"""

from enum import Enum


class ModelType(str, Enum):
    """Tipos de modelo ML"""
    COLLABORATIVE_FILTERING = "collaborative_filtering"
    CONTENT_BASED = "content_based"
    NEURAL_CF = "neural_cf"
    TWO_TOWER = "two_tower"
    HYBRID = "hybrid"


class ModelStatus(str, Enum):
    """Status do modelo"""
    TRAINING = "training"
    TRAINED = "trained"
    DEPLOYED = "deployed"
    ARCHIVED = "archived"
    FAILED = "failed"