FROM python:3.12-slim

WORKDIR /app

# Instalar dependencias del sistema necesarias
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Crear usuario no root para ejecutar la aplicación (mejores prácticas de seguridad)
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Copiar requirements e instalar dependencias
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copiar el código del backend
# NOTA: El archivo .dockerignore excluye archivos sensibles (.env, credenciales, etc.)
# para prevenir que se copien accidentalmente al contenedor
COPY . .

# Cambiar propiedad de los archivos al usuario no root
RUN chown -R appuser:appuser /app

# Hacer ejecutable los scripts
RUN chmod +x start.sh start_simple.sh simple_app.py

# Cambiar al usuario no root
USER appuser

# Puerto por defecto (se usará PORT en runtime)
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:${PORT:-8000}/health || exit 1

# Usar el script de inicio
CMD ["./start.sh"]
