from flask import Blueprint, render_template, request, redirect, url_for, flash
from models import db, Vehiculo, Servicio
from datetime import datetime

vehiculo_bp = Blueprint('vehiculos', __name__, url_prefix='/vehiculos')


@vehiculo_bp.route('/')
def listar():
    """Lista todos los vehículos registrados"""
    # Obtener parámetros de filtrado
    filtro_placa = request.args.get('placa', '')
    filtro_tipo = request.args.get('tipo', '')

    # Construir consulta base
    query = Vehiculo.query

    # Aplicar filtros si se proporcionan
    if filtro_placa:
        query = query.filter(Vehiculo.Placa.ilike(f'%{filtro_placa}%'))
    if filtro_tipo:
        query = query.filter(Vehiculo.Tipo_Vehículo == filtro_tipo)

    # Ordenar y ejecutar consulta
    vehiculos = query.order_by(Vehiculo.Placa).all()

    # Obtener lista de tipos de vehículos para el filtro
    tipos_vehiculo = {v.Tipo_Vehículo for v in Vehiculo.query.all()}

    return render_template('vehiculos/listado.html',
                           vehiculos=vehiculos,
                           tipos_vehiculo=sorted(tipos_vehiculo),
                           filtro_placa=filtro_placa,
                           filtro_tipo=filtro_tipo)


@vehiculo_bp.route('/<int:id>')
def detalle(id):
    """Muestra detalles de un vehículo específico"""
    vehiculo = Vehiculo.query.get_or_404(id)

    # Obtener todos los servicios de este vehículo
    servicios = Servicio.query.filter_by(Id_Tipovehículo=id).order_by(Servicio.Fecha.desc(),
                                                                      Servicio.Hora_Recibe.desc()).all()

    return render_template('vehiculos/detalle.html',
                           vehiculo=vehiculo,
                           servicios=servicios)


@vehiculo_bp.route('/registrar', methods=['GET', 'POST'])
def registrar():
    """Registra un nuevo vehículo"""
    if request.method == 'POST':
        placa = request.form['placa']
        marca = request.form['marca']
        modelo = request.form['modelo']
        color = request.form['color']
        tipo_vehiculo = request.form['tipo_vehiculo']
        descripcion = request.form['descripcion']
        estado = request.form['estado']

        # Verificar si la placa ya existe
        vehiculo_existente = Vehiculo.query.filter_by(Placa=placa).first()
        if vehiculo_existente:
            flash('❌ Ya existe un vehículo con esa placa', 'danger')
            return render_template('vehiculos/registro.html',
                                   valores=request.form)

        # Crear nuevo vehículo
        vehiculo = Vehiculo(
            Placa=placa,
            Marca=marca,
            Modelo=modelo,
            Color=color,
            Tipo_Vehículo=tipo_vehiculo,
            Descripcion=descripcion,
            Estado=estado
        )

        db.session.add(vehiculo)
        db.session.commit()

        flash('✅ Vehículo registrado correctamente', 'success')
        return redirect(url_for('vehiculos.detalle', id=vehiculo.Id))

    # Valores iniciales o redirección desde otro formulario
    placa_inicial = request.args.get('placa_redirect', '')

    return render_template('vehiculos/registro.html',
                           placa_inicial=placa_inicial)


@vehiculo_bp.route('/<int:id>/editar', methods=['GET', 'POST'])
def editar(id):
    """Editar un vehículo existente"""
    vehiculo = Vehiculo.query.get_or_404(id)

    if request.method == 'POST':
        vehiculo.Marca = request.form['marca']
        vehiculo.Modelo = request.form['modelo']
        vehiculo.Color = request.form['color']
        vehiculo.Tipo_Vehículo = request.form['tipo_vehiculo']
        vehiculo.Descripcion = request.form['descripcion']
        vehiculo.Estado = request.form['estado']

        db.session.commit()
        flash('✅ Vehículo actualizado correctamente', 'success')
        return redirect(url_for('vehiculos.detalle', id=vehiculo.Id))

    return render_template('vehiculos/editar.html', vehiculo=vehiculo)


@vehiculo_bp.route('/<int:id>/cambiar_estado', methods=['POST'])
def cambiar_estado(id):
    """Cambia el estado de un vehículo (activo/inactivo)"""
    vehiculo = Vehiculo.query.get_or_404(id)

    nuevo_estado = "Inactivo" if vehiculo.Estado == "Activo" else "Activo"
    vehiculo.Estado = nuevo_estado
    db.session.commit()

    flash(f'✅ Estado cambiado a {nuevo_estado}', 'success')
    return redirect(url_for('vehiculos.detalle', id=id))