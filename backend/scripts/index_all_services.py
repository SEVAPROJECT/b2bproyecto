#!/usr/bin/env python3
"""
Script para indexar TODOS los servicios en Weaviate para búsqueda con IA.
Vectoriza los servicios para que sean buscables semánticamente.

Uso:
    python scripts/index_all_services.py
"""

import sys
import os
import asyncio
from typing import Dict, Any

# Agregar el directorio raíz del backend al path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.services.direct_db_service import direct_db_service
from app.services.weaviate_service import weaviate_service

async def index_all_services():
    """Indexa todos los servicios activos en Weaviate."""
    print("🚀 Iniciando indexación de servicios en Weaviate...\n")
    
    # Verificar que Weaviate esté conectado
    if not weaviate_service.connected:
        print("❌ Error: Weaviate no está conectado.")
        print("💡 Verifica que WEAVIATE_URL esté configurado en .env")
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
                weaviate_service._index_servicio(dict(service))
                indexed_count += 1
                
                # Mostrar progreso cada 50 servicios
                if indexed_count % 50 == 0:
                    print(f"  ✅ {indexed_count}/{total_services} servicios indexados...")
                    
            except Exception as e:
                error_count += 1
                if error_count <= 5:  # Mostrar solo los primeros 5 errores
                    print(f"  ⚠️  Error indexando servicio ID {service['id_servicio']}: {str(e)}")
        
        # Resumen
        print("\n" + "=" * 60)
        print("📊 RESUMEN DE INDEXACIÓN")
        print("=" * 60)
        print(f"✅ Servicios indexados exitosamente: {indexed_count}")
        print(f"❌ Errores: {error_count}")
        print(f"📊 Total procesado: {total_services}")
        print()
        
        # Probar búsqueda
        print("🔍 Probando búsqueda en Weaviate...")
        try:
            # Buscar algunos servicios para verificar
            test_results = weaviate_service.search_servicios("catering", limit=5)
            print(f"✅ Búsqueda funcionando: {len(test_results)} resultados encontrados para 'catering'")
            
            if test_results:
                print("\n📋 Ejemplo de resultados:")
                for i, result in enumerate(test_results[:3], 1):
                    print(f"  {i}. {result.get('nombre', 'Sin nombre')} - {result.get('empresa', 'Sin empresa')}")
        except Exception as e:
            print(f"⚠️  Error en prueba de búsqueda: {str(e)}")
        
        return indexed_count > 0
        
    except Exception as e:
        print(f"❌ Error durante la indexación: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(index_all_services())
    
    if success:
        print("\n🎉 ¡Indexación completada exitosamente!")
        print("💡 Los servicios ahora están vectorizados y listos para búsqueda con IA")
    else:
        print("\n❌ La indexación tuvo problemas")
        print("💡 Revisa la configuración de Weaviate y los logs anteriores")
