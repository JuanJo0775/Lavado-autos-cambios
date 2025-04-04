from models import db

class TipoInsumo(db.Model):
    """Modelo para categorizar los insumos"""
    __tablename__ = 'tipo_insumo'

    Id = db.Column(db.Integer, primary_key=True)
    Nombre = db.Column(db.String(50), nullable=False)
    Descripción = db.Column(db.String(200))  # Corregido: cambiado de Integer a String
    Estado = db.Column(db.Integer, default=1)  # 1=Activo, 0=Inactivo

    # Relaciones
    insumos = db.relationship('Insumo', back_populates='tipo_insumo')

    def __repr__(self):
        return f'<TipoInsumo {self.Id}: {self.Nombre}>'

    @property
    def estado_texto(self):
        """Retorna el estado en formato texto"""
        return "Activo" if self.Estado == 1 else "Inactivo"
        return f'<TipoInsumo {self.Id}: {self.Nombre}>'


class Insumo(db.Model):
    """Modelo para almacenar insumos para lavado"""
    __tablename__ = 'insumos'

    Id = db.Column(db.Integer, primary_key=True)
    Nombre = db.Column(db.String(50), nullable=False)
    Precio_Unitario = db.Column(db.Numeric(10, 2), nullable=False)
    Id_TipoInsumo = db.Column(db.Integer, db.ForeignKey('tipo_insumo.Id'))
    Estado = db.Column(db.String(50), default="Activo")

    # Relaciones
    tipo_insumo = db.relationship('TipoInsumo', back_populates='insumos')
    inventario_items = db.relationship('Inventario', back_populates='insumo')

    def __repr__(self):
        return f'<Insumo {self.Id}: {self.Nombre} - ${self.Precio_Unitario}>'

    @property
    def stock_actual(self):
        """Retorna el stock actual del insumo"""
        if not self.inventario_items:
            return 0
        return sum(item.Stock for item in self.inventario_items)

    @property
    def necesita_reposicion(self):
        """Indica si el insumo necesita reposición (stock < 10)"""
        return self.stock_actual < 10

    @property
    def valor_inventario(self):
        """Calcula el valor total del insumo en inventario"""
        return float(self.Precio_Unitario) * self.stock_actual