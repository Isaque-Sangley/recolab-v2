"""
Unit Tests: Movie Entity

Testa lógica de negócio da entidade Movie.
"""

import pytest
from src.domain.entities import Movie
from src.domain.value_objects import MovieId


class TestMovieEntity:
    """Testes para Movie entity"""
    
    def test_movie_creation(self):
        """Testa criação básica de filme"""
        movie = Movie(
            id=MovieId(1),
            title="Inception",
            genres=["Action", "Sci-Fi"],
            year=2010,
            rating_count=100,
            avg_rating=4.5
        )
        
        assert movie.id == MovieId(1)
        assert movie.title == "Inception"
        assert movie.genres == ["Action", "Sci-Fi"]
        assert movie.year == 2010
        assert movie.rating_count == 100
        assert movie.avg_rating == 4.5
    
    def test_movie_without_genres_gets_unknown(self):
        """Filme sem gêneros recebe 'Unknown'"""
        movie = Movie(
            id=MovieId(1),
            title="Test Movie",
            genres=[]
        )
        
        assert movie.genres == ["Unknown"]
    
    def test_is_popular_with_many_ratings(self, popular_movie):
        """Filme é popular se tem 50+ ratings"""
        assert popular_movie.is_popular() is True
    
    def test_is_not_popular_with_few_ratings(self, niche_movie):
        """Filme não é popular se tem < 50 ratings"""
        assert niche_movie.is_popular() is False
    
    def test_is_well_rated_high_avg(self):
        """Filme é bem avaliado se avg >= 4.0"""
        movie = Movie(
            id=MovieId(1),
            title="Great Movie",
            genres=["Drama"],
            avg_rating=4.5,
            rating_count=100
        )
        
        assert movie.is_well_rated() is True
    
    def test_is_not_well_rated_low_avg(self):
        """Filme não é bem avaliado se avg < 4.0"""
        movie = Movie(
            id=MovieId(1),
            title="Mediocre Movie",
            genres=["Drama"],
            avg_rating=3.5,
            rating_count=100
        )
        
        assert movie.is_well_rated() is False
    
    def test_add_rating_updates_stats(self):
        """Adicionar rating atualiza estatísticas"""
        movie = Movie(
            id=MovieId(1),
            title="Test Movie",
            genres=["Drama"],
            rating_count=0,
            avg_rating=0.0
        )
        
        # Adiciona primeiro rating
        movie.add_rating(4.5)
        assert movie.rating_count == 1
        assert movie.avg_rating == 4.5
        
        # Adiciona segundo rating
        movie.add_rating(3.5)
        assert movie.rating_count == 2
        assert movie.avg_rating == 4.0  # (4.5 + 3.5) / 2
    
    def test_calculate_popularity_score(self, popular_movie):
        """Testa cálculo de score de popularidade"""
        score = popular_movie.calculate_popularity_score()
        
        # Score deve estar entre 0-10
        assert 0.0 <= score <= 10.0
        
        # Popular + bem avaliado = score alto
        assert score > 8.0
    
    def test_calculate_popularity_score_no_ratings(self):
        """Score é 0 se não tem ratings"""
        movie = Movie(
            id=MovieId(1),
            title="New Movie",
            genres=["Drama"],
            rating_count=0,
            avg_rating=0.0
        )
        
        assert movie.calculate_popularity_score() == 0.0
    
    def test_has_genre(self, sample_movie):
        """Testa verificação de gênero"""
        assert sample_movie.has_genre("Action") is True
        assert sample_movie.has_genre("Sci-Fi") is True
        assert sample_movie.has_genre("Comedy") is False
    
    def test_has_genre_case_insensitive(self, sample_movie):
        """has_genre é case-insensitive"""
        assert sample_movie.has_genre("action") is True
        assert sample_movie.has_genre("ACTION") is True
        assert sample_movie.has_genre("ScI-fI") is True
    
    def test_genre_similarity_identical_genres(self):
        """Similaridade 1.0 para gêneros idênticos"""
        movie = Movie(
            id=MovieId(1),
            title="Test",
            genres=["Action", "Drama"]
        )
        
        similarity = movie.genre_similarity(["Action", "Drama"])
        assert similarity == 1.0
    
    def test_genre_similarity_no_overlap(self):
        """Similaridade 0.0 para gêneros diferentes"""
        movie = Movie(
            id=MovieId(1),
            title="Test",
            genres=["Action", "Drama"]
        )
        
        similarity = movie.genre_similarity(["Comedy", "Horror"])
        assert similarity == 0.0
    
    def test_genre_similarity_partial_overlap(self):
        """Similaridade parcial para overlap parcial"""
        movie = Movie(
            id=MovieId(1),
            title="Test",
            genres=["Action", "Drama"]
        )
        
        # 1 gênero em comum de 3 total = 1/3 = 0.333
        similarity = movie.genre_similarity(["Action", "Comedy"])
        assert 0.3 <= similarity <= 0.4
    
    def test_get_content_for_tfidf(self, sample_movie):
        """Testa geração de conteúdo para TF-IDF"""
        content = sample_movie.get_content_for_tfidf()
        
        assert "The Matrix" in content
        assert "Action" in content
        assert "Sci-Fi" in content
    
    def test_movie_equality_by_id(self):
        """Filmes são iguais se têm mesmo ID"""
        movie1 = Movie(id=MovieId(1), title="Test", genres=["Drama"])
        movie2 = Movie(id=MovieId(1), title="Different Title", genres=["Comedy"])
        movie3 = Movie(id=MovieId(2), title="Test", genres=["Drama"])
        
        assert movie1 == movie2  # Mesmo ID
        assert movie1 != movie3  # IDs diferentes
    
    def test_invalid_empty_title(self):
        """Título não pode ser vazio"""
        with pytest.raises(ValueError, match="Title cannot be empty"):
            Movie(
                id=MovieId(1),
                title="",
                genres=["Drama"]
            )
    
    def test_invalid_negative_rating_count(self):
        """rating_count não pode ser negativo"""
        with pytest.raises(ValueError, match="rating_count cannot be negative"):
            Movie(
                id=MovieId(1),
                title="Test",
                genres=["Drama"],
                rating_count=-1
            )
    
    def test_invalid_avg_rating_too_high(self):
        """avg_rating não pode ser > 5.0"""
        with pytest.raises(ValueError, match="avg_rating must be 0-5"):
            Movie(
                id=MovieId(1),
                title="Test",
                genres=["Drama"],
                avg_rating=6.0
            )
    
    def test_invalid_avg_rating_negative(self):
        """avg_rating não pode ser negativo"""
        with pytest.raises(ValueError, match="avg_rating must be 0-5"):
            Movie(
                id=MovieId(1),
                title="Test",
                genres=["Drama"],
                avg_rating=-1.0
            )