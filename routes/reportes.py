from flask import Blueprint, render_template, request
from models import db, Servicio, Vehiculo, Insumo, Empleado, TipoLavado, InsumoPorServicio
from datetime import datetime, timedelta
from sqlalchemy import func, desc, extract
import calendar

reporte_bp = Blueprint('reportes', __name__, url_prefix='/reportes')


@reporte_bp.route('/')
def index():
    """Página principal de reportes disponibles"""
    return render_template('reportes/index.html')


@reporte_bp.route('/diario')
def diario():
    """Reporte de actividad diaria"""
    # Obtener fecha del parámetro o usar la fecha actual
    fecha_str = request.args.get('fecha', '')
    try:
        if fecha_str:
            fecha = datetime.strptime(fecha_str, '%Y-%m-%d').date()
        else:
            fecha = datetime.now().date()
    except ValueError:
        fecha = datetime.now().date()

    # Obtener servicios del día
    servicios = Servicio.query.filter_by(Fecha=fecha).all()

    # Calcular estadísticas
    stats = {
        'total_servicios': len(servicios),
        'completados': sum(1 for s in servicios if s.Estado == 'Completado'),
        'en_proceso': sum(1 for s in servicios if s.Estado == 'En proceso'),
        'cancelados': sum(1 for s in servicios if s.Estado == 'Cancelado'),
        'ingresos': sum(float(s.Precio) for s in servicios if s.Estado == 'Completado'),
        'tiempo_promedio': calcular_tiempo_promedio(servicios),
    }

    # Distribución por tipo de lavado
    tipos_lavado = {}
    for servicio in servicios:
        tipo_nombre = servicio.tipo_lavado.Nombre if servicio.tipo_lavado else "Desconocido"
        if tipo_nombre not in tipos_lavado:
            tipos_lavado[tipo_nombre] = {'count': 0, 'ingresos': 0}
        tipos_lavado[tipo_nombre]['count'] += 1
        if servicio.Estado == 'Completado':
            tipos_lavado[tipo_nombre]['ingresos'] += float(servicio.Precio)

    # Distribución por tipo de vehículo
    tipos_vehiculo = {}
    for servicio in servicios:
        if servicio.vehiculo:
            tipo = servicio.vehiculo.Tipo_Vehículo
            if tipo not in tipos_vehiculo:
                tipos_vehiculo[tipo] = 0
            tipos_vehiculo[tipo] += 1

    # Rendimiento de empleados
    empleados = {}
    for servicio in servicios:
        if servicio.empleado_lava:
            emp_id = servicio.empleado_lava.Id
            emp_nombre = servicio.empleado_lava.nombre_completo
            if emp_id not in empleados:
                empleados[emp_id] = {
                    'nombre': emp_nombre,
                    'servicios': 0,
                    'completados': 0,
                    'tiempo_total': 0,
                    'tiempo_promedio': 0
                }
            empleados[emp_id]['servicios'] += 1
            if servicio.Estado == 'Completado':
                empleados[emp_id]['completados'] += 1
                if servicio.duracion:
                    empleados[emp_id]['tiempo_total'] += servicio.duracion

    # Calcular tiempo promedio por empleado
    for emp_id, data in empleados.items():
        if data['completados'] > 0:
            data['tiempo_promedio'] = data['tiempo_total'] / data['completados']

    return render_template('reportes/diario.html',
                           fecha=fecha,
                           servicios=servicios,
                           stats=stats,
                           tipos_lavado=tipos_lavado,
                           tipos_vehiculo=tipos_vehiculo,
                           empleados=empleados,
                           timedelta=timedelta)  # Pasar timedelta para usar en la plantilla


