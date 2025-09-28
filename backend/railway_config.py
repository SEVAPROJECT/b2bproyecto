#!/usr/bin/env python3
"""
Configuración específica para Railway
"""

import os

# Configuración de Railway
RAILWAY_ENVIRONMENT = os.getenv("RAILWAY_ENVIRONMENT", "false").lower() == "true"

# Configuración del pool de conexiones para Railway
if RAILWAY_ENVIRONMENT:
    # Railway: Configuración conservadora
    POOL_MIN_SIZE = 1
    POOL_MAX_SIZE = 3  # Muy conservador para Railway
    POOL_TIMEOUT = 60
    POOL_COMMAND_TIMEOUT = 45
    POOL_KEEPALIVE_IDLE = 600
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
