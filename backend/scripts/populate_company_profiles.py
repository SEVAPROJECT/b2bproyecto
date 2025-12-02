#!/usr/bin/env python3
"""
Script para crear perfiles de empresa completos.
Primero crea usuarios en Supabase Auth, luego crea los perfiles de empresa asociados.

Uso:
    python scripts/populate_company_profiles.py
"""

import sys
import os
import asyncio
from datetime import datetime
from typing import List, Dict, Any, Optional
from uuid import UUID

# Agregar el directorio raíz del backend al path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.services.direct_db_service import direct_db_service
from app.supabase.auth_service import supabase_admin
from app.core.config import SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY

# Datos de empresas de ejemplo
EMPRESAS_DATA = [
    {
        "email": "catering.deluxe@example.com",
        "password": "Catering123!",
        "nombre_persona": "María González",
        "nombre_empresa": "Catering Deluxe S.A.",
        "ruc": "80012345-1",
        "razon_social": "Catering Deluxe Sociedad Anónima",
        "nombre_fantasia": "Catering Deluxe",
        "departamento": "Central",
        "ciudad": "San Lorenzo",
        "barrio": "Barcequillo",
        "calle": "Av. Mariscal López",
        "numero": "1234",
        "referencia": "Cerca del Shopping del Sol"
    },
    {
        "email": "transporte.executivo@example.com",
        "password": "Transporte123!",
        "nombre_persona": "Carlos Ramírez",
        "nombre_empresa": "Transporte Ejecutivo S.R.L.",
        "ruc": "80023456-2",
        "razon_social": "Transporte Ejecutivo Sociedad de Responsabilidad Limitada",
        "nombre_fantasia": "Transporte Ejecutivo",
        "departamento": "Asunción",
        "ciudad": "Asunción",
        "barrio": "Villa Morra",
        "calle": "Av. España",
        "numero": "567",
        "referencia": "Frente al Shopping Mariscal"
    },
    {
        "email": "salud.ocupacional@example.com",
        "password": "Salud123!",
        "nombre_persona": "Ana Martínez",
        "nombre_empresa": "Salud Ocupacional Integral S.A.",
        "ruc": "80034567-3",
        "razon_social": "Salud Ocupacional Integral Sociedad Anónima",
        "nombre_fantasia": "Salud Ocupacional Integral",
        "departamento": "Central",
        "ciudad": "Fernando de la Mora",
        "barrio": "Centro",
        "calle": "Av. Mariscal Estigarribia",
        "numero": "890",
        "referencia": "Cerca del Hospital Bautista"
    },
    {
        "email": "educacion.tech@example.com",
        "password": "Educacion123!",
        "nombre_persona": "Roberto Silva",
        "nombre_empresa": "Educación Tech Paraguay S.A.",
        "ruc": "80045678-4",
        "razon_social": "Educación Tech Paraguay Sociedad Anónima",
        "nombre_fantasia": "Educación Tech",
        "departamento": "Asunción",
        "ciudad": "Asunción",
        "barrio": "Centro",
        "calle": "Av. Palma",
        "numero": "234",
        "referencia": "Edificio Plaza Uruguaya"
    },
    {
        "email": "desarrollo.software@example.com",
        "password": "Software123!",
        "nombre_persona": "Laura Fernández",
        "nombre_empresa": "Desarrollo Software Solutions S.A.",
        "ruc": "80056789-5",
        "razon_social": "Desarrollo Software Solutions Sociedad Anónima",
        "nombre_fantasia": "DevSolutions",
        "departamento": "Central",
        "ciudad": "Luque",
        "barrio": "Centro",
        "calle": "Av. Aviadores del Chaco",
        "numero": "1234",
        "referencia": "Cerca del Aeropuerto"
    },
    {
        "email": "construccion.expertos@example.com",
        "password": "Construccion123!",
        "nombre_persona": "Pedro Benítez",
        "nombre_empresa": "Construcción Expertos S.R.L.",
        "ruc": "80067890-6",
        "razon_social": "Construcción Expertos Sociedad de Responsabilidad Limitada",
        "nombre_fantasia": "Construcción Expertos",
        "departamento": "Central",
        "ciudad": "San Lorenzo",
        "barrio": "Centro",
        "calle": "Av. Mcal. López",
        "numero": "2345",
        "referencia": "Frente a la Universidad"
    },
    {
        "email": "eventos.premium@example.com",
        "password": "Eventos123!",
        "nombre_persona": "Sofía Rojas",
        "nombre_empresa": "Eventos Premium S.A.",
        "ruc": "80078901-7",
        "razon_social": "Eventos Premium Sociedad Anónima",
        "nombre_fantasia": "Eventos Premium",
        "departamento": "Asunción",
        "ciudad": "Asunción",
        "barrio": "Villa Morra",
        "calle": "Av. Aviadores del Chaco",
        "numero": "3456",
        "referencia": "Cerca del Shopping Multiplaza"
    },
    {
        "email": "limpieza.profesional@example.com",
        "password": "Limpieza123!",
        "nombre_persona": "Miguel Torres",
        "nombre_empresa": "Limpieza Profesional S.R.L.",
        "ruc": "80089012-8",
        "razon_social": "Limpieza Profesional Sociedad de Responsabilidad Limitada",
        "nombre_fantasia": "Limpieza Pro",
        "departamento": "Central",
        "ciudad": "Fernando de la Mora",
        "barrio": "Centro",
        "calle": "Av. Defensores del Chaco",
        "numero": "4567",
        "referencia": "Cerca del Supermercado"
    }
]

