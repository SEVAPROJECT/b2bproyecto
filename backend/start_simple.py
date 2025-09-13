#!/usr/bin/env python3
"""
Script de inicio simple y robusto para el servidor B2B
"""
import os
import sys
import logging

# Configurar logging básico
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

def check_environment():
    """Verificar entorno básico"""
    print("🔍 Verificando entorno...")

    # Verificar Python
    print(f"   🐍 Python: {sys.version}")

    # Verificar directorio
    cwd = os.getcwd()
    print(f"   📁 Directorio: {cwd}")

    # Verificar archivos críticos
    critical_files = [
        'app/main.py',
        'app/__init__.py',
        'requirements.txt'
    ]

    for file_path in critical_files:
        if os.path.exists(file_path):
            print(f"   ✅ {file_path}")
        else:
            print(f"   ❌ {file_path} - NO ENCONTRADO")

def start_server():
    """Iniciar servidor con configuración básica"""
    print("\n🚀 Iniciando servidor B2B Backend...")

    try:
        # Configurar variables de entorno mínimas si no existen
        if not os.getenv('DATABASE_URL'):
            os.environ['DATABASE_URL'] = 'postgresql://user:password@localhost:5432/b2b_db'
            print("   ⚠️ Usando DATABASE_URL por defecto")

        # Importar uvicorn
        import uvicorn

        print("   📡 Iniciando servidor en http://localhost:8000")
        print("   📊 Dashboard: http://localhost:8000/docs")
        print("   🛑 Presiona Ctrl+C para detener")
        print()

        # Iniciar servidor con configuración básica
        uvicorn.run(
            "app.main:app",
            host="127.0.0.1",  # Cambiar a localhost para evitar problemas
            port=8000,
            reload=False,  # Deshabilitar reload para evitar problemas
            log_level="info",
            access_log=True
        )

    except KeyboardInterrupt:
        print("\n👋 Servidor detenido por el usuario")
    except ImportError as e:
        print(f"\n❌ Error de importación: {e}")
        print("💡 Instala las dependencias:")
        print("   pip install -r requirements.txt")
    except Exception as e:
        print(f"\n❌ Error iniciando servidor: {e}")
        print("💡 Revisa los logs para más detalles")

        # Intentar con configuración más básica
        print("\n🔄 Intentando con configuración básica...")
        try:
            import uvicorn
            uvicorn.run(
                "app.main:app",
                host="127.0.0.1",
                port=8000,
                reload=False,
                log_level="error"  # Solo errores
            )
        except Exception as e2:
            print(f"❌ Error con configuración básica: {e2}")

def main():
    check_environment()
    start_server()

if __name__ == "__main__":
    main()

