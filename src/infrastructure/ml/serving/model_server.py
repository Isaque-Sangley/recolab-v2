"""
Model Serving

Camada de serving para inference em produção.
Gerencia cache, batching, e fallbacks.
"""

import asyncio
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

from ....domain.entities import Recommendation, RecommendationSource
from ....domain.events import ModelType
from ....domain.value_objects import MovieId, RecommendationScore, Timestamp, UserId
from ..models import BaseRecommendationModel
from ..registry.model_registry import ModelRegistry


class ModelServer:
    """
    Model Server - Serving layer para modelos em produção.

    Responsabilidades:
    - Servir predições
    - Cache de resultados
    - Request batching (otimização)
    - Fallback strategies
    - A/B testing support
    - Latency monitoring

    Otimizações:
    - Cache de recomendações
    - Batch inference
    - Async processing
    """

    def __init__(
        self,
        model_registry: ModelRegistry,
        cache_ttl: int = 3600,  # 1 hora
        enable_batching: bool = False,
        batch_size: int = 32,
        batch_timeout: float = 0.1,  # 100ms
    ):
        """
        Args:
            model_registry: registry de modelos
            cache_ttl: tempo de vida do cache (segundos)
            enable_batching: habilita request batching
            batch_size: tamanho do batch
            batch_timeout: timeout para formar batch
        """
        self.model_registry = model_registry
        self.cache_ttl = cache_ttl
        self.enable_batching = enable_batching
        self.batch_size = batch_size
        self.batch_timeout = batch_timeout

        # Cache de recomendações
        self._recommendation_cache: Dict[str, List[Recommendation]] = {}
        self._cache_timestamps: Dict[str, datetime] = {}

        # Modelos carregados
        self._loaded_models: Dict[ModelType, BaseRecommendationModel] = {}

        # Métricas de serving
        self._serving_stats = {
            "total_requests": 0,
            "cache_hits": 0,
            "cache_misses": 0,
            "avg_latency_ms": 0.0,
            "errors": 0,
        }

    async def predict(
        self, model_type: ModelType, user_id: int, item_id: int, version: Optional[str] = None
    ) -> float:
        """
        Prediz rating para user-item pair.

        Args:
            model_type: tipo do modelo
            user_id: ID do usuário
            item_id: ID do item
            version: versão específica (None = champion)

        Returns:
            Rating predito (0-5)
        """
        start_time = datetime.now()

        try:
            # Carrega modelo
            model = await self._get_model(model_type, version)

            # Prediz
            prediction = model.predict(user_id, item_id)

            # Atualiza stats
            self._update_latency(start_time)

            return prediction

        except Exception as e:
            self._serving_stats["errors"] += 1
            print(f"❌ Prediction error: {e}")

            # Fallback: retorna média neutra
            return 3.0

    async def recommend(
        self,
        model_type: ModelType,
        user_id: int,
        n_recommendations: int = 10,
        exclude_items: List[int] = None,
        version: Optional[str] = None,
        use_cache: bool = True,
    ) -> List[Recommendation]:
        """
        Gera recomendações para um usuário.

        Args:
            model_type: tipo do modelo
            user_id: ID do usuário
            n_recommendations: número de recomendações
            exclude_items: itens a excluir
            version: versão específica
            use_cache: usar cache

        Returns:
            Lista de Recommendation entities
        """
        start_time = datetime.now()
        self._serving_stats["total_requests"] += 1

        # Verifica cache
        if use_cache:
            cached = self._get_from_cache(user_id, n_recommendations)
            if cached:
                self._serving_stats["cache_hits"] += 1
                self._update_latency(start_time)
                return cached

        self._serving_stats["cache_misses"] += 1

        try:
            # Carrega modelo
            model = await self._get_model(model_type, version)

            # Gera recomendações
            exclude_items = exclude_items or []
            raw_recommendations = model.recommend(
                user_id=user_id, n_recommendations=n_recommendations, exclude_items=exclude_items
            )

            # Converte para domain entities
            timestamp = Timestamp.now()
            recommendations = []

            for rank, (item_id, score) in enumerate(raw_recommendations, start=1):
                rec = Recommendation(
                    user_id=UserId(user_id),
                    movie_id=MovieId(item_id),
                    score=RecommendationScore(float(score)),
                    source=self._map_model_type_to_source(model_type),
                    timestamp=timestamp,
                    rank=rank,
                    metadata={
                        "model_type": model_type.value,
                        "model_version": version or "champion",
                        "serving_latency_ms": 0,  # Será atualizado depois
                    },
                )
                recommendations.append(rec)

            # Atualiza latency no metadata
            latency_ms = (datetime.now() - start_time).total_seconds() * 1000
            for rec in recommendations:
                rec.metadata["serving_latency_ms"] = round(latency_ms, 2)

            # Cache
            if use_cache:
                self._put_in_cache(user_id, n_recommendations, recommendations)

            # Atualiza stats
            self._update_latency(start_time)

            return recommendations

        except Exception as e:
            self._serving_stats["errors"] += 1
            print(f"❌ Recommendation error: {e}")

            # Fallback: retorna lista vazia (ou popular items)
            return []

    async def recommend_batch(
        self,
        model_type: ModelType,
        user_ids: List[int],
        n_recommendations: int = 10,
        version: Optional[str] = None,
    ) -> Dict[int, List[Recommendation]]:
        """
        Gera recomendações em batch (otimização).

        Args:
            model_type: tipo do modelo
            user_ids: lista de user IDs
            n_recommendations: número de recomendações por user
            version: versão específica

        Returns:
            Dict user_id → List[Recommendation]
        """
        # TODO: Implementar batching real com PyTorch
        # Por ora, processa sequencialmente

        results = {}

        for user_id in user_ids:
            recommendations = await self.recommend(
                model_type=model_type,
                user_id=user_id,
                n_recommendations=n_recommendations,
                version=version,
                use_cache=True,
            )
            results[user_id] = recommendations

        return results

    async def _get_model(
        self, model_type: ModelType, version: Optional[str] = None
    ) -> BaseRecommendationModel:
        """
        Obtém modelo (do cache ou registry).

        Args:
            model_type: tipo do modelo
            version: versão específica

        Returns:
            Modelo carregado
        """
        # Se não especificou versão, usa champion
        if version is None:
            cache_key = model_type
        else:
            cache_key = f"{model_type.value}:{version}"

        # Verifica cache
        if cache_key in self._loaded_models:
            return self._loaded_models[cache_key]

        # Carrega do registry
        model = await self.model_registry.load_model(model_type, version)

        # Cache (apenas champion para economizar memória)
        if version is None:
            self._loaded_models[model_type] = model

        return model

    def _get_from_cache(
        self, user_id: int, n_recommendations: int
    ) -> Optional[List[Recommendation]]:
        """Obtém recomendações do cache"""
        cache_key = f"{user_id}:{n_recommendations}"

        if cache_key not in self._recommendation_cache:
            return None

        # Verifica TTL
        timestamp = self._cache_timestamps.get(cache_key)
        if timestamp:
            age = (datetime.now() - timestamp).total_seconds()
            if age > self.cache_ttl:
                # Expirou
                del self._recommendation_cache[cache_key]
                del self._cache_timestamps[cache_key]
                return None

        return self._recommendation_cache[cache_key]

    def _put_in_cache(
        self, user_id: int, n_recommendations: int, recommendations: List[Recommendation]
    ) -> None:
        """Coloca recomendações no cache"""
        cache_key = f"{user_id}:{n_recommendations}"
        self._recommendation_cache[cache_key] = recommendations
        self._cache_timestamps[cache_key] = datetime.now()

    def invalidate_user_cache(self, user_id: int) -> None:
        """Invalida cache de um usuário específico"""
        keys_to_remove = [
            key for key in self._recommendation_cache.keys() if key.startswith(f"{user_id}:")
        ]

        for key in keys_to_remove:
            del self._recommendation_cache[key]
            if key in self._cache_timestamps:
                del self._cache_timestamps[key]

    def clear_cache(self) -> None:
        """Limpa todo o cache"""
        self._recommendation_cache.clear()
        self._cache_timestamps.clear()

    def _update_latency(self, start_time: datetime) -> None:
        """Atualiza estatísticas de latência"""
        latency_ms = (datetime.now() - start_time).total_seconds() * 1000

        # Média móvel exponencial
        alpha = 0.1
        current_avg = self._serving_stats["avg_latency_ms"]
        self._serving_stats["avg_latency_ms"] = alpha * latency_ms + (1 - alpha) * current_avg

    def _map_model_type_to_source(self, model_type: ModelType) -> RecommendationSource:
        """Mapeia ModelType para RecommendationSource"""
        mapping = {
            ModelType.COLLABORATIVE_FILTERING: RecommendationSource.COLLABORATIVE,
            ModelType.CONTENT_BASED: RecommendationSource.CONTENT_BASED,
            ModelType.NEURAL_CF: RecommendationSource.COLLABORATIVE,
            ModelType.TWO_TOWER: RecommendationSource.COLLABORATIVE,
            ModelType.HYBRID: RecommendationSource.HYBRID,
        }

        return mapping.get(model_type, RecommendationSource.PERSONALIZED)

    def get_serving_stats(self) -> Dict[str, Any]:
        """Retorna estatísticas de serving"""
        total = self._serving_stats["total_requests"]
        cache_hit_rate = self._serving_stats["cache_hits"] / total * 100 if total > 0 else 0.0

        return {
            **self._serving_stats,
            "cache_hit_rate": round(cache_hit_rate, 2),
            "cache_size": len(self._recommendation_cache),
        }
