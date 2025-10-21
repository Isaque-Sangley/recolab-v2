# ADR 0001: Adoção de Clean Architecture com Domain-Driven Design

## Status

Aceito

## Contexto

O RecoLab v2 é um sistema de recomendação que precisa lidar com múltiplos desafios:

1. Lógica de negócio complexa envolvendo diferentes estratégias de recomendação
2. Necessidade de testar algoritmos de ML independentemente da infraestrutura
3. Requisito de trocar facilmente entre diferentes bancos de dados e frameworks
4. Expectativa de evolução constante dos modelos de Machine Learning
5. Separação clara entre regras de negócio e detalhes técnicos de implementação

A arquitetura tradicional em camadas (MVC) apresenta acoplamento excessivo entre lógica de negócio e infraestrutura, dificultando testes e manutenção. Microservices seriam prematuros para um MVP e adicionariam complexidade operacional desnecessária.

## Decisão

Implementar Clean Architecture seguindo os princípios de Domain-Driven Design (DDD), organizando o código em quatro camadas distintas:

**Domain Layer (núcleo)**
- Entities: User, Movie, Rating, Recommendation
- Value Objects: UserId, MovieId, RatingScore, Timestamp
- Domain Services: RecommendationStrategyService, DiversityService, UserProfileService
- Domain Events: RatingCreated, RecommendationGenerated, ModelTrained
- Repository Interfaces (abstrações)

**Application Layer**
- Use Cases e Commands (CreateRating, GenerateRecommendations)
- Application Services (orquestração de operações)
- DTOs e Mappers
- Queries (separação CQRS parcial)

**Infrastructure Layer**
- Implementações de Repositories (PostgreSQL)
- ML Models (PyTorch, scikit-learn)
- Cache (Redis)
- External Services

**Presentation Layer**
- FastAPI Routes
- Request/Response Schemas
- Error Handlers
- Dependency Injection

A regra de dependência é estritamente respeitada: camadas externas dependem de camadas internas, nunca o contrário.

## Consequências

### Positivas

1. **Testabilidade Superior**: Domain layer é 100% testável sem mocks de infraestrutura. Testes unitários rodam em milissegundos.

2. **Independência de Frameworks**: Possível trocar FastAPI por outro framework web sem alterar regras de negócio.

3. **Independência de Banco de Dados**: Repositories abstraem completamente a persistência. Testes usam SQLite in-memory, produção usa PostgreSQL.

4. **Facilidade de Evolução**: Adicionar novos algoritmos de ML requer apenas implementar a interface do Domain Service.

5. **Clareza Conceitual**: Cada camada tem responsabilidade bem definida. Novos desenvolvedores entendem rapidamente onde adicionar funcionalidades.

6. **Inversão de Dependências**: Domain não conhece detalhes de implementação, apenas contratos.

### Negativas

1. **Boilerplate Inicial**: Mais arquivos e abstrações comparado a MVC simples.

2. **Curva de Aprendizado**: Desenvolvedores júnior podem levar mais tempo para entender a estrutura.

3. **Over-engineering Percebido**: Para funcionalidades triviais, a separação em camadas pode parecer excessiva.

4. **Duplicação de Modelos**: Entities do domínio separados de Models do ORM requer mappers.

## Alternativas Consideradas

### MVC Tradicional
**Rejeitado**: Acoplamento forte entre Controller-Model-View. Difícil testar lógica de negócio sem inicializar banco de dados. Não escala bem para sistemas complexos de ML.

### Hexagonal Architecture (Ports and Adapters)
**Considerado similar**: Conceitualmente equivalente à Clean Architecture. Rejeitado por ser menos didático e ter menos material de referência.

### Microservices
**Rejeitado**: Complexidade operacional prematura para MVP. Overhead de comunicação entre serviços. Monólito modular (Clean Architecture) oferece os mesmos benefícios de separação sem a complexidade distribuída.

### Layered Architecture sem DDD
**Rejeitado**: Separação apenas técnica (Controller-Service-Repository) sem modelagem rica de domínio. Anemic Domain Model resultaria em lógica espalhada em services.