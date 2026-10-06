"""Pantallas del pedido de mudanza (Hito 3). Las reglas viven en reglas.py."""
from django.http import Http404
from django.shortcuts import get_object_or_404, render

from usuarios.models import Pedido
from . import reglas
from .forms import FiltroPedidosForm
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
