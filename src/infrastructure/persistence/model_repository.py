"""
Model Repository Implementation (PostgreSQL + File System)

Armazena metadata em PostgreSQL e modelos em disco.
"""

import pickle
from datetime import datetime
from pathlib import Path
from typing import Any, List, Optional

import joblib
from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from ...domain.events import ModelStatus, ModelType
from ...domain.repositories import IModelRepository, ModelMetadata
from ..database.models import ModelMetadataModel


class ModelRepository(IModelRepository):
    """
    Implementação do IModelRepository.

    Estratégia híbrida:
    - Metadata: PostgreSQL (rápido para queries)
    - Modelos: File system (eficiente para objetos grandes)

    Path structure:
    /models/
        /collaborative_filtering/
            v1.0.0.pkl
            v1.0.1.pkl
        /neural_cf/
            v1.0.0.pkl
    """

    def __init__(self, session: AsyncSession, models_path: str = "models"):
        self.session = session
        self.models_path = Path(models_path)
        self.models_path.mkdir(parents=True, exist_ok=True)

    def _get_model_path(self, model_type: ModelType, version: str) -> Path:
        """
        Retorna caminho do arquivo do modelo.

        Args:
            model_type: tipo do modelo
            version: versão

        Returns:
            Path completo do arquivo
        """
        type_dir = self.models_path / model_type.value
        type_dir.mkdir(parents=True, exist_ok=True)

        return type_dir / f"{version}.pkl"

    async def save(self, entity: ModelMetadata) -> ModelMetadata:
        """Salva metadata do modelo"""
        model_id = f"{entity.model_type.value}:{entity.version}"

        # Verifica se já existe
        stmt = select(ModelMetadataModel).where(ModelMetadataModel.id == model_id)
        result = await self.session.execute(stmt)
        existing = result.scalar_one_or_none()

        if existing:
            # Atualiza
            existing.status = entity.status.value
            existing.metrics = entity.metrics
            existing.training_config = entity.training_config
            existing.file_path = str(entity.file_path) if entity.file_path else None

            if entity.status == ModelStatus.DEPLOYED:
                existing.deployed_at = datetime.now()

            await self.session.flush()

            return ModelMetadata(
                model_type=ModelType(existing.model_type),
                version=existing.version,
                status=ModelStatus(existing.status),
                metrics=existing.metrics,
                training_config=existing.training_config,
                file_path=Path(existing.file_path) if existing.file_path else None,
                created_at=existing.created_at.isoformat(),
            )
        else:
            # Cria novo
            model = ModelMetadataModel(
                id=model_id,
                model_type=entity.model_type.value,
                version=entity.version,
                status=entity.status.value,
                file_path=str(entity.file_path) if entity.file_path else None,
                metrics=entity.metrics,
                training_config=entity.training_config,
                deployed_at=datetime.now() if entity.status == ModelStatus.DEPLOYED else None,
            )

            self.session.add(model)
            await self.session.flush()

            return ModelMetadata(
                model_type=ModelType(model.model_type),
                version=model.version,
                status=ModelStatus(model.status),
                metrics=model.metrics,
                training_config=model.training_config,
                file_path=Path(model.file_path) if model.file_path else None,
                created_at=model.created_at.isoformat(),
            )

    async def find_by_id(self, entity_id: str) -> Optional[ModelMetadata]:
        """Busca metadata por ID (model_type:version)"""
        stmt = select(ModelMetadataModel).where(ModelMetadataModel.id == entity_id)
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()

        if not model:
            return None

        return ModelMetadata(
            model_type=ModelType(model.model_type),
            version=model.version,
            status=ModelStatus(model.status),
            metrics=model.metrics,
            training_config=model.training_config,
            file_path=Path(model.file_path) if model.file_path else None,
            created_at=model.created_at.isoformat(),
        )

    async def find_all(self, limit: int = 100, offset: int = 0) -> List[ModelMetadata]:
        """Lista todos os modelos"""
        stmt = (
            select(ModelMetadataModel)
            .order_by(ModelMetadataModel.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        result = await self.session.execute(stmt)
        models = result.scalars().all()

        return [
            ModelMetadata(
                model_type=ModelType(m.model_type),
                version=m.version,
                status=ModelStatus(m.status),
                metrics=m.metrics,
                training_config=m.training_config,
                file_path=Path(m.file_path) if m.file_path else None,
                created_at=m.created_at.isoformat(),
            )
            for m in models
        ]

    async def delete(self, entity_id: str) -> bool:
        """Remove modelo (metadata + arquivo)"""
        stmt = select(ModelMetadataModel).where(ModelMetadataModel.id == entity_id)
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()

        if model:
            # Remove arquivo se existe
            if model.file_path:
                file_path = Path(model.file_path)
                if file_path.exists():
                    file_path.unlink()

            # Remove metadata
            await self.session.delete(model)
            await self.session.flush()
            return True

        return False

    async def exists(self, entity_id: str) -> bool:
        """Verifica se modelo existe"""
        stmt = (
            select(func.count())
            .select_from(ModelMetadataModel)
            .where(ModelMetadataModel.id == entity_id)
        )
        result = await self.session.execute(stmt)
        return result.scalar() > 0

    async def count(self) -> int:
        """Conta total de modelos"""
        stmt = select(func.count()).select_from(ModelMetadataModel)
        result = await self.session.execute(stmt)
        return result.scalar()

    # Métodos específicos do IModelRepository

    async def save_model(
        self,
        model_type: ModelType,
        version: str,
        model_object: Any,
        metrics: dict,
        training_config: dict,
    ) -> ModelMetadata:
        """
        Salva modelo completo (objeto + metadata).

        Args:
            model_type: tipo do modelo
            version: versão (ex: "1.0.0")
            model_object: objeto do modelo treinado
            metrics: métricas de avaliação
            training_config: configuração usada no treino

        Returns:
            ModelMetadata salvo
        """
        # Caminho do arquivo
        file_path = self._get_model_path(model_type, version)

        # Salva objeto usando joblib (mais eficiente que pickle para numpy/sklearn)
        joblib.dump(model_object, file_path, compress=3)

        # Cria metadata
        metadata = ModelMetadata(
            model_type=model_type,
            version=version,
            status=ModelStatus.TRAINED,
            metrics=metrics,
            training_config=training_config,
            file_path=file_path,
            created_at=datetime.now().isoformat(),
        )

        # Salva metadata no banco
        saved_metadata = await self.save(metadata)

        return saved_metadata

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
        file_path = self._get_model_path(model_type, version)

        if not file_path.exists():
            raise FileNotFoundError(f"Model file not found: {file_path}")

        # Carrega objeto
        model_object = joblib.load(file_path)

        return model_object

    async def get_latest_version(self, model_type: ModelType) -> Optional[ModelMetadata]:
        """Obtém última versão de um modelo"""
        stmt = (
            select(ModelMetadataModel)
            .where(ModelMetadataModel.model_type == model_type.value)
            .order_by(ModelMetadataModel.created_at.desc())
            .limit(1)
        )

        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()

        if not model:
            return None

        return ModelMetadata(
            model_type=ModelType(model.model_type),
            version=model.version,
            status=ModelStatus(model.status),
            metrics=model.metrics,
            training_config=model.training_config,
            file_path=Path(model.file_path) if model.file_path else None,
            created_at=model.created_at.isoformat(),
        )

    async def get_deployed_version(self, model_type: ModelType) -> Optional[ModelMetadata]:
        """Obtém versão atualmente em produção"""
        stmt = (
            select(ModelMetadataModel)
            .where(
                and_(
                    ModelMetadataModel.model_type == model_type.value,
                    ModelMetadataModel.status == ModelStatus.DEPLOYED.value,
                )
            )
            .order_by(ModelMetadataModel.deployed_at.desc())
            .limit(1)
        )

        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()

        if not model:
            return None

        return ModelMetadata(
            model_type=ModelType(model.model_type),
            version=model.version,
            status=ModelStatus(model.status),
            metrics=model.metrics,
            training_config=model.training_config,
            file_path=Path(model.file_path) if model.file_path else None,
            created_at=model.created_at.isoformat(),
        )

    async def set_deployed_version(self, model_type: ModelType, version: str) -> ModelMetadata:
        """
        Define versão como deployed (produção).

        Estratégia:
        1. Remove flag deployed de versões antigas
        2. Seta nova versão como deployed
        """
        # Remove deployed de versões antigas
        old_deployed_stmt = select(ModelMetadataModel).where(
            and_(
                ModelMetadataModel.model_type == model_type.value,
                ModelMetadataModel.status == ModelStatus.DEPLOYED.value,
            )
        )
        old_result = await self.session.execute(old_deployed_stmt)
        old_models = old_result.scalars().all()

        for old_model in old_models:
            old_model.status = ModelStatus.TRAINED.value

        # Seta nova versão como deployed
        model_id = f"{model_type.value}:{version}"
        stmt = select(ModelMetadataModel).where(ModelMetadataModel.id == model_id)
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()

        if not model:
            raise ValueError(f"Model not found: {model_id}")

        model.status = ModelStatus.DEPLOYED.value
        model.deployed_at = datetime.now()

        await self.session.flush()

        return ModelMetadata(
            model_type=ModelType(model.model_type),
            version=model.version,
            status=ModelStatus(model.status),
            metrics=model.metrics,
            training_config=model.training_config,
            file_path=Path(model.file_path) if model.file_path else None,
            created_at=model.created_at.isoformat(),
        )

    async def list_versions(self, model_type: ModelType) -> List[ModelMetadata]:
        """Lista todas as versões de um modelo"""
        stmt = (
            select(ModelMetadataModel)
            .where(ModelMetadataModel.model_type == model_type.value)
            .order_by(ModelMetadataModel.created_at.desc())
        )

        result = await self.session.execute(stmt)
        models = result.scalars().all()

        return [
            ModelMetadata(
                model_type=ModelType(m.model_type),
                version=m.version,
                status=ModelStatus(m.status),
                metrics=m.metrics,
                training_config=m.training_config,
                file_path=Path(m.file_path) if m.file_path else None,
                created_at=m.created_at.isoformat(),
            )
            for m in models
        ]

    async def compare_versions(self, model_type: ModelType, version_a: str, version_b: str) -> dict:
        """Compara métricas entre duas versões"""
        # Busca versão A
        model_id_a = f"{model_type.value}:{version_a}"
        stmt_a = select(ModelMetadataModel).where(ModelMetadataModel.id == model_id_a)
        result_a = await self.session.execute(stmt_a)
        model_a = result_a.scalar_one_or_none()

        # Busca versão B
        model_id_b = f"{model_type.value}:{version_b}"
        stmt_b = select(ModelMetadataModel).where(ModelMetadataModel.id == model_id_b)
        result_b = await self.session.execute(stmt_b)
        model_b = result_b.scalar_one_or_none()

        if not model_a or not model_b:
            raise ValueError("One or both models not found")

        # Compara métricas
        metrics_a = model_a.metrics or {}
        metrics_b = model_b.metrics or {}

        all_metrics = set(metrics_a.keys()) | set(metrics_b.keys())

        comparison = {"version_a": version_a, "version_b": version_b, "metrics": {}}

        for metric_name in all_metrics:
            value_a = metrics_a.get(metric_name, 0.0)
            value_b = metrics_b.get(metric_name, 0.0)

            delta = value_b - value_a
            delta_percentage = (delta / value_a * 100) if value_a != 0 else 0.0

            comparison["metrics"][metric_name] = {
                "version_a": value_a,
                "version_b": value_b,
                "delta": round(delta, 4),
                "delta_percentage": round(delta_percentage, 2),
                "winner": (
                    "version_b"
                    if value_b > value_a
                    else "version_a" if value_a > value_b else "tie"
                ),
            }

        return comparison

    async def delete_version(self, model_type: ModelType, version: str) -> bool:
        """Remove versão de um modelo"""
        model_id = f"{model_type.value}:{version}"
        return await self.delete(model_id)

    async def get_model_stats(self) -> dict:
        """Retorna estatísticas de modelos"""
        # Modelos por tipo
        models_by_type = {}
        for model_type in ModelType:
            type_stmt = (
                select(func.count())
                .select_from(ModelMetadataModel)
                .where(ModelMetadataModel.model_type == model_type.value)
            )
            type_result = await self.session.execute(type_stmt)
            models_by_type[model_type.value] = type_result.scalar()

        # Versões por tipo
        versions_by_type = {}
        for model_type in ModelType:
            versions_stmt = (
                select(ModelMetadataModel.version)
                .where(ModelMetadataModel.model_type == model_type.value)
                .order_by(ModelMetadataModel.created_at.desc())
            )
            versions_result = await self.session.execute(versions_stmt)
            versions = [row[0] for row in versions_result]
            versions_by_type[model_type.value] = versions

        # Versões deployed
        deployed_versions = {}
        for model_type in ModelType:
            deployed = await self.get_deployed_version(model_type)
            deployed_versions[model_type.value] = deployed.version if deployed else None

        # Métricas médias por tipo (exemplo com NDCG)
        avg_metrics_by_type = {}
        for model_type in ModelType:
            # Aqui simplificado - na prática você faria agregação JSON
            avg_metrics_by_type[model_type.value] = {}

        return {
            "models_by_type": models_by_type,
            "versions_by_type": versions_by_type,
            "deployed_versions": deployed_versions,
            "avg_metrics_by_type": avg_metrics_by_type,
        }
