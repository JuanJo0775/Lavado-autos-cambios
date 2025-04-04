from flask import Blueprint, render_template, request, redirect, url_for, flash
from models import db, Inventario, Insumo
from sqlalchemy import desc
from datetime import datetime

inventario_bp = Blueprint('inventario', __name__, url_prefix='/inventario')


@inventario_bp.route('/')
def listar():
    """Listar todos los items de inventario"""
    # Obtener parámetros de filtrado
    filtro_insumo = request.args.get('insumo', '')

    # Construir consulta base
    query = Inventario.query.join(Inventario.insumo)

    # Aplicar filtros si se proporcionan
    if filtro_insumo:
        query = query.filter(Insumo.Nombre.ilike(f'%{filtro_insumo}%'))

    # Ordenar y ejecutar consulta
    inventario = query.order_by(Insumo.Nombre).all()

    # Calcular valor total del inventario
    valor_total = sum(item.valor_total for item in inventario)

    return render_template('inventario/listado.html',
                           inventario=inventario,
                           valor_total=valor_total,
                           filtro_insumo=filtro_insumo)


@inventario_bp.route('/registrar', methods=['GET', 'POST'])
def registrar():
    """Registrar un nuevo item de inventario o aumentar el stock"""
    if request.method == 'POST':
        insumo_id = request.form['insumo']
        stock = int(request.form['stock'])
        estado = int(request.form['estado'])
        # Campos adicionales que podrían ser útiles (opcional)
        proveedor = request.form.get('proveedor', '')
        factura = request.form.get('factura', '')
        observaciones = request.form.get('observaciones', '')

        # Verificar que el insumo exista
        insumo = Insumo.query.get(insumo_id)
        if not insumo:
            flash('❌ El insumo seleccionado no existe', 'danger')
            return render_template('inventario/registro.html',
                                   insumos=Insumo.query.all(),  # Obtener todos sin filtrar
                                   valores=request.form)

        # Verificar que el stock sea positivo
        if stock <= 0:
            flash('❌ La cantidad debe ser mayor a 0', 'danger')
            return render_template('inventario/registro.html',
                                   insumos=Insumo.query.all(),  # Obtener todos sin filtrar
                                   valores=request.form)

        # Buscar si ya existe un registro para este insumo
        item_existente = Inventario.query.filter_by(Id_insumo=insumo_id).first()

        if item_existente:
            # Aumentar stock del existente
            item_existente.Stock += stock
            flash('✅ Stock actualizado correctamente', 'success')
        else:
            # Crear nuevo registro
            item = Inventario(
                Id_insumo=insumo_id,
                Stock=stock,
                Estado=estado
            )
            db.session.add(item)
            flash('✅ Item de inventario registrado correctamente', 'success')

        db.session.commit()
        return redirect(url_for('inventario.listar'))

    # Mostrar formulario (GET)
    # Obtener todos los insumos sin filtrar por estado para evitar problemas
    insumos = Insumo.query.all()

    # Verificar si hay insumos disponibles
    print(f"Número de insumos recuperados: {len(insumos)}")
    for ins in insumos[:3]:  # Mostrar los primeros 3 como ejemplo
        print(f"Insumo: ID={ins.Id}, Nombre={ins.Nombre}, Estado={ins.Estado}")

    # Si se proporciona un ID de insumo en la URL
    insumo_id = request.args.get('insumo')
    if insumo_id:
        insumo_seleccionado = Insumo.query.get(insumo_id)
        if insumo_seleccionado:
            flash(f'Preparado para agregar stock de: {insumo_seleccionado.Nombre}', 'info')

    return render_template('inventario/registro.html', insumos=insumos)

@inventario_bp.route('/<int:id>/ajustar', methods=['GET', 'POST'])
def ajustar(id):
    """Ajustar la cantidad de un item de inventario"""
    item = Inventario.query.get_or_404(id)

    if request.method == 'POST':
        nuevo_stock = int(request.form['stock'])
        motivo = request.form['motivo']
        observaciones = request.form.get('observaciones', '')

        # Para motivos personalizados
        if motivo == 'otro':
            motivo_detalle = request.form.get('motivoOtro', '')
            if motivo_detalle:
                motivo = f"Otro: {motivo_detalle}"

        # Registrar el ajuste (en un sistema real se guardaría un registro de este ajuste)
        stock_anterior = item.Stock
        item.Stock = nuevo_stock

        # Actualizar estado si es necesario
        if nuevo_stock == 0:
            item.Estado = 0  # Agotado
        else:
            item.Estado = 1  # Disponible

        db.session.commit()

        diferencia = nuevo_stock - stock_anterior
        flash(f'✅ Stock ajustado: {stock_anterior} → {nuevo_stock} (Diferencia: {diferencia})', 'success')

        return redirect(url_for('inventario.listar'))

    return render_template('inventario/ajustar.html', item=item)


@inventario_bp.route('/reporte')
def reporte():
    """Generar un reporte del inventario"""
    # Calcular estadísticas
    inventario = Inventario.query.all()

    total_items = len(inventario)
    valor_total = sum(item.valor_total for item in inventario)
    items_agotados = sum(1 for item in inventario if item.Stock == 0)
    items_criticos = sum(1 for item in inventario if 0 < item.Stock < 10)

    # Calcular valor por tipo de insumo
    valor_por_tipo = {}
    for item in inventario:
        tipo_nombre = item.insumo.tipo_insumo.Nombre
        if tipo_nombre not in valor_por_tipo:
            valor_por_tipo[tipo_nombre] = 0
        valor_por_tipo[tipo_nombre] += item.valor_total

    # Ordenar los tipos por valor
    valor_por_tipo = dict(sorted(valor_por_tipo.items(), key=lambda x: x[1], reverse=True))

    # Fecha y hora actual para el reporte
    now = datetime.now()

    return render_template('inventario/reporte.html',
                           inventario=inventario,
                           total_items=total_items,
                           valor_total=valor_total,
                           items_agotados=items_agotados,
                           items_criticos=items_criticos,
                           valor_por_tipo=valor_por_tipo,
                           now=now)