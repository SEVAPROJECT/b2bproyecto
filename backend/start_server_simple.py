#!/usr/bin/env python3
"""
Script simple para iniciar el servidor sin dependencias complejas.
"""
import uvicorn
import os
import sys

# Configuración básica
os.environ["DATABASE_URL_LOCAL"] = "postgresql+asyncpg://postgres:postgres@localhost:5432/postgres"

# Agregar directorio raíz al path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

if __name__ == "__main__":
    print("🚀 Iniciando servidor FastAPI...")
    print("📍 URL: http://localhost:8000")
    print("📖 Docs: http://localhost:8000/docs")
    print("🔄 Presiona Ctrl+C para detener")
    print()

    uvicorn.run(
        "app.main:app",
        host="localhost",
        port=8000,
        reload=True,
        log_level="info"
    )

