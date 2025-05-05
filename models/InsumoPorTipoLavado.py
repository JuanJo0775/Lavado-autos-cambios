from models import db

class InsumoPorTipoLavado(db.Model):
    """Modelo para registrar los insumos necesarios para cada tipo de lavado"""
    __tablename__ = 'insumos_por_tipo_lavado'

    Id = db.Column(db.Integer, primary_key=True)
    Id_TipoLavado = db.Column(db.Integer, db.ForeignKey('tipo_lavado.Id'))
    Id_Insumo = db.Column(db.Integer, db.ForeignKey('insumos.Id'))
    Cantidad_Requerida = db.Column(db.Integer, nullable=False)

    # Relaciones
    tipo_lavado = db.relationship('TipoLavado', back_populates='insumos_requeridos')
    insumo = db.relationship('Insumo')

    def __repr__(self):
        insumo_nombre = self.insumo.Nombre if self.insumo else "N/A"
        tipo_lavado_nombre = self.tipo_lavado.Nombre if self.tipo_lavado else "N/A"
        return f'<InsumoPorTipoLavado: {tipo_lavado_nombre} requiere {self.Cantidad_Requerida} de {insumo_nombre}>'