from models import db


class TipoLavado(db.Model):
    """Modelo para almacenar los tipos de lavado disponibles"""
    __tablename__ = 'tipo_lavado'

    Id = db.Column(db.Integer, primary_key=True)
    Nombre = db.Column(db.String(50), nullable=False)
    Precio = db.Column(db.Numeric(10, 2), nullable=False)
    Id_Insumo = db.Column(db.Integer, db.ForeignKey('insumos.Id'))
    Estado = db.Column(db.String(50), default="activo")

    # Relaciones
    servicios = db.relationship('Servicio', back_populates='tipo_lavado')
    insumo_principal = db.relationship('Insumo', foreign_keys=[Id_Insumo])

    def __repr__(self):
        return f'<TipoLavado {self.Id}: {self.Nombre} - ${self.Precio}>'

    @property
    def nombre_precio(self):
        """Retorna nombre y precio para mostrar en selects"""
        return f"{self.Nombre} - ${self.Precio}"

    @property
    def total_servicios(self):
        """Retorna el número total de servicios con este tipo de lavado"""
        return len(self.servicios)

    @property
    def esta_activo(self):
        """Verifica si el tipo de lavado está activo"""
        return self.Estado.lower() == "activo"