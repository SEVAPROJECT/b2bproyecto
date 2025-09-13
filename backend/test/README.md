# Pruebas Unitarias - SEVA B2B API

Este directorio contiene las pruebas unitarias para la API de SEVA B2B.

## 📁 Estructura

```
test/
├── __init__.py
├── test_auth_endpoints.py      # Pruebas de endpoints de autenticación
├── test_auth_dependencies.py   # Pruebas de dependencias de auth
└── README.md                   # Este archivo
```

## 🧪 Tipos de Pruebas

### 1. **Pruebas de Endpoints (`test_auth_endpoints.py`)**

Prueban los endpoints HTTP de autenticación:

- ✅ **Registro de usuarios** (`/api/v1/auth/signup`)
- ✅ **Login de usuarios** (`/api/v1/auth/signin`)
- ✅ **Refresh de tokens** (`/api/v1/auth/refresh`)
- ✅ **Recuperación de contraseña** (`/api/v1/auth/forgot-password`)
- ✅ **Obtención de perfil** (`/api/v1/auth/me`)
- ✅ **Logout** (`/api/v1/auth/signout`)

**Casos cubiertos:**
- ✅ Éxito en operaciones
- ✅ Datos inválidos
- ✅ Errores de Supabase
- ✅ Tokens inválidos
- ✅ Validación de esquemas

### 2. **Pruebas de Dependencias (`test_auth_dependencies.py`)**

Prueban las dependencias de autenticación:

- ✅ **`get_current_user`** - Validación de JWT
- ✅ **`get_admin_user`** - Verificación de roles admin
- ✅ **Flujo completo de autenticación**

**Casos cubiertos:**
- ✅ Tokens válidos
- ✅ Tokens inválidos
- ✅ Usuarios sin perfil
- ✅ Usuarios sin permisos admin
- ✅ Usuarios con múltiples roles

## 🚀 Instalación y Ejecución

### 1. **Instalar dependencias de testing**

```bash
# Desde el directorio backend/
pip install -r requirements-test.txt

# O usar el script
python run_tests.py install
```

### 2. **Ejecutar todas las pruebas**

```bash
# Usando pytest directamente
pytest test/ -v

# O usar el script
python run_tests.py
```

### 3. **Ejecutar pruebas específicas**

```bash
# Solo pruebas de endpoints
pytest test/test_auth_endpoints.py -v

# Solo pruebas de dependencias
pytest test/test_auth_dependencies.py -v

# Solo pruebas de auth
pytest test/ -m auth -v

# Usando el script
python run_tests.py specific test/test_auth_endpoints.py
```

### 4. **Ejecutar con cobertura**

```bash
# Cobertura en terminal
pytest test/ --cov=app --cov-report=term-missing -v

# Cobertura en HTML
pytest test/ --cov=app --cov-report=html -v
```

## 📊 Cobertura de Pruebas

### **Endpoints Cubiertos:**

| Endpoint | Método | Casos de Prueba | Estado |
|----------|--------|-----------------|--------|
| `/auth/signup` | POST | ✅ Éxito, ❌ Datos inválidos, ❌ Error Supabase | ✅ |
| `/auth/signin` | POST | ✅ Éxito, ❌ Credenciales inválidas, ❌ Datos inválidos | ✅ |
| `/auth/refresh` | POST | ✅ Éxito, ❌ Token inválido | ✅ |
| `/auth/forgot-password` | POST | ✅ Éxito, ❌ Email inválido | ✅ |
| `/auth/me` | GET | ✅ Éxito, ❌ Sin token, ❌ Token inválido | ✅ |
| `/auth/signout` | POST | ✅ Éxito, ❌ Error | ✅ |

### **Dependencias Cubiertas:**

| Dependencia | Casos de Prueba | Estado |
|-------------|-----------------|--------|
| `get_current_user` | ✅ Token válido, ❌ Sin credenciales, ❌ Token inválido, ❌ Error inesperado | ✅ |
| `get_admin_user` | ✅ Usuario admin, ❌ Sin perfil, ❌ Sin permisos, ✅ Múltiples roles | ✅ |

## 🔧 Configuración

### **pytest.ini**

```ini
[tool:pytest]
testpaths = test
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = 
    -v
    --tb=short
    --strict-markers
    --disable-warnings
    --color=yes
markers =
    slow: marks tests as slow
    integration: marks tests as integration tests
    unit: marks tests as unit tests
    auth: marks tests as authentication tests
```

### **Marcadores de Pruebas**

```bash
# Ejecutar solo pruebas unitarias
pytest test/ -m unit

# Ejecutar solo pruebas de integración
pytest test/ -m integration

# Excluir pruebas lentas
pytest test/ -m "not slow"

# Ejecutar solo pruebas de auth
pytest test/ -m auth
```

## 🛠️ Herramientas Utilizadas

- **pytest**: Framework de pruebas
- **pytest-asyncio**: Soporte para pruebas asíncronas
- **pytest-mock**: Mocking y patching
- **pytest-cov**: Cobertura de código
- **httpx**: Cliente HTTP para pruebas
- **unittest.mock**: Mocking nativo de Python

## 📝 Convenciones

### **Nomenclatura**

- **Archivos**: `test_*.py`
- **Clases**: `Test*`
- **Métodos**: `test_*`
- **Fixtures**: `mock_*`, `sample_*`

### **Estructura de Pruebas**

```python
class TestFeature:
    """Descripción de la funcionalidad"""
    
    @pytest.fixture
    def setup_data(self):
        """Configuración de datos de prueba"""
        pass
    
    def test_success_case(self, setup_data):
        """Prueba caso exitoso"""
        # Arrange
        # Act
        # Assert
        pass
    
    def test_error_case(self, setup_data):
        """Prueba caso de error"""
        # Arrange
        # Act & Assert
        with pytest.raises(ExpectedException):
            pass
```

## 🐛 Debugging

### **Ejecutar con más verbosidad**

```bash
pytest test/ -v -s --tb=long
```

### **Ejecutar una prueba específica**

```bash
pytest test/test_auth_endpoints.py::TestAuthEndpoints::test_signup_success -v
```

### **Ejecutar con breakpoints**

```bash
pytest test/ --pdb
```

## 📈 Métricas de Calidad

### **Cobertura Objetivo**

- **Endpoints**: 100%
- **Dependencias**: 100%
- **Validaciones**: 100%
- **Manejo de errores**: 100%

### **Tipos de Pruebas**

- **Unitarias**: 80%
- **Integración**: 20%
- **End-to-End**: 0% (se implementarán después)

## 🔄 CI/CD

Las pruebas se ejecutan automáticamente en:

- **Push a main**: Ejecuta todas las pruebas
- **Pull Request**: Ejecuta pruebas + cobertura
- **Deploy**: Ejecuta pruebas de integración

## 📞 Soporte

Si encuentras problemas con las pruebas:

1. Verifica que todas las dependencias estén instaladas
2. Asegúrate de estar en el directorio correcto (`backend/`)
3. Revisa los logs de error detallados
4. Consulta la documentación de pytest

---

**¡Las pruebas ayudan a mantener la calidad del código!** 🚀