@reporte_bp.route('/mensual')
def mensual():
    """Reporte de actividad mensual"""
    # Obtener mes y año del parámetro o usar el actual
    try:
        mes = int(request.args.get('mes', datetime.now().month))
        anio = int(request.args.get('anio', datetime.now().year))
    except ValueError:
        mes = datetime.now().month
        anio = datetime.now().year

    # Calcular primer y último día del mes
    primer_dia = datetime(anio, mes, 1).date()
    ultimo_dia = datetime(anio, mes, calendar.monthrange(anio, mes)[1]).date()

    # Obtener servicios del mes
    servicios = Servicio.query.filter(
        Servicio.Fecha >= primer_dia,
        Servicio.Fecha <= ultimo_dia
    ).all()

    # Calcular estadísticas generales
    stats = {
        'total_servicios': len(servicios),
        'completados': sum(1 for s in servicios if s.Estado == 'Completado'),
        'en_proceso': sum(1 for s in servicios if s.Estado == 'En proceso'),
        'cancelados': sum(1 for s in servicios if s.Estado == 'Cancelado'),
        'ingresos': sum(float(s.Precio) for s in servicios if s.Estado == 'Completado'),
        'tiempo_promedio': calcular_tiempo_promedio(servicios),
    }

    # Distribución por día del mes
    servicios_por_dia = {}
    for dia in range(1, calendar.monthrange(anio, mes)[1] + 1):
        fecha = datetime(anio, mes, dia).date()
        servicios_por_dia[fecha] = {
            'total': 0,
            'ingresos': 0
        }

    for servicio in servicios:
        if servicio.Fecha in servicios_por_dia:
            servicios_por_dia[servicio.Fecha]['total'] += 1
            if servicio.Estado == 'Completado':
                servicios_por_dia[servicio.Fecha]['ingresos'] += float(servicio.Precio)

    # Top tipos de lavado
    tipos_lavado = {}
    for servicio in servicios:
        if servicio.Estado == 'Completado':
            tipo_nombre = servicio.tipo_lavado.Nombre if servicio.tipo_lavado else "Desconocido"
            if tipo_nombre not in tipos_lavado:
                tipos_lavado[tipo_nombre] = {'count': 0, 'ingresos': 0}
            tipos_lavado[tipo_nombre]['count'] += 1
            tipos_lavado[tipo_nombre]['ingresos'] += float(servicio.Precio)

    # Ordenar por ingresos
    tipos_lavado = dict(sorted(tipos_lavado.items(), key=lambda x: x[1]['ingresos'], reverse=True))

    # Top vehículos frecuentes (placas con más servicios)
    vehiculos_frecuentes = {}
    for servicio in servicios:
        if servicio.Placa not in vehiculos_frecuentes:
            vehiculos_frecuentes[servicio.Placa] = {
                'count': 0,
                'info': f"{servicio.vehiculo.Marca} {servicio.vehiculo.Modelo}" if servicio.vehiculo else "N/A"
            }
        vehiculos_frecuentes[servicio.Placa]['count'] += 1

    # Ordenar por frecuencia y tomar top 10
    vehiculos_frecuentes = dict(sorted(
        vehiculos_frecuentes.items(),
        key=lambda x: x[1]['count'],
        reverse=True
    )[:10])

    return render_template('reportes/mensual.html',
                           mes=mes,
                           anio=anio,
                           nombre_mes=calendar.month_name[mes],
                           servicios=servicios,
                           stats=stats,
                           servicios_por_dia=servicios_por_dia,
                           tipos_lavado=tipos_lavado,
                           vehiculos_frecuentes=vehiculos_frecuentes)


