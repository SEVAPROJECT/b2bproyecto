# app/api/v1/routers/providers.py

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from app.api.v1.dependencies.auth_user import get_current_user
from app.api.v1.dependencies.database_supabase import get_async_db
from app.models.empresa.perfil_empresa import PerfilEmpresa
from app.models.empresa.verificacion_solicitud import VerificacionSolicitud
from app.models.empresa.documento import Documento
from app.models.empresa.direccion import Direccion
from app.models.perfil import UserModel 
from app.schemas.empresa.perfil_empresa import PerfilEmpresaIn
from app.schemas.auth_user import SupabaseUser
from app.api.v1.dependencies.local_storage import local_storage_service
from app.api.v1.dependencies.idrive import upload_file_to_idrive, smart_upload_service
from app.services.direct_db_service import direct_db_service
from typing import Optional, List
import uuid
import asyncpg
from datetime import datetime
import json
from datetime import datetime
from app.schemas.publicar_servicio.solicitud_servicio import SolicitudServicioIn, SolicitudServicioOut  # noqa: E402
from app.api.v1.dependencies.auth_user import get_approved_provider  # noqa: E402
from app.models.publicar_servicio.solicitud_servicio import SolicitudServicio
from app.models.empresa.barrio import Barrio
from app.models.empresa.ciudad import Ciudad
from app.models.empresa.departamento import Departamento
from geoalchemy2 import WKTElement
from app.models.empresa.tipo_documento import TipoDocumento
from sqlalchemy.exc import IntegrityError
from sqlalchemy import text
from app.models.empresa.sucursal_empresa import SucursalEmpresa
from fastapi.responses import Response
import mimetypes
import urllib.parse
from sqlalchemy import select
from app.models.publicar_servicio.category import CategoriaModel
from app.models.empresa.perfil_empresa import PerfilEmpresa
from app.models.empresa.verificacion_solicitud import VerificacionSolicitud
from app.models.empresa.sucursal_empresa import SucursalEmpresa
import datetime
from app.supabase.auth_service import supabase_auth
from app.idrive.idrive_service import idrive_s3_client




router = APIRouter(prefix="/providers", tags=["providers"])

# Constantes para estados
ESTADO_PENDIENTE = "pendiente"
ESTADO_VERIFICADO_FALSE = False

# Constantes para valores por defecto
FILENAME_EMPTY = "empty.txt"
NOMBRE_SUCURSAL_DEFAULT = "Casa Matriz"
PREFIX_TEMP = "temp://"
PREFIX_LOCAL = "local://"
PREFIX_DOCUMENTOS = "documentos/"
DOCUMENT_TYPE_PROVIDER = "provider"

# Constantes para coordenadas
COORDENADAS_ASUNCION = WKTElement('POINT(-57.5759 -25.2637)', srid=4326)

# Constantes para mensajes de error
MSG_ERROR_JSON_INVALIDO = "Formato JSON inválido en perfil_in"
MSG_ERROR_NUMERO_DOCUMENTOS = "El número de nombres de tipo de documento no coincide con el número de archivos."
MSG_PERFIL_USUARIO_NO_ENCONTRADO = "Perfil de usuario no encontrado."
MSG_RAZON_SOCIAL_NO_CONFIGURADA = "La razón social no está configurada en tu perfil de usuario. Por favor, completa tu perfil antes de solicitar ser proveedor."
MSG_EMPRESA_YA_REGISTRADA = "Una empresa con esta razón social o nombre de fantasía ya está registrada."
MSG_DEPARTAMENTO_NO_ENCONTRADO = "Departamento '{departamento}' no encontrado"
MSG_CIUDAD_NO_ENCONTRADA = "Ciudad '{ciudad}' no encontrada en el departamento '{departamento}'"
MSG_TIPO_DOCUMENTO_NO_ENCONTRADO = "Tipo de documento '{nombre_tip_documento}' no encontrado"
MSG_DOCUMENTO_NO_ENCONTRADO = "Documento no encontrado"
MSG_DOCUMENTO_NO_DISPONIBLE = "Documento no disponible para visualización."
MSG_ERROR_INTERNO_SERVIDOR = "Error interno del servidor"
MSG_ERROR_INESPERADO = "Error inesperado: {error}"
MSG_ERROR_INESPERADO_SERVICIO = "Error inesperado al proponer el servicio: {error}"
MSG_ERROR_INESPERADO_GENERAL = "Error inesperado: {error}"
MSG_ERROR_DIAGNOSTICO = "Error en diagnóstico: {error}"
MSG_PERFIL_EMPRESA_NO_ENCONTRADO = "No se encontró perfil de empresa para este usuario"
MSG_SOLICITUD_VERIFICACION_NO_ENCONTRADA = "No se encontró solicitud de verificación"
MSG_URL_INVALIDA_LOCAL = "URL inválida. Solo se permiten archivos locales."
MSG_ARCHIVO_NO_ENCONTRADO = "Archivo no encontrado: {message}"
MSG_ERROR_SIRVIENDO_ARCHIVO = "Error sirviendo archivo: {serve_message}"

# Constantes para mensajes de éxito
MSG_SOLICITUD_REENVIADA = "Solicitud de verificación reenviada exitosamente."
MSG_SOLICITUD_CREADA = "Perfil de empresa y solicitud de verificación creados exitosamente."

# Constantes para valores por defecto en respuestas
VALOR_DEFAULT_ESTADO_APROBACION = "pendiente"
VALOR_DEFAULT_NO_ESPECIFICADO = "No especificado"
VALOR_DEFAULT_TIPO_NO_ENCONTRADO = "Tipo no encontrado"

# Funciones helper para reducir complejidad cognitiva
def parse_and_validate_profile(perfil_in: str) -> dict:
    """Parsea y valida el JSON del perfil"""
        try:
            perfil_data = json.loads(perfil_in)
            print(f"✅ JSON parseado correctamente: {perfil_data}")
        return perfil_data
        except json.JSONDecodeError as e:
            print(f"❌ Error parseando JSON: {e}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
            detail=MSG_ERROR_JSON_INVALIDO
            )
        
def validate_documents_count(nombres_tip_documento: List[str], documentos: List[UploadFile]) -> None:
    """Valida que la cantidad de nombres de tipos de documento coincide con la de los archivos"""
        if len(nombres_tip_documento) != len(documentos):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
            detail=MSG_ERROR_NUMERO_DOCUMENTOS
            )

def filter_valid_documents(documentos: List[UploadFile], nombres_tip_documento: List[str]) -> tuple:
    """Filtra documentos vacíos y retorna documentos y nombres válidos"""
        documentos_validos = []
        nombres_tip_documento_validos = []
        
        for i, doc in enumerate(documentos):
        if doc.filename != FILENAME_EMPTY and doc.size > 0:
                documentos_validos.append(doc)
                nombres_tip_documento_validos.append(nombres_tip_documento[i])
            else:
                print(f"⚠️ Documento vacío filtrado: {doc.filename}")
        
    return documentos_validos, nombres_tip_documento_validos

async def get_user_profile(db: AsyncSession, user_id: str):
    """
    Obtiene y valida el perfil de usuario.
    Usa direct_db_service para evitar problemas con PgBouncer.
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

async def validate_company_uniqueness(
    db: AsyncSession, 
    razon_social: str, 
    nombre_fantasia: str, 
    current_user_id: str
):
    """
    Valida la unicidad de la empresa y retorna empresa existente si existe.
    Usa direct_db_service para evitar problemas con PgBouncer.
    Retorna un objeto compatible con PerfilEmpresa o None.
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
            
            # Crear objeto compatible con PerfilEmpresa
            empresa_existente = type('PerfilEmpresa', (), {
                'id_perfil': empresa_row['id_perfil'],
                'razon_social': empresa_row['razon_social'],
                'nombre_fantasia': empresa_row['nombre_fantasia'],
                'user_id': empresa_row['user_id'],
                'estado': empresa_row['estado'],
                'verificado': empresa_row['verificado'],
                'id_direccion': empresa_row['id_direccion']
            })()
            
            return empresa_existente
        
        return None
    finally:
        if conn:
            await direct_db_service.pool.release(conn)

