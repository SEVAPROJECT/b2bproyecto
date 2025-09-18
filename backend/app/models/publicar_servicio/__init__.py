# Importar todos los modelos para hacerlos disponibles para SQLAlchemy
from .category import Categoria
from .service import Servicio
from .moneda import Moneda
from .tarifa_servicio import TarifaServicio
from .tipo_tarifa_servicio import TipoTarifaServicio
from .solicitud_servicio import SolicitudServicio
from .solicitud_categoria import SolicitudCategoria

__all__ = [
    'Categoria',
    'Servicio',
    'Moneda',
    'TarifaServicio',
    'TipoTarifaServicio',
    'SolicitudServicio',
    'SolicitudCategoria'
]

