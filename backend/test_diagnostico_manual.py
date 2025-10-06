#!/usr/bin/env python3
"""
Script para probar manualmente el endpoint de diagnóstico
"""
import requests
import json

def test_diagnostico_manual():
    """Probar el endpoint de diagnóstico manualmente"""
    print("=== PRUEBA MANUAL DEL ENDPOINT DE DIAGNOSTICO ===")
    print()
    
    # Configuración
    base_url = "http://localhost:8000"
    endpoint = f"{base_url}/api/v1/reservas/diagnostico-usuario"
    
    print(f"URL del endpoint: {endpoint}")
    print()
    print("INSTRUCCIONES:")
    print("1. Abre tu navegador o herramienta de API (Postman, Insomnia, etc.)")
    print("2. Ve a la URL: http://localhost:8000/api/v1/reservas/diagnostico-usuario")
    print("3. Agrega el header de autorización:")
    print("   Authorization: Bearer TU_TOKEN_AQUI")
    print("4. Haz la petición GET")
    print()
    print("ALTERNATIVAMENTE, puedes usar curl:")
    print(f"curl -H 'Authorization: Bearer TU_TOKEN_AQUI' {endpoint}")
    print()
    print("RESULTADOS ESPERADOS:")
    print("=" * 50)
    print()
    print("ESCENARIO 1: Usuario es PROVEEDOR")
    print("-" * 30)
    print("""{
  "usuario": {
    "email": "bapiwo2018@anysilo.com",
    "nombre_persona": "Tu Nombre"
  },
  "es_proveedor": true,
  "es_cliente": false,
  "proveedor": {
    "id_perfil": 123,
    "nombre_fantasia": "Mi Empresa",
    "verificado": true,
    "estado": "activo"
  },
  "reservas": {
    "como_cliente": 0,
    "como_proveedor": 5
  },
  "endpoints_recomendados": [
    "GET /api/v1/reservas/reservas-proveedor"
  ]
}""")
    print()
    print("SOLUCION: Usar el endpoint /reservas-proveedor")
    print()
    print("ESCENARIO 2: Usuario es CLIENTE")
    print("-" * 30)
    print("""{
  "usuario": {
    "email": "bapiwo2018@anysilo.com",
    "nombre_persona": "Tu Nombre"
  },
  "es_proveedor": false,
  "es_cliente": true,
  "reservas": {
    "como_cliente": 3,
    "como_proveedor": 0
  },
  "endpoints_recomendados": [
    "GET /api/v1/reservas/mis-reservas"
  ]
}""")
    print()
    print("SOLUCION: Usar el endpoint /mis-reservas")
    print()
    print("ESCENARIO 3: Usuario SIN DATOS")
    print("-" * 30)
    print("""{
  "usuario": {
    "email": "bapiwo2018@anysilo.com",
    "nombre_persona": "Tu Nombre"
  },
  "es_proveedor": false,
  "es_cliente": false,
  "reservas": {
    "como_cliente": 0,
    "como_proveedor": 0
  },
  "endpoints_recomendados": [
    "No hay endpoints disponibles - usuario sin reservas ni perfil de proveedor"
  ]
}""")
    print()
    print("SOLUCION: El usuario necesita crear reservas o perfil de proveedor")
    print()
    print("COMO OBTENER EL TOKEN:")
    print("=" * 30)
    print("1. Abre las herramientas de desarrollador del navegador (F12)")
    print("2. Ve a la pestaña 'Application' o 'Aplicacion'")
    print("3. Busca en 'Local Storage' o 'Session Storage'")
    print("4. Busca una clave como 'token', 'auth_token', 'access_token'")
    print("5. Copia el valor y úsalo en la petición")
    print()
    print("O desde el backend:")
    print("1. Mira los logs del backend")
    print("2. Busca el token en las respuestas de autenticación")
    print("3. Úsalo en la petición")

if __name__ == "__main__":
    test_diagnostico_manual()
