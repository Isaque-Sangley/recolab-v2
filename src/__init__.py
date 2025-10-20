"""
RecoLab - Sistema de Recomendação de Filmes

Arquitetura em camadas (Clean Architecture / Hexagonal):

┌─────────────────────────────────────────────┐
│         PRESENTATION LAYER                  │
│         (FastAPI - REST API)                │
└────────────────┬────────────────────────────┘
                 │
┌────────────────▼────────────────────────────┐
│         APPLICATION LAYER                   │
│         (Use Cases, DTOs, CQRS)             │
└────────────────┬────────────────────────────┘
                 │
┌────────────────▼────────────────────────────┐
│         DOMAIN LAYER                        │
│         (Entities, Value Objects, Events)   │
└────────────────┬────────────────────────────┘
                 │
┌────────────────▼────────────────────────────┐
│         INFRASTRUCTURE LAYER                │
│         (Database, ML, Repositories)        │
└─────────────────────────────────────────────┘

Tecnologias:
- FastAPI: API REST
- PostgreSQL: Banco de dados
- PyTorch: Deep Learning (Neural CF)
- SQLAlchemy: ORM
- Pydantic: Validação

Modelos de ML:
- Neural Collaborative Filtering (NCF)
- Feature Store
- Model Registry
- Model Server

Padrões:
- Clean Architecture
- Domain-Driven Design (DDD)
- CQRS (Command Query Responsibility Segregation)
- Repository Pattern
- Dependency Injection
"""

__version__ = "2.0.0"
__author__ = "RecoLab Team"
__description__ = "Sistema de Recomendação de Filmes com Deep Learning"