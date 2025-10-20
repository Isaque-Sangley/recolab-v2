"""
Entity: Recommendation

Representa uma recomendação gerada pelo sistema.
"""

from dataclasses import dataclass, field
from typing import Dict, Any, Optional
from enum import Enum

from ..value_objects import UserId, MovieId, RecommendationScore, Timestamp


class RecommendationSource(str, Enum):
    """
    Fonte da recomendação.
    
    Importante para explicabilidade e debugging.
    """
    COLLABORATIVE = "collaborative"
    CONTENT_BASED = "content_based"
    HYBRID = "hybrid"
    POPULAR = "popular"
    GENRE_BASED = "genre_based"
    PERSONALIZED = "personalized"


@dataclass
class Recommendation:
    """
    Entidade: Recomendação
    
    Representa uma sugestão de filme para um usuário.
    
    Inclui metadata para explicabilidade e análise.
    """
    
    user_id: UserId
    movie_id: MovieId
    score: RecommendationScore
    source: RecommendationSource
    timestamp: Timestamp
    rank: int  # Posição na lista (1 = primeira recomendação)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Validações"""
        if self.rank < 1:
            raise ValueError(f"Rank must be >= 1, got {self.rank}")
    
    def add_metadata(self, key: str, value: Any) -> None:
        """
        Adiciona metadata para explicabilidade.
        
        Exemplos:
        - "similar_to": [movie_id1, movie_id2]
        - "matching_genres": ["Action", "Sci-Fi"]
        - "cf_weight": 0.7
        """
        self.metadata[key] = value
    
    def get_metadata(self, key: str, default: Any = None) -> Any:
        """Recupera metadata"""
        return self.metadata.get(key, default)
    
    def is_high_confidence(self, threshold: float = 0.7) -> bool:
        """
        Verifica se é recomendação de alta confiança.
        
        Alta confiança = score >= threshold
        """
        return float(self.score) >= threshold
    
    def get_explanation(self) -> str:
        """
        Gera explicação humanizada da recomendação.
        
        Exemplos:
        - "Baseado em filmes similares que você assistiu"
        - "Popular entre usuários com gostos parecidos"
        - "Combina com seus gêneros favoritos: Action, Sci-Fi"
        """
        explanations = {
            RecommendationSource.COLLABORATIVE: "Baseado em usuários com gostos similares",
            RecommendationSource.CONTENT_BASED: "Baseado em filmes que você gostou",
            RecommendationSource.HYBRID: "Combinação de múltiplos fatores",
            RecommendationSource.POPULAR: "Popular no catálogo",
            RecommendationSource.GENRE_BASED: "Baseado nos seus gêneros favoritos",
            RecommendationSource.PERSONALIZED: "Personalizado para você"
        }
        
        base_explanation = explanations.get(
            self.source,
            "Recomendado pelo sistema"
        )
        
        # Adiciona informação de confiança
        confidence = self.score.confidence_level()
        confidence_text = {
            "very_high": "Alta confiança",
            "high": "Boa confiança",
            "medium": "Confiança média",
            "low": "Baixa confiança",
            "very_low": "Muito baixa confiança"
        }.get(confidence, "")
        
        return f"{base_explanation} ({confidence_text}: {self.score})"
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Converte para dicionário (útil para API responses).
        """
        return {
            "user_id": int(self.user_id),
            "movie_id": int(self.movie_id),
            "score": float(self.score),
            "source": self.source.value,
            "rank": self.rank,
            "timestamp": self.timestamp.to_iso(),
            "confidence_level": self.score.confidence_level(),
            "explanation": self.get_explanation(),
            "metadata": self.metadata
        }
    
    def __eq__(self, other: object) -> bool:
        """
        Recomendações são únicas por (user_id, movie_id, timestamp).
        """
        if not isinstance(other, Recommendation):
            return False
        return (
            self.user_id == other.user_id and
            self.movie_id == other.movie_id and
            self.timestamp == other.timestamp
        )
    
    def __hash__(self) -> int:
        return hash((self.user_id, self.movie_id, self.timestamp))
    
    def __lt__(self, other: 'Recommendation') -> bool:
        """
        Permite ordenação por score (maior primeiro).
        
        Usado em: sorted(recommendations)
        """
        return self.score > other.score  # Invertido: maior score = menor na ordenação
    
    def __repr__(self) -> str:
        return (
            f"Recommendation(user={self.user_id}, movie={self.movie_id}, "
            f"score={self.score}, rank={self.rank}, source={self.source.value})"
        )