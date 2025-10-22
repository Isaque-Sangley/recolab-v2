"""
Model Trainer

Orquestra treinamento de modelos de ML.
Suporta múltiplos algoritmos e estratégias.
"""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd

from ....domain.events import ModelStatus, ModelTrainingCompleted, ModelTrainingStarted, ModelType
from ..models import BaseRecommendationModel, NeuralCF


class TrainingStrategy(str, Enum):
    """Estratégias de treinamento"""

    FULL = "full"  # Treina com todos os dados
    INCREMENTAL = "incremental"  # Atualiza modelo existente
    SAMPLE = "sample"  # Treina com amostra (para testes)


@dataclass
class TrainingConfig:
    """
    Configuração de treinamento.

    Centraliza hiperparâmetros e configurações.
    """

    model_type: ModelType
    strategy: TrainingStrategy = TrainingStrategy.FULL

    # NCF hyperparameters
    ncf_embedding_dim: int = 64
    ncf_hidden_layers: List[int] = None
    ncf_dropout: float = 0.2
    ncf_learning_rate: float = 0.001
    ncf_batch_size: int = 256
    ncf_epochs: int = 20

    # Training options
    validation_split: float = 0.1
    random_seed: int = 42
    sample_size: Optional[int] = None  # Para strategy=SAMPLE

    def __post_init__(self):
        if self.ncf_hidden_layers is None:
            self.ncf_hidden_layers = [128, 64, 32]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "model_type": self.model_type.value,
            "strategy": self.strategy.value,
            "ncf_embedding_dim": self.ncf_embedding_dim,
            "ncf_hidden_layers": self.ncf_hidden_layers,
            "ncf_dropout": self.ncf_dropout,
            "ncf_learning_rate": self.ncf_learning_rate,
            "ncf_batch_size": self.ncf_batch_size,
            "ncf_epochs": self.ncf_epochs,
            "validation_split": self.validation_split,
            "random_seed": self.random_seed,
            "sample_size": self.sample_size,
        }


@dataclass
class TrainingResult:
    """
    Resultado do treinamento.

    Contém modelo treinado e métricas.
    """

    model: BaseRecommendationModel
    metrics: Dict[str, float]
    training_duration: float
    config: TrainingConfig
    status: ModelStatus
    error_message: Optional[str] = None

    def is_success(self) -> bool:
        return self.status == ModelStatus.TRAINED


