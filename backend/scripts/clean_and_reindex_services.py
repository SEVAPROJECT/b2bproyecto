#!/usr/bin/env python3
"""
Script para limpiar el índice de Weaviate y reindexar todos los servicios desde cero.
Elimina todos los objetos existentes y luego indexa todos los servicios activos.

Uso:
    python scripts/clean_and_reindex_services.py
"""

import sys
import os
import asyncio
import requests
from typing import Dict, Any

# Agregar el directorio raíz del backend al path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.services.direct_db_service import direct_db_service
from app.services.weaviate_service import weaviate_service

def delete_all_objects_from_weaviate() -> int:
    """Elimina todos los objetos de la colección Servicios en Weaviate"""
    print("🗑️  Limpiando índice de Weaviate...\n")
    
    if not weaviate_service.connected:
        print("❌ Error: Weaviate no está conectado.")
        return 0
    
    deleted_count = 0
    
    try:
        # Obtener todos los objetos primero
        print("📊 Obteniendo lista de objetos a eliminar...")
        all_objects = weaviate_service._fetch_objects_from_weaviate(limit=10000)
        
        if not all_objects:
            print("✅ No hay objetos para eliminar")
            return 0
        
        total_objects = len(all_objects)
        print(f"📊 Objetos encontrados: {total_objects}\n")
        
        # Eliminar cada objeto usando su ID
        print("🗑️  Eliminando objetos...")
        for i, obj in enumerate(all_objects, 1):
            try:
                obj_id = obj.get('id')
                if not obj_id:
                    continue
                
                # Eliminar objeto usando HTTP DELETE
                delete_url = f"{weaviate_service.base_url}/v1/objects/{obj_id}"
                headers = weaviate_service._build_search_headers()
                
                response = requests.delete(delete_url, headers=headers, timeout=30)
                
                if response.status_code in [200, 204]:
                    deleted_count += 1
                    if deleted_count % 50 == 0:
                        print(f"  ✅ {deleted_count}/{total_objects} objetos eliminados...")
                else:
                    print(f"  ⚠️  Error eliminando objeto {obj_id}: HTTP {response.status_code}")
                    
            except Exception as e:
                print(f"  ⚠️  Error eliminando objeto: {str(e)}")
        
        print(f"\n✅ Eliminados {deleted_count} objetos del índice")
        return deleted_count
        
    except Exception as e:
        print(f"❌ Error limpiando índice: {str(e)}")
        import traceback
        traceback.print_exc()
        return deleted_count

async def reindex_all_services():
    """Reindexa todos los servicios activos en Weaviate"""
    print("\n🚀 Iniciando reindexación de servicios...\n")
    
    if not weaviate_service.connected:
        print("❌ Error: Weaviate no está conectado.")
        return False
    
    try:
        # Obtener todos los servicios activos
        conn = await direct_db_service.get_connection()
        
        query = """
            SELECT 
                s.id_servicio,
                s.nombre,
                s.descripcion,
                s.precio,
                s.estado,
                COALESCE(c.nombre, 'Sin categoría') as categoria,
                COALESCE(pe.nombre_fantasia, 'Sin empresa') as empresa
            FROM servicio s
            LEFT JOIN categoria c ON s.id_categoria = c.id_categoria
            LEFT JOIN perfil_empresa pe ON s.id_perfil = pe.id_perfil
            WHERE s.estado = true
            ORDER BY s.id_servicio
        """
        
        services = await conn.fetch(query)
        await direct_db_service.pool.release(conn)
        
        total_services = len(services)
        print(f"📊 Servicios encontrados en BD: {total_services}\n")
        
        if total_services == 0:
            print("⚠️  No hay servicios para indexar")
            return False
        
        # Indexar servicios uno por uno
        indexed_count = 0
        error_count = 0
        
        print(f"🤖 Indexando servicios en Weaviate (vectorizando para IA)...\n")
        
        for i, service in enumerate(services, 1):
            try:
                # Indexar servicio (esto lo vectoriza automáticamente en Weaviate)
                success = weaviate_service._index_servicio(dict(service))
                
                if success:
                    indexed_count += 1
                    
                    # Mostrar progreso cada 50 servicios
                    if indexed_count % 50 == 0:
                        print(f"  ✅ {indexed_count}/{total_services} servicios indexados...")
                else:
                    error_count += 1
                    if error_count <= 5:  # Mostrar solo los primeros 5 errores
                        print(f"  ⚠️  Error indexando servicio ID {service['id_servicio']}")
                    
            except Exception as e:
                error_count += 1
                if error_count <= 5:  # Mostrar solo los primeros 5 errores
                    print(f"  ⚠️  Error indexando servicio ID {service['id_servicio']}: {str(e)}")
        
        # Resumen
        print("\n" + "=" * 60)
        print("📊 RESUMEN DE REINDEXACIÓN")
        print("=" * 60)
        print(f"✅ Servicios indexados exitosamente: {indexed_count}")
        print(f"❌ Errores: {error_count}")
        print(f"📊 Total procesado: {total_services}")
        print()
        
        # Verificar indexación
        print("🔍 Verificando indexación...")
        try:
            all_results = weaviate_service._fetch_objects_from_weaviate(limit=10000)
            print(f"✅ Objetos en Weaviate después de indexación: {len(all_results) if all_results else 0}")
            
            # Probar búsqueda
            test_results = weaviate_service.search_servicios("desarrollo", limit=10)
            print(f"✅ Búsqueda de prueba 'desarrollo': {len(test_results)} resultados")
            
            if test_results:
                print("\n📋 Ejemplo de resultados:")
                for i, result in enumerate(test_results[:3], 1):
                    print(f"  {i}. {result.get('nombre', 'Sin nombre')} - {result.get('empresa', 'Sin empresa')}")
        except Exception as e:
            print(f"⚠️  Error en verificación: {str(e)}")
        
        return indexed_count > 0
        
    except Exception as e:
        print(f"❌ Error durante la reindexación: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Función principal"""
    print("=" * 60)
    print("🧹 LIMPIEZA Y REINDEXACIÓN DE SERVICIOS EN WEAVIATE")
    print("=" * 60)
    print()
    
    # Paso 1: Limpiar índice
    deleted_count = delete_all_objects_from_weaviate()
    
    if deleted_count > 0:
        print(f"\n✅ Índice limpiado: {deleted_count} objetos eliminados")
    else:
        print("\n✅ Índice ya estaba vacío o no se encontraron objetos")
    
    # Paso 2: Reindexar todos los servicios
    print("\n" + "=" * 60)
    success = await reindex_all_services()
    
    print("\n" + "=" * 60)
    if success:
        print("🎉 ¡Limpieza y reindexación completadas exitosamente!")
        print("💡 Los servicios ahora están vectorizados y listos para búsqueda con IA")
    else:
        print("❌ La reindexación tuvo problemas")
        print("💡 Revisa la configuración de Weaviate y los logs anteriores")

if __name__ == "__main__":
    asyncio.run(main())



