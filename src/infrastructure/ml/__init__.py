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

# Models
from .models import BaseRecommendationModel, NeuralCF

# Features
from .features import FeatureStore, FeatureDefinition, FeatureVector, FeatureType

# Training
from .training import ModelTrainer, TrainingConfig, TrainingResult, TrainingStrategy

# Registry
from .registry import ModelRegistry, ModelVersion, DeploymentStrategy

# Serving
from .serving import ModelServer

__all__ = [
    # Models
    'BaseRecommendationModel',
    'NeuralCF',
    
    # Features
    'FeatureStore',
    'FeatureDefinition',
    'FeatureVector',
    'FeatureType',
    
    # Training
    'ModelTrainer',
    'TrainingConfig',
    'TrainingResult',
    'TrainingStrategy',
    
    # Registry
    'ModelRegistry',
    'ModelVersion',
    'DeploymentStrategy',
    
    # Serving
    'ModelServer',
]