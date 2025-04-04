import os
from datetime import timedelta


class Config:
    """Configuración base"""
    # Conexión a MariaDB o MySQL
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URI',
                                             'mysql+mysqlconnector://root:@localhost:3306/lavadoautos_base_cambios')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECRET_KEY = os.environ.get('SECRET_KEY', 'clave-secreta-predeterminada')

    # Configuración de sesión
    PERMANENT_SESSION_LIFETIME = timedelta(hours=2)

    # Configuración de archivos
    UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static/uploads')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # Máximo 16 MB


class DevelopmentConfig(Config):
    """Configuración de desarrollo"""
    DEBUG = True
    SQLALCHEMY_ECHO = True


class ProductionConfig(Config):
    """Configuración de producción"""
    DEBUG = False

    # En producción, asegúrate de tener estas variables de entorno configuradas
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URI')
    SECRET_KEY = os.environ.get('SECRET_KEY')


# Configuración por defecto
config_by_name = {
    'dev': DevelopmentConfig,
    'prod': ProductionConfig
}

# Configuración activa
active_config = config_by_name[os.environ.get('FLASK_ENV', 'dev')]



