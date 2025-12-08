# app/services/providers/verification_service.py
"""
Servicio para gestión de solicitudes de verificación de proveedores.
Capa de Lógica de Negocio - Contiene todas las validaciones y reglas de negocio.
"""

from typing import Optional, List
import asyncpg
import json
from fastapi import HTTPException, status, UploadFile

from app.models.empresa.verificacion_solicitud import VerificacionSolicitud
from app.repositories.providers.provider_repository import ProviderRepository
from app.services.providers.company_service import CompanyService
from app.services.providers.document_service import DocumentService
from app.api.v1.routers.providers.constants import (
    ESTADO_PENDIENTE,
    MSG_ERROR_JSON_INVALIDO,
    MSG_ERROR_NUMERO_DOCUMENTOS,
    FILENAME_EMPTY
)
from app.services.direct_db_service import direct_db_service


class VerificationService:
    """Servicio para gestión de solicitudes de verificación - Lógica de Negocio"""
    
    @staticmethod
    def parse_and_validate_profile(perfil_in: str) -> dict:
        """
        Parsea y valida el JSON del perfil.
        Validación de formato - parte de la lógica de negocio.
        """
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

    @staticmethod
    def validate_documents_count(nombres_tip_documento: List[str], documentos: List[UploadFile]) -> None:
        """
        Valida que la cantidad de nombres de tipos de documento coincide con la de los archivos.
        Validación de negocio - debe estar en la capa de servicios.
        """
        if len(nombres_tip_documento) != len(documentos):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=MSG_ERROR_NUMERO_DOCUMENTOS
            )

    @staticmethod
    def filter_valid_documents(documentos: List[UploadFile], nombres_tip_documento: List[str]) -> tuple:
        """
        Filtra documentos vacíos y retorna documentos y nombres válidos.
        Lógica de negocio - procesamiento de documentos.
        """
        documentos_validos = []
        nombres_tip_documento_validos = []
        
        for i, doc in enumerate(documentos):
            if doc.filename != FILENAME_EMPTY and doc.size > 0:
                documentos_validos.append(doc)
                nombres_tip_documento_validos.append(nombres_tip_documento[i])
            else:
                print(f"⚠️ Documento vacío filtrado: {doc.filename}")
        
        return documentos_validos, nombres_tip_documento_validos


    @staticmethod
    async def process_verification_request(
        perfil_in: str,
        nombres_tip_documento: List[str],
        documentos: List[UploadFile],
        comentario_solicitud: Optional[str],
        current_user_id: str
    ) -> dict:
        """
        Procesa una solicitud de verificación completa.
        Orquesta toda la lógica de negocio y validaciones.
        
        Args:
            perfil_in: JSON string con los datos del perfil
            nombres_tip_documento: Lista de nombres de tipos de documento
            documentos: Lista de archivos de documentos
            comentario_solicitud: Comentario opcional
            current_user_id: ID del usuario actual
            
        Returns:
            dict: Mensaje de éxito
        """
        conn: Optional[asyncpg.Connection] = None
        try:
            print("🚀 Iniciando solicitud de verificación...")
            print(f"👤 Usuario: {current_user_id}")
            
            # VALIDACIONES DE NEGOCIO (Capa de Servicios)
            # 1. Parsear y validar formato JSON
            perfil_data = VerificationService.parse_and_validate_profile(perfil_in)
            print(f"📄 Perfil recibido: {perfil_in[:200]}...")
            
            # 2. Validar cantidad de documentos
            VerificationService.validate_documents_count(nombres_tip_documento, documentos)
            print(f"📎 Archivos: {len(documentos)} archivos")
            print(f"📝 Nombres tipos documento: {nombres_tip_documento}")
            
            # 3. Filtrar documentos válidos (lógica de negocio)
            documentos, nombres_tip_documento = VerificationService.filter_valid_documents(
                documentos, nombres_tip_documento
            )
            print(f"📎 Documentos válidos para procesar: {len(documentos)}")
            print(f"💬 Comentario: {comentario_solicitud}")

            # Obtener conexión
            conn = await direct_db_service.get_connection()
            
            # Usar transacción para todas las operaciones
            async with conn.transaction():
                # 4. Obtener perfil de usuario y razón social
                print("🔍 Obteniendo perfil de usuario...")
                user_profile = await ProviderRepository.get_user_profile(current_user_id)
                razon_social = user_profile.nombre_empresa
                print(f"✅ Perfil de usuario obtenido. Razón social: {razon_social}")
                
                # 5. Validar unicidad de empresa (regla de negocio)
                print("🔍 Validando unicidad de empresa...")
                empresa_existente = await ProviderRepository.validate_company_uniqueness(
                    razon_social, perfil_data['nombre_fantasia'], current_user_id
                )
                print(f"✅ Validación de unicidad completada. Empresa existente: {empresa_existente is not None}")
                
                # 6. Buscar datos de ubicación
                print(f"🔍 Buscando datos de ubicación: {perfil_data['direccion']}")
                departamento, ciudad, barrio = await ProviderRepository.find_location_data(
                    perfil_data['direccion']
                )
                print(f"✅ Datos de ubicación encontrados. Departamento: {departamento.nombre}, Ciudad: {ciudad.nombre}, Barrio: {barrio.nombre if barrio else 'N/A'}")
                
                # 7. Determinar si hay empresa existente del mismo usuario
                id_perfil_existente = None
                id_direccion_existente = None
                if empresa_existente and str(empresa_existente['user_id']) == current_user_id:
                    print(f"🔍 Actualizando empresa existente para reenvío: {empresa_existente['razon_social']}")
                    id_perfil_existente = empresa_existente['id_perfil']
                    id_direccion_existente = empresa_existente['id_direccion']
                
                # 8. Crear o actualizar dirección (usando repositorio)
                from app.api.v1.routers.providers.constants import COORDENADAS_ASUNCION_WKT, COORDENADAS_ASUNCION_SRID
                nueva_direccion_id = await ProviderRepository.create_or_update_direccion(
                    conn, perfil_data, departamento, ciudad, barrio, id_direccion_existente,
                    COORDENADAS_ASUNCION_WKT, COORDENADAS_ASUNCION_SRID
                )
                
                # 9. Crear o actualizar empresa (usando repositorio)
                from app.api.v1.routers.providers.constants import ESTADO_VERIFICADO_FALSE
                id_perfil_final = await ProviderRepository.create_or_update_empresa(
                    conn, current_user_id, razon_social, perfil_data['nombre_fantasia'],
                    nueva_direccion_id, id_perfil_existente, ESTADO_PENDIENTE, ESTADO_VERIFICADO_FALSE
                )
                
                if id_perfil_existente is None:
                    print(f"✅ Nueva empresa creada con ID: {id_perfil_final}")
                
                # 10. Crear o actualizar sucursal (usando repositorio)
                from app.api.v1.routers.providers.constants import NOMBRE_SUCURSAL_DEFAULT
                await ProviderRepository.create_or_update_sucursal(
                    conn, perfil_data, id_perfil_final, nueva_direccion_id, NOMBRE_SUCURSAL_DEFAULT
                )
                
                # 11. Crear solicitud de verificación (usando repositorio)
                nueva_solicitud = await ProviderRepository.create_verification_request(
                    conn, id_perfil_final, comentario_solicitud, ESTADO_PENDIENTE
                )
                id_verificacion = nueva_solicitud['id_verificacion']
                print(f"🔍 Nueva solicitud creada: {id_verificacion} para empresa: {razon_social}")
                
                # 12. Copiar RUC aprobado a documentos (si existe)
                # El RUC ya fue verificado durante el registro, así que lo copiamos automáticamente
                ruc_aprobado = await ProviderRepository.get_approved_ruc_for_user(conn, current_user_id)
                if ruc_aprobado:
                    print(f"📄 RUC aprobado encontrado, copiando a documentos de la solicitud...")
                    # Verificar si ya existe un documento RUC en esta solicitud
                    doc_ruc_existente = await conn.fetchrow("""
                        SELECT d.id_documento 
                        FROM documento d
                        INNER JOIN tipo_documento td ON d.id_tip_documento = td.id_tip_documento
                        WHERE d.id_verificacion = $1 
                            AND td.tipo_documento = 'Constancia de RUC'
                        LIMIT 1
                    """, id_verificacion)
                    
                    if not doc_ruc_existente:
                        # Crear documento RUC en la solicitud (ya está aprobado, así que estado = 'aprobado')
                        await ProviderRepository.create_document(
                            conn, id_verificacion, ruc_aprobado['id_tip_documento'],
                            ruc_aprobado['url_documento'], 'aprobado'
                        )
                        print(f"✅ RUC copiado a documentos de la solicitud (estado: aprobado)")
                    else:
                        print(f"⚠️ RUC ya existe en los documentos de la solicitud, omitiendo copia")
                else:
                    print(f"ℹ️ No se encontró RUC aprobado para el usuario (puede ser usuario legacy)")
                
                # 13. Procesar documentos (lógica de negocio + acceso a datos)
                id_perfil_para_docs = id_perfil_existente if empresa_existente and str(empresa_existente['user_id']) == current_user_id else None
                await DocumentService.process_documents(
                    conn, documentos, nombres_tip_documento, razon_social, 
                    id_verificacion, id_perfil_para_docs, current_user_id
                )
            
            # La transacción se confirma automáticamente al salir del bloque
            
            if empresa_existente and str(empresa_existente['user_id']) == current_user_id:
                from app.api.v1.routers.providers.constants import MSG_SOLICITUD_REENVIADA
                return {"message": MSG_SOLICITUD_REENVIADA}
            else:
                from app.api.v1.routers.providers.constants import MSG_SOLICITUD_CREADA
                return {"message": MSG_SOLICITUD_CREADA}
                
        finally:
            if conn:
                await direct_db_service.pool.release(conn)

    @staticmethod
    def build_solicitud_data(solicitud: VerificacionSolicitud) -> dict:
        """Construye los datos de solicitud para la respuesta"""
        return {
            "id_verificacion": solicitud.id_verificacion,
            "estado": solicitud.estado,
            "comentario": solicitud.comentario,
            "fecha_solicitud": solicitud.fecha_solicitud,
            "fecha_revision": solicitud.fecha_revision
        }

    @staticmethod
    def build_response_data(
        empresa: dict,
        direccion_data: Optional[dict],
        sucursal_data: Optional[dict],
        solicitud: VerificacionSolicitud
    ) -> dict:
        """Construye la respuesta completa con todos los datos"""
        empresa_data = CompanyService.build_empresa_data(
            type('PerfilEmpresa', (), empresa)(), sucursal_data
        )
        
        return {
            "empresa": empresa_data,
            "direccion": direccion_data,
            "solicitud": VerificationService.build_solicitud_data(solicitud)
        }
