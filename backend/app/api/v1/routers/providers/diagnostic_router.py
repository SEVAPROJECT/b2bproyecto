# app/api/v1/routers/providers/diagnostic_router.py
"""
Router para endpoints de diagnóstico y pruebas de proveedores.
Estos endpoints no son parte de la funcionalidad principal y pueden ser deshabilitados en producción.
"""

from fastapi import APIRouter, HTTPException, status
from datetime import datetime

from app.services.storage_service import storage_service
from app.api.v1.routers.providers.constants import MSG_ERROR_DIAGNOSTICO

router = APIRouter(tags=["providers-diagnostic"])  # Sin prefix - el router principal ya lo tiene


@router.get(
    "/diagnostic",
    description="Diagnóstico básico del endpoint de proveedores"
)
async def diagnostic_endpoint():
    """
    Endpoint de diagnóstico simple para verificar funcionamiento básico
    """
    try:
        return {
            "status": "ok",
            "message": "Endpoint de proveedores funcionando correctamente",
            "timestamp": datetime.now().isoformat(),
            "routes": [
                "/solicitar-verificacion",
                "/mis-documentos",
                "/mis-datos-solicitud",
                "/services/proponer",
                "/download-document",
                "/diagnostic",
                "/diagnostic/storage"
            ],
            "notes": [
                "Refactorización completada - código separado por responsabilidades",
                "Servicios creados para: verificación, documentos, direcciones, empresas",
                "Repositorio unificado para acceso a datos",
                "Routers separados por funcionalidad"
            ]
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Error en diagnóstico: {str(e)}",
            "timestamp": datetime.now().isoformat()
        }


@router.get(
    "/diagnostic/storage",
    description="Diagnóstico del sistema de almacenamiento (iDrive y local)"
)
async def diagnose_storage_system():
    """
    Endpoint para diagnosticar el estado del sistema de almacenamiento
    """
    try:
        # Obtener diagnóstico de ambos servicios
        results = storage_service.test_services()
        
        # Información adicional del sistema
        system_info = {
            "timestamp": datetime.now().isoformat(),
            "services": results,
            "recommendations": []
        }
        
        # Agregar recomendaciones basadas en el estado
        if results["idrive"]["status"] == "error":
            system_info["recommendations"].append({
                "service": "iDrive",
                "issue": results["idrive"]["message"],
                "solution": "Verificar credenciales, permisos y conectividad de red"
            })
        
        if results["local"]["status"] == "error":
            system_info["recommendations"].append({
                "service": "Local Storage",
                "issue": results["local"]["message"],
                "solution": "Verificar permisos de escritura en directorio uploads"
            })
        
        if results["idrive"]["status"] == "ok" and results["local"]["status"] == "ok":
            system_info["recommendations"].append({
                "service": "General",
                "issue": "Ninguno",
                "solution": "Sistema funcionando correctamente"
            })
        
        return system_info
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=MSG_ERROR_DIAGNOSTICO.format(error=str(e))
        )

