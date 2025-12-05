#!/usr/bin/env python3
"""
Script para poblar cientos de servicios masivamente asociados a categorías y empresas.
Genera servicios variados con descripciones detalladas para probar la búsqueda con IA.

Uso:
    python scripts/populate_many_services.py
"""

import sys
import os
import asyncio
import random
from typing import List, Dict, Any, Optional
from uuid import UUID

# Agregar el directorio raíz del backend al path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.services.direct_db_service import direct_db_service

# Plantillas de servicios por categoría con variaciones
SERVICIOS_TEMPLATES = {
    "Catering": [
        ("Catering para {tipo_evento}", "Servicio completo de catering para {tipo_evento}. Incluye buffet gourmet, bebidas premium, postres artesanales y servicio de meseros profesionales. Menú personalizable según necesidades del cliente. Ideal para {contexto}."),
        ("Box Lunch {tipo_empresa}", "Servicio de box lunch para {tipo_empresa}. Opciones vegetarianas, veganas, sin gluten y keto disponibles. Incluye bebida natural, postre saludable y servicio de entrega puntual."),
        ("Catering {tipo_comida} para {tipo_evento}", "Catering especializado en {tipo_comida} para {tipo_evento}. Chef especializado, ingredientes frescos, presentación elegante. Incluye coordinación completa del evento."),
    ],
    "Transporte": [
        ("Transporte {tipo_vehiculo} para {tipo_servicio}", "Servicio de transporte {tipo_vehiculo} para {tipo_servicio}. Vehículos {condicion}, conductores profesionales, puntualidad garantizada. Ideal para {contexto}."),
        ("Alquiler de {tipo_vehiculo} con {capacidad}", "Alquiler de {tipo_vehiculo} con capacidad para {capacidad} personas. Incluye conductor profesional, seguro de pasajeros y {extras}. Perfecto para {contexto}."),
        ("Servicio de {tipo_mensajeria} {tipo_entrega}", "Servicio de {tipo_mensajeria} {tipo_entrega} en {cobertura}. Entrega {tiempo_entrega}, seguimiento en tiempo real y cobertura amplia. Ideal para {contexto}."),
    ],
    "Salud": [
        ("Consultoría en {area_salud} para {tipo_empresa}", "Servicios de consultoría en {area_salud} para {tipo_empresa}. {servicios_incluidos}. Certificaciones y auditorías incluidas. Cumplimiento de normativas garantizado."),
        ("Servicio de {tipo_servicio_salud} {disponibilidad}", "Servicio de {tipo_servicio_salud} {disponibilidad} con personal médico capacitado. Equipamiento de última generación, respuesta rápida y {caracteristicas}."),
        ("Programa de {tipo_programa} para {tipo_empresa}", "Programa completo de {tipo_programa} para {tipo_empresa}. Incluye {componentes}. Servicio {modalidad} disponible. Resultados medibles y reportes detallados."),
    ],
    "Educación": [
        ("Capacitación en {tema_tecnologia} para {tipo_audiencia}", "Cursos y talleres de capacitación en {tema_tecnologia} para {tipo_audiencia}. {metodologia}, certificaciones reconocidas. Modalidad {modalidad} disponible."),
        ("Programa de {tipo_programa_educacion} {nivel}", "Programa completo de {tipo_programa_educacion} {nivel}. {contenido}. Diseñado para {tipo_audiencia}. Metodología práctica y casos de estudio reales."),
        ("Curso de {idioma} {nivel} para {tipo_empresa}", "Curso de {idioma} {nivel} para {tipo_empresa}. Metodología comunicativa, horarios flexibles y certificaciones internacionales. Clases {modalidad_clases} disponibles."),
    ],
    "Tecnología": [
        ("Desarrollo de {tipo_aplicacion} {plataforma}", "Desarrollo de {tipo_aplicacion} {plataforma} personalizadas para empresas. Tecnologías {tecnologias}, diseño {caracteristicas_diseno}, integración con sistemas existentes."),
        ("Consultoría en {area_tecnologia} para {tipo_empresa}", "Servicios de consultoría en {area_tecnologia} para {tipo_empresa}. {servicios_especificos}. Roadmap personalizado y acompañamiento en la implementación."),
        ("Soporte Técnico {tipo_soporte} para {tipo_infraestructura}", "Servicio de soporte técnico {tipo_soporte} para {tipo_infraestructura}. Monitoreo {disponibilidad}, resolución de incidencias, {servicios_adicionales}. Planes {tipo_plan} disponibles."),
    ],
    "Construcción": [
        ("Construcción de {tipo_espacio} {caracteristicas}", "Servicios completos de construcción de {tipo_espacio} {caracteristicas}. Diseño arquitectónico, construcción, {instalaciones} y acabados de calidad. Proyectos {tipo_proyecto}."),
        ("Instalaciones {tipo_instalacion} {nivel}", "Instalación y mantenimiento de sistemas {tipo_instalacion} {nivel}. Certificaciones, cumplimiento de normativas, {caracteristicas_especiales}. Servicio de emergencias {disponibilidad}."),
        ("Remodelación de {tipo_espacio} {estilo}", "Remodelación completa de {tipo_espacio} {estilo}. {servicios_incluidos}. Presupuesto detallado, cronograma garantizado y supervisión profesional."),
    ],
    "Eventos": [
        ("Organización de {tipo_evento} {tamaño}", "Servicio completo de organización de {tipo_evento} {tamaño}. Planificación detallada, coordinación, logística, {servicios_adicionales}. Desde {tipo_minimo} hasta {tipo_maximo}."),
        ("Alquiler de {tipo_equipo} para {tipo_evento}", "Alquiler de {tipo_equipo} para {tipo_evento}. Equipos de última generación, {servicios_incluidos}. Personal técnico especializado y soporte durante el evento."),
        ("Producción de {tipo_produccion} {caracteristicas}", "Producción completa de {tipo_produccion} {caracteristicas}. {servicios_incluidos}. Experiencia en {tipos_eventos} y atención personalizada."),
    ],
    "Limpieza": [
        ("Limpieza {tipo_limpieza} de {tipo_espacio}", "Servicio de limpieza {tipo_limpieza} de {tipo_espacio}. Personal capacitado, productos {tipo_productos}, horarios flexibles. Planes {tipo_plan} disponibles."),
        ("Limpieza {tipo_especializada} {contexto}", "Servicio especializado de limpieza {tipo_especializada} {contexto}. {metodos_especiales}, equipos industriales y personal especializado. Resultados garantizados."),
        ("Mantenimiento de {tipo_mantenimiento} para {tipo_espacio}", "Servicio de mantenimiento de {tipo_mantenimiento} para {tipo_espacio}. {servicios_incluidos}. Frecuencia {frecuencia} y reportes detallados de limpieza."),
    ]
}

