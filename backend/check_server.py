#!/usr/bin/env python3
"""
Script para verificar el estado del servidor backend y reiniciarlo si es necesario
"""
import requests
import subprocess
import sys
import os
import time

def check_server_status():
    """Verifica si el servidor backend está funcionando"""
    try:
        response = requests.get("http://localhost:8000/", timeout=5)
        if response.status_code == 200:
            print("✅ Servidor backend está funcionando correctamente")
            return True
        else:
            print(f"❌ Servidor responde con código: {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ No se puede conectar al servidor: {e}")
        return False

def check_cors():
    """Verifica la configuración CORS"""
    try:
        headers = {
            'Origin': 'http://localhost:5173',
            'Access-Control-Request-Method': 'GET'
        }
        response = requests.options("http://localhost:8000/api/v1/provider/services/", headers=headers, timeout=5)
        cors_headers = response.headers.get('access-control-allow-origin', '')
        if 'localhost:5173' in cors_headers or cors_headers == '*':
            print("✅ CORS configurado correctamente")
            return True
        else:
            print(f"❌ Problema con CORS: {cors_headers}")
            return False
    except Exception as e:
        print(f"❌ Error verificando CORS: {e}")
        return False

def start_server():
    """Inicia el servidor backend"""
    print("🚀 Iniciando servidor backend...")

    try:
        # Cambiar al directorio backend
        os.chdir(os.path.dirname(__file__))

        # Verificar que existe main.py
        if not os.path.exists("app/main.py"):
            print("❌ No se encuentra app/main.py")
            return False

        # Iniciar servidor en background
        process = subprocess.Popen([
            sys.executable, "start_simple.py"
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        print(f"✅ Servidor iniciado con PID: {process.pid}")

        # Esperar un poco para que inicie
        time.sleep(3)

        # Verificar que esté funcionando
        if check_server_status():
            print("🎉 Servidor iniciado exitosamente")
            return True
        else:
            print("❌ El servidor no responde después de iniciarse")
            return False

    except Exception as e:
        print(f"❌ Error iniciando servidor: {e}")
        return False

def main():
    print("🔍 VERIFICACIÓN DEL SERVIDOR BACKEND")
    print("=" * 50)

    # Verificar estado del servidor
    server_ok = check_server_status()

    if server_ok:
        # Si está funcionando, verificar CORS
        cors_ok = check_cors()

        if cors_ok:
            print("\n✅ TODO FUNCIONANDO CORRECTAMENTE")
            print("🎯 El frontend debería poder conectarse sin problemas")
        else:
            print("\n❌ PROBLEMA CON CORS")
            print("🔧 Revisa la configuración CORS en main.py")
    else:
        print("\n❌ SERVIDOR NO FUNCIONA")
        print("🔧 Intentando iniciar el servidor...")

        if start_server():
            print("\n✅ SERVIDOR INICIADO EXITOSAMENTE")
            print("🎯 Ahora puedes usar el frontend")
        else:
            print("\n❌ NO SE PUDO INICIAR EL SERVIDOR")
            print("🔧 Revisa los logs de error arriba")

    print("\n" + "=" * 50)
    print("💡 COMANDOS ÚTILES:")
    print("   - Ver logs del servidor: tail -f logs o revisa la terminal")
    print("   - Detener servidor: Ctrl+C en la terminal del servidor")
    print("   - Reiniciar: python check_server.py")
    print("=" * 50)

if __name__ == "__main__":
    main()

