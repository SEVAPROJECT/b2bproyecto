#!/usr/bin/env python3
"""
Script optimizado para asociar disponibilidades a servicios que no las tienen.
Usa inserción masiva para mejor rendimiento.

Uso:
    python scripts/populate_availability_optimized.py
"""

import sys
import os
import asyncio
from datetime import datetime, timedelta, timezone
from typing import List, Tuple

# Agregar el directorio raíz del backend al path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.services.direct_db_service import direct_db_service

# Configuración de disponibilidades para pruebas
# Mismo horario para todos: Lunes a Viernes, 9:00 AM - 5:00 PM
# Próximos 30 días, slots de 1 hora cada uno
DIAS_DISPONIBLES = 30  # Días futuros a crear disponibilidades
HORA_INICIO_DIA = 9  # 9:00 AM - inicio del día laboral
HORA_FIN_DIA = 17  # 5:00 PM - fin del día laboral
DURACION_SLOT_HORAS = 1  # Duración de cada slot en horas
DIAS_SEMANA = [0, 1, 2, 3, 4]  # Lunes a Viernes (0=Lunes, 6=Domingo)

def generate_availability_slots() -> List[Tuple[datetime, datetime]]:
    """
    Genera slots de disponibilidad para los próximos N días
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
    """Asocia disponibilidades a servicios que no las tienen usando inserción masiva"""
    print("🚀 Iniciando población optimizada de disponibilidades...\n")
    
    # Paso 1: Obtener servicios sin disponibilidad
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
        total_services = len(services)
        
        print(f"📊 Servicios sin disponibilidad: {total_services}\n")
        
        if total_services == 0:
            print("✅ Todos los servicios ya tienen disponibilidades")
            return
        
        # Paso 2: Generar slots de disponibilidad
        print("📅 Generando slots de disponibilidad...")
        availability_slots = generate_availability_slots()
        print(f"📅 Generados {len(availability_slots)} slots (próximos {DIAS_DISPONIBLES} días laborables)\n")
        
        # Paso 3: Inserción masiva
        print(f"🤖 Creando disponibilidades para {total_services} servicios...")
        print(f"📊 Total de registros a crear: {total_services * len(availability_slots)}\n")
        
        total_inserted = 0
        
        # Procesar en lotes de servicios para mejor rendimiento
        batch_size = 50  # Procesar 50 servicios a la vez
        
        for batch_start in range(0, total_services, batch_size):
            batch = services[batch_start:batch_start + batch_size]
            batch_num = (batch_start // batch_size) + 1
            total_batches = (total_services + batch_size - 1) // batch_size
            
            print(f"📦 Procesando lote {batch_num}/{total_batches} ({len(batch)} servicios)...")
            
            async with conn.transaction():
                # Preparar todos los valores para inserción masiva
                values = []
                for service in batch:
                    id_servicio = service['id_servicio']
                    for fecha_inicio, fecha_fin in availability_slots:
                        observaciones = f"Disponibilidad automática para pruebas - Servicio ID {id_servicio}"
                        values.append((
                            id_servicio,
                            fecha_inicio,
                            fecha_fin,
                            True,  # disponible
                            0.0,   # precio_adicional
                            observaciones
                        ))
                
                # Inserción masiva usando executemany
                if values:
                    insert_query = """
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
                    
                    await conn.executemany(insert_query, values)
                    total_inserted += len(values)
                    print(f"  ✅ {len(values)} disponibilidades insertadas en lote {batch_num}")
            
            print(f"  ✅ Lote {batch_num} completado\n")
        
        # Resumen
        print("=" * 60)
        print("📊 RESUMEN DE POBLACIÓN")
        print("=" * 60)
        print(f"✅ Servicios procesados: {total_services}")
        print(f"📊 Total de disponibilidades creadas: {total_inserted}")
        print(f"📅 Slots por servicio: {len(availability_slots)}")
        print(f"⏰ Horario: {HORA_INICIO_DIA:02d}:00 - {HORA_FIN_DIA:02d}:00 (slots de {DURACION_SLOT_HORAS} hora)")
        print(f"📆 Días: Lunes a Viernes (próximos {DIAS_DISPONIBLES} días)")
        print()
        
        # Verificar inserción
        verify_query = "SELECT COUNT(*) as total FROM disponibilidad"
        result = await conn.fetchrow(verify_query)
        print(f"✅ Verificación: {result['total']} disponibilidades en total en la base de datos")
        
    except Exception as e:
        print(f"❌ Error durante la población: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        if conn:
            await direct_db_service.pool.release(conn)

if __name__ == "__main__":
    asyncio.run(populate_availability())



