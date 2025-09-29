#!/usr/bin/env python3
"""
Configuración específica para Railway
"""

import os

# Configuración de Railway
RAILWAY_ENVIRONMENT = os.getenv("RAILWAY_ENVIRONMENT", "false").lower() == "true"

# Configuración del pool de conexiones para Railway
if RAILWAY_ENVIRONMENT:
    # Railway: Configuración optimizada para rendimiento
    POOL_MIN_SIZE = 2  # Mantener 2 conexiones siempre activas
    POOL_MAX_SIZE = 5   # Aumentado para mejor rendimiento
    POOL_TIMEOUT = 30   # Reducido para respuestas más rápidas
    POOL_COMMAND_TIMEOUT = 20  # Timeout más agresivo
    POOL_KEEPALIVE_IDLE = 300  # Mantener conexiones vivas
    POOL_KEEPALIVE_INTERVAL = 30
    POOL_KEEPALIVE_COUNT = 3
else:
    # Desarrollo local: Configuración más permisiva
    POOL_MIN_SIZE = 1
    POOL_MAX_SIZE = 5
    POOL_TIMEOUT = 30
    POOL_COMMAND_TIMEOUT = 30
    POOL_KEEPALIVE_IDLE = 300
    POOL_KEEPALIVE_INTERVAL = 30
    POOL_KEEPALIVE_COUNT = 3

print(f"🚀 Configuración Railway: {'Sí' if RAILWAY_ENVIRONMENT else 'No'}")
print(f"📊 Pool configurado: min={POOL_MIN_SIZE}, max={POOL_MAX_SIZE}")
