"""
Base Model Interface

Interface para todos os modelos de recomendação.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Tuple

import numpy as np


class BaseRecommendationModel(ABC):
    """
    Interface base para modelos de recomendação.

    Por que interface?
    - Padroniza API de todos os modelos
    - Facilita troca de modelos
    - Polimorfismo (strategy pattern)
    """

    @abstractmethod
    def fit(
        self, user_ids: np.ndarray, item_ids: np.ndarray, ratings: np.ndarray
    ) -> Dict[str, float]:
        """
        Treina o modelo.

        Args:
            user_ids: array de user IDs
            item_ids: array de item IDs
            ratings: array de ratings

        Returns:
            Dict com métricas de treinamento
        """
        pass

    @abstractmethod
    def predict(self, user_id: int, item_id: int) -> float:
        """
        Prediz rating para um par user-item.

        Args:
            user_id: ID do usuário
            item_id: ID do item

        Returns:
            Rating predito (0-5 ou 0-1 dependendo do modelo)
        """
        pass

    @abstractmethod
    def recommend(
        self, user_id: int, n_recommendations: int = 10, exclude_items: List[int] = None
    ) -> List[Tuple[int, float]]:
        """
        Gera top-N recomendações para um usuário.

        Args:
            user_id: ID do usuário
            n_recommendations: número de recomendações
            exclude_items: itens a excluir (já vistos)

        Returns:
            Lista de (item_id, score) ordenada por score DESC
        """
        pass

    @abstractmethod
    def save(self, path: str) -> None:
        """Salva modelo em disco"""
        pass

    @abstractmethod
    def load(self, path: str) -> None:
        """Carrega modelo do disco"""
        pass

    @abstractmethod
    def get_model_info(self) -> Dict[str, Any]:
        """
        Retorna informações sobre o modelo.

        Returns:
            Dict com info (tipo, hiperparâmetros, etc)
        """
        pass
