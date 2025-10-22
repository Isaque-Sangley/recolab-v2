"""
Integration Tests Configuration

Estes testes requerem PostgreSQL.
Para rodar: export DATABASE_URL=postgresql://user:pass@localhost/test_db
"""

import os

import pytest


def pytest_configure(config):
    """Configura markers para testes de integração"""
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests (requires PostgreSQL)"
    )


@pytest.fixture(scope="session", autouse=True)
def check_postgresql():
    """
    Verifica se PostgreSQL está disponível para testes de integração.

    Se DATABASE_URL não estiver definida ou for SQLite, pula todos os testes.
    """
    db_url = os.getenv("DATABASE_URL", "")

    # Se não tem DATABASE_URL ou é SQLite, pula testes de integração
    if not db_url or "sqlite" in db_url.lower():
        pytest.skip(
            "\n\n"
            "=" * 70 + "\n"
            "⚠️  TESTES DE INTEGRAÇÃO PULADOS\n"
            "=" * 70 + "\n"
            "Motivo: Requerem PostgreSQL\n\n"
            "Para rodar estes testes:\n"
            "  1. Instale PostgreSQL\n"
            "  2. Configure: export DATABASE_URL=postgresql://user:pass@localhost/test_db\n"
            "  3. Rode: pytest tests/integration/ -v\n"
            "=" * 70 + "\n",
            allow_module_level=True,
        )
