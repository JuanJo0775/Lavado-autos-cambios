from models import db
from datetime import datetime


class Proveedor(db.Model):
    """Modelo para almacenar información de proveedores"""
    __tablename__ = 'proveedor'

    Id = db.Column(db.Integer, primary_key=True)
    Nombre = db.Column(db.String(100), nullable=False)
    Contacto = db.Column(db.String(100), nullable=False)
    Email = db.Column(db.String(100), nullable=False)
    Telefono = db.Column(db.String(20), nullable=False)
    Direccion = db.Column(db.String(200), nullable=True)
    Fecha_Registro = db.Column(db.DateTime, default=datetime.now)
    Estado = db.Column(db.String(20), default="Activo")

    # Relaciones
    cotizaciones = db.relationship('Cotizacion', back_populates='proveedor')

    def __repr__(self):
        return f'<Proveedor {self.Id}: {self.Nombre}>'


class Cotizacion(db.Model):
    """Modelo para almacenar cotizaciones de precios de insumos"""
    __tablename__ = 'cotizacion'

    Id = db.Column(db.Integer, primary_key=True)
    Id_Proveedor = db.Column(db.Integer, db.ForeignKey('proveedor.Id'))
    Id_Insumo = db.Column(db.Integer, db.ForeignKey('insumos.Id'))
    Precio = db.Column(db.Numeric(10, 2), nullable=False)
    Fecha_Cotizacion = db.Column(db.DateTime, default=datetime.now)
    Observaciones = db.Column(db.Text, nullable=True)
    Estado = db.Column(db.String(20), default="Pendiente")  # Pendiente, Aprobada, Rechazada

    # Relaciones
    proveedor = db.relationship('Proveedor', back_populates='cotizaciones')
    insumo = db.relationship('Insumo')

    def __repr__(self):
        return f'<Cotizacion {self.Id}: {self.insumo.Nombre if self.insumo else "N/A"} - ${self.Precio}>'


class SolicitudCotizacion(db.Model):
    """Modelo para almacenar solicitudes de cotización de insumos"""
    __tablename__ = 'solicitud_cotizacion'

    Id = db.Column(db.Integer, primary_key=True)
    Id_Insumo = db.Column(db.Integer, db.ForeignKey('insumos.Id'))
    Cantidad_Requerida = db.Column(db.Integer, nullable=False)
    Fecha_Limite = db.Column(db.Date, nullable=True)
    Descripcion = db.Column(db.Text, nullable=True)
    Fecha_Publicacion = db.Column(db.DateTime, default=datetime.now)
    Estado = db.Column(db.String(20), default="Activa")  # Activa, Cerrada

    # Relaciones
    insumo = db.relationship('Insumo')

    def __repr__(self):
        return f'<SolicitudCotizacion {self.Id}: {self.insumo.Nombre if self.insumo else "N/A"} - {self.Cantidad_Requerida} unidades>'