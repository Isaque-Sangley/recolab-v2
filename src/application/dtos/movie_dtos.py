"""
Movie DTOs
"""

from dataclasses import dataclass
from typing import List, Optional


@dataclass
class MovieDTO:
    """DTO de filme"""

    id: int
    title: str
    genres: List[str]
    year: Optional[int]
    rating_count: int
    avg_rating: float

    # Campos computados
    popularity_score: float
    is_popular: bool
    is_well_rated: bool

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "title": self.title,
            "genres": self.genres,
            "year": self.year,
            "rating_count": self.rating_count,
            "avg_rating": self.avg_rating,
            "popularity_score": self.popularity_score,
            "is_popular": self.is_popular,
            "is_well_rated": self.is_well_rated,
        }


@dataclass
class MovieDetailDTO:
    """DTO detalhado de filme"""

    movie: MovieDTO
    similar_movies: List[MovieDTO]
    genre_distribution: dict  # Distribuição de ratings por gênero

    def to_dict(self) -> dict:
        return {
            "movie": self.movie.to_dict(),
            "similar_movies": [m.to_dict() for m in self.similar_movies],
            "genre_distribution": self.genre_distribution,
        }


@dataclass
class SearchMoviesRequest:
    """Request para buscar filmes"""

    query: str
    limit: int = 50


@dataclass
class FilterMoviesRequest:
    """Request para filtrar filmes"""

    genres: Optional[List[str]] = None
    min_year: Optional[int] = None
    max_year: Optional[int] = None
    min_rating: Optional[float] = None
    min_rating_count: Optional[int] = None
    limit: int = 100