async def get_departamento_id(nombre: str) -> Optional[int]:
    """Obtiene el ID de un departamento."""
    conn = await direct_db_service.get_connection()
    try:
        row = await conn.fetchrow(
            "SELECT id_departamento FROM departamento WHERE nombre = $1",
            nombre
        )
        return row['id_departamento'] if row else None
    finally:
        if conn:
            await direct_db_service.pool.release(conn)

async def get_ciudad_id(nombre: str, id_departamento: int) -> Optional[int]:
    """Obtiene el ID de una ciudad."""
    conn = await direct_db_service.get_connection()
    try:
        row = await conn.fetchrow(
            "SELECT id_ciudad FROM ciudad WHERE nombre = $1 AND id_departamento = $2",
            nombre, id_departamento
        )
        return row['id_ciudad'] if row else None
    finally:
        if conn:
            await direct_db_service.pool.release(conn)

async def get_barrio_id(nombre: str, id_ciudad: int) -> Optional[int]:
    """Obtiene el ID de un barrio."""
    conn = await direct_db_service.get_connection()
    try:
        row = await conn.fetchrow(
            "SELECT id_barrio FROM barrio WHERE nombre = $1 AND id_ciudad = $2",
            nombre, id_ciudad
        )
        return row['id_barrio'] if row else None
    finally:
        if conn:
            await direct_db_service.pool.release(conn)

async def create_direccion(
    calle: str,
    numero: str,
    referencia: str,
    id_departamento: Optional[int],
    id_ciudad: Optional[int],
    id_barrio: Optional[int],
    lat: float = -25.3398,  # Coordenadas por defecto (Asunción)
    lon: float = -57.5086
) -> int:
    """Crea una dirección con coordenadas."""
    conn = await direct_db_service.get_connection()
    try:
        # Crear punto geográfico usando PostGIS
        row = await conn.fetchrow(
            """
            INSERT INTO direccion (calle, numero, referencia, id_departamento, id_ciudad, id_barrio, coordenadas)
            VALUES ($1, $2, $3, $4, $5, $6, ST_SetSRID(ST_MakePoint($7, $8), 4326))
            RETURNING id_direccion
            """,
            calle, numero, referencia, id_departamento, id_ciudad, id_barrio, lon, lat
        )
        return row['id_direccion']
    finally:
        if conn:
            await direct_db_service.pool.release(conn)

async def create_user_in_db(user_id: UUID, nombre_persona: str, nombre_empresa: str, ruc: str) -> bool:
    """Crea el registro en la tabla users si no existe."""
    conn = await direct_db_service.get_connection()
    try:
        # Verificar si ya existe
        existing = await conn.fetchrow(
            "SELECT id FROM users WHERE id = $1",
            user_id
        )
        if existing:
            return True
        
        # Crear registro
        await conn.execute(
            """
            INSERT INTO users (id, nombre_persona, nombre_empresa, ruc, estado)
            VALUES ($1, $2, $3, $4, 'ACTIVO')
            ON CONFLICT (id) DO NOTHING
            """,
            user_id, nombre_persona, nombre_empresa, ruc
        )
        return True
    finally:
        if conn:
            await direct_db_service.pool.release(conn)

async def create_perfil_empresa(
    user_id: UUID,
    razon_social: str,
    nombre_fantasia: str,
    id_direccion: Optional[int],
    verificado: bool = True
) -> int:
    """Crea un perfil de empresa."""
    conn = await direct_db_service.get_connection()
    try:
        row = await conn.fetchrow(
            """
            INSERT INTO perfil_empresa (user_id, razon_social, nombre_fantasia, estado, verificado, fecha_verificacion, id_direccion)
            VALUES ($1, $2, $3, 'ACTIVO', $4, NOW(), $5)
            RETURNING id_perfil
            """,
            user_id, razon_social, nombre_fantasia, verificado, id_direccion
        )
        return row['id_perfil']
    finally:
        if conn:
            await direct_db_service.pool.release(conn)

