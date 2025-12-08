# app/repositories/providers/provider_repository.py
"""
Repositorio unificado para acceso a datos de proveedores.
Centraliza todas las consultas a la base de datos.
Capa de Acceso a Datos (Data Access Layer).
"""

import uuid
from typing import Optional
import asyncpg
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.services.direct_db_service import direct_db_service
from app.models.empresa.perfil_empresa import PerfilEmpresa
from app.models.empresa.verificacion_solicitud import VerificacionSolicitud
from app.api.v1.routers.providers.constants import (
    MSG_PERFIL_USUARIO_NO_ENCONTRADO,
    MSG_RAZON_SOCIAL_NO_CONFIGURADA,
    MSG_EMPRESA_YA_REGISTRADA,
    MSG_DEPARTAMENTO_NO_ENCONTRADO,
    MSG_CIUDAD_NO_ENCONTRADA
)
from fastapi import HTTPException, status


class ProviderRepository:
    """
    Repositorio para acceso a datos de proveedores.
    Responsabilidad: Abstraer el acceso a la base de datos.
    """
    
    @staticmethod
    async def get_user_profile(user_id: str):
        """
        Obtiene y valida el perfil de usuario.
        Retorna un objeto compatible con UserModel.
        """
        conn = None
        try:
            conn = await direct_db_service.get_connection()
            
            user_query = """
                SELECT id, nombre_persona, nombre_empresa, ruc, foto_perfil, estado
                FROM users
                WHERE id = $1
            """
            user_row = await conn.fetchrow(user_query, user_id)
            
            if not user_row:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=MSG_PERFIL_USUARIO_NO_ENCONTRADO
                )

            if not user_row['nombre_empresa']:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=MSG_RAZON_SOCIAL_NO_CONFIGURADA
                )
            
            # Crear objeto compatible con UserModel
            user_profile = type('UserModel', (), {
                'id': user_row['id'],
                'nombre_persona': user_row['nombre_persona'],
                'nombre_empresa': user_row['nombre_empresa'],
                'ruc': user_row['ruc'],
                'foto_perfil': user_row['foto_perfil'],
                'estado': user_row['estado']
            })()
            
            return user_profile
        finally:
            if conn:
                await direct_db_service.pool.release(conn)

    @staticmethod
    async def validate_company_uniqueness(
        razon_social: str, 
        nombre_fantasia: str, 
        current_user_id: str
    ) -> Optional[dict]:
        """
        Valida la unicidad de la empresa y retorna empresa existente si existe.
        Retorna un diccionario con los datos de la empresa o None.
        """
        conn = None
        try:
            conn = await direct_db_service.get_connection()
            
            empresa_query = """
                SELECT id_perfil, razon_social, nombre_fantasia, user_id, estado, verificado, id_direccion
                FROM perfil_empresa
                WHERE razon_social = $1 OR nombre_fantasia = $2
                LIMIT 1
            """
            empresa_row = await conn.fetchrow(empresa_query, razon_social, nombre_fantasia)
            
            if empresa_row:
                # Verificar si pertenece a otro usuario
                if str(empresa_row['user_id']) != current_user_id:
                    raise HTTPException(
                        status_code=status.HTTP_409_CONFLICT,
                        detail=MSG_EMPRESA_YA_REGISTRADA
                    )
                
                return {
                    'id_perfil': empresa_row['id_perfil'],
                    'razon_social': empresa_row['razon_social'],
                    'nombre_fantasia': empresa_row['nombre_fantasia'],
                    'user_id': empresa_row['user_id'],
                    'estado': empresa_row['estado'],
                    'verificado': empresa_row['verificado'],
                    'id_direccion': empresa_row['id_direccion']
                }
            
            return None
        finally:
            if conn:
                await direct_db_service.pool.release(conn)

    @staticmethod
    async def find_location_data(direccion_data: dict) -> tuple:
        """
        Busca y valida departamento, ciudad y barrio.
        Retorna objetos con estructura compatible con los modelos ORM.
        """
        conn = None
        try:
            conn = await direct_db_service.get_connection()
            
            # Buscar departamento
            dept_query = "SELECT id_departamento, nombre, created_at FROM departamento WHERE nombre = $1"
            dept_row = await conn.fetchrow(dept_query, direccion_data['departamento'])
            
            if not dept_row:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=MSG_DEPARTAMENTO_NO_ENCONTRADO.format(departamento=direccion_data['departamento'])
                )
            
            # Crear objeto departamento compatible
            departamento = type('Departamento', (), {
                'id_departamento': dept_row['id_departamento'],
                'nombre': dept_row['nombre'],
                'created_at': dept_row['created_at']
            })()
            
            # Buscar ciudad
            ciudad_query = """
                SELECT id_ciudad, nombre, id_departamento, created_at 
                FROM ciudad 
                WHERE nombre = $1 AND id_departamento = $2
            """
            ciudad_row = await conn.fetchrow(
                ciudad_query, 
                direccion_data['ciudad'], 
                departamento.id_departamento
            )
            
            if not ciudad_row:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=MSG_CIUDAD_NO_ENCONTRADA.format(
                        ciudad=direccion_data['ciudad'], 
                        departamento=direccion_data['departamento']
                    )
                )
            
            # Crear objeto ciudad compatible
            ciudad = type('Ciudad', (), {
                'id_ciudad': ciudad_row['id_ciudad'],
                'nombre': ciudad_row['nombre'],
                'id_departamento': ciudad_row['id_departamento'],
                'created_at': ciudad_row['created_at']
            })()
            
            # Buscar barrio (opcional)
            barrio = None
            barrio_value = direccion_data.get('barrio')
            if barrio_value and isinstance(barrio_value, str) and barrio_value.strip():
                barrio_query = """
                    SELECT id_barrio, nombre, id_ciudad 
                    FROM barrio 
                    WHERE nombre = $1 AND id_ciudad = $2
                """
                barrio_row = await conn.fetchrow(
                    barrio_query,
                    direccion_data['barrio'],
                    ciudad.id_ciudad
                )
                
                if barrio_row:
                    # Crear objeto barrio compatible
                    barrio = type('Barrio', (), {
                        'id_barrio': barrio_row['id_barrio'],
                        'nombre': barrio_row['nombre'],
                        'id_ciudad': barrio_row['id_ciudad']
                    })()
                else:
                    print(f"⚠️ Barrio '{direccion_data['barrio']}' no encontrado, continuando sin barrio")
            
            return departamento, ciudad, barrio
        finally:
            if conn:
                await direct_db_service.pool.release(conn)

    @staticmethod
    async def get_tipo_documento_by_name(conn: asyncpg.Connection, nombre_tip_documento: str) -> Optional[dict]:
        """Obtiene un tipo de documento por su nombre"""
        tipo_doc_row = await conn.fetchrow("""
            SELECT id_tip_documento FROM tipo_documento WHERE tipo_documento = $1
        """, nombre_tip_documento)
        
        if not tipo_doc_row:
            # Obtener todos los tipos de documento disponibles para debugging
            todos_tipos = await conn.fetch("""
                SELECT tipo_documento FROM tipo_documento ORDER BY tipo_documento
            """)
            tipos_disponibles = [row['tipo_documento'] for row in todos_tipos]
            print(f"❌ Tipo de documento '{nombre_tip_documento}' no encontrado.")
            print(f"📋 Tipos disponibles en BD: {tipos_disponibles}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Tipo de documento '{nombre_tip_documento}' no encontrado. Tipos disponibles: {', '.join(tipos_disponibles)}"
            )
        
        return {'id_tip_documento': tipo_doc_row['id_tip_documento']}

    @staticmethod
    async def get_existing_document(
        conn: asyncpg.Connection,
        id_perfil: int,
        id_tip_documento: int
    ) -> Optional[dict]:
        """Obtiene un documento existente para un perfil y tipo de documento"""
        doc_existente = await conn.fetchrow("""
            SELECT d.id_documento 
            FROM documento d
            JOIN verificacion_solicitud vs ON d.id_verificacion = vs.id_verificacion
            WHERE vs.id_perfil = $1 AND d.id_tip_documento = $2
            ORDER BY d.created_at DESC
            LIMIT 1
        """, id_perfil, id_tip_documento)
        
        return dict(doc_existente) if doc_existente else None

    @staticmethod
    async def get_empresa_with_sucursales_orm(
        db: AsyncSession,
        user_id: str
    ) -> PerfilEmpresa:
        """Obtiene el perfil de empresa del usuario con relación de sucursales usando ORM"""
        empresa_query = select(PerfilEmpresa).options(
            selectinload(PerfilEmpresa.sucursal_empresa)
        ).where(PerfilEmpresa.user_id == uuid.UUID(user_id))
        empresa_result = await db.execute(empresa_query)
        empresa = empresa_result.scalars().first()
        
        if not empresa:
            from app.api.v1.routers.providers.constants import MSG_PERFIL_EMPRESA_NO_ENCONTRADO
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=MSG_PERFIL_EMPRESA_NO_ENCONTRADO
            )
        return empresa

    @staticmethod
    async def get_latest_verification_request_orm(
        db: AsyncSession,
        perfil_id: int
    ) -> VerificacionSolicitud:
        """Obtiene la solicitud de verificación más reciente para un perfil usando ORM"""
        solicitud_query = select(VerificacionSolicitud).where(
            VerificacionSolicitud.id_perfil == perfil_id
        ).order_by(VerificacionSolicitud.created_at.desc())
        solicitud_result = await db.execute(solicitud_query)
        solicitud = solicitud_result.scalars().first()
        
        if not solicitud:
            from app.api.v1.routers.providers.constants import MSG_SOLICITUD_VERIFICACION_NO_ENCONTRADA
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=MSG_SOLICITUD_VERIFICACION_NO_ENCONTRADA
            )
        return solicitud

    # ========== MÉTODOS DE ESCRITURA (INSERT/UPDATE) ==========
    # Estos métodos ejecutan SQL directamente - pertenecen a la capa de acceso a datos

    @staticmethod
    async def create_verification_request(
        conn: asyncpg.Connection,
        id_perfil: int,
        comentario_solicitud: Optional[str],
        estado: str
    ) -> dict:
        """
        Crea una solicitud de verificación en la base de datos.
        Acceso a datos - INSERT.
        """
        nueva_solicitud_row = await conn.fetchrow("""
            INSERT INTO verificacion_solicitud (id_perfil, estado, comentario)
            VALUES ($1, $2, $3)
            RETURNING id_verificacion, id_perfil, estado, comentario, fecha_solicitud, created_at
        """, id_perfil, estado, comentario_solicitud)
        
        return dict(nueva_solicitud_row)

    @staticmethod
    async def create_or_update_direccion(
        conn: asyncpg.Connection,
        perfil_data: dict,
        departamento,
        ciudad,
        barrio,
        id_direccion_existente: Optional[int],
        coordenadas_wkt: str,
        coordenadas_srid: int
    ) -> int:
        """
        Crea o actualiza una dirección en la base de datos.
        Acceso a datos - INSERT/UPDATE.
        """
        calle = perfil_data['direccion'].get('calle', '')
        numero = perfil_data['direccion'].get('numero', '')
        referencia = perfil_data['direccion'].get('referencia', '')
        
        if id_direccion_existente:
            # Actualizar dirección existente
            await conn.execute("""
                UPDATE direccion 
                SET calle = $1, numero = $2, referencia = $3, 
                    id_departamento = $4, id_ciudad = $5, id_barrio = $6,
                    coordenadas = ST_GeomFromText($7, $8)
                WHERE id_direccion = $9
            """, calle, numero, referencia, departamento.id_departamento,
                ciudad.id_ciudad if ciudad else None, barrio.id_barrio if barrio else None,
                coordenadas_wkt, coordenadas_srid, id_direccion_existente)
            return id_direccion_existente
        else:
            # Crear nueva dirección
            nueva_direccion_row = await conn.fetchrow("""
                INSERT INTO direccion (calle, numero, referencia, id_departamento, id_ciudad, id_barrio, coordenadas)
                VALUES ($1, $2, $3, $4, $5, $6, ST_GeomFromText($7, $8))
                RETURNING id_direccion
            """, calle, numero, referencia, departamento.id_departamento,
                ciudad.id_ciudad if ciudad else None, barrio.id_barrio if barrio else None,
                coordenadas_wkt, coordenadas_srid)
            return nueva_direccion_row['id_direccion']

    @staticmethod
    async def create_or_update_empresa(
        conn: asyncpg.Connection,
        user_id: str,
        razon_social: str,
        nombre_fantasia: str,
        id_direccion: int,
        id_perfil_existente: Optional[int],
        estado: str,
        verificado: bool
    ) -> int:
        """
        Crea o actualiza una empresa en la base de datos.
        Acceso a datos - INSERT/UPDATE.
        """
        if id_perfil_existente:
            # Actualizar empresa existente
            await conn.execute("""
                UPDATE perfil_empresa 
                SET razon_social = $1, nombre_fantasia = $2, estado = $3, verificado = $4, id_direccion = $5
                WHERE id_perfil = $6
            """, razon_social, nombre_fantasia, estado, verificado, id_direccion, id_perfil_existente)
            return id_perfil_existente
        else:
            # Crear nueva empresa
            nuevo_perfil_row = await conn.fetchrow("""
                INSERT INTO perfil_empresa (user_id, razon_social, nombre_fantasia, id_direccion, estado, verificado)
                VALUES ($1, $2, $3, $4, $5, $6)
                RETURNING id_perfil
            """, uuid.UUID(user_id), razon_social, nombre_fantasia, id_direccion, estado, verificado)
            return nuevo_perfil_row['id_perfil']

    @staticmethod
    async def create_or_update_sucursal(
        conn: asyncpg.Connection,
        perfil_data: dict,
        id_perfil: int,
        id_direccion: int,
        nombre_default: str
    ) -> None:
        """
        Crea o actualiza una sucursal en la base de datos.
        Acceso a datos - INSERT/UPDATE.
        """
        if not perfil_data.get('sucursal'):
            return
        
        sucursal_data = perfil_data['sucursal']
        nombre = sucursal_data.get('nombre', nombre_default) or nombre_default
        telefono = sucursal_data.get('telefono', '') or ''
        email = sucursal_data.get('email', '') or ''
        
        # Verificar si existe sucursal
        sucursal_existente = await conn.fetchrow("""
            SELECT id_sucursal FROM sucursal_empresa WHERE id_perfil = $1 LIMIT 1
        """, id_perfil)
        
        if sucursal_existente:
            # Actualizar sucursal existente
            await conn.execute("""
                UPDATE sucursal_empresa 
                SET nombre = $1, telefono = $2, email = $3, id_direccion = $4
                WHERE id_sucursal = $5
            """, nombre, telefono, email, id_direccion, sucursal_existente['id_sucursal'])
        else:
            # Crear nueva sucursal
            await conn.execute("""
                INSERT INTO sucursal_empresa (id_perfil, nombre, telefono, email, id_direccion, es_principal)
                VALUES ($1, $2, $3, $4, $5, $6)
            """, id_perfil, nombre, telefono, email, id_direccion, True)

    @staticmethod
    async def create_document(
        conn: asyncpg.Connection,
        id_verificacion: int,
        id_tip_documento: int,
        url_archivo: str,
        estado_revision: str
    ) -> None:
        """
        Crea un nuevo documento en la base de datos.
        Acceso a datos - INSERT.
        """
        await conn.execute("""
            INSERT INTO documento (id_verificacion, id_tip_documento, url_archivo, estado_revision)
            VALUES ($1, $2, $3, $4)
        """, id_verificacion, id_tip_documento, url_archivo, estado_revision)

    @staticmethod
    async def update_document(
        conn: asyncpg.Connection,
        id_documento: int,
        url_archivo: str,
        estado_revision: str,
        fecha_verificacion,
        id_verificacion: int
    ) -> None:
        """
        Actualiza un documento existente en la base de datos.
        Acceso a datos - UPDATE.
        """
        await conn.execute("""
            UPDATE documento 
            SET url_archivo = $1, estado_revision = $2, observacion = NULL,
                fecha_verificacion = $3, id_verificacion = $4
            WHERE id_documento = $5
        """, url_archivo, estado_revision, fecha_verificacion, id_verificacion, id_documento)

    @staticmethod
    async def get_approved_ruc_for_user(
        conn: asyncpg.Connection,
        user_id: str
    ) -> Optional[dict]:
        """
        Obtiene el RUC aprobado de un usuario desde verificacion_ruc.
        Retorna None si no existe o no está aprobado.
        Acceso a datos - SELECT.
        """
        ruc_row = await conn.fetchrow("""
            SELECT 
                vr.id_verificacion_ruc,
                vr.url_documento,
                vr.id_tip_documento,
                td.tipo_documento AS tipo_documento_nombre
            FROM verificacion_ruc vr
            LEFT JOIN tipo_documento td ON vr.id_tip_documento = td.id_tip_documento
            WHERE vr.user_id = $1 
                AND vr.estado = 'aprobada'
            ORDER BY vr.fecha_verificacion DESC
            LIMIT 1
        """, user_id)
        
        if ruc_row:
            return dict(ruc_row)
        return None

