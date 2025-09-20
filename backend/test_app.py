#!/usr/bin/env python3
"""
Script de prueba para verificar que la aplicación FastAPI funciona correctamente
"""

import sys
import os

def test_imports():
    """Verificar que todas las dependencias se pueden importar"""
    print("🔍 Verificando importaciones...")
    
    try:
        import fastapi
        print("✅ FastAPI importado correctamente")
    except ImportError as e:
        print(f"❌ Error al importar FastAPI: {e}")
        return False
    
    try:
        import uvicorn
        print("✅ Uvicorn importado correctamente")
    except ImportError as e:
        print(f"❌ Error al importar Uvicorn: {e}")
        return False
    
    try:
        from app.main import app
        print("✅ Aplicación FastAPI importada correctamente")
    except ImportError as e:
        print(f"❌ Error al importar la aplicación: {e}")
        return False
    
    return True

def test_app_creation():
    """Verificar que la aplicación se puede crear"""
    print("🔍 Verificando creación de la aplicación...")
    
    try:
        from app.main import app
        print(f"✅ Aplicación creada: {app.title}")
        print(f"✅ Versión: {app.version}")
        return True
    except Exception as e:
        print(f"❌ Error al crear la aplicación: {e}")
        return False

def main():
    """Función principal de prueba"""
    print("🚀 Iniciando pruebas de la aplicación...")
    
    if not test_imports():
        print("❌ Falló la verificación de importaciones")
        sys.exit(1)
    
    if not test_app_creation():
        print("❌ Falló la verificación de creación de la aplicación")
        sys.exit(1)
    
    print("✅ Todas las pruebas pasaron correctamente")
    print("🎯 La aplicación está lista para ejecutarse")

if __name__ == "__main__":
    main()

