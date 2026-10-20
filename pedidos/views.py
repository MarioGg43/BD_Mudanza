"""Pantallas del pedido de mudanza (Hito 3). Las reglas viven en reglas.py."""
from datetime import date

from django.contrib import messages
from django.http import Http404, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_GET, require_POST

from usuarios.models import Pedido
from usuarios.permisos import pantalla_inicio
from usuarios.views import get_usuario_actual
from . import reglas
from .pdf import respuesta_pdf
from .forms import AnularForm, FiltroPedidosForm, InventarioFormSet, PedidoForm, RegistroClienteForm
from .permisos import requiere_permiso, tiene_permiso


def _ve_todos(usuario):
    """Quien gestiona pedidos ve todos; el cliente, solo los suyos."""
    return tiene_permiso(usuario, 'PED_GESTIONAR')


def _pedido_visible(request, id_pedido):
    """El pedido, si el usuario puede verlo. Un pedido ajeno da 404 y no 403,
    para no revelar que existe."""
    pedido = get_object_or_404(
        Pedido.objects.select_related('idUsuario', 'patente_vehiculo', 'usuario_anulacion')
                      .prefetch_related('detalles__idServicio', 'inventario__idObjeto'),
        pk=id_pedido)
    if not _ve_todos(request.usuario) and pedido.idUsuario_id != request.usuario.id_usuario:
        raise Http404('Pedido inexistente')
    return pedido


def _consulta(request):
    """La consulta con los filtros del GET: la usan la pantalla y el PDF."""
    ve_todos = _ve_todos(request.usuario)
    base = Pedido.objects.all() if ve_todos else Pedido.objects.filter(idUsuario=request.usuario)
    form = FiltroPedidosForm(request.GET or None, ve_todos=ve_todos)
    filtros = form.filtros() if form.is_valid() else {}
    return form, ve_todos, reglas.filtrar_pedidos(base, **filtros)


@requiere_permiso('PED_CONSULTAR')
def lista(request):
    form, ve_todos, pedidos = _consulta(request)
    avisos = reglas.contar_avisos() if ve_todos else {}
    return render(request, 'pedidos/lista.html', {
        'form': form, 've_todos': ve_todos, 'pedidos': pedidos,
        'vencidos': avisos.get(reglas.VENCIDO), 'para_finalizar': avisos.get(reglas.PARA_FINALIZAR),
        'por_confirmar': avisos.get(reglas.POR_CONFIRMAR), 'dias_por_confirmar': reglas.DIAS_POR_CONFIRMAR,
        'puede_registrar': tiene_permiso(request.usuario, 'PED_REGISTRAR'),
    })


@requiere_permiso('PED_CONSULTAR')
def descargar(request):
    """La lista filtrada en PDF, con los filtros usados."""
    form, ve_todos, pedidos = _consulta(request)
    usados = []
    if form.is_valid():
        for nombre, campo in form.fields.items():
            valor = form.cleaned_data.get(nombre)
            if valor:
                if hasattr(valor, 'strftime'):
                    texto = valor.strftime('%d/%m/%Y')
                elif hasattr(campo, 'label_from_instance'):
                    texto = campo.label_from_instance(valor)
                else:
                    texto = str(valor)
                usados.append((campo.label, texto))
    return respuesta_pdf(request, 'pedidos/lista_pdf.html', {
        'pedidos': pedidos, 've_todos': ve_todos, 'filtros_usados': usados,
        'emitido': timezone.localtime()}, 'Pedidos.pdf')


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
                    request.usuario, d['fecha_servicio'], d['hora_servicio'], d['origen'], d['destino'],
                    d['servicio'].id_servicio, d['vehiculo'].patente,
                    [f.cleaned_data for f in items.forms if f.cleaned_data],
                    ids_adicionales=[s.id_servicio for s in d['adicionales']])
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
        'servicios': form.fields['servicio'].queryset,
        'adicionales': form.fields['adicionales'].queryset,
        'elegido': str(form['servicio'].value() or ''),
        'adicionales_elegidos': [str(i) for i in form['adicionales'].value() or []],
    })


@requiere_permiso('PED_REGISTRAR')
@require_GET
def vehiculos_libres(request):
    """Para el formulario: los vehículos libres en la fecha elegida."""
    try:
        fecha = date.fromisoformat(request.GET.get('fecha', ''))
    except ValueError:
        return JsonResponse({'vehiculos': []})
    libres = [{'patente': v.patente, 'descripcion': f'{v.tipo_vehiculo} · {v.marca_modelo}',
               'capacidad_kg': float(v.capacidad_kg), 'capacidad_m3': float(v.capacidad_m3)}
              for v in reglas.vehiculos_libres(fecha)]
    return JsonResponse({'vehiculos': libres,
                         'motivo': '' if libres else reglas.motivo_sin_vehiculos(fecha)})


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
    pedido = _pedido_visible(request, id_pedido)
    if pedido.estado not in Pedido.ACTIVOS:
        messages.error(request, f'El pedido N° {id_pedido} está {pedido.estado.lower()} y no se puede anular.')
        return redirect('pedidos_detalle', id_pedido=id_pedido)
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


@requiere_permiso('PED_COMPROBANTE')
def comprobante(request, id_pedido):
    pedido = _pedido_visible(request, id_pedido)
    return render(request, 'pedidos/comprobante.html', {'pedido': pedido, 'emitido': timezone.localtime()})


@requiere_permiso('PED_COMPROBANTE')
def comprobante_pdf(request, id_pedido):
    pedido = _pedido_visible(request, id_pedido)
    return respuesta_pdf(request, 'pedidos/comprobante_pdf.html',
                         {'pedido': pedido, 'emitido': timezone.localtime()},
                         f'Comprobante-pedido-{pedido.id_pedido}.pdf')


def registro(request):
    """Alta pública de clientes: queda con el rol Cliente e inicia sesión."""
    usuario = get_usuario_actual(request)
    if usuario:
        return pantalla_inicio(usuario)
    form = RegistroClienteForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        cliente = form.crear_cliente()
        cliente.registrar_acceso()
        request.session.cycle_key()
        request.session['usuario_dni'] = cliente.DNI
        request.session['usuario_rol'] = cliente.idRol.nom_rol
        messages.success(request, f'¡Bienvenida/o! Tu usuario es {cliente.NombreUsuario}.')
        return redirect('pedidos_lista')
    return render(request, 'pedidos/registro.html', {'form': form})
