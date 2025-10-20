"""
Unit Tests: User Entity

Testa lógica de negócio da entidade User.
"""

import pytest
from datetime import datetime, timedelta

from src.domain.entities import User
from src.domain.value_objects import UserId, Timestamp


class TestUserEntity:
    """Testes para User entity"""
    
    def test_user_creation(self):
        """Testa criação básica de usuário"""
        user = User(
            id=UserId(1),
            created_at=Timestamp.now(),
            n_ratings=0,
            avg_rating=0.0
        )
        
        assert user.id == UserId(1)
        assert user.n_ratings == 0
        assert user.avg_rating == 0.0
    
    def test_user_classification_cold_start(self, cold_start_user):
        """Cold start user (0 ratings)"""
        assert cold_start_user.classify_type() == "cold_start"
        assert cold_start_user.get_user_type() == "cold_start"
    
    def test_user_classification_new(self):
        """New user (1-4 ratings)"""
        user = User(
            id=UserId(1),
            created_at=Timestamp.now(),
            n_ratings=3,
            avg_rating=4.0
        )
        assert user.classify_type() == "new"
    
    def test_user_classification_casual(self):
        """Casual user (5-19 ratings)"""
        user = User(
            id=UserId(1),
            created_at=Timestamp.now(),
            n_ratings=10,
            avg_rating=4.0
        )
        assert user.classify_type() == "casual"
    
    def test_user_classification_active(self):
        """Active user (20-99 ratings)"""
        user = User(
            id=UserId(1),
            created_at=Timestamp.now(),
            n_ratings=50,
            avg_rating=4.0
        )
        assert user.classify_type() == "active"
    
    def test_user_classification_power_user(self, power_user):
        """Power user (100+ ratings)"""
        assert power_user.classify_type() == "power_user"
    
    def test_record_rating_updates_stats(self):
        """Testar que record_rating atualiza estatísticas"""
        user = User(
            id=UserId(1),
            created_at=Timestamp.now(),
            n_ratings=0,
            avg_rating=0.0
        )
        
        # Adiciona primeiro rating
        user.record_rating(4.5)
        assert user.n_ratings == 1
        assert user.avg_rating == 4.5
        assert user.last_activity is not None
        
        # Adiciona segundo rating
        user.record_rating(3.5)
        assert user.n_ratings == 2
        assert user.avg_rating == 4.0  # (4.5 + 3.5) / 2
    
    def test_mark_activity_updates_timestamp(self, sample_user):
        """Testa que mark_activity atualiza timestamp"""
        import time
        
        old_activity = sample_user.last_activity
        
        # Pequeno delay para garantir que timestamp será diferente
        time.sleep(0.001)
        
        sample_user.mark_activity()
        
        assert sample_user.last_activity != old_activity
        assert sample_user.last_activity is not None
    
    def test_is_active_user_recent_activity(self):
        """Usuário é ativo se teve atividade nos últimos 30 dias"""
        user = User(
            id=UserId(1),
            created_at=Timestamp.now(),
            n_ratings=10,
            avg_rating=4.0,
            last_activity=Timestamp.now()
        )
        
        assert user.is_active_user() is True
    
    def test_is_active_user_old_activity(self):
        """Usuário não é ativo se última atividade foi há 31+ dias"""
        old_date = datetime.now() - timedelta(days=31)
        user = User(
            id=UserId(1),
            created_at=Timestamp.now(),
            n_ratings=10,
            avg_rating=4.0,
            last_activity=Timestamp(old_date)
        )
        
        assert user.is_active_user() is False
    
    def test_cf_weight_increases_with_ratings(self):
        """Peso CF aumenta conforme usuário tem mais ratings"""
        cold_start = User(id=UserId(1), created_at=Timestamp.now(), n_ratings=0)
        casual = User(id=UserId(2), created_at=Timestamp.now(), n_ratings=10)
        power = User(id=UserId(3), created_at=Timestamp.now(), n_ratings=150)
        
        assert cold_start.get_cf_weight() < casual.get_cf_weight()
        assert casual.get_cf_weight() < power.get_cf_weight()
    
    def test_cb_weight_is_complement_of_cf(self, sample_user):
        """CB weight é complementar ao CF weight"""
        cf_weight = sample_user.get_cf_weight()
        cb_weight = sample_user.get_cb_weight()
        
        assert cf_weight + cb_weight == pytest.approx(1.0)
    
    def test_update_favorite_genres(self, sample_user):
        """Testa atualização de gêneros favoritos"""
        new_genres = ["Comedy", "Drama", "Horror"]
        sample_user.update_favorite_genres(new_genres)
        
        assert sample_user.favorite_genres == new_genres
    
    def test_update_favorite_genres_max_5(self, sample_user):
        """Máximo 5 gêneros favoritos"""
        with pytest.raises(ValueError, match="Maximum 5 favorite genres"):
            sample_user.update_favorite_genres(["A", "B", "C", "D", "E", "F"])
    
    def test_user_equality_by_id(self):
        """Usuários são iguais se têm mesmo ID"""
        user1 = User(id=UserId(1), created_at=Timestamp.now())
        user2 = User(id=UserId(1), created_at=Timestamp.now(), n_ratings=100)
        user3 = User(id=UserId(2), created_at=Timestamp.now())
        
        assert user1 == user2  # Mesmo ID
        assert user1 != user3  # IDs diferentes
    
    def test_invalid_n_ratings(self):
        """n_ratings não pode ser negativo"""
        with pytest.raises(ValueError, match="n_ratings cannot be negative"):
            User(
                id=UserId(1),
                created_at=Timestamp.now(),
                n_ratings=-1
            )
    
    def test_invalid_avg_rating(self):
        """avg_rating deve estar entre 0-5"""
        with pytest.raises(ValueError, match="avg_rating must be 0-5"):
            User(
                id=UserId(1),
                created_at=Timestamp.now(),
                avg_rating=6.0
            )