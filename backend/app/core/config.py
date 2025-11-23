# config.py
from dotenv import load_dotenv
import os

#busca automáticamente el archivo .env en la raíz del proyecto
# y carga las variables de entorno definidas en él
try:
    load_dotenv()  # Lee .env
except Exception:
    pass  # Si no hay .env, continuar sin él

# Supabase Auth
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SERVICE_ROLE")

#PostgreSQL Supabase
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/postgres")

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


#WEAVIATE_API_KEY = os.getenv("WEAVIATE_API_KEY")
WEAVIATE_URL = os.getenv("WEAVIATE_URL")

# SMTP Configuration for Email
SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USERNAME = os.getenv("SMTP_USERNAME")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
SMTP_FROM_EMAIL = os.getenv("SMTP_FROM_EMAIL", SMTP_USERNAME)
SMTP_FROM_NAME = os.getenv("SMTP_FROM_NAME", "B2B Platform")

# Diagnóstico detallado de Email
smtp_configurado = bool(SMTP_USERNAME and SMTP_PASSWORD)
sendgrid_configurado = bool(os.getenv("SENDGRID_API_KEY"))

print(f"📧 SMTP configurado: {'Sí' if smtp_configurado else 'No'}")
print(f"📧 Brevo configurado: {'Sí' if os.getenv('BREVO_API_KEY') else 'No'}")
print(f"📧 SendGrid configurado: {'Sí' if sendgrid_configurado else 'No'}")
print(f"📧 Mailgun configurado: {'Sí' if os.getenv('MAILGUN_API_KEY') and os.getenv('MAILGUN_DOMAIN') else 'No'}")
print(f"📧 Resend configurado: {'Sí' if os.getenv('RESEND_API_KEY') else 'No'}")

brevo_configurado = bool(os.getenv("BREVO_API_KEY"))
mailgun_configurado = bool(os.getenv("MAILGUN_API_KEY") and os.getenv("MAILGUN_DOMAIN"))
resend_configurado = bool(os.getenv("RESEND_API_KEY"))

if brevo_configurado:
    print("   📧 Brevo configurado - gratuito sin tarjeta")
elif sendgrid_configurado:
    print("   ✅ SendGrid configurado - requiere verificación")
elif mailgun_configurado:
    print("   📧 Mailgun configurado - requiere tarjeta")
elif resend_configurado:
    print("   🚂 Resend configurado - no funciona con Gmail")

if smtp_configurado:
    print("   🔄 SMTP con 2 configuraciones rápidas: Gmail TLS/SSL (último respaldo)")
    if brevo_configurado or sendgrid_configurado or mailgun_configurado or resend_configurado:
        apis = []
        if brevo_configurado: apis.append("Brevo")
        if sendgrid_configurado: apis.append("SendGrid")
        if mailgun_configurado: apis.append("Mailgun")
        if resend_configurado: apis.append("Resend")
        print(f"   ✅ Configuración completa: {', '.join(apis)} + SMTP respaldo (óptimo)")
    else:
        print("   ℹ️ Solo SMTP configurado - Railway bloquea SMTP en planes gratuitos")

if not smtp_configurado and not brevo_configurado and not sendgrid_configurado and not mailgun_configurado and not resend_configurado:
    print("   ⚠️ NINGÚN método de email configurado - Railway requiere API HTTP en planes gratuitos")
    print("   📧 SOLUCIONES RECOMENDADAS:")
    print("   📧 1. BREVO_API_KEY (gratuito sin tarjeta)")
    print("   📧 2. SENDGRID_API_KEY (con verificación de email)")
    print("   📧 3. MAILGUN_API_KEY + MAILGUN_DOMAIN (requiere tarjeta)")
    print("   📧 ❌ RESEND_API_KEY (no funciona con Gmail)")