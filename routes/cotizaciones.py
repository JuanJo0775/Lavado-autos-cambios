from flask import Blueprint, render_template, request, redirect, url_for, flash, abort
from models import db, Insumo, Proveedor, Cotizacion, SolicitudCotizacion
from sqlalchemy import desc
from datetime import datetime, date, timedelta

cotizacion_bp = Blueprint('cotizaciones', __name__, url_prefix='/cotizaciones')


# ========================== Rutas para Panel de Administración ==========================

@cotizacion_bp.route('/')
def index():
    """Panel de administración de cotizaciones"""
    # Obtener solicitudes activas
    solicitudes_activas = SolicitudCotizacion.query.filter_by(Estado='Activa').order_by(
        SolicitudCotizacion.Fecha_Publicacion.desc()).all()

    # Obtener últimas cotizaciones recibidas
    cotizaciones_recientes = db.session.query(Cotizacion, Proveedor, Insumo).join(
        Proveedor, Cotizacion.Id_Proveedor == Proveedor.Id
    ).join(
        Insumo, Cotizacion.Id_Insumo == Insumo.Id
    ).order_by(Cotizacion.Fecha_Cotizacion.desc()).limit(10).all()

    return render_template('cotizaciones/index.html',
                           solicitudes_activas=solicitudes_activas,
                           cotizaciones_recientes=cotizaciones_recientes)


@cotizacion_bp.route('/nueva_solicitud', methods=['GET', 'POST'])
def nueva_solicitud():
    """Crear una nueva solicitud de cotización"""
    if request.method == 'POST':
        insumo_id = request.form['insumo']
        cantidad = int(request.form['cantidad'])
        descripcion = request.form.get('descripcion', '')

        # Validar fecha límite si se proporciona
        fecha_limite = None
        fecha_limite_str = request.form.get('fecha_limite', '')
        if fecha_limite_str:
            try:
                fecha_limite = datetime.strptime(fecha_limite_str, '%Y-%m-%d').date()
            except ValueError:
                flash('❌ Formato de fecha inválido', 'danger')
                return redirect(url_for('cotizaciones.nueva_solicitud'))

        # Validar que el insumo exista
        insumo = Insumo.query.get(insumo_id)
        if not insumo:
            flash('❌ El insumo seleccionado no existe', 'danger')
            return redirect(url_for('cotizaciones.nueva_solicitud'))

        # Validar cantidad
        if cantidad <= 0:
            flash('❌ La cantidad debe ser mayor a 0', 'danger')
            return redirect(url_for('cotizaciones.nueva_solicitud'))

        # Crear solicitud
        solicitud = SolicitudCotizacion(
            Id_Insumo=insumo_id,
            Cantidad_Requerida=cantidad,
            Fecha_Limite=fecha_limite,
            Descripcion=descripcion
        )

        db.session.add(solicitud)
        db.session.commit()

        flash('✅ Solicitud de cotización publicada correctamente', 'success')
        return redirect(url_for('cotizaciones.index'))

    # GET: Mostrar formulario
    insumos = Insumo.query.filter_by(Estado='Activo').all()

    # Sugerir fecha límite (7 días a partir de hoy)
    fecha_sugerida = (datetime.now() + timedelta(days=7)).strftime('%Y-%m-%d')

    return render_template('cotizaciones/nueva_solicitud.html',
                           insumos=insumos,
                           fecha_sugerida=fecha_sugerida)


@cotizacion_bp.route('/solicitudes')
def listar_solicitudes():
    """Listar todas las solicitudes de cotización"""
    # Filtros
    estado = request.args.get('estado', 'todas')

    # Consulta base
    query = SolicitudCotizacion.query

    # Aplicar filtros
    if estado != 'todas':
        query = query.filter_by(Estado=estado)

    # Obtener datos
    solicitudes = query.order_by(SolicitudCotizacion.Fecha_Publicacion.desc()).all()

    # Añadir la fecha de hoy para comparaciones en el template
    hoy = date.today()

    return render_template('cotizaciones/solicitudes.html',
                           solicitudes=solicitudes,
                           filtro_estado=estado,
                           hoy=hoy)  # <-- Añadido


