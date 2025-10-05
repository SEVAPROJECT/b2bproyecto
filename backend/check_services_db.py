#!/usr/bin/env python3
"""
Script para verificar servicios en la base de datos
"""
import asyncio
from app.services.direct_db_service import direct_db_service

async def check_services_in_db():
    """Verificar servicios en la base de datos"""
    print("🔍 Verificando servicios en la base de datos...")
    
    try:
        conn = await direct_db_service.get_connection()
        
        query = """
            SELECT 
                s.id_servicio,
                s.nombre,
                s.descripcion,
                s.precio,
                s.estado,
                c.nombre as categoria,
                pe.nombre_fantasia as empresa
            FROM servicio s
            LEFT JOIN categoria c ON s.id_categoria = c.id_categoria
            LEFT JOIN perfil_empresa pe ON s.id_perfil = pe.id_perfil
            WHERE s.estado = true
            LIMIT 10
        """
        
        result = await conn.fetch(query)
        print(f"📊 Servicios encontrados en la BD: {len(result)}")
        
        for i, servicio in enumerate(result, 1):
            print(f"  {i}. {servicio['nombre']} - {servicio['empresa']} - {servicio['categoria']}")
        
        await direct_db_service.pool.release(conn)
        return len(result) > 0
        
    except Exception as e:
        print(f"❌ Error al verificar servicios: {str(e)}")
        return False

async def main():
    """Función principal"""
    print("🚀 Verificando servicios en la base de datos...")
    print("=" * 50)
    
    has_services = await check_services_in_db()
    
    print("\n" + "=" * 50)
    if has_services:
        print("✅ Hay servicios en la base de datos")
        print("💡 Ahora puedes indexarlos en Weaviate")
    else:
        print("❌ No hay servicios en la base de datos")
        print("💡 Necesitas crear servicios primero")

if __name__ == "__main__":
    asyncio.run(main())
