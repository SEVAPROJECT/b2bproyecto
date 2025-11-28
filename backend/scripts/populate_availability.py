#!/usr/bin/env python3
"""
Script para asociar disponibilidades a servicios que no las tienen.
Para pruebas, usa las mismas fechas y horas para todos los servicios.

Uso:
    python scripts/populate_availability.py
"""

import sys
import os
import asyncio
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Any

# Agregar el directorio raíz del backend al path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.services.direct_db_service import direct_db_service

# Configuración de disponibilidades para pruebas
# Mismo horario para todos: Lunes a Viernes, 9:00 AM - 5:00 PM
# Próximos 30 días
# Slots de 1 hora cada uno
DIAS_DISPONIBLES = 30  # Días futuros a crear disponibilidades
HORA_INICIO_DIA = 9  # 9:00 AM - inicio del día laboral
HORA_FIN_DIA = 17  # 5:00 PM - fin del día laboral
DURACION_SLOT_HORAS = 1  # Duración de cada slot en horas
DIAS_SEMANA = [0, 1, 2, 3, 4]  # Lunes a Viernes (0=Lunes, 6=Domingo)

async def get_services_without_availability() -> List[Dict[str, Any]]:
    """Obtiene servicios activos que no tienen disponibilidades"""
    conn = await direct_db_service.get_connection()
    
    try:
        query = """
            SELECT DISTINCT s.id_servicio
            FROM servicio s
            WHERE s.estado = true
            AND s.id_servicio NOT IN (
                SELECT DISTINCT id_servicio 
                FROM disponibilidad
            )
            ORDER BY s.id_servicio
        """
        
        services = await conn.fetch(query)
        return [dict(service) for service in services]
    finally:
        if conn:
            await direct_db_service.pool.release(conn)

async def get_existing_availability_pattern() -> Dict[str, Any]:
    """Obtiene un patrón de disponibilidad existente para usar como referencia"""
    conn = await direct_db_service.get_connection()
    
    try:
        query = """
            SELECT 
                fecha_inicio,
                fecha_fin,
                disponible,
                precio_adicional
            FROM disponibilidad
            LIMIT 1
        """
        
        result = await conn.fetchrow(query)
        if result:
            return dict(result)
        return None
    finally:
        if conn:
            await direct_db_service.pool.release(conn)

async def create_availability_for_service(
    conn,
    id_servicio: int,
    fecha_inicio: datetime,
    fecha_fin: datetime,
    disponible: bool = True,
    precio_adicional: float = 0.0
) -> bool:
    """Crea una disponibilidad para un servicio"""
    try:
        query = """
            INSERT INTO disponibilidad (
                id_servicio,
                fecha_inicio,
                fecha_fin,
                disponible,
                precio_adicional,
                observaciones,
                created_at,
                updated_at
            )
            VALUES ($1, $2, $3, $4, $5, $6, NOW(), NOW())
        """
        
        observaciones = f"Disponibilidad automática para pruebas - Servicio ID {id_servicio}"
        
        await conn.execute(
            query,
            id_servicio,
            fecha_inicio,
            fecha_fin,
            disponible,
            precio_adicional,
            observaciones
        )
        return True
    except Exception as e:
        print(f"  ⚠️  Error creando disponibilidad para servicio {id_servicio}: {str(e)}")
        return False

async def generate_availability_dates() -> List[tuple]:
    """
    Genera fechas y horas de disponibilidad para los próximos N días
    Crea slots de 1 hora cada uno (ej: 9:00-10:00, 10:00-11:00, etc.)
    Retorna lista de tuplas (fecha_inicio, fecha_fin)
    """
    availability_slots = []
    today = datetime.now(timezone.utc)
    
    for day_offset in range(DIAS_DISPONIBLES):
        current_date = today + timedelta(days=day_offset)
        
        # Solo días laborables (Lunes a Viernes)
        if current_date.weekday() in DIAS_SEMANA:
            # Crear slots de 1 hora desde HORA_INICIO_DIA hasta HORA_FIN_DIA
            for hora in range(HORA_INICIO_DIA, HORA_FIN_DIA):
                # Fecha inicio: día actual a la hora específica
                fecha_inicio = current_date.replace(
                    hour=hora,
                    minute=0,
                    second=0,
                    microsecond=0
                )
                
                # Fecha fin: 1 hora después
                fecha_fin = fecha_inicio + timedelta(hours=DURACION_SLOT_HORAS)
                
                availability_slots.append((fecha_inicio, fecha_fin))
    
    return availability_slots

