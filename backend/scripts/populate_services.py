#!/usr/bin/env python3
"""
Script para poblar servicios masivamente asociados a categorías y empresas.
Crea servicios variados con descripciones detalladas para probar la búsqueda con IA.

Uso:
    python scripts/populate_services.py
"""

import sys
import os
import asyncio
import json
from datetime import datetime
from typing import List, Dict, Any, Optional
from uuid import UUID

# Agregar el directorio raíz del backend al path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.services.direct_db_service import direct_db_service

# Servicios variados con descripciones detalladas para IA
SERVICIOS_DATA = [
    # CATERING
    {
        "nombre": "Catering para Eventos Corporativos",
        "descripcion": "Servicio completo de catering para eventos corporativos, incluye buffet, bebidas, postres y servicio de meseros. Ideal para conferencias, lanzamientos de productos y reuniones empresariales. Menú personalizable según necesidades del cliente.",
        "precio": 150000,
        "categoria": "Catering",
        "moneda": "PYG"
    },
    {
        "nombre": "Catering para Bodas y Celebraciones",
        "descripcion": "Catering especializado para bodas y celebraciones familiares. Ofrecemos menú gourmet, decoración de mesas, servicio de barra libre y atención personalizada. Incluye degustación previa y coordinación del evento.",
        "precio": 2500000,
        "categoria": "Catering",
        "moneda": "PYG"
    },
    {
        "nombre": "Box Lunch para Reuniones",
        "descripcion": "Servicio de box lunch para reuniones y eventos corporativos. Opciones vegetarianas, veganas y sin gluten disponibles. Incluye bebida, postre y servicio de entrega.",
        "precio": 45000,
        "categoria": "Catering",
        "moneda": "PYG"
    },
    
    # TRANSPORTE
    {
        "nombre": "Transporte Ejecutivo Empresarial",
        "descripcion": "Servicio de transporte ejecutivo para empresas. Vehículos de alta gama, conductores profesionales uniformados, puntualidad garantizada. Ideal para traslados de ejecutivos, clientes importantes y eventos corporativos.",
        "precio": 120000,
        "categoria": "Transporte",
        "moneda": "PYG"
    },
    {
        "nombre": "Alquiler de Microbuses para Eventos",
        "descripcion": "Alquiler de microbuses con capacidad para 20-30 personas. Ideal para traslados grupales, excursiones, eventos deportivos y viajes corporativos. Incluye conductor profesional y seguro de pasajeros.",
        "precio": 300000,
        "categoria": "Transporte",
        "moneda": "PYG"
    },
    {
        "nombre": "Servicio de Mensajería y Encomiendas",
        "descripcion": "Servicio rápido de mensajería y entrega de encomiendas en Asunción y Gran Asunción. Entrega el mismo día, seguimiento en tiempo real y cobertura amplia. Ideal para documentos importantes y paquetes urgentes.",
        "precio": 35000,
        "categoria": "Transporte",
        "moneda": "PYG"
    },
    
    # SALUD
    {
        "nombre": "Consultoría en Salud Ocupacional",
        "descripcion": "Servicios de consultoría en salud ocupacional para empresas. Evaluaciones médicas, programas de prevención, capacitación en seguridad laboral y cumplimiento de normativas. Certificaciones y auditorías incluidas.",
        "precio": 5000000,
        "categoria": "Salud",
        "moneda": "PYG"
    },
    {
        "nombre": "Servicio de Ambulancia y Emergencias",
        "descripcion": "Servicio de ambulancia 24/7 con personal médico capacitado. Equipamiento de última generación, respuesta rápida y traslado seguro a centros médicos. Ideal para eventos, empresas y emergencias domiciliarias.",
        "precio": 800000,
        "categoria": "Salud",
        "moneda": "PYG"
    },
    {
        "nombre": "Chequeos Médicos Preventivos",
        "descripcion": "Paquetes de chequeos médicos preventivos para empresas. Incluye análisis clínicos, electrocardiograma, espirometría y evaluación nutricional. Servicio a domicilio disponible para grupos.",
        "precio": 250000,
        "categoria": "Salud",
        "moneda": "PYG"
    },
    
    # EDUCACIÓN
    {
        "nombre": "Capacitación en Tecnologías de la Información",
        "descripcion": "Cursos y talleres de capacitación en TI para empresas. Programación, bases de datos, ciberseguridad, cloud computing y herramientas de productividad. Modalidad presencial y virtual disponible.",
        "precio": 2000000,
        "categoria": "Educación",
        "moneda": "PYG"
    },
    {
        "nombre": "Capacitación en Liderazgo y Gestión",
        "descripcion": "Programas de desarrollo de liderazgo y habilidades gerenciales. Talleres prácticos, coaching ejecutivo y metodologías probadas. Diseñado para equipos de trabajo y directivos empresariales.",
        "precio": 3500000,
        "categoria": "Educación",
        "moneda": "PYG"
    },
    {
        "nombre": "Idiomas para Empresas",
        "descripcion": "Cursos de idiomas (inglés, portugués, mandarín) para equipos empresariales. Metodología comunicativa, horarios flexibles y certificaciones internacionales. Clases grupales e individuales disponibles.",
        "precio": 1500000,
        "categoria": "Educación",
        "moneda": "PYG"
    },
    
    # TECNOLOGÍA
    {
        "nombre": "Desarrollo de Software a Medida",
        "descripcion": "Desarrollo de aplicaciones web y móviles personalizadas para empresas. Tecnologías modernas, diseño responsive, integración con sistemas existentes y soporte post-lanzamiento. Metodología ágil.",
        "precio": 15000000,
        "categoria": "Tecnología",
        "moneda": "PYG"
    },
    {
        "nombre": "Consultoría en Transformación Digital",
        "descripcion": "Servicios de consultoría para transformación digital empresarial. Análisis de procesos, implementación de soluciones tecnológicas, automatización y optimización de operaciones. Roadmap personalizado.",
        "precio": 8000000,
        "categoria": "Tecnología",
        "moneda": "PYG"
    },
    {
        "nombre": "Soporte Técnico y Mantenimiento IT",
        "descripcion": "Servicio de soporte técnico y mantenimiento de infraestructura IT. Monitoreo 24/7, resolución de incidencias, actualizaciones de seguridad y backup automatizado. Planes mensuales disponibles.",
        "precio": 2500000,
        "categoria": "Tecnología",
        "moneda": "PYG"
    },
    
    # CONSTRUCCIÓN
    {
        "nombre": "Construcción y Remodelación de Oficinas",
        "descripcion": "Servicios completos de construcción y remodelación de espacios comerciales y oficinas. Diseño arquitectónico, construcción, instalaciones eléctricas y sanitarias, acabados de calidad. Proyectos llave en mano.",
        "precio": 50000000,
        "categoria": "Construcción",
        "moneda": "PYG"
    },
    {
        "nombre": "Instalaciones Eléctricas Industriales",
        "descripcion": "Instalación y mantenimiento de sistemas eléctricos para empresas e industrias. Certificaciones, cumplimiento de normativas, sistemas de iluminación LED y eficiencia energética. Servicio de emergencias 24/7.",
        "precio": 12000000,
        "categoria": "Construcción",
        "moneda": "PYG"
    },
    
    # EVENTOS
    {
        "nombre": "Organización Integral de Eventos",
        "descripcion": "Servicio completo de organización de eventos corporativos y sociales. Planificación, coordinación, logística, decoración, catering y entretenimiento. Desde reuniones pequeñas hasta eventos masivos.",
        "precio": 8000000,
        "categoria": "Eventos",
        "moneda": "PYG"
    },
    {
        "nombre": "Alquiler de Equipos para Eventos",
        "descripcion": "Alquiler de equipos audiovisuales, sonido, iluminación, carpas y mobiliario para eventos. Incluye instalación, operación y desmontaje. Equipos de última generación y personal técnico especializado.",
        "precio": 1500000,
        "categoria": "Eventos",
        "moneda": "PYG"
    },
    
    # LIMPIEZA
    {
        "nombre": "Limpieza Profesional de Oficinas",
        "descripcion": "Servicio de limpieza profesional para oficinas y espacios comerciales. Personal capacitado, productos ecológicos, horarios flexibles y servicio de limpieza profunda. Planes diarios, semanales y mensuales.",
        "precio": 800000,
        "categoria": "Limpieza",
        "moneda": "PYG"
    },
    {
        "nombre": "Limpieza Post-Construcción",
        "descripcion": "Servicio especializado de limpieza post-construcción y remodelación. Eliminación de residuos, limpieza profunda, pulido de superficies y preparación para ocupación. Equipos industriales y personal especializado.",
        "precio": 2000000,
        "categoria": "Limpieza",
        "moneda": "PYG"
    }
]

