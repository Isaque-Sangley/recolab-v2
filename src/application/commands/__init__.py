"""
Commands Package

Commands são operações de WRITE (modificam estado do sistema).

CQRS Pattern:
- Commands: write operations
- Queries: read operations

Benefícios:
- Separação clara de responsabilidades
- Otimização independente
- Escalabilidade (write/read separados)
"""

from .rating_commands import CreateRatingCommand, DeleteRatingCommand, UpdateRatingCommand

__all__ = [
    "CreateRatingCommand",
    "UpdateRatingCommand",
    "DeleteRatingCommand",
]
