from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from models import db, TipoLavado, Insumo, InsumoPorTipoLavado
from sqlalchemy import desc

tipo_lavado_bp = Blueprint('tipo_lavado', __name__, url_prefix='/tipo_lavado')


@tipo_lavado_bp.route('/')
def listar():
    """Listar todos los tipos de lavado con filtros opcionales"""
    # Obtener parámetros de filtrado
    filtro_nombre = request.args.get('nombre', '')
    filtro_estado = request.args.get('estado', '')

    # Construir consulta base
    query = TipoLavado.query

    # Aplicar filtros si se proporcionan
    if filtro_nombre:
        query = query.filter(TipoLavado.Nombre.ilike(f'%{filtro_nombre}%'))
    if filtro_estado:
        query = query.filter(TipoLavado.Estado == filtro_estado)

    # Ordenar y ejecutar consulta
    tipos_lavado = query.order_by(TipoLavado.Nombre).all()

    return render_template('tipo_lavado/listado.html',
                           tipos_lavado=tipos_lavado,
                           filtro_nombre=filtro_nombre,
                           filtro_estado=filtro_estado)


@tipo_lavado_bp.route('/<int:id>')
def detalle(id):
    """Ver detalles de un tipo de lavado específico"""
    tipo_lavado = TipoLavado.query.get_or_404(id)

    # Obtener insumos requeridos para este tipo de lavado
    insumos_requeridos = InsumoPorTipoLavado.query.filter_by(Id_TipoLavado=id).all()

    # Obtener todos los insumos para posible adición
    insumos_disponibles = Insumo.query.filter_by(Estado='Activo').all()

    return render_template('tipo_lavado/detalle.html',
                           tipo_lavado=tipo_lavado,
                           insumos_requeridos=insumos_requeridos,
                           insumos_disponibles=insumos_disponibles)


@tipo_lavado_bp.route('/crear', methods=['GET', 'POST'])
def crear():
    """Crear un nuevo tipo de lavado"""
    if request.method == 'POST':
        nombre = request.form['nombre']
        precio = request.form['precio']
        estado = request.form.get('estado', 'activo')
        insumo_principal_id = request.form.get('insumo_principal')

        # Validar datos básicos
        try:
            precio_float = float(precio)
            if precio_float <= 0:
                flash('❌ El precio debe ser mayor a 0', 'danger')
                return redirect(url_for('tipo_lavado.crear'))
        except ValueError:
            flash('❌ El precio debe ser un número válido', 'danger')
            return redirect(url_for('tipo_lavado.crear'))

        # Verificar que el nombre no esté duplicado
        tipo_existente = TipoLavado.query.filter(TipoLavado.Nombre.ilike(nombre)).first()
        if tipo_existente:
            flash('❌ Ya existe un tipo de lavado con ese nombre', 'danger')
            return redirect(url_for('tipo_lavado.crear'))

        # Crear nuevo tipo de lavado
        nuevo_tipo = TipoLavado(
            Nombre=nombre,
            Precio=precio,
            Estado=estado,
            Id_Insumo=insumo_principal_id if insumo_principal_id else None
        )

        db.session.add(nuevo_tipo)
        db.session.commit()

        # Procesar insumos requeridos (si hay)
        # Formato esperado: insumos[]=1&cantidades[]=2&insumos[]=3&cantidades[]=1
        insumos_ids = request.form.getlist('insumos[]')
        cantidades = request.form.getlist('cantidades[]')

        # Validar que las listas tengan la misma longitud
        if len(insumos_ids) == len(cantidades) and insumos_ids:
            for i in range(len(insumos_ids)):
                try:
                    insumo_id = int(insumos_ids[i])
                    cantidad = int(cantidades[i])

                    # Verificar que la cantidad sea positiva
                    if cantidad <= 0:
                        continue

                    # Verificar que el insumo exista
                    insumo = Insumo.query.get(insumo_id)
                    if not insumo:
                        continue

                    # Crear relación
                    insumo_requerido = InsumoPorTipoLavado(
                        Id_TipoLavado=nuevo_tipo.Id,
                        Id_Insumo=insumo_id,
                        Cantidad_Requerida=cantidad
                    )
                    db.session.add(insumo_requerido)
                except ValueError:
                    continue

            db.session.commit()

        flash('✅ Tipo de lavado creado correctamente', 'success')
        return redirect(url_for('tipo_lavado.detalle', id=nuevo_tipo.Id))

    # GET: Mostrar formulario
    insumos = Insumo.query.filter_by(Estado='Activo').all()
    return render_template('tipo_lavado/crear.html', insumos=insumos)


@tipo_lavado_bp.route('/<int:id>/editar', methods=['GET', 'POST'])
def editar(id):
    """Editar un tipo de lavado existente"""
    tipo_lavado = TipoLavado.query.get_or_404(id)

    if request.method == 'POST':
        tipo_lavado.Nombre = request.form['nombre']
        tipo_lavado.Precio = request.form['precio']
        tipo_lavado.Estado = request.form['estado']

        insumo_principal_id = request.form.get('insumo_principal')
        tipo_lavado.Id_Insumo = insumo_principal_id if insumo_principal_id else None

        db.session.commit()
        flash('✅ Tipo de lavado actualizado correctamente', 'success')
        return redirect(url_for('tipo_lavado.detalle', id=tipo_lavado.Id))

    # GET: Mostrar formulario
    insumos = Insumo.query.filter_by(Estado='Activo').all()
    return render_template('tipo_lavado/editar.html',
                           tipo_lavado=tipo_lavado,
                           insumos=insumos)


