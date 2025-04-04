from flask import Blueprint, render_template, request, redirect, url_for, flash
from models import db, Empleado, Servicio, TurnoEmpleado
from datetime import datetime, date, timedelta
from sqlalchemy import desc
from sqlalchemy import func
empleado_bp = Blueprint('empleados', __name__, url_prefix='/empleados')


@empleado_bp.route('/')
def listar():
    """Listar todos los empleados con filtros opcionales"""
    # Obtener parámetros de filtrado
    filtro_nombre = request.args.get('nombre', '')
    filtro_estado = request.args.get('estado', '')

    # Construir consulta base
    query = Empleado.query

    # Aplicar filtros si se proporcionan
    if filtro_nombre:
        query = query.filter(
            (Empleado.Nombre.ilike(f'%{filtro_nombre}%')) |
            (Empleado.Apellidos.ilike(f'%{filtro_nombre}%'))
        )
    if filtro_estado:
        query = query.filter(Empleado.Estado == filtro_estado)

    # Ordenar y ejecutar consulta
    empleados = query.order_by(Empleado.Apellidos, Empleado.Nombre).all()

    return render_template('empleados/listado.html',
                           empleados=empleados,
                           filtro_nombre=filtro_nombre,
                           filtro_estado=filtro_estado)


@empleado_bp.route('/<int:id>')
def detalle(id):
    """Ver detalles de un empleado específico"""
    empleado = Empleado.query.get_or_404(id)

    # Obtener servicios recientes del empleado (últimos 10)
    servicios_recibidos = Servicio.query.filter_by(Id_Empleado_Recibe=id).order_by(
        desc(Servicio.Fecha), desc(Servicio.Hora_Recibe)
    ).limit(10).all()

    servicios_lavados = Servicio.query.filter_by(Id_Empleado_Lava=id).order_by(
        desc(Servicio.Fecha), desc(Servicio.Hora_Recibe)
    ).limit(10).all()

    # Obtener turnos del empleado
    turnos = TurnoEmpleado.query.filter_by(Id_Empleado=id).all()

    return render_template('empleados/detalle.html',
                           empleado=empleado,
                           servicios_recibidos=servicios_recibidos,
                           servicios_lavados=servicios_lavados,
                           turnos=turnos)


@empleado_bp.route('/registrar', methods=['GET', 'POST'])
def registrar():
    """Registrar un nuevo empleado"""
    if request.method == 'POST':
        nombre = request.form['nombre']
        apellidos = request.form['apellidos']
        fecha_nacimiento_str = request.form['fecha_nacimiento']
        estado = request.form.get('estado', 'Activo')

        # Validar fecha de nacimiento
        try:
            fecha_nacimiento = datetime.strptime(fecha_nacimiento_str, '%Y-%m-%d').date()
        except ValueError:
            flash('❌ Formato de fecha inválido', 'danger')
            return render_template('empleados/registro.html', valores=request.form)

        # Validar edad mínima (18 años)
        hoy = date.today()
        edad = hoy.year - fecha_nacimiento.year - (
                    (hoy.month, hoy.day) < (fecha_nacimiento.month, fecha_nacimiento.day))
        if edad < 18:
            flash('❌ El empleado debe ser mayor de edad', 'danger')
            return render_template('empleados/registro.html', valores=request.form)

        # Crear nuevo empleado
        empleado = Empleado(
            Nombre=nombre,
            Apellidos=apellidos,
            Fecha_Nacimiento=fecha_nacimiento,
            Estado=estado
        )

        db.session.add(empleado)
        db.session.commit()

        flash('✅ Empleado registrado correctamente', 'success')
        return redirect(url_for('empleados.detalle', id=empleado.Id))

    # GET: Mostrar formulario
    return render_template('empleados/registro.html')



@empleado_bp.route('/<int:id>/cambiar_estado', methods=['POST'])
def cambiar_estado(id):
    """Cambiar estado de un empleado (activar/desactivar)"""
    empleado = Empleado.query.get_or_404(id)

    # Cambiar estado
    nuevo_estado = "Inactivo" if empleado.Estado == "Activo" else "Activo"
    empleado.Estado = nuevo_estado
    db.session.commit()

    flash(f'✅ Estado cambiado a {nuevo_estado}', 'success')
    return redirect(url_for('empleados.detalle', id=id))


