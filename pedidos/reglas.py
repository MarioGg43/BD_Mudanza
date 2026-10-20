"""Reglas del pedido de mudanza (Hito 3).

Las vistas solo arman los datos y muestran el resultado: todo lo que decide si un
pedido es válido, cuánto cuesta y a qué estado pasa vive acá. Cada operación que
escribe corre en una transacción: o se guarda todo, o no se guarda nada.
"""
from datetime import time, timedelta

from django.db import transaction
from django.db.models import Q
from django.utils import timezone

from usuarios.models import DetallePedido, InventarioDetalle, Objeto, Pedido, Servicio, Vehiculo

MAX_DIAS_ADELANTO = 365
MAX_CANTIDAD = 999
MAX_DIRECCION = 200
MAX_OBSERVACION = 200


def tiene_pedidos_activos(**filtro):
    """¿Hay pedidos Pendientes o Confirmados de hoy en adelante? (patente_vehiculo=... o idUsuario=...)"""
    return Pedido.objects.filter(estado__in=Pedido.ACTIVOS, fecha_servicio__gte=timezone.localdate(),
                                 **filtro).exists()


class ErrorPedido(Exception):
    """Errores de validación como {campo: mensaje}; '__all__' es un error general."""

    def __init__(self, errores):
        if isinstance(errores, str):
            errores = {'__all__': errores}
        self.errores = errores
        super().__init__(' '.join(errores.values()))


def vehiculos_libres(fecha):
    """Vehículos en estado Disponible que no tienen otro pedido activo ese día."""
    ocupados = Pedido.objects.filter(fecha_servicio=fecha, estado__in=Pedido.ACTIVOS) \
                             .values('patente_vehiculo')
    return Vehiculo.objects.filter(estado='Disponible').exclude(patente__in=ocupados).order_by('patente')


def _validar_fecha(fecha, errores):
    hoy = timezone.localdate()
    if not fecha:
        errores['fecha_servicio'] = 'Elegí la fecha de la mudanza.'
    elif fecha < hoy:
        errores['fecha_servicio'] = 'La fecha de la mudanza tiene que ser de hoy en adelante.'
    elif fecha > hoy + timedelta(days=MAX_DIAS_ADELANTO):
        errores['fecha_servicio'] = 'Se puede reservar con un año de anticipación como máximo.'


def _validar_hora(fecha, hora, errores):
    if not hora:
        errores['hora_servicio'] = 'Elegí la hora de inicio.'
    elif fecha == timezone.localdate() and hora <= timezone.localtime().time():
        errores['hora_servicio'] = 'Para hoy, elegí una hora que todavía no pasó.'


def _validar_direcciones(origen, destino, errores):
    for campo, valor, nombre in (('origen', origen, 'origen'), ('destino', destino, 'destino')):
        if not valor:
            errores[campo] = f'Escribí la dirección de {nombre}.'
        elif len(valor) > MAX_DIRECCION:
            errores[campo] = f'La dirección de {nombre} puede tener hasta {MAX_DIRECCION} caracteres.'
    if origen and destino and origen.lower() == destino.lower():
        errores['destino'] = 'El destino tiene que ser distinto del origen.'


def _validar_servicios(id_servicio, ids_adicionales, errores):
    """Un servicio principal obligatorio y, opcionales, los adicionales (sin repetir)."""
    principal = None
    if id_servicio is None:
        errores['servicio'] = 'Elegí un servicio.'
    else:
        principal = Servicio.objects.filter(id_servicio=id_servicio, Activo=True,
                                            Categoria=Servicio.PRINCIPAL).first()
        if not principal:
            errores['servicio'] = 'Ese servicio ya no está disponible.'
    ids = list(dict.fromkeys(int(i) for i in ids_adicionales or ()))
    adicionales = list(Servicio.objects.filter(id_servicio__in=ids, Activo=True,
                                               Categoria=Servicio.ADICIONAL).order_by('Tipo_servicio'))
    if len(adicionales) != len(ids):
        errores['adicionales'] = 'Alguno de los adicionales elegidos ya no está disponible.'
    return principal, adicionales


