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
    insumos_requeridos = db.relationship('InsumoPorTipoLavado', back_populates='tipo_lavado',
                                         cascade="all, delete-orphan")

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

    def get_insumos_requeridos(self):
        """Retorna una lista de diccionarios con los insumos requeridos y sus cantidades"""
        return [
            {
                'insumo': insumo_requerido.insumo,
                'cantidad': insumo_requerido.Cantidad_Requerida
            }
            for insumo_requerido in self.insumos_requeridos
        ]

    def tiene_suficiente_stock(self):
        """Verifica si hay suficiente stock de todos los insumos requeridos"""
        for insumo_requerido in self.insumos_requeridos:
            insumo = insumo_requerido.insumo
            if insumo.stock_actual < insumo_requerido.Cantidad_Requerida:
                return False
        return True

    def consumir_insumos(self, id_servicio=None):
        """
        Consume los insumos necesarios del inventario y registra el uso

        Args:
            id_servicio (int, optional): ID del servicio al que se asociarán los insumos.
                                        Si se proporciona, se crearán registros en InsumoPorServicio.
        """
        from models import Inventario, InsumoPorServicio, db

        # Para cada insumo requerido para este tipo de lavado
        for insumo_req in self.insumos_requeridos:
            # Buscar el ítem de inventario para este insumo
            inventario_item = Inventario.query.filter_by(Id_insumo=insumo_req.Id_Insumo).first()
            if inventario_item:
                # Restar la cantidad usada
                inventario_item.Stock -= insumo_req.Cantidad_Requerida
                # Si el stock llega a cero, actualizar el estado
                if inventario_item.Stock <= 0:
                    inventario_item.Stock = 0
                    inventario_item.Estado = 0  # 0 = Agotado

                # Si se proporcionó un ID de servicio, registrar el uso del insumo
                if id_servicio:
                    insumo_servicio = InsumoPorServicio(
                        Id_Servicio=id_servicio,
                        Id_Insumo=insumo_req.Id_Insumo,
                        Cantidad_Utilizada=insumo_req.Cantidad_Requerida
                    )
                    db.session.add(insumo_servicio)