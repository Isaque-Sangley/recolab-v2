"""
Train ML Model Script

Treina modelo de recomendação Neural CF.
"""

import asyncio
import sys
from datetime import datetime
from pathlib import Path

import pandas as pd

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

# Adiciona src ao path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.domain.events import DomainEventBus, ModelType
from src.infrastructure.database import get_session
from src.infrastructure.ml import ModelRegistry, ModelTrainer, TrainingConfig, TrainingStrategy
from src.infrastructure.persistence import ModelRepository
from src.infrastructure.persistence.orm_models import MovieORM, RatingORM


async def load_training_data(session):
    """Carrega dados para treinamento"""
    print("📚 Carregando dados de treinamento...")

    from sqlalchemy import select

    # Carrega ratings
    result = await session.execute(select(RatingORM))
    ratings = result.scalars().all()

    if not ratings:
        print("❌ Nenhum rating encontrado no banco!")
        print("   Execute primeiro: python scripts/load_movielens.py")
        sys.exit(1)

    # Converte para DataFrame
    ratings_data = []
    for r in ratings:
        ratings_data.append({"user_id": r.user_id, "item_id": r.movie_id, "rating": r.score})

    ratings_df = pd.DataFrame(ratings_data)

    print(f"✅ {len(ratings_df)} ratings carregados")
    print(f"   Usuários: {ratings_df['user_id'].nunique()}")
    print(f"   Filmes: {ratings_df['item_id'].nunique()}")

    return ratings_df


async def main():
    """Main function"""
    print("=" * 60)
    print("  RECOLAB - TRAIN ML MODEL")
    print("=" * 60)
    print()

    # Configuração de treinamento
    print("Opções de treinamento:")
    print("  1. Quick test (2 epochs, sample)")
    print("  2. Normal training (10 epochs)")
    print("  3. Full training (20 epochs)")

    choice = input("\nEscolha (1/2/3) [1]: ").strip() or "1"

    configs = {
        "1": TrainingConfig(
            model_type=ModelType.NEURAL_CF,
            strategy=TrainingStrategy.SAMPLE,
            sample_size=5000,
            ncf_epochs=2,
            ncf_batch_size=256,
            validation_split=0.1,
        ),
        "2": TrainingConfig(
            model_type=ModelType.NEURAL_CF,
            strategy=TrainingStrategy.FULL,
            ncf_epochs=10,
            ncf_batch_size=256,
            validation_split=0.1,
        ),
        "3": TrainingConfig(
            model_type=ModelType.NEURAL_CF,
            strategy=TrainingStrategy.FULL,
            ncf_epochs=20,
            ncf_batch_size=512,
            validation_split=0.1,
        ),
    }

    config = configs.get(choice, configs["1"])

    print()
    print(f"⚙️  Configuração:")
    print(f"   Estratégia: {config.strategy.value}")
    print(f"   Epochs: {config.ncf_epochs}")
    print(f"   Batch size: {config.ncf_batch_size}")
    print()

    # Carrega dados
    async for session in get_session():
        ratings_df = await load_training_data(session)
        break

    print()

    # Event bus
    event_bus = DomainEventBus()

    # Trainer
    trainer = ModelTrainer(event_bus)

    # Treina
    print("🚀 Iniciando treinamento...")
    print()

    version = datetime.now().strftime("%Y%m%d_%H%M%S")

    result = trainer.train(config=config, ratings_data=ratings_df, version=version)

    print()

    if result.is_success():
        print("=" * 60)
        print("  TREINAMENTO CONCLUÍDO!")
        print("=" * 60)
        print()
        print(f"📊 Métricas:")
        for metric, value in result.metrics.items():
            if isinstance(value, list):
                print(f"   {metric}: (lista com {len(value)} valores)")
            elif isinstance(value, (int, float)):
                print(f"   {metric}: {value:.4f}")
            else:
                print(f"   {metric}: {value}")
        print()
        print(f"⏱️  Tempo: {result.training_duration:.2f}s")
        print()

        # Salva modelo
        print("💾 Salvando modelo...")

        async for session in get_session():
            model_repo = ModelRepository(session, models_path="models")
            model_registry = ModelRegistry(model_repo, event_bus)

            # Registra modelo
            model_version = await model_registry.register_model(
                model=result.model,
                model_type=config.model_type,
                version=version,
                metrics=result.metrics,
                training_config=config.to_dict(),
            )

            # COMMIT para persistir metadata
            await session.commit()

            # Promove para champion
            await model_registry.promote_to_champion(model_type=config.model_type, version=version)

            # COMMIT para persistir champion
            await session.commit()

            print(f"✅ Modelo salvo e promovido para CHAMPION!")
            print(f"   Versão: {version}")

            break

    else:
        print("=" * 60)
        print("  TREINAMENTO FALHOU!")
        print("=" * 60)
        print(f"\n❌ Erro: {result.error_message}")


if __name__ == "__main__":
    asyncio.run(main())
