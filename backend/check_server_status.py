#!/usr/bin/env python3
"""
Script para verificar el estado del servidor y las conexiones.
"""
import socket
import requests
import sys

def check_server():
    """Verificar si el servidor está corriendo"""
    print("🔍 VERIFICANDO ESTADO DEL SERVIDOR")
    print("=" * 35)

    # Verificar puerto 8000
    print("1. Verificando puerto 8000...")
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        result = sock.connect_ex(('localhost', 8000))
        sock.close()

        if result == 0:
            print("✅ Puerto 8000 está abierto")
        else:
            print("❌ Puerto 8000 está cerrado")
            return False
    except:
        print("❌ Error al verificar puerto")
        return False

    # Verificar endpoint de health
    print("\n2. Verificando endpoint básico...")
    try:
        response = requests.get("http://localhost:8000/", timeout=5)
        if response.status_code == 200:
            print("✅ Servidor responde correctamente")
            return True
        else:
            print(f"❌ Servidor responde con código: {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Error de conexión: {e}")
        return False

def check_cors():
    """Verificar configuración CORS"""
    print("\n3. Verificando CORS...")
    try:
        headers = {
            'Origin': 'http://localhost:5173',
            'Access-Control-Request-Method': 'GET'
        }
        response = requests.options("http://localhost:8000/api/v1/service-requests/",
                                  headers=headers, timeout=5)

        cors_headers = ['access-control-allow-origin', 'access-control-allow-methods']
        has_cors = any(h in response.headers for h in cors_headers)

        if has_cors:
            print("✅ CORS configurado correctamente")
            return True
        else:
            print("❌ CORS no configurado")
            return False
    except:
        print("❌ Error al verificar CORS")
        return False

def main():
    print("🖥️  DIAGNÓSTICO DEL SERVIDOR BACKEND")
    print("=" * 40)

    server_ok = check_server()
    cors_ok = check_cors() if server_ok else False

    print("\n" + "=" * 50)
    print("📋 RESULTADO:")

    if server_ok and cors_ok:
        print("✅ Servidor funcionando correctamente")
        print("🌐 URL: http://localhost:8000")
        print("📖 API Docs: http://localhost:8000/docs")
    else:
        print("❌ Hay problemas con el servidor:")
        if not server_ok:
            print("   • Servidor no está ejecutándose")
            print("   💡 Ejecuta: python run_simple.py")
        if not cors_ok:
            print("   • CORS no está configurado")

    print("\n🔧 Para iniciar el servidor:")
    print("   cd b2bproyecto-main-main/backend")
    print("   python run_simple.py")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n⚠️  Verificación cancelada")
    except Exception as e:
        print(f"❌ Error inesperado: {e}")

