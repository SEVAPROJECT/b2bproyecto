#!/usr/bin/env python3
"""
Script de prueba simple para verificar que el servidor puede iniciarse
"""
import os
import sys

def test_imports():
    """Probar imports básicos"""
    print("🔍 Probando imports básicos...")

    try:
        import fastapi
        print(f"   ✅ FastAPI: {fastapi.__version__}")
    except ImportError as e:
        print(f"   ❌ FastAPI error: {e}")
        return False

    try:
        import uvicorn
        print(f"   ✅ Uvicorn: {uvicorn.__version__}")
    except ImportError as e:
        print(f"   ❌ Uvicorn error: {e}")
        return False

    return True

def test_basic_app():
    """Probar crear aplicación básica"""
    print("\n🏗️ Probando aplicación básica...")

    try:
        from fastapi import FastAPI
        from fastapi.middleware.cors import CORSMiddleware

        app = FastAPI(title="Test B2B Server")

        app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

        @app.get("/")
        def read_root():
            return {"message": "Test server funcionando", "status": "ok"}

        print("   ✅ Aplicación básica creada")
        return app
    except Exception as e:
        print(f"   ❌ Error creando aplicación: {e}")
        return None

def test_main_app():
    """Probar importar la aplicación principal"""
    print("\n📦 Probando aplicación principal...")

    try:
        # Agregar directorio actual al path
        sys.path.insert(0, os.getcwd())

        from app.main import app
        print("   ✅ Aplicación principal importada")
        return app
    except Exception as e:
        print(f"   ❌ Error importando aplicación principal: {e}")
        print("   💡 Este es el error que necesitamos solucionar")
        return None

def main():
    print("🚀 TEST DE SERVIDOR B2B BACKEND")
    print("=" * 50)

    # Cambiar al directorio del script
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)
    print(f"📁 Directorio de trabajo: {script_dir}")

    # Test 1: Imports básicos
    if not test_imports():
        print("\n❌ Faltan dependencias. Ejecuta:")
        print("   pip install fastapi uvicorn")
        return

    # Test 2: Aplicación básica
    basic_app = test_basic_app()

    # Test 3: Aplicación principal
    main_app = test_main_app()

    print("\n" + "=" * 50)
    print("📊 RESULTADOS:")

    if basic_app:
        print("   ✅ Servidor básico: FUNCIONA")
    else:
        print("   ❌ Servidor básico: ERROR")

    if main_app:
        print("   ✅ Aplicación principal: FUNCIONA")
        print("\n🎯 El servidor debería funcionar correctamente")
        print("💡 Ejecuta: uvicorn app.main:app --reload --host 0.0.0.0 --port 8000")
    else:
        print("   ❌ Aplicación principal: ERROR")
        print("\n🔧 SOLUCIONES:")
        print("   1. Verifica que todos los archivos de la app existan")
        print("   2. Revisa las variables de entorno (.env)")
        print("   3. Verifica la conexión a la base de datos")
        print("   4. Usa el servidor básico como alternativa")

    print("\n" + "=" * 50)

if __name__ == "__main__":
    main()