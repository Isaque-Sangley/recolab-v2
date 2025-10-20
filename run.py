import asyncio
import sys
import uvicorn

# FIX para Windows
if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

from src.presentation import create_app

if __name__ == "__main__":
    print("=" * 50)
    print("    🎬 RecoLab API v2.0.0")
    print("    Sistema de Recomendação de Filmes")
    print("    com Deep Learning")
    print("=" * 50)
    print()
    print("🚀 Starting server...")
    print("📚 Docs: http://localhost:8000/docs")
    print("📖 ReDoc: http://localhost:8000/redoc")
    print("💚 Health: http://localhost:8000/health")
    print()
    
    # CORRIJA ESTA PARTE:
    uvicorn.run(
        "src.presentation.main:app",  # ← String import (não objeto)
        host="0.0.0.0",
        port=8000,
        reload=False,  # ← Desliga reload no Windows por enquanto
        log_level="info"
    )