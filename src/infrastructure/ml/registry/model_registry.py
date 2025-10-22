"""
Model Registry

Sistema de versionamento e deployment de modelos ML.
Implementa Champion/Challenger pattern.

Inspirado em MLflow Model Registry, AWS SageMaker Model Registry.
"""

import asyncio
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from ....domain.events import ModelDeployed, ModelPerformanceDegraded, ModelStatus, ModelType
from ....domain.repositories import IModelRepository, ModelMetadata
from ..models import BaseRecommendationModel


@dataclass
class ModelVersion:
    """
    Versão de um modelo.

    Representa uma instância específica de um modelo treinado.
    """

    model_type: ModelType
    version: str
    status: ModelStatus
    metrics: Dict[str, float]
    training_config: Dict[str, Any]
    created_at: str
    deployed_at: Optional[str] = None

    def get_metric(self, metric_name: str, default: float = 0.0) -> float:
        """Obtém métrica específica"""
        return self.metrics.get(metric_name, default)

    def is_better_than(self, other: "ModelVersion", metric: str = "val_ndcg@10") -> bool:
        """
        Compara com outra versão.

        Args:
            other: outra versão
            metric: métrica para comparar

        Returns:
            True se esta versão é melhor
        """
        my_score = self.get_metric(metric)
        other_score = other.get_metric(metric)

        return my_score > other_score

    def to_dict(self) -> Dict[str, Any]:
        return {
            "model_type": self.model_type.value,
            "version": self.version,
            "status": self.status.value,
            "metrics": self.metrics,
            "training_config": self.training_config,
            "created_at": self.created_at,
            "deployed_at": self.deployed_at,
        }


class DeploymentStrategy:
    """
    Estratégias de deployment.

    Define como um novo modelo é implantado.
    """

    @staticmethod
    def full_rollout() -> Dict[str, Any]:
        """
        Full Rollout: troca completamente o modelo.

        Risco: alto
        Velocidade: rápida
        """
        return {
            "type": "full_rollout",
            "description": "Replace current model completely",
            "risk_level": "high",
            "rollback_available": True,
        }

    @staticmethod
    def canary(percentage: int = 10) -> Dict[str, Any]:
        """
        Canary Deployment: direciona X% do tráfego para novo modelo.

        Risco: baixo
        Velocidade: gradual

        Args:
            percentage: % de tráfego para novo modelo (1-100)
        """
        return {
            "type": "canary",
            "percentage": percentage,
            "description": f"Route {percentage}% traffic to new model",
            "risk_level": "low",
            "rollback_available": True,
        }

    @staticmethod
    def ab_test(split: float = 0.5) -> Dict[str, Any]:
        """
        A/B Test: divide tráfego igualmente entre modelos.

        Usado para: comparação de performance

        Args:
            split: proporção para novo modelo (0-1)
        """
        return {
            "type": "ab_test",
            "split": split,
            "description": f"A/B test with {split*100}% to new model",
            "risk_level": "medium",
            "rollback_available": True,
        }

    @staticmethod
    def blue_green() -> Dict[str, Any]:
        """
        Blue-Green: mantém ambos ambientes, troca instantaneamente.

        Risco: médio
        Velocidade: instantânea
        """
        return {
            "type": "blue_green",
            "description": "Maintain both environments, instant switch",
            "risk_level": "medium",
            "rollback_available": True,
        }


