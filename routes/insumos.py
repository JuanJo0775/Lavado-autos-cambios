from flask import Blueprint, render_template, request, redirect, url_for, flash
from models import db, Insumo, TipoInsumo, InsumoPorServicio
from sqlalchemy import desc

insumo_bp = Blueprint('insumos', __name__, url_prefix='/insumos')


@insumo_bp.route('/')
def listar():
    """Listar todos los insumos con filtros opcionales"""
    # Obtener parámetros de filtrado
    filtro_nombre = request.args.get('nombre', '')
    filtro_tipo = request.args.get('tipo', '')

    # Construir consulta base
    query = Insumo.query

    # Aplicar filtros si se proporcionan
    if filtro_nombre:
        query = query.filter(Insumo.Nombre.ilike(f'%{filtro_nombre}%'))
    if filtro_tipo and filtro_tipo.isdigit():
        tipo_id = int(filtro_tipo)
        query = query.filter(Insumo.Id_TipoInsumo == tipo_id)

    # Ordenar y ejecutar consulta
    insumos = query.order_by(Insumo.Nombre).all()

    # Obtener tipos de insumo para el select
    tipos_insumo = TipoInsumo.query.all()

    return render_template('insumos/listado.html',
                           insumos=insumos,
                           tipos_insumo=tipos_insumo,
                           filtro_nombre=filtro_nombre,
                           filtro_tipo=filtro_tipo)


@insumo_bp.route('/<int:id>')
def detalle(id):
    """Ver detalles de un insumo específico"""
    insumo = Insumo.query.get_or_404(id)

    # Obtener usos del insumo
    insumo_usos = InsumoPorServicio.query.filter_by(Id_Insumo=id).all()

    return render_template('insumos/detalle.html', insumo=insumo, insumo_usos=insumo_usos)


@insumo_bp.route('/registrar', methods=['GET', 'POST'])
def registrar():
    """Registrar un nuevo insumo"""
    if request.method == 'POST':
        nombre = request.form['nombre']
        precio = request.form['precio']
        tipo_id = request.form['tipo']
        estado = request.form['estado']

        # Verificar que el tipo de insumo exista
        tipo_insumo = TipoInsumo.query.get(tipo_id)
        if not tipo_insumo:
            flash('❌ El tipo de insumo seleccionado no existe', 'danger')
            return render_template('insumos/registro.html',
                                   tipos_insumo=TipoInsumo.query.all(),
                                   valores=request.form)

        # Verificar que el nombre no esté duplicado
        insumo_existente = Insumo.query.filter(Insumo.Nombre.ilike(nombre)).first()
        if insumo_existente:
            flash('❌ Ya existe un insumo con ese nombre', 'danger')
            return render_template('insumos/registro.html',
                                   tipos_insumo=TipoInsumo.query.all(),
                                   valores=request.form)

        # Verificar que el precio sea positivo
        try:
            precio_float = float(precio)
            if precio_float <= 0:
                flash('❌ El precio debe ser mayor a 0', 'danger')
                return render_template('insumos/registro.html',
                                       tipos_insumo=TipoInsumo.query.all(),
                                       valores=request.form)
        except ValueError:
            flash('❌ El precio debe ser un número válido', 'danger')
            return render_template('insumos/registro.html',
                                   tipos_insumo=TipoInsumo.query.all(),
                                   valores=request.form)

        # Crear nuevo insumo
        insumo = Insumo(
            Nombre=nombre,
            Precio_Unitario=precio,
            Id_TipoInsumo=tipo_id,
            Estado=estado
        )

        db.session.add(insumo)
        db.session.commit()

        flash('✅ Insumo registrado correctamente', 'success')
        return redirect(url_for('insumos.detalle', id=insumo.Id))

    # Mostrar formulario (GET)
    tipos_insumo = TipoInsumo.query.all()
    return render_template('insumos/registro.html', tipos_insumo=tipos_insumo)


@insumo_bp.route('/<int:id>/editar', methods=['GET', 'POST'])
def editar(id):
    """Editar un insumo existente"""
    insumo = Insumo.query.get_or_404(id)

    if request.method == 'POST':
        insumo.Nombre = request.form['nombre']
        insumo.Precio_Unitario = request.form['precio']
        insumo.Id_TipoInsumo = request.form['tipo']
        insumo.Estado = request.form['estado']

        db.session.commit()
        flash('✅ Insumo actualizado correctamente', 'success')
        return redirect(url_for('insumos.detalle', id=insumo.Id))

    # Mostrar formulario (GET)
    tipos_insumo = TipoInsumo.query.all()
    return render_template('insumos/editar.html',
                           insumo=insumo,
                           tipos_insumo=tipos_insumo)


@insumo_bp.route('/<int:id>/cambiar_estado', methods=['POST'])
def cambiar_estado(id):
    """Cambia el estado de un insumo (activo/inactivo)"""
    insumo = Insumo.query.get_or_404(id)

    nuevo_estado = "Inactivo" if insumo.Estado == "Activo" else "Activo"
    insumo.Estado = nuevo_estado
    db.session.commit()

    flash(f'✅ Estado cambiado a {nuevo_estado}', 'success')
    return redirect(url_for('insumos.detalle', id=id))


@insumo_bp.route('/tipos')
def listar_tipos():
    """Listar todos los tipos de insumo"""
    tipos = TipoInsumo.query.all()
    return render_template('insumos/tipos.html', tipos=tipos)


@insumo_bp.route('/tipos/crear', methods=['GET', 'POST'])
def crear_tipo():
    """Crear un nuevo tipo de insumo"""
    if request.method == 'POST':
        nombre = request.form['nombre']
        descripcion = request.form['descripcion']

        # Verificar que el nombre no esté duplicado
        tipo_existente = TipoInsumo.query.filter(TipoInsumo.Nombre.ilike(nombre)).first()
        if tipo_existente:
            flash('❌ Ya existe un tipo de insumo con ese nombre', 'danger')
            return render_template('insumos/crear_tipo.html', valores=request.form)

        # Crear nuevo tipo de insumo
        tipo = TipoInsumo(
            Nombre=nombre,
            Descripción=descripcion,
            Estado=1  # Activo
        )

        db.session.add(tipo)
        db.session.commit()

        flash('✅ Tipo de insumo creado correctamente', 'success')
        return redirect(url_for('insumos.listar_tipos'))

    return render_template('insumos/crear_tipo.html')


@insumo_bp.route('/tipos/<int:id>/editar', methods=['POST'])
def editar_tipo(id):
    """Editar un tipo de insumo existente"""
    tipo = TipoInsumo.query.get_or_404(id)

    tipo.Nombre = request.form['nombre']
    tipo.Descripción = request.form['descripcion']
    tipo.Estado = int(request.form['estado'])

    db.session.commit()
    flash('✅ Tipo de insumo actualizado correctamente', 'success')
    return redirect(url_for('insumos.listar_tipos'))


@insumo_bp.route('/stock_bajo')
def stock_bajo():
    """Muestra los insumos con stock bajo (menos de 10 unidades)"""
    insumos_bajo_stock = []
    insumos = Insumo.query.all()

    for insumo in insumos:
        if insumo.stock_actual < 10:
            insumos_bajo_stock.append(insumo)

    return render_template('insumos/stock_bajo.html', insumos=insumos_bajo_stock)