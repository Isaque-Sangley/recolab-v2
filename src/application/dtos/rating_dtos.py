"""
Rating DTOs
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class RatingDTO:
    """DTO de rating"""
    user_id: int
    movie_id: int
    score: float
    timestamp: str
    
    def to_dict(self) -> dict:
        return {
            "user_id": self.user_id,
            "movie_id": self.movie_id,
            "score": self.score,
            "timestamp": self.timestamp
        }


@dataclass
class CreateRatingRequest:
    """Request para criar rating"""
    user_id: int
    movie_id: int
    score: float
    
    def validate(self) -> None:
        """Valida request"""
        if not 0.5 <= self.score <= 5.0:
            raise ValueError("Rating must be between 0.5 and 5.0")
        
        if self.score % 0.5 != 0:
            raise ValueError("Rating must be in 0.5 increments")


@dataclass
class UpdateRatingRequest:
    """Request para atualizar rating"""
    user_id: int
    movie_id: int
    score: float
    
    def validate(self) -> None:
        if not 0.5 <= self.score <= 5.0:
            raise ValueError("Rating must be between 0.5 and 5.0")
        
        if self.score % 0.5 != 0:
            raise ValueError("Rating must be in 0.5 increments")


@dataclass
class DeleteRatingRequest:
    """Request para deletar rating"""
    user_id: int
    movie_id: int