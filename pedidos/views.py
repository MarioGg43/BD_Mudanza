"""Pantallas del pedido de mudanza (Hito 3). Las reglas viven en reglas.py."""
from datetime import date, time
from urllib.parse import quote, urlencode

from django.conf import settings
from django.contrib import messages
from django.core.paginator import Paginator
from django.http import Http404, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_GET, require_POST

from usuarios.models import Pedido, PersonalPedido, Reprogramacion, Servicio
from usuarios.permisos import pantalla_inicio, requiere_permiso_api
from usuarios.views import get_usuario_actual
from . import mapa, materiales, reglas
from .pdf import respuesta_pdf
from .forms import (AnularForm, AsignarPersonalForm, FiltroPedidosForm, InventarioFormSet, PedidoForm,
                    RegistroClienteForm, ReprogramarForm, ServiciosPedidoForm, objetos_para_elegir)
from .permisos import requiere_permiso, tiene_permiso


POR_PAGINA = 25


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
    atrasadas = {p.pk for p in reglas.mudanzas_atrasadas()} if ve_todos else set()
    # de a 25 por página: con cientos de pedidos la lista entera tardaba en cargar
    pagina = Paginator(pedidos, POR_PAGINA).get_page(request.GET.get('pagina'))
    pedidos = list(pagina.object_list)
    # al cliente se le marca el pedido que cambió de horario y todavía no abrió
    cambiados = set() if ve_todos else set(Reprogramacion.objects.filter(
        idPedido__in=[p.pk for p in pedidos], visto_cliente=False).values_list('idPedido', flat=True))
    for p in pedidos:
        p.atrasada = p.pk in atrasadas
        p.horario_cambiado = p.pk in cambiados
    return render(request, 'pedidos/lista.html', {
        'form': form, 've_todos': ve_todos, 'pedidos': pedidos, 'pagina': pagina,
        'consulta': urlencode({k: v for k, v in request.GET.items() if k != 'pagina'}), 'atrasadas': avisos.get(reglas.ATRASADA),
        'vencidos': avisos.get(reglas.VENCIDO), 'para_finalizar': avisos.get(reglas.PARA_FINALIZAR),
        'por_confirmar': avisos.get(reglas.POR_CONFIRMAR), 'dias_por_confirmar': reglas.DIAS_POR_CONFIRMAR,
        'sin_chofer': avisos.get(reglas.SIN_CHOFER),
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
    personal = list(pedido.personal.select_related('idUsuario'))
    # Aviso de mudanza atrasada: en la atrasada (quién la espera) y en la que espera
    siguiente = anterior = None
    if _ve_todos(request.usuario):
        atrasadas = reglas.mudanzas_atrasadas()
        siguiente = atrasadas.get(pedido)
        anterior = next((p for p, q in atrasadas.items() if q.pk == pedido.pk), None)
    # Cambios de horario: el administrador ve el historial y puede avisar por WhatsApp; el
    # cliente ve el último, y al abrir su pedido queda como visto
    reprogramaciones = list(pedido.reprogramaciones.select_related('usuario'))
    ultima = reprogramaciones[0] if reprogramaciones else None
    cambio_nuevo = bool(ultima and not ultima.visto_cliente)
    whatsapp = ''
    if ultima and pedido.estado in Pedido.ACTIVOS:
        telefono = reglas.telefono_whatsapp(pedido.idUsuario.Telefono)
        if telefono:
            whatsapp = f'https://wa.me/{telefono}?text={quote(reglas.mensaje_reprogramacion(ultima))}'
    if cambio_nuevo and pedido.idUsuario_id == request.usuario.id_usuario:
        pedido.reprogramaciones.filter(visto_cliente=False).update(visto_cliente=True)
    return render(request, 'pedidos/detalle.html', {
        'pedido': pedido, 'reprogramaciones': reprogramaciones, 'ultima': ultima, 'cambio_nuevo': cambio_nuevo,
        'whatsapp': whatsapp,
        'como_llegar': mapa.como_llegar(pedido.origen, pedido.destino, *mapa.puntos(pedido)),
        'siguiente': siguiente, 'comparte_siguiente': siguiente and reglas.que_comparten(pedido, siguiente),
        'anterior': anterior, 'comparte_anterior': anterior and reglas.que_comparten(anterior, pedido),
        'chofer': next((x.idUsuario for x in personal if x.Funcion == PersonalPedido.CHOFER), None),
        'ayudantes': [x.idUsuario for x in personal if x.Funcion == PersonalPedido.AYUDANTE],
        'se_puede_asignar': pedido.estado in Pedido.ACTIVOS and not pedido.ya_empezo,
        'puede_gestionar': tiene_permiso(request.usuario, 'PED_GESTIONAR'),
        'es_mio': pedido.idUsuario_id == request.usuario.id_usuario,
        'cliente_puede_cambiar': reglas.cliente_puede_cambiar(pedido),
        'horas_limite': reglas.HORAS_LIMITE_CLIENTE,
        'puede_anular': tiene_permiso(request.usuario, 'PED_ANULAR'),
        'puede_comprobante': tiene_permiso(request.usuario, 'PED_COMPROBANTE'),
        'materiales': _materiales_del_pedido(pedido) if tiene_permiso(request.usuario, 'PED_GESTIONAR') else None,
    })


def _materiales_del_pedido(pedido):
    """Para el detalle: qué sugieren los servicios y, si la mudanza salió, los movimientos."""
    movs = list(pedido.movimientos_material.select_related('idMaterial', 'idUsuario').order_by('fec_mov', 'pk'))
    return {'sugeridos': [{'material': m, 'cantidad': c, 'falta': max(c - m.stock_material, 0)}
                          for m, c in materiales.sugeridos(pedido).items()],
            'movimientos': movs}


@requiere_permiso('PED_REGISTRAR')
def nuevo(request):
    return _formulario_pedido(request)


@requiere_permiso('PED_REGISTRAR')
def modificar(request, id_pedido):
    """El cliente cambia su pedido hasta 24 h antes, con la misma pantalla que para pedir."""
    pedido = get_object_or_404(Pedido.objects.prefetch_related('detalles__idServicio', 'inventario'),
                               pk=id_pedido, idUsuario=request.usuario)
    if not reglas.cliente_puede_cambiar(pedido):
        messages.error(request, f'Ya no se puede modificar: faltan menos de {reglas.HORAS_LIMITE_CLIENTE} horas '
                                'o el pedido no está activo. Comunicate con la empresa.')
        return redirect('pedidos_detalle', id_pedido=id_pedido)
    return _formulario_pedido(request, pedido)


@requiere_permiso('PED_CONSULTAR')
def cancelar(request, id_pedido):
    """El cliente cancela su mudanza hasta 24 h antes (queda Anulada con su motivo)."""
    pedido = get_object_or_404(Pedido, pk=id_pedido, idUsuario=request.usuario)
    if not reglas.cliente_puede_cambiar(pedido):
        messages.error(request, f'Ya no se puede cancelar: faltan menos de {reglas.HORAS_LIMITE_CLIENTE} horas '
                                'o el pedido no está activo. Comunicate con la empresa.')
        return redirect('pedidos_detalle', id_pedido=id_pedido)
    form = AnularForm(request.POST or None)
    form.fields['motivo'].label = '¿Por qué cancelás la mudanza?'
    if request.method == 'POST' and form.is_valid():
        try:
            reglas.cancelar_por_cliente(id_pedido, request.usuario, form.cleaned_data['motivo'])
        except reglas.ErrorPedido as e:
            form.add_error('motivo', ' '.join(e.errores.values()))
        else:
            messages.success(request, f'Cancelaste la mudanza del pedido N° {id_pedido}.')
            return redirect('pedidos_detalle', id_pedido=id_pedido)
    return render(request, 'pedidos/cancelar.html', {'pedido': pedido, 'form': form})


def _con_materiales(servicios):
    """Los servicios con los materiales activos que lleva cada uno («Incluye: mantas ×6…»)."""
    from django.db.models import Prefetch
    from usuarios.models import RecursoAsignado
    return servicios.prefetch_related(Prefetch(
        'recursos', queryset=RecursoAsignado.objects.filter(idMaterial__Activo=True)
        .select_related('idMaterial').order_by('idMaterial__nom_material')))


def _formulario_pedido(request, pedido=None):
    """Pedir una mudanza o, con `pedido`, modificarla (las reglas: registrar_pedido / modificar_pedido)."""
    if request.method == 'POST':
        form = PedidoForm(request.POST)
        items = InventarioFormSet(request.POST, prefix='inv')
        if form.is_valid() and items.is_valid():
            d = form.cleaned_data
            datos = (d['fecha_servicio'], d['hora_servicio'], d['origen'], d['destino'], d['servicio'].id_servicio,
                     d['vehiculo'].patente, [f.cleaned_data for f in items.forms if f.cleaned_data])
            puntos = form.puntos()
            hecho = 'modificado' if pedido else 'registrado'
            try:
                if pedido:
                    pedido = reglas.modificar_pedido(pedido.pk, request.usuario, *datos, puntos=puntos,
                                                     ids_adicionales=[s.id_servicio for s in d['adicionales']])
                else:
                    pedido = reglas.registrar_pedido(request.usuario, *datos, puntos=puntos,
                                                     ids_adicionales=[s.id_servicio for s in d['adicionales']])
            except reglas.ErrorPedido as e:
                for campo, mensaje in e.errores.items():
                    form.add_error(campo if campo in form.fields else None, mensaje)
            else:
                messages.success(request, f'Pedido N° {pedido.id_pedido} {hecho}. '
                                          'Queda pendiente hasta que la empresa lo confirme.')
                return redirect('pedidos_detalle', id_pedido=pedido.id_pedido)
        messages.error(request, 'Revisá los datos marcados.')
    elif pedido:
        detalles = list(pedido.detalles.all())
        form = PedidoForm(initial={
            'fecha_servicio': pedido.fecha_servicio, 'hora_servicio': pedido.hora_servicio,
            'origen': pedido.origen, 'destino': pedido.destino, 'vehiculo': pedido.patente_vehiculo_id,
            'lat_origen': pedido.lat_origen, 'lon_origen': pedido.lon_origen,
            'lat_destino': pedido.lat_destino, 'lon_destino': pedido.lon_destino,
            'servicio': next((d.idServicio_id for d in detalles if d.idServicio.Categoria == Servicio.PRINCIPAL), None),
            'adicionales': [d.idServicio_id for d in detalles if d.idServicio.Categoria == Servicio.ADICIONAL]})
        items = InventarioFormSet(prefix='inv')
    else:
        form = PedidoForm()
        items = InventarioFormSet(prefix='inv')
    # Para la ventana «Agregar objeto»: el catálogo con la clave de comparación (la misma de las
    # reglas) y, si el formulario vuelve con errores, lo que la persona ya había cargado
    catalogo = [{'id': o.pk, 'nombre': o.nom_objeto, 'clave': reglas.clave_objeto(o.nom_objeto), 'otro': o.es_otro}
                for o in objetos_para_elegir()]
    items_iniciales = [{'objeto': f['objeto'].value(), 'cantidad': f['cantidad'].value(),
                        'fragil': bool(f['fragil'].value()), 'observacion': f['observacion'].value() or ''}
                       for f in items.forms if items.is_bound and f['objeto'].value()]
    if pedido and not items.is_bound:
        items_iniciales = [{'objeto': i.idObjeto_id, 'cantidad': i.Cantidad, 'fragil': i.Fragil,
                            'observacion': i.Observacion or ''} for i in pedido.inventario.all()]
    return render(request, 'pedidos/nuevo.html', {
        'form': form, 'items': items, 'catalogo': catalogo, 'items_iniciales': items_iniciales, 'pedido': pedido,
        'horas_limite': reglas.HORAS_LIMITE_CLIENTE,
        'mapa_activo': bool(settings.ORS_API_KEY),  # «Elegir en el mapa» solo si hay clave
        'max_cantidad': reglas.MAX_CANTIDAD,
        # con sus materiales, para mostrarle al cliente qué incluye cada servicio
        'servicios': _con_materiales(form.fields['servicio'].queryset),
        'adicionales': _con_materiales(form.fields['adicionales'].queryset),
        'elegido': str(form['servicio'].value() or ''),
        'adicionales_elegidos': [str(i) for i in form['adicionales'].value() or []],
    })


@requiere_permiso('PED_REGISTRAR')
@require_GET
def vehiculos_libres(request):
    """Para el formulario: los vehículos libres en el horario elegido (fecha, hora y la
    duración del servicio principal)."""
    try:
        fecha = date.fromisoformat(request.GET.get('fecha', ''))
        hora = time.fromisoformat(request.GET.get('hora', ''))
    except ValueError:
        return JsonResponse({'vehiculos': [], 'motivo': ''})
    servicio = Servicio.objects.filter(pk=request.GET.get('servicio') or None, Activo=True,
                                       Categoria=Servicio.PRINCIPAL).first()
    if not servicio:
        return JsonResponse({'vehiculos': [], 'motivo': 'Elegí el servicio para ver los vehículos libres.'})
    horas = servicio.Duracion_horas or reglas.MIN_HORAS
    propio = Pedido.objects.filter(pk=request.GET.get('pedido') or None, idUsuario=request.usuario).first()
    libres = [{'patente': v.patente, 'descripcion': f'{v.tipo_vehiculo} · {v.marca_modelo}', 'recargo': v.recargo,
               'capacidad_kg': float(v.capacidad_kg), 'capacidad_m3': float(v.capacidad_m3)}
              for v in reglas.vehiculos_libres(reglas.inicio_de(fecha, hora), horas, propio)]
    return JsonResponse({'vehiculos': libres, 'motivo': '' if libres else reglas.motivo_sin_vehiculos()})


def _accion(request, id_pedido, funcion, hecho):
    get_object_or_404(Pedido, pk=id_pedido)
    try:
        funcion(id_pedido)
        messages.success(request, f'Pedido N° {id_pedido} {hecho}.')
    except reglas.ErrorPedido as e:
        messages.error(request, str(e))
    # el recordatorio de finalizar vuelve a la pantalla desde donde se tocó el botón
    volver = request.POST.get('next', '')
    if volver and url_has_allowed_host_and_scheme(volver, allowed_hosts={request.get_host()}):
        return redirect(volver)
    return redirect('pedidos_detalle', id_pedido=id_pedido)


@requiere_permiso('PED_GESTIONAR')
@require_POST
def confirmar(request, id_pedido):
    return _accion(request, id_pedido, reglas.confirmar, 'confirmado')


@requiere_permiso('PED_GESTIONAR')
@require_POST
def finalizar(request, id_pedido):
    return _accion(request, id_pedido, reglas.finalizar, 'finalizado')


@requiere_permiso('PED_GESTIONAR')
def asignar(request, id_pedido):
    """Asignar el personal de la mudanza: un chofer y los ayudantes que hagan falta."""
    pedido = get_object_or_404(Pedido.objects.select_related('idUsuario', 'patente_vehiculo__chofer_asignado'),
                               pk=id_pedido)
    if pedido.estado not in Pedido.ACTIVOS or pedido.ya_empezo:
        messages.error(request, f'El pedido N° {id_pedido} ya no admite cambios de personal.')
        return redirect('pedidos_detalle', id_pedido=id_pedido)
    actual = list(pedido.personal.all())
    inicial = {'chofer': next((x.idUsuario_id for x in actual if x.Funcion == PersonalPedido.CHOFER), None),
               'ayudantes': [x.idUsuario_id for x in actual if x.Funcion == PersonalPedido.AYUDANTE]}
    sugerido = None
    form = AsignarPersonalForm(request.POST or None, pedido=pedido, initial=dict(inicial))
    if not inicial['chofer']:
        # se sugiere el chofer habitual del vehículo, si está libre en ese horario
        habitual = pedido.patente_vehiculo.chofer_asignado
        if habitual and form.fields['chofer'].queryset.filter(pk=habitual.pk).exists():
            form.initial['chofer'] = habitual.pk
            sugerido = habitual
    if request.method == 'POST' and form.is_valid():
        try:
            reglas.asignar_personal(id_pedido, form.cleaned_data['chofer'].pk,
                                    [a.pk for a in form.cleaned_data['ayudantes']])
        except reglas.ErrorPedido as e:
            for campo, mensaje in e.errores.items():
                form.add_error(campo if campo in form.fields else None, mensaje)
        else:
            messages.success(request, f'Personal del pedido N° {id_pedido} asignado.')
            return redirect('pedidos_detalle', id_pedido=id_pedido)
    return render(request, 'pedidos/asignar.html', {
        'pedido': pedido, 'form': form, 'max_ayudantes': reglas.MAX_AYUDANTES,
        'sugerido': sugerido})


@requiere_permiso('PED_GESTIONAR')
def servicios_pedido(request, id_pedido):
    """El administrador cambia el principal o los adicionales; el total se recalcula."""
    pedido = get_object_or_404(Pedido.objects.select_related('idUsuario', 'patente_vehiculo'), pk=id_pedido)
    if pedido.estado not in Pedido.ACTIVOS:
        messages.error(request, f'El pedido N° {id_pedido} está {pedido.estado.lower()}: no se pueden cambiar los servicios.')
        return redirect('pedidos_detalle', id_pedido=id_pedido)
    detalles = list(pedido.detalles.select_related('idServicio'))
    form = ServiciosPedidoForm(request.POST or None, initial={
        'servicio': next((d.idServicio_id for d in detalles if d.idServicio.Categoria == Servicio.PRINCIPAL), None),
        'adicionales': [d.idServicio_id for d in detalles if d.idServicio.Categoria == Servicio.ADICIONAL]})
    if request.method == 'POST' and form.is_valid():
        try:
            reglas.editar_servicios(id_pedido, form.cleaned_data['servicio'].pk,
                                    [s.pk for s in form.cleaned_data['adicionales']])
        except reglas.ErrorPedido as e:
            for campo, mensaje in e.errores.items():
                form.add_error(campo if campo in form.fields else None, mensaje)
        else:
            messages.success(request, f'Servicios del pedido N° {id_pedido} actualizados.')
            return redirect('pedidos_detalle', id_pedido=id_pedido)
    return render(request, 'pedidos/servicios_pedido.html', {'pedido': pedido, 'form': form})


@requiere_permiso('MUDANZAS_OPERAR')
def relevamiento(request, id_pedido):
    """El chofer, al llegar: cantidades reales, objetos que no se declararon, adicionales y recargo."""
    pedido = get_object_or_404(Pedido.objects.select_related('idUsuario', 'patente_vehiculo')
                                             .prefetch_related('inventario__idObjeto', 'detalles__idServicio'),
                               pk=id_pedido)
    es_chofer = pedido.personal.filter(Funcion=PersonalPedido.CHOFER, idUsuario=request.usuario).exists()
    if not es_chofer or not pedido.en_curso:
        messages.error(request, 'El relevamiento lo hace el chofer de la mudanza, después de marcar «Empezamos».')
        return redirect('usuario_portal')
    tiene = {d.idServicio_id for d in pedido.detalles.all()}
    adicionales = Servicio.objects.filter(Activo=True, Categoria=Servicio.ADICIONAL).exclude(pk__in=tiene)
    errores = {}
    if request.method == 'POST':
        reales = {i.pk: request.POST.get(f'real-{i.pk}', i.Cantidad) for i in pedido.inventario.all()}
        nuevos = []
        for n in range(5):
            id_obj = request.POST.get(f'nuevo-{n}-objeto')
            if id_obj and id_obj.isdigit():
                nuevos.append({'objeto': int(id_obj), 'cantidad': request.POST.get(f'nuevo-{n}-cantidad'),
                               'fragil': request.POST.get(f'nuevo-{n}-fragil') == 'on',
                               'observacion': request.POST.get(f'nuevo-{n}-observacion', '')})
        try:
            reglas.relevamiento(id_pedido, request.usuario, reales, nuevos,
                                [int(x) for x in request.POST.getlist('adicionales')],
                                request.POST.get('recargo') or 0, request.POST.get('motivo', ''))
        except reglas.ErrorPedido as e:
            errores = e.errores
        else:
            messages.success(request, f'Relevamiento del pedido N° {id_pedido} guardado.')
            return redirect('usuario_portal')
    return render(request, 'pedidos/relevamiento.html', {
        'pedido': pedido, 'adicionales': adicionales, 'objetos': objetos_para_elegir(), 'errores': errores,
        'datos': request.POST, 'filas_nuevas': range(5)})


@requiere_permiso('MUDANZAS_OPERAR')
@require_POST
def empezar(request, id_pedido):
    """«Empezamos» desde el portal: solo el chofer de la mudanza."""
    get_object_or_404(Pedido, pk=id_pedido)
    try:
        pedido = reglas.marcar_inicio(id_pedido, request.usuario)
        messages.success(request, f'Mudanza N° {id_pedido} en curso. Cuando terminen, tocá «Terminamos».')
        if pedido.faltantes:  # salió lo que había: que el chofer sepa qué le falta
            messages.warning(request, 'No alcanzó el stock de: ' + ', '.join(
                f'{m.nom_material} (llevan {llevado} de {sugerido})' for m, sugerido, llevado in pedido.faltantes)
                + '. Ya le avisamos al administrador.')
    except reglas.ErrorPedido as e:
        messages.error(request, str(e))
    return redirect('usuario_portal')


@requiere_permiso('MUDANZAS_OPERAR')
def terminar(request, id_pedido):
    """«Terminamos» desde el portal: el chofer cuenta qué se gastó y qué volvió de los materiales,
    y con eso se guarda la hora real y el pedido queda finalizado."""
    pedido = get_object_or_404(Pedido.objects.select_related('idUsuario'), pk=id_pedido)
    es_chofer = pedido.personal.filter(Funcion=PersonalPedido.CHOFER, idUsuario=request.usuario).exists()
    if not (es_chofer and pedido.estado == Pedido.CONFIRMADO and pedido.inicio_real):
        messages.error(request, 'Solo el chofer puede terminar una mudanza que esté en curso.')
        return redirect('usuario_portal')
    salieron = list(materiales.enviados(pedido).items())
    filas = [{'material': m, 'salio': c, 'campo': f'mat_{m.pk}',
              'valor': request.POST.get(f'mat_{m.pk}', c)} for m, c in salieron]
    error = ''
    if request.method == 'POST':
        usados = {}
        for f in filas:
            try:
                usados[f['material'].pk] = int(f['valor'])
            except (TypeError, ValueError):
                error = f'{f["material"].nom_material}: escribí un número de 0 a {f["salio"]}.'
        if not error:
            try:
                reglas.marcar_fin(id_pedido, request.usuario, usados)
            except reglas.ErrorPedido as e:
                error = str(e)
            else:
                perdidos = [f'{f["salio"] - usados[f["material"].pk]} {f["material"].nom_material.lower()}'
                            for f in filas if f['material'].reutilizable and usados[f['material'].pk] < f['salio']]
                messages.success(request, f'Mudanza N° {id_pedido} terminada y finalizada. ¡Buen trabajo!')
                if perdidos:
                    messages.warning(request, f'Quedó registrado que no volvieron: {", ".join(perdidos)}.')
                return redirect('usuario_portal')
        if not filas and error:  # sin materiales no hay formulario que mostrar
            messages.error(request, error)
            return redirect('usuario_portal')
    return render(request, 'pedidos/terminar.html', {'pedido': pedido, 'filas': filas, 'error': error})


@requiere_permiso('PED_GESTIONAR')
def reprogramar(request, id_pedido):
    """Cambiar la fecha, la hora o el vehículo de un pedido, con el motivo. Queda en el historial
    y el cliente lo ve en su pedido; desde el detalle se le puede avisar por WhatsApp."""
    pedido = get_object_or_404(Pedido.objects.select_related('idUsuario', 'patente_vehiculo')
                                             .prefetch_related('personal__idUsuario'), pk=id_pedido)
    if pedido.estado not in Pedido.ACTIVOS:
        messages.error(request, f'El pedido N° {id_pedido} está {pedido.estado.lower()}: no se puede reprogramar.')
        return redirect('pedidos_detalle', id_pedido=id_pedido)
    form = ReprogramarForm(request.POST or None, pedido=pedido, initial={
        'fecha_servicio': pedido.fecha_servicio, 'hora_servicio': pedido.hora_servicio,
        'vehiculo': pedido.patente_vehiculo_id, 'motivo': request.GET.get('motivo', '')})
    if request.method == 'POST' and form.is_valid():
        d = form.cleaned_data
        try:
            reglas.reprogramar(id_pedido, request.usuario, d['fecha_servicio'], d['hora_servicio'],
                               d['vehiculo'].patente, d['motivo'], d['observacion'], d['quitar_ocupados'],
                               id_chofer=d['chofer'].pk if d['chofer'] else None)
        except reglas.ErrorPedido as e:
            for campo, mensaje in e.errores.items():
                form.add_error(campo if campo in form.fields else None, mensaje)
        else:
            messages.success(request, f'Pedido N° {id_pedido} reprogramado. Avisale al cliente.')
            return redirect('pedidos_detalle', id_pedido=id_pedido)
    return render(request, 'pedidos/reprogramar.html', {'pedido': pedido, 'form': form})


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


def recorrido(request, id_pedido):
    """El recorrido del pedido para el mapa (JSON). Lo ven el cliente dueño del pedido, quien
    gestiona pedidos y el personal asignado a esa mudanza. La página lo pide aparte, así no
    espera al servicio de mapas para mostrarse."""
    usuario = get_usuario_actual(request)
    if not usuario:
        return JsonResponse({'ok': False, 'error': 'Tenés que iniciar sesión.'}, status=401)
    pedido = get_object_or_404(Pedido, pk=id_pedido)
    es_suyo = tiene_permiso(usuario, 'PED_CONSULTAR') and (
        _ve_todos(usuario) or pedido.idUsuario_id == usuario.id_usuario)
    lo_hace = tiene_permiso(usuario, 'MUDANZAS_OPERAR') and pedido.personal.filter(idUsuario=usuario).exists()
    if not (es_suyo or lo_hace):
        raise Http404('Pedido inexistente')  # como en el detalle: no se revela que existe
    respuesta = {'como_llegar': mapa.como_llegar(pedido.origen, pedido.destino, *mapa.puntos(pedido))}
    try:
        respuesta.update(ok=True, **mapa.recorrido(pedido.origen, pedido.destino, *mapa.puntos(pedido)))
    except mapa.ErrorMapa as e:
        respuesta.update(ok=False, error=str(e))
    return JsonResponse(respuesta)


@requiere_permiso_api('PED_REGISTRAR')
@require_GET
def ubicar_direccion(request):
    """Dónde cae una dirección escrita a mano (JSON), para que el cliente confirme «¿Es acá?»."""
    direccion = ' '.join((request.GET.get('direccion') or '').split())
    if len(direccion) < 5:
        return JsonResponse({'ok': False, 'error': 'Escribí la dirección completa.'}, status=400)
    try:
        return JsonResponse({'ok': True, **mapa.ubicar(direccion[:200])})
    except mapa.ErrorMapa as e:
        return JsonResponse({'ok': False, 'error': str(e)})


@requiere_permiso_api('PED_REGISTRAR')
@require_GET
def direccion_en_mapa(request):
    """La dirección del punto que el cliente tocó en el mapa al cargar el pedido (JSON)."""
    try:
        lat, lon = float(request.GET['lat']), float(request.GET['lon'])
    except (KeyError, ValueError):
        return JsonResponse({'ok': False, 'error': 'Faltan las coordenadas del punto.'}, status=400)
    if not (-56 <= lat <= -21 and -74 <= lon <= -53):  # más o menos, la Argentina
        return JsonResponse({'ok': False, 'error': 'Elegí un punto dentro de la Argentina.'}, status=400)
    try:
        return JsonResponse({'ok': True, 'direccion': mapa.direccion_de(lat, lon)})
    except mapa.ErrorMapa as e:
        return JsonResponse({'ok': False, 'error': str(e)})
