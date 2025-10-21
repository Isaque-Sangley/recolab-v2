# RecoLab v2 - Arquitetura de Software

## Índice

1. [Visão Geral](#visão-geral)
2. [Princípios Arquiteturais](#princípios-arquiteturais)
3. [Estrutura de Camadas](#estrutura-de-camadas)
4. [Domain Layer](#domain-layer)
5. [Application Layer](#application-layer)
6. [Infrastructure Layer](#infrastructure-layer)
7. [Presentation Layer](#presentation-layer)
8. [Fluxos Principais](#fluxos-principais)
9. [Padrões de Design](#padrões-de-design)
10. [Decisões Técnicas](#decisões-técnicas)
11. [Segurança](#segurança)
12. [Performance e Escalabilidade](#performance-e-escalabilidade)
13. [Monitoramento e Observabilidade](#monitoramento-e-observabilidade)

---

## Visão Geral

O RecoLab v2 é um sistema de recomendação de filmes construído seguindo os princípios de **Clean Architecture** e **Domain-Driven Design (DDD)**. A arquitetura prioriza separação de responsabilidades, testabilidade e independência de frameworks e tecnologias externas.

### Objetivos Arquiteturais

1. **Testabilidade**: Camada de domínio 100% testável sem dependências externas
2. **Manutenibilidade**: Mudanças em infraestrutura não afetam regras de negócio
3. **Escalabilidade**: Sistema preparado para crescimento horizontal e vertical
4. **Flexibilidade**: Fácil troca de componentes de infraestrutura (banco, cache, ML models)
5. **Independência**: Lógica de negócio independente de frameworks (FastAPI, PostgreSQL, Redis)

### Arquitetura de Alto Nível
```
┌─────────────────────────────────────────────────────────────────┐
│                       EXTERNAL SYSTEMS                           │
│                  (Client Apps, Admin Panel)                      │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             │ HTTP/REST
                             │
┌────────────────────────────▼────────────────────────────────────┐
│                     PRESENTATION LAYER                           │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │   FastAPI    │  │   Schemas    │  │    Error     │          │
│  │   Routes     │  │   (Pydantic) │  │   Handlers   │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             │ DTOs
                             │
┌────────────────────────────▼────────────────────────────────────┐
│                    APPLICATION LAYER                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │  Use Cases   │  │   Commands   │  │    Queries   │          │
│  │  Services    │  │   (Write)    │  │    (Read)    │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             │ Domain Entities
                             │
┌────────────────────────────▼────────────────────────────────────┐
│                       DOMAIN LAYER                               │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │   Entities   │  │    Value     │  │   Domain     │          │
│  │ User, Movie  │  │   Objects    │  │   Services   │          │
│  │Rating, Rec.  │  │  UserId, etc │  │  Strategy    │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
│  ┌──────────────┐  ┌──────────────┐                            │
│  │ Repository   │  │   Domain     │                            │
│  │ Interfaces   │  │   Events     │                            │
│  └──────────────┘  └──────────────┘                            │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             │ Interfaces
                             │
┌────────────────────────────▼────────────────────────────────────┐
│                  INFRASTRUCTURE LAYER                            │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │  PostgreSQL  │  │     Redis    │  │  ML Models   │          │
│  │ Repositories │  │     Cache    │  │   (PyTorch)  │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
│  ┌──────────────┐  ┌──────────────┐                            │
│  │   ORM/SQL    │  │  External    │                            │
│  │  Alchemy     │  │   Services   │                            │
│  └──────────────┘  └──────────────┘                            │
└─────────────────────────────────────────────────────────────────┘
```

---

## Princípios Arquiteturais

### 1. Dependency Rule

A regra fundamental da Clean Architecture: **dependências apontam para dentro**.
```
Presentation → Application → Domain
Infrastructure → Domain (via interfaces)
```

**Nunca**:
- Domain depende de Application
- Domain depende de Infrastructure
- Application depende de Infrastructure diretamente

### 2. Separation of Concerns

Cada camada tem responsabilidades bem definidas:

- **Domain**: Regras de negócio, lógica essencial
- **Application**: Orquestração, casos de uso
- **Infrastructure**: Detalhes técnicos, persistência, I/O
- **Presentation**: Interface com usuário, HTTP, serialização

### 3. Inversion of Control

Domain define interfaces, Infrastructure as implementa:
```python
# Domain layer define
class IUserRepository(ABC):
    @abstractmethod
    async def find_by_id(self, user_id: UserId) -> Optional[User]:
        pass

# Infrastructure implementa
class UserRepository(IUserRepository):
    async def find_by_id(self, user_id: UserId) -> Optional[User]:
        # PostgreSQL implementation
        ...
```

### 4. Single Responsibility Principle

Cada componente tem uma única razão para mudar:

- **Entity**: Muda apenas se regras de negócio mudarem
- **Repository**: Muda apenas se tecnologia de persistência mudar
- **Use Case**: Muda apenas se fluxo de aplicação mudar

### 5. Open/Closed Principle

Componentes abertos para extensão, fechados para modificação:
```python
# Adicionar nova estratégia não requer modificar código existente
class NewMLStrategy(IRecommendationStrategy):
    async def recommend(self, user: User, n: int) -> List[Recommendation]:
        # Nova implementação
        ...

# Registrar estratégia
strategy_factory.register("new_ml", NewMLStrategy)
```

---

## Estrutura de Camadas

### Organização de Diretórios
```
backend/
├── src/
│   ├── domain/                      # Domain Layer (core business logic)
│   │   ├── entities/                # Entidades de negócio
│   │   │   ├── user.py
│   │   │   ├── movie.py
│   │   │   ├── rating.py
│   │   │   └── recommendation.py
│   │   ├── value_objects/           # Objetos de valor imutáveis
│   │   │   ├── user_id.py
│   │   │   ├── movie_id.py
│   │   │   ├── rating_score.py
│   │   │   └── timestamp.py
│   │   ├── services/                # Domain services (lógica complexa)
│   │   │   ├── recommendation_strategy_service.py
│   │   │   ├── diversity_service.py
│   │   │   └── user_profile_service.py
│   │   ├── repositories/            # Interfaces de repositórios
│   │   │   ├── user_repository.py
│   │   │   ├── movie_repository.py
│   │   │   ├── rating_repository.py
│   │   │   └── recommendation_repository.py
│   │   └── events/                  # Domain events
│   │       ├── rating_events.py
│   │       ├── recommendation_events.py
│   │       └── event_bus.py
│   │
│   ├── application/                 # Application Layer (use cases)
│   │   ├── services/                # Application services
│   │   │   ├── user_service.py
│   │   │   ├── movie_service.py
│   │   │   ├── rating_service.py
│   │   │   └── recommendation_service.py
│   │   ├── commands/                # Write operations (CQRS)
│   │   │   └── rating_commands.py
│   │   ├── queries/                 # Read operations (CQRS)
│   │   │   ├── user_queries.py
│   │   │   ├── movie_queries.py
│   │   │   └── recommendation_queries.py
│   │   └── dtos/                    # Data Transfer Objects
│   │       ├── user_dtos.py
│   │       ├── movie_dtos.py
│   │       ├── rating_dtos.py
│   │       └── recommendation_dtos.py
│   │
│   ├── infrastructure/              # Infrastructure Layer (technical details)
│   │   ├── database/                # Database configuration
│   │   │   ├── config.py
│   │   │   ├── models.py            # SQLAlchemy ORM models
│   │   │   └── mappers.py           # ORM ↔ Domain mapping
│   │   ├── persistence/             # Repository implementations
│   │   │   ├── user_repository.py
│   │   │   ├── movie_repository.py
│   │   │   ├── rating_repository.py
│   │   │   └── recommendation_repository.py
│   │   └── ml/                      # Machine Learning infrastructure
│   │       ├── models/              # PyTorch models
│   │       │   ├── neural_cf.py
│   │       │   └── base.py
│   │       ├── training/            # Training pipeline
│   │       │   └── model_trainer.py
│   │       ├── serving/             # Model serving
│   │       │   └── model_server.py
│   │       ├── features/            # Feature engineering
│   │       │   └── feature_store.py
│   │       └── registry/            # Model versioning
│   │           └── model_registry.py
│   │
│   └── presentation/                # Presentation Layer (HTTP API)
│       ├── main.py                  # FastAPI app
│       ├── config.py                # Application config
│       ├── dependencies.py          # Dependency injection
│       ├── error_handlers.py        # Global error handling
│       └── routers/                 # API routes
│           ├── users.py
│           ├── movies.py
│           ├── ratings.py
│           └── recommendations.py
│
├── tests/                           # Test suite
│   ├── unit/                        # Unit tests (domain + services)
│   └── integration/                 # Integration tests (API + DB)
│
└── scripts/                         # Utility scripts
    ├── init_db.py
    ├── load_movielens.py
    └── train_model.py
```

---

## Domain Layer

### Responsabilidades

- Definir regras de negócio fundamentais
- Modelar conceitos do domínio (User, Movie, Rating)
- Encapsular lógica de negócio complexa em Domain Services
- Definir contratos (interfaces) para dependências externas
- Publicar Domain Events quando mudanças importantes ocorrem

### Entities

Entidades são objetos com identidade única e ciclo de vida.

#### User Entity
```python
from dataclasses import dataclass
from typing import List, Optional
from enum import Enum

class UserClassification(Enum):
    """Classificação baseada em número de ratings"""
    COLD_START = "cold_start"      # 0 ratings
    NEW = "new"                     # 1-5 ratings
    CASUAL = "casual"               # 6-20 ratings
    ACTIVE = "active"               # 21-100 ratings
    POWER_USER = "power_user"       # 100+ ratings

@dataclass
class User:
    """
    Aggregate Root: User
    
    Representa um usuário do sistema com seu histórico de avaliações.
    """
    id: UserId
    created_at: Timestamp
    n_ratings: int = 0
    avg_rating: float = 0.0
    last_activity: Optional[Timestamp] = None
    favorite_genres: List[str] = None
    
    def __post_init__(self):
        if self.favorite_genres is None:
            self.favorite_genres = []
        self._validate()
    
    def _validate(self):
        """Invariantes de negócio"""
        if self.n_ratings < 0:
            raise ValueError("n_ratings cannot be negative")
        if not (0.0 <= self.avg_rating <= 5.0):
            raise ValueError("avg_rating must be between 0 and 5")
    
    def classify(self) -> UserClassification:
        """
        Business rule: Classifica usuário baseado em atividade.
        
        Esta classificação determina qual estratégia de recomendação usar.
        """
        if self.n_ratings == 0:
            return UserClassification.COLD_START
        elif self.n_ratings <= 5:
            return UserClassification.NEW
        elif self.n_ratings <= 20:
            return UserClassification.CASUAL
        elif self.n_ratings <= 100:
            return UserClassification.ACTIVE
        else:
            return UserClassification.POWER_USER
    
    def record_rating(self, score: RatingScore) -> None:
        """
        Business logic: Atualiza estatísticas quando usuário avalia filme.
        """
        # Recalcula média incremental (evita somar todos ratings novamente)
        total = self.avg_rating * self.n_ratings
        self.n_ratings += 1
        self.avg_rating = (total + float(score)) / self.n_ratings
        self.last_activity = Timestamp.now()
    
    def get_cf_weight(self) -> float:
        """
        Business rule: Peso de Collaborative Filtering baseado em histórico.
        
        Mais ratings = mais confiança em CF.
        """
        return min(1.0, self.n_ratings / 50.0)
    
    def get_cb_weight(self) -> float:
        """Business rule: Peso de Content-Based (complemento de CF)"""
        return 1.0 - self.get_cf_weight()
```

#### Movie Entity
```python
@dataclass
class Movie:
    """
    Aggregate Root: Movie
    
    Representa um filme com suas características e estatísticas.
    """
    id: MovieId
    title: str
    genres: List[str]
    year: Optional[int] = None
    rating_count: int = 0
    avg_rating: float = 0.0
    
    def __post_init__(self):
        if not self.genres:
            self.genres = ["Unknown"]
        self._validate()
    
    def _validate(self):
        """Invariantes"""
        if not self.title or self.title.strip() == "":
            raise ValueError("title cannot be empty")
        if self.rating_count < 0:
            raise ValueError("rating_count cannot be negative")
        if not (0.0 <= self.avg_rating <= 5.0):
            raise ValueError("avg_rating must be between 0 and 5")
    
    def is_popular(self, threshold: int = 100) -> bool:
        """Business rule: Popularidade baseada em número de avaliações"""
        return self.rating_count >= threshold
    
    def is_well_rated(self, threshold: float = 4.0) -> bool:
        """Business rule: Qualidade baseada em média de avaliações"""
        return self.avg_rating >= threshold
    
    def add_rating(self, score: RatingScore) -> None:
        """Business logic: Atualiza estatísticas quando recebe nova avaliação"""
        total = self.avg_rating * self.rating_count
        self.rating_count += 1
        self.avg_rating = (total + float(score)) / self.rating_count
    
    def calculate_popularity_score(self) -> float:
        """
        Business rule: Score de popularidade combinando contagem e qualidade.
        
        Fórmula: log(rating_count + 1) * avg_rating
        """
        import math
        return math.log10(self.rating_count + 1) * self.avg_rating
    
    def has_genre(self, genre: str) -> bool:
        """Verifica se filme pertence a um gênero (case-insensitive)"""
        return genre.lower() in [g.lower() for g in self.genres]
    
    def genre_similarity(self, other_genres: List[str]) -> float:
        """
        Business logic: Similaridade de gêneros (Jaccard similarity).
        
        Usado para Content-Based Filtering.
        """
        if not self.genres or not other_genres:
            return 0.0
        
        set_a = set(g.lower() for g in self.genres)
        set_b = set(g.lower() for g in other_genres)
        
        intersection = len(set_a & set_b)
        union = len(set_a | set_b)
        
        return intersection / union if union > 0 else 0.0
```

#### Rating Entity
```python
@dataclass
class Rating:
    """
    Entity: Rating
    
    Representa avaliação de um usuário sobre um filme.
    Composite key: (user_id, movie_id)
    """
    user_id: UserId
    movie_id: MovieId
    score: RatingScore
    timestamp: Timestamp
    
    def is_positive(self) -> bool:
        """Business rule: Rating positivo >= 4.0"""
        return float(self.score) >= 4.0
    
    def is_negative(self) -> bool:
        """Business rule: Rating negativo <= 2.5"""
        return float(self.score) <= 2.5
    
    def is_recent(self, days: int = 30) -> bool:
        """Business rule: Rating é recente se < N dias"""
        from datetime import timedelta
        cutoff = Timestamp.now() - timedelta(days=days)
        return self.timestamp >= cutoff
    
    def get_normalized_score(self) -> float:
        """Normaliza score [0.5, 5.0] para [0, 1]"""
        return (float(self.score) - 0.5) / 4.5
    
    def to_interaction_tuple(self) -> tuple:
        """Formato para ML model: (user_id, movie_id, score)"""
        return (int(self.user_id), int(self.movie_id), float(self.score))
```

### Value Objects

Objetos imutáveis sem identidade, definidos apenas por seus valores.
```python
@dataclass(frozen=True)
class UserId:
    """Value Object: User ID"""
    value: int
    
    def __post_init__(self):
        if self.value <= 0:
            raise ValueError("UserId must be positive")
    
    def __int__(self):
        return self.value
    
    def __str__(self):
        return f"User#{self.value}"

@dataclass(frozen=True)
class RatingScore:
    """
    Value Object: Rating Score
    
    Business rule: Ratings são em incrementos de 0.5 entre 0.5 e 5.0
    """
    value: float
    
    def __post_init__(self):
        if not (0.5 <= self.value <= 5.0):
            raise ValueError("RatingScore must be between 0.5 and 5.0")
        if (self.value * 2) % 1 != 0:
            raise ValueError("RatingScore must be in 0.5 increments")
    
    def __float__(self):
        return self.value
    
    def is_positive(self) -> bool:
        return self.value >= 4.0
    
    def normalize(self) -> float:
        """Normaliza para [0, 1]"""
        return (self.value - 0.5) / 4.5
```

### Domain Services

Lógica de negócio que não pertence naturalmente a uma entidade.

#### RecommendationStrategyService
```python
class RecommendationStrategyService:
    """
    Domain Service: Seleção de Estratégia de Recomendação
    
    Business rule: Estratégia depende da classificação do usuário.
    """
    
    def select_strategy(self, user: User) -> str:
        """
        Determina qual estratégia usar baseado no perfil do usuário.
        
        Returns:
            Nome da estratégia: "popular", "content_based", "collaborative", "hybrid"
        """
        classification = user.classify()
        
        if classification == UserClassification.COLD_START:
            return "popular"
        
        elif classification == UserClassification.NEW:
            return "content_based"
        
        elif classification in [UserClassification.CASUAL, UserClassification.ACTIVE]:
            return "hybrid"
        
        else:  # POWER_USER
            return "collaborative_with_diversity"
    
    def get_strategy_weights(self, user: User) -> dict:
        """
        Business rule: Pesos das estratégias no modo híbrido.
        
        Returns:
            {"collaborative": 0.6, "content_based": 0.4}
        """
        classification = user.classify()
        
        if classification == UserClassification.CASUAL:
            return {"collaborative": 0.6, "content_based": 0.4}
        
        elif classification == UserClassification.ACTIVE:
            return {"collaborative": 0.8, "content_based": 0.2}
        
        elif classification == UserClassification.POWER_USER:
            return {"collaborative": 0.7, "diversity": 0.3}
        
        return {"content_based": 1.0}
```

#### DiversityService
```python
class DiversityService:
    """
    Domain Service: Otimização de Diversidade
    
    Business rule: Power users precisam de diversidade para evitar filter bubble.
    """
    
    def calculate_diversity(self, movies: List[Movie]) -> float:
        """
        Calcula score de diversidade de uma lista de filmes.
        
        Considera:
        - Diversidade de gêneros (Shannon entropy)
        - Diversidade de popularidade (desvio padrão)
        - Diversidade temporal (range de anos)
        
        Returns:
            Score [0, 1] onde 1 = máxima diversidade
        """
        if not movies:
            return 0.0
        
        # Diversidade de gêneros
        all_genres = []
        for movie in movies:
            all_genres.extend(movie.genres)
        
        genre_diversity = self._calculate_shannon_entropy(all_genres)
        
        # Diversidade de popularidade
        popularity_scores = [m.calculate_popularity_score() for m in movies]
        popularity_diversity = self._calculate_std_normalized(popularity_scores)
        
        # Diversidade temporal
        years = [m.year for m in movies if m.year]
        year_diversity = self._calculate_range_normalized(years)
        
        # Média ponderada
        return 0.5 * genre_diversity + 0.3 * popularity_diversity + 0.2 * year_diversity
    
    def rerank_for_diversity(
        self,
        recommendations: List[Recommendation],
        movies: List[Movie],
        lambda_param: float = 0.7
    ) -> List[Recommendation]:
        """
        Re-ranqueia recomendações usando MMR (Maximal Marginal Relevance).
        
        Business rule: Balanceia relevância vs diversidade.
        
        Args:
            lambda_param: Peso da relevância (0.7 = 70% relevância, 30% diversidade)
        """
        # Implementação do algoritmo MMR
        # ...
```

### Repository Interfaces

Domain define contratos, Infrastructure implementa.
```python
from abc import ABC, abstractmethod
from typing import List, Optional

class IUserRepository(ABC):
    """Interface: User Repository (definida no Domain)"""
    
    @abstractmethod
    async def save(self, user: User) -> User:
        """Persiste ou atualiza usuário"""
        pass
    
    @abstractmethod
    async def find_by_id(self, user_id: UserId) -> Optional[User]:
        """Busca usuário por ID"""
        pass
    
    @abstractmethod
    async def find_power_users(self, limit: int) -> List[User]:
        """Busca usuários com mais de 100 ratings"""
        pass
    
    @abstractmethod
    async def count(self) -> int:
        """Conta total de usuários"""
        pass

class IMovieRepository(ABC):
    """Interface: Movie Repository"""
    
    @abstractmethod
    async def find_by_id(self, movie_id: MovieId) -> Optional[Movie]:
        pass
    
    @abstractmethod
    async def find_by_genres(self, genres: List[str], limit: int) -> List[Movie]:
        """Busca filmes que contêm qualquer um dos gêneros"""
        pass
    
    @abstractmethod
    async def find_popular(self, min_rating_count: int, limit: int) -> List[Movie]:
        """Busca filmes populares ordenados por rating_count"""
        pass
    
    @abstractmethod
    async def find_well_rated(self, min_avg_rating: float, limit: int) -> List[Movie]:
        """Busca filmes bem avaliados"""
        pass
```

### Domain Events

Comunicação entre agregados sem acoplamento direto.
```python
from dataclasses import dataclass
from datetime import datetime

@dataclass
class DomainEvent:
    """Base class para domain events"""
    occurred_at: datetime
    event_id: str
    aggregate_id: str

@dataclass
class RatingCreatedEvent(DomainEvent):
    """Event: Rating foi criado"""
    user_id: UserId
    movie_id: MovieId
    score: RatingScore
    
    def __post_init__(self):
        if not self.occurred_at:
            self.occurred_at = datetime.now()

@dataclass
class RecommendationGeneratedEvent(DomainEvent):
    """Event: Recomendações foram geradas"""
    user_id: UserId
    strategy_used: str
    n_recommendations: int
    diversity_score: float

# Event Bus para pub/sub
class EventBus:
    """Simple in-memory event bus"""
    
    def __init__(self):
        self._handlers = {}
    
    def subscribe(self, event_type: type, handler: callable):
        """Registra handler para um tipo de evento"""
        if event_type not in self._handlers:
            self._handlers[event_type] = []
        self._handlers[event_type].append(handler)
    
    async def publish(self, event: DomainEvent):
        """Publica evento para todos os handlers registrados"""
        event_type = type(event)
        if event_type in self._handlers:
            for handler in self._handlers[event_type]:
                await handler(event)
```

---

## Application Layer

### Responsabilidades

- Orquestrar casos de uso (use cases)
- Coordenar operações entre múltiplos agregados
- Gerenciar transações
- Converter entre Domain entities e DTOs
- Implementar CQRS (Commands/Queries)

### Application Services

#### RecommendationService
```python
class RecommendationService:
    """
    Application Service: Orquestra geração de recomendações
    
    Coordena:
    - Domain Services (strategy selection, diversity)
    - Repositories (user, movie, rating)
    - Infrastructure (ML models, cache)
    """
    
    def __init__(
        self,
        user_repo: IUserRepository,
        movie_repo: IMovieRepository,
        rating_repo: IRatingRepository,
        strategy_service: RecommendationStrategyService,
        diversity_service: DiversityService,
        model_server: ModelServer,
        cache: CacheService,
        event_bus: EventBus
    ):
        self.user_repo = user_repo
        self.movie_repo = movie_repo
        self.rating_repo = rating_repo
        self.strategy_service = strategy_service
        self.diversity_service = diversity_service
        self.model_server = model_server
        self.cache = cache
        self.event_bus = event_bus
    
    async def generate_recommendations(
        self,
        user_id: UserId,
        n_recommendations: int = 10,
        force_refresh: bool = False
    ) -> RecommendationResult:
        """
        Use Case: Gerar Recomendações
        
        Fluxo:
        1. Buscar usuário
        2. Verificar cache (se não force_refresh)
        3. Selecionar estratégia baseado no perfil
        4. Gerar recomendações usando estratégia
        5. Aplicar diversidade se necessário
        6. Salvar em cache
        7. Publicar evento
        8. Retornar resultado
        """
        # 1. Buscar usuário
        user = await self.user_repo.find_by_id(user_id)
        if not user:
            raise UserNotFoundError(f"User {user_id} not found")
        
        # 2. Verificar cache
        if not force_refresh:
            cached = await self._get_from_cache(user_id, n_recommendations)
            if cached:
                return cached
        
        # 3. Selecionar estratégia
        strategy_name = self.strategy_service.select_strategy(user)
        
        # 4. Gerar recomendações
        if strategy_name == "popular":
            recommendations = await self._generate_popular(user, n_recommendations)
        
        elif strategy_name == "content_based":
            recommendations = await self._generate_content_based(user, n_recommendations)
        
        elif strategy_name == "collaborative":
            recommendations = await self._generate_collaborative(user, n_recommendations)
        
        elif strategy_name == "hybrid":
            recommendations = await self._generate_hybrid(user, n_recommendations)
        
        else:  # collaborative_with_diversity
            recommendations = await self._generate_with_diversity(user, n_recommendations)
        
        # 5. Aplicar diversidade se power user
        if user.classify() == UserClassification.POWER_USER:
            movies = await self._fetch_movies([r.movie_id for r in recommendations])
            recommendations = self.diversity_service.rerank_for_diversity(
                recommendations, movies, lambda_param=0.7
            )
        
        # 6. Preparar resultado
        result = RecommendationResult(
            user_id=user_id,
            recommendations=recommendations,
            strategy_used=strategy_name,
            diversity_score=self.diversity_service.calculate_diversity(movies)
        )
        
        # 7. Salvar em cache
        await self._save_to_cache(result)
        
        # 8. Publicar evento
        await self.event_bus.publish(RecommendationGeneratedEvent(
            user_id=user_id,
            strategy_used=strategy_name,
            n_recommendations=len(recommendations),
            diversity_score=result.diversity_score,
            occurred_at=datetime.now()
        ))
        
        return result
    
    async def _generate_collaborative(self, user: User, n: int) -> List[Recommendation]:
        """Gera recomendações usando Neural CF model"""
        # Buscar histórico do usuário
        user_ratings = await self.rating_repo.find_by_user(user.id)
        
        # Buscar todos os filmes
        all_movies = await self.movie_repo.find_all()
        
        # Filtrar filmes já avaliados
        rated_movie_ids = {r.movie_id for r in user_ratings}
        candidate_movies = [m for m in all_movies if m.id not in rated_movie_ids]
        
        # Predição do modelo
        predictions = await self.model_server.predict(
            user_id=int(user.id),
            movie_ids=[int(m.id) for m in candidate_movies]
        )
        
        # Ordenar por score e pegar top N
        sorted_predictions = sorted(predictions, key=lambda x: x['score'], reverse=True)
        top_n = sorted_predictions[:n]
        
        # Converter para Recommendation entities
        recommendations = [
            Recommendation(
                user_id=user.id,
                movie_id=MovieId(pred['movie_id']),
                score=RecommendationScore(pred['score']),
                source="collaborative",
                rank=idx + 1,
                timestamp=Timestamp.now(),
                explanation="Based on your viewing history and similar users"
            )
            for idx, pred in enumerate(top_n)
        ]
        
        return recommendations
```

### Commands (Write Operations)
```python
@dataclass
class CreateRatingCommand:
    """Command: Criar avaliação de filme"""
    user_id: int
    movie_id: int
    score: float

class CreateRatingHandler:
    """Handler para CreateRatingCommand"""
    
    def __init__(
        self,
        user_repo: IUserRepository,
        movie_repo: IMovieRepository,
        rating_repo: IRatingRepository,
        event_bus: EventBus
    ):
        self.user_repo = user_repo
        self.movie_repo = movie_repo
        self.rating_repo = rating_repo
        self.event_bus = event_bus
    
    async def handle(self, command: CreateRatingCommand) -> Rating:
        """
        Use Case: Criar Rating
        
        Fluxo:
        1. Validar user e movie existem
        2. Criar Rating entity
        3. Atualizar estatísticas de User e Movie
        4. Persistir tudo em transação
        5. Publicar RatingCreatedEvent
        """
        # 1. Validar
        user = await self.user_repo.find_by_id(UserId(command.user_id))
        if not user:
            raise UserNotFoundError()
        
        movie = await self.movie_repo.find_by_id(MovieId(command.movie_id))
        if not movie:
            raise MovieNotFoundError()
        
        # 2. Criar Rating entity
        rating = Rating(
            user_id=user.id,
            movie_id=movie.id,
            score=RatingScore(command.score),
            timestamp=Timestamp.now()
        )
        
        # 3. Atualizar estatísticas (business logic nas entities)
        user.record_rating(rating.score)
        movie.add_rating(rating.score)
        
        # 4. Persistir em transação
        async with self.rating_repo.transaction():
            await self.rating_repo.save(rating)
            await self.user_repo.save(user)
            await self.movie_repo.save(movie)
        
        # 5. Publicar evento
        await self.event_bus.publish(RatingCreatedEvent(
            user_id=user.id,
            movie_id=movie.id,
            score=rating.score,
            occurred_at=datetime.now()
        ))
        
        return rating
```

### Queries (Read Operations)
```python
class GetUserProfileQuery:
    """Query: Buscar perfil completo do usuário"""
    user_id: int

class GetUserProfileHandler:
    """Handler para GetUserProfileQuery"""
    
    def __init__(
        self,
        user_repo: IUserRepository,
        rating_repo: IRatingRepository,
        cache: CacheService
    ):
        self.user_repo = user_repo
        self.rating_repo = rating_repo
        self.cache = cache
    
    async def handle(self, query: GetUserProfileQuery) -> UserProfileDTO:
        """
        Use Case: Buscar perfil do usuário
        
        Otimização: Resultado cacheado por 30 minutos
        """
        # Tentar cache
        cache_key = f"user:profile:{query.user_id}"
        cached = await self.cache.get(cache_key)
        if cached:
            return UserProfileDTO.from_dict(cached)
        
        # Buscar do banco
        user = await self.user_repo.find_by_id(UserId(query.user_id))
        if not user:
            raise UserNotFoundError()
        
        # Buscar ratings recentes
        recent_ratings = await self.rating_repo.find_by_user(
            user.id,
            limit=20
        )
        
        # Montar DTO
        profile = UserProfileDTO(
            user_id=int(user.id),
            classification=user.classify().value,
            n_ratings=user.n_ratings,
            avg_rating=user.avg_rating,
            favorite_genres=user.favorite_genres,
            recent_ratings=[
                RatingDTO.from_entity(r) for r in recent_ratings
            ],
            cf_weight=user.get_cf_weight(),
            cb_weight=user.get_cb_weight()
        )
        
        # Salvar em cache
        await self.cache.set(cache_key, profile.to_dict(), ttl=1800)
        
        return profile
```

### DTOs (Data Transfer Objects)
```python
from pydantic import BaseModel, Field
from typing import List, Optional

class UserProfileDTO(BaseModel):
    """DTO: Perfil completo do usuário"""
    user_id: int
    classification: str
    n_ratings: int
    avg_rating: float
    favorite_genres: List[str]
    recent_ratings: List['RatingDTO']
    cf_weight: float
    cb_weight: float

class RecommendationDTO(BaseModel):
    """DTO: Recomendação individual"""
    movie_id: int
    movie_title: str
    movie_genres: List[str]
    score: float = Field(..., ge=0.0, le=1.0)
    rank: int
    source: str
    explanation: str
    
    @classmethod
    def from_entities(
        cls,
        recommendation: Recommendation,
        movie: Movie
    ) -> 'RecommendationDTO':
        return cls(
            movie_id=int(recommendation.movie_id),
            movie_title=movie.title,
            movie_genres=movie.genres,
            score=float(recommendation.score),
            rank=recommendation.rank,
            source=recommendation.source,
            explanation=recommendation.explanation
        )

class RecommendationResultDTO(BaseModel):
    """DTO: Resultado completo de recomendações"""
    user_id: int
    recommendations: List[RecommendationDTO]
    strategy_used: str
    diversity_score: float
    generated_at: str
```

---

## Infrastructure Layer

### Responsabilidades

- Implementar interfaces definidas no Domain
- Gerenciar conexões com sistemas externos (PostgreSQL, Redis, APIs)
- Implementar persistência (Repositories)
- Servir modelos de ML
- Logging, monitoring, tracing

### Database - SQLAlchemy ORM
```python
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy import String, Integer, Float, DateTime, ForeignKey, Index
from sqlalchemy.dialects.postgresql import ARRAY
from datetime import datetime

class Base(DeclarativeBase):
    """Base class for all ORM models"""
    pass

class UserModel(Base):
    """ORM Model: User table"""
    __tablename__ = "users"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    n_ratings: Mapped[int] = mapped_column(Integer, default=0)
    avg_rating: Mapped[float] = mapped_column(Float, default=0.0)
    last_activity: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    favorite_genres: Mapped[list[str]] = mapped_column(ARRAY(String), default=list)
    
    # Relationships
    ratings = relationship("RatingModel", back_populates="user", cascade="all, delete-orphan")
    
    # Indexes
    __table_args__ = (
        Index('idx_user_activity', 'last_activity'),
        Index('idx_user_n_ratings', 'n_ratings'),
    )

class MovieModel(Base):
    """ORM Model: Movie table"""
    __tablename__ = "movies"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(500))
    genres: Mapped[list[str]] = mapped_column(ARRAY(String), default=list)
    year: Mapped[int] = mapped_column(Integer, nullable=True)
    rating_count: Mapped[int] = mapped_column(Integer, default=0)
    avg_rating: Mapped[float] = mapped_column(Float, default=0.0)
    
    # Relationships
    ratings = relationship("RatingModel", back_populates="movie", cascade="all, delete-orphan")
    
    # Indexes
    __table_args__ = (
        Index('idx_movie_title', 'title'),
        Index('idx_movie_rating_count', 'rating_count'),
        Index('idx_movie_avg_rating', 'avg_rating'),
    )
```

### Mappers (ORM ↔ Domain)
```python
class UserMapper:
    """Mapper: UserModel ↔ User Entity"""
    
    @staticmethod
    def to_domain(model: UserModel) -> User:
        """Converte ORM model para Domain entity"""
        return User(
            id=UserId(model.id),
            created_at=Timestamp(model.created_at),
            n_ratings=model.n_ratings,
            avg_rating=model.avg_rating,
            last_activity=Timestamp(model.last_activity) if model.last_activity else None,
            favorite_genres=model.favorite_genres or []
        )
    
    @staticmethod
    def to_model(entity: User) -> UserModel:
        """Converte Domain entity para ORM model"""
        return UserModel(
            id=int(entity.id),
            created_at=entity.created_at.value,
            n_ratings=entity.n_ratings,
            avg_rating=entity.avg_rating,
            last_activity=entity.last_activity.value if entity.last_activity else None,
            favorite_genres=entity.favorite_genres
        )
    
    @staticmethod
    def update_model(model: UserModel, entity: User) -> None:
        """Atualiza model existente com dados da entity"""
        model.n_ratings = entity.n_ratings
        model.avg_rating = entity.avg_rating
        model.last_activity = entity.last_activity.value if entity.last_activity else None
        model.favorite_genres = entity.favorite_genres
```

### Repository Implementations
```python
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import List, Optional

class UserRepository(IUserRepository):
    """PostgreSQL implementation of IUserRepository"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
        self.mapper = UserMapper()
    
    async def save(self, entity: User) -> User:
        """Persiste ou atualiza usuário"""
        stmt = select(UserModel).where(UserModel.id == int(entity.id))
        result = await self.session.execute(stmt)
        existing = result.scalar_one_or_none()
        
        if existing:
            # Update
            self.mapper.update_model(existing, entity)
            await self.session.flush()
            return self.mapper.to_domain(existing)
        else:
            # Insert
            model = self.mapper.to_model(entity)
            self.session.add(model)
            await self.session.flush()
            return self.mapper.to_domain(model)
    
    async def find_by_id(self, user_id: UserId) -> Optional[User]:
        """Busca usuário por ID"""
        stmt = select(UserModel).where(UserModel.id == int(user_id))
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        
        return self.mapper.to_domain(model) if model else None
    
    async def find_power_users(self, limit: int = 1000) -> List[User]:
        """Busca power users (100+ ratings)"""
        stmt = (
            select(UserModel)
            .where(UserModel.n_ratings >= 100)
            .order_by(UserModel.n_ratings.desc())
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        models = result.scalars().all()
        
        return [self.mapper.to_domain(m) for m in models]
    
    async def count(self) -> int:
        """Conta total de usuários"""
        stmt = select(func.count()).select_from(UserModel)
        result = await self.session.execute(stmt)
        return result.scalar()
```

### Machine Learning Infrastructure

#### Neural CF Model (PyTorch)
```python
import torch
import torch.nn as nn
from typing import Tuple

class NeuralCFModel(nn.Module):
    """
    Neural Collaborative Filtering model.
    
    Arquitetura:
    - User Embedding (64 dims)
    - Movie Embedding (64 dims)
    - GMF Path (Generalized Matrix Factorization)
    - MLP Path (Multi-Layer Perceptron)
    - Fusion Layer
    """
    
    def __init__(
        self,
        n_users: int,
        n_movies: int,
        embedding_dim: int = 64,
        mlp_layers: list = [128, 64, 32]
    ):
        super().__init__()
        
        # Embeddings
        self.user_embedding = nn.Embedding(n_users, embedding_dim)
        self.movie_embedding = nn.Embedding(n_movies, embedding_dim)
        
        # GMF path
        self.gmf_layer = nn.Linear(embedding_dim, 1)
        
        # MLP path
        mlp_modules = []
        input_size = embedding_dim * 2
        for hidden_size in mlp_layers:
            mlp_modules.extend([
                nn.Linear(input_size, hidden_size),
                nn.ReLU(),
                nn.Dropout(0.2)
            ])
            input_size = hidden_size
        
        self.mlp = nn.Sequential(*mlp_modules)
        
        # Fusion
        fusion_input_size = mlp_layers[-1] + 1
        self.fusion = nn.Linear(fusion_input_size, 1)
        self.sigmoid = nn.Sigmoid()
        
        # Inicialização
        self._init_weights()
    
    def _init_weights(self):
        """Xavier initialization"""
        nn.init.xavier_uniform_(self.user_embedding.weight)
        nn.init.xavier_uniform_(self.movie_embedding.weight)
    
    def forward(
        self,
        user_ids: torch.Tensor,
        movie_ids: torch.Tensor
    ) -> torch.Tensor:
        """
        Forward pass.
        
        Args:
            user_ids: [batch_size]
            movie_ids: [batch_size]
        
        Returns:
            predictions: [batch_size, 1] - ratings normalized to [0, 1]
        """
        # Get embeddings
        user_emb = self.user_embedding(user_ids)  # [batch, 64]
        movie_emb = self.movie_embedding(movie_ids)  # [batch, 64]
        
        # GMF path: element-wise product
        gmf = user_emb * movie_emb  # [batch, 64]
        gmf_out = self.gmf_layer(gmf)  # [batch, 1]
        
        # MLP path: concatenation + dense layers
        mlp_input = torch.cat([user_emb, movie_emb], dim=-1)  # [batch, 128]
        mlp_out = self.mlp(mlp_input)  # [batch, 32]
        
        # Fusion
        fusion_input = torch.cat([gmf_out, mlp_out], dim=-1)  # [batch, 33]
        output = self.fusion(fusion_input)  # [batch, 1]
        
        # Sigmoid for [0, 1] output
        return self.sigmoid(output)
```

#### Model Server
```python
class ModelServer:
    """
    Model Serving: Carrega e serve modelo treinado para inferência.
    """
    
    def __init__(self, model_registry: ModelRegistry):
        self.model_registry = model_registry
        self.model = None
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    
    async def load_model(self, model_id: str = "latest"):
        """Carrega modelo do registry"""
        metadata = await self.model_registry.get_metadata(model_id)
        
        # Carrega pesos
        state_dict = torch.load(metadata.file_path, map_location=self.device)
        
        # Inicializa modelo
        self.model = NeuralCFModel(
            n_users=metadata.config["n_users"],
            n_movies=metadata.config["n_movies"],
            embedding_dim=metadata.config["embedding_dim"]
        )
        self.model.load_state_dict(state_dict)
        self.model.to(self.device)
        self.model.eval()
        
        logger.info(f"Loaded model {model_id} (version {metadata.version})")
    
    async def predict(
        self,
        user_id: int,
        movie_ids: List[int]
    ) -> List[dict]:
        """
        Predição em batch.
        
        Args:
            user_id: ID do usuário
            movie_ids: Lista de IDs de filmes
        
        Returns:
            Lista de {"movie_id": int, "score": float}
        """
        if self.model is None:
            await self.load_model()
        
        # Preparar tensors
        user_tensor = torch.tensor([user_id] * len(movie_ids), dtype=torch.long).to(self.device)
        movie_tensor = torch.tensor(movie_ids, dtype=torch.long).to(self.device)
        
        # Inferência
        with torch.no_grad():
            predictions = self.model(user_tensor, movie_tensor)
        
        # Converter para lista
        scores = predictions.cpu().numpy().flatten().tolist()
        
        return [
            {"movie_id": mid, "score": score}
            for mid, score in zip(movie_ids, scores)
        ]
    
    async def predict_batch(
        self,
        user_ids: List[int],
        movie_ids: List[int]
    ) -> List[dict]:
        """Predição para múltiplos pares (user, movie)"""
        if self.model is None:
            await self.load_model()
        
        user_tensor = torch.tensor(user_ids, dtype=torch.long).to(self.device)
        movie_tensor = torch.tensor(movie_ids, dtype=torch.long).to(self.device)
        
        with torch.no_grad():
            predictions = self.model(user_tensor, movie_tensor)
        
        scores = predictions.cpu().numpy().flatten().tolist()
        
        return [
            {"user_id": uid, "movie_id": mid, "score": score}
            for uid, mid, score in zip(user_ids, movie_ids, scores)
        ]
```

---

## Presentation Layer

### Responsabilidades

- Expor API REST (FastAPI)
- Validar requests (Pydantic schemas)
- Serializar responses
- Tratamento de erros
- Autenticação/Autorização
- Rate limiting
- Logging de requests

### FastAPI Application
```python
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import logging

# Configuração
app = FastAPI(
    title="RecoLab v2 API",
    description="Sistema de Recomendação de Filmes com ML",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Em produção: lista específica
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Error Handlers
@app.exception_handler(UserNotFoundError)
async def user_not_found_handler(request, exc):
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={"detail": str(exc)}
    )

@app.exception_handler(ValidationError)
async def validation_error_handler(request, exc):
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": exc.errors()}
    )

# Health Check
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "version": "2.0.0",
        "timestamp": datetime.now().isoformat()
    }

# Incluir routers
from .routers import users, movies, ratings, recommendations

app.include_router(users.router, prefix="/api/v1/users", tags=["users"])
app.include_router(movies.router, prefix="/api/v1/movies", tags=["movies"])
app.include_router(ratings.router, prefix="/api/v1/ratings", tags=["ratings"])
app.include_router(recommendations.router, prefix="/api/v1/recommendations", tags=["recommendations"])
```

### API Routes
```python
from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List

router = APIRouter()

@router.post("/", status_code=status.HTTP_201_CREATED)
async def generate_recommendations(
    request: GenerateRecommendationsRequest,
    service: RecommendationService = Depends(get_recommendation_service)
) -> RecommendationResultDTO:
    """
    Gera recomendações personalizadas para um usuário.
    
    Estratégia é selecionada automaticamente baseado no perfil:
    - Cold Start (0 ratings): Popular
    - New (1-5 ratings): Content-Based
    - Casual (6-20 ratings): Hybrid (60% CF + 40% CB)
    - Active (21-100 ratings): Hybrid (80% CF + 20% CB)
    - Power User (100+ ratings): Collaborative + Diversity
    """
    try:
        result = await service.generate_recommendations(
            user_id=UserId(request.user_id),
            n_recommendations=request.n_recommendations,
            force_refresh=request.force_refresh
        )
        
        return RecommendationResultDTO.from_result(result)
    
    except UserNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User {request.user_id} not found"
        )
    except Exception as e:
        logger.error(f"Error generating recommendations: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@router.get("/{user_id}/history")
async def get_recommendation_history(
    user_id: int,
    limit: int = Query(20, ge=1, le=100),
    service: RecommendationService = Depends(get_recommendation_service)
) -> List[RecommendationResultDTO]:
    """Retorna histórico de recomendações geradas para o usuário"""
    history = await service.get_history(UserId(user_id), limit=limit)
    return [RecommendationResultDTO.from_result(r) for r in history]
```

### Dependency Injection
```python
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

async def get_db_session() -> AsyncSession:
    """Dependency: Database session"""
    async with async_session() as session:
        yield session

def get_user_repository(
    session: AsyncSession = Depends(get_db_session)
) -> IUserRepository:
    """Dependency: User repository"""
    return UserRepository(session)

def get_recommendation_service(
    user_repo: IUserRepository = Depends(get_user_repository),
    movie_repo: IMovieRepository = Depends(get_movie_repository),
    rating_repo: IRatingRepository = Depends(get_rating_repository),
    # ... outros
) -> RecommendationService:
    """Dependency: Recommendation service"""
    return RecommendationService(
        user_repo=user_repo,
        movie_repo=movie_repo,
        rating_repo=rating_repo,
        strategy_service=RecommendationStrategyService(),
        diversity_service=DiversityService(),
        model_server=get_model_server(),
        cache=get_cache_service(),
        event_bus=get_event_bus()
    )
```

---

## Fluxos Principais

### Fluxo 1: Criar Rating
```
Client                  API                 Application             Domain              Infrastructure
  │                      │                      │                      │                      │
  ├──POST /ratings──────>│                      │                      │                      │
  │                      │                      │                      │                      │
  │                      ├──CreateRatingCmd────>│                      │                      │
  │                      │                      │                      │                      │
  │                      │                      ├──find_by_id(user)──>│                      │
  │                      │                      │                      │                      │
  │                      │                      │                      ├──SELECT users──────>│
  │                      │                      │                      │<─────User Model─────┤
  │                      │                      │<─────User Entity─────┤                      │
  │                      │                      │                      │                      │
  │                      │                      ├──find_by_id(movie)─>│                      │
  │                      │                      │<─────Movie Entity────┤                      │
  │                      │                      │                      │                      │
  │                      │                      ├──Rating()──────────>│                      │
  │                      │                      │  (validate business  │                      │
  │                      │                      │   rules)             │                      │
  │                      │                      │                      │                      │
  │                      │                      ├──user.record_rating>│                      │
  │                      │                      │  (update statistics) │                      │
  │                      │                      │                      │                      │
  │                      │                      ├──movie.add_rating──>│                      │
  │                      │                      │                      │                      │
  │                      │                      ├──BEGIN TRANSACTION─>│                      │
  │                      │                      │                      │                      │
  │                      │                      ├──save(rating)──────>│                      │
  │                      │                      │                      ├──INSERT ratings────>│
  │                      │                      │                      │                      │
  │                      │                      ├──save(user)────────>│                      │
  │                      │                      │                      ├──UPDATE users──────>│
  │                      │                      │                      │                      │
  │                      │                      ├──save(movie)───────>│                      │
  │                      │                      │                      ├──UPDATE movies─────>│
  │                      │                      │                      │                      │
  │                      │                      ├──COMMIT───────────>│                      │
  │                      │                      │                      │                      │
  │                      │                      ├──publish(RatingEvent)                      │
  │                      │                      │                      │                      │
  │                      │                      ├──invalidate_cache──>│                      │
  │                      │                      │                      ├──DEL recommendations│
  │                      │                      │<─────────────────────┤                      │
  │                      │                      │                      │                      │
  │                      │<─────RatingDTO───────┤                      │                      │
  │                      │                      │                      │                      │
  │<─────201 Created─────┤                      │                      │                      │
  │   {rating_id, ...}   │                      │                      │                      │
```

### Fluxo 2: Gerar Recomendações
```
Client                  API                 Application             Domain              Infrastructure
  │                      │                      │                      │                      │
  ├─POST /recommend─────>│                      │                      │                      │
  │                      │                      │                      │                      │
  │                      ├──GenerateRecsCmd────>│                      │                      │
  │                      │                      │                      │                      │
  │                      │                      ├──check_cache───────>│                      │
  │                      │                      │                      ├──GET recommendations│
  │                      │                      │<─────MISS────────────┤                      │
  │                      │                      │                      │                      │
  │                      │                      ├──find_user(id)─────>│                      │
  │                      │                      │<─────User Entity─────┤                      │
  │                      │                      │                      │                      │
  │                      │                      ├──user.classify()───>│                      │
  │                      │                      │<─────"active"────────┤                      │
  │                      │                      │                      │                      │
  │                      │                      ├──select_strategy───>│                      │
  │                      │                      │  (StrategyService)   │                      │
  │                      │                      │<─────"hybrid"────────┤                      │
  │                      │                      │                      │                      │
  │                      │                      ├──find_user_ratings─>│                      │
  │                      │                      │                      ├──SELECT ratings────>│
  │                      │                      │<─────Ratings─────────┤                      │
  │                      │                      │                      │                      │
  │                      │                      ├──model.predict()───>│                      │
  │                      │                      │                      ├──PyTorch inference─>│
  │                      │                      │<─────Predictions─────┤                      │
  │                      │                      │                      │                      │
  │                      │                      ├──calculate_diversity│                      │
  │                      │                      │  (DiversityService)  │                      │
  │                      │                      │                      │                      │
  │                      │                      ├──rerank_for_diversity                      │
  │                      │                      │  (MMR algorithm)     │                      │
  │                      │                      │                      │                      │
  │                      │                      ├──save_cache────────>│                      │
  │                      │                      │                      ├──SET recommendations│
  │                      │                      │                      │                      │
  │                      │                      ├──publish(RecEvent)  │                      │
  │                      │                      │                      │                      │
  │                      │<─────ResultDTO───────┤                      │                      │
  │                      │                      │                      │                      │
  │<─────200 OK──────────┤                      │                      │                      │
  │   {recommendations}  │                      │                      │                      │
```

---

## Padrões de Design

### 1. Repository Pattern

Abstrai persistência de dados.
```python
# Interface no Domain
class IUserRepository(ABC):
    @abstractmethod
    async def find_by_id(self, user_id: UserId) -> Optional[User]:
        pass

# Implementação no Infrastructure
class UserRepository(IUserRepository):
    async def find_by_id(self, user_id: UserId) -> Optional[User]:
        # PostgreSQL specific implementation
        ...
```

### 2. Factory Pattern

Criação de objetos complexos.
```python
class RecommendationStrategyFactory:
    """Factory para criar estratégias de recomendação"""
    
    def __init__(self):
        self._strategies = {}
    
    def register(self, name: str, strategy_class: type):
        """Registra nova estratégia"""
        self._strategies[name] = strategy_class
    
    def create(self, name: str, **kwargs) -> IRecommendationStrategy:
        """Cria instância da estratégia"""
        strategy_class = self._strategies.get(name)
        if not strategy_class:
            raise ValueError(f"Unknown strategy: {name}")
        return strategy_class(**kwargs)

# Usage
factory = RecommendationStrategyFactory()
factory.register("collaborative", CollaborativeStrategy)
factory.register("content_based", ContentBasedStrategy)
factory.register("hybrid", HybridStrategy)

strategy = factory.create("hybrid", cf_weight=0.6, cb_weight=0.4)
```

### 3. Strategy Pattern

Algoritmos intercambiáveis.
```python
class IRecommendationStrategy(ABC):
    """Interface para estratégias de recomendação"""
    
    @abstractmethod
    async def recommend(self, user: User, n: int) -> List[Recommendation]:
        pass

class CollaborativeStrategy(IRecommendationStrategy):
    async def recommend(self, user: User, n: int) -> List[Recommendation]:
        # Collaborative filtering implementation
        ...

class ContentBasedStrategy(IRecommendationStrategy):
    async def recommend(self, user: User, n: int) -> List[Recommendation]:
        # Content-based implementation
        ...

class HybridStrategy(IRecommendationStrategy):
    def __init__(self, cf_weight: float, cb_weight: float):
        self.cf_strategy = CollaborativeStrategy()
        self.cb_strategy = ContentBasedStrategy()
        self.cf_weight = cf_weight
        self.cb_weight = cb_weight
    
    async def recommend(self, user: User, n: int) -> List[Recommendation]:
        # Combina resultados das duas estratégias
        cf_recs = await self.cf_strategy.recommend(user, n)
        cb_recs = await self.cb_strategy.recommend(user, n)
        
        # Weighted merge
        return self._merge_weighted(cf_recs, cb_recs)
```

### 4. Observer Pattern (Domain Events)

Desacoplamento entre agregados.
```python
# Publisher
class Rating:
    def __init__(self, ..., event_bus: EventBus):
        self.event_bus = event_bus
    
    async def save(self):
        # Persistir rating
        ...
        # Publicar evento
        await self.event_bus.publish(RatingCreatedEvent(
            user_id=self.user_id,
            movie_id=self.movie_id,
            score=self.score
        ))

# Subscriber
class CacheInvalidator:
    def __init__(self, event_bus: EventBus, cache: CacheService):
        self.cache = cache
        event_bus.subscribe(RatingCreatedEvent, self.handle_rating_created)
    
    async def handle_rating_created(self, event: RatingCreatedEvent):
        """Invalida cache quando rating é criado"""
        await self.cache.delete_pattern(f"recommendations:user:{event.user_id}:*")
```

### 5. CQRS (Command Query Responsibility Segregation)

Separação entre writes e reads.
```python
# Command (Write)
@dataclass
class CreateRatingCommand:
    user_id: int
    movie_id: int
    score: float

class CreateRatingHandler:
    async def handle(self, cmd: CreateRatingCommand) -> Rating:
        # Validação + Business Logic + Persistência
        ...

# Query (Read)
@dataclass
class GetUserRatingsQuery:
    user_id: int
    limit: int = 20

class GetUserRatingsHandler:
    async def handle(self, query: GetUserRatingsQuery) -> List[RatingDTO]:
        # Apenas leitura, sem business logic
        ...
```

---

## Decisões Técnicas

### Por que Clean Architecture?

1. **Testabilidade**: Domain layer testável sem infraestrutura
2. **Independência**: Trocar FastAPI não afeta regras de negócio
3. **Escalabilidade**: Adicionar features não afeta código existente
4. **Clareza**: Separação clara de responsabilidades

### Por que PostgreSQL?

1. **ACID**: Garantia de consistência
2. **Performance**: Índices eficientes para queries complexas
3. **ARRAY Type**: Armazenar gêneros sem tabela adicional
4. **Maturidade**: Ecossistema robusto

### Por que Neural CF?

1. **Captura não-linearidades**: MLP aprende padrões complexos
2. **State-of-the-art**: Baseline forte em benchmarks
3. **Flexível**: Fácil adicionar features contextuais
4. **Performance**: Inferência rápida após treinamento

### Por que Redis?

1. **Performance**: Latência < 5ms
2. **Estruturas de dados**: Lists, Sets, Hashes
3. **Persistência**: RDB/AOF para durabilidade
4. **Escalabilidade**: 100k+ ops/s

---

## Segurança

### Autenticação
```python
# JWT tokens
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt

security = HTTPBearer()

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> User:
    """Extrai usuário do JWT token"""
    try:
        payload = jwt.decode(
            credentials.credentials,
            SECRET_KEY,
            algorithms=["HS256"]
        )
        user_id = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        
        user = await user_repo.find_by_id(UserId(user_id))
        if not user:
            raise HTTPException(status_code=401, detail="User not found")
        
        return user
    
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid token")
```

### SQL Injection Prevention

SQLAlchemy ORM com prepared statements.
```python
# Seguro
stmt = select(UserModel).where(UserModel.id == user_id)

# NUNCA fazer (SQL injection)
query = f"SELECT * FROM users WHERE id = {user_id}"
```

### Input Validation

Pydantic schemas validam todos os inputs.
```python
class GenerateRecommendationsRequest(BaseModel):
    user_id: int = Field(..., gt=0)
    n_recommendations: int = Field(10, ge=1, le=100)
    strategy: Optional[str] = Field(None, regex="^(auto|popular|collaborative|hybrid)$")
```

### Rate Limiting
```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@app.post("/recommendations/")
@limiter.limit("100/minute")
async def generate_recommendations(...):
    ...
```

---

## Performance e Escalabilidade

### Database Optimization

**Connection Pooling**:
```python
engine = create_async_engine(
    DATABASE_URL,
    pool_size=20,
    max_overflow=40,
    pool_pre_ping=True
)
```

**Índices Estratégicos**:
```sql
CREATE INDEX idx_rating_user_movie ON ratings(user_id, movie_id);
CREATE INDEX idx_movie_rating_count ON movies(rating_count DESC);
```

**Query Optimization**:
```python
# Eager loading para evitar N+1 queries
stmt = select(UserModel).options(
    selectinload(UserModel.ratings)
)
```

### Caching Strategy

**3-Layer Cache**:
1. **Application Cache (Redis)**: Recomendações, perfis
2. **Query Cache (PostgreSQL)**: Materialized views
3. **HTTP Cache**: CDN para assets estáticos

**Cache Invalidation**:
```python
# Event-driven invalidation
@event_handler(RatingCreatedEvent)
async def invalidate_cache(event):
    await redis.delete(f"recommendations:user:{event.user_id}:*")
```

### Async I/O
```python
# Requisições paralelas
async def get_recommendations_with_details(user_id: int):
    user, ratings, movies = await asyncio.gather(
        user_repo.find_by_id(user_id),
        rating_repo.find_by_user(user_id),
        movie_repo.find_popular(limit=100)
    )
    ...
```

### Horizontal Scaling

**Stateless Application**:
- Sessões em Redis (não em memória)
- Múltiplas instâncias atrás de load balancer

**Database Read Replicas**:
- Writes no primary
- Reads distribuídos entre replicas

---

## Monitoramento e Observabilidade

### Logging Estruturado
```python
import structlog

logger = structlog.get_logger()

logger.info(
    "recommendation_generated",
    user_id=user_id,
    strategy=strategy_name,
    n_recommendations=len(recommendations),
    latency_ms=latency,
    diversity_score=diversity_score
)
```

### Métricas
```python
from prometheus_client import Counter, Histogram

# Request metrics
request_count = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status']
)

request_latency = Histogram(
    'http_request_duration_seconds',
    'HTTP request latency',
    ['method', 'endpoint']
)

# Business metrics
recommendations_generated = Counter(
    'recommendations_generated_total',
    'Total recommendations generated',
    ['strategy', 'user_classification']
)
```

### Tracing
```python
from opentelemetry import trace

tracer = trace.get_tracer(__name__)

@tracer.start_as_current_span("generate_recommendations")
async def generate_recommendations(user_id: int):
    with tracer.start_as_current_span("fetch_user"):
        user = await user_repo.find_by_id(user_id)
    
    with tracer.start_as_current_span("ml_inference"):
        predictions = await model_server.predict(...)
    
    ...
```

### Health Checks
```python
@app.get("/health")
async def health_check():
    checks = {
        "database": await check_database(),
        "redis": await check_redis(),
        "ml_model": await check_ml_model()
    }
    
    status = "healthy" if all(checks.values()) else "degraded"
    
    return {
        "status": status,
        "checks": checks,
        "timestamp": datetime.now().isoformat()
    }
```

---

## Referências

### Livros

- Clean Architecture (Robert C. Martin)
- Domain-Driven Design (Eric Evans)
- Implementing Domain-Driven Design (Vaughn Vernon)
- Building Microservices (Sam Newman)

### Papers

- Neural Collaborative Filtering (He et al., WWW 2017)
- Deep Learning for Recommender Systems (Covington et al., RecSys 2016)
- The Netflix Recommender System (Gomez-Uribe & Hunt, 2015)

### Documentação

- FastAPI: https://fastapi.tiangolo.com
- SQLAlchemy 2.0: https://docs.sqlalchemy.org
- PyTorch: https://pytorch.org/docs
- Redis: https://redis.io/documentation

---

**Última atualização**: Outubro 2025  
**Versão**: 2.0.0  
**Autor**: Isaque Sangley dos Santos Gomes