"""
Unit Tests: Value Objects

Testa Value Objects do domínio.
"""

import pytest
from datetime import datetime, timedelta

from src.domain.value_objects import (
    UserId,
    MovieId,
    RatingScore,
    RecommendationScore,
    Timestamp
)


class TestUserId:
    """Testes para UserId Value Object"""
    
    def test_valid_user_id(self):
        """Cria UserId válido"""
        user_id = UserId(1)
        assert int(user_id) == 1
    
    def test_user_id_equality(self):
        """UserIds com mesmo valor são iguais"""
        id1 = UserId(1)
        id2 = UserId(1)
        id3 = UserId(2)
        
        assert id1 == id2
        assert id1 != id3
    
    def test_user_id_immutable(self):
        """UserId é imutável"""
        user_id = UserId(1)
        
        with pytest.raises(AttributeError):
            user_id.value = 2
    
    def test_invalid_user_id_zero(self):
        """UserId não pode ser zero"""
        with pytest.raises(ValueError, match="UserId must be positive"):
            UserId(0)
    
    def test_invalid_user_id_negative(self):
        """UserId não pode ser negativo"""
        with pytest.raises(ValueError, match="UserId must be positive"):
            UserId(-1)
    
    def test_user_id_hashable(self):
        """UserId pode ser usado em sets/dicts"""
        id1 = UserId(1)
        id2 = UserId(1)
        id3 = UserId(2)
        
        id_set = {id1, id2, id3}
        assert len(id_set) == 2  # id1 e id2 são iguais


class TestMovieId:
    """Testes para MovieId Value Object"""
    
    def test_valid_movie_id(self):
        """Cria MovieId válido"""
        movie_id = MovieId(100)
        assert int(movie_id) == 100
    
    def test_movie_id_equality(self):
        """MovieIds com mesmo valor são iguais"""
        id1 = MovieId(100)
        id2 = MovieId(100)
        id3 = MovieId(200)
        
        assert id1 == id2
        assert id1 != id3
    
    def test_invalid_movie_id_negative(self):
        """MovieId não pode ser negativo"""
        with pytest.raises(ValueError):
            MovieId(-1)


class TestRatingScore:
    """Testes para RatingScore Value Object"""
    
    def test_valid_rating_scores(self):
        """Testa todos os scores válidos"""
        valid_scores = [0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0, 4.5, 5.0]
        
        for score in valid_scores:
            rating_score = RatingScore(score)
            assert float(rating_score) == score
    
    def test_rating_score_equality(self):
        """RatingScores com mesmo valor são iguais"""
        score1 = RatingScore(4.5)
        score2 = RatingScore(4.5)
        score3 = RatingScore(3.5)
        
        assert score1 == score2
        assert score1 != score3
    
    def test_rating_score_immutable(self):
        """RatingScore é imutável"""
        score = RatingScore(4.5)
        
        with pytest.raises(AttributeError):
            score.value = 3.0
    
    def test_invalid_rating_score_too_low(self):
        """Score não pode ser < 0.5"""
        with pytest.raises(ValueError, match="RatingScore must be between"):
            RatingScore(0.0)
    
    def test_invalid_rating_score_too_high(self):
        """Score não pode ser > 5.0"""
        with pytest.raises(ValueError, match="RatingScore must be between"):
            RatingScore(5.5)
    
    def test_invalid_rating_score_not_half_increment(self):
        """Score deve ser múltiplo de 0.5"""
        with pytest.raises(ValueError, match="must be in 0.5 increments"):
            RatingScore(3.7)
    
    def test_is_positive(self):
        """Testa classificação positiva"""
        assert RatingScore(4.5).is_positive() is True
        assert RatingScore(4.0).is_positive() is True
        assert RatingScore(3.5).is_positive() is False
    
    def test_is_negative(self):
        """Testa classificação negativa"""
        assert RatingScore(2.5).is_negative() is True
        assert RatingScore(2.0).is_negative() is True
        assert RatingScore(3.0).is_negative() is False
    
    def test_normalize(self):
        """Testa normalização"""
        score_max = RatingScore(5.0)
        score_min = RatingScore(0.5)
        score_mid = RatingScore(3.0)  # Mudado de 2.75 para 3.0 (múltiplo de 0.5)
        
        assert score_max.normalize() == pytest.approx(1.0)
        assert score_min.normalize() == pytest.approx(0.0)
        assert 0.5 <= score_mid.normalize() <= 0.6


class TestRecommendationScore:
    """Testes para RecommendationScore Value Object"""
    
    def test_valid_recommendation_score(self):
        """Cria RecommendationScore válido"""
        score = RecommendationScore(0.85)
        assert float(score) == 0.85
    
    def test_invalid_recommendation_score_negative(self):
        """Score não pode ser negativo"""
        with pytest.raises(ValueError, match="RecommendationScore must be between"):
            RecommendationScore(-0.1)
    
    def test_invalid_recommendation_score_too_high(self):
        """Score não pode ser > 1.0"""
        with pytest.raises(ValueError, match="RecommendationScore must be between"):
            RecommendationScore(1.5)
    
    def test_confidence_level_very_high(self):
        """Score >= 0.8 é very_high"""
        score = RecommendationScore(0.9)
        assert score.confidence_level() == "very_high"
    
    def test_confidence_level_high(self):
        """Score 0.6-0.8 é high"""
        score = RecommendationScore(0.7)
        assert score.confidence_level() == "high"
    
    def test_confidence_level_medium(self):
        """Score 0.4-0.6 é medium"""
        score = RecommendationScore(0.5)
        assert score.confidence_level() == "medium"
    
    def test_confidence_level_low(self):
        """Score 0.2-0.4 é low"""
        score = RecommendationScore(0.3)
        assert score.confidence_level() == "low"
    
    def test_confidence_level_very_low(self):
        """Score < 0.2 é very_low"""
        score = RecommendationScore(0.1)
        assert score.confidence_level() == "very_low"
    
    def test_recommendation_score_comparable(self):
        """RecommendationScores podem ser comparados"""
        score1 = RecommendationScore(0.8)
        score2 = RecommendationScore(0.6)
        score3 = RecommendationScore(0.9)
        
        assert score1 > score2
        assert score3 > score1
        assert score2 < score1


class TestTimestamp:
    """Testes para Timestamp Value Object"""
    
    def test_timestamp_now(self):
        """Cria timestamp atual"""
        ts = Timestamp.now()
        assert isinstance(ts.value, datetime)
    
    def test_timestamp_from_datetime(self):
        """Cria timestamp de datetime"""
        dt = datetime(2024, 1, 1, 12, 0, 0)
        ts = Timestamp(dt)
        assert ts.value == dt
    
    def test_timestamp_age_in_days(self):
        """Testa cálculo de idade em dias"""
        old_date = datetime.now() - timedelta(days=10)
        ts = Timestamp(old_date)
        
        age = ts.age_in_days()
        assert 9 <= age <= 11  # Aproximadamente 10 dias
    
    def test_timestamp_is_recent(self):
        """Testa verificação de recência"""
        recent = Timestamp.now()
        old = Timestamp(datetime.now() - timedelta(days=31))
        
        assert recent.is_recent(days=30) is True
        assert old.is_recent(days=30) is False
    
    def test_timestamp_to_iso(self):
        """Testa conversão para ISO string"""
        dt = datetime(2024, 1, 1, 12, 0, 0)
        ts = Timestamp(dt)
        
        iso = ts.to_iso()
        assert isinstance(iso, str)
        assert "2024-01-01" in iso