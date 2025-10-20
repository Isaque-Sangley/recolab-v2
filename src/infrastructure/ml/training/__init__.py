"""
Training Package

Componentes para treinamento de modelos.

Componentes:
- ModelTrainer: orquestração de treinamento
- TrainingConfig: configuração
- TrainingResult: resultado do treinamento
"""

from .model_trainer import (
    ModelTrainer,
    TrainingConfig,
    TrainingResult,
    TrainingStrategy
)

__all__ = [
    'ModelTrainer',
    'TrainingConfig',
    'TrainingResult',
    'TrainingStrategy',
]