# 📊 Scripts para Poblar Base de Datos

Este directorio contiene scripts útiles para trabajar con la base de datos.

## 📋 Scripts Disponibles

### 1. `export_table_structure.py`
Exporta la estructura de todas las tablas de la base de datos en formato SQL y JSON.

**Uso:**
```bash
cd b2bproyecto/backend
python scripts/export_table_structure.py
```

**Salida:**
- `database_structure.json` - Estructura de tablas en formato JSON
- `database_structure.sql` - DDL SQL de todas las tablas

### 2. `bulk_insert_data.py`
Inserta datos masivamente en la base de datos desde un archivo JSON.

**Uso:**
```bash
cd b2bproyecto/backend
python scripts/bulk_insert_data.py
```

**Archivo de datos:**
Crea un archivo `sample_data.json` en el directorio `scripts/` con el siguiente formato:

```json
{
  "departamentos": [
    {"nombre": "Central"},
    {"nombre": "Asunción"}
  ],
  "ciudades": [
    {"nombre": "Asunción", "departamento": "Asunción"},
    {"nombre": "San Lorenzo", "departamento": "Central"}
  ],
  "barrios": [
    {"nombre": "Centro", "ciudad": "Asunción"}
  ],
  "categorias": [
    {"nombre": "Catering", "estado": true}
  ],
  "tipos_documento": [
    {"nombre": "Constancia de RUC", "es_requerido": true}
  ]
}
```

### 3. `generate_ddl.py`
Genera el DDL (Data Definition Language) desde los modelos SQLAlchemy.

**Uso:**
```bash
cd b2bproyecto/backend
python scripts/generate_ddl.py > database_schema.sql
```

## 🚀 Pasos para Poblar la Base de Datos

### Paso 1: Exportar la Estructura de Tablas (Opcional)

```bash
cd b2bproyecto/backend
python scripts/export_table_structure.py
```

Esto generará:
- `database_structure.json` - Para entender la estructura
- `database_structure.sql` - Para referencia

### Paso 2: Insertar Datos Básicos (Departamentos, Ciudades, etc.)

```bash
python scripts/bulk_insert_data.py
```

O edita el archivo `scripts/sample_data.json` con tus datos y ejecuta el script.

### Paso 3: Crear Perfiles de Empresa

```bash
python scripts/populate_company_profiles.py
```

Esto creará 8 empresas de ejemplo con usuarios en Supabase Auth y perfiles de empresa verificados.

### Paso 4: Crear Servicios

```bash
python scripts/populate_services.py
```

Esto creará 20 servicios variados distribuidos entre las empresas creadas.

## 📝 Formato de Datos

### Departamentos
```json
{
  "departamentos": [
    {"nombre": "Nombre del Departamento"}
  ]
}
```

### Ciudades
```json
{
  "ciudades": [
    {"nombre": "Nombre de la Ciudad", "departamento": "Nombre del Departamento"}
  ]
}
```

### Barrios
```json
{
  "barrios": [
    {"nombre": "Nombre del Barrio", "ciudad": "Nombre de la Ciudad"}
  ]
}
```

### Categorías
```json
{
  "categorias": [
    {"nombre": "Nombre de la Categoría", "estado": true}
  ]
}
```

### Tipos de Documento
```json
{
  "tipos_documento": [
    {"nombre": "Nombre del Tipo", "es_requerido": true}
  ]
}
```

## ⚠️ Notas Importantes

1. **Orden de Inserción**: Los datos deben insertarse en el siguiente orden:
   - Departamentos
   - Ciudades (requiere departamentos)
   - Barrios (requiere ciudades)
   - Categorías
   - Tipos de Documento

2. **Evitar Duplicados**: Los scripts usan `ON CONFLICT DO NOTHING` para evitar duplicados.

3. **Variables de Entorno**: Asegúrate de tener configurado el archivo `.env` con `DATABASE_URL`.

### 4. `populate_company_profiles.py`
Crea perfiles de empresa completos. Primero crea usuarios en Supabase Auth, luego crea los perfiles de empresa asociados con direcciones.

**Uso:**
```bash
cd b2bproyecto/backend
python scripts/populate_company_profiles.py
```

**Requisitos:**
- Debe tener configurado `SUPABASE_SERVICE_ROLE_KEY` en `.env`
- Debe haber departamentos, ciudades y barrios en la base de datos

**Nota:** Este script crea 8 empresas de ejemplo con diferentes categorías de servicios.

### 5. `populate_services.py`
Crea servicios variados asociados a categorías y empresas existentes. Incluye descripciones detalladas para probar la búsqueda con IA.

**Uso:**
```bash
cd b2bproyecto/backend
python scripts/populate_services.py
```

**Requisitos:**
- Debe haber categorías existentes en la base de datos
- Debe haber al menos un perfil de empresa verificado

**Nota:** Este script distribuye automáticamente los servicios entre los perfiles de empresa disponibles.

## 🔧 Troubleshooting

### Error: "DATABASE_URL no está configurado"
- Verifica que el archivo `.env` exista en `b2bproyecto/backend/`
- Asegúrate de que contenga `DATABASE_URL=tu_connection_string`

### Error: "Departamento no encontrado"
- Asegúrate de insertar los departamentos antes que las ciudades
- Verifica que el nombre del departamento coincida exactamente

### Error: "Ciudad no encontrada"
- Asegúrate de insertar las ciudades antes que los barrios
- Verifica que el nombre de la ciudad coincida exactamente

### Error: "No se encontraron perfiles de empresa verificados"
- Necesitas crear perfiles de empresa primero usando el proceso de registro de proveedores
- Los perfiles deben estar en estado 'ACTIVO' y verificados

