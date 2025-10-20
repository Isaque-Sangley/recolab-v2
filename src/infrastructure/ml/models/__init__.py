"""
ML Models Package

Modelos de Machine Learning para recomendação.

Modelos disponíveis:
- NeuralCF: Neural Collaborative Filtering (PyTorch)
- Mais modelos virão (TwoTower, Transformers, etc)

Todos implementam BaseRecommendationModel interface.
"""

from .base import BaseRecommendationModel
from .neural_cf import NeuralCF

__all__ = [
    'BaseRecommendationModel',
    'NeuralCF',
]