class ModelTrainer:
    """
    Model Trainer - Orquestra treinamento de modelos.

    Responsabilidades:
    - Preparar dados para treinamento
    - Instanciar e configurar modelos
    - Executar treinamento
    - Calcular métricas de avaliação
    - Gerenciar eventos de treinamento

    Suporta:
    - Neural CF (PyTorch)
    - Outros modelos (extensível)
    """

    def __init__(self, event_bus: Optional[Any] = None):
        """
        Args:
            event_bus: bus de eventos para publicar eventos de domínio
        """
        self.event_bus = event_bus

    def train(
        self, config: TrainingConfig, ratings_data: pd.DataFrame, version: str = None
    ) -> TrainingResult:
        """
        Treina um modelo.

        Args:
            config: configuração de treinamento
            ratings_data: DataFrame com colunas [user_id, item_id, rating]
            version: versão do modelo (auto-gerada se None)

        Returns:
            TrainingResult com modelo treinado
        """
        if version is None:
            version = datetime.now().strftime("%Y%m%d_%H%M%S")

        print(f"🚀 Starting training...")
        print(f"   Model type: {config.model_type.value}")
        print(f"   Version: {version}")
        print(f"   Strategy: {config.strategy.value}")

        # Publica evento de início
        if self.event_bus:
            start_event = ModelTrainingStarted(
                model_type=config.model_type,
                model_version=version,
                n_training_samples=len(ratings_data),
                training_config=config.to_dict(),
            )
            self.event_bus.publish(start_event)

        start_time = datetime.now()

        try:
            # Prepara dados
            train_data, val_data = self._prepare_data(ratings_data, config)

            # Instancia modelo
            model = self._create_model(config)

            # Treina
            training_metrics = model.fit(
                user_ids=train_data["user_id"].values,
                item_ids=train_data["item_id"].values,
                ratings=train_data["rating"].values,
            )

            # Avalia
            eval_metrics = self._evaluate_model(model, val_data)

            # Combina métricas
            all_metrics = {**training_metrics, **eval_metrics}

            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()

            # Resultado
            result = TrainingResult(
                model=model,
                metrics=all_metrics,
                training_duration=duration,
                config=config,
                status=ModelStatus.TRAINED,
            )

            # Publica evento de sucesso
            if self.event_bus:
                complete_event = ModelTrainingCompleted(
                    model_type=config.model_type,
                    model_version=version,
                    status=ModelStatus.TRAINED,
                    training_duration_seconds=duration,
                    metrics=all_metrics,
                )
                self.event_bus.publish(complete_event)

            print(f"✅ Training complete!")
            print(f"   Duration: {duration:.2f}s")
            print(f"   Metrics: {all_metrics}")

            return result

        except Exception as e:
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()

            error_msg = str(e)
            print(f"❌ Training failed: {error_msg}")

            # Publica evento de falha
            if self.event_bus:
                fail_event = ModelTrainingCompleted(
                    model_type=config.model_type,
                    model_version=version,
                    status=ModelStatus.FAILED,
                    training_duration_seconds=duration,
                    metrics={},
                    error_message=error_msg,
                )
                self.event_bus.publish(fail_event)

            # Retorna resultado com erro
            return TrainingResult(
                model=None,
                metrics={},
                training_duration=duration,
                config=config,
                status=ModelStatus.FAILED,
                error_message=error_msg,
            )

    def _prepare_data(
        self, ratings_data: pd.DataFrame, config: TrainingConfig
    ) -> tuple[pd.DataFrame, pd.DataFrame]:
        """
        Prepara dados para treinamento.

        Args:
            ratings_data: dados brutos
            config: configuração

        Returns:
            (train_df, validation_df)
        """
        # Sample se necessário
        if config.strategy == TrainingStrategy.SAMPLE and config.sample_size:
            if len(ratings_data) > config.sample_size:
                ratings_data = ratings_data.sample(
                    n=config.sample_size, random_state=config.random_seed
                )
                print(f"   📊 Sampled {len(ratings_data)} interactions")

        # Shuffle
        ratings_data = ratings_data.sample(frac=1, random_state=config.random_seed)

        # Split train/validation
        split_idx = int(len(ratings_data) * (1 - config.validation_split))

        train_df = ratings_data.iloc[:split_idx]
        val_df = ratings_data.iloc[split_idx:]

        print(f"   📊 Train: {len(train_df)}, Validation: {len(val_df)}")

        return train_df, val_df

    def _create_model(self, config: TrainingConfig) -> BaseRecommendationModel:
        """
        Instancia modelo baseado na configuração.

        Args:
            config: configuração

        Returns:
            Modelo instanciado
        """
        if config.model_type == ModelType.NEURAL_CF:
            return NeuralCF(
                embedding_dim=config.ncf_embedding_dim,
                hidden_layers=config.ncf_hidden_layers,
                dropout=config.ncf_dropout,
                learning_rate=config.ncf_learning_rate,
                batch_size=config.ncf_batch_size,
                epochs=config.ncf_epochs,
            )
        else:
            raise ValueError(f"Unsupported model type: {config.model_type}")

    def _evaluate_model(
        self, model: BaseRecommendationModel, val_data: pd.DataFrame
    ) -> Dict[str, float]:
        """
        Avalia modelo no conjunto de validação.

        Calcula:
        - RMSE (Root Mean Squared Error)
        - MAE (Mean Absolute Error)
        - Precision@10
        - NDCG@10

        Args:
            model: modelo treinado
            val_data: dados de validação

        Returns:
            Dict com métricas
        """
        print(f"   📊 Evaluating model...")

        # Predições
        predictions = []
        actuals = []

        for _, row in val_data.iterrows():
            user_id = int(row["user_id"])
            item_id = int(row["item_id"])
            actual_rating = float(row["rating"])

            try:
                pred_rating = model.predict(user_id, item_id)
                predictions.append(pred_rating)
                actuals.append(actual_rating)
            except Exception:
                continue

        if not predictions:
            return {"error": "No valid predictions"}

        predictions = np.array(predictions)
        actuals = np.array(actuals)

        # RMSE
        rmse = np.sqrt(np.mean((predictions - actuals) ** 2))

        # MAE
        mae = np.mean(np.abs(predictions - actuals))

        # Precision@10 e NDCG@10 (simplificado)
        # Em produção, calcular para cada usuário
        precision_at_10 = self._calculate_precision_at_k(model, val_data, k=10)
        ndcg_at_10 = self._calculate_ndcg_at_k(model, val_data, k=10)

        metrics = {
            "val_rmse": float(rmse),
            "val_mae": float(mae),
            "val_precision@10": float(precision_at_10),
            "val_ndcg@10": float(ndcg_at_10),
        }

        return metrics

    def _calculate_precision_at_k(
        self, model: BaseRecommendationModel, val_data: pd.DataFrame, k: int = 10
    ) -> float:
        """
        Calcula Precision@K médio.

        Precision@K = (# itens relevantes em top-K) / K
        """
        # Agrupa por usuário
        user_groups = val_data.groupby("user_id")

        precisions = []

        for user_id, group in user_groups:
            if len(group) < 5:  # Precisa dados suficientes
                continue

            # Itens relevantes (rating >= 4)
            relevant_items = set(group[group["rating"] >= 4.0]["item_id"].values)

            if not relevant_items:
                continue

            # Gera recomendações
            try:
                seen_items = list(group["item_id"].values)
                recommendations = model.recommend(
                    user_id=int(user_id), n_recommendations=k, exclude_items=seen_items
                )

                recommended_items = [item_id for item_id, _ in recommendations]

                # Conta hits
                hits = len(set(recommended_items) & relevant_items)
                precision = hits / k

                precisions.append(precision)
            except Exception:
                continue

        return np.mean(precisions) if precisions else 0.0

    def _calculate_ndcg_at_k(
        self, model: BaseRecommendationModel, val_data: pd.DataFrame, k: int = 10
    ) -> float:
        """
        Calcula NDCG@K médio.

        NDCG = DCG / IDCG (normalizado)
        """
        user_groups = val_data.groupby("user_id")

        ndcgs = []

        for user_id, group in user_groups:
            if len(group) < 5:
                continue

            # Relevâncias (ratings normalizados)
            relevance_dict = dict(
                zip(group["item_id"].values, group["rating"].values / 5.0)  # Normaliza 0-1
            )

            # Gera recomendações
            try:
                seen_items = list(group["item_id"].values)
                recommendations = model.recommend(
                    user_id=int(user_id), n_recommendations=k, exclude_items=seen_items
                )

                recommended_items = [item_id for item_id, _ in recommendations]

                # DCG
                dcg = 0.0
                for i, item_id in enumerate(recommended_items):
                    relevance = relevance_dict.get(item_id, 0.0)
                    dcg += relevance / np.log2(i + 2)  # i+2 pois posições começam em 1

                # IDCG (ideal DCG)
                ideal_relevances = sorted(relevance_dict.values(), reverse=True)[:k]
                idcg = sum(rel / np.log2(i + 2) for i, rel in enumerate(ideal_relevances))

                # NDCG
                ndcg = dcg / idcg if idcg > 0 else 0.0
                ndcgs.append(ndcg)
            except Exception:
                continue

        return np.mean(ndcgs) if ndcgs else 0.0