async def get_or_create_moneda(codigo: str, nombre: str, simbolo: str) -> int:
    """Obtiene o crea una moneda."""
    conn = await direct_db_service.get_connection()
    try:
        # Buscar moneda existente
        row = await conn.fetchrow(
            "SELECT id_moneda FROM moneda WHERE codigo_iso_moneda = $1",
            codigo
        )
        if row:
            return row['id_moneda']
        
        # Crear nueva moneda
        row = await conn.fetchrow(
            "INSERT INTO moneda (codigo_iso_moneda, nombre, simbolo) VALUES ($1, $2, $3) RETURNING id_moneda",
            codigo, nombre, simbolo
        )
        return row['id_moneda']
    finally:
        if conn:
            await direct_db_service.pool.release(conn)

async def get_categoria_id(nombre: str) -> Optional[int]:
    """Obtiene el ID de una categoría por nombre."""
    conn = await direct_db_service.get_connection()
    try:
        row = await conn.fetchrow(
            "SELECT id_categoria FROM categoria WHERE nombre = $1 AND estado = true",
            nombre
        )
        return row['id_categoria'] if row else None
    finally:
        if conn:
            await direct_db_service.pool.release(conn)

async def get_perfiles_empresa() -> List[Dict[str, Any]]:
    """Obtiene todos los perfiles de empresa verificados."""
    conn = await direct_db_service.get_connection()
    try:
        rows = await conn.fetch(
            """
            SELECT id_perfil, razon_social, nombre_fantasia, user_id
            FROM perfil_empresa
            WHERE estado = 'ACTIVO' AND verificado = true
            ORDER BY id_perfil
            """
        )
        return [dict(row) for row in rows]
    finally:
        if conn:
            await direct_db_service.pool.release(conn)

