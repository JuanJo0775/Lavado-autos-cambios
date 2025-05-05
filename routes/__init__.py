from .dashboard import dashboard_bp
from .vehiculos import vehiculo_bp
from .servicios import servicio_bp
from .insumos import insumo_bp
from .inventario import inventario_bp
from .reportes import reporte_bp
from .evaluaciones import evaluacion_bp
from .cotizaciones import cotizacion_bp
from .empleados import empleado_bp
from .tipo_lavado import tipo_lavado_bp

def register_blueprints(app):
    """Registra todos los blueprints de la aplicación"""
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(vehiculo_bp)
    app.register_blueprint(servicio_bp)
    app.register_blueprint(insumo_bp)
    app.register_blueprint(inventario_bp)
    app.register_blueprint(reporte_bp)
    app.register_blueprint(evaluacion_bp)
    app.register_blueprint(cotizacion_bp)
    app.register_blueprint(empleado_bp)
    app.register_blueprint(tipo_lavado_bp)