#!/usr/bin/env python3
"""
Script de diagnóstico para identificar problemas con el servidor.
"""
import sys
import os
import socket

def check_postgresql():
    """Verificar si PostgreSQL está ejecutándose"""
    print("🔍 Verificando PostgreSQL...")
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        result = sock.connect_ex(('localhost', 5432))
        sock.close()
        if result == 0:
            print("✅ PostgreSQL está ejecutándose en localhost:5432")
            return True
        else:
            print("❌ PostgreSQL no está ejecutándose o no está en el puerto 5432")
            return False
    except:
        print("❌ Error al verificar PostgreSQL")
        return False

def check_dependencies():
    """Verificar dependencias de Python"""
    print("\n🔍 Verificando dependencias de Python...")
    dependencies = [
        'fastapi',
        'uvicorn',
        'sqlalchemy',
        'asyncpg',
        'pydantic'
    ]

    missing = []
    for dep in dependencies:
        try:
            __import__(dep)
            print(f"✅ {dep} - OK")
        except ImportError:
            print(f"❌ {dep} - FALTANTE")
            missing.append(dep)

    if missing:
        print(f"\n❌ Faltan {len(missing)} dependencias:")
        print("   pip install " + " ".join(missing))
        return False

    print("✅ Todas las dependencias están instaladas")
    return True

def check_files():
    """Verificar archivos importantes"""
    print("\n🔍 Verificando archivos del proyecto...")

    important_files = [
        'app/main.py',
        'app/models/publicar_servicio/solicitud_servicio.py',
        'app/api/v1/routers/services/service_requests.py'
    ]

    for file_path in important_files:
        if os.path.exists(file_path):
            print(f"✅ {file_path} - Existe")
        else:
            print(f"❌ {file_path} - NO ENCONTRADO")

def check_server_port():
    """Verificar si el puerto 8000 está disponible"""
    print("\n🔍 Verificando puerto 8000...")
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        result = sock.connect_ex(('localhost', 8000))
        sock.close()
        if result == 0:
            print("❌ Puerto 8000 está ocupado (posiblemente otro servidor)")
            return False
        else:
            print("✅ Puerto 8000 está disponible")
            return True
    except:
        print("❌ Error al verificar puerto 8000")
        return False

def main():
    print("🔧 DIAGNÓSTICO DEL SISTEMA")
    print("=" * 30)

    # Cambiar al directorio backend
    backend_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(backend_dir)
    print(f"📁 Directorio de trabajo: {backend_dir}")

    # Ejecutar verificaciones
    postgresql_ok = check_postgresql()
    dependencies_ok = check_dependencies()
    check_files()
    port_ok = check_server_port()

    print("\n" + "=" * 50)
    print("📋 RESUMEN DEL DIAGNÓSTICO:")

    if postgresql_ok and dependencies_ok and port_ok:
        print("✅ El sistema parece estar configurado correctamente")
        print("💡 Si el servidor no inicia, verifica los logs de error detallados")
    else:
        print("❌ Hay problemas que deben resolverse:")
        if not postgresql_ok:
            print("   - PostgreSQL no está ejecutándose")
        if not dependencies_ok:
            print("   - Faltan dependencias de Python")
        if not port_ok:
            print("   - Puerto 8000 ocupado")

    print("\n🚀 Para iniciar el servidor:")
    print("   python run_simple.py")

if __name__ == "__main__":
    main()

