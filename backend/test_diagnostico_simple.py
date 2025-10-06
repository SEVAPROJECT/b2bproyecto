#!/usr/bin/env python3
"""
Script simple para probar el endpoint de diagnóstico de usuario
"""
import asyncio
import aiohttp
import json
import os

async def test_diagnostico_usuario():
    """Probar el endpoint de diagnóstico de usuario"""
    print("Probando endpoint de diagnostico de usuario...")
    print("=" * 60)
    
    # Configuración
    base_url = os.getenv("API_BASE_URL", "http://localhost:8000")
    endpoint = f"{base_url}/api/v1/reservas/diagnostico-usuario"
    
    # Token de autenticación
    auth_token = os.getenv("AUTH_TOKEN", "your-auth-token-here")
    
    headers = {
        "Authorization": f"Bearer {auth_token}",
        "Content-Type": "application/json"
    }
    
    print(f"URL del endpoint: {endpoint}")
    print(f"Token configurado: {'Si' if auth_token != 'your-auth-token-here' else 'No (usar AUTH_TOKEN)'}")
    
    async with aiohttp.ClientSession() as session:
        try:
            print(f"\nEjecutando diagnostico...")
            print("-" * 40)
            
            async with session.get(endpoint, headers=headers) as response:
                print(f"Status Code: {response.status}")
                
                if response.status == 200:
                    data = await response.json()
                    print(f"Diagnostico exitoso:")
                    print(f"   Usuario: {data.get('usuario', {}).get('email', 'N/A')}")
                    print(f"   Es Proveedor: {data.get('es_proveedor', False)}")
                    print(f"   Es Cliente: {data.get('es_cliente', False)}")
                    
                    # Información del proveedor
                    if data.get('proveedor'):
                        proveedor = data['proveedor']
                        print(f"   Empresa: {proveedor.get('nombre_fantasia', 'N/A')}")
                        print(f"   Verificado: {proveedor.get('verificado', False)}")
                        print(f"   Estado: {proveedor.get('estado', 'N/A')}")
                    
                    # Información de reservas
                    reservas = data.get('reservas', {})
                    print(f"   Reservas como cliente: {reservas.get('como_cliente', 0)}")
                    print(f"   Reservas como proveedor: {reservas.get('como_proveedor', 0)}")
                    
                    # Endpoints recomendados
                    endpoints = data.get('endpoints_recomendados', [])
                    print(f"   Endpoints recomendados:")
                    for endpoint_rec in endpoints:
                        print(f"      - {endpoint_rec}")
                    
                    # Análisis y recomendaciones
                    print(f"\nANALISIS:")
                    print("-" * 20)
                    
                    if data.get('es_proveedor') and data.get('proveedor', {}).get('verificado'):
                        print("Es un proveedor verificado")
                        print("Recomendacion: Usar /api/v1/reservas/reservas-proveedor")
                        
                        if reservas.get('como_proveedor', 0) > 0:
                            print(f"Tiene {reservas['como_proveedor']} reservas de clientes")
                        else:
                            print("No tiene reservas de clientes aun")
                            
                    elif data.get('es_cliente'):
                        print("Es un cliente")
                        print("Recomendacion: Usar /api/v1/reservas/mis-reservas")
                        
                        if reservas.get('como_cliente', 0) > 0:
                            print(f"Tiene {reservas['como_cliente']} reservas como cliente")
                        else:
                            print("No tiene reservas como cliente")
                            
                    elif data.get('es_proveedor') and not data.get('proveedor', {}).get('verificado'):
                        print("Es proveedor pero NO esta verificado")
                        print("Necesita verificacion para usar endpoints de proveedor")
                        
                    else:
                        print("No es ni cliente ni proveedor")
                        print("Necesita crear reservas o perfil de proveedor")
                    
                    # Mostrar datos completos
                    print(f"\nDATOS COMPLETOS:")
                    print("-" * 20)
                    print(json.dumps(data, indent=2, ensure_ascii=False))
                    
                elif response.status == 401:
                    print(f"No autenticado: Token invalido o expirado")
                    print("Verifica que el token de autenticacion sea correcto")
                    
                elif response.status == 403:
                    error_data = await response.json()
                    print(f"Acceso denegado: {error_data.get('detail', 'No tienes permisos')}")
                    
                else:
                    error_data = await response.json()
                    print(f"Error {response.status}: {error_data.get('detail', 'Error desconocido')}")
                    
        except Exception as e:
            print(f"Error en la peticion: {str(e)}")
    
    print(f"\nPrueba completada")
    print("=" * 60)

async def test_endpoint_availability():
    """Probar si el endpoint está disponible"""
    print("Verificando disponibilidad del servidor...")
    
    base_url = os.getenv("API_BASE_URL", "http://localhost:8000")
    health_endpoint = f"{base_url}/health"
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(health_endpoint) as response:
                if response.status == 200:
                    print("Servidor esta funcionando")
                    return True
                else:
                    print(f"Servidor no responde correctamente: {response.status}")
                    return False
    except Exception as e:
        print(f"No se puede conectar al servidor: {str(e)}")
        return False

if __name__ == "__main__":
    print("Iniciando prueba de diagnostico de usuario...")
    
    # Verificar disponibilidad del servidor
    if asyncio.run(test_endpoint_availability()):
        # Ejecutar diagnóstico
        asyncio.run(test_diagnostico_usuario())
    else:
        print("No se puede conectar al servidor. Verifica la configuracion.")
