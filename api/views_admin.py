"""Controladores REST del administrador: lo que en Django hacen las pantallas de gestión de pedidos
(confirmar, finalizar, anular, asignar personal, editar servicios y reprogramar). Igual que en
views.py, cada uno solo traduce JSON y llama a pedidos/reglas.py."""
from datetime import date, time

from django.http import JsonResponse
from django.shortcuts import get_object_or_404

from pedidos import reglas
from usuarios.models import Pedido, PersonalPedido, Reprogramacion, Servicio, Usuario, Vehiculo
from .autenticacion import endpoint, error, leer_json
from .views import _persona, _servicio


def _respuesta_error(e):
    return error(str(e) if '__all__' in e.errores else 'Revisá los datos marcados.', errores=e.errores)


def _entero(valor):
    try:
        return int(valor)
    except (TypeError, ValueError):
        return None


@endpoint('PED_GESTIONAR')
def opciones(request):
    """GET /api/admin/opciones: las listas de los filtros de la consulta de pedidos."""
    return JsonResponse({
        'estados': [e for e, _ in Pedido.ESTADOS],
        'avisos': list(reglas.AVISOS),
        'clientes': [{'id': u.id_usuario, 'nombre': f'{u.Apellido}, {u.Nombre}'} for u in
                     Usuario.objects.filter(idRol__nom_rol='Cliente').order_by('Apellido', 'Nombre')],
        'vehiculos': list(Vehiculo.objects.order_by('patente').values_list('patente', flat=True)),
        'servicios': [{'id': s.id_servicio, 'nombre': s.Tipo_servicio} for s in Servicio.objects.order_by('Tipo_servicio')],
    })


# ------------------------------------------------------------------ cambios de estado

def _cambiar_estado(id_pedido, funcion, estado):
    get_object_or_404(Pedido, pk=id_pedido)
    try:
        funcion(id_pedido)
    except reglas.ErrorPedido as e:
        return _respuesta_error(e)
    return JsonResponse({'id': id_pedido, 'estado': estado})


@endpoint('PED_GESTIONAR', metodos=('POST',))
def confirmar(request, id_pedido):
    """POST /api/pedidos/<id>/confirmar (hace falta el chofer asignado)."""
    return _cambiar_estado(id_pedido, reglas.confirmar, Pedido.CONFIRMADO)


@endpoint('PED_GESTIONAR', metodos=('POST',))
def finalizar(request, id_pedido):
    """POST /api/pedidos/<id>/finalizar (desde que empezó la mudanza)."""
    return _cambiar_estado(id_pedido, reglas.finalizar, Pedido.FINALIZADO)


@endpoint('PED_ANULAR', metodos=('POST',))
def anular(request, id_pedido):
    """POST /api/pedidos/<id>/anular {motivo}"""
    get_object_or_404(Pedido, pk=id_pedido)
    try:
        reglas.anular(id_pedido, request.usuario, str(leer_json(request).get('motivo') or ''))
    except reglas.ErrorPedido as e:
        return _respuesta_error(e)
    return JsonResponse({'id': id_pedido, 'estado': Pedido.ANULADO})


# ------------------------------------------------------------------ personal

@endpoint('PED_GESTIONAR', metodos=('GET', 'PUT'))
def personal(request, id_pedido):
    """GET /api/pedidos/<id>/personal: choferes y ayudantes libres en el horario del pedido.
    PUT {chofer, ayudantes}: asigna el personal (reemplaza al anterior)."""
    pedido = get_object_or_404(Pedido.objects.select_related('patente_vehiculo__chofer_asignado'), pk=id_pedido)
    if request.method == 'PUT':
        datos = leer_json(request)
        try:
            reglas.asignar_personal(id_pedido, _entero(datos.get('chofer')),
                                    [i for i in map(_entero, datos.get('ayudantes') or []) if i])
        except reglas.ErrorPedido as e:
            return _respuesta_error(e)
        return JsonResponse({'id': id_pedido})

    if pedido.estado not in Pedido.ACTIVOS or pedido.ya_empezo:
        return error(f'El pedido N° {id_pedido} ya no admite cambios de personal.')
    actual = list(pedido.personal.all())
    chofer = next((x.idUsuario_id for x in actual if x.Funcion == PersonalPedido.CHOFER), None)
    choferes = reglas.personal_libre(pedido, reglas.ROL_CHOFER)
    # si todavía no tiene chofer, se sugiere el habitual del vehículo (si está libre)
    habitual = pedido.patente_vehiculo.chofer_asignado
    sugerido = habitual.pk if not chofer and habitual and choferes.filter(pk=habitual.pk).exists() else None
    return JsonResponse({
        'choferes': [_persona(u) for u in choferes],
        'ayudantes': [_persona(u) for u in reglas.personal_libre(pedido, reglas.ROL_AYUDANTE)],
        'chofer': chofer, 'sugerido': sugerido,
        'elegidos': [x.idUsuario_id for x in actual if x.Funcion == PersonalPedido.AYUDANTE],
        'max_ayudantes': reglas.MAX_AYUDANTES,
    })


