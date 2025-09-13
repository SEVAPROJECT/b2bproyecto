# config.py
from dotenv import load_dotenv
import os

#busca automáticamente el archivo .env en la raíz del proyecto
# y carga las variables de entorno definidas en él
try:
    load_dotenv()  # Lee .env
except:
    pass  # Si no hay .env, continuar sin él

# Supabase Auth
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SERVICE_ROLE")

# Verificar configuración de Supabase
if not SUPABASE_URL or not SUPABASE_ANON_KEY:
    print("⚠️  ADVERTENCIA: Supabase no configurado. Algunas funciones pueden no funcionar.")
    print(f"   SUPABASE_URL: {'✅' if SUPABASE_URL else '❌'}")
    print(f"   SUPABASE_ANON_KEY: {'✅' if SUPABASE_ANON_KEY else '❌'}")
else:
    print("✅ Supabase configurado correctamente")

#PostgreSQL Supabase
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://postgres:postgres@localhost:5432/postgres")

#PostgreSQL Local
DATABASE_URL_LOCAL = os.getenv("DATABASE_URL_LOCAL", "postgresql+asyncpg://postgres:postgres@localhost:5432/postgres")

# PostgreSQL
DB_HOST     = os.getenv("DB_HOST", "localhost")
DB_PORT     = os.getenv("DB_PORT", "5432")
DB_NAME     = os.getenv("DB_NAME", "postgres")
DB_USER     = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "postgres")

#DATABASE_URL = (f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}")

#IDRIVE2 - Soporte para diferentes tipos de credenciales
IDRIVE_ENDPOINT_URL = os.getenv("IDRIVE_ENDPOINT_URL")

# Intentar diferentes nombres de variables para las credenciales
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID") or os.getenv("IDRIVE_ACCESS_KEY") or os.getenv("ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY") or os.getenv("IDRIVE_SECRET_KEY") or os.getenv("SECRET_ACCESS_KEY")

print(f"🔑 Access Key configurada: {'Sí' if AWS_ACCESS_KEY_ID else 'No'}")
print(f"🔐 Secret Key configurada: {'Sí' if AWS_SECRET_ACCESS_KEY else 'No'}")

IDRIVE_BUCKET_NAME = os.getenv("IDRIVE_BUCKET_NAME")

# Verificar configuración de IDrive
if not AWS_ACCESS_KEY_ID or not AWS_SECRET_ACCESS_KEY or not IDRIVE_BUCKET_NAME:
    print("⚠️  ADVERTENCIA: IDrive no configurado. Funciones de almacenamiento no disponibles.")
    print(f"   AWS_ACCESS_KEY_ID: {'✅' if AWS_ACCESS_KEY_ID else '❌'}")
    print(f"   AWS_SECRET_ACCESS_KEY: {'✅' if AWS_SECRET_ACCESS_KEY else '❌'}")
    print(f"   IDRIVE_BUCKET_NAME: {'✅' if IDRIVE_BUCKET_NAME else '❌'}")
else:
    print("✅ IDrive configurado correctamente")

#Weaviate
#WEAVIATE_URL = os.getenv("WEAVIATE_URL")
#WEAVIATE_API_KEY = os.getenv("WEAVIATE_API_KEY")
WEAVIATE_URL = os.getenv("WEAVIATE_URL")

# SMTP Configuration for Email
SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USERNAME = os.getenv("SMTP_USERNAME")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
SMTP_FROM_EMAIL = os.getenv("SMTP_FROM_EMAIL", SMTP_USERNAME)
SMTP_FROM_NAME = os.getenv("SMTP_FROM_NAME", "B2B Platform")

print(f"📧 SMTP configurado: {'Sí' if SMTP_USERNAME and SMTP_PASSWORD else 'No'}")