"""
Entity: Movie

Representa um filme/item no catálogo.
"""

from dataclasses import dataclass, field
from typing import List, Optional

from ..value_objects import MovieId


@dataclass
class Movie:
    """
    Entidade: Filme
    
    Responsabilidades:
    - Manter metadados do filme
    - Calcular popularidade
    - Validar dados
    """
    
    id: MovieId
    title: str
    genres: List[str]
    year: Optional[int] = None
    rating_count: int = 0
    avg_rating: float = 0.0
    content_features: Optional[str] = None  # Para TF-IDF
    
    def __post_init__(self):
        """Validações"""
        if not self.title or len(self.title.strip()) == 0:
            raise ValueError("Title cannot be empty")
        
        if self.rating_count < 0:
            raise ValueError(f"rating_count cannot be negative: {self.rating_count}")
        
        if not (0.0 <= self.avg_rating <= 5.0):
            raise ValueError(f"avg_rating must be 0-5: {self.avg_rating}")
        
        # Garante que genres não está vazio
        if not self.genres:
            self.genres = ["Unknown"]
    
    def add_rating(self, rating_value: float) -> None:
        """
        Adiciona um novo rating ao filme.
        
        Atualiza contagem e média incrementalmente.
        """
        new_total = (self.avg_rating * self.rating_count) + rating_value
        self.rating_count += 1
        self.avg_rating = new_total / self.rating_count
    
    def is_popular(self, threshold: int = 50) -> bool:
        """
        Verifica se filme é popular.
        
        Regra de negócio: popular se tem >= threshold ratings
        """
        return self.rating_count >= threshold
    
    def is_well_rated(self, threshold: float = 4.0) -> bool:
        """
        Verifica se filme é bem avaliado.
        
        Regra de negócio: bem avaliado se avg >= threshold
        """
        return self.avg_rating >= threshold
    
    def has_genre(self, genre: str) -> bool:
        """Verifica se filme pertence a um gênero"""
        return genre.lower() in [g.lower() for g in self.genres]
    
    def get_content_for_tfidf(self) -> str:
        """
        Retorna conteúdo textual para TF-IDF.
        
        Combina título + gêneros para criar features de conteúdo.
        """
        if self.content_features:
            return self.content_features
        
        # Fallback: combina título e gêneros
        genres_text = " ".join(self.genres)
        return f"{self.title} {genres_text}"
    
    def genre_similarity(self, other_genres: List[str]) -> float:
        """
        Calcula similaridade de gêneros com outra lista.
        
        Retorna: Jaccard similarity (0-1)
        """
        if not self.genres or not other_genres:
            return 0.0
        
        set_a = set(g.lower() for g in self.genres)
        set_b = set(g.lower() for g in other_genres)
        
        intersection = len(set_a & set_b)
        union = len(set_a | set_b)
        
        return intersection / union if union > 0 else 0.0
    
    def calculate_popularity_score(self) -> float:
        """
        Calcula score de popularidade do filme.
        
        Fórmula: Combina número de ratings + média de rating
        - Usa log para normalizar rating_count (evita dominância de blockbusters)
        - Pondera avg_rating
        - Score final de 0-10 (mais intuitivo)
        
        Returns:
            Score de 0-10
            
        Examples:
            - Filme com 100 ratings e avg 4.5 → ~9.5
            - Filme com 10 ratings e avg 5.0 → ~7.5
            - Filme com 1000 ratings e avg 3.0 → ~8.0
        """
        import math
        
        if self.rating_count == 0:
            return 0.0
        
        # Componente 1: Log do número de ratings (normalizado 0-5)
        # Log evita que filmes ultra-populares dominem completamente
        # log(100) ≈ 4.6, então dividimos por log(100) para normalizar
        count_score = min(5.0, math.log(self.rating_count + 1) / math.log(100) * 5.0)
        
        # Componente 2: Média de rating (já está 0-5)
        rating_score = self.avg_rating
        
        # Score final: soma dos dois componentes (0-10)
        # Isso balanceia popularidade (count) com qualidade (rating)
        popularity = count_score + rating_score
        
        return round(popularity, 2)
    
    def __eq__(self, other: object) -> bool:
        """Comparação por identidade (ID)"""
        if not isinstance(other, Movie):
            return False
        return self.id == other.id
    
    def __hash__(self) -> int:
        return hash(self.id)
    
    def __repr__(self) -> str:
        genres_str = ", ".join(self.genres[:2])
        return (
            f"Movie(id={self.id}, title='{self.title}', "
            f"genres=[{genres_str}], ratings={self.rating_count})"
        )