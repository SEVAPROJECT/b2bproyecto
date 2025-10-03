#!/usr/bin/env python3
"""
Script para verificar si el backend local está funcionando
"""
import requests
import sys

def check_local_backend():
    """Verificar si el backend local está funcionando"""
    try:
        print("🔍 Verificando backend local en http://localhost:8000...")
        
        # Probar health check
        response = requests.get("http://localhost:8000/health", timeout=5)
        print(f"✅ Health check: {response.status_code}")
        print(f"📊 Respuesta: {response.text}")
        
        # Probar endpoint raíz
        response = requests.get("http://localhost:8000/", timeout=5)
        print(f"✅ Endpoint raíz: {response.status_code}")
        print(f"📊 Respuesta: {response.text}")
        
        return response.status_code == 200
        
    except requests.exceptions.ConnectionError:
        print("❌ No se puede conectar al backend local")
        print("💡 Asegúrate de que el backend esté ejecutándose en el puerto 8000")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def check_endpoint_test():
    """Verificar el endpoint de prueba"""
    try:
        print("\n🔍 Verificando endpoint de prueba...")
        
        # Probar endpoint de prueba (sin autenticación)
        response = requests.get("http://localhost:8000/api/v1/reservas/mis-reservas-test", timeout=5)
        print(f"📊 Status: {response.status_code}")
        print(f"📊 Respuesta: {response.text}")
        
        return response.status_code in [200, 401, 422]  # 401 es esperado sin auth
        
    except Exception as e:
        print(f"❌ Error en endpoint de prueba: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Verificando backend local...")
    
    backend_ok = check_local_backend()
    endpoint_ok = check_endpoint_test()
    
    print(f"\n{'='*50}")
    print("RESUMEN:")
    print(f"Backend local: {'✅ OK' if backend_ok else '❌ ERROR'}")
    print(f"Endpoint test: {'✅ OK' if endpoint_ok else '❌ ERROR'}")
    
    if not backend_ok:
        print("\n💡 Para iniciar el backend local:")
        print("   cd b2bproyecto/backend")
        print("   python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000")
    
    sys.exit(0 if backend_ok else 1)