@cotizacion_bp.route('/solicitud/<int:id>')
def detalle_solicitud(id):
    """Ver detalle de una solicitud y sus cotizaciones"""
    solicitud = SolicitudCotizacion.query.get_or_404(id)

    # Obtener cotizaciones para esta solicitud
    cotizaciones = db.session.query(Cotizacion, Proveedor).join(
        Proveedor, Cotizacion.Id_Proveedor == Proveedor.Id
    ).filter(
        Cotizacion.Id_Insumo == solicitud.Id_Insumo
    ).order_by(Cotizacion.Precio).all()

    return render_template('cotizaciones/detalle_solicitud.html',
                           solicitud=solicitud,
                           cotizaciones=cotizaciones,
                           now=datetime.now())  # Añadir esta línea


@cotizacion_bp.route('/solicitud/<int:id>/cerrar', methods=['POST'])
def cerrar_solicitud(id):
    """Cerrar una solicitud de cotización"""
    solicitud = SolicitudCotizacion.query.get_or_404(id)

    solicitud.Estado = 'Cerrada'
    db.session.commit()

    flash('✅ Solicitud cerrada correctamente', 'success')
    return redirect(url_for('cotizaciones.detalle_solicitud', id=id))


@cotizacion_bp.route('/cotizaciones')
def listar_cotizaciones():
    # Obtener filtros de la URL
    filtro_insumo = request.args.get('insumo', '')
    filtro_proveedor = request.args.get('proveedor', '')
    filtro_estado = request.args.get('estado', '')

    # Construir la consulta base
    query = Cotizacion.query

    # Aplicar filtros si existen
    if filtro_insumo:
        query = query.join(Insumo).filter(Insumo.Nombre.ilike(f'%{filtro_insumo}%'))

    if filtro_proveedor:
        query = query.join(Proveedor).filter(Proveedor.Nombre.ilike(f'%{filtro_proveedor}%'))

    if filtro_estado:
        query = query.filter(Cotizacion.Estado == filtro_estado)

    # Importante: Cargar explícitamente todas las relaciones necesarias
    query = query.options(
        db.joinedload(Cotizacion.insumo).joinedload(Insumo.tipo_insumo),
        db.joinedload(Cotizacion.proveedor)
    )

    # Obtener resultados
    cotizaciones = query.order_by(Cotizacion.Fecha_Cotizacion.desc()).all()

    return render_template('cotizaciones/cotizaciones.html',
                           cotizaciones=cotizaciones,
                           filtro_insumo=filtro_insumo,
                           filtro_proveedor=filtro_proveedor,
                           filtro_estado=filtro_estado)


@cotizacion_bp.route('/cotizacion/<int:id>/aprobar', methods=['POST'])
def aprobar_cotizacion(id):
    """Aprobar una cotización"""
    cotizacion = Cotizacion.query.get_or_404(id)

    cotizacion.Estado = 'Aprobada'
    db.session.commit()

    flash('✅ Cotización aprobada correctamente', 'success')
    return redirect(url_for('cotizaciones.listar_cotizaciones'))


@cotizacion_bp.route('/cotizacion/<int:id>/rechazar', methods=['POST'])
def rechazar_cotizacion(id):
    """Rechazar una cotización"""
    cotizacion = Cotizacion.query.get_or_404(id)

    cotizacion.Estado = 'Rechazada'
    db.session.commit()

    flash('✅ Cotización rechazada', 'success')
    return redirect(url_for('cotizaciones.listar_cotizaciones'))


