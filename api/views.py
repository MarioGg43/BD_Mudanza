"""Controladores REST que consume el frontend en React (carpeta frontend/).

Responden JSON y usan las mismas reglas que las pantallas de Django (pedidos/reglas.py): la API
solo traduce entre JSON y esas funciones, no repite ninguna regla."""
from datetime import date, time
from urllib.parse import quote

from django.http import Http404
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.utils import timezone

from pedidos import reglas
from pedidos.forms import FiltroPedidosForm, RegistroClienteForm, objetos_para_elegir
from pedidos.pdf import respuesta_pdf
from usuarios.models import Pedido, PersonalPedido, Servicio, Usuario, Vehiculo
from usuarios import operaciones
from usuarios.permisos import tiene_permiso
from .autenticacion import crear_token, datos_usuario, endpoint, error, leer_json, publico


# ------------------------------------------------------------------ autenticación

@publico()
def login(request):
    """POST /api/auth/login {usuario, clave} → {token, usuario}. Acepta DNI, usuario o correo."""
    datos = leer_json(request)
    ident, clave = str(datos.get('usuario', '')).strip(), str(datos.get('clave', ''))
    if not ident or not clave:
        return error('Completá el usuario y la clave.')
    usuario = _buscar(ident)
    if not usuario or not usuario.verificar_clave(clave):
        return error('Usuario o contraseña incorrectos.', 401)
    if not usuario.Activo:
        return error('El usuario está dado de baja.', 403)
    if usuario.DebeCambiarClave:
        # React muestra el formulario para elegir la clave nueva (POST /auth/cambiar-clave)
        return error('Tu clave es provisoria: elegí una nueva para entrar.', 403,
                     errores={'cambiar_clave': 'Tenés que elegir una clave nueva.'})
    usuario.registrar_acceso()
    return JsonResponse({'token': crear_token(usuario), 'usuario': datos_usuario(usuario)})


def _buscar(ident):
    """El usuario por DNI, nombre de usuario o correo (igual que el login de Django)."""
    usuario = Usuario.objects.filter(DNI=int(ident)).first() if ident.isdigit() else None
    return (usuario or Usuario.objects.filter(NombreUsuario=ident.lower()).first()
            or Usuario.objects.filter(Correo=ident.lower()).first())


@publico()
def cambiar_clave(request):
    """POST /api/auth/cambiar-clave {usuario, clave, nueva, confirmar}: reemplaza la clave provisoria
    y entra. Las reglas son las de usuarios/operaciones.py, las mismas que el login de Django."""
    d = leer_json(request)
    usuario = _buscar(str(d.get('usuario', '')).strip())
    # sin revelar si el usuario existe: el mismo mensaje que una clave incorrecta
    if not usuario or not usuario.verificar_clave(str(d.get('clave', ''))):
        return error('Usuario o contraseña incorrectos.', 401)
    try:
        operaciones.cambiar_clave_provisoria(usuario, str(d.get('clave', '')), str(d.get('nueva', '')),
                                             str(d.get('confirmar', '')))
    except operaciones.ErrorUsuario as e:
        return error(str(e), e.status, errores={'nueva': str(e)} if e.status == 400 else None)
    usuario.registrar_acceso()
    return JsonResponse({'token': crear_token(usuario), 'usuario': datos_usuario(usuario)})


@publico()
def registro(request):
    """POST /api/auth/registro: alta de cliente (mismas validaciones que la pantalla) y login."""
    form = RegistroClienteForm(leer_json(request))
    if not form.is_valid():
        return error('Revisá los datos marcados.', errores={k: ' '.join(v) for k, v in form.errors.items()})
    cliente = form.crear_cliente()
    cliente.registrar_acceso()
    return JsonResponse({'token': crear_token(cliente), 'usuario': datos_usuario(cliente)}, status=201)


@publico()
def recuperar_clave(request):
    """POST /api/auth/recuperar-clave {dni, correo, nueva, confirmar}: «Olvidé mi contraseña» para
    clientes. Si el DNI y el correo coinciden, guarda la clave nueva y entra."""
    d = leer_json(request)
    try:
        usuario = operaciones.recuperar_clave_cliente(str(d.get('dni', '')).strip(), str(d.get('correo', '')),
                                                      str(d.get('nueva', '')), str(d.get('confirmar', '')))
    except operaciones.ErrorUsuario as e:
        return error(str(e), e.status)
    usuario.registrar_acceso()
    return JsonResponse({'token': crear_token(usuario), 'usuario': datos_usuario(usuario)})


