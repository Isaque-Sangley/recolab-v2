"""
Model Repository Interface

Define contrato para persistência de modelos de ML.
"""

from abc import abstractmethod
from pathlib import Path
from typing import Any, List, Optional

from ..events import ModelStatus, ModelType
from .base import BaseRepository


class ModelMetadata:
    """
    Metadata de um modelo treinado.

    Não é uma Entity porque não tem lógica de negócio,
    apenas armazena informação.
    """

    def __init__(
        self,
        model_type: ModelType,
        version: str,
        status: ModelStatus,
        metrics: dict,
        training_config: dict,
        file_path: Optional[Path] = None,
        created_at: str = None,
    ):
        self.model_type = model_type
        self.version = version
        self.status = status
        self.metrics = metrics
        self.training_config = training_config
        self.file_path = file_path
        self.created_at = created_at

    def get_metric(self, name: str, default: float = 0.0) -> float:
        return self.metrics.get(name, default)


class IModelRepository(BaseRepository[ModelMetadata, str]):
    """
    Interface para repository de modelos.

    Responsabilidades:
    - Salvar modelos treinados
    - Carregar modelos
    - Versionamento
    - Champion/Challenger pattern
    """

    @abstractmethod
    async def save_model(
        self,
        model_type: ModelType,
        version: str,
        model_object: Any,
        metrics: dict,
        training_config: dict,
    ) -> ModelMetadata:
        """
        Salva modelo treinado.

        Args:
            model_type: tipo do modelo
            version: versão (ex: "1.0.0", "2024-01-15")
            model_object: objeto do modelo (PyTorch, scikit-learn, etc)
            metrics: métricas de avaliação
            training_config: configuração usada no treino

        Returns:
            Metadata do modelo salvo
        """
        pass

    @abstractmethod
    async def load_model(self, model_type: ModelType, version: str) -> Any:
        """
        Carrega modelo treinado.

        Args:
            model_type: tipo do modelo
            version: versão específica

        Returns:
            Objeto do modelo carregado

        Raises:
            FileNotFoundError: se modelo não existe
        """
        pass

    @abstractmethod
    async def get_latest_version(self, model_type: ModelType) -> Optional[ModelMetadata]:
        """
        Obtém última versão de um modelo.

        Args:
            model_type: tipo do modelo

        Returns:
            Metadata da última versão ou None
        """
        pass

    @abstractmethod
    async def get_deployed_version(self, model_type: ModelType) -> Optional[ModelMetadata]:
        """
        Obtém versão atualmente em produção.

        Args:
            model_type: tipo do modelo

        Returns:
            Metadata da versão deployed ou None
        """
        pass

    @abstractmethod
    async def set_deployed_version(self, model_type: ModelType, version: str) -> ModelMetadata:
        """
        Define versão como deployed (produção).

        Args:
            model_type: tipo do modelo
            version: versão a deployar

        Returns:
            Metadata atualizado
        """
        pass

    @abstractmethod
    async def list_versions(self, model_type: ModelType) -> List[ModelMetadata]:
        """
        Lista todas as versões de um modelo.

        Args:
            model_type: tipo do modelo

        Returns:
            Lista de metadata ordenada por created_at DESC
        """
        pass

    @abstractmethod
    async def compare_versions(self, model_type: ModelType, version_a: str, version_b: str) -> dict:
        """
        Compara métricas entre duas versões.

        Args:
            model_type: tipo do modelo
            version_a: primeira versão
            version_b: segunda versão

        Returns:
            Dict com comparação de métricas
        """
        pass

    @abstractmethod
    async def delete_version(self, model_type: ModelType, version: str) -> bool:
        """
        Remove versão de um modelo.

        Args:
            model_type: tipo do modelo
            version: versão a remover

        Returns:
            True se removeu, False se não encontrou
        """
        pass

    @abstractmethod
    async def get_model_stats(self) -> dict:
        """
        Retorna estatísticas de modelos.

        Returns:
            Dict com:
            - models_by_type
            - versions_by_type
            - deployed_versions
            - avg_metrics_by_type
        """
        pass