# Valores para rellenar las plantillas
VALORES_VARIABLES = {
    "tipo_evento": ["Eventos Corporativos", "Bodas y Celebraciones", "Cumpleaños", "Aniversarios", "Lanzamientos", "Conferencias", "Seminarios", "Workshops", "Reuniones Ejecutivas", "Cenas de Gala"],
    "contexto": ["empresas multinacionales", "pequeñas y medianas empresas", "instituciones educativas", "organizaciones sin fines de lucro", "eventos gubernamentales", "celebración familiar", "eventos deportivos", "festivales culturales"],
    "tipo_empresa": ["empresas", "instituciones", "organizaciones", "colegios", "universidades", "hospitales", "hoteles", "restaurantes"],
    "tipo_comida": ["Italiana", "Asiática", "Mediterránea", "Paraguaya", "Internacional", "Vegetariana", "Vegana", "Sin Gluten", "Gourmet", "Casera"],
    "tipo_vehiculo": ["Ejecutivo", "Premium", "Lujo", "Económico", "SUV", "Van", "Microbús", "Ómnibus", "Motocicleta", "Bicicleta"],
    "condicion": ["nuevos", "semi-nuevos", "de alta gama", "confortables", "espaciosos", "modernos"],
    "capacidad": ["4-6", "8-12", "15-20", "20-30", "30-40", "40-50"],
    "extras": ["aire acondicionado", "WiFi", "entretenimiento", "refrigerador", "asientos reclinables"],
    "tipo_mensajeria": ["Mensajería", "Encomiendas", "Paquetería", "Documentos", "Alimentos", "Farmacéuticos"],
    "tipo_entrega": ["Express", "Urgente", "Programada", "Económica", "Premium"],
    "cobertura": ["Asunción", "Gran Asunción", "todo el país", "zona metropolitana", "área rural"],
    "tiempo_entrega": ["el mismo día", "en 2 horas", "en 24 horas", "programada", "inmediata"],
    "area_salud": ["Salud Ocupacional", "Medicina Preventiva", "Ergonomía", "Psicología Laboral", "Nutrición Empresarial", "Fisioterapia", "Seguridad Industrial"],
    "servicios_incluidos": ["Evaluaciones médicas", "Programas de prevención", "Capacitación en seguridad", "Análisis de riesgos", "Chequeos periódicos", "Vacunación", "Primeros auxilios"],
    "tipo_servicio_salud": ["Ambulancia", "Emergencias", "Chequeos Médicos", "Vacunación", "Fisioterapia", "Psicología", "Nutrición"],
    "disponibilidad": ["24/7", "en horario laboral", "fines de semana", "emergencias", "domiciliario"],
    "caracteristicas": ["traslado seguro", "atención personalizada", "equipamiento completo", "personal certificado"],
    "tipo_programa": ["Bienestar Laboral", "Prevención de Riesgos", "Salud Mental", "Nutrición", "Ejercicio", "Desintoxicación"],
    "componentes": ["evaluaciones", "talleres", "seguimiento", "reportes", "certificaciones"],
    "modalidad": ["presencial", "virtual", "híbrida", "a domicilio"],
    "tema_tecnologia": ["Programación", "Bases de Datos", "Ciberseguridad", "Cloud Computing", "Inteligencia Artificial", "Machine Learning", "DevOps", "Diseño UX/UI", "Marketing Digital", "Análisis de Datos"],
    "tipo_audiencia": ["desarrolladores", "gerentes", "equipos técnicos", "ejecutivos", "estudiantes", "profesionales"],
    "metodologia": ["práctica", "teórico-práctica", "basada en proyectos", "con certificación", "intensiva"],
    "tipo_programa_educacion": ["Desarrollo de Liderazgo", "Habilidades Blandas", "Gestión de Proyectos", "Comunicación Efectiva", "Trabajo en Equipo", "Innovación", "Emprendimiento"],
    "nivel": ["Básico", "Intermedio", "Avanzado", "Ejecutivo", "Especializado"],
    "contenido": ["talleres interactivos", "casos de estudio", "simulaciones", "role playing", "coaching personalizado"],
    "idioma": ["Inglés", "Portugués", "Mandarín", "Francés", "Alemán", "Italiano"],
    "modalidad_clases": ["grupales", "individuales", "intensivas", "extensivas"],
    "tipo_aplicacion": ["Aplicaciones Web", "Aplicaciones Móviles", "Sistemas ERP", "Plataformas E-commerce", "Dashboards", "APIs", "Microservicios"],
    "plataforma": ["Web", "iOS", "Android", "Multiplataforma", "Desktop"],
    "tecnologias": ["modernas", "escalables", "seguras", "cloud-native"],
    "caracteristicas_diseno": ["responsive", "intuitivo", "moderno", "accesible"],
    "area_tecnologia": ["Transformación Digital", "Cloud Computing", "Ciberseguridad", "Big Data", "IoT", "Blockchain", "Automatización"],
    "servicios_especificos": ["Análisis de procesos", "Implementación de soluciones", "Automatización", "Optimización", "Migración a la nube"],
    "tipo_soporte": ["Técnico", "Especializado", "Preventivo", "Correctivo"],
    "tipo_infraestructura": ["IT", "Redes", "Servidores", "Aplicaciones", "Bases de Datos"],
    "servicios_adicionales": ["actualizaciones de seguridad", "backup automatizado", "monitoreo proactivo", "optimización continua"],
    "tipo_plan": ["mensuales", "anuales", "por incidente", "premium"],
    "tipo_espacio": ["Oficinas", "Locales Comerciales", "Almacenes", "Fábricas", "Centros de Distribución", "Showrooms", "Restaurantes", "Hoteles"],
    "caracteristicas": ["modernas", "sustentables", "inteligentes", "eficientes", "acogedoras"],
    "instalaciones": ["eléctricas", "sanitarias", "climatización", "iluminación LED", "sistemas de seguridad"],
    "tipo_proyecto": ["llave en mano", "por etapas", "personalizados"],
    "tipo_instalacion": ["Eléctricas", "Sanitarias", "Climatización", "Iluminación", "Seguridad", "Comunicaciones"],
    "caracteristicas_especiales": ["eficiencia energética", "sistemas inteligentes", "automatización", "certificaciones verdes"],
    "estilo": ["moderno", "clásico", "minimalista", "industrial", "corporativo", "hospitalario"],
    "servicios_incluidos": ["diseño", "demolición", "construcción", "instalaciones", "acabados", "decoración"],
    "tamaño": ["pequeños", "medianos", "grandes", "masivos", "exclusivos"],
    "servicios_adicionales": ["decoración", "entretenimiento", "fotografía", "video", "streaming"],
    "tipo_minimo": ["reuniones íntimas", "eventos pequeños"],
    "tipo_maximo": ["eventos masivos", "convenciones internacionales"],
    "tipo_equipo": ["Audiovisuales", "Sonido", "Iluminación", "Escenarios", "Carpas", "Mobiliario", "Cocina Móvil"],
    "tipo_produccion": ["Eventos", "Videos Corporativos", "Streaming", "Transmisiones", "Grabaciones"],
    "tipos_eventos": ["corporativos", "sociales", "culturales", "deportivos"],
    "tipo_limpieza": ["Profesional", "Especializada", "Profunda", "Rutinaria", "Post-Construcción", "Industrial"],
    "tipo_espacio": ["Oficinas", "Locales", "Almacenes", "Fábricas", "Hospitales", "Escuelas", "Hoteles"],
    "tipo_productos": ["ecológicos", "biodegradables", "premium", "certificados"],
    "tipo_plan": ["diarios", "semanales", "mensuales", "por evento"],
    "tipo_especializada": ["Post-Construcción", "Industrial", "Hospitalaria", "Alfombras", "Vidrios", "Fachadas"],
    "metodos_especiales": ["vapor", "ultrasonido", "presión", "químicos especializados"],
    "tipo_mantenimiento": ["Limpieza", "Conservación", "Sanitización", "Desinfección"],
    "frecuencia": ["diaria", "semanal", "quincenal", "mensual", "según necesidad"]
}

