from models import db
from datetime import datetime


class Empleado(db.Model):
    """Modelo para almacenar información de empleados"""
    __tablename__ = 'empleado'

    Id = db.Column(db.Integer, primary_key=True)
    Nombre = db.Column(db.String(50), nullable=False)
    Apellidos = db.Column(db.String(50), nullable=False)
    Fecha_Nacimiento = db.Column(db.Date, nullable=False)
    Estado = db.Column(db.String(50), default="Activo")

    # Relaciones
    servicios_recibe = db.relationship('Servicio',
                                       foreign_keys='Servicio.Id_Empleado_Recibe',
                                       back_populates='empleado_recibe')
    servicios_lava = db.relationship('Servicio',
                                     foreign_keys='Servicio.Id_Empleado_Lava',
                                     back_populates='empleado_lava')
    turnos = db.relationship('TurnoEmpleado', back_populates='empleado')

    def __repr__(self):
        return f'<Empleado {self.Id}: {self.Nombre} {self.Apellidos}>'

    @property
    def nombre_completo(self):
        """Retorna el nombre completo del empleado"""
        return f"{self.Nombre} {self.Apellidos}"

    @property
    def edad(self):
        """Calcula la edad actual del empleado"""
        today = datetime.now().date()
        return today.year - self.Fecha_Nacimiento.year - (
                (today.month, today.day) < (self.Fecha_Nacimiento.month, self.Fecha_Nacimiento.day)
        )

    @property
    def servicios_recibidos_hoy(self):
        """Retorna el número de servicios recibidos hoy por este empleado"""
        from datetime import date
        return len([s for s in self.servicios_recibe if s.Fecha == date.today()])

    @property
    def servicios_lavados_hoy(self):
        """Retorna el número de servicios lavados hoy por este empleado"""
        from datetime import date
        return len([s for s in self.servicios_lava if s.Fecha == date.today()])