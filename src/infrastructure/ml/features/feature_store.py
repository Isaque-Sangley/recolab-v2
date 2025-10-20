"""
Feature Store

Gerenciamento centralizado de features para ML.
Inspirado em Feast, Tecton, AWS Feature Store.

Responsabilidades:
- Armazenar features computadas
- Versionamento de features
- Feature serving (low latency)
- Feature engineering pipeline
"""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime
import numpy as np
import pandas as pd
from enum import Enum


class FeatureType(str, Enum):
    """Tipos de features"""
    NUMERICAL = "numerical"
    CATEGORICAL = "categorical"
    EMBEDDING = "embedding"
    TEMPORAL = "temporal"


@dataclass
class FeatureDefinition:
    """
    Definição de uma feature.
    
    Metadata sobre feature para documentação e validação.
    """
    name: str
    feature_type: FeatureType
    description: str
    version: str = "1.0.0"
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    is_active: bool = True
    
    # Metadata adicional
    source: Optional[str] = None  # De onde vem a feature
    dependencies: List[str] = field(default_factory=list)  # Features necessárias
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "feature_type": self.feature_type.value,
            "description": self.description,
            "version": self.version,
            "created_at": self.created_at,
            "is_active": self.is_active,
            "source": self.source,
            "dependencies": self.dependencies
        }


@dataclass
class FeatureVector:
    """
    Vetor de features para uma entidade (user ou item).
    
    Contém features computadas em um momento específico.
    """
    entity_id: int  # user_id ou item_id
    entity_type: str  # "user" ou "item"
    features: Dict[str, Any]
    computed_at: str = field(default_factory=lambda: datetime.now().isoformat())
    version: str = "1.0.0"
    
    def get_feature(self, feature_name: str, default: Any = None) -> Any:
        """Obtém valor de uma feature"""
        return self.features.get(feature_name, default)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "entity_id": self.entity_id,
            "entity_type": self.entity_type,
            "features": self.features,
            "computed_at": self.computed_at,
            "version": self.version
        }