def generar_servicio(categoria: str) -> Dict[str, Any]:
    """Genera un servicio aleatorio para una categoría."""
    if categoria not in SERVICIOS_TEMPLATES:
        return None
    
    template_nombre, template_descripcion = random.choice(SERVICIOS_TEMPLATES[categoria])
    
    # Rellenar plantilla de nombre
    nombre = template_nombre
    for key, values in VALORES_VARIABLES.items():
        if f"{{{key}}}" in nombre:
            nombre = nombre.replace(f"{{{key}}}", random.choice(values))
    
    # Rellenar plantilla de descripción
    descripcion = template_descripcion
    for key, values in VALORES_VARIABLES.items():
        if f"{{{key}}}" in descripcion:
            descripcion = descripcion.replace(f"{{{key}}}", random.choice(values))
    
    # Generar precio aleatorio según categoría
    precios_base = {
        "Catering": (50000, 5000000),
        "Transporte": (30000, 500000),
        "Salud": (200000, 10000000),
        "Educación": (500000, 5000000),
        "Tecnología": (2000000, 20000000),
        "Construcción": (5000000, 100000000),
        "Eventos": (1000000, 15000000),
        "Limpieza": (200000, 3000000)
    }
    
    precio_min, precio_max = precios_base.get(categoria, (50000, 1000000))
    precio = random.randint(precio_min, precio_max)
    
    return {
        "nombre": nombre,
        "descripcion": descripcion,
        "precio": precio,
        "categoria": categoria,
        "moneda": "PYG"
    }

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

