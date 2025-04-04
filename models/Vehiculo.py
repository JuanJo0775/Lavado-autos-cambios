from models import db
from datetime import datetime


class Vehiculo(db.Model):
    """Modelo para almacenar información de vehículos"""
    __tablename__ = 'vehículos'

    Id = db.Column(db.Integer, primary_key=True)
    Placa = db.Column(db.String(20), unique=True, nullable=False, index=True)
    Marca = db.Column(db.String(50), nullable=False)
    Modelo = db.Column(db.String(50), nullable=False)
    Color = db.Column(db.String(50), nullable=False)
    Tipo_Vehículo = db.Column(db.String(50), nullable=False)
    Descripcion = db.Column(db.String(200))
    Estado = db.Column(db.String(20), default="Activo")

    # Relaciones
    servicios = db.relationship('Servicio', back_populates='vehiculo')

    def __repr__(self):
        return f'<Vehículo {self.Placa} - {self.Marca} {self.Modelo}>'

    @property
    def info_completa(self):
        """Retorna información completa del vehículo"""
        return f"{self.Marca} {self.Modelo} - {self.Color} - {self.Placa}"

    @property
    def total_servicios(self):
        """Retorna el número total de servicios de este vehículo"""
        return len(self.servicios)

    @property
    def ultimo_servicio(self):
        """Retorna el último servicio realizado a este vehículo"""
        if not self.servicios:
            return None
        return sorted(self.servicios, key=lambda s: (s.Fecha, s.Hora_Recibe), reverse=True)[0]

    @classmethod
    def buscar_por_placa(cls, placa):
        """Busca un vehículo por su placa"""
        return cls.query.filter(cls.Placa.ilike(f'%{placa}%')).all()