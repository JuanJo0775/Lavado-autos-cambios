from flask import Flask, render_template
from config import active_config
from models import db, init_app
from flask_migrate import Migrate
from sqlalchemy.exc import OperationalError
from routes import register_blueprints
import logging
import os

# Configuración de logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    handlers=[logging.FileHandler("app.log"),
                              logging.StreamHandler()])
logger = logging.getLogger(__name__)


def create_app(config_object=None):
    """Crea y configura la aplicación Flask"""
    app = Flask(__name__)

    # Configuración de la aplicación
    if config_object:
        app.config.from_object(config_object)
    else:
        app.config.from_object(active_config)

    # Asegurarse de que existe el directorio para uploads
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

    # Inicializar la base de datos
    init_app(app)

    # Configurar migración de base de datos
    migrate = Migrate(app, db)

    # Registrar blueprints (rutas)
    register_blueprints(app)

    # Configurar manejadores de errores
    register_error_handlers(app)

    # Verificar conexión a la base de datos
    with app.app_context():
        try:
            from sqlalchemy import text
            db.session.execute(text('SELECT 1'))
            logger.info("✅ Conexión a la base de datos exitosa.")
        except OperationalError as e:
            logger.error(f"❌ Error al conectar a la base de datos: {e}")

    return app


def register_error_handlers(app):
    """Registra manejadores de errores para la aplicación"""

    @app.errorhandler(404)
    def page_not_found(e):
        return render_template('errors/404.html'), 404

    @app.errorhandler(500)
    def internal_server_error(e):
        return render_template('errors/500.html'), 500

    @app.errorhandler(OperationalError)
    def db_error(e):
        logger.error(f"Error de base de datos: {e}")
        return render_template('errors/500.html',
                               error="Error de conexión a la base de datos. Por favor, contacte al administrador."), 500


# Crear la aplicación
app = create_app()

if __name__ == '__main__':
    # Crear directorios necesarios para el proyecto si no existen
    os.makedirs('logs', exist_ok=True)

    # Crear directorios para las plantillas de errores si no existen
    os.makedirs('templates/errors', exist_ok=True)

    # Crear y guardar plantillas de error si no existen
    error_templates = {
        '404.html': """{% extends "base.html" %}
{% block title %}404 - Página no encontrada{% endblock %}
{% block content %}
<div class="text-center py-5">
    <h1 class="display-1 fw-bold text-danger">404</h1>
    <p class="fs-3">Página no encontrada</p>
    <p class="lead">La página que está buscando no existe o ha sido movida.</p>
    <a href="{{ url_for('dashboard.index') }}" class="btn btn-primary">Volver al inicio</a>
</div>
{% endblock %}""",
        '500.html': """{% extends "base.html" %}
{% block title %}500 - Error del servidor{% endblock %}
{% block content %}
<div class="text-center py-5">
    <h1 class="display-1 fw-bold text-danger">500</h1>
    <p class="fs-3">Error interno del servidor</p>
    <p class="lead">{{ error|default('Ha ocurrido un error inesperado.') }}</p>
    <a href="{{ url_for('dashboard.index') }}" class="btn btn-primary">Volver al inicio</a>
</div>
{% endblock %}"""
    }

    for template_name, content in error_templates.items():
        template_path = f'templates/errors/{template_name}'
        if not os.path.exists(template_path):
            with open(template_path, 'w') as f:
                f.write(content)

    app.run(debug=True, host='0.0.0.0', port=5000)