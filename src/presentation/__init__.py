"""
Presentation Layer Package

Camada de apresentação - API REST com FastAPI.

Componentes:
- main: aplicação FastAPI principal
- routers: endpoints REST
- dependencies: dependency injection
- error_handlers: tratamento de erros
- config: configurações

Arquitetura:
┌─────────────────────────────┐
│      FastAPI App            │
│                             │
│  ┌─────────────────────┐   │
│  │   Routers           │   │
│  │   - users           │   │
│  │   - movies          │   │
│  │   - ratings         │   │
│  │   - recommendations │   │ ← Você está aqui
│  └──────────┬──────────┘   │
│             │               │
│  ┌──────────▼──────────┐   │
│  │   Dependencies      │   │
│  │   (DI Container)    │   │
│  └──────────┬──────────┘   │
│             │               │
└─────────────┼───────────────┘
              │
┌─────────────▼───────────────┐
│   Application Layer         │
│   (Services, DTOs, CQRS)    │
└─────────────────────────────┘
"""

from .config import get_settings
from .main import app, create_app

__all__ = [
    "app",
    "create_app",
    "get_settings",
]