@cotizacion_bp.route('/proveedores')
def listar_proveedores():
    """Listar todos los proveedores registrados"""
    # Filtros
    filtro_nombre = request.args.get('nombre', '')
    filtro_estado = request.args.get('estado', '')

    # Consulta base
    query = Proveedor.query

    # Aplicar filtros
    if filtro_nombre:
        query = query.filter(Proveedor.Nombre.ilike(f'%{filtro_nombre}%'))

    if filtro_estado:
        query = query.filter(Proveedor.Estado == filtro_estado)

    # Importante: Cargar las cotizaciones para cada proveedor
    query = query.options(db.joinedload(Proveedor.cotizaciones))

    # Obtener resultados
    proveedores = query.all()

    # Convertir reversed() a lista cuando sea necesario
    for proveedor in proveedores:
        # Si estás usando reversed() en algún lugar, conviértelo a lista
        if hasattr(proveedor, 'cotizaciones_reversed'):
            proveedor.cotizaciones_reversed = list(proveedor.cotizaciones_reversed)

    return render_template('cotizaciones/proveedores.html',
                           proveedores=proveedores,
                           filtro_nombre=filtro_nombre,
                           filtro_estado=filtro_estado)


@cotizacion_bp.route('/reporte')
def reporte():
    """Generar reporte de cotizaciones"""
    # Obtener el periodo seleccionado (por defecto, 30 días)
    periodo = request.args.get('periodo', 30, type=int)

    # Calcular fechas de inicio y fin
    fecha_fin = datetime.now()
    fecha_inicio = fecha_fin - timedelta(days=periodo)

    # Estadísticas generales
    total_cotizaciones = Cotizacion.query.count()
    cotizaciones_aprobadas = Cotizacion.query.filter_by(Estado='Aprobada').count()
    cotizaciones_pendientes = Cotizacion.query.filter_by(Estado='Pendiente').count()
    cotizaciones_rechazadas = Cotizacion.query.filter_by(Estado='Rechazada').count()

    # Proveedores activos
    proveedores_activos = Proveedor.query.filter_by(Estado='Activo').count()

    # Contar insumos diferentes cotizados
    insumos_cotizados = db.session.query(db.func.count(db.distinct(Cotizacion.Id_Insumo))).scalar()

    # Análisis por insumo
    insumos_con_cotizaciones = db.session.query(
        Insumo.Id,
        Insumo.Nombre,
        db.func.count(Cotizacion.Id).label('total_cotizaciones'),
        db.func.min(Cotizacion.Precio).label('precio_minimo'),
        db.func.max(Cotizacion.Precio).label('precio_maximo'),
        db.func.avg(Cotizacion.Precio).label('precio_promedio')
    ).join(
        Cotizacion, Cotizacion.Id_Insumo == Insumo.Id
    ).group_by(Insumo.Id).all()

    # Preparar datos de análisis de precios
    analisis_precios = {}
    for insumo in insumos_con_cotizaciones:
        analisis_precios[insumo.Id] = {
            'nombre': insumo.Nombre,
            'cotizaciones': insumo.total_cotizaciones,
            'min_precio': insumo.precio_minimo,
            'max_precio': insumo.precio_maximo,
            'promedio': insumo.precio_promedio
        }

    # Análisis por proveedor
    proveedores_con_cotizaciones = db.session.query(
        Proveedor.Id,
        Proveedor.Nombre,
        db.func.count(Cotizacion.Id).label('total_cotizaciones'),
        db.func.avg(Cotizacion.Precio).label('precio_promedio')
    ).join(
        Cotizacion, Cotizacion.Id_Proveedor == Proveedor.Id
    ).group_by(Proveedor.Id).order_by(db.func.count(Cotizacion.Id).desc()).limit(5).all()

    # Preparar datos para el top de proveedores
    proveedores_top = []
    for proveedor in proveedores_con_cotizaciones:
        proveedores_top.append({
            'nombre': proveedor.Nombre,
            'cotizaciones': proveedor.total_cotizaciones
        })

    return render_template('cotizaciones/reporte.html',
                           fecha_inicio=fecha_inicio,
                           fecha_fin=fecha_fin,
                           periodo=periodo,
                           total_cotizaciones=total_cotizaciones,
                           cotizaciones_aprobadas=cotizaciones_aprobadas,
                           cotizaciones_pendientes=cotizaciones_pendientes,
                           cotizaciones_rechazadas=cotizaciones_rechazadas,
                           proveedores_activos=proveedores_activos,
                           insumos_cotizados=insumos_cotizados,
                           analisis_precios=analisis_precios,
                           proveedores_top=proveedores_top,
                           insumos_con_cotizaciones=insumos_con_cotizaciones,
                           proveedores_con_cotizaciones=proveedores_con_cotizaciones)

