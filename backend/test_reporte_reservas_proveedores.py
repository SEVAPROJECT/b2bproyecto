#!/usr/bin/env python3
"""
Script para probar el endpoint de reporte de reservas de proveedores
"""

import requests
import json
from datetime import datetime

def test_reporte_reservas_proveedores():
    """Prueba el endpoint de reporte de reservas de proveedores"""
    
    # URL del endpoint
    base_url = "http://localhost:8000"
    endpoint = "/api/v1/admin/reports/reservas-proveedores"
    url = f"{base_url}{endpoint}"
    
    print("=" * 60)
    print("PRUEBA DEL ENDPOINT DE REPORTE DE RESERVAS DE PROVEEDORES")
    print("=" * 60)
    print(f"URL: {url}")
    print(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    try:
        # Headers (necesitarás un token de admin válido)
        headers = {
            "Content-Type": "application/json",
            "Authorization": "Bearer TU_TOKEN_ADMIN_AQUI"  # Reemplaza con tu token
        }
        
        print("Realizando petición...")
        response = requests.get(url, headers=headers, timeout=30)
        
        print(f"Status Code: {response.status_code}")
        print(f"Headers: {dict(response.headers)}")
        print()
        
        if response.status_code == 200:
            data = response.json()
            print("✅ RESPUESTA EXITOSA")
            print("=" * 40)
            
            # Mostrar estadísticas generales
            print(f"Total de reservas: {data.get('total_reservas', 0)}")
            print(f"Fecha de generación: {data.get('fecha_generacion', 'N/A')}")
            print(f"Filtros aplicados: {data.get('filtros_aplicados', 'N/A')}")
            print()
            
            # Mostrar estadísticas por estado
            if 'estadisticas' in data:
                stats = data['estadisticas']
                print("ESTADÍSTICAS:")
                print(f"  - Total proveedores: {stats.get('total_proveedores', 0)}")
                print(f"  - Total clientes: {stats.get('total_clientes', 0)}")
                
                if 'por_estado' in stats:
                    print("  - Por estado:")
                    for estado, count in stats['por_estado'].items():
                        print(f"    * {estado}: {count}")
                print()
            
            # Mostrar primeras 3 reservas como ejemplo
            reservas = data.get('reservas', [])
            print(f"PRIMERAS {min(3, len(reservas))} RESERVAS:")
            print("-" * 40)
            
            for i, reserva in enumerate(reservas[:3]):
                print(f"\nReserva {i+1}:")
                print(f"  ID: {reserva.get('id_reserva', 'N/A')}")
                print(f"  Cliente: {reserva.get('cliente', {}).get('nombre', 'N/A')}")
                print(f"  Email: {reserva.get('cliente', {}).get('email', 'N/A')}")
                print(f"  User ID: {reserva.get('cliente', {}).get('user_id', 'N/A')}")
                print(f"  Proveedor: {reserva.get('proveedor', {}).get('empresa', 'N/A')}")
                print(f"  Servicio: {reserva.get('servicio', {}).get('nombre', 'N/A')}")
                print(f"  Precio: ${reserva.get('servicio', {}).get('precio', 0):,.2f}")
                print(f"  Fecha servicio: {reserva.get('reserva', {}).get('fecha_servicio', 'N/A')}")
                print(f"  Estado: {reserva.get('estado', {}).get('label', 'N/A')}")
                
                if reserva.get('reserva', {}).get('observacion'):
                    print(f"  Observación: {reserva['reserva']['observacion']}")
            
            if len(reservas) > 3:
                print(f"\n... y {len(reservas) - 3} reservas más")
            
            print("\n" + "=" * 60)
            print("✅ REPORTE GENERADO EXITOSAMENTE")
            print("=" * 60)
            
        elif response.status_code == 401:
            print("❌ ERROR: No autenticado")
            print("Necesitas un token de administrador válido")
            print("\nPara obtener el token:")
            print("1. Inicia sesión como admin en el frontend")
            print("2. Abre las herramientas de desarrollador (F12)")
            print("3. Ve a Application > Local Storage")
            print("4. Copia el valor de 'accessToken'")
            print("5. Reemplaza 'TU_TOKEN_ADMIN_AQUI' en este script")
            
        elif response.status_code == 403:
            print("❌ ERROR: Acceso denegado")
            print("El usuario no tiene permisos de administrador")
            
        else:
            print(f"❌ ERROR: {response.status_code}")
            try:
                error_data = response.json()
                print(f"Detalle: {error_data}")
            except:
                print(f"Respuesta: {response.text}")
                
    except requests.exceptions.ConnectionError:
        print("❌ ERROR: No se pudo conectar al servidor")
        print("Asegúrate de que el backend esté ejecutándose en http://localhost:8000")
        
    except requests.exceptions.Timeout:
        print("❌ ERROR: Timeout - La petición tardó demasiado")
        
    except Exception as e:
        print(f"❌ ERROR INESPERADO: {str(e)}")

if __name__ == "__main__":
    test_reporte_reservas_proveedores()
