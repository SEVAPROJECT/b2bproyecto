#!/usr/bin/env python3
"""
Script para diagnosticar y resolver problemas del servidor backend
"""

import os
import sys
import subprocess
import time
from pathlib import Path

def print_header():
    print("🔧 DIAGNÓSTICO Y REPARACIÓN DEL SERVIDOR BACKEND")
    print("=" * 60)

def check_environment():
    """Verificar entorno y dependencias"""
    print("\n📋 VERIFICANDO ENTORNO:")

    # Verificar Python
    print(f"   🐍 Python: {sys.version}")

    # Verificar directorio
    cwd = os.getcwd()
    print(f"   📁 Directorio: {cwd}")

    # Verificar archivos importantes
    files_to_check = [
        'app/main.py',
        'requirements.txt',
        'venv/',
        '.env'
    ]

    for file_path in files_to_check:
        if os.path.exists(file_path):
            print(f"   ✅ {file_path}")
        else:
            print(f"   ❌ {file_path} - NO ENCONTRADO")

def check_imports():
    """Verificar imports críticos"""
    print("\n📦 VERIFICANDO IMPORTS:")

    try:
        import fastapi
        print(f"   ✅ FastAPI: {fastapi.__version__}")
    except ImportError:
        print("   ❌ FastAPI no instalado")

    try:
        import uvicorn
        print(f"   ✅ Uvicorn: {uvicorn.__version__}")
    except ImportError:
        print("   ❌ Uvicorn no instalado")

    try:
        import sqlalchemy
        print(f"   ✅ SQLAlchemy: {sqlalchemy.__version__}")
    except ImportError:
        print("   ❌ SQLAlchemy no instalado")

def test_basic_import():
    """Probar import básico de la aplicación"""
    print("\n🔍 PROBANDO IMPORT BÁSICO:")

    try:
        sys.path.append('.')
        from app.main import app
        print("   ✅ Import de app.main exitoso")
        return True
    except Exception as e:
        print(f"   ❌ Error en import: {e}")
        return False

def create_simple_server():
    """Crear servidor simple para testing"""
    print("\n🚀 CREANDO SERVIDOR SIMPLE:")

    server_code = '''#!/usr/bin/env python3
"""
Servidor simple para testing
"""
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

app = FastAPI(title="B2B Simple Server")

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {
        "message": "B2B Server funcionando",
        "status": "ok",
        "version": "1.0.0"
    }

@app.get("/api/v1/health")
def health_check():
    return {
        "status": "healthy",
        "timestamp": "2024-01-01T00:00:00Z"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
'''

    try:
        with open('simple_server.py', 'w', encoding='utf-8') as f:
            f.write(server_code)
        print("   ✅ Servidor simple creado: simple_server.py")
        return True
    except Exception as e:
        print(f"   ❌ Error creando servidor simple: {e}")
        return False

def create_startup_script():
    """Crear script de inicio optimizado"""
    print("\n⚡ CREANDO SCRIPT DE INICIO OPTIMIZADO:")

    startup_code = '''#!/usr/bin/env python3
"""
Script de inicio optimizado para el servidor B2B
"""
import os
import sys
import subprocess
import time

def main():
    print("🚀 Iniciando servidor B2B Backend...")

    # Verificar que estamos en el directorio correcto
    if not os.path.exists("app/main.py"):
        print("❌ Error: No se encuentra app/main.py")
        print("💡 Asegúrate de ejecutar desde el directorio backend")
        return

    # Verificar dependencias
    try:
        import fastapi
        import uvicorn
        import sqlalchemy
        print("✅ Dependencias verificadas")
    except ImportError as e:
        print(f"❌ Dependencia faltante: {e}")
        print("💡 Ejecuta: pip install -r requirements.txt")
        return

    # Probar import de la aplicación
    try:
        from app.main import app
        print("✅ Aplicación importada correctamente")
    except Exception as e:
        print(f"❌ Error importando aplicación: {e}")
        print("💡 Revisa los archivos de configuración")
        return

    # Iniciar servidor
    print("🔧 Iniciando servidor en http://localhost:8000")
    print("📊 Dashboard: http://localhost:8000/docs")
    print("🛑 Presiona Ctrl+C para detener")

    try:
        import uvicorn
        uvicorn.run(
            "app.main:app",
            host="0.0.0.0",
            port=8000,
            reload=True,
            reload_dirs=["app"],
            log_level="info"
        )
    except KeyboardInterrupt:
        print("\\n👋 Servidor detenido")
    except Exception as e:
        print(f"❌ Error iniciando servidor: {e}")

if __name__ == "__main__":
    main()
'''

    try:
        with open('start_server.py', 'w', encoding='utf-8') as f:
            f.write(startup_code)
        print("   ✅ Script de inicio creado: start_server.py")
        return True
    except Exception as e:
        print(f"   ❌ Error creando script de inicio: {e}")
        return False

def create_requirements_backup():
    """Crear archivo requirements.txt de respaldo"""
    print("\n📦 CREANDO REQUIREMENTS BACKUP:")

    requirements = '''fastapi==0.104.1
uvicorn[standard]==0.24.0
sqlalchemy==2.0.23
asyncpg==0.29.0
alembic==1.12.1
pydantic==2.5.0
python-multipart==0.0.6
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
python-dotenv==1.0.0
supabase==2.3.0
httpx==0.25.2
'''

    try:
        if not os.path.exists('requirements.txt'):
            with open('requirements.txt', 'w', encoding='utf-8') as f:
                f.write(requirements)
            print("   ✅ requirements.txt creado")
        else:
            print("   ✅ requirements.txt ya existe")
        return True
    except Exception as e:
        print(f"   ❌ Error creando requirements.txt: {e}")
        return False

def main():
    print_header()
    check_environment()
    check_imports()

    success = test_basic_import()

    if success:
        print("\n✅ EL SERVIDOR DEBERÍA FUNCIONAR")
        print("💡 Ejecuta: python start_server.py")
    else:
        print("\n❌ HAY PROBLEMAS CON LA APLICACIÓN")
        print("🔧 Creando soluciones alternativas...")

        create_simple_server()
        create_startup_script()
        create_requirements_backup()

        print("\n" + "=" * 60)
        print("🎯 SOLUCIONES CREADAS:")
        print("1. 📄 simple_server.py - Servidor básico para testing")
        print("2. 🚀 start_server.py - Script de inicio optimizado")
        print("3. 📦 requirements.txt - Dependencias verificadas")
        print("=" * 60)

        print("\n📋 INSTRUCCIONES:")
        print("1. Ejecuta: pip install -r requirements.txt")
        print("2. Prueba: python simple_server.py")
        print("3. Si funciona, prueba: python start_server.py")
        print("4. Si no funciona, revisa los errores y configura la BD")

if __name__ == "__main__":
    main()

