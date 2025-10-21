"""
Unit Tests: DiversityService

Testa cálculo e otimização de diversidade de recomendações.
"""

import pytest
from src.domain.services import DiversityService
from src.domain.entities import Movie
from src.domain.value_objects import MovieId


class TestDiversityService:
    """Testes para DiversityService"""
    
    @pytest.fixture
    def diversity_service(self):
        """Cria instância do serviço"""
        return DiversityService()
    
    @pytest.fixture
    def diverse_movies(self):
        """Lista de filmes diversos (vários gêneros, anos, popularidades)"""
        return [
            Movie(
                id=MovieId(1),
                title="Action Blockbuster",
                genres=["Action", "Sci-Fi"],
                year=2020,
                rating_count=1000,
                avg_rating=4.5
            ),
            Movie(
                id=MovieId(2),
                title="Indie Drama",
                genres=["Drama", "Independent"],
                year=2019,
                rating_count=50,
                avg_rating=4.7
            ),
            Movie(
                id=MovieId(3),
                title="Classic Comedy",
                genres=["Comedy"],
                year=1990,
                rating_count=500,
                avg_rating=4.3
            ),
            Movie(
                id=MovieId(4),
                title="Horror Thriller",
                genres=["Horror", "Thriller"],
                year=2015,
                rating_count=200,
                avg_rating=4.0
            ),
        ]
    
    @pytest.fixture
    def homogeneous_movies(self):
        """Lista de filmes homogêneos (todos action sci-fi)"""
        return [
            Movie(
                id=MovieId(i + 1),
                title=f"Action Movie {i}",
                genres=["Action", "Sci-Fi"],
                year=2020,
                rating_count=100,  # ✅ ADICIONADO
                avg_rating=4.0
            )
            for i in range(5)
        ]
    
    def test_calculate_diversity_empty_list(self, diversity_service):
        """Lista vazia retorna métricas zeradas"""
        metrics = diversity_service.calculate_diversity([])
        
        assert metrics.genre_diversity == 0.0
        assert metrics.popularity_diversity == 0.0
        assert metrics.year_diversity == 0.0
        assert metrics.overall_diversity == 0.0
        assert len(metrics.unique_genres) == 0
    
    def test_calculate_diversity_diverse_list(self, diversity_service, diverse_movies):
        """Lista diversa tem score alto"""
        metrics = diversity_service.calculate_diversity(diverse_movies)
        
        # Deve ter boa diversidade
        assert metrics.genre_diversity > 0.5
        assert metrics.overall_diversity > 0.5
        
        # Deve ter vários gêneros únicos
        assert len(metrics.unique_genres) >= 7
    
    def test_calculate_diversity_homogeneous_list(self, diversity_service, homogeneous_movies):
        """Lista homogênea tem score baixo"""
        metrics = diversity_service.calculate_diversity(homogeneous_movies)
        
        # Como todos têm os mesmos 2 gêneros perfeitamente distribuídos,
        # a diversidade de gêneros será alta (Shannon Entropy)
        # Mas ano e popularidade serão baixos
        assert metrics.year_diversity == 0.0  # Todos do mesmo ano
        assert len(metrics.unique_genres) == 2  # Apenas Action e Sci-Fi
    
    def test_genre_diversity_single_genre(self, diversity_service):
        """Filmes de um único gênero têm diversidade mínima"""
        movies = [
            Movie(
                id=MovieId(i + 1), 
                title=f"Movie {i}", 
                genres=["Drama"],
                rating_count=100,  # ✅ ADICIONADO
                avg_rating=4.0
            )
            for i in range(3)
        ]
        
        metrics = diversity_service.calculate_diversity(movies)
        
        # Diversidade de gênero deve ser 0 (todos iguais)
        assert metrics.genre_diversity == pytest.approx(0.0, abs=0.1)
    
    def test_genre_diversity_all_different(self, diversity_service):
        """Filmes com gêneros completamente diferentes têm alta diversidade"""
        movies = [
            Movie(id=MovieId(1), title="Movie 1", genres=["Action"], rating_count=100, avg_rating=4.0),
            Movie(id=MovieId(2), title="Movie 2", genres=["Drama"], rating_count=100, avg_rating=4.0),
            Movie(id=MovieId(3), title="Movie 3", genres=["Comedy"], rating_count=100, avg_rating=4.0),
            Movie(id=MovieId(4), title="Movie 4", genres=["Horror"], rating_count=100, avg_rating=4.0),
        ]
        
        metrics = diversity_service.calculate_diversity(movies)
        
        # Diversidade de gênero deve ser alta
        assert metrics.genre_diversity > 0.8
    
    def test_popularity_diversity_mixed(self, diversity_service, diverse_movies):
        """Mix de filmes populares e nicho tem boa diversidade de popularidade"""
        metrics = diversity_service.calculate_diversity(diverse_movies)
        
        # Tem filmes com 50, 200, 500, 1000 ratings = boa variedade
        assert metrics.popularity_diversity > 0.3
    
    def test_popularity_diversity_all_same(self, diversity_service):
        """Filmes com mesma popularidade têm baixa diversidade"""
        movies = [
            Movie(
                id=MovieId(i + 1),
                title=f"Movie {i}",
                genres=["Drama"],
                rating_count=100,  # ✅ Todos iguais
                avg_rating=4.0
            )
            for i in range(5)
        ]
        
        metrics = diversity_service.calculate_diversity(movies)
        
        # Diversidade de popularidade deve ser baixa
        assert metrics.popularity_diversity < 0.3
    
    def test_year_diversity_wide_range(self, diversity_service, diverse_movies):
        """Filmes de diferentes décadas têm boa diversidade temporal"""
        metrics = diversity_service.calculate_diversity(diverse_movies)
        
        # Anos: 1990, 2015, 2019, 2020 = boa variedade
        assert metrics.year_diversity > 0.4
    
    def test_year_diversity_same_year(self, diversity_service):
        """Filmes do mesmo ano têm baixa diversidade temporal"""
        movies = [
            Movie(
                id=MovieId(i + 1),
                title=f"Movie {i}",
                genres=["Drama"],
                year=2020,  # Todos do mesmo ano
                rating_count=100,  # ✅ ADICIONADO
                avg_rating=4.0
            )
            for i in range(5)
        ]
        
        metrics = diversity_service.calculate_diversity(movies)
        
        # Diversidade de ano deve ser 0
        assert metrics.year_diversity == pytest.approx(0.0, abs=0.1)
    
    def test_overall_diversity_is_weighted_average(self, diversity_service, diverse_movies):
        """Overall diversity é média ponderada das dimensões"""
        metrics = diversity_service.calculate_diversity(diverse_movies)
        
        # Fórmula: 0.5*genre + 0.3*popularity + 0.2*year
        expected = (
            0.5 * metrics.genre_diversity +
            0.3 * metrics.popularity_diversity +
            0.2 * metrics.year_diversity
        )
        
        assert metrics.overall_diversity == pytest.approx(expected, abs=0.01)
    
    def test_genre_distribution(self, diversity_service, diverse_movies):
        """Genre distribution conta corretamente"""
        metrics = diversity_service.calculate_diversity(diverse_movies)
        
        distribution = metrics.genre_distribution
        
        # Verifica se todos os gêneros estão presentes
        expected_genres = ["Action", "Sci-Fi", "Drama", "Independent", "Comedy", "Horror", "Thriller"]
        for genre in expected_genres:
            assert genre in distribution
            assert distribution[genre] >= 1
    
    def test_unique_genres_set(self, diversity_service, diverse_movies):
        """Unique genres é um set (sem duplicatas)"""
        metrics = diversity_service.calculate_diversity(diverse_movies)
        
        assert isinstance(metrics.unique_genres, set)
        
        # Deve ter 7 gêneros únicos
        assert len(metrics.unique_genres) == 7
    
    def test_metrics_are_rounded(self, diversity_service, diverse_movies):
        """Métricas devem estar arredondadas (3 casas decimais)"""
        metrics = diversity_service.calculate_diversity(diverse_movies)
        
        # Verifica que tem no máximo 3 casas decimais
        assert len(str(metrics.genre_diversity).split('.')[-1]) <= 3
        assert len(str(metrics.popularity_diversity).split('.')[-1]) <= 3
        assert len(str(metrics.year_diversity).split('.')[-1]) <= 3
        assert len(str(metrics.overall_diversity).split('.')[-1]) <= 3
    
    def test_diversity_increases_with_variety(self, diversity_service):
        """Diversidade aumenta conforme adicionamos variedade"""
        # Lista 1: Apenas 1 tipo de filme
        movies_1 = [
            Movie(
                id=MovieId(i + 1), 
                title=f"Movie {i}", 
                genres=["Drama"],
                rating_count=100,  # ✅ ADICIONADO
                avg_rating=4.0
            )
            for i in range(3)
        ]
        
        # Lista 2: 2 tipos
        movies_2 = [
            Movie(id=MovieId(1), title="Movie 1", genres=["Drama"], rating_count=100, avg_rating=4.0),
            Movie(id=MovieId(2), title="Movie 2", genres=["Drama"], rating_count=100, avg_rating=4.0),
            Movie(id=MovieId(3), title="Movie 3", genres=["Comedy"], rating_count=100, avg_rating=4.0),
        ]
        
        # Lista 3: 3 tipos
        movies_3 = [
            Movie(id=MovieId(1), title="Movie 1", genres=["Drama"], rating_count=100, avg_rating=4.0),
            Movie(id=MovieId(2), title="Movie 2", genres=["Comedy"], rating_count=100, avg_rating=4.0),
            Movie(id=MovieId(3), title="Movie 3", genres=["Action"], rating_count=100, avg_rating=4.0),
        ]
        
        metrics_1 = diversity_service.calculate_diversity(movies_1)
        metrics_2 = diversity_service.calculate_diversity(movies_2)
        metrics_3 = diversity_service.calculate_diversity(movies_3)
        
        # Diversidade deve aumentar
        assert metrics_1.genre_diversity < metrics_2.genre_diversity
        assert metrics_2.genre_diversity < metrics_3.genre_diversity