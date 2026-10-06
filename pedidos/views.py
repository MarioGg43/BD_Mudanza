"""Pantallas del pedido de mudanza (Hito 3). Las reglas viven en reglas.py."""
from datetime import date

from django.contrib import messages
from django.http import Http404, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_GET, require_POST

from usuarios.models import Pedido
from . import reglas
from .forms import AnularForm, FiltroPedidosForm, InventarioFormSet, PedidoForm
from .permisos import requiere_permiso, tiene_permiso


def _ve_todos(usuario):
    """Quien gestiona pedidos ve todos; el cliente, solo los suyos."""
    return tiene_permiso(usuario, 'PED_GESTIONAR')


def _pedido_visible(request, id_pedido):
    """El pedido, si el usuario puede verlo. Un pedido ajeno da 404 y no 403,
    para no revelar que existe."""
    pedido = get_object_or_404(
        Pedido.objects.select_related('idUsuario', 'patente_vehiculo', 'usuario_anulacion')
                      .prefetch_related('detalles__idServicio', 'inventario'),
        pk=id_pedido)
    if not _ve_todos(request.usuario) and pedido.idUsuario_id != request.usuario.id_usuario:
        raise Http404('Pedido inexistente')
    return pedido


@requiere_permiso('PED_CONSULTAR')
def lista(request):
    ve_todos = _ve_todos(request.usuario)
    base = Pedido.objects.all() if ve_todos else Pedido.objects.filter(idUsuario=request.usuario)
    form = FiltroPedidosForm(request.GET or None, ve_todos=ve_todos)
    filtros = form.filtros() if form.is_valid() else {}
    return render(request, 'pedidos/lista.html', {
        'form': form, 've_todos': ve_todos,
        'pedidos': reglas.filtrar_pedidos(base, **filtros),
        'puede_registrar': tiene_permiso(request.usuario, 'PED_REGISTRAR'),
    })


@requiere_permiso('PED_CONSULTAR')
def detalle(request, id_pedido):
    pedido = _pedido_visible(request, id_pedido)
    return render(request, 'pedidos/detalle.html', {
        'pedido': pedido,
        'puede_gestionar': tiene_permiso(request.usuario, 'PED_GESTIONAR'),
        'puede_anular': tiene_permiso(request.usuario, 'PED_ANULAR'),
        'puede_comprobante': tiene_permiso(request.usuario, 'PED_COMPROBANTE'),
    })


@requiere_permiso('PED_REGISTRAR')
def nuevo(request):
    if request.method == 'POST':
        form = PedidoForm(request.POST)
        items = InventarioFormSet(request.POST, prefix='inv')
        if form.is_valid() and items.is_valid():
            d = form.cleaned_data
            try:
                pedido = reglas.registrar_pedido(
                    request.usuario, d['fecha_servicio'], d['origen'], d['destino'],
                    [s.id_servicio for s in d['servicios']], d['vehiculo'].patente,
                    [f.cleaned_data for f in items.forms if f.cleaned_data])
            except reglas.ErrorPedido as e:
                for campo, mensaje in e.errores.items():
                    form.add_error(campo if campo in form.fields else None, mensaje)
            else:
                messages.success(request, f'Pedido N° {pedido.id_pedido} registrado. '
                                          'Queda pendiente hasta que la empresa lo confirme.')
                return redirect('pedidos_detalle', id_pedido=pedido.id_pedido)
        messages.error(request, 'Revisá los datos marcados.')
    else:
        form = PedidoForm()
        items = InventarioFormSet(prefix='inv')
    return render(request, 'pedidos/nuevo.html', {
        'form': form, 'items': items,
        'servicios': form.fields['servicios'].queryset,
        'elegidos': [str(v) for v in (form['servicios'].value() or [])],
    })


@requiere_permiso('PED_REGISTRAR')
@require_GET
def vehiculos_libres(request):
    """Para el formulario: los vehículos libres en la fecha elegida."""
    try:
        fecha = date.fromisoformat(request.GET.get('fecha', ''))
    except ValueError:
        return JsonResponse({'vehiculos': []})
    return JsonResponse({'vehiculos': [
        {'patente': v.patente, 'descripcion': f'{v.tipo_vehiculo} · {v.marca_modelo}',
         'capacidad_kg': float(v.capacidad_kg)}
        for v in reglas.vehiculos_libres(fecha)]})


def _accion(request, id_pedido, funcion, hecho):
    get_object_or_404(Pedido, pk=id_pedido)
    try:
        funcion(id_pedido)
        messages.success(request, f'Pedido N° {id_pedido} {hecho}.')
    except reglas.ErrorPedido as e:
        messages.error(request, str(e))
    return redirect('pedidos_detalle', id_pedido=id_pedido)


@requiere_permiso('PED_GESTIONAR')
@require_POST
def confirmar(request, id_pedido):
    return _accion(request, id_pedido, reglas.confirmar, 'confirmado')


@requiere_permiso('PED_GESTIONAR')
@require_POST
def finalizar(request, id_pedido):
    return _accion(request, id_pedido, reglas.finalizar, 'finalizado')


@requiere_permiso('PED_ANULAR')
def anular(request, id_pedido):
    pedido = get_object_or_404(Pedido, pk=id_pedido)
    form = AnularForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        try:
            reglas.anular(id_pedido, request.usuario, form.cleaned_data['motivo'])
        except reglas.ErrorPedido as e:
            if 'motivo' in e.errores:
                form.add_error('motivo', e.errores['motivo'])
            else:
                messages.error(request, str(e))
                return redirect('pedidos_detalle', id_pedido=id_pedido)
        else:
            messages.success(request, f'Pedido N° {id_pedido} anulado.')
            return redirect('pedidos_detalle', id_pedido=id_pedido)
    return render(request, 'pedidos/anular.html', {'pedido': pedido, 'form': form})
