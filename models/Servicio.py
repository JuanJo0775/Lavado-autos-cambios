from models import db
from datetime import datetime, time


class Servicio(db.Model):
    """Modelo para registrar servicios de lavado"""
    __tablename__ = 'servicios'

    Id = db.Column(db.Integer, primary_key=True)
    Id_Empleado_Recibe = db.Column(db.Integer, db.ForeignKey('empleado.Id'))
    Id_Empleado_Lava = db.Column(db.Integer, db.ForeignKey('empleado.Id'))
    Id_Tipovehículo = db.Column(db.Integer, db.ForeignKey('vehículos.Id'))
    Id_TipoLavado = db.Column(db.Integer, db.ForeignKey('tipo_lavado.Id'))
    Hora_Recibe = db.Column(db.Time, nullable=False)
    Hora_Entrega = db.Column(db.Time)
    Precio = db.Column(db.Numeric(10, 2), nullable=False)
    Placa = db.Column(db.String(50), nullable=False)
    Fecha = db.Column(db.Date, nullable=False)
    Estado = db.Column(db.String(50), default='En proceso')

    # Relaciones
    empleado_recibe = db.relationship('Empleado', foreign_keys=[Id_Empleado_Recibe], back_populates='servicios_recibe')
    empleado_lava = db.relationship('Empleado', foreign_keys=[Id_Empleado_Lava], back_populates='servicios_lava')
    vehiculo = db.relationship('Vehiculo', back_populates='servicios')
    tipo_lavado = db.relationship('TipoLavado', back_populates='servicios')
    checklist = db.relationship('ChecklistIngreso', back_populates='servicio', uselist=False)
    insumos_usados = db.relationship('InsumoPorServicio', back_populates='servicio')

    def __repr__(self):
        return f'<Servicio {self.Id}: {self.Placa} - {self.tipo_lavado.Nombre if self.tipo_lavado else "N/A"}>'

    @property
    def duracion(self):
        """Calcula la duración del servicio en minutos"""
        if not self.Hora_Entrega:
            return None

        # Convertir a datetime para poder restar
        fecha = self.Fecha
        recibe = datetime.combine(fecha, self.Hora_Recibe)
        entrega = datetime.combine(fecha, self.Hora_Entrega)

        # Si la entrega es al día siguiente (cruce de medianoche)
        if entrega < recibe:
            entrega = datetime.combine(fecha.replace(day=fecha.day + 1), self.Hora_Entrega)

        diff = entrega - recibe
        return diff.total_seconds() // 60  # Duración en minutos

    @property
    def esta_completado(self):
        """Verifica si el servicio está completado"""
        return self.Estado.lower() == 'completado'

    @property
    def esta_en_proceso(self):
        """Verifica si el servicio está en proceso"""
        return self.Estado.lower() == 'en proceso'

    @classmethod
    def servicios_del_dia(cls, fecha=None):
        """Retorna los servicios para una fecha específica"""
        if fecha is None:
            fecha = datetime.now().date()
        return cls.query.filter_by(Fecha=fecha).all()

    @classmethod
    def servicios_en_proceso(cls):
        """Retorna los servicios que están en proceso"""
        return cls.query.filter_by(Estado='En proceso').order_by(cls.Fecha, cls.Hora_Recibe).all()


class ChecklistIngreso(db.Model):
    """Modelo para el checklist de ingreso de vehículos"""
    __tablename__ = 'checklist_ingreso'

    Id = db.Column(db.Integer, primary_key=True)
    Id_Servicio = db.Column(db.Integer, db.ForeignKey('servicios.Id'))
    Observaciones = db.Column(db.Text)
    EstadoVehiculo = db.Column(db.String(100), default="Normal")

    # Relaciones
    servicio = db.relationship('Servicio', back_populates='checklist')

    def __repr__(self):
        return f'<ChecklistIngreso {self.Id} para Servicio {self.Id_Servicio}>'



class InsumoPorServicio(db.Model):
    """Modelo para registrar los insumos utilizados en cada servicio"""
    __tablename__ = 'insumos_por_servicio'

    Id = db.Column(db.Integer, primary_key=True)
    Id_Servicio = db.Column(db.Integer, db.ForeignKey('servicios.Id'))
    Id_Insumo = db.Column(db.Integer, db.ForeignKey('insumos.Id'))
    Cantidad_Utilizada = db.Column(db.Integer, nullable=False)

    # Relaciones
    servicio = db.relationship('Servicio', back_populates='insumos_usados')
    insumo = db.relationship('Insumo')

    def __repr__(self):
        insumo_nombre = self.insumo.Nombre if self.insumo else "N/A"
        return f'<InsumoPorServicio {self.Id}: {insumo_nombre} - Cantidad: {self.Cantidad_Utilizada}>'

    @property
    def costo_total(self):
        """Calcula el costo total de los insumos usados"""
        if not self.insumo:
            return 0
        return float(self.insumo.Precio_Unitario) * self.Cantidad_Utilizada