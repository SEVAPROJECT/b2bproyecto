#!/usr/bin/env python3
"""
Script para probar el endpoint /api/v1/reservas/mis-reservas
"""
import requests
import json
import sys

# Configuración
API_BASE_URL = "https://backend-production-249d.up.railway.app"
ENDPOINT = f"{API_BASE_URL}/api/v1/reservas/mis-reservas"

def test_endpoint_without_auth():
    """Probar el endpoint sin autenticación"""
    print("🔍 Probando endpoint sin autenticación...")
    try:
        response = requests.get(ENDPOINT, params={
            'limit': 20,
            'offset': 0
        })
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        return response.status_code == 401  # Esperamos 401 (Unauthorized)
    except Exception as e:
        print(f"Error: {e}")
        return False

def test_endpoint_with_invalid_auth():
    """Probar el endpoint con token inválido"""
    print("\n🔍 Probando endpoint con token inválido...")
    try:
        headers = {
            'Authorization': 'Bearer invalid_token_12345',
            'Content-Type': 'application/json'
        }
        response = requests.get(ENDPOINT, params={
            'limit': 20,
            'offset': 0
        }, headers=headers)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        return response.status_code == 401  # Esperamos 401 (Unauthorized)
    except Exception as e:
        print(f"Error: {e}")
        return False

def test_endpoint_with_invalid_params():
    """Probar el endpoint con parámetros inválidos"""
    print("\n🔍 Probando endpoint con parámetros inválidos...")
    try:
        headers = {
            'Authorization': 'Bearer fake_token_for_testing',
            'Content-Type': 'application/json'
        }
        response = requests.get(ENDPOINT, params={
            'limit': 999,  # Límite muy alto
            'offset': -1,  # Offset negativo
            'fecha_desde': 'invalid-date',  # Fecha inválida
            'estado': 'invalid_state'  # Estado inválido
        }, headers=headers)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        return response.status_code == 422  # Esperamos 422 (Unprocessable Entity)
    except Exception as e:
        print(f"Error: {e}")
        return False

def test_endpoint_health():
    """Probar el health check del backend"""
    print("\n🔍 Probando health check del backend...")
    try:
        response = requests.get(f"{API_BASE_URL}/health")
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        return response.status_code == 200
    except Exception as e:
        print(f"Error: {e}")
        return False

def main():
    print("🚀 Iniciando pruebas del endpoint mis-reservas...")
    print(f"Endpoint: {ENDPOINT}")
    
    tests = [
        ("Health Check", test_endpoint_health),
        ("Sin autenticación", test_endpoint_without_auth),
        ("Token inválido", test_endpoint_with_invalid_auth),
        ("Parámetros inválidos", test_endpoint_with_invalid_params),
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n{'='*50}")
        print(f"Ejecutando: {test_name}")
        print('='*50)
        
        try:
            result = test_func()
            results.append((test_name, result))
            print(f"✅ {test_name}: {'PASÓ' if result else 'FALLÓ'}")
        except Exception as e:
            print(f"❌ {test_name}: ERROR - {e}")
            results.append((test_name, False))
    
    print(f"\n{'='*50}")
    print("RESUMEN DE PRUEBAS")
    print('='*50)
    
    for test_name, result in results:
        status = "✅ PASÓ" if result else "❌ FALLÓ"
        print(f"{test_name}: {status}")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    print(f"\nResultado: {passed}/{total} pruebas pasaron")

if __name__ == "__main__":
    main()
