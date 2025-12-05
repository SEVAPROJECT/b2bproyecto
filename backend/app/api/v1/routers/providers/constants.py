# app/api/v1/routers/providers/constants.py
"""
Constantes compartidas para el módulo de proveedores.
"""

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
COORDENADAS_ASUNCION_WKT = 'POINT(-57.5759 -25.2637)'
COORDENADAS_ASUNCION_SRID = 4326

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

