from models import db


class Inventario(db.Model):
    """Modelo para gestionar el inventario de insumos"""
    __tablename__ = 'inventario'

    Id = db.Column(db.Integer, primary_key=True)
    Id_insumo = db.Column(db.Integer, db.ForeignKey('insumos.Id'))
    Stock = db.Column(db.Integer, nullable=False)
    Estado = db.Column(db.Integer)  # En la BD está como Integer pero conceptualmente es un string

    # Relaciones
    insumo = db.relationship('Insumo', back_populates='inventario_items')

    def __repr__(self):
        return f'<Inventario {self.Id}: {self.insumo.Nombre if self.insumo else "N/A"} - Stock: {self.Stock}>'

    @property
    def valor_total(self):
        """Calcula el valor total del item de inventario"""
        if not self.insumo:
            return 0
        return float(self.insumo.Precio_Unitario) * self.Stock

    @property
    def estado_texto(self):
        """Convierte el estado numérico a texto"""
        if self.Estado == 1:
            return "Disponible"
        elif self.Estado == 0:
            return "Agotado"
        return "Desconocido"