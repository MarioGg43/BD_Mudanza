"""Controladores REST del control de materiales para React: el catálogo con su stock, la ficha con
los movimientos y la carga de compras y ajustes. Las reglas son las de pedidos/materiales.py y
los formularios los de pedidos/forms.py (MaterialForm), igual que en las pantallas de Django."""
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Count, Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.utils import timezone

from pedidos import materiales as reglas_mat
from pedidos.forms import MaterialForm
from usuarios.models import Material, MovimientoMaterial
from .autenticacion import endpoint, error, leer_json


def _material(m, en_uso=0):
    return {'id': m.id_material, 'nombre': m.nom_material, 'unidad': m.unidad_material, 'stock': m.stock_material,
            'minimo': m.stock_min_material, 'reutilizable': m.reutilizable, 'activo': m.Activo,
            'bajo_minimo': m.Activo and m.bajo_minimo, 'en_uso': en_uso}


def _movimiento(mv):
    return {'id': mv.pk, 'fecha': timezone.localtime(mv.fec_mov).strftime('%d/%m/%Y %H:%M'),
            'material': mv.idMaterial.nom_material, 'id_material': mv.idMaterial_id, 'tipo': mv.tipo_mov,
            'efecto': mv.efecto_texto or str(mv.cant_mov), 'cambia_stock': bool(mv.efecto),
            'observacion': mv.observacion_mov, 'pedido': mv.idPedido_id,
            'quien': f'{mv.idUsuario.Nombre} {mv.idUsuario.Apellido}' if mv.idUsuario else 'Sistema'}


def _guardar(form):
    if not form.is_valid():
        return None, error('Revisá los datos marcados.', errores={k: ' '.join(v) for k, v in form.errors.items()})
    return form.save(), None


@endpoint('MAT_GESTIONAR', metodos=('GET', 'POST'))
def materiales(request):
    """GET /api/materiales: el catálogo con su stock, cuántos reutilizables están afuera, el resumen
    y los últimos movimientos. POST: alta (con stock inicial opcional, que se registra como ingreso)."""
    if request.method == 'POST':
        datos = leer_json(request)
        form = MaterialForm({**datos, 'reutilizable': bool(datos.get('reutilizable')), 'Activo': datos.get('Activo', True)})
        if not form.is_valid():
            return error('Revisá los datos marcados.', errores={k: ' '.join(v) for k, v in form.errors.items()})
        with transaction.atomic():
            m = form.save()
            if form.cleaned_data.get('stock_inicial'):
                reglas_mat.registrar_ingreso(m, form.cleaned_data['stock_inicial'], request.usuario, 'Stock inicial')
        m.refresh_from_db()
        return JsonResponse(_material(m), status=201)
    en_uso = reglas_mat.en_uso()
    todos = list(Material.objects.annotate(cant_servicios=Count('servicios', filter=Q(servicios__idServicio__Activo=True)))
                 .order_by('-Activo', 'nom_material'))
    inicio_mes = timezone.localdate().replace(day=1)
    return JsonResponse({
        'materiales': [{**_material(m, en_uso.get(m.pk, 0)), 'servicios': m.cant_servicios} for m in todos],
        'resumen': {'activos': sum(m.Activo for m in todos), 'bajo_minimo': sum(m.Activo and m.bajo_minimo for m in todos),
                    'afuera': sum(en_uso.values()),
                    'movimientos_mes': MovimientoMaterial.objects.filter(fec_mov__date__gte=inicio_mes).count()},
        'ultimos': [_movimiento(mv) for mv in MovimientoMaterial.objects.select_related('idMaterial', 'idUsuario')
                    .order_by('-fec_mov', '-pk')[:8]],
    })


@endpoint('MAT_GESTIONAR', metodos=('GET', 'PUT'))
def material(request, id_material):
    """GET /api/materiales/<id>?pagina=: la ficha con sus servicios y sus movimientos.
    PUT: edita nombre, unidad, mínimo, si es reutilizable y si está activo (el stock no)."""
    m = get_object_or_404(Material, pk=id_material)
    if request.method == 'PUT':
        datos = leer_json(request)
        form = MaterialForm({'nom_material': m.nom_material, 'unidad_material': m.unidad_material,
                             'stock_min_material': m.stock_min_material, 'reutilizable': m.reutilizable,
                             'Activo': m.Activo, **datos}, instance=m)
        m, respuesta = _guardar(form)
        if respuesta:
            return respuesta
        reglas_mat._revisar_minimos([m])  # si subió el mínimo, puede quedar por debajo
    pagina = Paginator(m.movimientos.select_related('idUsuario', 'idPedido', 'idMaterial').order_by('-fec_mov', '-pk'), 25)
    pagina = pagina.get_page(request.GET.get('pagina'))
    return JsonResponse({
        **_material(m, reglas_mat.en_uso().get(m.pk, 0)),
        'servicios_que_lo_usan': [{'servicio': r.idServicio.Tipo_servicio, 'cantidad': r.cant_sugerida}
                                  for r in m.servicios.select_related('idServicio').order_by('idServicio__Tipo_servicio')],
        'movimientos': [_movimiento(mv) for mv in pagina],
        'pagina': pagina.number, 'paginas': pagina.paginator.num_pages,
    })


@endpoint('MAT_GESTIONAR', metodos=('POST',))
def movimiento(request, id_material):
    """POST /api/materiales/<id>/movimiento {tipo: Ingreso|Ajuste, cantidad, observacion}: una
    compra o un ajuste del inventario (con signo y motivo)."""
    m = get_object_or_404(Material, pk=id_material)
    datos = leer_json(request)
    try:
        cantidad = int(datos.get('cantidad'))
    except (TypeError, ValueError):
        return error('Revisá los datos marcados.', errores={'cantidad': 'Escribí un número entero.'})
    observacion = str(datos.get('observacion') or '')[:200]
    try:
        if datos.get('tipo') == 'Ingreso':
            if cantidad <= 0:
                return error('Revisá los datos marcados.', errores={'cantidad': 'En un ingreso la cantidad tiene que ser mayor a 0.'})
            reglas_mat.registrar_ingreso(m, cantidad, request.usuario, observacion)
        elif datos.get('tipo') == 'Ajuste':
            reglas_mat.registrar_ajuste(m, cantidad, request.usuario, observacion)
        else:
            return error('Revisá los datos marcados.', errores={'tipo': 'Elegí Ingreso o Ajuste.'})
    except reglas_mat.ErrorMaterial as e:
        return error(str(e))
    m.refresh_from_db()
    return JsonResponse(_material(m, reglas_mat.en_uso().get(m.pk, 0)))


@endpoint('MAT_GESTIONAR', metodos=('POST',))
def baja(request, id_material):
    """POST /api/materiales/<id>/baja: deja de sugerirse en las mudanzas; el historial queda."""
    m = get_object_or_404(Material, pk=id_material)
    m.Activo = False
    m.save(update_fields=['Activo'])
    return JsonResponse(_material(m))


@endpoint('SRV_GESTIONAR')
def catalogo_materiales(request):
    """GET /api/materiales/catalogo: los materiales activos, para elegirlos en un servicio."""
    return JsonResponse({'materiales': [{'id': m.pk, 'nombre': m.nom_material, 'unidad': m.unidad_material}
                                        for m in Material.objects.filter(Activo=True).order_by('nom_material')]})
