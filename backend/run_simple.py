#!/usr/bin/env python3
"""
Script ultra simple para ejecutar el servidor sin complicaciones.
"""
import subprocess
import sys
import os

def main():
    print("🚀 SERVIDOR FASTAPI - MODO SIMPLE")
    print("=" * 40)

    # Cambiar al directorio backend
    backend_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(backend_dir)

    print(f"📁 Directorio: {backend_dir}")
    print("🌐 URL del servidor: http://localhost:8000")
    print("📖 Documentación API: http://localhost:8000/docs")
    print()

    # Configurar variables de entorno básicas
    env = os.environ.copy()
    env["DATABASE_URL_LOCAL"] = "postgresql+asyncpg://postgres:postgres@localhost:5432/postgres"
    env["DATABASE_URL"] = "postgresql+asyncpg://postgres:postgres@localhost:5432/postgres"
    env["DB_HOST"] = "localhost"
    env["DB_PORT"] = "5432"
    env["DB_NAME"] = "postgres"
    env["DB_USER"] = "postgres"
    env["DB_PASSWORD"] = "postgres"

    print("🔧 Variables de entorno configuradas")
    print("🔄 Iniciando servidor...")

    try:
        # Ejecutar uvicorn directamente
        cmd = [
            sys.executable, "-m", "uvicorn",
            "app.main:app",
            "--host", "localhost",
            "--port", "8000",
            "--reload",
            "--log-level", "info"
        ]

        print(f"📝 Comando: {' '.join(cmd)}")
        print()

        subprocess.run(cmd, env=env, check=True)

    except subprocess.CalledProcessError as e:
        print(f"❌ Error al iniciar el servidor: {e}")
        print()
        print("💡 Verificaciones:")
        print("1. PostgreSQL debe estar ejecutándose")
        print("2. Todas las dependencias deben estar instaladas")
        print("3. Puerto 8000 debe estar disponible")
        print()
        print("🔧 Para instalar dependencias:")
        print("   pip install -r requirements.txt")
        print()
        print("🗄️ Para verificar PostgreSQL:")
        print("   pg_isready -h localhost -p 5432")

    except KeyboardInterrupt:
        print("\n⚠️  Servidor detenido por el usuario")

if __name__ == "__main__":
    main()