def _validar_items(items, errores):
    """Cada objeto sale del catálogo (OBJETOS): no se escriben nombres, así no hay variantes
    como «mesa» y «meza». Lo que no está en la lista va como «Otro», contado en la observación.
    Un mismo objeto va una sola vez por pedido: si son varios, se suma la cantidad."""
    if not items:
        errores['inventario'] = 'Agregá al menos un objeto.'
        return []
    activos = {o.pk: o for o in Objeto.objects.filter(Activo=True)}
    limpios, vistos = [], set()
    for n, item in enumerate(items, start=1):
        elegido = item.get('objeto')
        objeto = activos.get(getattr(elegido, 'pk', elegido))
        try:
            cantidad = int(item.get('cantidad'))
        except (TypeError, ValueError):
            errores['inventario'] = f'Objeto {n}: la cantidad tiene que ser un número.'
            continue
        observacion = (item.get('observacion') or '').strip()
        if elegido in (None, ''):
            errores['inventario'] = f'Objeto {n}: elegí qué es de la lista.'
        elif objeto is None:
            errores['inventario'] = f'Objeto {n}: ese objeto ya no está en la lista. Elegí otro.'
        elif objeto.es_otro and not observacion:
            errores['inventario'] = f'Objeto {n}: si elegís «Otro», contá en la observación qué es.'
        elif not objeto.es_otro and objeto.pk in vistos:
            errores['inventario'] = f'Ya agregaste «{objeto}»: sumá la cantidad en una sola fila.'
        elif len(observacion) > MAX_OBSERVACION:
            errores['inventario'] = f'Objeto {n}: la observación puede tener hasta {MAX_OBSERVACION} caracteres.'
        elif not 1 <= cantidad <= MAX_CANTIDAD:
            errores['inventario'] = f'Objeto {n}: la cantidad va de 1 a {MAX_CANTIDAD}.'
        else:
            vistos.add(objeto.pk)
            limpios.append({'objeto': objeto, 'cantidad': cantidad,
                            'fragil': bool(item.get('fragil')), 'observacion': observacion or None})
    return limpios


def registrar_pedido(cliente, fecha_servicio, hora_servicio, origen, destino, id_servicio, patente, items,
                     ids_adicionales=()):
    """Registra el pedido completo (cabecera, servicios e inventario) en una sola
    transacción y lo deja Pendiente. Solo el servicio principal tiene precio: los
    adicionales se anotan sin costo. Si algo no es válido lanza ErrorPedido."""
    errores = {}
    origen, destino = (origen or '').strip(), (destino or '').strip()
    _validar_fecha(fecha_servicio, errores)
    _validar_hora(fecha_servicio, hora_servicio, errores)
    _validar_direcciones(origen, destino, errores)
    principal, adicionales = _validar_servicios(id_servicio, ids_adicionales, errores)
    limpios = _validar_items(items, errores)
    if not patente:
        errores['vehiculo'] = 'Elegí un vehículo.'
    if errores:
        raise ErrorPedido(errores)

    with transaction.atomic():
        # Bloquea el vehículo: si dos clientes lo eligen para el mismo día, el segundo espera
        # a que el primero termine y después lo encuentra ocupado.
        # Este bloqueo depende de que la función abra su propia transacción y no haya leído nada
        # antes dentro de ella: quien la llame no debe envolverla en un atomic() externo que lea primero.
        vehiculo = Vehiculo.objects.select_for_update().filter(patente=patente).first()
        if not vehiculo or not vehiculos_libres(fecha_servicio).filter(patente=patente).exists():
            raise ErrorPedido({'vehiculo': 'Ese vehículo no está libre para esa fecha. Elegí otro.'})

        pedido = Pedido.objects.create(
            patente_vehiculo=vehiculo, idUsuario=cliente, Fecha_pedido=timezone.localdate(),
            fecha_servicio=fecha_servicio, hora_servicio=hora_servicio, origen=origen, destino=destino,
            estado=Pedido.PENDIENTE, total=principal.Precio_base)
        # Una fila por servicio. El principal guarda el precio del día (si después cambia, el
        # pedido no cambia); los adicionales van en 0 porque no tienen precio.
        DetallePedido.objects.bulk_create(
            [DetallePedido(idPedido=pedido, idServicio=principal,
                           precio_unitario=principal.Precio_base, subtotal=principal.Precio_base)]
            + [DetallePedido(idPedido=pedido, idServicio=s, precio_unitario=0, subtotal=0) for s in adicionales])
        InventarioDetalle.objects.bulk_create([
            InventarioDetalle(idPedido=pedido, idObjeto=i['objeto'], Cantidad=i['cantidad'],
                              Fragil=i['fragil'], Observacion=i['observacion'])
            for i in limpios])
    return pedido