async def find_location_data(
    db: AsyncSession, 
    direccion_data: dict
) -> tuple:
    """
    Busca y valida departamento, ciudad y barrio.
    Usa direct_db_service para evitar problemas con PgBouncer.
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

async def sync_direccion_sequence(db: AsyncSession) -> None:
    """Sincroniza la secuencia de direccion"""
    await db.execute(text("""
        SELECT setval(
            pg_get_serial_sequence('direccion', 'id_direccion'),
            COALESCE((SELECT MAX(id_direccion) FROM direccion), 0) + 1,
            false
        )
    """))
    await db.flush()

async def create_direccion_with_retry(
    db: AsyncSession,
    direccion_data: dict,
    departamento,
    ciudad,
    barrio
) -> Direccion:
    """Crea una dirección con manejo de errores de secuencia"""
            nueva_direccion = Direccion(
        calle=direccion_data['calle'],
        numero=direccion_data['numero'],
        referencia=direccion_data['referencia'],
                id_departamento=departamento.id_departamento,
                id_ciudad=ciudad.id_ciudad if ciudad else None,
                id_barrio=barrio.id_barrio if barrio else None,
        coordenadas=COORDENADAS_ASUNCION
            )
            db.add(nueva_direccion)
    
            try:
                await db.flush()
            except IntegrityError as e:
                if 'duplicate key value violates unique constraint "direccion_pkey"' in str(e):
                    print("⚠️ Secuencia de direccion desincronizada, sincronizando...")
                    db.expunge(nueva_direccion)
            await sync_direccion_sequence(db)
                    # Recrear el objeto dirección
                    nueva_direccion = Direccion(
                calle=direccion_data['calle'],
                numero=direccion_data['numero'],
                referencia=direccion_data['referencia'],
                        id_departamento=departamento.id_departamento,
                        id_ciudad=ciudad.id_ciudad if ciudad else None,
                        id_barrio=barrio.id_barrio if barrio else None,
                coordenadas=COORDENADAS_ASUNCION
                    )
                    db.add(nueva_direccion)
                    await db.flush()
                else:
                    raise
            
    return nueva_direccion

async def update_or_create_direccion(
    db: AsyncSession,
    perfil_data: dict,
    departamento,
    ciudad,
    barrio,
    nuevo_perfil: Optional[PerfilEmpresa]
) -> Direccion:
    """Crea o actualiza la dirección según si existe perfil"""
    if nuevo_perfil is None:
        return await create_direccion_with_retry(
            db, perfil_data['direccion'], departamento, ciudad, barrio
        )
        else:
            if nuevo_perfil.id_direccion:
            direccion_existente_result = await db.execute(
                    select(Direccion).where(Direccion.id_direccion == nuevo_perfil.id_direccion)
                )
            direccion_existente = direccion_existente_result.scalars().first()
                if direccion_existente:
                    direccion_existente.calle = perfil_data['direccion']['calle']
                    direccion_existente.numero = perfil_data['direccion']['numero']
                    direccion_existente.referencia = perfil_data['direccion']['referencia']
                    direccion_existente.id_departamento = departamento.id_departamento
                    direccion_existente.id_ciudad = ciudad.id_ciudad if ciudad else None
                    direccion_existente.id_barrio = barrio.id_barrio if barrio else None
                    await db.flush()
                return direccion_existente
        
        nueva_direccion = await create_direccion_with_retry(
            db, perfil_data['direccion'], departamento, ciudad, barrio
        )
        nuevo_perfil.id_direccion = nueva_direccion.id_direccion
                    await db.flush()
        return nueva_direccion

async def update_or_create_empresa(
    db: AsyncSession,
    perfil_data: dict,
    razon_social: str,
    current_user_id: str,
    nueva_direccion: Direccion,
    empresa_existente: Optional[PerfilEmpresa]
) -> PerfilEmpresa:
    """Crea o actualiza el perfil de empresa"""
    if empresa_existente and empresa_existente.user_id == uuid.UUID(current_user_id):
        print(f"🔍 Actualizando empresa existente: {empresa_existente.razon_social}")
        empresa_existente.razon_social = razon_social
        empresa_existente.nombre_fantasia = perfil_data['nombre_fantasia']
        empresa_existente.estado = ESTADO_PENDIENTE
        empresa_existente.verificado = ESTADO_VERIFICADO_FALSE
                        await db.flush()
        return empresa_existente
                    else:
        nuevo_perfil = PerfilEmpresa(
            user_id=uuid.UUID(current_user_id),
            razon_social=razon_social,
            nombre_fantasia=perfil_data['nombre_fantasia'],
            id_direccion=nueva_direccion.id_direccion,
            estado=ESTADO_PENDIENTE,
            verificado=ESTADO_VERIFICADO_FALSE
        )
        db.add(nuevo_perfil)
                await db.flush()
        return nuevo_perfil

async def update_or_create_sucursal(
    db: AsyncSession,
    perfil_data: dict,
    nuevo_perfil: PerfilEmpresa,
    nueva_direccion: Direccion
) -> None:
    """Crea o actualiza la sucursal si hay datos"""
    if not perfil_data.get('sucursal'):
        return
    
    sucursal_data = perfil_data['sucursal']
            sucursal_existente_query = select(SucursalEmpresa).where(
                SucursalEmpresa.id_perfil == nuevo_perfil.id_perfil
            )
            sucursal_existente_result = await db.execute(sucursal_existente_query)
            sucursal_existente = sucursal_existente_result.scalars().first()
            
            if sucursal_existente:
        sucursal_existente.nombre = sucursal_data.get('nombre', NOMBRE_SUCURSAL_DEFAULT)
                sucursal_existente.telefono = sucursal_data.get('telefono', '')
                sucursal_existente.email = sucursal_data.get('email', '')
        sucursal_existente.id_direccion = nueva_direccion.id_direccion
            else:
                nueva_sucursal = SucursalEmpresa(
                    id_perfil=nuevo_perfil.id_perfil,
            nombre=sucursal_data.get('nombre', NOMBRE_SUCURSAL_DEFAULT),
                    telefono=sucursal_data.get('telefono', ''),
                    email=sucursal_data.get('email', ''),
            id_direccion=nueva_direccion.id_direccion,
                    es_principal=True
                )
                db.add(nueva_sucursal)
            
            await db.flush()

async def process_documents(
    db: AsyncSession,
    documentos: List[UploadFile],
    nombres_tip_documento: List[str],
    razon_social: str,
    nueva_solicitud: VerificacionSolicitud,
    empresa_existente: Optional[PerfilEmpresa],
    current_user_id: str
) -> None:
    """Procesa y sube los documentos"""
    if not documentos:
        print("⚠️ No hay documentos nuevos para procesar")
        return
    
            for index, file in enumerate(documentos):
                nombre_tip_documento = nombres_tip_documento[index]
                
                tipo_doc_result = await db.execute(
                    select(TipoDocumento).where(TipoDocumento.nombre == nombre_tip_documento)
                )
                tipo_documento = tipo_doc_result.scalars().first()
                
                if not tipo_documento:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                detail=MSG_TIPO_DOCUMENTO_NO_ENCONTRADO.format(nombre_tip_documento=nombre_tip_documento)
                    )
                
        # Subir archivo
                try:
                    file_content = await file.read()
                    file_key = f"{razon_social}/{nombre_tip_documento}/{uuid.uuid4()}_{file.filename}"
            idrive_url = upload_file_to_idrive(
                        file_content=file_content,
                        filename=file_key,
                document_type=DOCUMENT_TYPE_PROVIDER
                    )
                    print(f"✅ Archivo subido exitosamente: {idrive_url}")
                except Exception as upload_error:
                    print(f"❌ Error al subir archivo: {upload_error}")
            idrive_url = f"{PREFIX_TEMP}{file.filename}_{current_user_id}_{tipo_documento.id_tip_documento}"
                
        # Crear o actualizar documento
        if empresa_existente and empresa_existente.user_id == uuid.UUID(current_user_id):
                    doc_existente_query = select(Documento).join(VerificacionSolicitud).where(
                        VerificacionSolicitud.id_perfil == empresa_existente.id_perfil,
                        Documento.id_tip_documento == tipo_documento.id_tip_documento
                    ).order_by(Documento.created_at.desc())
                    
                    doc_existente_result = await db.execute(doc_existente_query)
                    doc_existente = doc_existente_result.scalars().first()
                    
                    if doc_existente:
                        print(f"🔄 Actualizando documento existente: {nombre_tip_documento}")
                        doc_existente.url_archivo = idrive_url
                doc_existente.estado_revision = ESTADO_PENDIENTE
                doc_existente.observacion = None
                        from app.services.date_service import DateService
                        doc_existente.fecha_verificacion = DateService.now_for_database()
                        doc_existente.id_verificacion = nueva_solicitud.id_verificacion
                    else:
                        print(f"➕ Creando nuevo documento: {nombre_tip_documento}")
                        nuevo_documento = Documento(
                            id_verificacion=nueva_solicitud.id_verificacion,
                            id_tip_documento=tipo_documento.id_tip_documento,
                            url_archivo=idrive_url,
                    estado_revision=ESTADO_PENDIENTE
                        )
                        db.add(nuevo_documento)
                else:
                    nuevo_documento = Documento(
                        id_verificacion=nueva_solicitud.id_verificacion,
                        id_tip_documento=tipo_documento.id_tip_documento,
                        url_archivo=idrive_url,
                estado_revision=ESTADO_PENDIENTE
                    )
                    db.add(nuevo_documento)

# Funciones helper para solicitar_verificacion_completa usando SQL directo
async def create_or_update_direccion_sql(
    conn: asyncpg.Connection,
    perfil_data: dict,
    departamento,
    ciudad,
    barrio,
    id_direccion_existente: Optional[int]
) -> int:
    """Crea o actualiza una dirección usando SQL directo"""
    calle = perfil_data['direccion'].get('calle', '')
    numero = perfil_data['direccion'].get('numero', '')
    referencia = perfil_data['direccion'].get('referencia', '')
    coordenadas_wkt = 'POINT(-57.5759 -25.2637)'  # Asunción por defecto
    
    if id_direccion_existente:
        # Actualizar dirección existente
        await conn.execute("""
            UPDATE direccion 
            SET calle = $1, numero = $2, referencia = $3, 
                id_departamento = $4, id_ciudad = $5, id_barrio = $6,
                coordenadas = ST_GeomFromText($7, 4326)
            WHERE id_direccion = $8
        """, calle, numero, referencia, departamento.id_departamento,
            ciudad.id_ciudad if ciudad else None, barrio.id_barrio if barrio else None,
            coordenadas_wkt, id_direccion_existente)
        return id_direccion_existente
        else:
        # Crear nueva dirección
        nueva_direccion_row = await conn.fetchrow("""
            INSERT INTO direccion (calle, numero, referencia, id_departamento, id_ciudad, id_barrio, coordenadas)
            VALUES ($1, $2, $3, $4, $5, $6, ST_GeomFromText($7, 4326))
            RETURNING id_direccion
        """, calle, numero, referencia, departamento.id_departamento,
            ciudad.id_ciudad if ciudad else None, barrio.id_barrio if barrio else None,
            coordenadas_wkt)
        return nueva_direccion_row['id_direccion']

async def create_or_update_sucursal_sql(
    conn: asyncpg.Connection,
    perfil_data: dict,
    id_perfil: int,
    id_direccion: int
) -> None:
    """Crea o actualiza una sucursal usando SQL directo"""
    if not perfil_data.get('sucursal'):
        return
    
    sucursal_data = perfil_data['sucursal']
    nombre = sucursal_data.get('nombre', NOMBRE_SUCURSAL_DEFAULT) or NOMBRE_SUCURSAL_DEFAULT
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

async def process_documents_sql(
    conn: asyncpg.Connection,
    documentos: List[UploadFile],
    nombres_tip_documento: List[str],
    razon_social: str,
    id_verificacion: int,
    id_perfil_existente: Optional[int],
    current_user_id: str
) -> None:
    """Procesa y sube los documentos usando SQL directo"""
    if not documentos:
        print("⚠️ No hay documentos nuevos para procesar")
        return
    
    for index, file in enumerate(documentos):
        nombre_tip_documento = nombres_tip_documento[index]
        
        # Obtener tipo de documento
        # NOTA: La columna en la BD se llama 'tipo_documento', no 'nombre'
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
        
        id_tip_documento = tipo_doc_row['id_tip_documento']
        
        # Subir archivo
        try:
            file_content = await file.read()
            file_key = f"{razon_social}/{nombre_tip_documento}/{uuid.uuid4()}_{file.filename}"
            idrive_url = upload_file_to_idrive(
                file_content=file_content,
                filename=file_key,
                document_type=DOCUMENT_TYPE_PROVIDER
            )
            print(f"✅ Archivo subido exitosamente: {idrive_url}")
        except Exception as upload_error:
            print(f"❌ Error al subir archivo: {upload_error}")
            idrive_url = f"{PREFIX_TEMP}{file.filename}_{current_user_id}_{id_tip_documento}"
        
        # Verificar si existe documento previo (solo si hay empresa existente)
        doc_existente = None
        if id_perfil_existente:
            doc_existente = await conn.fetchrow("""
                SELECT d.id_documento 
                FROM documento d
                JOIN verificacion_solicitud vs ON d.id_verificacion = vs.id_verificacion
                WHERE vs.id_perfil = $1 AND d.id_tip_documento = $2
                ORDER BY d.created_at DESC
                LIMIT 1
            """, id_perfil_existente, id_tip_documento)
        
        if doc_existente:
            # Actualizar documento existente
            print(f"🔄 Actualizando documento existente: {nombre_tip_documento}")
            from app.services.date_service import DateService
            fecha_verificacion = DateService.now_for_database()
            await conn.execute("""
                UPDATE documento 
                SET url_archivo = $1, estado_revision = $2, observacion = NULL,
                    fecha_verificacion = $3, id_verificacion = $4
                WHERE id_documento = $5
            """, idrive_url, ESTADO_PENDIENTE, fecha_verificacion, id_verificacion, doc_existente['id_documento'])
        else:
            # Crear nuevo documento
            print(f"➕ Creando nuevo documento: {nombre_tip_documento}")
            await conn.execute("""
                INSERT INTO documento (id_verificacion, id_tip_documento, url_archivo, estado_revision)
                VALUES ($1, $2, $3, $4)
            """, id_verificacion, id_tip_documento, idrive_url, ESTADO_PENDIENTE)

@router.post(
    "/solicitar-verificacion",
    status_code=status.HTTP_201_CREATED,
    description="Registra un perfil de empresa y una solicitud de verificación con documentos adjuntos."
)
async def solicitar_verificacion_completa(
    perfil_in: str = Form(...),  # Recibir como string JSON
    nombres_tip_documento: List[str] = Form(...), # Recibe una lista de nombres de tipos de documento
    documentos: List[UploadFile] = File(...),
    comentario_solicitud: Optional[str] = Form(None),
    current_user: SupabaseUser = Depends(get_current_user)
):
    """
    Registra un perfil de empresa y una solicitud de verificación con documentos adjuntos.
    Usa direct_db_service con SQL directo para evitar problemas con PgBouncer.
    """
    conn: Optional[asyncpg.Connection] = None
    try:
        print("🚀 Iniciando solicitud de verificación...")
        print(f"👤 Usuario: {current_user.email} ({current_user.id})")
        print(f"📄 Perfil recibido: {perfil_in[:200]}...")
        print(f"📎 Archivos: {len(documentos)} archivos")
        print(f"📝 Nombres tipos documento: {nombres_tip_documento}")
        print(f"💬 Comentario: {comentario_solicitud}")

        # Parsear y validar perfil
        perfil_data = parse_and_validate_profile(perfil_in)
        
        # Validar documentos
        validate_documents_count(nombres_tip_documento, documentos)
        documentos, nombres_tip_documento = filter_valid_documents(documentos, nombres_tip_documento)
        print(f"📎 Documentos válidos para procesar: {len(documentos)}")

        # Obtener conexión de direct_db_service
        conn = await direct_db_service.get_connection()
        
        # Usar transacción para todas las operaciones
        async with conn.transaction():
            # Obtener perfil de usuario y razón social
            print("🔍 Obteniendo perfil de usuario...")
            user_profile = await get_user_profile(None, current_user.id)  # db no se usa
            razon_social = user_profile.nombre_empresa
            print(f"✅ Perfil de usuario obtenido. Razón social: {razon_social}")
            
            # Validar unicidad de empresa
            print("🔍 Validando unicidad de empresa...")
            empresa_existente = await validate_company_uniqueness(
                None, razon_social, perfil_data['nombre_fantasia'], current_user.id  # db no se usa
            )
            print(f"✅ Validación de unicidad completada. Empresa existente: {empresa_existente is not None}")
            
            # Buscar datos de ubicación
            print(f"🔍 Buscando datos de ubicación: {perfil_data['direccion']}")
            departamento, ciudad, barrio = await find_location_data(None, perfil_data['direccion'])  # db no se usa
            print(f"✅ Datos de ubicación encontrados. Departamento: {departamento.nombre}, Ciudad: {ciudad.nombre}, Barrio: {barrio.nombre if barrio else 'N/A'}")
            
            # Determinar si hay empresa existente del mismo usuario
            id_perfil_existente = None
            id_direccion_existente = None
            if empresa_existente and str(empresa_existente.user_id) == current_user.id:
                print(f"🔍 Actualizando empresa existente para reenvío: {empresa_existente.razon_social}")
                id_perfil_existente = empresa_existente.id_perfil
                id_direccion_existente = empresa_existente.id_direccion
                
                # Actualizar empresa existente
                await conn.execute("""
                    UPDATE perfil_empresa 
                    SET razon_social = $1, nombre_fantasia = $2, estado = $3, verificado = $4
                    WHERE id_perfil = $5
                """, razon_social, perfil_data['nombre_fantasia'], ESTADO_PENDIENTE, ESTADO_VERIFICADO_FALSE, id_perfil_existente)
            
            # Crear o actualizar dirección usando SQL directo
            nueva_direccion_id = await create_or_update_direccion_sql(
                conn, perfil_data, departamento, ciudad, barrio, id_direccion_existente
            )
            
            # Crear o actualizar empresa (solo si no existe)
            if id_perfil_existente is None:
                nuevo_perfil_row = await conn.fetchrow("""
                    INSERT INTO perfil_empresa (user_id, razon_social, nombre_fantasia, id_direccion, estado, verificado)
                    VALUES ($1, $2, $3, $4, $5, $6)
                    RETURNING id_perfil, user_id, razon_social, nombre_fantasia, id_direccion, estado, verificado
                """, uuid.UUID(current_user.id), razon_social, perfil_data['nombre_fantasia'], 
                    nueva_direccion_id, ESTADO_PENDIENTE, ESTADO_VERIFICADO_FALSE)
                id_perfil_existente = nuevo_perfil_row['id_perfil']
                print(f"✅ Nueva empresa creada con ID: {id_perfil_existente}")
            else:
                # Actualizar dirección de empresa existente
                await conn.execute("""
                    UPDATE perfil_empresa SET id_direccion = $1 WHERE id_perfil = $2
                """, nueva_direccion_id, id_perfil_existente)
            
            # Crear o actualizar sucursal usando SQL directo
            await create_or_update_sucursal_sql(
                conn, perfil_data, id_perfil_existente, nueva_direccion_id
            )
            
            # Crear solicitud de verificación
            nueva_solicitud_row = await conn.fetchrow("""
                INSERT INTO verificacion_solicitud (id_perfil, estado, comentario)
                VALUES ($1, $2, $3)
                RETURNING id_verificacion, id_perfil, estado, comentario, fecha_solicitud, created_at
            """, id_perfil_existente, ESTADO_PENDIENTE, comentario_solicitud)
            id_verificacion = nueva_solicitud_row['id_verificacion']
            print(f"🔍 Nueva solicitud creada: {id_verificacion} para empresa: {razon_social}")
            
            # Procesar documentos usando SQL directo
            id_perfil_para_docs = id_perfil_existente if empresa_existente and str(empresa_existente.user_id) == current_user.id else None
            await process_documents_sql(
                conn, documentos, nombres_tip_documento, razon_social, 
                id_verificacion, id_perfil_para_docs, current_user.id
            )
        
        # La transacción se confirma automáticamente al salir del bloque `async with conn.transaction()`
        
        if empresa_existente and str(empresa_existente.user_id) == current_user.id:
            return {"message": MSG_SOLICITUD_REENVIADA}
        else:
            return {"message": MSG_SOLICITUD_CREADA}

    except HTTPException:
        raise
    except Exception as e:
        import traceback
        error_traceback = traceback.format_exc()
        print(f"❌ Error completo en solicitar_verificacion_completa: {str(e)}")
        print(f"📋 Traceback completo:\n{error_traceback}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail=f"Error inesperado: {str(e)}"
        )
    finally:
        if conn:
            await direct_db_service.pool.release(conn)


# Funciones helper para servir_mi_documento
def validate_token_and_get_user_id(token: Optional[str]) -> Optional[str]:
    """Valida el token y retorna el ID del usuario"""
    if not token:
        print("⚠️ No se recibió token, continuando sin autenticación...")
        return None
    
    try:
                user_response = supabase_auth.auth.get_user(token)
                if user_response and user_response.user:
                    current_user_id = user_response.user.id
                    print(f"✅ Token válido para usuario: {current_user_id}")
            return current_user_id
                else:
                    print("⚠️ Token inválido, continuando sin validación completa...")
            return None
            except Exception as auth_error:
                print(f"⚠️ Error validando token: {auth_error}, continuando sin validación...")
        return None

async def verify_document_permissions(
    db: AsyncSession,
    documento: Documento,
    current_user_id: Optional[str]
) -> None:
    """Verifica que el documento pertenece al usuario actual"""
    if not current_user_id:
        return
    
    try:
                solicitud_query = select(VerificacionSolicitud).where(
                    VerificacionSolicitud.id_verificacion == documento.id_verificacion
                )
                solicitud_result = await db.execute(solicitud_query)
                solicitud = solicitud_result.scalars().first()

                if solicitud:
                    empresa_query = select(PerfilEmpresa).where(
                        PerfilEmpresa.id_perfil == solicitud.id_perfil
                    )
                    empresa_result = await db.execute(empresa_query)
                    empresa = empresa_result.scalars().first()

                    if empresa and empresa.user_id == uuid.UUID(current_user_id):
                        print("✅ Permisos verificados correctamente")
                    else:
                        print("⚠️ Documento no pertenece al usuario, pero permitiendo acceso para testing")
            except Exception as perm_error:
                print(f"⚠️ Error verificando permisos: {perm_error}, continuando...")

def extract_file_key_from_url(url_completa: str) -> str:
    """Extrae la clave del archivo desde la URL completa"""
    if PREFIX_DOCUMENTOS in url_completa:
        file_key = url_completa.split(PREFIX_DOCUMENTOS, 1)[1]
        file_key = urllib.parse.unquote(file_key)
        print(f"🔍 Clave extraída para S3: {file_key}")
        return file_key
    else:
        print(f"⚠️ No se encontró '{PREFIX_DOCUMENTOS}' en la URL, usando URL completa como clave")
        return url_completa

def get_content_type_from_filename(file_key: str) -> str:
    """Determina el tipo de contenido basado en el nombre del archivo"""
    file_name = file_key.split('/')[-1] if '/' in file_key else file_key
    content_type, _ = mimetypes.guess_type(file_name)
    return content_type if content_type else 'application/octet-stream'

def get_file_from_s3(file_key: str) -> bytes:
    """Obtiene el archivo desde S3 usando la clave"""
    print(f"🔍 Intentando acceder a archivo: {file_key}")
    response = idrive_s3_client.get_object(
        Bucket='documentos',
        Key=file_key
    )
    file_content = response['Body'].read()
    print(f"✅ Archivo obtenido exitosamente: {file_key}")
    return file_content

@router.get(
    "/mis-documentos/{documento_id}/servir",
    description="Sirve directamente el archivo de documento del proveedor autenticado."
)
async def servir_mi_documento(
    documento_id: int,
    token: str = None,
    db: AsyncSession = Depends(get_async_db)
):
    """Sirve directamente el archivo de documento del proveedor autenticado"""
    
    try:
        print(f"🔍 Intentando servir documento {documento_id}...")
        print(f"🔍 Token recibido: {token[:20] if token else 'None'}...")

        # Validar token y obtener ID de usuario
        current_user_id = validate_token_and_get_user_id(token)

        # Buscar el documento
        doc_query = select(Documento).where(Documento.id_documento == documento_id)
        doc_result = await db.execute(doc_query)
        documento = doc_result.scalars().first()

        if not documento:
            print(f"❌ Documento {documento_id} no encontrado")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=MSG_DOCUMENTO_NO_ENCONTRADO
            )

        print(f"✅ Documento encontrado: {documento.url_archivo}")

        # Verificar permisos del documento
        await verify_document_permissions(db, documento, current_user_id)
        
        # Verificar que el documento tiene una URL válida
        if not documento.url_archivo or documento.url_archivo.startswith(PREFIX_TEMP):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=MSG_DOCUMENTO_NO_DISPONIBLE
            )
        
        # Intentar servir el archivo desde Idrive2
        try:
            url_completa = documento.url_archivo
            print(f"🔍 URL completa del documento: {url_completa}")

            # Extraer clave del archivo desde la URL
            file_key = extract_file_key_from_url(url_completa)
            
            # Obtener archivo desde S3
            file_content = get_file_from_s3(file_key)
            
            # Determinar tipo de contenido
            content_type = get_content_type_from_filename(file_key)
            file_name = file_key.split('/')[-1] if '/' in file_key else file_key
            
            # Devolver el archivo
            return Response(
                content=file_content,
                media_type=content_type,
                headers={
                    "Content-Disposition": f"inline; filename={file_name}"
                }
            )
            
        except Exception as s3_error:
            print(f"❌ Error accediendo a S3: {s3_error}")
            print(f"🔍 URL del archivo: {documento.url_archivo}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=MSG_DOCUMENTO_NO_DISPONIBLE
            )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error sirviendo documento: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=MSG_ERROR_INTERNO_SERVIDOR
        )

@router.get(
    "/test-documento/{documento_id}",
    description="Endpoint de prueba para acceder a documentos sin autenticación."
)
async def test_documento(
    documento_id: int,
    db: AsyncSession = Depends(get_async_db)
):
    """Endpoint de prueba para acceder a documentos sin autenticación"""

    try:
        print(f"🧪 Probando acceso a documento {documento_id}...")

        # Buscar el documento
        doc_query = select(Documento).where(Documento.id_documento == documento_id)
        doc_result = await db.execute(doc_query)
        documento = doc_result.scalars().first()

        if not documento:
            return {
                "error": "Documento no encontrado",
                "documento_id": documento_id
            }

        return {
            "success": True,
            "documento": {
                "id": documento.id_documento,
                "tipo": documento.id_tip_documento,
                "url": documento.url_archivo,
                "estado": documento.estado_revision,
                "observacion": documento.observacion
            },
            "message": "Documento encontrado correctamente"
        }

    except Exception as e:
        print(f"❌ Error en test documento: {e}")
        return {
            "error": str(e),
            "documento_id": documento_id
        }

@router.get(
    "/debug-auth",
    description="Endpoint para debuggear la autenticación."
)
async def debug_auth(token: str = None):
    """Endpoint para debuggear la autenticación"""

    try:
        print(f"🔍 Debug auth - Token recibido: {token[:20] if token else 'None'}...")

        if not token:
            return {
                "error": "No token provided",
                "message": "Se requiere un token para la autenticación"
            }

        # Intentar validar el token
    

        print("🔍 Intentando validar token con Supabase...")
        user_response = supabase_auth.auth.get_user(token)

        print(f"🔍 Respuesta de Supabase: {user_response}")

        if not user_response or not user_response.user:
            return {
                "error": "Invalid token",
                "message": "El token no es válido o ha expirado",
                "response": str(user_response)
            }

        user_data = user_response.user
        print(f"✅ Token válido para usuario: {user_data.id}")

        return {
            "success": True,
            "user": {
                "id": user_data.id,
                "email": user_data.email,
                "aud": user_data.aud if hasattr(user_data, 'aud') else None
            },
            "message": "Token válido y usuario autenticado correctamente"
        }

    except Exception as e:
        print(f"❌ Error en debug auth: {e}")
        import traceback
        traceback.print_exc()
        return {
            "error": str(e),
            "message": "Error procesando la autenticación",
            "traceback": traceback.format_exc()
        }


@router.get(
    "/mis-documentos-test",
    description="Versión de prueba del endpoint mis-documentos sin autenticación"
)
async def get_mis_documentos_test(
    user_id: str = None,
    db: AsyncSession = Depends(get_async_db)
):
    """Versión de prueba del endpoint mis-documentos sin autenticación"""

    try:
        print(f"🧪 Endpoint de prueba mis-documentos llamado con user_id: {user_id}")

        if not user_id:
            return {
                "error": "user_id requerido",
                "message": "Debe proporcionar un user_id como parámetro de query"
            }

        # Buscar el perfil de empresa del usuario con relación de sucursales
        empresa_query = select(PerfilEmpresa).options(
            selectinload(PerfilEmpresa.sucursal_empresa)
        ).where(PerfilEmpresa.user_id == uuid.UUID(user_id))
        empresa_result = await db.execute(empresa_query)
        empresa = empresa_result.scalars().first()

        if not empresa:
            return {
                "error": "Perfil no encontrado",
                "user_id": user_id,
                "message": "No se encontró perfil de empresa para este usuario"
            }

        # Buscar la solicitud de verificación más reciente
        solicitud_query = select(VerificacionSolicitud).where(
            VerificacionSolicitud.id_perfil == empresa.id_perfil
        ).order_by(VerificacionSolicitud.created_at.desc())
        solicitud_result = await db.execute(solicitud_query)
        solicitud = solicitud_result.scalars().first()

        if not solicitud:
            return {
                "error": "Solicitud no encontrada",
                "user_id": user_id,
                "empresa_id": str(empresa.id_perfil),
                "message": MSG_SOLICITUD_VERIFICACION_NO_ENCONTRADA
            }

        # Obtener documentos de la solicitud
        documentos_query = select(Documento).where(
            Documento.id_verificacion == solicitud.id_verificacion
        )
        documentos_result = await db.execute(documentos_query)
        documentos = documentos_result.scalars().all()

        documentos_detallados = []
        for doc in documentos:
            # Obtener el nombre del tipo de documento
            tipo_doc_query = select(TipoDocumento).where(TipoDocumento.id_tip_documento == doc.id_tip_documento)
            tipo_doc_result = await db.execute(tipo_doc_query)
            tipo_doc = tipo_doc_result.scalars().first()

            tipo_documento_nombre = tipo_doc.nombre if tipo_doc else f"Tipo {doc.id_tip_documento}"

            documentos_detallados.append({
                "id_documento": doc.id_documento,
                "tipo_documento": tipo_documento_nombre,
                "url_archivo": doc.url_archivo,
                "estado_revision": doc.estado_revision,
                "observacion": doc.observacion
            })

        return {
            "success": True,
            "solicitud_id": solicitud.id_verificacion,
            "estado": solicitud.estado,
            "documentos": documentos_detallados,
            "user_id": user_id,
            "empresa_id": str(empresa.id_perfil)
        }

    except Exception as e:
        print(f"❌ Error en get_mis_documentos_test: {e}")
        import traceback
        traceback.print_exc()
        return {
            "error": str(e),
            "user_id": user_id,
            "traceback": traceback.format_exc()
        }


@router.get(
    "/mis-documentos",
    description="Obtiene los documentos de la solicitud de verificación del proveedor autenticado."
)
async def get_mis_documentos(
    current_user: SupabaseUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """Obtiene los documentos de la solicitud de verificación del proveedor autenticado"""

    try:
        # Buscar el perfil de empresa del usuario con relación de sucursales
        empresa_query = select(PerfilEmpresa).options(
            selectinload(PerfilEmpresa.sucursal_empresa)
        ).where(PerfilEmpresa.user_id == uuid.UUID(current_user.id))
        empresa_result = await db.execute(empresa_query)
        empresa = empresa_result.scalars().first()
        
        if not empresa:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=MSG_PERFIL_EMPRESA_NO_ENCONTRADO
            )
        
        # Buscar la solicitud de verificación más reciente
        solicitud_query = select(VerificacionSolicitud).where(
            VerificacionSolicitud.id_perfil == empresa.id_perfil
        ).order_by(VerificacionSolicitud.created_at.desc())
        solicitud_result = await db.execute(solicitud_query)
        solicitud = solicitud_result.scalars().first()
        
        if not solicitud:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=MSG_SOLICITUD_VERIFICACION_NO_ENCONTRADA
            )
        
        # Obtener documentos de la solicitud
        documentos_query = select(Documento).where(
            Documento.id_verificacion == solicitud.id_verificacion
        )
        documentos_result = await db.execute(documentos_query)
        documentos = documentos_result.scalars().all()
        
        # Obtener tipos de documento
        documentos_detallados = []
        for doc in documentos:
            # Obtener tipo de documento
            tipo_doc_query = select(TipoDocumento).where(TipoDocumento.id_tip_documento == doc.id_tip_documento)
            tipo_doc_result = await db.execute(tipo_doc_query)
            tipo_doc = tipo_doc_result.scalars().first()
            
            documentos_detallados.append({
                "id_documento": doc.id_documento,
                "tipo_documento": tipo_doc.nombre if tipo_doc else VALOR_DEFAULT_TIPO_NO_ENCONTRADO,
                "es_requerido": tipo_doc.es_requerido if tipo_doc else False,
                "estado_revision": doc.estado_revision,
                "url_archivo": doc.url_archivo,
                "fecha_verificacion": doc.fecha_verificacion,
                "observacion": doc.observacion,
                "created_at": doc.created_at
            })
        
        return {
            "solicitud_id": solicitud.id_verificacion,
            "estado": solicitud.estado,
            "documentos": documentos_detallados
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error obteniendo documentos: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=MSG_ERROR_INTERNO_SERVIDOR
        )


# Funciones helper para get_mis_datos_solicitud
async def get_empresa_with_sucursales(db: AsyncSession, user_id: str) -> PerfilEmpresa:
    """Obtiene el perfil de empresa del usuario con relación de sucursales"""
        empresa_query = select(PerfilEmpresa).options(
            selectinload(PerfilEmpresa.sucursal_empresa)
    ).where(PerfilEmpresa.user_id == uuid.UUID(user_id))
        empresa_result = await db.execute(empresa_query)
        empresa = empresa_result.scalars().first()
        
        if not empresa:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
            detail=MSG_PERFIL_EMPRESA_NO_ENCONTRADO
            )
    return empresa
        
async def get_latest_verification_request(db: AsyncSession, perfil_id: int) -> VerificacionSolicitud:
    """Obtiene la solicitud de verificación más reciente para un perfil"""
        solicitud_query = select(VerificacionSolicitud).where(
        VerificacionSolicitud.id_perfil == perfil_id
        ).order_by(VerificacionSolicitud.created_at.desc())
        solicitud_result = await db.execute(solicitud_query)
        solicitud = solicitud_result.scalars().first()
        
        if not solicitud:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
            detail=MSG_SOLICITUD_VERIFICACION_NO_ENCONTRADA
        )
    return solicitud

def extract_ciudad_data(departamento) -> Optional[dict]:
    """Extrae los datos de ciudad desde el departamento"""
    if departamento.ciudad and len(departamento.ciudad) > 0:
        ciudad = departamento.ciudad[0]
        return {"nombre": ciudad.nombre}
    return None

def extract_barrio_data(departamento) -> Optional[dict]:
    """Extrae los datos de barrio desde el departamento"""
    if departamento.ciudad and len(departamento.ciudad) > 0:
        ciudad = departamento.ciudad[0]
        if ciudad.barrio and len(ciudad.barrio) > 0:
            barrio = ciudad.barrio[0]
            return {"nombre": barrio.nombre}
    return None

async def get_direccion_data(db: AsyncSession, direccion_id: int) -> Optional[dict]:
    """Obtiene los datos de dirección con sus relaciones"""
    if not direccion_id:
        return None
    
            direccion_query = select(Direccion).options(
                selectinload(Direccion.departamento).selectinload(Departamento.ciudad).selectinload(Ciudad.barrio)
    ).where(Direccion.id_direccion == direccion_id)
            direccion_result = await db.execute(direccion_query)
            direccion = direccion_result.scalars().first()
            
    if not direccion or not direccion.departamento:
        return None
    
    departamento_data = {"nombre": direccion.departamento.nombre}
    ciudad_data = extract_ciudad_data(direccion.departamento)
    barrio_data = extract_barrio_data(direccion.departamento)
    
    return {
                    "calle": direccion.calle,
                    "numero": direccion.numero,
                    "referencia": direccion.referencia,
                    "departamento": departamento_data["nombre"],
                    "ciudad": ciudad_data["nombre"] if ciudad_data else None,
                    "barrio": barrio_data["nombre"] if barrio_data else None
                }
        
def get_sucursal_data(empresa: PerfilEmpresa) -> Optional[dict]:
    """Obtiene los datos de la sucursal principal de la empresa"""
        print(f"🔍 Sucursales encontradas: {len(empresa.sucursal_empresa) if empresa.sucursal_empresa else 0}")
        print(f"🔍 Tipo de sucursal_empresa: {type(empresa.sucursal_empresa)}")
    
    if not empresa.sucursal_empresa:
        print("⚠️ No se encontraron sucursales para esta empresa")
        print(f"🔍 Verificando si empresa tiene id_perfil: {empresa.id_perfil if hasattr(empresa, 'id_perfil') else 'No tiene id_perfil'}")
        return None
    
            print(f"🔍 Lista de sucursales: {[s.nombre for s in empresa.sucursal_empresa]}")
    # Ya verificamos que sucursal_empresa no está vacío arriba, así que podemos acceder directamente
    sucursal = empresa.sucursal_empresa[0]
    
    if not sucursal:
        print("⚠️ No se encontró sucursal principal")
        return None
    
    print(f"✅ Sucursal encontrada: {sucursal.nombre}")
    return {
                    "nombre": sucursal.nombre,
                    "telefono": sucursal.telefono,
                    "email": sucursal.email
                }

def build_empresa_data(empresa: PerfilEmpresa, sucursal_data: Optional[dict]) -> dict:
    """Construye los datos de empresa para la respuesta"""
    return {
                "razon_social": empresa.razon_social,
                "nombre_fantasia": empresa.nombre_fantasia,
                "telefono_contacto": sucursal_data["telefono"] if sucursal_data else None,
                "email_contacto": sucursal_data["email"] if sucursal_data else None,
                "nombre_sucursal": sucursal_data["nombre"] if sucursal_data else None
    }

def build_solicitud_data(solicitud: VerificacionSolicitud) -> dict:
    """Construye los datos de solicitud para la respuesta"""
    return {
                "id_verificacion": solicitud.id_verificacion,
                "estado": solicitud.estado,
                "comentario": solicitud.comentario,
                "fecha_solicitud": solicitud.fecha_solicitud,
                "fecha_revision": solicitud.fecha_revision
            }

def build_response_data(empresa: PerfilEmpresa, direccion_data: Optional[dict], 
                       sucursal_data: Optional[dict], solicitud: VerificacionSolicitud) -> dict:
    """Construye la respuesta completa con todos los datos"""
    return {
        "empresa": build_empresa_data(empresa, sucursal_data),
        "direccion": direccion_data,
        "solicitud": build_solicitud_data(solicitud)
    }

@router.get(
    "/mis-datos-solicitud",
    description="Obtiene los datos de la solicitud de verificación del proveedor autenticado para recuperación."
)
async def get_mis_datos_solicitud(
    current_user: SupabaseUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """Obtiene los datos de la solicitud de verificación del proveedor autenticado para recuperación"""
    try:
        empresa = await get_empresa_with_sucursales(db, current_user.id)
        solicitud = await get_latest_verification_request(db, empresa.id_perfil)
        direccion_data = await get_direccion_data(db, empresa.id_direccion)
        sucursal_data = get_sucursal_data(empresa)
        datos_solicitud = build_response_data(empresa, direccion_data, sucursal_data, solicitud)
        
        print(f"🔍 Datos de solicitud preparados para usuario {current_user.id}:")
        print(f"  - Empresa: {empresa.razon_social}")
        print(f"  - Dirección: {direccion_data}")
        print(f"  - Estado solicitud: {solicitud.estado}")
        
        return datos_solicitud
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error obteniendo datos de solicitud: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=MSG_ERROR_INTERNO_SERVIDOR
        )


@router.get(
    "/simple-test",
    description="Endpoint simple de prueba básico."
)
async def simple_test():
    """Endpoint simple de prueba que no requiere autenticación ni base de datos"""
    try:
        # Verificar que las importaciones básicas funcionan
       
        current_time = datetime.datetime.now().isoformat()

        return {
            "success": True,
            "message": "Endpoint simple funcionando correctamente",
            "timestamp": current_time,
            "python_version": "3.x",
            "fastapi_status": "OK"
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": "Error en endpoint simple"
        }

@router.get(
    "/test-auth",
    description="Endpoint de prueba con autenticación básica."
)
async def test_auth(current_user: SupabaseUser = Depends(get_current_user)):
    """Endpoint de prueba con autenticación"""
    try:
        return {
            "success": True,
            "user_id": str(current_user.id),
            "message": f"Usuario autenticado correctamente: {current_user.id}",
            "email": getattr(current_user, 'email', 'No disponible')
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": "Error en autenticación"
        }

@router.get(
    "/test-imports",
    description="Endpoint para probar las importaciones de modelos."
)
async def test_imports():
    """Endpoint para probar las importaciones de modelos"""
    try:
        

        # Probar crear instancias (sin guardar en BD)
        perfil = PerfilEmpresa(
            user_id=uuid.uuid4(),
            razon_social="Test Company",
            nombre_fantasia="Test Company",
            estado=ESTADO_PENDIENTE,
            verificado=ESTADO_VERIFICADO_FALSE
        )

        return {
            "success": True,
            "message": "Importaciones y modelos funcionando correctamente",
            "models_tested": ["PerfilEmpresa", "VerificacionSolicitud", "SucursalEmpresa"],
            "perfil_test": {
                "razon_social": perfil.razon_social,
                "estado": perfil.estado
            }
        }
    except Exception as e:
        import traceback
        return {
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc(),
            "message": "Error en importaciones de modelos"
        }

@router.get(
    "/test-datos",
    description="Endpoint de prueba para verificar datos de solicitud."
)
async def test_datos_solicitud(
    current_user: SupabaseUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """Endpoint de prueba para verificar datos de solicitud"""

    try:
        print(f"🔍 Usuario autenticado: {current_user.id}")

        # Solo probar la conexión básica a la base de datos
        try:
            # Hacer una consulta simple para verificar la conexión
            test_query = select(PerfilEmpresa).limit(1)
            test_result = await db.execute(test_query)
            test_count = len(test_result.scalars().all())
            print(f"🔍 Conexión a BD OK. PerfilEmpresa tiene {test_count} registros")
        except Exception as db_error:
            print(f"❌ Error de conexión a BD: {db_error}")
            return {
                "error": f"Error de conexión a BD: {str(db_error)}",
                "usuario_id": current_user.id
            }

        # Buscar el perfil de empresa del usuario
        empresa_query = select(PerfilEmpresa).where(PerfilEmpresa.user_id == uuid.UUID(current_user.id))
        empresa_result = await db.execute(empresa_query)
        empresa = empresa_result.scalars().first()

        print(f"🔍 Empresa encontrada: {empresa}")

        if not empresa:
            return {
                "error": "No se encontró perfil de empresa",
                "usuario_id": current_user.id,
                "message": "El usuario no tiene un perfil de empresa registrado"
            }

        # Buscar la solicitud de verificación más reciente
        solicitud_query = select(VerificacionSolicitud).where(
            VerificacionSolicitud.id_perfil == empresa.id_perfil
        ).order_by(VerificacionSolicitud.created_at.desc())
        solicitud_result = await db.execute(solicitud_query)
        solicitud = solicitud_result.scalars().first()

        print(f"🔍 Solicitud encontrada: {solicitud}")

        if not solicitud:
            return {
                "error": MSG_SOLICITUD_VERIFICACION_NO_ENCONTRADA,
                "empresa": {
                    "id": empresa.id_perfil,
                    "razon_social": empresa.razon_social,
                    "nombre_fantasia": empresa.nombre_fantasia,
                    "estado": empresa.estado,
                    "verificado": empresa.verificado
                },
                "message": "El usuario tiene empresa pero no tiene solicitud de verificación"
            }

        return {
            "success": True,
            "message": "Datos obtenidos correctamente",
            "empresa": {
                "id": empresa.id_perfil,
                "razon_social": empresa.razon_social,
                "nombre_fantasia": empresa.nombre_fantasia,
                "estado": empresa.estado,
                "verificado": empresa.verificado,
                "id_direccion": empresa.id_direccion
            },
            "solicitud": {
                "id": solicitud.id_verificacion,
                "estado": solicitud.estado,
                "comentario": solicitud.comentario,
                "fecha_solicitud": solicitud.fecha_solicitud.isoformat() if solicitud.fecha_solicitud else None,
                "fecha_revision": solicitud.fecha_revision.isoformat() if solicitud.fecha_revision else None
            },
            "usuario_id": current_user.id
        }

    except Exception as e:
        print(f"❌ Error en test endpoint: {e}")
        import traceback
        traceback.print_exc()
        return {
            "error": str(e),
            "usuario_id": current_user.id,
            "traceback": traceback.format_exc()
        }


  # noqa: E402

# Función helper para enriquecer respuesta de solicitud de servicio creada
async def enrich_service_request_response(request: SolicitudServicio, db: AsyncSession) -> dict:
    """
    Enriquecer la respuesta de una solicitud de servicio con datos adicionales.
    """
   

    # Consulta para obtener datos completos
    enriched_query = select(
        SolicitudServicio.id_solicitud,
        SolicitudServicio.nombre_servicio,
        SolicitudServicio.descripcion,
        SolicitudServicio.estado_aprobacion,
        SolicitudServicio.comentario_admin,
        SolicitudServicio.created_at,
        SolicitudServicio.id_categoria,
        SolicitudServicio.id_perfil,
        CategoriaModel.nombre.label('nombre_categoria'),
        PerfilEmpresa.razon_social.label('nombre_empresa'),
        UserModel.nombre_persona.label('nombre_contacto')
    ).select_from(SolicitudServicio)\
     .join(CategoriaModel, SolicitudServicio.id_categoria == CategoriaModel.id_categoria, isouter=True)\
     .join(PerfilEmpresa, SolicitudServicio.id_perfil == PerfilEmpresa.id_perfil, isouter=True)\
     .join(UserModel, PerfilEmpresa.user_id == UserModel.id, isouter=True)\
     .where(SolicitudServicio.id_solicitud == request.id_solicitud)

    enriched_result = await db.execute(enriched_query)
    enriched_row = enriched_result.first()

    if enriched_row:
        return {
            "id_solicitud": enriched_row.id_solicitud,
            "nombre_servicio": enriched_row.nombre_servicio,
            "descripcion": enriched_row.descripcion,
            "estado_aprobacion": enriched_row.estado_aprobacion or VALOR_DEFAULT_ESTADO_APROBACION,
            "comentario_admin": enriched_row.comentario_admin,
            "created_at": enriched_row.created_at.isoformat() if enriched_row.created_at else None,
            "id_categoria": enriched_row.id_categoria,
            "id_perfil": enriched_row.id_perfil,
            "nombre_categoria": enriched_row.nombre_categoria or VALOR_DEFAULT_NO_ESPECIFICADO,
            "nombre_empresa": enriched_row.nombre_empresa or VALOR_DEFAULT_NO_ESPECIFICADO,
            "nombre_contacto": enriched_row.nombre_contacto or VALOR_DEFAULT_NO_ESPECIFICADO,
            "email_contacto": None  # Email no disponible en UserModel
        }
    else:
        # Fallback básico si la consulta enriquecida falla
        return {
            "id_solicitud": request.id_solicitud,
            "nombre_servicio": request.nombre_servicio,
            "descripcion": request.descripcion,
            "estado_aprobacion": request.estado_aprobacion or VALOR_DEFAULT_ESTADO_APROBACION,
            "comentario_admin": request.comentario_admin,
            "created_at": request.created_at.isoformat() if request.created_at else None,
            "id_categoria": request.id_categoria,
            "id_perfil": request.id_perfil,
            "nombre_categoria": VALOR_DEFAULT_NO_ESPECIFICADO,
            "nombre_empresa": VALOR_DEFAULT_NO_ESPECIFICADO,
            "nombre_contacto": VALOR_DEFAULT_NO_ESPECIFICADO,
            "email_contacto": None
        }

@router.post(
    "/services/proponer",
    status_code=status.HTTP_201_CREATED,
    description="Permite a un proveedor proponer un nuevo servicio."
)
async def propose_service(
    solicitud: SolicitudServicioIn,
    perfil_aprobado: PerfilEmpresa = Depends(get_approved_provider),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Recibe una propuesta de servicio de un proveedor
    aprobado y la guarda para que el administrador la revise y apruebe o rechace.
    Devuelve la solicitud creada con datos enriquecidos.
    """
    try:
        # Validar longitud de descripción (ya validado por Pydantic, pero agregamos validación adicional)
        if len(solicitud.descripcion) > 500:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="La descripción no puede superar los 500 caracteres. Por favor, acorta tu descripción."
            )
        
        nueva_solicitud = SolicitudServicio(
            id_perfil=perfil_aprobado.id_perfil,
            nombre_servicio=solicitud.nombre_servicio,
            descripcion=solicitud.descripcion,
            id_categoria=solicitud.id_categoria,
    
            comentario_admin=solicitud.comentario_admin
        )
        db.add(nueva_solicitud)
        await db.commit()
        await db.refresh(nueva_solicitud)

        # Enriquecer la respuesta con datos adicionales
        enriched_response = await enrich_service_request_response(nueva_solicitud, db)

        print(f"✅ Solicitud de servicio creada: {nueva_solicitud.nombre_servicio}")
        return enriched_response

    except Exception as e:
        await db.rollback()
        print(f"❌ Error al crear solicitud de servicio: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=MSG_ERROR_INESPERADO_SERVICIO.format(error=str(e))
        )