async def create_servicio(
    nombre: str,
    descripcion: str,
    precio: float,
    id_categoria: Optional[int],
    id_perfil: int,
    id_moneda: int,
    imagen: Optional[str] = None
) -> int:
    """Crea un servicio."""
    conn = await direct_db_service.get_connection()
    try:
        row = await conn.fetchrow(
            """
            INSERT INTO servicio (nombre, descripcion, precio, id_categoria, id_perfil, id_moneda, imagen, estado)
            VALUES ($1, $2, $3, $4, $5, $6, $7, true)
            RETURNING id_servicio
            """,
            nombre, descripcion, precio, id_categoria, id_perfil, id_moneda, imagen
        )
        return row['id_servicio']
    finally:
        if conn:
            await direct_db_service.pool.release(conn)

async def populate_services():
    """Función principal para poblar servicios."""
    print("🚀 Iniciando población de servicios...\n")
    
    # 1. Obtener o crear monedas
    print("💰 Configurando monedas...")
    id_moneda_pyg = await get_or_create_moneda("PYG", "Guaraní Paraguayo", "₲")
    id_moneda_usd = await get_or_create_moneda("USD", "Dólar Estadounidense", "$")
    print(f"✅ Monedas configuradas: PYG (ID: {id_moneda_pyg}), USD (ID: {id_moneda_usd})\n")
    
    # 2. Obtener perfiles de empresa
    print("🏢 Obteniendo perfiles de empresa...")
    perfiles = await get_perfiles_empresa()
    if not perfiles:
        print("⚠️  No se encontraron perfiles de empresa verificados.")
        print("💡 Necesitas crear perfiles de empresa primero usando el proceso de registro de proveedores.")
        return
    
    print(f"✅ Encontrados {len(perfiles)} perfiles de empresa\n")
    
    # 3. Distribuir servicios entre perfiles
    servicios_creados = 0
    servicios_por_perfil = len(SERVICIOS_DATA) // len(perfiles)
    resto = len(SERVICIOS_DATA) % len(perfiles)
    
    print("📦 Creando servicios...\n")
    
    conn = await direct_db_service.get_connection()
    try:
        async with conn.transaction():
            servicio_idx = 0
            for perfil_idx, perfil in enumerate(perfiles):
                # Calcular cuántos servicios asignar a este perfil
                cantidad = servicios_por_perfil + (1 if perfil_idx < resto else 0)
                
                print(f"🏢 {perfil['razon_social']} ({perfil['nombre_fantasia']}):")
                
                for _ in range(cantidad):
                    if servicio_idx >= len(SERVICIOS_DATA):
                        break
                    
                    servicio_data = SERVICIOS_DATA[servicio_idx]
                    
                    # Obtener categoría
                    id_categoria = await get_categoria_id(servicio_data['categoria'])
                    if not id_categoria:
                        print(f"  ⚠️  Categoría '{servicio_data['categoria']}' no encontrada, saltando servicio '{servicio_data['nombre']}'")
                        servicio_idx += 1
                        continue
                    
                    # Determinar moneda
                    id_moneda = id_moneda_pyg if servicio_data['moneda'] == 'PYG' else id_moneda_usd
                    
                    # Crear servicio
                    id_servicio = await create_servicio(
                        nombre=servicio_data['nombre'],
                        descripcion=servicio_data['descripcion'],
                        precio=servicio_data['precio'],
                        id_categoria=id_categoria,
                        id_perfil=perfil['id_perfil'],
                        id_moneda=id_moneda,
                        imagen=None
                    )
                    
                    print(f"  ✅ {servicio_data['nombre']} (ID: {id_servicio})")
                    servicios_creados += 1
                    servicio_idx += 1
                
                print()
    finally:
        if conn:
            await direct_db_service.pool.release(conn)
    
    print(f"\n✅ Población completada: {servicios_creados} servicios creados")

if __name__ == "__main__":
    asyncio.run(populate_services())