# acción: (estados desde los que se puede, estado al que pasa)
TRANSICIONES = {
    'confirmar': ((Pedido.PENDIENTE,), Pedido.CONFIRMADO),
    'finalizar': ((Pedido.CONFIRMADO,), Pedido.FINALIZADO),
    'anular': (Pedido.ACTIVOS, Pedido.ANULADO),
}


def _pasar_a(id_pedido, accion):
    """Bloquea el pedido y le cambia el estado en memoria; el que llama guarda."""
    desde, hacia = TRANSICIONES[accion]
    pedido = Pedido.objects.select_for_update().get(pk=id_pedido)
    if pedido.estado not in desde:
        raise ErrorPedido(f'No se puede {accion} un pedido en estado {pedido.estado}.')
    pedido.estado = hacia
    return pedido


VENCIDO = 'Vencido'  # no es un estado guardado: es un Pendiente cuya fecha y hora ya pasaron


def filtro_vencidos():
    """Pendientes cuya mudanza ya debía haber empezado."""
    ahora = timezone.localtime()
    return Q(estado=Pedido.PENDIENTE) & (Q(fecha_servicio__lt=ahora.date())
                                         | Q(fecha_servicio=ahora.date(), hora_servicio__lte=ahora.time()))


def confirmar(id_pedido):
    """Un pedido vencido no se confirma: la fecha ya pasó, se anula."""
    with transaction.atomic():
        pedido = _pasar_a(id_pedido, 'confirmar')
        if pedido.ya_empezo:
            raise ErrorPedido('La fecha y hora de la mudanza ya pasaron sin confirmar: el pedido está vencido. '
                              'Anulalo y, si el cliente quiere, que pida una fecha nueva.')
        pedido.save(update_fields=['estado'])
    return pedido


def finalizar(id_pedido):
    """Solo se finaliza una mudanza que ya empezó (desde su fecha y hora de inicio)."""
    with transaction.atomic():
        pedido = _pasar_a(id_pedido, 'finalizar')
        if not pedido.ya_empezo:
            inicio = timezone.localtime(pedido.inicio)
            raise ErrorPedido(f'La mudanza todavía no empezó: se puede finalizar desde el '
                              f'{inicio:%d/%m/%Y} a las {inicio:%H:%M}.')
        pedido.save(update_fields=['estado'])
    return pedido


def anular(id_pedido, usuario, motivo):
    """Anula sin borrar: guarda fecha, motivo y usuario. Como un pedido anulado ya no
    cuenta como activo, el vehículo vuelve a estar libre ese día."""
    motivo = (motivo or '').strip()
    if not 5 <= len(motivo) <= 200:
        raise ErrorPedido({'motivo': 'El motivo tiene que tener entre 5 y 200 caracteres.'})
    with transaction.atomic():
        pedido = _pasar_a(id_pedido, 'anular')
        pedido.fecha_anulacion = timezone.now()
        pedido.motivo_anulacion = motivo
        pedido.usuario_anulacion = usuario
        pedido.save(update_fields=['estado', 'fecha_anulacion', 'motivo_anulacion', 'usuario_anulacion'])
    return pedido


def filtrar_pedidos(pedidos, desde=None, hasta=None, estado=None, id_servicio=None, id_cliente=None, patente=None):
    """Filtros de la consulta. Las fechas son de la mudanza (fecha_servicio)."""
    if desde:
        pedidos = pedidos.filter(fecha_servicio__gte=desde)
    if hasta:
        pedidos = pedidos.filter(fecha_servicio__lte=hasta)
    if estado == VENCIDO:
        pedidos = pedidos.filter(filtro_vencidos())
    elif estado:
        pedidos = pedidos.filter(estado=estado)
    if id_servicio:
        pedidos = pedidos.filter(detalles__idServicio_id=id_servicio)
    if id_cliente:
        pedidos = pedidos.filter(idUsuario_id=id_cliente)
    if patente:
        pedidos = pedidos.filter(patente_vehiculo_id=patente)
    return (pedidos.distinct()
            .select_related('idUsuario', 'patente_vehiculo')
            .prefetch_related('detalles__idServicio')
            .order_by('-id_pedido'))
