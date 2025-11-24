FROM python:3.12-slim

WORKDIR /app

# Instalar dependencias del sistema necesarias
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copiar requirements e instalar dependencias primero (para aprovechar cache de Docker)
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip setuptools wheel && \
    pip install --no-cache-dir -r requirements.txt && \
    pip list

# Copiar el código del backend
COPY . .

# Hacer ejecutable los scripts
RUN chmod +x start.sh start_simple.sh simple_app.py && \
    ls -la start.sh start_simple.sh simple_app.py

# Verificar que la aplicación se puede importar
RUN python -c "from app.main import app; print('✅ App importada correctamente')" || \
    (echo "❌ Error al importar la aplicación" && exit 1)

# Puerto por defecto (se usará PORT en runtime)
EXPOSE 8000

# Health check (Railway inyecta PORT automáticamente)
HEALTHCHECK --interval=30s --timeout=30s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Usar el script de inicio
CMD ["./start.sh"]
