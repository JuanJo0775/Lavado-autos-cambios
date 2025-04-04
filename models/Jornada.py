from models import db


class Jornada(db.Model):
    """Modelo para definir los horarios de jornada laboral"""
    __tablename__ = 'jornada'

    Id = db.Column(db.Integer, primary_key=True)
    Hora_Inicio = db.Column(db.Time, nullable=False)
    Hora_Final = db.Column(db.Time, nullable=False)
    Estado = db.Column(db.String(50), default="Activo")

    # Relaciones
    turnos = db.relationship('TurnoEmpleado', back_populates='jornada')

    def __repr__(self):
        return f'<Jornada {self.Id}: {self.Hora_Inicio} - {self.Hora_Final}>'

    @property
    def rango_horario(self):
        """Retorna el rango horario formateado"""
        inicio = self.Hora_Inicio.strftime('%H:%M')
        final = self.Hora_Final.strftime('%H:%M')
        return f"{inicio} - {final}"


class TurnoEmpleado(db.Model):
    """Modelo para asignar turnos a empleados"""
    __tablename__ = 'turno_empleado'

    Id = db.Column(db.Integer, primary_key=True)
    Id_Empleado = db.Column(db.Integer, db.ForeignKey('empleado.Id'))
    Día = db.Column(db.String(50), nullable=False)
    Id_Jornada = db.Column(db.Integer, db.ForeignKey('jornada.Id'))

    # Relaciones
    empleado = db.relationship('Empleado', back_populates='turnos')
    jornada = db.relationship('Jornada', back_populates='turnos')

    def __repr__(self):
        empleado_nombre = self.empleado.nombre_completo if self.empleado else "N/A"
        jornada_rango = self.jornada.rango_horario if self.jornada else "N/A"
        return f'<Turno {self.Id}: {empleado_nombre} - {self.Día} {jornada_rango}>'