@endpoint()
def yo(request):
    """GET /api/auth/yo: comprueba que el token sigue valiendo y devuelve el usuario."""
    return JsonResponse({'usuario': datos_usuario(request.usuario)})


# ------------------------------------------------------------------ página de inicio (pública)

@publico(metodos=('GET',))
def publico_info(request):
    """GET /api/publico: lo que muestra la página de inicio sin iniciar sesión: los servicios
    activos con su precio y los tamaños de camión con su capacidad y recargo."""
    activos = Servicio.objects.filter(Activo=True).order_by('Precio_base')
    camiones = []
    for tipo in Vehiculo.TIPOS:
        flota = Vehiculo.objects.filter(tipo_vehiculo=tipo).exclude(estado='Fuera de Servicio')
        if flota.exists():
            camiones.append({'tipo': tipo, 'recargo': Vehiculo.RECARGOS[tipo], 'cantidad': flota.count(),
                             'capacidad_kg': float(max(v.capacidad_kg for v in flota)),
                             'capacidad_m3': float(max(v.capacidad_m3 for v in flota))})
    return JsonResponse({
        'principales': [_servicio(s) for s in activos.filter(Categoria=Servicio.PRINCIPAL)],
        'adicionales': [_servicio(s) for s in activos.filter(Categoria=Servicio.ADICIONAL)],
        'camiones': camiones,
        'horas_limite': reglas.HORAS_LIMITE_CLIENTE,
    })


# ------------------------------------------------------------------ catálogo

def _servicio(s):
    return {'id': s.id_servicio, 'nombre': s.Tipo_servicio, 'precio': float(s.Precio_base),
            'horas': s.Duracion_horas or reglas.MIN_HORAS}


@endpoint('PED_REGISTRAR')
def catalogo(request):
    """GET /api/catalogo: lo que hace falta para armar el formulario de pedido."""
    activos = Servicio.objects.filter(Activo=True).order_by('Tipo_servicio')
    return JsonResponse({
        'principales': [_servicio(s) for s in activos.filter(Categoria=Servicio.PRINCIPAL)],
        'adicionales': [_servicio(s) for s in activos.filter(Categoria=Servicio.ADICIONAL)],
        # la clave es la de reglas.clave_objeto: React la usa para avisar mientras se escribe
        'objetos': [{'id': o.pk, 'nombre': o.nom_objeto, 'clave': reglas.clave_objeto(o.nom_objeto), 'otro': o.es_otro}
                    for o in objetos_para_elegir()],
        'max_cantidad': reglas.MAX_CANTIDAD,
        'horas_limite': reglas.HORAS_LIMITE_CLIENTE,
    })


@endpoint('PED_REGISTRAR')
def vehiculos_libres(request):
    """GET /api/vehiculos-libres?fecha=&hora=&servicio=[&pedido=]"""
    try:
        fecha = date.fromisoformat(request.GET.get('fecha', ''))
        hora = time.fromisoformat(request.GET.get('hora', ''))
    except ValueError:
        return JsonResponse({'vehiculos': [], 'motivo': 'Elegí la fecha y la hora.'})
    servicio = Servicio.objects.filter(pk=request.GET.get('servicio') or None, Activo=True,
                                       Categoria=Servicio.PRINCIPAL).first()
    if not servicio:
        return JsonResponse({'vehiculos': [], 'motivo': 'Elegí el servicio para ver los vehículos libres.'})
    propio = Pedido.objects.filter(pk=request.GET.get('pedido') or None, idUsuario=request.usuario).first()
    libres = [{'patente': v.patente, 'tipo': v.tipo_vehiculo, 'modelo': v.marca_modelo, 'recargo': v.recargo,
               'capacidad_kg': float(v.capacidad_kg), 'capacidad_m3': float(v.capacidad_m3)}
              for v in reglas.vehiculos_libres(reglas.inicio_de(fecha, hora),
                                               servicio.Duracion_horas or reglas.MIN_HORAS, propio)]
    return JsonResponse({'vehiculos': libres, 'motivo': '' if libres else reglas.motivo_sin_vehiculos()})


# ------------------------------------------------------------------ pedidos

def _fecha_hora(dt):
    return timezone.localtime(dt).strftime('%Y-%m-%dT%H:%M') if dt else None


