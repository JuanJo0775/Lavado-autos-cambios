from flask import Blueprint, render_template, request, redirect, url_for, flash
from models import db, Servicio, ChecklistIngreso, Empleado, Vehiculo, TipoLavado, InsumoPorServicio, Insumo, Inventario
from datetime import datetime, date
from sqlalchemy import desc

servicio_bp = Blueprint('servicios', __name__, url_prefix='/servicios')


@servicio_bp.route('/')
def listar():
    """Listar todos los servicios con filtros opcionales"""
    # Obtener parámetros de filtrado
    estado = request.args.get('estado', '')
    fecha_str = request.args.get('fecha', '')
    placa = request.args.get('placa', '')

    # Construir consulta base
    query = Servicio.query

    # Aplicar filtros si se proporcionan
    if estado:
        query = query.filter(Servicio.Estado == estado)
    if fecha_str:
        try:
            fecha_obj = datetime.strptime(fecha_str, '%Y-%m-%d').date()
            query = query.filter(Servicio.Fecha == fecha_obj)
        except ValueError:
            flash('❌ Formato de fecha inválido. Use YYYY-MM-DD', 'warning')
    if placa:
        query = query.filter(Servicio.Placa.ilike(f'%{placa}%'))

    # Ordenar y ejecutar consulta
    servicios = query.order_by(desc(Servicio.Fecha), desc(Servicio.Hora_Recibe)).all()

    # Obtener estados únicos para el filtro
    estados_servicio = {s.Estado for s in Servicio.query.all() if s.Estado}

    return render_template('servicios/listado.html',
                           servicios=servicios,
                           estados_servicio=sorted(estados_servicio),
                           filtro_estado=estado,
                           filtro_fecha=fecha_str,
                           filtro_placa=placa)


@servicio_bp.route('/<int:id>')
def detalle(id):
    """Ver detalles de un servicio específico"""
    servicio = Servicio.query.get_or_404(id)
    checklist = ChecklistIngreso.query.filter_by(Id_Servicio=id).first()
    insumos_usados = InsumoPorServicio.query.filter_by(Id_Servicio=id).all()

    # Obtener insumos disponibles para mostrar en el modal de agregar insumo
    insumos = Insumo.query.filter_by(Estado='Activo').all()

    return render_template('servicios/detalle.html',
                           servicio=servicio,
                           checklist=checklist,
                           insumos_usados=insumos_usados,
                           insumos=insumos)


@servicio_bp.route('/registrar', methods=['GET', 'POST'])
def registrar():
    """Registrar un nuevo servicio"""
    if request.method == 'POST':
        # Recoger datos del formulario
        placa = request.form['placa']
        empleado_recibe_id = int(request.form['empleado_recibe'])
        empleado_lava_id = int(request.form['empleado_lava'])
        tipo_lavado_id = int(request.form['tipo_lavado'])
        observaciones = request.form['observaciones']

        # Obtener vehículo
        vehiculo = Vehiculo.query.filter_by(Placa=placa).first()
        if not vehiculo:
            flash('❌ Vehículo no encontrado. Por favor, regístrelo primero.', 'danger')
            return redirect(url_for('vehiculos.registrar', placa_redirect=placa))

        # Obtener tipo de lavado y su precio
        tipo_lavado = TipoLavado.query.get_or_404(tipo_lavado_id)
        precio = tipo_lavado.Precio

        # Crear nuevo servicio
        servicio = Servicio(
            Id_Empleado_Recibe=empleado_recibe_id,
            Id_Empleado_Lava=empleado_lava_id,
            Id_Tipovehículo=vehiculo.Id,
            Id_TipoLavado=tipo_lavado_id,
            Hora_Recibe=datetime.now().time(),
            Fecha=datetime.now().date(),
            Precio=precio,
            Placa=placa,
            Estado='En proceso'
        )

        # Guardar servicio
        db.session.add(servicio)
        db.session.commit()

        # Registrar checklist de ingreso
        checklist = ChecklistIngreso(
            Id_Servicio=servicio.Id,
            Observaciones=observaciones,
            EstadoVehiculo="Normal"
        )
        db.session.add(checklist)
        db.session.commit()

        flash('✅ Servicio registrado correctamente', 'success')
        return redirect(url_for('servicios.detalle', id=servicio.Id))

    # Mostrar formulario (GET)
    # Obtener todos los empleados sin filtrar por estado para evitar problemas
    empleados = Empleado.query.all()

    # Verificamos si la lista tiene elementos y la mostramos en el log
    print(f"Número de empleados recuperados: {len(empleados)}")
    for emp in empleados[:3]:  # Mostrar los primeros 3 como ejemplo
        print(f"Empleado: ID={emp.Id}, Nombre={emp.nombre_completo}, Estado={emp.Estado}")

    # También obtenemos todos los tipos de lavado sin filtrar por estado
    tipos_lavado = TipoLavado.query.all()

    # Verificamos si hay tipos de lavado disponibles
    print(f"Número de tipos de lavado recuperados: {len(tipos_lavado)}")
    for tipo in tipos_lavado[:3]:  # Mostrar los primeros 3 como ejemplo
        print(f"Tipo de lavado: ID={tipo.Id}, Nombre={tipo.Nombre}, Estado={tipo.Estado}")

    # Placa por defecto si viene de otro formulario
    placa_inicial = request.args.get('placa', '')

    return render_template('servicios/registro.html',
                           empleados=empleados,
                           tipos_lavado=tipos_lavado,
                           placa_inicial=placa_inicial)