class ModelRegistry:
    """
    Model Registry - Gerenciamento de modelos em produção.

    Responsabilidades:
    - Registrar modelos treinados
    - Versionamento
    - Deployment (champion/challenger)
    - Rollback
    - Comparação de versões
    - Monitoring de performance

    Padrões:
    - Champion: modelo atual em produção
    - Challenger: novo modelo sendo testado
    - Archived: modelos antigos (não em uso)
    """

    def __init__(self, model_repository: IModelRepository, event_bus: Optional[Any] = None):
        """
        Args:
            model_repository: repository para persistência
            event_bus: bus de eventos
        """
        self.model_repository = model_repository
        self.event_bus = event_bus

        # Cache de modelos carregados (em memória)
        self._loaded_models: Dict[str, BaseRecommendationModel] = {}

    async def register_model(
        self,
        model: BaseRecommendationModel,
        model_type: ModelType,
        version: str,
        metrics: Dict[str, float],
        training_config: Dict[str, Any],
    ) -> ModelVersion:
        """
        Registra um novo modelo treinado.

        Args:
            model: modelo treinado
            model_type: tipo do modelo
            version: versão (ex: "1.0.0", "20250118_143020")
            metrics: métricas de avaliação
            training_config: configuração de treinamento

        Returns:
            ModelVersion registrado
        """
        print(f"📝 Registering model {model_type.value} v{version}")

        # Salva modelo
        metadata = await self.model_repository.save_model(
            model_type=model_type,
            version=version,
            model_object=model,
            metrics=metrics,
            training_config=training_config,
        )

        model_version = ModelVersion(
            model_type=metadata.model_type,
            version=metadata.version,
            status=metadata.status,
            metrics=metadata.metrics,
            training_config=metadata.training_config,
            created_at=metadata.created_at,
        )

        print(f"✅ Model registered successfully")
        print(f"   Metrics: {metrics}")

        return model_version

    async def get_champion(self, model_type: ModelType) -> Optional[ModelVersion]:
        """
        Obtém modelo champion (em produção).

        Args:
            model_type: tipo do modelo

        Returns:
            ModelVersion do champion ou None
        """
        metadata = await self.model_repository.get_deployed_version(model_type)

        if not metadata:
            return None

        return ModelVersion(
            model_type=metadata.model_type,
            version=metadata.version,
            status=metadata.status,
            metrics=metadata.metrics,
            training_config=metadata.training_config,
            created_at=metadata.created_at,
            deployed_at=None,  # TODO: pegar do metadata
        )

    async def promote_to_champion(
        self, model_type: ModelType, version: str, strategy: Dict[str, Any] = None
    ) -> ModelVersion:
        """
        Promove versão para champion (produção).

        Champion/Challenger pattern:
        - Champion: modelo atual
        - Challenger: novo modelo sendo promovido

        Args:
            model_type: tipo do modelo
            version: versão a promover
            strategy: estratégia de deployment

        Returns:
            ModelVersion promovido
        """
        if strategy is None:
            strategy = DeploymentStrategy.full_rollout()

        print(f"🚀 Promoting {model_type.value} v{version} to CHAMPION")
        print(f"   Strategy: {strategy['type']}")

        # Obtém versão atual (antigo champion)
        old_champion = await self.get_champion(model_type)

        # Promove nova versão
        metadata = await self.model_repository.set_deployed_version(
            model_type=model_type, version=version
        )

        new_champion = ModelVersion(
            model_type=metadata.model_type,
            version=metadata.version,
            status=metadata.status,
            metrics=metadata.metrics,
            training_config=metadata.training_config,
            created_at=metadata.created_at,
            deployed_at=datetime.now().isoformat(),
        )

        # Publica evento
        if self.event_bus:
            event = ModelDeployed(
                model_type=model_type,
                model_version=version,
                previous_version=old_champion.version if old_champion else None,
                deployment_strategy=strategy["type"],
            )
            self.event_bus.publish(event)

        print(f"✅ Promotion complete!")
        if old_champion:
            print(f"   Previous champion: v{old_champion.version}")
        print(f"   New champion: v{new_champion.version}")

        return new_champion

    async def rollback(self, model_type: ModelType, to_version: str) -> ModelVersion:
        """
        Faz rollback para versão anterior.

        Args:
            model_type: tipo do modelo
            to_version: versão para voltar

        Returns:
            ModelVersion após rollback
        """
        print(f"⏮️  Rolling back {model_type.value} to v{to_version}")

        return await self.promote_to_champion(
            model_type=model_type,
            version=to_version,
            strategy={
                "type": "rollback",
                "description": f"Emergency rollback to v{to_version}",
                "risk_level": "low",
            },
        )

    async def compare_versions(
        self, model_type: ModelType, version_a: str, version_b: str
    ) -> Dict[str, Any]:
        """
        Compara duas versões de modelo.

        Args:
            model_type: tipo do modelo
            version_a: primeira versão
            version_b: segunda versão

        Returns:
            Dict com comparação detalhada
        """
        comparison = await self.model_repository.compare_versions(
            model_type=model_type, version_a=version_a, version_b=version_b
        )

        return comparison

    async def list_versions(
        self, model_type: ModelType, status: Optional[ModelStatus] = None
    ) -> List[ModelVersion]:
        """
        Lista versões de um modelo.

        Args:
            model_type: tipo do modelo
            status: filtrar por status (opcional)

        Returns:
            Lista de ModelVersion
        """
        metadatas = await self.model_repository.list_versions(model_type)

        versions = [
            ModelVersion(
                model_type=m.model_type,
                version=m.version,
                status=m.status,
                metrics=m.metrics,
                training_config=m.training_config,
                created_at=m.created_at,
            )
            for m in metadatas
        ]

        # Filtra por status se fornecido
        if status:
            versions = [v for v in versions if v.status == status]

        return versions

    async def load_model(
        self, model_type: ModelType, version: Optional[str] = None
    ) -> BaseRecommendationModel:
        """
        Carrega modelo para uso.

        Args:
            model_type: tipo do modelo
            version: versão específica (None = champion)

        Returns:
            Modelo carregado
        """
        # Se não especificou versão, carrega champion
        if version is None:
            champion = await self.get_champion(model_type)
            if not champion:
                raise ValueError(f"No champion found for {model_type.value}")
            version = champion.version

        # Verifica cache
        cache_key = f"{model_type.value}:{version}"
        if cache_key in self._loaded_models:
            print(f"📦 Loading model from cache: {cache_key}")
            return self._loaded_models[cache_key]

        # Carrega do repository
        print(f"📂 Loading model from disk: {cache_key}")
        model = await self.model_repository.load_model(model_type, version)

        # Cache
        self._loaded_models[cache_key] = model

        return model

    async def monitor_performance(
        self,
        model_type: ModelType,
        current_metrics: Dict[str, float],
        threshold_degradation: float = 0.1,
    ) -> Optional[Dict[str, Any]]:
        """
        Monitora performance do modelo em produção.

        Detecta degradação e alerta.

        Args:
            model_type: tipo do modelo
            current_metrics: métricas atuais
            threshold_degradation: % de degradação permitida

        Returns:
            Dict com alerta se degradou, None caso contrário
        """
        champion = await self.get_champion(model_type)

        if not champion:
            return None

        # Compara cada métrica
        degradations = {}

        for metric_name, current_value in current_metrics.items():
            baseline_value = champion.get_metric(metric_name)

            if baseline_value == 0:
                continue

            # Calcula degradação percentual
            degradation = (baseline_value - current_value) / baseline_value

            if degradation > threshold_degradation:
                degradations[metric_name] = {
                    "baseline": baseline_value,
                    "current": current_value,
                    "degradation": degradation * 100,
                }

        if degradations:
            # Tem degradação - publica evento
            worst_metric = max(degradations.items(), key=lambda x: x[1]["degradation"])
            metric_name, metric_data = worst_metric

            if self.event_bus:
                event = ModelPerformanceDegraded(
                    model_type=model_type,
                    model_version=champion.version,
                    metric_name=metric_name,
                    current_value=metric_data["current"],
                    threshold_value=metric_data["baseline"],
                    degradation_percentage=metric_data["degradation"],
                )
                self.event_bus.publish(event)

            return {
                "status": "degraded",
                "model_type": model_type.value,
                "version": champion.version,
                "degradations": degradations,
                "action_required": "Consider rollback or retrain",
            }

        return None

    def clear_cache(self) -> None:
        """Limpa cache de modelos carregados"""
        self._loaded_models.clear()
        print("🗑️  Model cache cleared")