@reporte_bp.route('/insumos')
def insumos():
    """Reporte de uso de insumos"""
    # Obtener período del parámetro
    try:
        periodo = int(request.args.get('periodo', 30))  # Días por defecto
    except ValueError:
        periodo = 30

    # Calcular fecha de inicio
    fecha_fin = datetime.now().date()
    fecha_inicio = fecha_fin - timedelta(days=periodo)

    # Obtener servicios del período
    servicios = Servicio.query.filter(
        Servicio.Fecha >= fecha_inicio,
        Servicio.Fecha <= fecha_fin
    ).all()

    # Obtener insumos usados en estos servicios
    insumos_usados = {}
    for servicio in servicios:
        for uso in servicio.insumos_usados:
            if uso.insumo:
                insumo_id = uso.insumo.Id
                if insumo_id not in insumos_usados:
                    insumos_usados[insumo_id] = {
                        'nombre': uso.insumo.Nombre,
                        'cantidad': 0,
                        'costo': 0
                    }
                insumos_usados[insumo_id]['cantidad'] += uso.Cantidad_Utilizada
                insumos_usados[insumo_id]['costo'] += uso.costo_total

    # Ordenar por cantidad usada
    insumos_usados = dict(sorted(
        insumos_usados.items(),
        key=lambda x: x[1]['cantidad'],
        reverse=True
    ))

    # Calcular stock actual e identificar necesidades de reposición
    necesidades_reposicion = []
    for insumo in Insumo.query.all():
        stock_actual = insumo.stock_actual

        # Calcular consumo promedio diario (si hay datos)
        consumo_id = insumo.Id
        if consumo_id in insumos_usados:
            consumo_total = insumos_usados[consumo_id]['cantidad']
            consumo_diario = consumo_total / periodo
            dias_restantes = stock_actual / consumo_diario if consumo_diario > 0 else float('inf')

            if dias_restantes < 15:  # Menos de 15 días de stock
                necesidades_reposicion.append({
                    'id': insumo.Id,
                    'nombre': insumo.Nombre,
                    'stock_actual': stock_actual,
                    'consumo_diario': consumo_diario,
                    'dias_restantes': dias_restantes,
                    'cantidad_recomendada': max(15 - int(dias_restantes), 0) * int(consumo_diario) + 5
                    # Stock para 15 días + margen
                })

    # Ordenar por días restantes (más urgentes primero)
    necesidades_reposicion.sort(key=lambda x: x['dias_restantes'])

    return render_template('reportes/insumos.html',
                           fecha_inicio=fecha_inicio,
                           fecha_fin=fecha_fin,
                           periodo=periodo,
                           insumos_usados=insumos_usados,
                           necesidades_reposicion=necesidades_reposicion)


@reporte_bp.route('/empleados')
def empleados():
    """Reporte de rendimiento de empleados"""
    # Obtener período del parámetro
    try:
        periodo = int(request.args.get('periodo', 30))  # Días por defecto
    except ValueError:
        periodo = 30

    # Calcular fecha de inicio
    fecha_fin = datetime.now().date()
    fecha_inicio = fecha_fin - timedelta(days=periodo)

    # Obtener servicios del período
    servicios = Servicio.query.filter(
        Servicio.Fecha >= fecha_inicio,
        Servicio.Fecha <= fecha_fin
    ).all()

    # Rendimiento de empleados
    empleados_data = {}
    for servicio in servicios:
        if not servicio.empleado_lava:
            continue

        emp_id = servicio.empleado_lava.Id
        emp_nombre = servicio.empleado_lava.nombre_completo

        if emp_id not in empleados_data:
            empleados_data[emp_id] = {
                'id': emp_id,
                'nombre': emp_nombre,
                'servicios_total': 0,
                'servicios_completados': 0,
                'ingresos_generados': 0,
                'tiempo_total': 0,
                'tipos_lavado': {}
            }

        empleados_data[emp_id]['servicios_total'] += 1

        if servicio.Estado == 'Completado':
            empleados_data[emp_id]['servicios_completados'] += 1
            empleados_data[emp_id]['ingresos_generados'] += float(servicio.Precio)

            if servicio.duracion:
                empleados_data[emp_id]['tiempo_total'] += servicio.duracion

            # Contabilizar por tipo de lavado
            tipo_nombre = servicio.tipo_lavado.Nombre if servicio.tipo_lavado else "Desconocido"
            if tipo_nombre not in empleados_data[emp_id]['tipos_lavado']:
                empleados_data[emp_id]['tipos_lavado'][tipo_nombre] = {
                    'count': 0,
                    'tiempo_total': 0
                }
            empleados_data[emp_id]['tipos_lavado'][tipo_nombre]['count'] += 1
            if servicio.duracion:
                empleados_data[emp_id]['tipos_lavado'][tipo_nombre]['tiempo_total'] += servicio.duracion

    # Calcular tiempos promedio
    for emp_id, data in empleados_data.items():
        # Tiempo promedio general
        if data['servicios_completados'] > 0:
            data['tiempo_promedio'] = data['tiempo_total'] / data['servicios_completados']
        else:
            data['tiempo_promedio'] = 0

        # Tiempo promedio por tipo de lavado
        for tipo, tipo_data in data['tipos_lavado'].items():
            if tipo_data['count'] > 0:
                tipo_data['tiempo_promedio'] = tipo_data['tiempo_total'] / tipo_data['count']
            else:
                tipo_data['tiempo_promedio'] = 0

    # Ordenar por cantidad de servicios completados
    empleados_lista = sorted(
        empleados_data.values(),
        key=lambda x: x['servicios_completados'],
        reverse=True
    )

    return render_template('reportes/empleados.html',
                           fecha_inicio=fecha_inicio,
                           fecha_fin=fecha_fin,
                           periodo=periodo,
                           empleados=empleados_lista)


