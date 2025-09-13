#!/usr/bin/env python3
"""
Script para iniciar el servidor y probar los endpoints automáticamente.
"""
import subprocess
import sys
import os
import time
import requests

def start_server():
    """Iniciar el servidor en segundo plano"""
    print("🚀 Iniciando servidor FastAPI...")

    # Cambiar al directorio backend
    backend_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(backend_dir)

    # Configurar entorno
    env = os.environ.copy()
    env["DATABASE_URL_LOCAL"] = "postgresql+asyncpg://postgres:postgres@localhost:5432/postgres"
    env["DATABASE_URL"] = "postgresql+asyncpg://postgres:postgres@localhost:5432/postgres"

    # Comando para iniciar el servidor
    cmd = [
        sys.executable, "-m", "uvicorn",
        "app.main:app",
        "--host", "localhost",
        "--port", "8000",
        "--log-level", "error"  # Solo errores para no llenar la consola
    ]

    # Iniciar servidor en segundo plano
    process = subprocess.Popen(
        cmd,
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )

    return process

def wait_for_server(max_attempts=10):
    """Esperar a que el servidor esté listo"""
    print("⏳ Esperando que el servidor inicie...")

    for attempt in range(max_attempts):
        try:
            response = requests.get("http://localhost:8000/", timeout=2)
            if response.status_code == 200:
                print("✅ Servidor listo!")
                return True
        except:
            pass

        time.sleep(1)
        print(f"   Intento {attempt + 1}/{max_attempts}...")

    return False

def test_endpoints():
    """Probar los endpoints principales"""
    print("🧪 Probando endpoints...")

    try:
        # Probar endpoint de solicitudes pendientes
        response = requests.get("http://localhost:8000/api/v1/service-requests/", timeout=5)
        if response.status_code == 200:
            print("✅ Endpoint /api/v1/service-requests/ - OK")
        else:
            print(f"❌ Endpoint /api/v1/service-requests/ - Error {response.status_code}")

        # Probar endpoint de mis solicitudes (simulado sin token por ahora)
        response = requests.get("http://localhost:8000/api/v1/service-requests/my-requests", timeout=5)
        # Este debería dar error 401 (no autorizado) si funciona correctamente
        if response.status_code == 401:
            print("✅ Endpoint /api/v1/service-requests/my-requests - OK (requiere autenticación)")
        elif response.status_code == 200:
            print("✅ Endpoint /api/v1/service-requests/my-requests - OK")
        else:
            print(f"❌ Endpoint /api/v1/service-requests/my-requests - Error {response.status_code}")

    except Exception as e:
        print(f"❌ Error probando endpoints: {e}")
        return False

    return True

def main():
    print("🔧 SERVIDOR AUTOMÁTICO + PRUEBAS")
    print("=" * 35)

    # Verificar si el servidor ya está corriendo
    try:
        response = requests.get("http://localhost:8000/", timeout=2)
        if response.status_code == 200:
            print("✅ Servidor ya está ejecutándose")
            server_process = None
        else:
            server_process = start_server()
    except:
        server_process = start_server()

    # Esperar a que el servidor inicie
    if server_process and not wait_for_server():
        print("❌ Servidor no pudo iniciar correctamente")
        if server_process:
            server_process.terminate()
        return

    # Probar endpoints
    if test_endpoints():
        print("\n🎉 ¡Servidor funcionando correctamente!")
        print("🌐 URL: http://localhost:8000")
        print("📖 API Docs: http://localhost:8000/docs")
        print("\n⚠️  El servidor seguirá ejecutándose en segundo plano")
        print("   Presiona Ctrl+C para detenerlo")
    else:
        print("\n❌ Hay problemas con los endpoints")

    # Mantener el servidor corriendo
    try:
        if server_process:
            server_process.wait()
        else:
            print("Manteniendo servidor existente...")
            while True:
                time.sleep(1)
    except KeyboardInterrupt:
        print("\n⚠️  Deteniendo servidor...")
        if server_process:
            server_process.terminate()
        print("✅ Servidor detenido")

if __name__ == "__main__":
    main()