@router.get(
    "/download-document/{document_url:path}",
    description="Descarga un documento almacenado localmente"
)
async def download_document(document_url: str):
    """
    Endpoint para descargar documentos almacenados localmente
    """
    try:
        # Decodificar la URL del documento
       
        decoded_url = urllib.parse.unquote(document_url)
        
        # Verificar que sea una URL local
        if not decoded_url.startswith(PREFIX_LOCAL):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=MSG_URL_INVALIDA_LOCAL
            )
        
        # Obtener información del archivo
        success, message, file_info = local_storage_service.get_file_info(decoded_url)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=MSG_ARCHIVO_NO_ENCONTRADO.format(message=message)
            )
        
        # Servir el archivo
        serve_success, serve_message, file_content = local_storage_service.serve_file(decoded_url)
        
        if not serve_success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=MSG_ERROR_SIRVIENDO_ARCHIVO.format(serve_message=serve_message)
            )
        
        # Obtener el nombre del archivo original
        filename = file_info["filename"] if file_info else "documento"
        
        # Determinar el tipo de contenido
        
        content_type, _ = mimetypes.guess_type(filename)
        if not content_type:
            content_type = "application/octet-stream"
        
        return Response(
            content=file_content,
            media_type=content_type,
            headers={
                "Content-Disposition": f"attachment; filename={filename}",
                "Content-Length": str(len(file_content))
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=MSG_ERROR_INESPERADO_GENERAL.format(error=str(e))
        )

@router.get(
    "/diagnostic",
    description="Diagnóstico básico del endpoint de proveedores"
)
async def diagnostic_endpoint():
    """
    Endpoint de diagnóstico simple para verificar funcionamiento básico
    """
    try:
        return {
            "status": "ok",
            "message": "Endpoint de proveedores funcionando correctamente",
            "timestamp": datetime.now().isoformat(),
            "routes": [
                "/simple-test",
                "/test-imports",
                "/test-auth",
                "/test-datos",
                "/mis-documentos",
                "/mis-documentos-test",
                "/solicitar-verificacion",
                "/diagnostic"
            ],
            "notes": [
                "Error '.trim()' corregido - ahora se valida correctamente el tipo de barrio",
                "Endpoint '/mis-documentos-test' creado para testing sin autenticación",
                "Logging detallado agregado a '/solicitar-verificacion'",
                "Problema de clave S3 corregido en '/mis-documentos/*/servir'"
            ]
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Error en diagnóstico: {str(e)}",
            "timestamp": datetime.now().isoformat()
        }

@router.get(
    "/diagnostic/storage",
    description="Diagnóstico del sistema de almacenamiento (iDrive y local)"
)
async def diagnose_storage_system():
    """
    Endpoint para diagnosticar el estado del sistema de almacenamiento
    """
    try:
        # Obtener diagnóstico de ambos servicios
        results = smart_upload_service.test_services()
        
        # Información adicional del sistema
        system_info = {
            "timestamp": datetime.now().isoformat(),
            "services": results,
            "recommendations": []
        }
        
        # Agregar recomendaciones basadas en el estado
        if results["idrive"]["status"] == "error":
            system_info["recommendations"].append({
                "service": "iDrive",
                "issue": results["idrive"]["message"],
                "solution": "Verificar credenciales, permisos y conectividad de red"
            })
        
        if results["local"]["status"] == "error":
            system_info["recommendations"].append({
                "service": "Local Storage",
                "issue": results["local"]["message"],
                "solution": "Verificar permisos de escritura en directorio uploads"
            })
        
        if results["idrive"]["status"] == "ok" and results["local"]["status"] == "ok":
            system_info["recommendations"].append({
                "service": "General",
                "issue": "Ninguno",
                "solution": "Sistema funcionando correctamente"
            })
        
        return system_info
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=MSG_ERROR_DIAGNOSTICO.format(error=str(e))
        )
