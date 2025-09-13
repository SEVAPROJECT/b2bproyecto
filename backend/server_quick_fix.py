#!/usr/bin/env python3
"""
Solución rápida para problemas del servidor.
"""
import subprocess
import sys
import os
import time
import signal

def kill_existing_server():
    """Matar procesos existentes del servidor"""
    print("🔪 Matando procesos existentes del servidor...")

    try:
        # Buscar procesos de uvicorn
        result = subprocess.run(['tasklist', '/FI', 'IMAGENAME eq python.exe'], capture_output=True, text=True)

        if 'python.exe' in result.stdout:
            print("✅ Procesos de Python encontrados")
            # En Windows, es más difícil matar procesos específicos, así que solo informamos
            print("💡 Si hay procesos antiguos, ciérralos manualmente")
        else:
            print("✅ No hay procesos de Python ejecutándose")

    except Exception as e:
        print(f"⚠️  No se pudieron verificar procesos: {e}")

def start_server_clean():
    """Iniciar servidor de forma limpia"""
    print("🚀 Iniciando servidor limpio...")

    # Cambiar al directorio backend
    backend_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(backend_dir)

    # Configurar entorno limpio
    env = os.environ.copy()
    env["DATABASE_URL_LOCAL"] = "postgresql+asyncpg://postgres:postgres@localhost:5432/postgres"
    env["DATABASE_URL"] = "postgresql+asyncpg://postgres:postgres@localhost:5432/postgres"

    # Comando simple para iniciar el servidor
    cmd = [
        sys.executable, "-m", "uvicorn",
        "app.main:app",
        "--host", "0.0.0.0",
        "--port", "8000",
        "--reload",
        "--log-level", "info",
        "--no-access-log"  # Menos logs para claridad
    ]

    print(f"📝 Comando: {' '.join(cmd)}")
    print("🌐 URL: http://localhost:8000")
    print("📖 API Docs: http://localhost:8000/docs")
    print()
    print("⚠️  Presiona Ctrl+C para detener el servidor")
    print("=" * 50)

    try:
        subprocess.run(cmd, env=env, check=True)
    except subprocess.CalledProcessError as e:
        print(f"❌ Error al iniciar servidor: {e}")
    except KeyboardInterrupt:
        print("\n⚠️  Servidor detenido por el usuario")

def main():
    print("🔧 SERVIDOR - SOLUCIÓN RÁPIDA")
    print("=" * 35)

    # Paso 1: Matar procesos existentes
    kill_existing_server()
    print()

    # Paso 2: Pequeña pausa
    print("⏳ Preparando inicio limpio...")
    time.sleep(2)

    # Paso 3: Iniciar servidor
    start_server_clean()

if __name__ == "__main__":
    main()

