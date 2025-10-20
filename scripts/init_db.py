"""
Database Initialization Script

Cria todas as tabelas no PostgreSQL.
"""

import asyncio
import sys
from pathlib import Path


if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.infrastructure.database import get_database_config


async def main():
    """Main function"""
    print("="*60)
    print("  RECOLAB - DATABASE INITIALIZATION")
    print("="*60)
    print()
    
    print("🔧 Inicializando banco de dados...")
    
    db_config = get_database_config()
    
    try:
        print("📊 Criando tabelas...")
        
        # Importa ORM models para registrar no metadata
        from src.infrastructure.persistence.orm_models import Base
        
        # Cria todas as tabelas
        async with db_config.engine.begin() as conn:
            # Drop first (apenas dev!)
            await conn.run_sync(Base.metadata.drop_all)
            print("   🗑️  Tabelas antigas removidas")
            
            # Create
            await conn.run_sync(Base.metadata.create_all)
            print("   ✅ Tabelas criadas")
        
        print()
        print("✅ SETUP COMPLETO!")
        print()
        print("Tabelas criadas:")
        print("  - users")
        print("  - movies")
        print("  - ratings")
        print("  - recommendations")
        print("  - model_metadata")
        
    except Exception as e:
        print(f"\n❌ Erro: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    
    finally:
        await db_config.close()
    
    print()
    print("="*60)


if __name__ == "__main__":
    asyncio.run(main())