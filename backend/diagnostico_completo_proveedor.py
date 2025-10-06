#!/usr/bin/env python3
"""
Diagnóstico completo para el problema del proveedor
"""
import asyncio
import aiohttp
import json
import os

async def diagnostico_completo():
    """Diagnóstico completo del problema del proveedor"""
    print("=== DIAGNOSTICO COMPLETO DEL PROVEEDOR ===")
    print()
    
    # Configuración
    base_url = os.getenv("API_BASE_URL", "http://localhost:8000")
    auth_token = os.getenv("AUTH_TOKEN", "your-auth-token-here")
    
    headers = {
        "Authorization": f"Bearer {auth_token}",
        "Content-Type": "application/json"
    }
    
    print(f"URL Base: {base_url}")
    print(f"Token configurado: {'Si' if auth_token != 'your-auth-token-here' else 'No'}")
    print()
    
    async with aiohttp.ClientSession() as session:
        # 1. Diagnóstico del usuario
        print("1. DIAGNOSTICO DEL USUARIO")
        print("=" * 40)
        try:
            async with session.get(f"{base_url}/api/v1/reservas/diagnostico-usuario", headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    print("Usuario encontrado:")
                    print(f"  Email: {data.get('usuario', {}).get('email', 'N/A')}")
                    print(f"  Es Proveedor: {data.get('es_proveedor', False)}")
                    print(f"  Es Cliente: {data.get('es_cliente', False)}")
                    
                    if data.get('proveedor'):
                        proveedor = data['proveedor']
                        print(f"  Empresa: {proveedor.get('nombre_fantasia', 'N/A')}")
                        print(f"  Verificado: {proveedor.get('verificado', False)}")
                        print(f"  Estado: {proveedor.get('estado', 'N/A')}")
                        print(f"  ID Perfil: {proveedor.get('id_perfil', 'N/A')}")
                    
                    reservas = data.get('reservas', {})
                    print(f"  Reservas como cliente: {reservas.get('como_cliente', 0)}")
                    print(f"  Reservas como proveedor: {reservas.get('como_proveedor', 0)}")
                    
                    endpoints = data.get('endpoints_recomendados', [])
                    print(f"  Endpoints recomendados: {endpoints}")
                    
                else:
                    print(f"Error en diagnóstico: {response.status}")
                    error_data = await response.json()
                    print(f"Detalle: {error_data.get('detail', 'Error desconocido')}")
        except Exception as e:
            print(f"Error en diagnóstico: {str(e)}")
        
        print()
        
        # 2. Probar endpoint de reservas para proveedores
        print("2. PROBANDO ENDPOINT DE RESERVAS PROVEEDOR")
        print("=" * 40)
        try:
            async with session.get(f"{base_url}/api/v1/reservas/reservas-proveedor", headers=headers) as response:
                print(f"Status Code: {response.status}")
                
                if response.status == 200:
                    data = await response.json()
                    reservas = data.get('reservas', [])
                    pagination = data.get('pagination', {})
                    proveedor_info = data.get('proveedor', {})
                    
                    print(f"Reservas encontradas: {len(reservas)}")
                    print(f"Total: {pagination.get('total', 0)}")
                    print(f"Proveedor: {proveedor_info.get('nombre_empresa', 'N/A')}")
                    
                    if reservas:
                        print("Primeras 3 reservas:")
                        for i, reserva in enumerate(reservas[:3]):
                            print(f"  {i+1}. ID: {reserva.get('id_reserva')}")
                            print(f"     Servicio: {reserva.get('nombre_servicio')}")
                            print(f"     Cliente: {reserva.get('nombre_cliente')}")
                            print(f"     Fecha: {reserva.get('fecha')}")
                            print(f"     Estado: {reserva.get('estado')}")
                    else:
                        print("No se encontraron reservas")
                        
                elif response.status == 403:
                    error_data = await response.json()
                    print(f"Acceso denegado: {error_data.get('detail', 'Sin permisos')}")
                    
                elif response.status == 401:
                    print("No autenticado - Token inválido")
                    
                else:
                    error_data = await response.json()
                    print(f"Error {response.status}: {error_data.get('detail', 'Error desconocido')}")
                    
        except Exception as e:
            print(f"Error en endpoint: {str(e)}")
        
        print()
        
        # 3. Verificar servicios del proveedor
        print("3. VERIFICANDO SERVICIOS DEL PROVEEDOR")
        print("=" * 40)
        try:
            async with session.get(f"{base_url}/api/v1/services/services", headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    servicios = data.get('services', [])
                    print(f"Servicios del proveedor: {len(servicios)}")
                    
                    if servicios:
                        print("Servicios encontrados:")
                        for i, servicio in enumerate(servicios[:3]):
                            print(f"  {i+1}. ID: {servicio.get('id_servicio')}")
                            print(f"     Nombre: {servicio.get('nombre')}")
                            print(f"     Precio: {servicio.get('precio')}")
                            print(f"     Estado: {servicio.get('estado')}")
                    else:
                        print("No se encontraron servicios")
                else:
                    print(f"Error al obtener servicios: {response.status}")
        except Exception as e:
            print(f"Error al verificar servicios: {str(e)}")
        
        print()
        
        # 4. Verificar reservas en la base de datos
        print("4. VERIFICACION EN BASE DE DATOS")
        print("=" * 40)
        print("Para verificar manualmente en la base de datos:")
        print("1. Conecta a tu base de datos")
        print("2. Ejecuta estas consultas:")
        print()
        print("-- Verificar perfil del proveedor")
        print("SELECT id_perfil, nombre_fantasia, verificado, estado")
        print("FROM perfil_empresa")
        print("WHERE user_id = 'TU_USER_ID_AQUI';")
        print()
        print("-- Verificar servicios del proveedor")
        print("SELECT s.id_servicio, s.nombre, s.estado, s.id_perfil")
        print("FROM servicio s")
        print("INNER JOIN perfil_empresa pe ON s.id_perfil = pe.id_perfil")
        print("WHERE pe.user_id = 'TU_USER_ID_AQUI';")
        print()
        print("-- Verificar reservas de los servicios del proveedor")
        print("SELECT r.id_reserva, r.estado, r.fecha, s.nombre as servicio")
        print("FROM reserva r")
        print("INNER JOIN servicio s ON r.id_servicio = s.id_servicio")
        print("INNER JOIN perfil_empresa pe ON s.id_perfil = pe.id_perfil")
        print("WHERE pe.user_id = 'TU_USER_ID_AQUI';")
        print()
        
        # 5. Posibles problemas y soluciones
        print("5. POSIBLES PROBLEMAS Y SOLUCIONES")
        print("=" * 40)
        print("A. Problema: Usuario no es proveedor")
        print("   Solucion: Verificar que tenga perfil_empresa")
        print()
        print("B. Problema: Proveedor no verificado")
        print("   Solucion: Verificar campo 'verificado' en perfil_empresa")
        print()
        print("C. Problema: No tiene servicios")
        print("   Solucion: Crear servicios para el proveedor")
        print()
        print("D. Problema: No hay reservas de clientes")
        print("   Solucion: Crear reservas de prueba")
        print()
        print("E. Problema: Token de autenticacion incorrecto")
        print("   Solucion: Verificar token en localStorage")
        print()
        print("F. Problema: Endpoint incorrecto")
        print("   Solucion: Verificar que use /reservas-proveedor")
        print()
        
        print("6. COMANDOS DE PRUEBA")
        print("=" * 40)
        print("Para probar manualmente:")
        print(f"curl -H 'Authorization: Bearer {auth_token}' {base_url}/api/v1/reservas/diagnostico-usuario")
        print(f"curl -H 'Authorization: Bearer {auth_token}' {base_url}/api/v1/reservas/reservas-proveedor")

if __name__ == "__main__":
    asyncio.run(diagnostico_completo())
