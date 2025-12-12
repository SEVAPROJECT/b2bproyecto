# SEVA Empresas - B2B Service Marketplace

![Version](https://img.shields.io/badge/version-1.0.0-blue.svg)
![Python](https://img.shields.io/badge/python-3.12+-green.svg)
![Node](https://img.shields.io/badge/node-18+-green.svg)
![License](https://img.shields.io/badge/license-MIT-orange.svg)

Plataforma B2B de reservas de servicios para Mipymes en Paraguay. Conecta empresas con proveedores verificados, busca servicios con búsqueda semántica impulsada por IA y gestiona las necesidades de tu negocio de manera eficiente.

## 📋 Tabla de Contenidos

- [Características](#-características)
- [Tecnologías](#-tecnologías)
- [Arquitectura](#-arquitectura)
- [Requisitos Previos](#-requisitos-previos)
- [Instalación](#-instalación)
- [Configuración](#-configuración)
- [Uso](#-uso)
- [Estructura del Proyecto](#-estructura-del-proyecto)
- [API Documentation](#-api-documentation)
- [Despliegue](#-despliegue)
- [Testing](#-testing)
- [Contribución](#-contribución)
- [Licencia](#-licencia)

## ✨ Características

### Para Clientes
- 🔍 **Búsqueda Semántica con IA**: Encuentra servicios usando búsqueda por significado, no solo palabras clave
- 📅 **Sistema de Reservas**: Reserva servicios con gestión de horarios y disponibilidad
- ⭐ **Sistema de Calificaciones**: Califica y revisa servicios recibidos
- 👤 **Gestión de Perfil**: Administra tu perfil empresarial y preferencias
- 📊 **Dashboard Personalizado**: Visualiza tus reservas, servicios contratados y estadísticas

### Para Proveedores
- 🏢 **Gestión de Servicios**: Crea y administra múltiples servicios con tarifas y horarios
- 📋 **Solicitud de Verificación**: Proceso de verificación con documentación
- 📅 **Gestión de Disponibilidad**: Configura horarios y excepciones
- 💰 **Gestión de Tarifas**: Define precios por diferentes períodos y tipos de servicio
- 📈 **Analíticas**: Visualiza el rendimiento de tus servicios

### Para Administradores
- 👥 **Gestión de Usuarios**: Administra usuarios, roles y permisos
- ✅ **Verificación de Proveedores**: Revisa y aprueba solicitudes de proveedores
- 📝 **Gestión de Solicitudes**: Administra solicitudes de servicios y categorías
- 📊 **Reportes y Estadísticas**: Genera reportes detallados del sistema
- 🔐 **Control de Acceso**: Sistema robusto de roles y permisos

## 🛠 Tecnologías

### Backend
- **FastAPI** - Framework web moderno y rápido para Python
- **Python 3.12+** - Lenguaje de programación
- **PostgreSQL** - Base de datos relacional
- **Supabase** - Backend as a Service (Auth, Database, Storage)
- **SQLAlchemy** - ORM para Python
- **asyncpg** - Driver asíncrono para PostgreSQL
- **Weaviate** - Base de datos vectorial para búsqueda semántica
- **Alembic** - Migraciones de base de datos
- **Pydantic** - Validación de datos
- **Boto3** - Cliente AWS S3 para iDrive2
- **Uvicorn** - Servidor ASGI

### Frontend
- **React 19** - Biblioteca de UI
- **TypeScript** - Tipado estático
- **Vite** - Build tool y dev server
- **React Router** - Enrutamiento
- **Recharts** - Gráficos y visualizaciones
- **Tailwind CSS** - Framework CSS (implícito en componentes)

### Infraestructura y DevOps
- **Docker** - Containerización
- **Nginx** - Servidor web y reverse proxy
- **Railway** - Plataforma de despliegue
- **Vercel/Netlify** - Hosting frontend
- **SonarQube** - Análisis de calidad de código

## 🏗 Arquitectura

```
┌─────────────────┐
│   Frontend      │  React + TypeScript + Vite
│   (React)       │  Puerto: 5173 (dev)
└────────┬──────────┘
       │ HTTP/REST
┌───────▼──────────┐
│   Backend API    │  FastAPI + Python
│   (FastAPI)      │  Puerto: 8000
└───────┬──────────┘
        │
   ┌────┴────┬──────────┬──────────┐
   │         │          │          │
┌──▼──┐  ┌──▼──┐   ┌──▼──┐   ┌──▼──┐
│PostgreSQL│ │Supabase│ │Weaviate│ │iDrive2│
│          │ │        │ │        │ │(S3)   │
└──────────┘ └────────┘ └────────┘ └───────┘
```

## 📦 Requisitos Previos

- **Python 3.12+**
- **Node.js 18+** y npm
- **PostgreSQL 14+**
- **Cuenta de Supabase** (gratuita disponible)
- **Cuenta de Weaviate** (opcional, para búsqueda semántica)
- **Cuenta de iDrive2** (opcional, para almacenamiento de archivos)

## 🚀 Instalación

### 1. Clonar el Repositorio

```bash
git clone <repository-url>
cd SEVA-AJUSTES-01-11
```

### 2. Configurar Backend

```bash
cd b2bproyecto/backend

# Crear entorno virtual
python -m venv venv

# Activar entorno virtual
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Instalar dependencias
pip install -r requirements.txt
```

### 3. Configurar Frontend

```bash
cd b2bproyecto/frontend

# Instalar dependencias
npm install
```

## ⚙️ Configuración

### Variables de Entorno Backend

Crear archivo `.env` en `b2bproyecto/backend/`:

```env
# Supabase
SUPABASE_URL=https://tu-proyecto.supabase.co
SUPABASE_ANON_KEY=tu-anon-key
SUPABASE_SERVICE_ROLE_KEY=tu-service-role-key

# PostgreSQL
DATABASE_URL=postgresql://usuario:password@localhost:5432/nombre_db
DB_HOST=localhost
DB_PORT=5432
DB_NAME=nombre_db
DB_USER=usuario
DB_PASSWORD=password

# iDrive2 (S3-compatible)
IDRIVE_ENDPOINT_URL=https://s3.us-east-1.idrive.com
AWS_ACCESS_KEY_ID=tu-access-key
AWS_SECRET_ACCESS_KEY=tu-secret-key
IDRIVE_BUCKET_NAME=tu-bucket-name
AWS_REGION=us-east-1

# Weaviate (Opcional)
WEAVIATE_URL=https://tu-cluster.weaviate.network

# Email (Elegir uno)
# Opción 1: Brevo (Recomendado - Gratuito)
BREVO_API_KEY=tu-brevo-api-key

# Opción 2: SendGrid
SENDGRID_API_KEY=tu-sendgrid-key

# Opción 3: SMTP
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=tu-email@gmail.com
SMTP_PASSWORD=tu-app-password
SMTP_FROM_EMAIL=tu-email@gmail.com
SMTP_FROM_NAME=SEVA Empresas
```

### Variables de Entorno Frontend

Crear archivo `.env` en `b2bproyecto/frontend/`:

```env
VITE_API_URL=http://localhost:8000/api/v1
VITE_SUPABASE_URL=https://tu-proyecto.supabase.co
VITE_SUPABASE_ANON_KEY=tu-anon-key
```

## 🎯 Uso

### Desarrollo

#### Iniciar Backend

```bash
cd b2bproyecto/backend
source venv/bin/activate  # o venv\Scripts\activate en Windows
uvicorn app.main:app --reload --port 8000
```

El backend estará disponible en `http://localhost:8000`

#### Iniciar Frontend

```bash
cd b2bproyecto/frontend
npm run dev
```

El frontend estará disponible en `http://localhost:5173`

### Producción

Ver documentación de despliegue en:
- `b2bproyecto/RAILWAY_DEPLOYMENT.md` - Despliegue en Railway
- `b2bproyecto/backend/RAILWAY_DEPLOYMENT.md` - Configuración específica del backend

## 📁 Estructura del Proyecto

```
SEVA-AJUSTES-01-11/
├── b2bproyecto/
│   ├── backend/
│   │   ├── app/
│   │   │   ├── api/
│   │   │   │   └── v1/
│   │   │   │       └── routers/          # Endpoints de la API
│   │   │   ├── core/                      # Configuración core
│   │   │   │   ├── config.py             # Variables de entorno
│   │   │   │   └── startup.py            # Eventos de inicio
│   │   │   ├── models/                    # Modelos SQLAlchemy
│   │   │   ├── schemas/                   # Schemas Pydantic
│   │   │   ├── services/                  # Lógica de negocio
│   │   │   ├── supabase/                  # Integración Supabase
│   │   │   └── main.py                    # Aplicación FastAPI
│   │   ├── requirements.txt
│   │   ├── Dockerfile
│   │   └── alembic/                       # Migraciones DB
│   │
│   └── frontend/
│       ├── src/
│       │   ├── components/                 # Componentes React
│       │   │   ├── admin/                  # Componentes admin
│       │   │   ├── marketplace/            # Componentes marketplace
│       │   │   └── ui/                     # Componentes UI
│       │   ├── pages/                      # Páginas principales
│       │   ├── hooks/                      # Custom hooks
│       │   ├── services/                   # Servicios API
│       │   ├── contexts/                   # Context providers
│       │   ├── utils/                      # Utilidades
│       │   └── routes/                     # Configuración rutas
│       ├── package.json
│       └── vite.config.ts
│
└── scripts/                                # Scripts de utilidad
```

## 📚 API Documentation

Una vez iniciado el backend, la documentación interactiva de la API está disponible en:

- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

### Endpoints Principales

#### Autenticación
- `POST /api/v1/auth/signup` - Registro de usuario
- `POST /api/v1/auth/login` - Inicio de sesión
- `POST /api/v1/auth/logout` - Cerrar sesión
- `POST /api/v1/auth/refresh` - Refrescar token

#### Servicios
- `GET /api/v1/services` - Listar servicios
- `GET /api/v1/services/{id}` - Obtener servicio
- `POST /api/v1/services` - Crear servicio
- `PUT /api/v1/services/{id}` - Actualizar servicio
- `DELETE /api/v1/services/{id}` - Eliminar servicio

#### Reservas
- `GET /api/v1/reservations` - Listar reservas
- `POST /api/v1/reservations` - Crear reserva
- `PUT /api/v1/reservations/{id}` - Actualizar reserva
- `DELETE /api/v1/reservations/{id}` - Cancelar reserva

#### Administración
- `GET /api/v1/admin/users` - Listar usuarios
- `GET /api/v1/admin/roles` - Listar roles
- `POST /api/v1/admin/users/{id}/reset-password` - Resetear contraseña
- `GET /api/v1/admin/reports` - Generar reportes

## 🧪 Testing

### Backend

```bash
cd b2bproyecto/backend
pytest
```

### Frontend

```bash
cd b2bproyecto/frontend
npm test
```

## 🔒 Seguridad

- Autenticación basada en JWT tokens
- Validación de roles y permisos
- CORS configurado
- Validación de datos con Pydantic
- Sanitización de inputs
- Rate limiting en endpoints críticos

## 📊 Calidad de Código

El proyecto utiliza SonarQube para análisis de calidad de código:

```bash
# Ver documentación
cat SONARQUBE_SETUP.md
```

## 🚢 Despliegue

### Railway (Recomendado)

1. Conectar repositorio a Railway
2. Configurar variables de entorno
3. Deploy automático en cada push

Ver `b2bproyecto/RAILWAY_DEPLOYMENT.md` para detalles completos.

### Docker

```bash
# Backend
cd b2bproyecto/backend
docker build -t seva-backend .
docker run -p 8000:8000 seva-backend

# Frontend
cd b2bproyecto/frontend
docker build -t seva-frontend .
docker run -p 80:80 seva-frontend
```

## 🤝 Contribución

1. Fork el proyecto
2. Crea una rama para tu feature (`git checkout -b feature/AmazingFeature`)
3. Commit tus cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abre un Pull Request

### Estándares de Código

- Backend: Seguir PEP 8
- Frontend: Usar ESLint y Prettier
- Commits: Usar mensajes descriptivos
- Código: Sin duplicación (verificado con SonarQube)

## 📝 Licencia

Este proyecto está bajo la Licencia MIT - ver el archivo LICENSE para más detalles.

## 👥 Autores

- **Equipo SEVA** - Desarrollo inicial y mantenimiento

## 🙏 Agradecimientos

- Supabase por la infraestructura backend
- FastAPI por el excelente framework
- React por la biblioteca de UI
- Comunidad open source

## 📞 Soporte

Para soporte, abre un issue en el repositorio o contacta al equipo de desarrollo.

## 🔄 Changelog

### v1.0.0
- Lanzamiento inicial
- Sistema de autenticación completo
- Gestión de servicios y reservas
- Búsqueda semántica con IA
- Panel de administración
- Sistema de calificaciones

---

**Desarrollado con ❤️ para empresas paraguayas**