@reporte_bp.route('/vehiculos')
def vehiculos():
    """Reporte de vehículos atendidos"""
    # Obtener período del parámetro
    try:
        periodo = int(request.args.get('periodo', 90))  # Días por defecto (3 meses)
    except ValueError:
        periodo = 90

    # Calcular fecha de inicio
    fecha_fin = datetime.now().date()
    fecha_inicio = fecha_fin - timedelta(days=periodo)

    # Estadísticas por tipo de vehículo
    tipos_vehiculo = db.session.query(
        Vehiculo.Tipo_Vehículo,
        func.count(Servicio.Id).label('total_servicios'),
        func.sum(Servicio.Precio).label('total_ingresos')
    ).join(
        Servicio, Servicio.Id_Tipovehículo == Vehiculo.Id
    ).filter(
        Servicio.Fecha >= fecha_inicio,
        Servicio.Fecha <= fecha_fin,
        Servicio.Estado == 'Completado'
    ).group_by(
        Vehiculo.Tipo_Vehículo
    ).all()

    # Vehículos frecuentes (más de 3 visitas en el período)
    vehiculos_frecuentes = db.session.query(
        Servicio.Placa,
        func.count(Servicio.Id).label('visitas'),
        func.sum(Servicio.Precio).label('total_gastado')
    ).filter(
        Servicio.Fecha >= fecha_inicio,
        Servicio.Fecha <= fecha_fin
    ).group_by(
        Servicio.Placa
    ).having(
        func.count(Servicio.Id) >= 3
    ).order_by(
        desc('visitas')
    ).all()

    # Obtener info adicional de los vehículos frecuentes
    vehiculos_detalle = []
    for v in vehiculos_frecuentes:
        vehiculo = Vehiculo.query.filter_by(Placa=v.Placa).first()
        if vehiculo:
            vehiculos_detalle.append({
                'placa': v.Placa,
                'visitas': v.visitas,
                'total_gastado': v.total_gastado,
                'marca': vehiculo.Marca,
                'modelo': vehiculo.Modelo,
                'tipo': vehiculo.Tipo_Vehículo,
                'color': vehiculo.Color
            })

    return render_template('reportes/vehiculos.html',
                           fecha_inicio=fecha_inicio,
                           fecha_fin=fecha_fin,
                           periodo=periodo,
                           tipos_vehiculo=tipos_vehiculo,
                           vehiculos_frecuentes=vehiculos_detalle)


# Función auxiliar para calcular tiempo promedio
def calcular_tiempo_promedio(servicios):
    """Calcula el tiempo promedio de servicios completados en minutos"""
    servicios_completados = [s for s in servicios if s.Estado == 'Completado' and s.duracion]
    if not servicios_completados:
        return 0
    return sum(s.duracion for s in servicios_completados) / len(servicios_completados)