# Arquitectura de Capas - Módulo de Proveedores

## Visión General

Este módulo implementa una **Arquitectura de Capas (Layered Architecture)** que separa claramente las responsabilidades en tres niveles:

1. **Capa de Presentación** (Routers)
2. **Capa de Lógica de Negocio** (Services)
3. **Capa de Acceso a Datos** (Repositories)

## Diagrama de Capas

```
┌─────────────────────────────────────────────────────────┐
│           CAPA DE PRESENTACIÓN (Routers)                │
│  - Maneja peticiones HTTP                               │
│  - Valida entrada                                        │
│  - Formatea respuestas                                  │
│  - Maneja autenticación/autorización                   │
└───────────────────┬─────────────────────────────────────┘
                    │
                    ↓
┌─────────────────────────────────────────────────────────┐
│        CAPA DE LÓGICA DE NEGOCIO (Services)             │
│  - Contiene reglas de negocio                           │
│  - Orquesta operaciones complejas                       │
│  - Valida lógica de negocio                             │
│  - Coordina múltiples repositorios                      │
└───────────────────┬─────────────────────────────────────┘
                    │
                    ↓
┌─────────────────────────────────────────────────────────┐
│        CAPA DE ACCESO A DATOS (Repositories)            │
│  - Abstrae acceso a base de datos                       │
│  - Ejecuta consultas SQL/ORM                            │
│  - Mapea datos entre BD y modelos                       │
│  - Maneja transacciones                                 │
└───────────────────┬─────────────────────────────────────┘
                    │
                    ↓
            ┌───────────────┐
            │   DATABASE    │
            └───────────────┘
```

## Estructura de Directorios

```
app/
├── api/v1/routers/providers/          # Capa de Presentación
│   ├── providers.py                  # Router principal
│   ├── verification_router.py         # Endpoints de verificación
│   ├── documents_router.py          # Endpoints de documentos
│   ├── services_router.py           # Endpoints de servicios
│   ├── diagnostic_router.py         # Endpoints de diagnóstico
│   ├── constants.py                 # Constantes
│   └── utils.py                     # Utilidades
│
├── services/                          # Capa de Lógica de Negocio
│   ├── storage_service.py            # Servicio de almacenamiento (iDrive/Local)
│   └── providers/                    # Servicios específicos de proveedores
│       ├── verification_service.py   # Lógica de verificación
│       ├── document_service.py        # Lógica de documentos
│       ├── address_service.py        # Lógica de direcciones
│       └── company_service.py        # Lógica de empresas
│
└── repositories/providers/           # Capa de Acceso a Datos
    └── provider_repository.py        # Acceso a datos
```

## Responsabilidades por Capa

### Capa de Presentación (Routers)

**¿Qué hace?**
- Recibe peticiones HTTP
- Valida parámetros de entrada
- Maneja autenticación y autorización
- Formatea respuestas HTTP
- Maneja errores HTTP

**¿Qué NO hace?**
- No contiene lógica de negocio
- No accede directamente a la base de datos
- No realiza transformaciones complejas de datos

**Ejemplo:**
```python
@router.post("/solicitar-verificacion")
async def solicitar_verificacion_completa(...):
    # 1. Valida entrada
    perfil_data = parse_and_validate_profile(perfil_in)
    
    # 2. Llama al servicio
    result = await VerificationService.process_verification_request(...)
    
    # 3. Retorna respuesta
    return result
```

### Capa de Lógica de Negocio (Services)

**¿Qué hace?**
- Contiene reglas de negocio
- Orquesta operaciones complejas
- Coordina múltiples repositorios
- Valida lógica de negocio
- Transforma datos según reglas de negocio

**¿Qué NO hace?**
- No maneja HTTP directamente
- No ejecuta consultas SQL directamente
- No formatea respuestas HTTP

**Ejemplo:**
```python
class VerificationService:
    @staticmethod
    async def process_verification_request(...):
        # 1. Obtiene datos del repositorio
        user_profile = await ProviderRepository.get_user_profile(...)
        
        # 2. Aplica lógica de negocio
        empresa_existente = await ProviderRepository.validate_company_uniqueness(...)
        
        # 3. Orquesta operaciones
        # 4. Coordina múltiples repositorios
        # 5. Retorna resultado procesado
```

### Capa de Acceso a Datos (Repositories)

**¿Qué hace?**
- Abstrae acceso a base de datos
- Ejecuta consultas SQL/ORM
- Mapea datos entre BD y modelos
- Maneja transacciones
- Optimiza consultas

