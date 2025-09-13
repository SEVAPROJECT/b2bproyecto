#!/usr/bin/env python3
"""
Script ultra rápido para iniciar el servidor.
"""
import subprocess
import sys
import os

def start_server():
    """Iniciar servidor de manera simple"""
    print("🚀 INICIANDO SERVIDOR FASTAPI")
    print("=" * 30)

    # Cambiar al directorio backend
    backend_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(backend_dir)

    print(f"📁 Directorio: {backend_dir}")
    print("🌐 URL: http://localhost:8000")
    print("📖 API Docs: http://localhost:8000/docs")
    print()

    # Configurar entorno
    env = os.environ.copy()
    env["DATABASE_URL_LOCAL"] = "postgresql+asyncpg://postgres:postgres@localhost:5432/postgres"
    env["DATABASE_URL"] = "postgresql+asyncpg://postgres:postgres@localhost:5432/postgres"

    try:
        # Comando para iniciar el servidor
        cmd = [
            sys.executable, "-m", "uvicorn",
            "app.main:app",
            "--host", "0.0.0.0",  # Escuchar en todas las interfaces
            "--port", "8000",
            "--reload",
            "--log-level", "info",
            "--access-log"
        ]

        print("📝 Ejecutando:", " ".join(cmd))
        print("🔄 Servidor iniciándose...")
        print("⚠️  Presiona Ctrl+C para detener")
        print()

        subprocess.run(cmd, env=env, check=True)

    except subprocess.CalledProcessError as e:
        print(f"❌ Error al iniciar servidor: {e}")
        print("\n💡 Verificaciones:")
        print("1. PostgreSQL debe estar ejecutándose")
        print("2. Todas las dependencias instaladas: pip install -r requirements.txt")
        print("3. Puerto 8000 debe estar disponible")

    except KeyboardInterrupt:
        print("\n⚠️  Servidor detenido por el usuario")

if __name__ == "__main__":
    start_server()

