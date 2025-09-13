#!/usr/bin/env python3
"""
Script rápido para verificar que el error de sintaxis esté corregido
"""
import sys
import os

def test_import():
    """Probar importar el módulo que tenía el error"""
    print("🔍 Verificando corrección del error de sintaxis...")

    try:
        # Agregar directorio al path
        sys.path.insert(0, os.getcwd())

        # Intentar importar el módulo problemático
        from app.api.v1.routers.services.provider_services import router as provider_services_router

        print("   ✅ Módulo provider_services importado correctamente")
        print("   ✅ Error de sintaxis corregido")

        # Verificar que el router tenga los endpoints
        routes = [route.path for route in provider_services_router.routes]
        print(f"   📋 Endpoints encontrados: {len(routes)}")
        for route in routes[:3]:  # Mostrar primeros 3
            print(f"      - {route}")

        return True

    except SyntaxError as e:
        print(f"   ❌ Error de sintaxis persistente: {e}")
        return False
    except ImportError as e:
        print(f"   ❌ Error de importación: {e}")
        return False
    except Exception as e:
        print(f"   ❌ Error inesperado: {e}")
        return False

def main():
    print("🚀 VERIFICACIÓN DE CORRECCIÓN")
    print("=" * 40)

    if test_import():
        print("\n✅ VERIFICACIÓN EXITOSA")
        print("🎯 El servidor debería poder iniciarse correctamente ahora")
        print("\n💡 Comandos para iniciar:")
        print("   python start_simple.py")
        print("   # o")
        print("   uvicorn app.main:app --host 127.0.0.1 --port 8000")
    else:
        print("\n❌ VERIFICACIÓN FALLIDA")
        print("🔧 Revisa el archivo provider_services.py")

    print("=" * 40)

if __name__ == "__main__":
    main()

