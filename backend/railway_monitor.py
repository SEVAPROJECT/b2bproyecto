#!/usr/bin/env python3
"""
Script de monitoreo para Railway
Mantiene la aplicación activa y monitorea rendimiento
"""
import asyncio
import aiohttp
import time
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class RailwayMonitor:
    """Monitor para mantener la aplicación activa en Railway"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.session = None
        self.running = False
    
    async def start_monitoring(self):
        """Iniciar monitoreo continuo"""
        self.running = True
        self.session = aiohttp.ClientSession()
        
        logger.info("🚀 Iniciando monitor de Railway...")
        
        while self.running:
            try:
                await self._ping_health_check()
                await asyncio.sleep(30)  # Ping cada 30 segundos
            except Exception as e:
                logger.error(f"❌ Error en monitor: {e}")
                await asyncio.sleep(60)  # Esperar más en caso de error
    
    async def _ping_health_check(self):
        """Hacer ping al health check"""
        try:
            async with self.session.get(f"{self.base_url}/health") as response:
                if response.status == 200:
                    data = await response.json()
                    logger.info(f"✅ Health check OK: {data.get('status', 'unknown')}")
                else:
                    logger.warning(f"⚠️ Health check falló: {response.status}")
        except Exception as e:
            logger.error(f"❌ Error en health check: {e}")
    
    async def stop_monitoring(self):
        """Detener monitoreo"""
        self.running = False
        if self.session:
            await self.session.close()
        logger.info("🛑 Monitor detenido")

# Función para ejecutar en background
async def run_railway_monitor():
    """Ejecutar monitor en background"""
    monitor = RailwayMonitor()
    try:
        await monitor.start_monitoring()
    except KeyboardInterrupt:
        await monitor.stop_monitoring()

if __name__ == "__main__":
    asyncio.run(run_railway_monitor())