def _resumen(p):
    return {'id': p.id_pedido, 'fecha_servicio': p.fecha_servicio.isoformat(),
            'hora_servicio': p.hora_servicio.strftime('%H:%M'), 'horario': p.horario,
            'origen': p.origen, 'destino': p.destino, 'estado': p.estado, 'total': float(p.total),
            'vencido': p.vencido, 'en_curso': p.en_curso, 'vehiculo': p.patente_vehiculo_id,
            'vehiculo_tipo': p.patente_vehiculo.tipo_vehiculo,
            'cliente': f'{p.idUsuario.Apellido}, {p.idUsuario.Nombre}'}


def _detalle(p, usuario):
    personal = list(p.personal.select_related('idUsuario'))
    chofer = next((x.idUsuario for x in personal if x.Funcion == PersonalPedido.CHOFER), None)
    ultima = p.reprogramaciones.first()
    es_mio = p.idUsuario_id == usuario.id_usuario
    return {
        **_resumen(p),
        'duracion_horas': p.duracion_horas, 'fecha_pedido': p.Fecha_pedido.isoformat(),
        'inicio_real': _fecha_hora(p.inicio_real), 'fin_real': _fecha_hora(p.fin_real),
        'vehiculo_modelo': p.patente_vehiculo.marca_modelo, 'vehiculo_tipo': p.patente_vehiculo.tipo_vehiculo,
        'cliente_datos': {'dni': p.idUsuario.DNI, 'correo': p.idUsuario.Correo},
        'chofer': f'{chofer.Nombre} {chofer.Apellido}' if chofer else None,
        'recargo': float(p.recargo), 'motivo_recargo': p.motivo_recargo,
        'anulacion': {'fecha': _fecha_hora(p.fecha_anulacion), 'motivo': p.motivo_anulacion,
                      'por': f'{p.usuario_anulacion.Nombre} {p.usuario_anulacion.Apellido}'}
        if p.estado == Pedido.ANULADO and p.usuario_anulacion else None,
        'servicios': [{'id': d.idServicio_id, 'nombre': d.idServicio.Tipo_servicio,
                       'adicional': d.idServicio.Categoria == Servicio.ADICIONAL,
                       'precio': float(d.precio_unitario), 'subtotal': float(d.subtotal)} for d in p.detalles.all()],
        'inventario': [{'objeto': i.idObjeto_id, 'nombre': i.idObjeto.nom_objeto, 'otro': i.idObjeto.es_otro,
                        'cantidad': i.Cantidad, 'declarada': i.cantidad_declarada, 'fragil': i.Fragil,
                        'observacion': i.Observacion or ''} for i in p.inventario.all()],
        'ultimo_cambio': {'fecha_anterior': ultima.fecha_anterior.isoformat(),
                          'hora_anterior': ultima.hora_anterior.strftime('%H:%M'),
                          'fecha_nueva': ultima.fecha_nueva.isoformat(), 'hora_nueva': ultima.hora_nueva.strftime('%H:%M'),
                          'motivo': ultima.motivo_completo, 'nuevo': not ultima.visto_cliente,
                          'vehiculo_nuevo': ultima.vehiculo_nuevo_id
                          if ultima.vehiculo_nuevo_id != ultima.vehiculo_anterior_id else None} if ultima else None,
        'es_mio': es_mio,
        'puede_cambiar': es_mio and reglas.cliente_puede_cambiar(p),
        'puede_comprobante': tiene_permiso(usuario, 'PED_COMPROBANTE'),
        'gestion': _gestion(p, usuario, personal) if tiene_permiso(usuario, 'PED_GESTIONAR') else None,
    }


def _persona(u):
    return {'id': u.id_usuario, 'nombre': f'{u.Nombre} {u.Apellido}'}


