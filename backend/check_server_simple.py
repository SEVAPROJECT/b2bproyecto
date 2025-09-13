#!/usr/bin/env python3
"""
Verificación simple del estado del servidor.
"""
import requests
import time

def check_server():
    """Verificar si el servidor está funcionando"""
    print("🔍 Verificando estado del servidor...")

    try:
        # Verificar endpoint básico
        response = requests.get("http://localhost:8000/", timeout=5)
        if response.status_code == 200:
            print("✅ Servidor responde correctamente")
            return True
        else:
            print(f"❌ Servidor responde con código: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ Servidor no está ejecutándose")
        print("💡 Inicia el servidor con: python server_quick_fix.py")
        return False
    except Exception as e:
        print(f"❌ Error al verificar servidor: {e}")
        return False

def test_endpoints():
    """Probar endpoints específicos"""
    print("\n🔍 Probando endpoints...")

    endpoints = [
        ("http://localhost:8000/", "Endpoint básico"),
        ("http://localhost:8000/docs", "Documentación API"),
        ("http://localhost:8000/api/v1/service-requests/", "Solicitudes admin"),
    ]

    for url, name in endpoints:
        try:
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                print(f"✅ {name}: OK")
            elif response.status_code == 401:
                print(f"⚠️  {name}: Requiere autenticación (OK)")
            else:
                print(f"❌ {name}: Error {response.status_code}")
        except:
            print(f"❌ {name}: No responde")

def main():
    print("🖥️  VERIFICACIÓN RÁPIDA DEL SERVIDOR")
    print("=" * 40)

    if check_server():
        test_endpoints()
        print("\n🎉 ¡Servidor funcionando correctamente!")
    else:
        print("\n❌ Servidor no disponible")
        print("\n🔧 Solución:")
        print("   cd b2bproyecto-main-main/backend")
        print("   python server_quick_fix.py")

if __name__ == "__main__":
    main()