async def populate_availability():
    """Asocia disponibilidades a servicios que no las tienen"""
    print("🚀 Iniciando población de disponibilidades...\n")
    
    # Paso 1: Obtener servicios sin disponibilidad
    print("📊 Obteniendo servicios sin disponibilidad...")
    services_without_availability = await get_services_without_availability()
    total_services = len(services_without_availability)
    
    print(f"📊 Servicios sin disponibilidad: {total_services}\n")
    
    if total_services == 0:
        print("✅ Todos los servicios ya tienen disponibilidades")
        return
    
    # Paso 2: Verificar si hay disponibilidades existentes para usar como patrón
    print("🔍 Verificando patrón de disponibilidad existente...")
    existing_pattern = await get_existing_availability_pattern()
    
    if existing_pattern:
        print("✅ Encontrado patrón existente, usando fechas similares")
    else:
        print("📅 Generando fechas de disponibilidad estándar...")
    
    # Paso 3: Generar slots de disponibilidad
    availability_slots = await generate_availability_dates()
    print(f"📅 Generados {len(availability_slots)} slots de disponibilidad (próximos {DIAS_DISPONIBLES} días laborables)\n")
    
    # Paso 4: Crear disponibilidades para cada servicio
    print(f"🤖 Creando disponibilidades para {total_services} servicios...\n")
    print(f"📊 Esto creará aproximadamente {total_services * len(availability_slots)} disponibilidades\n")
    
    conn = await direct_db_service.get_connection()
    
    try:
        created_count = 0
        error_count = 0
        total_availabilities_created = 0
        
        # Procesar en lotes para mejor rendimiento
        batch_size = 10  # Procesar 10 servicios a la vez
        
        for batch_start in range(0, total_services, batch_size):
            batch = services_without_availability[batch_start:batch_start + batch_size]
            batch_num = (batch_start // batch_size) + 1
            total_batches = (total_services + batch_size - 1) // batch_size
            
            print(f"📦 Procesando lote {batch_num}/{total_batches} ({len(batch)} servicios)...")
            
            async with conn.transaction():
                for service in batch:
                    id_servicio = service['id_servicio']
                    
                    # Crear múltiples disponibilidades (una por cada slot)
                    service_created = 0
                    for fecha_inicio, fecha_fin in availability_slots:
                        success = await create_availability_for_service(
                            conn,
                            id_servicio,
                            fecha_inicio,
                            fecha_fin,
                            disponible=True,
                            precio_adicional=0.0
                        )
                        
                        if success:
                            service_created += 1
                            total_availabilities_created += 1
                    
                    if service_created > 0:
                        created_count += 1
                    else:
                        error_count += 1
                        print(f"  ⚠️  Error procesando servicio {id_servicio}")
            
            print(f"  ✅ Lote {batch_num} completado ({created_count} servicios procesados, {total_availabilities_created} disponibilidades creadas)\n")
        
        # Resumen
        print("\n" + "=" * 60)
        print("📊 RESUMEN DE POBLACIÓN")
        print("=" * 60)
        print(f"✅ Servicios con disponibilidades creadas: {created_count}")
        print(f"❌ Servicios con errores: {error_count}")
        print(f"📊 Total de disponibilidades creadas: {total_availabilities_created}")
        print(f"📅 Slots por servicio: {len(availability_slots)}")
        print(f"⏰ Horario: {HORA_INICIO_DIA:02d}:00 - {HORA_FIN_DIA:02d}:00 (slots de {DURACION_SLOT_HORAS} hora)")
        print(f"📆 Días: Lunes a Viernes (próximos {DIAS_DISPONIBLES} días)")
        print()
        
    except Exception as e:
        print(f"❌ Error durante la población: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        if conn:
            await direct_db_service.pool.release(conn)

if __name__ == "__main__":
    asyncio.run(populate_availability())

