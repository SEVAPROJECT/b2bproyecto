# backend/app/api/v1/routers/reserva.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.schemas.reserva_sevicio.reserva import ReservaIn, ReservaOut
from app.models.reserva_servicio.reserva import ReservaModel
from app.api.v1.dependencies.database_supabase import get_async_db
from app.api.v1.dependencies.auth_user import get_current_user
from app.schemas.auth_user import SupabaseUser
import logging
from uuid import UUID

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/reservas", tags=["reservas"])

@router.post(
    "/",
    response_model=ReservaOut,
    status_code=status.HTTP_201_CREATED,
    description="Permite a un usuario cliente crear una nueva reserva de servicio."
)
async def crear_reserva(
    reserva: ReservaIn,
    current_user: SupabaseUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Crea una nueva reserva de servicio.
    Requiere autenticación de usuario.
    """
    logger.info(f"Creando reserva para servicio {reserva.id_servicio} por usuario {current_user.id}")
    
    # Crea una nueva instancia del modelo de reserva
    nueva_reserva = ReservaModel(
        id_servicio=reserva.id_servicio,
        id_usuario=UUID(current_user.id),
        descripcion=reserva.descripcion,
        observacion=reserva.observacion,
        fecha=reserva.fecha,
        estado="pendiente"
    )
    
    try:
        db.add(nueva_reserva)
        await db.commit()
        await db.refresh(nueva_reserva)
        logger.info(f"Reserva {nueva_reserva.id} creada exitosamente.")
        return nueva_reserva
    except Exception as e:
        await db.rollback()
        logger.error(f"Error al crear la reserva: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ocurrió un error al procesar tu reserva."
        )