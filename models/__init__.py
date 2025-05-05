from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

# Importamos los modelos después de definir db para evitar problemas de dependencia circular
from .Empleado import Empleado
from .Vehiculo import Vehiculo
from .Insumo import Insumo, TipoInsumo
from .Inventario import Inventario
from .Jornada import Jornada, TurnoEmpleado
from .InsumoPorTipoLavado import InsumoPorTipoLavado
from .TipoLavado import TipoLavado
from .Servicio import Servicio, ChecklistIngreso, InsumoPorServicio
from .Evaluacion import Evaluacion
from .Cotizacion import Proveedor, Cotizacion, SolicitudCotizacion

# Función para inicializar la BD con la app
def init_app(app):
    db.init_app(app)