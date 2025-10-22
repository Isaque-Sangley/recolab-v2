"""
ML Infrastructure Package

Infraestrutura completa de Machine Learning.

Componentes:
- models: modelos de ML (NCF, etc)
- features: feature store
- training: orquestração de treinamento
- registry: versionamento e deployment
- serving: serving layer

Arquitetura:
┌─────────────────┐
│  Model Server   │ ← API requests
└────────┬────────┘
         │
    ┌────▼─────┐
    │ Registry │ ← Version management
    └────┬─────┘
         │
    ┌────▼────┐
    │ Models  │ ← NCF, TwoTower, etc
    └─────────┘
"""

# Features
from .features import FeatureDefinition, FeatureStore, FeatureType, FeatureVector

# Models
from .models import BaseRecommendationModel, NeuralCF

# Registry
from .registry import DeploymentStrategy, ModelRegistry, ModelVersion

# Serving
from .serving import ModelServer

# Training
from .training import ModelTrainer, TrainingConfig, TrainingResult, TrainingStrategy

__all__ = [
    # Models
    "BaseRecommendationModel",
    "NeuralCF",
    # Features
    "FeatureStore",
    "FeatureDefinition",
    "FeatureVector",
    "FeatureType",
    # Training
    "ModelTrainer",
    "TrainingConfig",
    "TrainingResult",
    "TrainingStrategy",
    # Registry
    "ModelRegistry",
    "ModelVersion",
    "DeploymentStrategy",
    # Serving
    "ModelServer",
]