async def get_or_create_moneda(codigo: str, nombre: str, simbolo: str) -> int:
    """Obtiene o crea una moneda."""
    conn = await direct_db_service.get_connection()
    try:
        row = await conn.fetchrow(
            "SELECT id_moneda FROM moneda WHERE codigo_iso_moneda = $1",
            codigo
        )
        if row:
            return row['id_moneda']
        
        row = await conn.fetchrow(
            "INSERT INTO moneda (codigo_iso_moneda, nombre, simbolo) VALUES ($1, $2, $3) RETURNING id_moneda",
            codigo, nombre, simbolo
        )
        return row['id_moneda']
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

async def populate_many_services(num_servicios: int = 200):
    """Función principal para poblar muchos servicios."""
    print(f"🚀 Iniciando población de {num_servicios} servicios...\n")
    
    # 1. Obtener o crear monedas
    print("💰 Configurando monedas...")
    id_moneda_pyg = await get_or_create_moneda("PYG", "Guaraní Paraguayo", "₲")
    print(f"✅ Moneda PYG configurada (ID: {id_moneda_pyg})\n")
    
    # 2. Obtener categorías
    print("📂 Obteniendo categorías...")
    categorias = {}
    categorias_nombres = ["Catering", "Transporte", "Salud", "Educación", "Tecnología", "Construcción", "Eventos", "Limpieza"]
    for cat_nombre in categorias_nombres:
        cat_id = await get_categoria_id(cat_nombre)
        if cat_id:
            categorias[cat_nombre] = cat_id
            print(f"  ✅ {cat_nombre} (ID: {cat_id})")
    print()
    
    if not categorias:
        print("❌ No se encontraron categorías. Ejecuta primero bulk_insert_data.py")
        return
    
    # 3. Obtener perfiles de empresa
    print("🏢 Obteniendo perfiles de empresa...")
    perfiles = await get_perfiles_empresa()
    if not perfiles:
        print("⚠️  No se encontraron perfiles de empresa verificados.")
        print("💡 Ejecuta primero populate_company_profiles.py")
        return
    
    print(f"✅ Encontrados {len(perfiles)} perfiles de empresa\n")
    
    # 4. Generar servicios
    print(f"📦 Generando y creando {num_servicios} servicios...\n")
    
    servicios_creados = 0
    servicios_por_categoria = {}
    
    conn = await direct_db_service.get_connection()
    try:
        async with conn.transaction():
            for i in range(num_servicios):
                # Seleccionar categoría aleatoria
                categoria_nombre = random.choice(list(categorias.keys()))
                id_categoria = categorias[categoria_nombre]
                
                # Generar servicio
                servicio_data = generar_servicio(categoria_nombre)
                if not servicio_data:
                    continue
                
                # Seleccionar perfil aleatorio
                perfil = random.choice(perfiles)
                
                # Crear servicio
                id_servicio = await create_servicio(
                    nombre=servicio_data['nombre'],
                    descripcion=servicio_data['descripcion'],
                    precio=servicio_data['precio'],
                    id_categoria=id_categoria,
                    id_perfil=perfil['id_perfil'],
                    id_moneda=id_moneda_pyg,
                    imagen=None
                )
                
                servicios_creados += 1
                if categoria_nombre not in servicios_por_categoria:
                    servicios_por_categoria[categoria_nombre] = 0
                servicios_por_categoria[categoria_nombre] += 1
                
                # Mostrar progreso cada 50 servicios
                if servicios_creados % 50 == 0:
                    print(f"  ✅ {servicios_creados} servicios creados...")
    finally:
        if conn:
            await direct_db_service.pool.release(conn)
    
    # Resumen
    print(f"\n✅ Población completada: {servicios_creados} servicios creados\n")
    print("📊 Distribución por categoría:")
    for cat, cantidad in sorted(servicios_por_categoria.items()):
        print(f"  - {cat}: {cantidad} servicios")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='Poblar servicios masivamente')
    parser.add_argument('--cantidad', type=int, default=200, help='Número de servicios a crear (default: 200)')
    args = parser.parse_args()
    
    asyncio.run(populate_many_services(args.cantidad))