@servicio_bp.route('/<int:id>/finalizar', methods=['POST'])
def finalizar(id):
    """Finalizar un servicio marcándolo como completado"""
    servicio = Servicio.query.get_or_404(id)

    # Verificar que el servicio esté en proceso
    if servicio.Estado != 'En proceso':
        flash('❌ Este servicio no está en proceso', 'danger')
        return redirect(url_for('servicios.detalle', id=id))

    # Actualizar estado y hora de entrega
    servicio.Estado = 'Completado'
    servicio.Hora_Entrega = datetime.now().time()
    db.session.commit()

    flash('✅ Servicio finalizado correctamente', 'success')
    return redirect(url_for('servicios.detalle', id=id))


@servicio_bp.route('/<int:id>/cancelar', methods=['POST'])
def cancelar(id):
    """Cancelar un servicio"""
    servicio = Servicio.query.get_or_404(id)

    # Verificar que el servicio esté en proceso
    if servicio.Estado != 'En proceso':
        flash('❌ Este servicio no está en proceso', 'danger')
        return redirect(url_for('servicios.detalle', id=id))

    # Actualizar estado
    servicio.Estado = 'Cancelado'
    db.session.commit()

    flash('❌ Servicio cancelado', 'warning')
    return redirect(url_for('servicios.detalle', id=id))


@servicio_bp.route('/<int:id>/agregar_insumo', methods=['POST'])
def agregar_insumo(id):
    """Agregar un insumo usado en el servicio"""
    servicio = Servicio.query.get_or_404(id)

    # Verificar que el servicio esté en proceso
    if servicio.Estado != 'En proceso':
        flash('❌ No se pueden agregar insumos a un servicio que no está en proceso', 'danger')
        return redirect(url_for('servicios.detalle', id=id))

    # Obtener datos del formulario
    insumo_id = int(request.form['insumo_id'])
    cantidad = int(request.form['cantidad'])

    # Verificar que la cantidad sea positiva
    if cantidad <= 0:
        flash('❌ La cantidad debe ser mayor a 0', 'danger')
        return redirect(url_for('servicios.detalle', id=id))

    # Verificar que haya suficiente stock
    insumo = Insumo.query.get_or_404(insumo_id)
    if insumo.stock_actual < cantidad:
        flash(f'❌ No hay suficiente stock de {insumo.Nombre}. Disponible: {insumo.stock_actual}', 'danger')
        return redirect(url_for('servicios.detalle', id=id))

    # Crear registro de insumo por servicio
    insumo_servicio = InsumoPorServicio(
        Id_Servicio=id,
        Id_Insumo=insumo_id,
        Cantidad_Utilizada=cantidad
    )
    db.session.add(insumo_servicio)

    # Actualizar inventario (restar cantidad utilizada)
    # Buscar el ítem de inventario para este insumo
    inventario_item = Inventario.query.filter_by(Id_insumo=insumo_id).first()
    if inventario_item:
        # Restar la cantidad usada
        inventario_item.Stock -= cantidad
        # Si el stock llega a cero, actualizar el estado
        if inventario_item.Stock <= 0:
            inventario_item.Stock = 0
            inventario_item.Estado = 0  # 0 = Agotado

    db.session.commit()

    flash(f'✅ Se agregaron {cantidad} unidades de {insumo.Nombre}', 'success')
    return redirect(url_for('servicios.detalle', id=id))



@servicio_bp.route('/en_proceso')
def en_proceso():
    """Muestra los servicios que están actualmente en proceso"""
    servicios = Servicio.query.filter_by(Estado='En proceso').order_by(Servicio.Fecha, Servicio.Hora_Recibe).all()

    # Estadísticas adicionales para la plantilla
    servicios_completados = Servicio.query.filter_by(Estado='Completado', Fecha=date.today()).count()
    ingresos_hoy = sum(float(s.Precio) for s in Servicio.query.filter_by(Fecha=date.today(), Estado='Completado').all())

    # Tiempo actual como datetime
    now = datetime.now()

    return render_template('servicios/en_proceso.html',
                           servicios=servicios,
                           servicios_completados=servicios_completados,
                           ingresos_hoy=ingresos_hoy,
                           now=now)


@servicio_bp.route('/historial_vehiculo/<placa>')
def historial_vehiculo(placa):
    """Muestra el historial de servicios para un vehículo específico"""
    vehiculo = Vehiculo.query.filter_by(Placa=placa).first_or_404()
    servicios = Servicio.query.filter_by(Placa=placa).order_by(desc(Servicio.Fecha), desc(Servicio.Hora_Recibe)).all()

    return render_template('servicios/historial_vehiculo.html',
                           vehiculo=vehiculo,
                           servicios=servicios)