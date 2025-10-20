"""
Unit Tests: Rating Entity

Testa lógica de negócio da entidade Rating.
"""

import pytest
from datetime import datetime, timedelta

from src.domain.entities import Rating
from src.domain.value_objects import UserId, MovieId, RatingScore, Timestamp


class TestRatingEntity:
    """Testes para Rating entity"""
    
    def test_rating_creation(self):
        """Testa criação básica de rating"""
        rating = Rating(
            user_id=UserId(1),
            movie_id=MovieId(100),
            score=RatingScore(4.5),
            timestamp=Timestamp.now()
        )
        
        assert rating.user_id == UserId(1)
        assert rating.movie_id == MovieId(100)
        assert float(rating.score) == 4.5
    
    def test_is_positive_high_rating(self):
        """Rating >= 4.0 é positivo"""
        rating = Rating(
            user_id=UserId(1),
            movie_id=MovieId(100),
            score=RatingScore(4.5),
            timestamp=Timestamp.now()
        )
        
        assert rating.is_positive() is True
        assert rating.is_negative() is False
    
    def test_is_positive_boundary_4_0(self):
        """Rating exatamente 4.0 é positivo"""
        rating = Rating(
            user_id=UserId(1),
            movie_id=MovieId(100),
            score=RatingScore(4.0),
            timestamp=Timestamp.now()
        )
        
        assert rating.is_positive() is True
    
    def test_is_negative_low_rating(self):
        """Rating <= 2.5 é negativo"""
        rating = Rating(
            user_id=UserId(1),
            movie_id=MovieId(100),
            score=RatingScore(2.0),
            timestamp=Timestamp.now()
        )
        
        assert rating.is_negative() is True
        assert rating.is_positive() is False
    
    def test_is_negative_boundary_2_5(self):
        """Rating exatamente 2.5 é negativo"""
        rating = Rating(
            user_id=UserId(1),
            movie_id=MovieId(100),
            score=RatingScore(2.5),
            timestamp=Timestamp.now()
        )
        
        assert rating.is_negative() is True
    
    def test_neutral_rating(self):
        """Rating 3.0-3.5 é neutro (nem positivo nem negativo)"""
        rating = Rating(
            user_id=UserId(1),
            movie_id=MovieId(100),
            score=RatingScore(3.0),
            timestamp=Timestamp.now()
        )
        
        assert rating.is_positive() is False
        assert rating.is_negative() is False
    
    def test_is_recent_within_30_days(self):
        """Rating nos últimos 30 dias é recente"""
        rating = Rating(
            user_id=UserId(1),
            movie_id=MovieId(100),
            score=RatingScore(4.0),
            timestamp=Timestamp.now()
        )
        
        assert rating.is_recent(days=30) is True
    
    def test_is_not_recent_old_rating(self):
        """Rating de 31+ dias não é recente"""
        old_date = datetime.now() - timedelta(days=31)
        rating = Rating(
            user_id=UserId(1),
            movie_id=MovieId(100),
            score=RatingScore(4.0),
            timestamp=Timestamp(old_date)
        )
        
        assert rating.is_recent(days=30) is False
    
    def test_get_normalized_score(self):
        """Testa normalização de score para 0-1"""
        rating = Rating(
            user_id=UserId(1),
            movie_id=MovieId(100),
            score=RatingScore(5.0),
            timestamp=Timestamp.now()
        )
        
        normalized = rating.get_normalized_score()
        
        # 5.0 deve ser normalizado para 1.0
        assert normalized == pytest.approx(1.0)
    
    def test_get_normalized_score_min(self):
        """Score mínimo (0.5) normaliza para 0.0"""
        rating = Rating(
            user_id=UserId(1),
            movie_id=MovieId(100),
            score=RatingScore(0.5),
            timestamp=Timestamp.now()
        )
        
        normalized = rating.get_normalized_score()
        assert normalized == pytest.approx(0.0)
    
    def test_to_interaction_tuple(self):
        """Testa conversão para tupla"""
        rating = Rating(
            user_id=UserId(1),
            movie_id=MovieId(100),
            score=RatingScore(4.5),
            timestamp=Timestamp.now()
        )
        
        user_id, movie_id, score, timestamp = rating.to_interaction_tuple()
        
        assert user_id == 1
        assert movie_id == 100
        assert score == 4.5
        assert isinstance(timestamp, str)
    
    def test_rating_equality(self):
        """Ratings são únicos por (user_id, movie_id)"""
        rating1 = Rating(
            user_id=UserId(1),
            movie_id=MovieId(100),
            score=RatingScore(4.5),
            timestamp=Timestamp.now()
        )
        
        rating2 = Rating(
            user_id=UserId(1),
            movie_id=MovieId(100),
            score=RatingScore(3.0),  # Score diferente, mas mesmo user+movie
            timestamp=Timestamp.now()
        )
        
        rating3 = Rating(
            user_id=UserId(2),
            movie_id=MovieId(100),
            score=RatingScore(4.5),
            timestamp=Timestamp.now()
        )
        
        assert rating1 == rating2  # Mesmo user+movie
        assert rating1 != rating3  # User diferente
    
    def test_rating_hashable(self):
        """Ratings podem ser usados em sets/dicts"""
        rating1 = Rating(
            user_id=UserId(1),
            movie_id=MovieId(100),
            score=RatingScore(4.5),
            timestamp=Timestamp.now()
        )
        
        rating2 = Rating(
            user_id=UserId(1),
            movie_id=MovieId(100),
            score=RatingScore(3.0),
            timestamp=Timestamp.now()
        )
        
        # Set deve conter apenas 1 elemento (mesmo hash)
        rating_set = {rating1, rating2}
        assert len(rating_set) == 1