# ------------------------------------------------------------------ servicios

@endpoint('PED_GESTIONAR', metodos=('GET', 'PUT'))
def servicios(request, id_pedido):
    """GET /api/pedidos/<id>/servicios: los servicios activos y los del pedido.
    PUT {servicio, adicionales}: los cambia y recalcula el total."""
    pedido = get_object_or_404(Pedido.objects.select_related('patente_vehiculo'), pk=id_pedido)
    if request.method == 'PUT':
        datos = leer_json(request)
        try:
            reglas.editar_servicios(id_pedido, _entero(datos.get('servicio')),
                                    [i for i in map(_entero, datos.get('adicionales') or []) if i])
        except reglas.ErrorPedido as e:
            return _respuesta_error(e)
        return JsonResponse({'id': id_pedido})

    if pedido.estado not in Pedido.ACTIVOS:
        return error(f'El pedido N° {id_pedido} está {pedido.estado.lower()}: no se pueden cambiar los servicios.')
    activos = Servicio.objects.filter(Activo=True).order_by('Tipo_servicio')
    detalles = list(pedido.detalles.select_related('idServicio'))
    return JsonResponse({
        'principales': [_servicio(s) for s in activos.filter(Categoria=Servicio.PRINCIPAL)],
        'adicionales': [_servicio(s) for s in activos.filter(Categoria=Servicio.ADICIONAL)],
        'servicio': next((d.idServicio_id for d in detalles if d.idServicio.Categoria == Servicio.PRINCIPAL), None),
        'elegidos': [d.idServicio_id for d in detalles if d.idServicio.Categoria == Servicio.ADICIONAL],
        'recargo': pedido.patente_vehiculo.recargo,
    })


# ------------------------------------------------------------------ reprogramar

@endpoint('PED_GESTIONAR', metodos=('GET', 'POST'))
def reprogramar(request, id_pedido):
    """GET /api/pedidos/<id>/reprogramar[?fecha=&hora=]: motivos, choferes y los vehículos libres en
    ese horario. POST {fecha_servicio, hora_servicio, vehiculo, motivo, observacion, chofer,
    quitar_ocupados}: lo reprograma y devuelve el enlace para avisarle al cliente por WhatsApp."""
    pedido = get_object_or_404(Pedido.objects.select_related('idUsuario'), pk=id_pedido)
    if pedido.estado not in Pedido.ACTIVOS:
        return error(f'El pedido N° {id_pedido} está {pedido.estado.lower()}: no se puede reprogramar.')

    if request.method == 'POST':
        d = leer_json(request)
        try:
            fecha = date.fromisoformat(str(d.get('fecha_servicio')))
        except ValueError:
            fecha = None
        try:
            hora = time.fromisoformat(str(d.get('hora_servicio')))
        except ValueError:
            hora = None
        try:
            reglas.reprogramar(id_pedido, request.usuario, fecha, hora, str(d.get('vehiculo') or ''),
                               str(d.get('motivo') or ''), str(d.get('observacion') or ''),
                               bool(d.get('quitar_ocupados')), id_chofer=_entero(d.get('chofer')))
        except reglas.ErrorPedido as e:
            return _respuesta_error(e)
        return JsonResponse({'id': id_pedido})

    vehiculos = Vehiculo.objects.filter(estado='Disponible').order_by('patente')
    motivo_libres = ''
    try:
        inicio = reglas.inicio_de(date.fromisoformat(request.GET.get('fecha', '')),
                                  time.fromisoformat(request.GET.get('hora', '')))
    except ValueError:
        inicio = None
    if inicio:
        vehiculos = reglas.vehiculos_libres(inicio, pedido.duracion_horas, pedido)
        if not vehiculos.exists():
            motivo_libres = reglas.motivo_sin_vehiculos()
    actual = list(pedido.personal.select_related('idUsuario'))
    return JsonResponse({
        'fecha_servicio': pedido.fecha_servicio.isoformat(), 'hora_servicio': pedido.hora_servicio.strftime('%H:%M'),
        'vehiculo': pedido.patente_vehiculo_id, 'duracion_horas': pedido.duracion_horas,
        'personal': [f'{x.idUsuario.Nombre} {x.idUsuario.Apellido} ({x.get_Funcion_display().lower()})' for x in actual],
        'motivos': [m for m, _ in Reprogramacion.MOTIVOS],
        'choferes': [_persona(u) for u in Usuario.objects.filter(Activo=True, idRol__nom_rol=reglas.ROL_CHOFER)
                     .order_by('Apellido', 'Nombre')],
        'vehiculos': [{'patente': v.patente, 'tipo': v.tipo_vehiculo, 'modelo': v.marca_modelo} for v in vehiculos],
        'motivo_sin_vehiculos': motivo_libres,
    })
