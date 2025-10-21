"""
Integration Tests: Rating Flow

Testa fluxo completo de criação/atualização/deleção de ratings.
"""

import pytest
import os
from src.domain.entities import User, Movie, Rating
from src.domain.value_objects import UserId, MovieId, RatingScore, Timestamp
from src.infrastructure.persistence.rating_repository import RatingRepository
from src.infrastructure.persistence.user_repository import UserRepository
from src.infrastructure.persistence.movie_repository import MovieRepository


# SKIP se não tiver PostgreSQL
pytestmark = [
    pytest.mark.integration,
    pytest.mark.skipif(
        not os.getenv("DATABASE_URL") or "sqlite" in os.getenv("DATABASE_URL", "").lower(),
        reason="Integration tests require PostgreSQL. Set DATABASE_URL=postgresql://..."
    )
]


@pytest.mark.integration
class TestRatingFlow:
    """Testes de integração para fluxo de ratings"""
    
    @pytest.fixture
    async def user_repo(self, db_session):
        """Cria repository de usuários"""
        return UserRepository(db_session)
    
    @pytest.fixture
    async def movie_repo(self, db_session):
        """Cria repository de filmes"""
        return MovieRepository(db_session)
    
    @pytest.fixture
    async def rating_repo(self, db_session):
        """Cria repository de ratings"""
        return RatingRepository(db_session)
    
    @pytest.fixture
    async def test_user(self, user_repo):
        """Cria usuário de teste no banco"""
        user = User(
            id=UserId(1),
            created_at=Timestamp.now(),
            n_ratings=0,
            avg_rating=0.0
        )
        
        saved_user = await user_repo.save(user)
        return saved_user
    
    @pytest.fixture
    async def test_movie(self, movie_repo):
        """Cria filme de teste no banco"""
        movie = Movie(
            id=MovieId(1),
            title="Test Movie",
            genres=["Drama", "Action"],
            year=2020,
            rating_count=0,
            avg_rating=0.0
        )
        
        saved_movie = await movie_repo.save(movie)
        return saved_movie
    
    async def test_create_rating(self, rating_repo, test_user, test_movie):
        """Testa criação de rating"""
        rating = Rating(
            user_id=test_user.id,
            movie_id=test_movie.id,
            score=RatingScore(4.5),
            timestamp=Timestamp.now()
        )
        
        # Salva
        saved_rating = await rating_repo.save(rating)
        
        # Verifica
        assert saved_rating.user_id == test_user.id
        assert saved_rating.movie_id == test_movie.id
        assert float(saved_rating.score) == 4.5
    
    async def test_find_rating_by_user_and_movie(
        self, 
        rating_repo, 
        test_user, 
        test_movie
    ):
        """Testa busca de rating específico"""
        # Cria rating
        rating = Rating(
            user_id=test_user.id,
            movie_id=test_movie.id,
            score=RatingScore(4.0),
            timestamp=Timestamp.now()
        )
        await rating_repo.save(rating)
        
        # Busca
        found = await rating_repo.find_by_user_and_movie(
            test_user.id,
            test_movie.id
        )
        
        # Verifica
        assert found is not None
        assert found.user_id == test_user.id
        assert found.movie_id == test_movie.id
        assert float(found.score) == 4.0
    
    async def test_update_rating(self, rating_repo, test_user, test_movie):
        """Testa atualização de rating"""
        # Cria rating inicial
        rating = Rating(
            user_id=test_user.id,
            movie_id=test_movie.id,
            score=RatingScore(3.0),
            timestamp=Timestamp.now()
        )
        await rating_repo.save(rating)
        
        # Atualiza score
        rating_updated = Rating(
            user_id=test_user.id,
            movie_id=test_movie.id,
            score=RatingScore(5.0),
            timestamp=Timestamp.now()
        )
        await rating_repo.save(rating_updated)
        
        # Busca e verifica
        found = await rating_repo.find_by_user_and_movie(
            test_user.id,
            test_movie.id
        )
        
        assert found is not None
        assert float(found.score) == 5.0  # Score atualizado
    
    async def test_delete_rating(self, rating_repo, test_user, test_movie):
        """Testa deleção de rating"""
        # Cria rating
        rating = Rating(
            user_id=test_user.id,
            movie_id=test_movie.id,
            score=RatingScore(4.0),
            timestamp=Timestamp.now()
        )
        await rating_repo.save(rating)
        
        # Deleta
        success = await rating_repo.delete_by_user_and_movie(
            test_user.id,
            test_movie.id
        )
        
        assert success is True
        
        # Verifica que não existe mais
        found = await rating_repo.find_by_user_and_movie(
            test_user.id,
            test_movie.id
        )
        
        assert found is None
    
    async def test_find_ratings_by_user(self, rating_repo, test_user, movie_repo):
        """Testa busca de todos os ratings de um usuário"""
        # Cria múltiplos filmes
        movies = []
        for i in range(3):
            movie = Movie(
                id=MovieId(100 + i),
                title=f"Movie {i}",
                genres=["Drama"]
            )
            saved_movie = await movie_repo.save(movie)
            movies.append(saved_movie)
        
        # Cria ratings para cada filme
        for movie in movies:
            rating = Rating(
                user_id=test_user.id,
                movie_id=movie.id,
                score=RatingScore(4.0),
                timestamp=Timestamp.now()
            )
            await rating_repo.save(rating)
        
        # Busca todos os ratings do usuário
        user_ratings = await rating_repo.find_by_user(test_user.id)
        
        # Verifica
        assert len(user_ratings) == 3
        assert all(r.user_id == test_user.id for r in user_ratings)
    
    async def test_find_ratings_by_movie(self, rating_repo, user_repo, test_movie):
        """Testa busca de todos os ratings de um filme"""
        # Cria múltiplos usuários
        users = []
        for i in range(3):
            user = User(
                id=UserId(200 + i),
                created_at=Timestamp.now()
            )
            saved_user = await user_repo.save(user)
            users.append(saved_user)
        
        # Cria ratings de cada usuário
        for user in users:
            rating = Rating(
                user_id=user.id,
                movie_id=test_movie.id,
                score=RatingScore(4.5),
                timestamp=Timestamp.now()
            )
            await rating_repo.save(rating)
        
        # Busca todos os ratings do filme
        movie_ratings = await rating_repo.find_by_movie(test_movie.id)
        
        # Verifica
        assert len(movie_ratings) == 3
        assert all(r.movie_id == test_movie.id for r in movie_ratings)
    
    async def test_rating_count(self, rating_repo, test_user, test_movie):
        """Testa contagem de ratings"""
        # Inicialmente vazio
        count_initial = await rating_repo.count()
        
        # Adiciona rating
        rating = Rating(
            user_id=test_user.id,
            movie_id=test_movie.id,
            score=RatingScore(4.0),
            timestamp=Timestamp.now()
        )
        await rating_repo.save(rating)
        
        # Conta novamente
        count_after = await rating_repo.count()
        
        assert count_after == count_initial + 1