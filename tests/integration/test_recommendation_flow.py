"""
Integration Tests: Recommendation Flow

Testa fluxo completo de geração de recomendações.
"""

import pytest
import os
from datetime import datetime
from src.domain.entities import User, Movie
from src.domain.value_objects import UserId, MovieId, Timestamp
from src.infrastructure.persistence.user_repository import UserRepository
from src.infrastructure.persistence.movie_repository import MovieRepository
from src.domain.services import RecommendationStrategyService


# SKIP se não tiver PostgreSQL
pytestmark = [
    pytest.mark.integration,
    pytest.mark.skipif(
        not os.getenv("DATABASE_URL") or "sqlite" in os.getenv("DATABASE_URL", "").lower(),
        reason="Integration tests require PostgreSQL. Set DATABASE_URL=postgresql://..."
    )
]


@pytest.mark.integration
class TestRecommendationFlow:
    """Testes de integração para fluxo de recomendações"""
    
    @pytest.fixture
    async def user_repo(self, db_session):
        return UserRepository(db_session)
    
    @pytest.fixture
    async def movie_repo(self, db_session):
        return MovieRepository(db_session)
    
    @pytest.fixture
    def strategy_service(self):
        return RecommendationStrategyService()
    
    @pytest.fixture
    async def sample_movies(self, movie_repo):
        """Cria filmes de exemplo no banco"""
        movies = [
            Movie(
                id=MovieId(1),
                title="The Matrix",
                genres=["Action", "Sci-Fi"],
                year=1999,
                rating_count=500,
                avg_rating=4.5
            ),
            Movie(
                id=MovieId(2),
                title="Inception",
                genres=["Action", "Sci-Fi", "Thriller"],
                year=2010,
                rating_count=600,
                avg_rating=4.7
            ),
            Movie(
                id=MovieId(3),
                title="The Shawshank Redemption",
                genres=["Drama"],
                year=1994,
                rating_count=700,
                avg_rating=4.9
            ),
            Movie(
                id=MovieId(4),
                title="Pulp Fiction",
                genres=["Crime", "Drama"],
                year=1994,
                rating_count=650,
                avg_rating=4.6
            ),
        ]
        
        saved_movies = []
        for movie in movies:
            saved = await movie_repo.save(movie)
            saved_movies.append(saved)
        
        return saved_movies
    
    async def test_cold_start_user_recommendation(
        self,
        user_repo,
        movie_repo,
        strategy_service,
        sample_movies
    ):
        """Cold start user deve receber filmes populares"""
        # Cria usuário cold start
        user = User(
            id=UserId(1),
            created_at=Timestamp.now(),
            n_ratings=0
        )
        await user_repo.save(user)
        
        # Decide estratégia
        strategy = strategy_service.decide_strategy(user)
        
        # Verifica estratégia
        assert strategy.strategy == StrategyType.POPULAR
        
        # Busca filmes populares
        popular_movies = await movie_repo.find_popular(min_rating_count=50, limit=10)
        
        # Verifica que retornou filmes
        assert len(popular_movies) > 0
        
        # Verifica que são ordenados por popularidade
        ratings = [m.rating_count for m in popular_movies]
        assert ratings == sorted(ratings, reverse=True)
    
    async def test_casual_user_gets_content_based_strategy(
        self,
        user_repo,
        strategy_service
    ):
        """Usuário casual deve receber estratégia content-based"""
        # Cria usuário casual
        user = User(
            id=UserId(2),
            created_at=Timestamp.now(),
            n_ratings=10,
            avg_rating=4.0,
            favorite_genres=["Action", "Sci-Fi"]
        )
        await user_repo.save(user)
        
        # Decide estratégia
        strategy = strategy_service.decide_strategy(user)
        
        # Verifica
        assert strategy.strategy == StrategyType.CONTENT_BASED
        assert strategy.cb_weight > strategy.cf_weight
    
    async def test_find_movies_by_genre(self, movie_repo, sample_movies):
        """Testa busca de filmes por gênero"""
        # Busca filmes de ação
        action_movies = await movie_repo.find_by_genres(["Action"], limit=10)
        
        # Verifica
        assert len(action_movies) >= 2  # Matrix e Inception
        assert all(m.has_genre("Action") for m in action_movies)
    
    async def test_find_well_rated_movies(self, movie_repo, sample_movies):
        """Testa busca de filmes bem avaliados"""
        well_rated = await movie_repo.find_well_rated(
            min_avg_rating=4.5,
            min_rating_count=50,
            limit=10
        )
        
        # Verifica
        assert len(well_rated) > 0
        assert all(m.avg_rating >= 4.5 for m in well_rated)
        assert all(m.rating_count >= 50 for m in well_rated)
    
    async def test_movie_popularity_score_calculation(self, sample_movies):
        """Testa cálculo de score de popularidade"""
        for movie in sample_movies:
            score = movie.calculate_popularity_score()
            
            # Score deve estar entre 0-10
            assert 0.0 <= score <= 10.0
            
            # Filmes populares devem ter score alto
            if movie.rating_count >= 500:
                assert score > 7.0
    
    async def test_user_classification_accuracy(self, user_repo):
        """Testa que classificação de usuário está correta"""
        test_cases = [
            (0, "cold_start"),
            (3, "new"),
            (10, "casual"),
            (50, "active"),
            (150, "power_user"),
        ]
        
        for n_ratings, expected_type in test_cases:
            user = User(
                id=UserId(100 + n_ratings),
                created_at=Timestamp.now(),
                n_ratings=n_ratings,
                avg_rating=4.0
            )
            await user_repo.save(user)
            
            # Verifica classificação
            assert user.classify_type() == expected_type