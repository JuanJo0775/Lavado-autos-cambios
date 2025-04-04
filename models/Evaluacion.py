from models import db
from datetime import datetime


class Evaluacion(db.Model):
    """Modelo para almacenar las evaluaciones de los servicios"""
    __tablename__ = 'evaluacion'

    Id = db.Column(db.Integer, primary_key=True)
    Id_Servicio = db.Column(db.Integer, db.ForeignKey('servicios.Id'))
    Tiempo_Espera = db.Column(db.Integer, nullable=False)  # Calificación 1-5
    Amabilidad = db.Column(db.Integer, nullable=False)  # Calificación 1-5
    Calidad_Servicio = db.Column(db.Integer, nullable=False)  # Calificación 1-5
    Comentario = db.Column(db.Text, nullable=True)
    Fecha_Evaluacion = db.Column(db.DateTime, default=datetime.now)

    # Relaciones
    servicio = db.relationship('Servicio', backref=db.backref('evaluacion', uselist=False))

    def __repr__(self):
        return f'<Evaluacion {self.Id} para Servicio {self.Id_Servicio}>'

    @property
    def calificacion_promedio(self):
        """Calcula el promedio de las tres calificaciones"""
        return round((self.Tiempo_Espera + self.Amabilidad + self.Calidad_Servicio) / 3, 1)