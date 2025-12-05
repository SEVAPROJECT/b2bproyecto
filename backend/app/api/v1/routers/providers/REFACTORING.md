# Refactorización del Módulo de Proveedores

## Resumen

Este documento describe la refactorización completa del archivo `providers.py` que violaba severamente los principios SRP (Single Responsibility Principle) y DRY (Don't Repeat Yourself).

## Problemas Identificados

### Violaciones de SRP
- **1,871 líneas** en un solo archivo
- **~60 funciones/endpoints** mezcladas
- **10+ responsabilidades diferentes**:
  - Gestión de solicitudes de verificación
  - Gestión de documentos
  - Gestión de direcciones
  - Gestión de sucursales
  - Gestión de empresas
  - Gestión de solicitudes de servicios
  - Endpoints de prueba/diagnóstico
  - Validación de permisos
  - Construcción de respuestas
  - Consultas a base de datos (ORM y SQL directo)

### Violaciones de DRY
- Duplicación entre funciones ORM y SQL directo:
  - `create_direccion_with_retry` vs `create_or_update_direccion_sql`
  - `update_or_create_sucursal` vs `create_or_update_sucursal_sql`
  - `process_documents` vs `process_documents_sql`
- Creación dinámica de objetos repetida en 5 lugares diferentes
- Lógica de consultas duplicada en múltiples endpoints
- Patrones de manejo de errores repetidos

## Solución Implementada

### Estructura Nueva - Arquitectura de Capas

```
app/
├── api/v1/routers/providers/          # CAPA DE PRESENTACIÓN (Presentation Layer)
│   ├── __init__.py
│   ├── providers.py                  # Router principal (consolida todos)
│   ├── verification_router.py        # Endpoints de verificación
│   ├── documents_router.py            # Endpoints de documentos
│   ├── services_router.py            # Endpoints de servicios
│   ├── diagnostic_router.py          # Endpoints de diagnóstico/pruebas
│   ├── constants.py                  # Constantes compartidas
│   └── utils.py                      # Utilidades compartidas
│
├── services/                          # CAPA DE LÓGICA DE NEGOCIO (Business Logic Layer)
│   ├── storage_service.py             # Servicio de almacenamiento (iDrive/Local)
│   └── providers/                     # Servicios específicos de proveedores
│       ├── __init__.py
│       ├── verification_service.py    # Lógica de verificación
│       ├── document_service.py        # Lógica de documentos
│       ├── address_service.py         # Lógica de direcciones
│       └── company_service.py         # Lógica de empresas y sucursales
│
└── repositories/providers/            # CAPA DE ACCESO A DATOS (Data Access Layer)
    ├── __init__.py
    └── provider_repository.py         # Repositorio unificado para acceso a datos
```

### Arquitectura de Capas (Layered Architecture)

Hemos implementado una **Arquitectura de Capas** clara que separa las responsabilidades en tres niveles:

#### 1. **Capa de Presentación** (Presentation Layer)
**Ubicación**: `app/api/v1/routers/providers/`

**Responsabilidad**: Manejar las peticiones HTTP, validar entrada, y formatear respuestas.

- `verification_router.py`: Endpoints relacionados con solicitudes de verificación
- `documents_router.py`: Endpoints relacionados con documentos
- `services_router.py`: Endpoints relacionados con propuestas de servicios
- `diagnostic_router.py`: Endpoints de diagnóstico y pruebas
- `providers.py`: Router principal que consolida todos los routers
- `constants.py`: Constantes compartidas
- `utils.py`: Utilidades compartidas

**Flujo**: Recibe request → Valida → Llama a Service → Retorna response

#### 2. **Capa de Lógica de Negocio** (Business Logic Layer)
**Ubicación**: `app/services/providers/`

**Responsabilidad**: Contener la lógica de negocio, orquestar operaciones complejas, y aplicar reglas de negocio.

**Servicios Generales:**
- `StorageService`: Gestiona subida de archivos (iDrive/Local con fallback automático)

**Servicios Específicos de Proveedores:**
- `VerificationService`: Orquesta el proceso completo de verificación
- `DocumentService`: Maneja procesamiento de documentos (usa StorageService para subir archivos)
- `AddressService`: Gestiona creación y actualización de direcciones
- `CompanyService`: Gestiona empresas y sucursales

**Flujo**: Recibe datos del Router → Aplica lógica de negocio → Usa StorageService si necesita subir archivos → Llama a Repository → Retorna resultado

#### 3. **Capa de Acceso a Datos** (Data Access Layer)
**Ubicación**: `app/repositories/providers/`

**Responsabilidad**: Abstraer el acceso a la base de datos, ejecutar consultas, y mapear datos.

- `ProviderRepository`: Centraliza todas las consultas a la base de datos
  - Métodos para SQL directo (asyncpg)
  - Métodos para ORM (SQLAlchemy)
  - Elimina duplicación entre ambos enfoques

**Flujo**: Recibe parámetros del Service → Ejecuta consulta SQL/ORM → Retorna datos

### Flujo de Datos Completo

```
HTTP Request
    ↓
[Router] → Valida entrada, maneja HTTP
    ↓
[Service] → Aplica lógica de negocio, orquesta operaciones
    ↓
[Repository] → Accede a base de datos
    ↓
[Database]
    ↓
[Repository] → Retorna datos
    ↓
[Service] → Procesa y transforma datos
    ↓
[Router] → Formatea respuesta HTTP
    ↓
HTTP Response
```

### Principios Aplicados

1. **Separación de Responsabilidades (SRP)**: Cada capa tiene una responsabilidad única
2. **Inversión de Dependencias**: Las capas superiores dependen de abstracciones de las inferiores
3. **Bajo Acoplamiento**: Las capas se comunican a través de interfaces claras
4. **Alta Cohesión**: Cada capa agrupa funcionalidades relacionadas

## Beneficios

### 1. Mantenibilidad
- Cada archivo tiene una responsabilidad clara
- Fácil localizar y modificar funcionalidad específica
- Código más legible y organizado

### 2. Testabilidad
- Servicios pueden ser probados independientemente
- Repositorio puede ser mockeado fácilmente
- Routers son más simples y fáciles de testear

### 3. Escalabilidad
- Fácil agregar nuevos endpoints sin modificar código existente
- Servicios pueden ser reutilizados en otros módulos
- Repositorio puede ser extendido sin afectar lógica de negocio

### 4. Eliminación de Duplicación
- Una sola implementación de cada funcionalidad
- Lógica compartida en servicios y repositorio
- Constantes centralizadas

## Migración

### Endpoints Mantenidos
Todos los endpoints existentes se mantienen con las mismas rutas:
- `POST /providers/solicitar-verificacion`
- `GET /providers/mis-documentos`
- `GET /providers/mis-documentos/{documento_id}/servir`
- `GET /providers/mis-datos-solicitud`
- `POST /providers/services/proponer`
- `GET /providers/download-document/{document_url:path}`
- `GET /providers/diagnostic`
- `GET /providers/diagnostic/storage`

### Endpoints de Diagnóstico Separados
Los endpoints de diagnóstico y pruebas fueron movidos a `diagnostic_router.py`:
- `GET /providers/diagnostic` - Diagnóstico básico del módulo
- `GET /providers/diagnostic/storage` - Diagnóstico del sistema de almacenamiento

**Nota**: Estos endpoints pueden ser deshabilitados en producción si es necesario, simplemente comentando la línea `router.include_router(diagnostic_router)` en `providers.py`.

### Endpoints Eliminados
Los siguientes endpoints de prueba fueron eliminados del código original (pueden ser recreados si es necesario):
- `GET /providers/test-documento/{documento_id}`
- `GET /providers/debug-auth`
- `GET /providers/mis-documentos-test`
- `GET /providers/simple-test`
- `GET /providers/test-auth`
- `GET /providers/test-imports`
- `GET /providers/test-datos`

## Próximos Pasos Recomendados

1. **Eliminar código ORM duplicado**: Elegir entre SQL directo o ORM, no ambos
2. **Crear tests unitarios**: Para cada servicio y repositorio
3. **Documentar APIs**: Agregar documentación OpenAPI más detallada
4. **Optimizar consultas**: Revisar y optimizar consultas SQL
5. **Agregar logging estructurado**: Reemplazar prints por logging apropiado

## Notas Técnicas

- Se mantiene compatibilidad con `direct_db_service` para evitar problemas con PgBouncer
- Los servicios usan SQL directo (asyncpg) para operaciones críticas
- Los repositorios mantienen métodos ORM para consultas simples
- Todas las transacciones se manejan correctamente con `async with conn.transaction()`