def _gestion(p, usuario, personal):
    """Lo que solo ve el administrador en el detalle: cliente, personal, acciones posibles,
    historial de cambios de horario y los avisos de mudanza atrasada."""
    activo = p.estado in Pedido.ACTIVOS
    chofer = next((x.idUsuario for x in personal if x.Funcion == PersonalPedido.CHOFER), None)
    reprogramaciones = list(p.reprogramaciones.select_related('usuario'))
    whatsapp = ''
    if reprogramaciones and activo:
        telefono = reglas.telefono_whatsapp(p.idUsuario.Telefono)
        if telefono:
            whatsapp = f'https://wa.me/{telefono}?text={quote(reglas.mensaje_reprogramacion(reprogramaciones[0]))}'
    atrasadas = reglas.mudanzas_atrasadas()
    siguiente = atrasadas.get(p)
    anterior = next((a for a, q in atrasadas.items() if q.pk == p.pk), None)
    inicio = timezone.localtime(p.inicio)
    return {
        'cliente': {'nombre': f'{p.idUsuario.Nombre} {p.idUsuario.Apellido}', 'dni': p.idUsuario.DNI,
                    'correo': p.idUsuario.Correo, 'telefono': p.idUsuario.Telefono or ''},
        'chofer': _persona(chofer) if chofer else None,
        'ayudantes': [_persona(x.idUsuario) for x in personal if x.Funcion == PersonalPedido.AYUDANTE],
        'inicio': inicio.strftime('%d/%m/%Y a las %H:%M'),
        'puede_asignar': activo and not p.ya_empezo,
        'puede_confirmar': p.estado == Pedido.PENDIENTE and not p.vencido,
        'puede_finalizar': p.estado == Pedido.CONFIRMADO and p.ya_empezo,
        'espera_para_finalizar': p.estado == Pedido.CONFIRMADO and not p.ya_empezo,
        'puede_reprogramar': activo,
        'puede_editar_servicios': activo,
        'puede_anular': activo and tiene_permiso(usuario, 'PED_ANULAR'),
        'reprogramaciones': [{
            'antes': f'{r.fecha_anterior:%d/%m/%Y} {r.hora_anterior:%H:%M}',
            'despues': f'{r.fecha_nueva:%d/%m/%Y} {r.hora_nueva:%H:%M}',
            'vehiculo': f'{r.vehiculo_anterior_id} → {r.vehiculo_nuevo_id}'
            if r.vehiculo_nuevo_id != r.vehiculo_anterior_id else None,
            'motivo': r.motivo_completo, 'por': f'{r.usuario.Nombre} {r.usuario.Apellido}',
            'cuando': timezone.localtime(r.fecha_registro).strftime('%d/%m/%Y %H:%M'),
            'visto': r.visto_cliente} for r in reprogramaciones],
        'whatsapp': whatsapp,
        # esta mudanza ya debía terminar y otra la espera / la anterior a esta está atrasada
        'atrasada': {'id': siguiente.pk, 'hora': timezone.localtime(siguiente.inicio).strftime('%d/%m %H:%M'),
                     'ya_empezo': siguiente.ya_empezo, 'comparte': reglas.que_comparten(p, siguiente),
                     'fin': timezone.localtime(p.fin).strftime('%H:%M')} if siguiente else None,
        'anterior': {'id': anterior.pk, 'comparte': reglas.que_comparten(anterior, p),
                     'fin': timezone.localtime(anterior.fin).strftime('%H:%M')} if anterior else None,
    }


def _pedido_visible(request, id_pedido):
    """Un pedido ajeno da 404 y no 403, para no revelar que existe (igual que la pantalla)."""
    pedido = get_object_or_404(
        Pedido.objects.select_related('idUsuario', 'patente_vehiculo', 'usuario_anulacion')
                      .prefetch_related('detalles__idServicio', 'inventario__idObjeto'), pk=id_pedido)
    if not tiene_permiso(request.usuario, 'PED_GESTIONAR') and pedido.idUsuario_id != request.usuario.id_usuario:
        raise Http404('Pedido inexistente')
    return pedido


def _datos_pedido(d):
    """Convierte el JSON del formulario a lo que piden registrar_pedido y modificar_pedido.
    Los tipos mal escritos quedan como None y las reglas dicen qué falta."""
    def a_fecha(v):
        try:
            return date.fromisoformat(v)
        except (TypeError, ValueError):
            return None

    def a_hora(v):
        try:
            return time.fromisoformat(v)
        except (TypeError, ValueError):
            return None

    def a_entero(v):
        try:
            return int(v)
        except (TypeError, ValueError):
            return None

    items = d.get('inventario') if isinstance(d.get('inventario'), list) else []
    items = [{'objeto': a_entero(i.get('objeto')), 'cantidad': i.get('cantidad'), 'fragil': bool(i.get('fragil')),
              'observacion': str(i.get('observacion') or '')} for i in items if isinstance(i, dict)]
    adicionales = [a for a in (a_entero(x) for x in d.get('adicionales') or []) if a is not None]
    return ((a_fecha(d.get('fecha_servicio')), a_hora(d.get('hora_servicio')), str(d.get('origen') or ''),
             str(d.get('destino') or ''), a_entero(d.get('servicio')), str(d.get('vehiculo') or ''), items),
            adicionales)