@empleado_bp.route('/reporte')
def reporte():
    """Vista para el reporte de rendimiento de empleados"""
    from datetime import datetime, timedelta, date
    from sqlalchemy import func

    # Obtener período de análisis del request
    periodo = request.args.get('periodo', '30')
    try:
        periodo = int(periodo)
    except ValueError:
        periodo = 30  # valor por defecto

    # Calcular fechas de inicio y fin
    fecha_fin = date.today()
    fecha_inicio = fecha_fin - timedelta(days=periodo)

    # Obtener todos los empleados
    empleados_db = Empleado.query.all()

    # Lista para almacenar los datos procesados de cada empleado
    empleados_data = []

    # Estadísticas generales
    total_servicios = 0
    total_completados = 0
    total_tiempo = 0
    servicios_con_tiempo = 0

    # Procesar cada empleado
    for empleado in empleados_db:
        # Servicios recibidos y lavados en el período
        servicios_recibidos = db.session.query(Servicio).filter(
            Servicio.Id_Empleado_Recibe == empleado.Id,
            Servicio.Fecha.between(fecha_inicio, fecha_fin)
        ).all()

        servicios_lavados = db.session.query(Servicio).filter(
            Servicio.Id_Empleado_Lava == empleado.Id,
            Servicio.Fecha.between(fecha_inicio, fecha_fin)
        ).all()

        # Contar servicios completados
        servicios_completados = len([s for s in servicios_lavados if s.Estado == 'Completado'])

        # Calcular tiempo promedio
        servicios_con_duracion = [s for s in servicios_lavados if s.duracion is not None]
        tiempo_promedio = None
        if servicios_con_duracion:
            tiempo_promedio = sum(s.duracion for s in servicios_con_duracion) / len(servicios_con_duracion)
            total_tiempo += sum(s.duracion for s in servicios_con_duracion)
            servicios_con_tiempo += len(servicios_con_duracion)

        # Calcular ingresos generados
        ingresos_generados = sum(float(s.Precio) for s in servicios_lavados if s.Estado == 'Completado')

        # Agregar datos a la lista
        empleado_data = {
            'Id': empleado.Id,
            'Nombre': empleado.Nombre,
            'Apellidos': empleado.Apellidos,
            'Estado': empleado.Estado,
            'nombre_completo': empleado.nombre_completo,
            'servicios_total': len(servicios_lavados),
            'servicios_completados': servicios_completados,
            'tiempo_promedio': tiempo_promedio,
            'ingresos_generados': ingresos_generados
        }

        # Actualizar estadísticas generales
        total_servicios += len(servicios_lavados)
        total_completados += servicios_completados

        empleados_data.append(empleado_data)

    # Calcular tiempo promedio general
    tiempo_promedio_general = None
    if servicios_con_tiempo > 0:
        tiempo_promedio_general = total_tiempo / servicios_con_tiempo

    # Análisis por día de la semana
    dias_semana = []
    dias_nombres = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo']

    # Obtener todos los servicios en el período
    todos_servicios = db.session.query(Servicio).filter(
        Servicio.Fecha.between(fecha_inicio, fecha_fin)
    ).all()

    # Para cada día de la semana
    for i, dia_nombre in enumerate(dias_nombres):
        # Filtrar manualmente los servicios para este día (lunes=0, domingo=6)
        dia_index = i
        servicios_dia = [
            s for s in todos_servicios
            if s.Fecha.weekday() == dia_index  # weekday() devuelve 0 para lunes, 6 para domingo
        ]

        if servicios_dia:
            # Calcular promedio diario (total servicios / número de ese día en el período)
            # Contar cuántos de ese día hay en el período
            dias_contados = sum(1 for day in range((fecha_fin - fecha_inicio).days + 1)
                                if (fecha_inicio + timedelta(days=day)).weekday() == dia_index)

            # Si hay al menos un día de ese tipo en el período
            if dias_contados > 0:
                promedio = len(servicios_dia) / dias_contados
            else:
                promedio = 0

            # Tiempo promedio para servicios en este día
            servicios_con_duracion = [s for s in servicios_dia if s.duracion is not None]
            tiempo_promedio_dia = None
            if servicios_con_duracion:
                tiempo_promedio_dia = sum(s.duracion for s in servicios_con_duracion) / len(servicios_con_duracion)

            # Ingresos promedio
            ingresos_total = sum(float(s.Precio) for s in servicios_dia if s.Estado == 'Completado')
            ingresos_promedio = ingresos_total / dias_contados if dias_contados > 0 else 0

            dias_semana.append({
                'nombre': dia_nombre,
                'servicios': len(servicios_dia),
                'promedio': promedio,
                'tiempo_promedio': tiempo_promedio_dia,
                'ingresos_promedio': ingresos_promedio
            })

    # Preparar datos para la plantilla
    return render_template('empleados/reporte.html',
                           empleados=empleados_data,
                           total_empleados=len(empleados_db),
                           empleados_activos=len([e for e in empleados_db if e.Estado == 'Activo']),
                           total_servicios=total_servicios,
                           tiempo_promedio=tiempo_promedio_general,
                           fecha_inicio=fecha_inicio,
                           fecha_fin=fecha_fin,
                           periodo=periodo,
                           dias_semana=dias_semana)


@empleado_bp.route('/editar/<int:id>', methods=['GET', 'POST'])
def editar(id):
    """Vista para editar un empleado"""
    from datetime import datetime

    # Obtener el empleado
    empleado = Empleado.query.get_or_404(id)

    if request.method == 'POST':
        # Obtener datos del formulario, eliminando espacios en blanco
        nombre = request.form.get('nombre', '').strip()
        apellidos = request.form.get('apellidos', '').strip()
        fecha_nacimiento_str = request.form.get('fecha_nacimiento', '').strip()
        estado = request.form.get('estado', 'Activo').strip()

        # Validar que los campos no estén vacíos
        if not nombre or not apellidos or not fecha_nacimiento_str:
            flash('❌ Todos los campos son obligatorios', 'danger')
            return render_template('empleados/editar.html', empleado=empleado)

        try:
            # Convertir fecha
            fecha_nacimiento = datetime.strptime(fecha_nacimiento_str, '%Y-%m-%d').date()

            # Actualizar datos del empleado
            empleado.Nombre = nombre
            empleado.Apellidos = apellidos
            empleado.Fecha_Nacimiento = fecha_nacimiento
            empleado.Estado = estado

            # Guardar cambios
            db.session.commit()
            flash('✅ Empleado actualizado correctamente', 'success')
            return redirect(url_for('empleados.detalle', id=empleado.Id))

        except ValueError:
            flash('❌ Formato de fecha inválido. Use YYYY-MM-DD.', 'danger')
        except Exception as e:
            db.session.rollback()  # Revertir cambios en caso de error
            flash(f'❌ Error al actualizar empleado: {str(e)}', 'danger')

    # Si es GET o hubo error, renderizar formulario con datos actuales
    return render_template('empleados/editar.html', empleado=empleado)
