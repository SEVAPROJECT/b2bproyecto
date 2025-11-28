#!/usr/bin/env python3
"""
Script para generar disponibilidades basándose en los horarios de trabajo (horario_trabajo).
Lee los horarios semanales de cada proveedor y genera disponibilidades para todos sus servicios.

Uso:
    python scripts/populate_availability_from_horarios.py
"""

import sys
import os
import asyncio
from datetime import datetime, timedelta, timezone, date, time
from typing import List, Dict, Any

# Agregar el directorio raíz del backend al path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.services.direct_db_service import direct_db_service

# Configuración
DIAS_DISPONIBLES = 30  # Días futuros a crear disponibilidades
DURACION_SLOT_MINUTOS = 60  # Duración de cada slot en minutos (1 hora)
BATCH_SIZE = 5000  # Tamaño del lote para inserción masiva

async def get_proveedores_con_horarios() -> List[Dict[str, Any]]:
    """Obtiene proveedores que tienen horarios de trabajo configurados"""
    conn = await direct_db_service.get_connection()
    
    try:
        query = """
            SELECT DISTINCT id_proveedor
            FROM horario_trabajo
            WHERE activo = true
        """
        
        proveedores = await conn.fetch(query)
        return [dict(prov) for prov in proveedores]
    finally:
        if conn:
            await direct_db_service.pool.release(conn)

async def get_horarios_proveedor(conn, id_proveedor: int) -> Dict[int, Dict[str, Any]]:
    """Obtiene los horarios de trabajo de un proveedor por día de la semana"""
    query = """
        SELECT dia_semana, hora_inicio, hora_fin, activo
        FROM horario_trabajo
        WHERE id_proveedor = $1 AND activo = true
    """
    
    horarios = await conn.fetch(query, id_proveedor)
    return {row['dia_semana']: dict(row) for row in horarios}

async def get_servicios_proveedor(conn, id_proveedor: int) -> List[int]:
    """Obtiene los IDs de servicios de un proveedor"""
    query = """
        SELECT id_servicio
        FROM servicio
        WHERE id_perfil = $1 AND estado = true
    """
    
    servicios = await conn.fetch(query, id_proveedor)
    return [row['id_servicio'] for row in servicios]

def generar_slots_desde_horario(
    fecha: date,
    hora_inicio: time,
    hora_fin: time,
    duracion_minutos: int
) -> List[tuple]:
    """
    Genera slots de disponibilidad para una fecha y horario específico
    Retorna lista de tuplas (fecha_inicio, fecha_fin) como datetime
    """
    slots = []
    
    # Combinar fecha con hora_inicio
    datetime_inicio = datetime.combine(fecha, hora_inicio)
    datetime_fin_base = datetime.combine(fecha, hora_fin)
    
    # Asegurar timezone UTC
    datetime_inicio = datetime_inicio.replace(tzinfo=timezone.utc)
    datetime_fin_base = datetime_fin_base.replace(tzinfo=timezone.utc)
    
    # Generar slots cada duracion_minutos
    slot_actual = datetime_inicio
    while slot_actual + timedelta(minutes=duracion_minutos) <= datetime_fin_base:
        slot_fin = slot_actual + timedelta(minutes=duracion_minutos)
        slots.append((slot_actual, slot_fin))
        slot_actual = slot_fin
    
    return slots

# Configuración para inserción masiva
BATCH_SIZE = 5000  # Tamaño del lote para inserción masiva