# ========================== Rutas Públicas para Proveedores ==========================

@cotizacion_bp.route('/publico')
def publico_index():
    """Página pública para proveedores"""
    # Obtener solicitudes activas
    solicitudes = SolicitudCotizacion.query.filter_by(Estado='Activa').order_by(
        SolicitudCotizacion.Fecha_Publicacion.desc()).all()

    return render_template('cotizaciones/publico/index.html',
                           solicitudes=solicitudes)


@cotizacion_bp.route('/publico/registro', methods=['GET', 'POST'])
def publico_registro():
    """Registro de proveedores"""
    if request.method == 'POST':
        nombre = request.form['nombre']
        contacto = request.form['contacto']
        email = request.form['email']
        telefono = request.form['telefono']
        direccion = request.form.get('direccion', '')

        # Validar que no exista un proveedor con el mismo email
        proveedor_existente = Proveedor.query.filter_by(Email=email).first()
        if proveedor_existente:
            flash('❌ Ya existe un proveedor registrado con ese email', 'danger')
            return render_template('cotizaciones/publico/registro.html', valores=request.form)

        # Crear nuevo proveedor
        proveedor = Proveedor(
            Nombre=nombre,
            Contacto=contacto,
            Email=email,
            Telefono=telefono,
            Direccion=direccion
        )

        db.session.add(proveedor)
        db.session.commit()

        flash('✅ Registro completado correctamente', 'success')
        return redirect(url_for('cotizaciones.publico_login', email=email))

    # GET: Mostrar formulario
    return render_template('cotizaciones/publico/registro.html')


@cotizacion_bp.route('/publico/login', methods=['GET', 'POST'])
def publico_login():
    """Login de proveedores"""
    if request.method == 'POST':
        email = request.form['email']

        # Buscar proveedor por email
        proveedor = Proveedor.query.filter_by(Email=email).first()
        if not proveedor:
            flash('❌ No existe un proveedor registrado con ese email', 'danger')
            return render_template('cotizaciones/publico/login.html')

        # En un sistema real se verificaría una contraseña
        # Para simplificar, solo verificamos que el proveedor exista

        # Guardar ID del proveedor en la sesión (simulado)
        # En un sistema real se usaría session['proveedor_id'] = proveedor.Id

        return redirect(url_for('cotizaciones.publico_portal', proveedor_id=proveedor.Id))

    # GET: Mostrar formulario
    email = request.args.get('email', '')
    return render_template('cotizaciones/publico/login.html', email=email)


@cotizacion_bp.route('/publico/portal/<int:proveedor_id>')
def publico_portal(proveedor_id):
    """Portal del proveedor"""
    # Verificar que el proveedor exista
    proveedor = Proveedor.query.get_or_404(proveedor_id)

    # Obtener solicitudes activas
    solicitudes = SolicitudCotizacion.query.filter_by(Estado='Activa').order_by(
        SolicitudCotizacion.Fecha_Publicacion.desc()).all()

    # Obtener cotizaciones del proveedor
    cotizaciones = db.session.query(Cotizacion, Insumo).join(
        Insumo, Cotizacion.Id_Insumo == Insumo.Id
    ).filter(
        Cotizacion.Id_Proveedor == proveedor_id
    ).order_by(Cotizacion.Fecha_Cotizacion.desc()).all()

    return render_template('cotizaciones/publico/portal.html',
                           proveedor=proveedor,
                           solicitudes=solicitudes,
                           cotizaciones=cotizaciones)


