from flask import Blueprint, render_template, request, redirect, url_for, flash, abort
from models import db, Servicio, Evaluacion
from sqlalchemy import desc

evaluacion_bp = Blueprint('evaluaciones', __name__, url_prefix='/evaluaciones')


@evaluacion_bp.route('/')
def listar():
    """Listar todas las evaluaciones de servicio"""
    evaluaciones = db.session.query(Evaluacion, Servicio).join(
        Servicio, Evaluacion.Id_Servicio == Servicio.Id
    ).order_by(desc(Evaluacion.Fecha_Evaluacion)).all()

    return render_template('evaluaciones/listado.html', evaluaciones=evaluaciones)


@evaluacion_bp.route('/reporte')
def reporte():
    """Generar reporte de evaluaciones"""
    from sqlalchemy import desc, func

    try:
        # Total de evaluaciones
        total_evaluaciones = Evaluacion.query.count()

        # Obtener promedios en una sola consulta
        promedios = db.session.query(
            func.avg(Evaluacion.Tiempo_Espera),
            func.avg(Evaluacion.Amabilidad),
            func.avg(Evaluacion.Calidad_Servicio)
        ).first()

        tiempo_promedio = promedios[0] or 0
        amabilidad_promedio = promedios[1] or 0
        calidad_promedio = promedios[2] or 0

        # Promedio general
        promedio_general = (
            (tiempo_promedio + amabilidad_promedio + calidad_promedio) / 3
            if total_evaluaciones > 0 else 0
        )

        # Últimas 10 evaluaciones con outerjoin para asegurar que no se pierdan registros
        ultimas_evaluaciones = db.session.query(Evaluacion, Servicio).outerjoin(
            Servicio, Evaluacion.Id_Servicio == Servicio.Id
        ).order_by(desc(Evaluacion.Fecha_Evaluacion)).limit(10).all()

        return render_template(
            'evaluaciones/reporte.html',
            total_evaluaciones=total_evaluaciones,
            tiempo_promedio=tiempo_promedio,
            amabilidad_promedio=amabilidad_promedio,
            calidad_promedio=calidad_promedio,
            promedio_general=promedio_general,
            ultimas_evaluaciones=ultimas_evaluaciones
        )

    except Exception as e:
        db.session.rollback()
        flash(f'❌ Error al generar el reporte: {str(e)}', 'danger')
        return redirect(url_for('inicio'))  # O ajusta a donde quieras redirigir en caso de error


@evaluacion_bp.route('/evaluar/<token>')
def evaluar(token):
    """Página pública para que el cliente evalúe el servicio"""
    # En una implementación real, el token sería un hash único
    # Para esta demo, usamos el ID del servicio directamente
    try:
        servicio_id = int(token)
        servicio = Servicio.query.get_or_404(servicio_id)

        # Verificar que el servicio esté completado
        if servicio.Estado != 'Completado':
            abort(400, description="Solo se pueden evaluar servicios completados")

        # Verificar que no haya sido evaluado ya
        evaluacion_existente = Evaluacion.query.filter_by(Id_Servicio=servicio_id).first()
        if evaluacion_existente:
            return render_template('evaluaciones/ya_evaluado.html', servicio=servicio)

        return render_template('evaluaciones/formulario.html', servicio=servicio, token=token)
    except (ValueError, TypeError):
        abort(404)


@evaluacion_bp.route('/guardar', methods=['POST'])
def guardar():
    """Guardar la evaluación del cliente"""
    if request.method == 'POST':
        token = request.form['token']
        try:
            servicio_id = int(token)
            servicio = Servicio.query.get_or_404(servicio_id)

            # Verificar que el servicio exista y esté completado
            if not servicio or servicio.Estado != 'Completado':
                abort(400)

            # Verificar que no haya sido evaluado ya
            evaluacion_existente = Evaluacion.query.filter_by(Id_Servicio=servicio_id).first()
            if evaluacion_existente:
                return render_template('evaluaciones/ya_evaluado.html', servicio=servicio)

            # Obtener las calificaciones
            tiempo_espera = int(request.form['tiempo_espera'])
            amabilidad = int(request.form['amabilidad'])
            calidad_servicio = int(request.form['calidad_servicio'])
            comentario = request.form.get('comentario', '')

            # Validar calificaciones (1-5)
            if not all(1 <= c <= 5 for c in [tiempo_espera, amabilidad, calidad_servicio]):
                abort(400, description="Las calificaciones deben estar entre 1 y 5")

            # Crear y guardar evaluación
            evaluacion = Evaluacion(
                Id_Servicio=servicio_id,
                Tiempo_Espera=tiempo_espera,
                Amabilidad=amabilidad,
                Calidad_Servicio=calidad_servicio,
                Comentario=comentario
            )

            db.session.add(evaluacion)
            db.session.commit()

            return render_template('evaluaciones/gracias.html')

        except (ValueError, TypeError):
            abort(400)

    return redirect(url_for('evaluaciones.listar'))


@evaluacion_bp.route('/generar_enlace/<int:servicio_id>', methods=['POST'])
def generar_enlace(servicio_id):
    """Genera un enlace para enviar al cliente"""
    servicio = Servicio.query.get_or_404(servicio_id)

    # Verificar que el servicio esté completado
    if servicio.Estado != 'Completado':
        flash('❌ Solo se pueden evaluar servicios completados', 'danger')
        return redirect(url_for('servicios.detalle', id=servicio_id))

    # Verificar que no haya sido evaluado ya
    evaluacion_existente = Evaluacion.query.filter_by(Id_Servicio=servicio_id).first()
    if evaluacion_existente:
        flash('❌ Este servicio ya ha sido evaluado', 'warning')
        return redirect(url_for('servicios.detalle', id=servicio_id))

    # En una implementación real, generaríamos un token único
    # Para esta demo, usamos el ID del servicio directamente
    token = str(servicio_id)

    # URL completa para compartir con el cliente
    enlace = request.host_url.rstrip('/') + url_for('evaluaciones.evaluar', token=token)

    return render_template('evaluaciones/enlace_generado.html',
                           servicio=servicio,
                           enlace=enlace)