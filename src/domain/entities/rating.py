"""
Entity: Rating

Representa uma avaliação de um usuário para um filme.
"""

from dataclasses import dataclass

from ..value_objects import UserId, MovieId, RatingScore, Timestamp


@dataclass
class Rating:
    """
    Entidade: Avaliação
    
    Representa a interação fundamental: User avalia Movie.
    
    Esta é a base de dados para Collaborative Filtering.
    """
    
    user_id: UserId
    movie_id: MovieId
    score: RatingScore
    timestamp: Timestamp
    
    def is_positive(self) -> bool:
        """
        Verifica se rating é positivo.
        
        Usado para identificar filmes que o usuário gostou.
        """
        return self.score.is_positive()
    
    def is_negative(self) -> bool:
        """
        Verifica se rating é negativo.
        
        Usado para evitar recomendar filmes similares aos que o usuário não gostou.
        """
        return self.score.is_negative()
    
    def is_recent(self, days: int = 30) -> bool:
        """
        Verifica se rating é recente.
        
        Ratings recentes têm mais peso em sistemas temporais.
        """
        return self.timestamp.is_recent(days=days)
    
    def get_normalized_score(self) -> float:
        """Retorna score normalizado (0-1)"""
        return self.score.normalize()
    
    def to_interaction_tuple(self) -> tuple:
        """
        Converte para tupla para facilitar processamento em batch.
        
        Retorna: (user_id, movie_id, score, timestamp)
        """
        return (
            int(self.user_id),
            int(self.movie_id),
            float(self.score),
            self.timestamp.to_iso()
        )
    
    def __eq__(self, other: object) -> bool:
        """
        Ratings são únicos por (user_id, movie_id).
        
        Um usuário só pode avaliar um filme uma vez.
        """
        if not isinstance(other, Rating):
            return False
        return self.user_id == other.user_id and self.movie_id == other.movie_id
    
    def __hash__(self) -> int:
        return hash((self.user_id, self.movie_id))
    
    def __repr__(self) -> str:
        return (
            f"Rating(user={self.user_id}, movie={self.movie_id}, "
            f"score={self.score}, time={self.timestamp})"
        )