async def create_company_profile(empresa_data: Dict[str, Any]) -> Dict[str, Any]:
    """Crea un perfil de empresa completo."""
    print(f"\n🏢 Creando perfil para: {empresa_data['razon_social']}")
    
    # 1. Crear usuario en Supabase Auth
    if not supabase_admin:
        raise Exception("❌ Supabase Admin no está configurado. Verifica SUPABASE_SERVICE_ROLE_KEY")
    
    print(f"  📧 Creando usuario en Supabase Auth: {empresa_data['email']}")
    try:
        auth_response = supabase_admin.auth.admin.create_user({
            "email": empresa_data['email'],
            "password": empresa_data['password'],
            "email_confirm": True,  # Confirmar email automáticamente
            "user_metadata": {
                "nombre_persona": empresa_data['nombre_persona'],
                "nombre_empresa": empresa_data['nombre_empresa'],
                "ruc": empresa_data['ruc']
            }
        })
        
        if not auth_response.user:
            raise Exception("No se pudo crear el usuario en Supabase Auth")
        
        user_id = UUID(auth_response.user.id)
        print(f"  ✅ Usuario creado en Auth: {user_id}")
    except Exception as e:
        if "already registered" in str(e).lower() or "already exists" in str(e).lower():
            print(f"  ⚠️  Usuario ya existe, obteniendo ID...")
            # Intentar obtener el usuario existente
            try:
                users = supabase_admin.auth.admin.list_users()
                user = next((u for u in users.users if u.email == empresa_data['email']), None)
                if user:
                    user_id = UUID(user.id)
                    print(f"  ✅ Usuario encontrado: {user_id}")
                else:
                    raise Exception(f"No se pudo encontrar el usuario existente: {empresa_data['email']}")
            except Exception as e2:
                raise Exception(f"Error al obtener usuario existente: {e2}")
        else:
            raise
    
    # 2. Esperar un momento para que el trigger cree el registro en users
    await asyncio.sleep(1)
    
    # 3. Crear registro en tabla users si no existe (por si el trigger no funcionó)
    print(f"  👤 Creando registro en tabla users...")
    await create_user_in_db(
        user_id,
        empresa_data['nombre_persona'],
        empresa_data['nombre_empresa'],
        empresa_data['ruc']
    )
    print(f"  ✅ Registro en users creado/verificado")
    
    # 4. Obtener IDs de ubicación
    print(f"  📍 Obteniendo datos de ubicación...")
    id_departamento = await get_departamento_id(empresa_data['departamento'])
    if not id_departamento:
        print(f"  ⚠️  Departamento '{empresa_data['departamento']}' no encontrado")
        id_departamento = None
    
    id_ciudad = None
    if id_departamento:
        id_ciudad = await get_ciudad_id(empresa_data['ciudad'], id_departamento)
        if not id_ciudad:
            print(f"  ⚠️  Ciudad '{empresa_data['ciudad']}' no encontrada")
    
    id_barrio = None
    if id_ciudad:
        id_barrio = await get_barrio_id(empresa_data['barrio'], id_ciudad)
        if not id_barrio:
            print(f"  ⚠️  Barrio '{empresa_data['barrio']}' no encontrado")
    
    # 5. Crear dirección
    print(f"  🏠 Creando dirección...")
    id_direccion = await create_direccion(
        calle=empresa_data['calle'],
        numero=empresa_data['numero'],
        referencia=empresa_data['referencia'],
        id_departamento=id_departamento,
        id_ciudad=id_ciudad,
        id_barrio=id_barrio
    )
    print(f"  ✅ Dirección creada (ID: {id_direccion})")
    
    # 6. Crear perfil de empresa
    print(f"  🏢 Creando perfil de empresa...")
    id_perfil = await create_perfil_empresa(
        user_id=user_id,
        razon_social=empresa_data['razon_social'],
        nombre_fantasia=empresa_data['nombre_fantasia'],
        id_direccion=id_direccion,
        verificado=True
    )
    print(f"  ✅ Perfil de empresa creado (ID: {id_perfil})")
    
    return {
        "user_id": user_id,
        "id_perfil": id_perfil,
        "email": empresa_data['email'],
        "razon_social": empresa_data['razon_social']
    }

async def populate_company_profiles():
    """Función principal para poblar perfiles de empresa."""
    print("🚀 Iniciando creación de perfiles de empresa...\n")
    
    if not supabase_admin:
        print("❌ Error: Supabase Admin no está configurado.")
        print("💡 Verifica que SUPABASE_SERVICE_ROLE_KEY esté configurado en .env")
        return
    
    perfiles_creados = []
    errores = []
    
    for empresa_data in EMPRESAS_DATA:
        try:
            resultado = await create_company_profile(empresa_data)
            perfiles_creados.append(resultado)
        except Exception as e:
            error_msg = f"Error creando {empresa_data['razon_social']}: {str(e)}"
            print(f"  ❌ {error_msg}")
            errores.append(error_msg)
    
    # Resumen
    print("\n" + "="*60)
    print("📊 RESUMEN")
    print("="*60)
    print(f"✅ Perfiles creados exitosamente: {len(perfiles_creados)}")
    print(f"❌ Errores: {len(errores)}")
    
    if perfiles_creados:
        print("\n📋 Perfiles creados:")
        for perfil in perfiles_creados:
            print(f"  - {perfil['razon_social']} (ID: {perfil['id_perfil']}, Email: {perfil['email']})")
    
    if errores:
        print("\n⚠️  Errores encontrados:")
        for error in errores:
            print(f"  - {error}")

if __name__ == "__main__":
    asyncio.run(populate_company_profiles())