@tipo_lavado_bp.route('/<int:id>/eliminar', methods=['POST'])
def eliminar(id):
    """Eliminar un tipo de lavado"""
    tipo_lavado = TipoLavado.query.get_or_404(id)

    try:
        # Verificar si hay servicios asociados
        if tipo_lavado.servicios:
            flash('❌ No se puede eliminar el tipo de lavado porque tiene servicios asociados', 'danger')
            return redirect(url_for('tipo_lavado.detalle', id=id))

        nombre = tipo_lavado.Nombre

        # Eliminar insumos requeridos asociados
        InsumoPorTipoLavado.query.filter_by(Id_TipoLavado=id).delete()

        # Eliminar el tipo de lavado
        db.session.delete(tipo_lavado)
        db.session.commit()

        flash(f'✅ Tipo de lavado "{nombre}" eliminado correctamente', 'success')
        return redirect(url_for('tipo_lavado.listar'))
    except Exception as e:
        db.session.rollback()
        flash(f'❌ Error al eliminar el tipo de lavado: {str(e)}', 'danger')
        return redirect(url_for('tipo_lavado.detalle', id=id))


@tipo_lavado_bp.route('/<int:id>/insumos')
def insumos(id):
    """Gestionar insumos requeridos para un tipo de lavado"""
    tipo_lavado = TipoLavado.query.get_or_404(id)
    insumos_requeridos = InsumoPorTipoLavado.query.filter_by(Id_TipoLavado=id).all()
    insumos_disponibles = Insumo.query.filter_by(Estado='Activo').all()

    return render_template('tipo_lavado/insumos.html',
                           tipo_lavado=tipo_lavado,
                           insumos_requeridos=insumos_requeridos,
                           insumos_disponibles=insumos_disponibles)


@tipo_lavado_bp.route('/<int:id>/agregar_insumo', methods=['POST'])
def agregar_insumo(id):
    """Agregar un insumo requerido para un tipo de lavado"""
    tipo_lavado = TipoLavado.query.get_or_404(id)

    insumo_id = int(request.form['insumo_id'])
    cantidad = int(request.form['cantidad'])

    # Validar datos
    if cantidad <= 0:
        flash('❌ La cantidad debe ser mayor a 0', 'danger')
        return redirect(url_for('tipo_lavado.insumos', id=id))

    # Verificar que el insumo exista
    insumo = Insumo.query.get_or_404(insumo_id)

    # Verificar si ya existe este insumo para este tipo de lavado
    insumo_existente = InsumoPorTipoLavado.query.filter_by(
        Id_TipoLavado=id,
        Id_Insumo=insumo_id
    ).first()

    if insumo_existente:
        # Actualizar cantidad
        insumo_existente.Cantidad_Requerida = cantidad
        mensaje = f'✅ Cantidad actualizada para el insumo "{insumo.Nombre}"'
    else:
        # Crear nuevo registro
        insumo_requerido = InsumoPorTipoLavado(
            Id_TipoLavado=id,
            Id_Insumo=insumo_id,
            Cantidad_Requerida=cantidad
        )
        db.session.add(insumo_requerido)
        mensaje = f'✅ Insumo "{insumo.Nombre}" agregado correctamente'

    db.session.commit()
    flash(mensaje, 'success')
    return redirect(url_for('tipo_lavado.insumos', id=id))


@tipo_lavado_bp.route('/<int:tipo_id>/eliminar_insumo/<int:insumo_id>', methods=['POST'])
def eliminar_insumo(tipo_id, insumo_id):
    """Eliminar un insumo requerido de un tipo de lavado"""
    insumo_requerido = InsumoPorTipoLavado.query.filter_by(
        Id_TipoLavado=tipo_id,
        Id_Insumo=insumo_id
    ).first_or_404()

    insumo_nombre = insumo_requerido.insumo.Nombre if insumo_requerido.insumo else "Desconocido"

    db.session.delete(insumo_requerido)
    db.session.commit()

    flash(f'✅ Insumo "{insumo_nombre}" eliminado del tipo de lavado', 'success')
    return redirect(url_for('tipo_lavado.insumos', id=tipo_id))


@tipo_lavado_bp.route('/api/verificar_stock/<int:id>')
def api_verificar_stock(id):
    """API para verificar si hay suficiente stock para un tipo de lavado"""
    tipo_lavado = TipoLavado.query.get_or_404(id)

    tiene_stock = tipo_lavado.tiene_suficiente_stock()
    insumos_faltantes = []

    if not tiene_stock:
        # Obtener insumos sin stock suficiente
        for insumo_req in tipo_lavado.insumos_requeridos:
            insumo = insumo_req.insumo
            if insumo.stock_actual < insumo_req.Cantidad_Requerida:
                insumos_faltantes.append({
                    'nombre': insumo.Nombre,
                    'stock_actual': insumo.stock_actual,
                    'requerido': insumo_req.Cantidad_Requerida
                })

    return jsonify({
        'tiene_stock_suficiente': tiene_stock,
        'insumos_faltantes': insumos_faltantes
    })