async def populate_from_horarios():
    """Genera disponibilidades basándose en horarios de trabajo"""
    print("🚀 Iniciando generación de disponibilidades desde horarios_trabajo...\n")
    
    # Paso 1: Obtener proveedores con horarios
    print("📊 Obteniendo proveedores con horarios de trabajo...")
    proveedores = await get_proveedores_con_horarios()
    total_proveedores = len(proveedores)
    
    print(f"📊 Proveedores con horarios: {total_proveedores}\n")
    
    if total_proveedores == 0:
        print("⚠️  No hay proveedores con horarios de trabajo configurados")
        return
    
    conn = await direct_db_service.get_connection()
    
    try:
        total_servicios_procesados = 0
        total_disponibilidades_creadas = 0
        
        # Paso 2: Para cada proveedor, obtener sus horarios y servicios
        for i, proveedor in enumerate(proveedores, 1):
            id_proveedor = proveedor['id_proveedor']
            
            print(f"📦 Procesando proveedor {i}/{total_proveedores} (ID: {id_proveedor})...")
            
            # Obtener horarios del proveedor
            horarios_map = await get_horarios_proveedor(conn, id_proveedor)
            
            if not horarios_map:
                print(f"  ⚠️  Proveedor {id_proveedor} no tiene horarios activos")
                continue
            
            # Obtener servicios del proveedor
            servicios_ids = await get_servicios_proveedor(conn, id_proveedor)
            
            if not servicios_ids:
                print(f"  ⚠️  Proveedor {id_proveedor} no tiene servicios activos")
                continue
            
            print(f"  📊 Horarios: {len(horarios_map)} días, Servicios: {len(servicios_ids)}")
            
            # Paso 3: Generar disponibilidades para los próximos N días
            today = date.today()
            all_availability_data = []
            
            # Generar todos los datos primero
            for day_offset in range(DIAS_DISPONIBLES):
                current_date = today + timedelta(days=day_offset)
                dia_semana = current_date.weekday()
                
                # Verificar si hay horario para este día
                if dia_semana not in horarios_map:
                    continue
                
                horario = horarios_map[dia_semana]
                hora_inicio = horario['hora_inicio']
                hora_fin = horario['hora_fin']
                
                # Generar slots para este día
                slots = generar_slots_desde_horario(
                    current_date,
                    hora_inicio,
                    hora_fin,
                    DURACION_SLOT_MINUTOS
                )
                
                # Agregar datos para cada servicio y cada slot
                for id_servicio in servicios_ids:
                    for fecha_inicio, fecha_fin in slots:
                        observaciones = f"Generado desde horario_trabajo - Servicio ID {id_servicio}"
                        all_availability_data.append((
                            id_servicio,
                            fecha_inicio,
                            fecha_fin,
                            True,  # disponible
                            0.0,   # precio_adicional
                            observaciones,
                            datetime.now(timezone.utc),  # created_at
                            datetime.now(timezone.utc)   # updated_at
                        ))
            
            # Insertar en lotes
            if all_availability_data:
                query = """
                    INSERT INTO disponibilidad (
                        id_servicio, fecha_inicio, fecha_fin, disponible,
                        precio_adicional, observaciones, created_at, updated_at
                    )
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                    ON CONFLICT DO NOTHING
                """
                
                num_batches = (len(all_availability_data) + BATCH_SIZE - 1) // BATCH_SIZE
                
                async with conn.transaction():
                    for batch_num in range(num_batches):
                        start_idx = batch_num * BATCH_SIZE
                        end_idx = min((batch_num + 1) * BATCH_SIZE, len(all_availability_data))
                        batch = all_availability_data[start_idx:end_idx]
                        
                        await conn.executemany(query, batch)
                        if batch_num == 0 or (batch_num + 1) % 5 == 0:
                            print(f"  📦 Lote {batch_num + 1}/{num_batches} insertado ({len(batch)} registros)...")
                
                disponibilidades_proveedor = len(all_availability_data)
            else:
                disponibilidades_proveedor = 0
            
            total_servicios_procesados += len(servicios_ids)
            total_disponibilidades_creadas += disponibilidades_proveedor
            print(f"  ✅ {disponibilidades_proveedor} disponibilidades creadas para {len(servicios_ids)} servicios\n")
        
        # Resumen
        print("=" * 60)
        print("📊 RESUMEN")
        print("=" * 60)
        print(f"✅ Proveedores procesados: {total_proveedores}")
        print(f"✅ Servicios procesados: {total_servicios_procesados}")
        print(f"📊 Total disponibilidades creadas: {total_disponibilidades_creadas}")
        print(f"📆 Período: Próximos {DIAS_DISPONIBLES} días")
        print(f"⏰ Duración de slots: {DURACION_SLOT_MINUTOS} minutos")
        print()
        
        # Verificar
        verify = await conn.fetchrow("SELECT COUNT(*) as total FROM disponibilidad")
        print(f"✅ Verificación: {verify['total']} disponibilidades en total en la base de datos")
        
    except Exception as e:
        print(f"❌ Error durante la generación: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        if conn:
            await direct_db_service.pool.release(conn)

if __name__ == "__main__":
    asyncio.run(populate_from_horarios())