class FeatureStore:
    """
    Feature Store - Gerenciamento centralizado de features.
    
    Padrão:
    - Features são computadas sob demanda
    - Cache em memória (em produção seria Redis)
    - Versionamento
    - Validação
    
    Features disponíveis:
    
    User Features:
    - n_ratings: número de avaliações
    - avg_rating: média de ratings
    - rating_variance: variância dos ratings
    - favorite_genres: gêneros favoritos
    - activity_score: score de atividade
    - recency_score: quão recente foi última atividade
    - user_embedding: embedding do modelo CF
    
    Item Features:
    - genres: lista de gêneros
    - popularity_score: score de popularidade
    - avg_rating: média de avaliações
    - rating_count: número de avaliações
    - item_embedding: embedding do modelo CF
    
    Contextual Features (request-time):
    - hour_of_day: hora do dia (0-23)
    - day_of_week: dia da semana (0-6)
    - is_weekend: se é fim de semana
    - device_type: tipo de dispositivo
    """
    
    def __init__(self):
        # Registry de definições de features
        self.feature_definitions: Dict[str, FeatureDefinition] = {}
        
        # Cache de features computadas (em produção seria Redis)
        self.user_features_cache: Dict[int, FeatureVector] = {}
        self.item_features_cache: Dict[int, FeatureVector] = {}
        
        # Inicializa definições
        self._register_default_features()
    
    def _register_default_features(self):
        """Registra features padrão"""
        
        # User features
        self.register_feature(FeatureDefinition(
            name="n_ratings",
            feature_type=FeatureType.NUMERICAL,
            description="Número total de avaliações do usuário",
            source="user.n_ratings"
        ))
        
        self.register_feature(FeatureDefinition(
            name="avg_rating",
            feature_type=FeatureType.NUMERICAL,
            description="Média das avaliações do usuário",
            source="user.avg_rating"
        ))
        
        self.register_feature(FeatureDefinition(
            name="rating_variance",
            feature_type=FeatureType.NUMERICAL,
            description="Variância dos ratings (consistência)",
            source="computed"
        ))
        
        self.register_feature(FeatureDefinition(
            name="favorite_genres",
            feature_type=FeatureType.CATEGORICAL,
            description="Gêneros favoritos do usuário",
            source="user.favorite_genres"
        ))
        
        self.register_feature(FeatureDefinition(
            name="activity_score",
            feature_type=FeatureType.NUMERICAL,
            description="Score de atividade (0-1)",
            source="computed",
            dependencies=["n_ratings", "recency_score"]
        ))
        
        self.register_feature(FeatureDefinition(
            name="recency_score",
            feature_type=FeatureType.TEMPORAL,
            description="Quão recente foi última atividade",
            source="user.last_activity"
        ))
        
        self.register_feature(FeatureDefinition(
            name="user_embedding",
            feature_type=FeatureType.EMBEDDING,
            description="Embedding do usuário do modelo CF",
            source="model"
        ))
        
        # Item features
        self.register_feature(FeatureDefinition(
            name="genres",
            feature_type=FeatureType.CATEGORICAL,
            description="Gêneros do filme",
            source="movie.genres"
        ))
        
        self.register_feature(FeatureDefinition(
            name="popularity_score",
            feature_type=FeatureType.NUMERICAL,
            description="Score de popularidade normalizado",
            source="computed",
            dependencies=["rating_count"]
        ))
        
        self.register_feature(FeatureDefinition(
            name="item_avg_rating",
            feature_type=FeatureType.NUMERICAL,
            description="Média de avaliações do item",
            source="movie.avg_rating"
        ))
        
        self.register_feature(FeatureDefinition(
            name="rating_count",
            feature_type=FeatureType.NUMERICAL,
            description="Número de avaliações do item",
            source="movie.rating_count"
        ))
        
        self.register_feature(FeatureDefinition(
            name="item_embedding",
            feature_type=FeatureType.EMBEDDING,
            description="Embedding do item do modelo CF",
            source="model"
        ))
        
        # Contextual features
        self.register_feature(FeatureDefinition(
            name="hour_of_day",
            feature_type=FeatureType.TEMPORAL,
            description="Hora do dia (0-23)",
            source="context"
        ))
        
        self.register_feature(FeatureDefinition(
            name="day_of_week",
            feature_type=FeatureType.TEMPORAL,
            description="Dia da semana (0-6, 0=Monday)",
            source="context"
        ))
        
        self.register_feature(FeatureDefinition(
            name="is_weekend",
            feature_type=FeatureType.CATEGORICAL,
            description="Se é fim de semana",
            source="context",
            dependencies=["day_of_week"]
        ))
    
    def register_feature(self, definition: FeatureDefinition) -> None:
        """
        Registra definição de feature.
        
        Args:
            definition: definição da feature
        """
        self.feature_definitions[definition.name] = definition
    
    def get_feature_definition(self, feature_name: str) -> Optional[FeatureDefinition]:
        """Obtém definição de uma feature"""
        return self.feature_definitions.get(feature_name)
    
    def list_features(self, feature_type: Optional[FeatureType] = None) -> List[FeatureDefinition]:
        """
        Lista features disponíveis.
        
        Args:
            feature_type: filtrar por tipo (opcional)
        
        Returns:
            Lista de definições de features
        """
        features = list(self.feature_definitions.values())
        
        if feature_type:
            features = [f for f in features if f.feature_type == feature_type]
        
        return features
    
    def compute_user_features(
        self,
        user_id: int,
        user_data: Dict[str, Any],
        ratings_data: Optional[List[Dict]] = None
    ) -> FeatureVector:
        """
        Computa features para um usuário.
        
        Args:
            user_id: ID do usuário
            user_data: dados do usuário (do repository)
            ratings_data: lista de ratings do usuário (opcional)
        
        Returns:
            FeatureVector com features computadas
        """
        features = {}
        
        # Features diretas do user
        features["n_ratings"] = user_data.get("n_ratings", 0)
        features["avg_rating"] = user_data.get("avg_rating", 0.0)
        features["favorite_genres"] = user_data.get("favorite_genres", [])
        
        # Computa rating_variance
        if ratings_data and len(ratings_data) > 1:
            ratings = [r["rating"] for r in ratings_data]
            features["rating_variance"] = float(np.var(ratings))
        else:
            features["rating_variance"] = 0.0
        
        # Computa recency_score
        last_activity = user_data.get("last_activity")
        if last_activity:
            from datetime import datetime
            last_dt = datetime.fromisoformat(last_activity) if isinstance(last_activity, str) else last_activity
            days_since = (datetime.now() - last_dt).days
            features["recency_score"] = max(0.0, 1.0 - (days_since / 30.0))  # Decai em 30 dias
        else:
            features["recency_score"] = 0.0
        
        # Computa activity_score
        import math
        n_ratings = features["n_ratings"]
        rating_score = min(1.0, math.log(n_ratings + 1) / math.log(100))
        features["activity_score"] = (0.6 * rating_score) + (0.4 * features["recency_score"])
        
        # Cria FeatureVector
        feature_vector = FeatureVector(
            entity_id=user_id,
            entity_type="user",
            features=features
        )
        
        # Cache
        self.user_features_cache[user_id] = feature_vector
        
        return feature_vector
    
    def compute_item_features(
        self,
        item_id: int,
        item_data: Dict[str, Any],
        max_rating_count: float = 1000.0
    ) -> FeatureVector:
        """
        Computa features para um item.
        
        Args:
            item_id: ID do item
            item_data: dados do item (do repository)
            max_rating_count: máximo para normalização
        
        Returns:
            FeatureVector com features computadas
        """
        features = {}
        
        # Features diretas do item
        features["genres"] = item_data.get("genres", [])
        features["item_avg_rating"] = item_data.get("avg_rating", 0.0)
        features["rating_count"] = item_data.get("rating_count", 0)
        
        # Computa popularity_score (normalizado)
        rating_count = features["rating_count"]
        features["popularity_score"] = min(1.0, rating_count / max_rating_count)
        
        # Cria FeatureVector
        feature_vector = FeatureVector(
            entity_id=item_id,
            entity_type="item",
            features=features
        )
        
        # Cache
        self.item_features_cache[item_id] = feature_vector
        
        return feature_vector
    
    def compute_contextual_features(
        self,
        timestamp: Optional[datetime] = None,
        device_type: str = "web"
    ) -> Dict[str, Any]:
        """
        Computa features contextuais (request-time).
        
        Args:
            timestamp: timestamp da requisição (None = now)
            device_type: tipo de dispositivo
        
        Returns:
            Dict com features contextuais
        """
        if timestamp is None:
            timestamp = datetime.now()
        
        features = {}
        
        # Temporal features
        features["hour_of_day"] = timestamp.hour
        features["day_of_week"] = timestamp.weekday()
        features["is_weekend"] = timestamp.weekday() >= 5  # Saturday=5, Sunday=6
        
        # Device feature
        features["device_type"] = device_type
        
        return features
    
    def get_user_features(
        self,
        user_id: int,
        use_cache: bool = True
    ) -> Optional[FeatureVector]:
        """
        Obtém features de um usuário (do cache).
        
        Args:
            user_id: ID do usuário
            use_cache: se True, usa cache
        
        Returns:
            FeatureVector ou None
        """
        if use_cache and user_id in self.user_features_cache:
            return self.user_features_cache[user_id]
        
        return None
    
    def get_item_features(
        self,
        item_id: int,
        use_cache: bool = True
    ) -> Optional[FeatureVector]:
        """
        Obtém features de um item (do cache).
        
        Args:
            item_id: ID do item
            use_cache: se True, usa cache
        
        Returns:
            FeatureVector ou None
        """
        if use_cache and item_id in self.item_features_cache:
            return self.item_features_cache[item_id]
        
        return None
    
    def invalidate_user_cache(self, user_id: int) -> None:
        """Invalida cache de features de um usuário"""
        if user_id in self.user_features_cache:
            del self.user_features_cache[user_id]
    
    def invalidate_item_cache(self, item_id: int) -> None:
        """Invalida cache de features de um item"""
        if item_id in self.item_features_cache:
            del self.item_features_cache[item_id]
    
    def clear_cache(self) -> None:
        """Limpa todo o cache"""
        self.user_features_cache.clear()
        self.item_features_cache.clear()
    
    def get_feature_stats(self) -> Dict[str, Any]:
        """Retorna estatísticas do feature store"""
        return {
            "total_features_registered": len(self.feature_definitions),
            "features_by_type": {
                feature_type.value: len([
                    f for f in self.feature_definitions.values()
                    if f.feature_type == feature_type
                ])
                for feature_type in FeatureType
            },
            "cached_user_features": len(self.user_features_cache),
            "cached_item_features": len(self.item_features_cache)
        }