**¿Qué NO hace?**
- No contiene lógica de negocio
- No valida reglas de negocio
- No formatea respuestas

**Ejemplo:**
```python
class ProviderRepository:
    @staticmethod
    async def get_user_profile(user_id: str):
        # Solo acceso a datos
        conn = await direct_db_service.get_connection()
        user_row = await conn.fetchrow("SELECT ... FROM users WHERE id = $1", user_id)
        return user_profile
```

## Flujo de Datos

### Flujo Típico de una Petición

```
1. HTTP Request llega al Router
   ↓
2. Router valida entrada (parámetros, autenticación)
   ↓
3. Router llama al Service correspondiente
   ↓
4. Service aplica lógica de negocio
   ↓
5a. Si necesita subir archivos → Service usa StorageService
   ↓
5b. Si necesita datos → Service llama a Repository
   ↓
6. Repository ejecuta consulta a BD / StorageService sube archivo
   ↓
7. Repository/StorageService retorna datos/URL al Service
   ↓
8. Service procesa y transforma datos
   ↓
9. Service retorna resultado al Router
   ↓
10. Router formatea respuesta HTTP
   ↓
11. HTTP Response enviado al cliente
```

## Ventajas de esta Arquitectura

### 1. **Separación de Responsabilidades**
- Cada capa tiene una responsabilidad clara
- Fácil entender qué hace cada componente
- Cambios en una capa no afectan otras

### 2. **Testabilidad**
- Cada capa puede ser testeada independientemente
- Fácil mockear dependencias
- Tests más rápidos y aislados

### 3. **Mantenibilidad**
- Código organizado y fácil de encontrar
- Cambios localizados en la capa correspondiente
- Fácil agregar nuevas funcionalidades

### 4. **Escalabilidad**
- Fácil agregar nuevos endpoints (Router)
- Fácil agregar nueva lógica (Service)
- Fácil cambiar implementación de BD (Repository)

### 5. **Reutilización**
- Servicios pueden ser reutilizados por múltiples routers
- Repositorios pueden ser reutilizados por múltiples servicios
- Lógica centralizada y compartida

## Reglas de Dependencias

### ✅ Permitido
- Router → Service
- Service → Repository
- Service → Service (mismo nivel)
- Repository → Model

### ❌ Prohibido
- Router → Repository (debe pasar por Service)
- Repository → Service (dependencia circular)
- Service → Router (dependencia circular)

## Ejemplo Completo

### Router (Capa de Presentación)
```python
@router.post("/solicitar-verificacion")
async def solicitar_verificacion_completa(
    perfil_in: str = Form(...),
    current_user: SupabaseUser = Depends(get_current_user)
):
    # Validación de entrada
    perfil_data = parse_and_validate_profile(perfil_in)
    
    # Llamada al servicio
    result = await VerificationService.process_verification_request(
        perfil_data=perfil_data,
        current_user_id=current_user.id
    )
    
    return result
```

### Service (Capa de Lógica de Negocio)
```python
class VerificationService:
    @staticmethod
    async def process_verification_request(...):
        # Lógica de negocio
        user_profile = await ProviderRepository.get_user_profile(user_id)
        
        # Validación de negocio
        empresa_existente = await ProviderRepository.validate_company_uniqueness(...)
        
        # Orquestación
        # ...
        
        return {"message": "Solicitud creada"}

class DocumentService:
    @staticmethod
    async def process_documents(...):
        # Usa StorageService para subir archivos (lógica de negocio)
        file_url = storage_service.upload_document(...)
        
        # Usa Repository para guardar en BD (acceso a datos)
        await ProviderRepository.create_document(...)
```

### Repository (Capa de Acceso a Datos)
```python
class ProviderRepository:
    @staticmethod
    async def get_user_profile(user_id: str):
        conn = await direct_db_service.get_connection()
        user_row = await conn.fetchrow("SELECT ... FROM users WHERE id = $1", user_id)
        return user_profile
```

## Conclusión

Esta arquitectura de capas proporciona:
- **Claridad**: Cada componente tiene un propósito claro
- **Organización**: Código bien estructurado y fácil de navegar
- **Mantenibilidad**: Fácil hacer cambios sin romper otras partes
- **Testabilidad**: Cada capa puede ser testeada independientemente
- **Escalabilidad**: Fácil agregar nuevas funcionalidades