@cotizacion_bp.route('/publico/cotizar/<int:proveedor_id>/<int:solicitud_id>', methods=['GET', 'POST'])
def publico_cotizar(proveedor_id, solicitud_id):
    """Formulario para que el proveedor cotice un insumo"""
    # Verificar que el proveedor y la solicitud existan
    proveedor = Proveedor.query.get_or_404(proveedor_id)
    solicitud = SolicitudCotizacion.query.get_or_404(solicitud_id)

    # Verificar que la solicitud esté activa
    if solicitud.Estado != 'Activa':
        flash('❌ Esta solicitud ya no está activa', 'danger')
        return redirect(url_for('cotizaciones.publico_portal', proveedor_id=proveedor_id))

    if request.method == 'POST':
        precio = float(request.form['precio'])
        observaciones = request.form.get('observaciones', '')

        # Validar precio
        if precio <= 0:
            flash('❌ El precio debe ser mayor a 0', 'danger')
            return render_template('cotizaciones/publico/cotizar.html',
                                   proveedor=proveedor,
                                   solicitud=solicitud,
                                   valores=request.form)

        # Verificar si ya existe una cotización para este proveedor y este insumo
        cotizacion_existente = Cotizacion.query.filter_by(
            Id_Proveedor=proveedor_id,
            Id_Insumo=solicitud.Id_Insumo
        ).first()

        if cotizacion_existente:
            # Actualizar cotización existente
            cotizacion_existente.Precio = precio
            cotizacion_existente.Observaciones = observaciones
            cotizacion_existente.Fecha_Cotizacion = datetime.now()
            cotizacion_existente.Estado = 'Pendiente'
            db.session.commit()

            flash('✅ Cotización actualizada correctamente', 'success')
        else:
            # Crear nueva cotización
            cotizacion = Cotizacion(
                Id_Proveedor=proveedor_id,
                Id_Insumo=solicitud.Id_Insumo,
                Precio=precio,
                Observaciones=observaciones
            )

            db.session.add(cotizacion)
            db.session.commit()

            flash('✅ Cotización enviada correctamente', 'success')

        return redirect(url_for('cotizaciones.publico_portal', proveedor_id=proveedor_id))

    # GET: Mostrar formulario
    # Verificar si ya existe una cotización
    cotizacion_existente = Cotizacion.query.filter_by(
        Id_Proveedor=proveedor_id,
        Id_Insumo=solicitud.Id_Insumo
    ).first()

    return render_template('cotizaciones/publico/cotizar.html',
                           proveedor=proveedor,
                           solicitud=solicitud,
                           cotizacion=cotizacion_existente)

@cotizacion_bp.route('/cotizacion/<int:id>/detalle')
def detalle_cotizacion(id):
    """Ver detalle de una cotización"""
    cotizacion = Cotizacion.query.get_or_404(id)
    return render_template('cotizaciones/detalle_cotizacion.html', cotizacion=cotizacion)


@cotizacion_bp.route('/proveedor/<int:id>/cambiar_estado', methods=['POST'])
def cambiar_estado_proveedor(id):
    """Cambiar estado de un proveedor (activar/desactivar)"""
    proveedor = Proveedor.query.get_or_404(id)

    # Cambiar el estado del proveedor
    if proveedor.Estado == 'Activo':
        proveedor.Estado = 'Inactivo'
        mensaje = 'Proveedor desactivado correctamente'
    else:
        proveedor.Estado = 'Activo'
        mensaje = 'Proveedor activado correctamente'

    db.session.commit()

    flash(f'✅ {mensaje}', 'success')
    return redirect(url_for('cotizaciones.listar_proveedores'))

@cotizacion_bp.route('/proveedor/<int:id>/detalle')
def detalle_proveedor(id):
    """Ver detalle de un proveedor"""
    proveedor = Proveedor.query.get_or_404(id)
    return render_template('cotizaciones/detalle_proveedor.html', proveedor=proveedor)