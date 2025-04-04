from flask import Blueprint, render_template
from models import Servicio, Vehiculo, Insumo, Empleado
from datetime import datetime, timedelta
from sqlalchemy import func

dashboard_bp = Blueprint('dashboard', __name__)


@dashboard_bp.route('/')
def index():
    """Página principal del dashboard"""
    # Fecha actual
    hoy = datetime.now().date()

    # Estadísticas para el dashboard
    stats = {
        # Servicios
        'servicios_hoy': Servicio.query.filter_by(Fecha=hoy).count(),
        'servicios_pendientes': Servicio.query.filter_by(Estado='En proceso').count(),
        'servicios_completados': Servicio.query.filter_by(Estado='Completado', Fecha=hoy).count(),
        'ingresos_hoy': sum(float(s.Precio) for s in Servicio.query.filter_by(Fecha=hoy, Estado='Completado').all()),

        # Vehículos
        'total_vehiculos': Vehiculo.query.count(),
        'vehiculos_activos': Vehiculo.query.filter_by(Estado='Activo').count(),

        # Inventario
        'insumos_criticos': sum(1 for i in Insumo.query.all() if i.stock_actual < 10),
        'valor_inventario': sum(i.valor_inventario for i in Insumo.query.all()),
    }

    # Servicios en proceso para mostrar en el dashboard
    servicios_en_proceso = Servicio.query.filter_by(Estado='En proceso').order_by(Servicio.Fecha,
                                                                                  Servicio.Hora_Recibe).limit(5).all()

    # Servicios recientes
    servicios_recientes = Servicio.query.order_by(Servicio.Id.desc()).limit(5).all()

    # Insumos con stock crítico
    insumos_criticos = [i for i in Insumo.query.all() if i.stock_actual < 10]

    # Datos para gráficos (últimos 7 días)
    fecha_inicio = hoy - timedelta(days=6)

    # Preparar fechas para la consulta
    fechas = []
    for i in range(7):
        fechas.append(fecha_inicio + timedelta(days=i))

    # Preparar datos para gráfico de servicios por día
    servicios_por_dia = []
    for fecha in fechas:
        servicios = Servicio.query.filter_by(Fecha=fecha).count()
        servicios_por_dia.append({
            'fecha': fecha.strftime('%d/%m'),
            'servicios': servicios
        })

    # Empleados con más servicios hoy
    empleados_servicio = {}
    for servicio in Servicio.query.filter_by(Fecha=hoy).all():
        empleado = servicio.empleado_lava
        if empleado.Id not in empleados_servicio:
            empleados_servicio[empleado.Id] = {
                'nombre': empleado.nombre_completo,
                'servicios': 0
            }
        empleados_servicio[empleado.Id]['servicios'] += 1

    # Ordenar por cantidad de servicios
    top_empleados = sorted(
        empleados_servicio.values(),
        key=lambda x: x['servicios'],
        reverse=True
    )[:5]

    return render_template('dashboard.html',
                           stats=stats,
                           servicios_en_proceso=servicios_en_proceso,
                           servicios_recientes=servicios_recientes,
                           insumos_criticos=insumos_criticos,
                           servicios_por_dia=servicios_por_dia,
                           top_empleados=top_empleados)