@endpoint('PED_CONSULTAR', metodos=('GET', 'POST'))
def pedidos(request):
    """GET /api/pedidos[?estado=&desde=&hasta=]: los pedidos del cliente (o todos si gestiona).
    POST /api/pedidos: registra un pedido (necesita PED_REGISTRAR)."""
    if request.method == 'POST':
        if not tiene_permiso(request.usuario, 'PED_REGISTRAR'):
            return error('No tenés permiso para esta operación.', 403)
        datos, adicionales = _datos_pedido(leer_json(request))
        try:
            pedido = reglas.registrar_pedido(request.usuario, *datos, ids_adicionales=adicionales)
        except reglas.ErrorPedido as e:
            return error('Revisá los datos marcados.', errores=e.errores)
        return JsonResponse({'id': pedido.id_pedido}, status=201)

    ve_todos = tiene_permiso(request.usuario, 'PED_GESTIONAR')
    base = Pedido.objects.all() if ve_todos else Pedido.objects.filter(idUsuario=request.usuario)
    form = FiltroPedidosForm(request.GET or None, ve_todos=ve_todos)
    filtros = form.filtros() if form.is_valid() else {}
    lista = reglas.filtrar_pedidos(base.select_related('idUsuario', 'patente_vehiculo'), **filtros)
    if not ve_todos:
        return JsonResponse({'pedidos': [_resumen(p) for p in lista]})
    # el administrador ve además los avisos y si cada pedido tiene chofer o está atrasado
    atrasadas = {p.pk for p in reglas.mudanzas_atrasadas()}
    filas = []
    for p in lista.prefetch_related('personal'):
        fila = _resumen(p)
        fila['atrasada'] = p.pk in atrasadas
        fila['tiene_chofer'] = any(x.Funcion == PersonalPedido.CHOFER for x in p.personal.all())
        filas.append(fila)
    return JsonResponse({'pedidos': filas, 'avisos': reglas.contar_avisos(),
                         'errores_filtro': {k: ' '.join(v) for k, v in form.errors.items()}})


@endpoint('PED_CONSULTAR', metodos=('GET', 'PUT'))
def pedido(request, id_pedido):
    """GET /api/pedidos/<id>: el detalle. PUT: el cliente lo modifica hasta 24 h antes."""
    if request.method == 'PUT':
        if not tiene_permiso(request.usuario, 'PED_REGISTRAR'):
            return error('No tenés permiso para esta operación.', 403)
        get_object_or_404(Pedido, pk=id_pedido, idUsuario=request.usuario)
        datos, adicionales = _datos_pedido(leer_json(request))
        try:
            reglas.modificar_pedido(id_pedido, request.usuario, *datos, ids_adicionales=adicionales)
        except reglas.ErrorPedido as e:
            return error('Revisá los datos marcados.', errores=e.errores)
        return JsonResponse({'id': id_pedido})

    p = _pedido_visible(request, id_pedido)
    respuesta = _detalle(p, request.usuario)
    # al cliente que abre su pedido, el cambio de horario le queda como visto (igual que la pantalla)
    if respuesta['es_mio']:
        p.reprogramaciones.filter(visto_cliente=False).update(visto_cliente=True)
    return JsonResponse(respuesta)


@endpoint('PED_CONSULTAR', metodos=('POST',))
def cancelar(request, id_pedido):
    """POST /api/pedidos/<id>/cancelar {motivo}: el cliente cancela hasta 24 h antes."""
    get_object_or_404(Pedido, pk=id_pedido, idUsuario=request.usuario)
    motivo = str(leer_json(request).get('motivo') or '').strip()
    if not 5 <= len(motivo) <= 200:
        return error('Revisá los datos marcados.', errores={'motivo': 'Contá el motivo (de 5 a 200 caracteres).'})
    try:
        reglas.cancelar_por_cliente(id_pedido, request.usuario, motivo)
    except reglas.ErrorPedido as e:
        return error(str(e), errores=e.errores)
    return JsonResponse({'id': id_pedido, 'estado': Pedido.ANULADO})


@endpoint('PED_COMPROBANTE')
def comprobante(request, id_pedido):
    """GET /api/pedidos/<id>/comprobante: el PDF (React lo baja con el token)."""
    p = _pedido_visible(request, id_pedido)
    return respuesta_pdf(request, 'pedidos/comprobante_pdf.html', {'pedido': p, 'emitido': timezone.localtime()},
                         f'Comprobante-pedido-{p.id_pedido}.pdf')
