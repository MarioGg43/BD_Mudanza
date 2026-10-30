"""Reglas del pedido de mudanza (Hito 3).

Las vistas solo arman los datos y muestran el resultado: todo lo que decide si un
pedido es válido, cuánto cuesta y a qué estado pasa vive acá. Cada operación que
escribe corre en una transacción: o se guarda todo, o no se guarda nada.
"""
import re
import unicodedata
from datetime import datetime, time, timedelta
from decimal import Decimal

from django.db import transaction
from django.db.models import Q
from django.utils import timezone

from usuarios.models import (DetallePedido, InventarioDetalle, Objeto, Pedido, PersonalPedido, Reprogramacion,
                             Servicio, Usuario, Vehiculo)

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


# Duración estimada de un servicio principal, en horas (de 5 horas a 5 días)
MIN_HORAS, MAX_HORAS = 5, 120


def inicio_de(fecha, hora):
    """Fecha y hora de inicio con zona horaria, igual que Pedido.inicio."""
    return timezone.make_aware(datetime.combine(fecha, hora))


def pedidos_que_se_cruzan(inicio, horas, excluir=None):
    """Pedidos activos cuyo horario se superpone con [inicio, inicio + horas).
    Uno que termina justo cuando empieza el otro no se cruza. Un pendiente vencido no
    ocupa nada: nadie lo confirmó y su hora ya pasó."""
    fin = inicio + timedelta(hours=horas)
    # Solo pueden cruzarse los que empiezan entre MAX_HORAS antes y el fin del nuevo
    desde = timezone.localtime(inicio - timedelta(hours=MAX_HORAS)).date()
    hasta = timezone.localtime(fin).date()
    cerca = Pedido.objects.filter(estado__in=Pedido.ACTIVOS, fecha_servicio__range=(desde, hasta)) \
                          .exclude(filtro_vencidos())
    if excluir is not None:
        cerca = cerca.exclude(pk=excluir.pk)
    return [p for p in cerca if p.inicio < fin and p.fin > inicio]


def vehiculos_libres(inicio, horas, pedido=None):
    """Vehículos en estado Disponible sin otra mudanza que se superponga en ese horario."""
    ocupados = {p.patente_vehiculo_id for p in pedidos_que_se_cruzan(inicio, horas, pedido)}
    return Vehiculo.objects.filter(estado='Disponible').exclude(patente__in=ocupados).order_by('patente')


def motivo_sin_vehiculos():
    """Por qué no hay vehículos libres en ese horario, para explicárselo al cliente."""
    disponibles = Vehiculo.objects.filter(estado='Disponible').count()
    if not disponibles:
        return 'No hay vehículos disponibles: están en mantenimiento, en viaje o fuera de servicio.'
    if disponibles == 1:
        return 'El único vehículo disponible ya tiene una mudanza en ese horario. Probá con otra fecha u hora.'
    return (f'Los {disponibles} vehículos disponibles ya tienen una mudanza en ese horario. '
            'Probá con otra fecha u hora.')


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


def clave_objeto(texto):
    """Forma comparable de un nombre: sin mayúsculas, tildes ni signos, y en singular.
    «Sillas», «silla» y «SILLA» dan lo mismo; también «Colchón» y «colchones»."""
    t = unicodedata.normalize('NFKD', texto or '').encode('ascii', 'ignore').decode().lower()
    palabras = []
    for p in re.sub(r'[^a-z0-9 ]', ' ', t).split():
        if p.endswith('es') and len(p) > 4:
            p = p[:-2]
        elif p.endswith('s') and len(p) > 3:
            p = p[:-1]
        palabras.append(p)
    return ' '.join(palabras)


def _validar_items(items, errores):
    """Cada objeto sale del catálogo (OBJETOS): no se escriben nombres, así no hay variantes
    como «mesa» y «meza». Lo que no está en la lista va como «Otro», contado en la observación.
    Un mismo objeto va una sola vez por pedido: si son varios, se suma la cantidad."""
    if not items:
        errores['inventario'] = 'Agregá al menos un objeto.'
        return []
    activos = {o.pk: o for o in Objeto.objects.filter(Activo=True)}
    # para que «Otro» no se use con algo que ya está en la lista («silla» cuando existe «Sillas»)
    en_la_lista = {clave_objeto(o.nom_objeto): o for o in activos.values() if not o.es_otro}
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
        elif objeto.es_otro and clave_objeto(observacion) in en_la_lista:
            errores['inventario'] = (f'Objeto {n}: «{observacion}» ya está en la lista como '
                                     f'«{en_la_lista[clave_objeto(observacion)]}»: elegilo de ahí.')
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


def precio_principal(principal, vehiculo):
    """El servicio principal con el recargo por tamaño del camión (Chico 0 %, Mediano 25 %, Grande 50 %)."""
    return (principal.Precio_base * (100 + vehiculo.recargo) / 100).quantize(Decimal('0.01'))


def registrar_pedido(cliente, fecha_servicio, hora_servicio, origen, destino, id_servicio, patente, items,
                     ids_adicionales=()):
    """Registra el pedido completo (cabecera, servicios e inventario) en una sola
    transacción y lo deja Pendiente. Total = principal según el camión + adicionales a su
    precio. Si algo no es válido lanza ErrorPedido."""
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
        # Bloquea el vehículo: si dos clientes lo eligen para horarios que se cruzan, el segundo
        # espera a que el primero termine y después lo encuentra ocupado.
        # Este bloqueo depende de que la función abra su propia transacción y no haya leído nada
        # antes dentro de ella: quien la llame no debe envolverla en un atomic() externo que lea primero.
        horas = principal.Duracion_horas or MIN_HORAS
        vehiculo = Vehiculo.objects.select_for_update().filter(patente=patente).first()
        libres = vehiculos_libres(inicio_de(fecha_servicio, hora_servicio), horas)
        if not vehiculo or not libres.filter(patente=patente).exists():
            raise ErrorPedido({'vehiculo': 'Ese vehículo no está libre en ese horario. Elegí otro.'})

        precio = precio_principal(principal, vehiculo)
        total = precio + sum((s.Precio_base for s in adicionales), Decimal('0'))
        pedido = Pedido.objects.create(
            patente_vehiculo=vehiculo, idUsuario=cliente, Fecha_pedido=timezone.localdate(),
            fecha_servicio=fecha_servicio, hora_servicio=hora_servicio, duracion_horas=horas,
            origen=origen, destino=destino, estado=Pedido.PENDIENTE, total=total)
        # Una fila por servicio, con el precio del día: si después cambia, el pedido no cambia
        DetallePedido.objects.bulk_create(
            [DetallePedido(idPedido=pedido, idServicio=principal, precio_unitario=precio, subtotal=precio)]
            + [DetallePedido(idPedido=pedido, idServicio=s, precio_unitario=s.Precio_base, subtotal=s.Precio_base)
               for s in adicionales])
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


# Avisos para el administrador. No son estados guardados: se calculan con la fecha y hora.
VENCIDO = 'Vencido'              # Pendiente cuya fecha y hora ya pasaron
PARA_FINALIZAR = 'Para finalizar'  # Confirmado cuya mudanza ya empezó y nadie finalizó
POR_CONFIRMAR = 'Por confirmar'    # Pendiente que se hace en los próximos días
SIN_CHOFER = 'Sin chofer'          # Confirmado que todavía no empezó y no tiene chofer asignado
DIAS_POR_CONFIRMAR = 2


def _ya_empezo():
    ahora = timezone.localtime()
    return Q(fecha_servicio__lt=ahora.date()) | Q(fecha_servicio=ahora.date(), hora_servicio__lte=ahora.time())


def filtro_por_venir():
    """Pendientes o confirmados que todavía no empezaron: la agenda de verdad."""
    return Q(estado__in=Pedido.ACTIVOS) & ~_ya_empezo()


def filtro_vencidos():
    """Pendientes cuya mudanza ya debía haber empezado."""
    return Q(estado=Pedido.PENDIENTE) & _ya_empezo()


def filtro_para_finalizar():
    """Confirmados cuya mudanza ya empezó: falta marcarlos como finalizados."""
    return Q(estado=Pedido.CONFIRMADO) & _ya_empezo()


def filtro_por_confirmar():
    """Pendientes de hoy a DIAS_POR_CONFIRMAR días, que todavía no vencieron."""
    limite = timezone.localdate() + timedelta(days=DIAS_POR_CONFIRMAR)
    return Q(estado=Pedido.PENDIENTE, fecha_servicio__lte=limite) & ~_ya_empezo()


def filtro_sin_chofer():
    """Confirmados por venir sin chofer (los de antes de que fuera obligatorio)."""
    return (Q(estado=Pedido.CONFIRMADO) & ~_ya_empezo()
            & ~Q(pk__in=PersonalPedido.objects.filter(Funcion=PersonalPedido.CHOFER).values('idPedido')))


def filtro_por_venir_sin_chofer():
    """Pendientes o confirmados que todavía no empezaron y no tienen chofer asignado."""
    return filtro_por_venir() & ~Q(pk__in=PersonalPedido.objects.filter(Funcion=PersonalPedido.CHOFER)
                                   .values('idPedido'))


ATRASADA = 'Atrasada'              # Confirmado que ya debía terminar y lo espera otra mudanza
HORAS_SIGUIENTE = 12               # cuánto después del fin se mira si hay otra mudanza esperando


def mudanzas_atrasadas():
    """{mudanza atrasada: la mudanza que la espera}. Está atrasada la confirmada que ya pasó su
    fin estimado, nadie finalizó, y cuyo vehículo o alguien de su personal tiene otra mudanza que
    empieza dentro de las HORAS_SIGUIENTE horas siguientes a ese fin. Si no la espera ninguna,
    alcanza con el aviso «Para finalizar»."""
    ahora = timezone.now()
    desde = timezone.localtime(ahora - timedelta(hours=MAX_HORAS + HORAS_SIGUIENTE)).date()
    confirmados = Pedido.objects.filter(estado=Pedido.CONFIRMADO, fecha_servicio__range=(desde, timezone.localdate()))
    pasadas = [p for p in confirmados.prefetch_related('personal') if p.fin_esperado <= ahora]
    atrasadas = {}
    for p in sorted(pasadas, key=lambda p: p.fin_esperado):
        limite = p.fin + timedelta(hours=HORAS_SIGUIENTE)
        personal = [x.idUsuario_id for x in p.personal.all()]
        candidatas = Pedido.objects.filter(
            Q(patente_vehiculo=p.patente_vehiculo_id) | Q(personal__idUsuario__in=personal),
            estado__in=Pedido.ACTIVOS,
            fecha_servicio__range=(timezone.localtime(p.fin).date(), timezone.localtime(limite).date()),
        ).exclude(pk=p.pk).exclude(filtro_vencidos()).distinct()
        siguientes = sorted((q for q in candidatas if p.fin <= q.inicio <= limite), key=lambda q: q.inicio)
        if siguientes:
            atrasadas[p] = siguientes[0]
    return atrasadas


def que_comparten(p, q):
    """Qué tienen en común dos mudanzas, para el aviso: «el vehículo AA123XR y Luciana Fernández»."""
    partes = [f'el vehículo {p.patente_vehiculo_id}'] if p.patente_vehiculo_id == q.patente_vehiculo_id else []
    comunes = Usuario.objects.filter(asignaciones__idPedido=p).filter(asignaciones__idPedido=q) \
                             .order_by('Apellido', 'Nombre').distinct()
    partes += [f'{u.Nombre} {u.Apellido}' for u in comunes]
    return ' y '.join([', '.join(partes[:-1]), partes[-1]]) if len(partes) > 1 else (partes[0] if partes else '')


def recordatorio_finalizar():
    """Confirmadas cuyo fin estimado ya pasó y nadie finalizó (las más viejas primero), con
    `atrasada` en las que además otra mudanza está esperando. Para el aviso de todas las pantallas
    del administrador (idea del proyecto de José)."""
    ahora = timezone.now()
    atrasadas = {p.pk for p in mudanzas_atrasadas()}
    confirmadas = Pedido.objects.filter(estado=Pedido.CONFIRMADO, fecha_servicio__lte=timezone.localdate()) \
                                .select_related('idUsuario', 'patente_vehiculo')
    vencidas = sorted((p for p in confirmadas if p.fin_esperado <= ahora), key=lambda p: p.fin_esperado)
    for p in vencidas:
        p.atrasada = p.pk in atrasadas
    return vencidas


def filtro_atrasadas():
    return Q(pk__in=[p.pk for p in mudanzas_atrasadas()])


AVISOS = {ATRASADA: filtro_atrasadas, VENCIDO: filtro_vencidos, PARA_FINALIZAR: filtro_para_finalizar,
          POR_CONFIRMAR: filtro_por_confirmar, SIN_CHOFER: filtro_sin_chofer}


def contar_avisos():
    """Cuántos pedidos hay en cada aviso (para la lista del administrador)."""
    return {nombre: Pedido.objects.filter(filtro()).count() for nombre, filtro in AVISOS.items()}


def confirmar(id_pedido):
    """Un pedido vencido no se confirma: la fecha ya pasó, se anula."""
    with transaction.atomic():
        pedido = _pasar_a(id_pedido, 'confirmar')
        if pedido.ya_empezo:
            raise ErrorPedido('La fecha y hora de la mudanza ya pasaron sin confirmar: el pedido está vencido. '
                              'Anulalo y, si el cliente quiere, que pida una fecha nueva.')
        if not pedido.personal.filter(Funcion=PersonalPedido.CHOFER).exists():
            raise ErrorPedido('Asigná el chofer antes de confirmar el pedido.')
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


# ---------------------------------------------------------------- el chofer marca la mudanza
HORAS_ANTES_DE_EMPEZAR = 2  # «Empezamos» se puede tocar desde 2 horas antes del horario...


def se_puede_empezar(pedido, ahora=None):
    """...y hasta el final de ese día: una demora del mismo día se contempla, pero no se marcan
    mudanzas de días anteriores (que las finalice el administrador)."""
    ahora = ahora or timezone.now()
    return (pedido.inicio - timedelta(hours=HORAS_ANTES_DE_EMPEZAR) <= ahora
            and timezone.localtime(ahora).date() <= pedido.fecha_servicio)


def _del_chofer(id_pedido, usuario):
    """El pedido bloqueado, si `usuario` es su chofer (los ayudantes no marcan)."""
    pedido = Pedido.objects.select_for_update().get(pk=id_pedido)
    if not pedido.personal.filter(Funcion=PersonalPedido.CHOFER, idUsuario=usuario).exists():
        raise ErrorPedido('Solo el chofer de esta mudanza puede marcar que empezó o terminó.')
    if pedido.estado != Pedido.CONFIRMADO:
        raise ErrorPedido(f'El pedido N° {pedido.pk} está {pedido.estado.lower()}: no se puede marcar.')
    return pedido


def marcar_inicio(id_pedido, usuario):
    """«Empezamos»: el chofer guarda la hora real de inicio."""
    with transaction.atomic():
        pedido = _del_chofer(id_pedido, usuario)
        if pedido.inicio_real:
            raise ErrorPedido(f'Ya marcaste que empezó a las {timezone.localtime(pedido.inicio_real):%H:%M}.')
        desde = pedido.inicio - timedelta(hours=HORAS_ANTES_DE_EMPEZAR)
        if timezone.now() < desde:
            desde = timezone.localtime(desde)
            raise ErrorPedido(f'Todavía es temprano: se puede marcar desde el {desde:%d/%m} a las {desde:%H:%M}.')
        if not se_puede_empezar(pedido):
            raise ErrorPedido(f'Esta mudanza era el {pedido.fecha_servicio:%d/%m}: ya no se puede marcar. '
                              'Si la hicieron, avisale al administrador para que la finalice.')
        pedido.inicio_real = timezone.now()
        pedido.save(update_fields=['inicio_real'])
    return pedido


def marcar_fin(id_pedido, usuario):
    """«Terminamos»: el chofer guarda la hora real de fin y el pedido queda Finalizado
    (el chofer actúa como encargado de la mudanza)."""
    with transaction.atomic():
        pedido = _del_chofer(id_pedido, usuario)
        if not pedido.inicio_real:
            raise ErrorPedido('Primero marcá «Empezamos».')
        pedido.fin_real = timezone.now()
        pedido.estado = Pedido.FINALIZADO
        pedido.save(update_fields=['fin_real', 'estado'])
    return pedido


def anular(id_pedido, usuario, motivo):
    """Anula sin borrar: guarda fecha, motivo y usuario. Como un pedido anulado ya no
    cuenta como activo, el vehículo vuelve a estar libre en ese horario."""
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
    if estado in AVISOS:
        pedidos = pedidos.filter(AVISOS[estado]())
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


# ---------------------------------------------------------------- asignar personal
ROL_CHOFER, ROL_AYUDANTE = 'Chofer', 'Ayudante de Carga'
MAX_AYUDANTES = 6


def personal_libre(pedido, rol):
    """Empleados activos de ese rol sin otra mudanza que se superponga con el horario del pedido
    (igual que los vehículos). Los del propio pedido cuentan como libres para poder editarlo."""
    cruzados = pedidos_que_se_cruzan(pedido.inicio, pedido.duracion_horas, excluir=pedido)
    ocupados = PersonalPedido.objects.filter(idPedido__in=[p.pk for p in cruzados]).values('idUsuario')
    return (Usuario.objects.filter(Activo=True, idRol__nom_rol=rol)
            .exclude(pk__in=ocupados).order_by('Apellido', 'Nombre'))


def asignar_personal(id_pedido, id_chofer, ids_ayudantes=()):
    """Asigna el chofer (obligatorio) y los ayudantes (opcionales) de un pedido que todavía no
    empezó. Reemplaza la asignación anterior. Si algo no es válido lanza ErrorPedido."""
    ids = list(dict.fromkeys(int(i) for i in ids_ayudantes or ()))
    with transaction.atomic():
        pedido = Pedido.objects.select_for_update().get(pk=id_pedido)
        if pedido.estado not in Pedido.ACTIVOS:
            raise ErrorPedido(f'No se puede asignar personal a un pedido {pedido.estado.lower()}.')
        if pedido.ya_empezo:
            raise ErrorPedido('La mudanza ya empezó: el personal no se puede cambiar.')
        # bloquea a las personas elegidas: si dos pedidos del mismo día las piden a la vez, el segundo espera
        list(Usuario.objects.select_for_update().filter(pk__in=[i for i in [id_chofer, *ids] if i]))
        errores = {}
        chofer = personal_libre(pedido, ROL_CHOFER).filter(pk=id_chofer).first() \
            if id_chofer else None
        if not id_chofer:
            errores['chofer'] = 'Elegí el chofer.'
        elif chofer is None:
            errores['chofer'] = 'Ese chofer no está libre en ese horario. Elegí otro.'
        if len(ids) > MAX_AYUDANTES:
            errores['ayudantes'] = f'Se pueden asignar hasta {MAX_AYUDANTES} ayudantes.'
        else:
            ayudantes = list(personal_libre(pedido, ROL_AYUDANTE).filter(pk__in=ids))
            if len(ayudantes) != len(ids):
                errores['ayudantes'] = 'Alguno de los ayudantes no está libre en ese horario.'
        if errores:
            raise ErrorPedido(errores)
        pedido.personal.all().delete()
        PersonalPedido.objects.bulk_create(
            [PersonalPedido(idPedido=pedido, idUsuario=chofer, Funcion=PersonalPedido.CHOFER)]
            + [PersonalPedido(idPedido=pedido, idUsuario=a, Funcion=PersonalPedido.AYUDANTE) for a in ayudantes])
    return pedido


# ---------------------------------------------------------------- reprogramar
def reprogramar(id_pedido, usuario, fecha, hora, patente, motivo, observacion='', quitar_ocupados=False,
                id_chofer=None):
    """Cambia la fecha, la hora y, si hace falta, el vehículo de un pedido activo, y guarda el
    cambio en REPROGRAMACIONES (de cuándo a cuándo, por qué y quién). El vehículo tiene que estar
    libre en el horario nuevo. Si alguien del personal no lo está, se avisa quién; con
    quitar_ocupados se lo saca del pedido (si era el chofer, queda en el aviso «Sin chofer»).
    Con id_chofer se pone otro chofer, que tiene que estar libre en el horario nuevo (idea del
    proyecto de José). El precio no cambia aunque cambie el camión: es el acordado con el cliente.
    Si algo no es válido lanza ErrorPedido."""
    errores = {}
    observacion = (observacion or '').strip()
    _validar_fecha(fecha, errores)
    _validar_hora(fecha, hora, errores)
    if motivo not in dict(Reprogramacion.MOTIVOS):
        errores['motivo'] = 'Elegí el motivo de la lista.'
    elif motivo == 'Otro' and len(observacion) < 5:
        errores['observacion'] = 'Con «Otro», contá el motivo (5 caracteres o más).'
    if len(observacion) > MAX_OBSERVACION:
        errores['observacion'] = f'La observación puede tener hasta {MAX_OBSERVACION} caracteres.'
    if errores:
        raise ErrorPedido(errores)

    with transaction.atomic():
        pedido = Pedido.objects.select_for_update().get(pk=id_pedido)
        if pedido.estado not in Pedido.ACTIVOS:
            raise ErrorPedido(f'No se puede reprogramar un pedido {pedido.estado.lower()}.')
        if (fecha, hora, patente) == (pedido.fecha_servicio, pedido.hora_servicio, pedido.patente_vehiculo_id):
            raise ErrorPedido('Es el mismo horario y el mismo vehículo que ya tiene: cambiá algo.')
        inicio = inicio_de(fecha, hora)
        vehiculo = Vehiculo.objects.select_for_update().filter(patente=patente).first()
        if not vehiculo or not vehiculos_libres(inicio, pedido.duracion_horas, pedido).filter(patente=patente).exists():
            raise ErrorPedido({'vehiculo': f'El vehículo {patente} no está libre en ese horario. '
                                           'Elegí otro vehículo u horario.'})

        # el personal asignado tiene que estar libre en el horario nuevo
        cruzados = pedidos_que_se_cruzan(inicio, pedido.duracion_horas, excluir=pedido)
        ocupado = PersonalPedido.objects.filter(idPedido__in=[p.pk for p in cruzados]).values('idUsuario')
        chofer_nuevo = None
        if id_chofer:
            chofer_nuevo = (Usuario.objects.filter(pk=id_chofer, Activo=True, idRol__nom_rol=ROL_CHOFER)
                            .exclude(pk__in=ocupado).first())
            if chofer_nuevo is None:
                raise ErrorPedido({'chofer': 'Ese chofer no está libre en el horario nuevo. Elegí otro.'})
        actual = pedido.personal.select_related('idUsuario')
        if chofer_nuevo:  # el chofer de antes se reemplaza: no importa si estaba ocupado
            actual = actual.exclude(Funcion=PersonalPedido.CHOFER)
        ocupados = list(actual.filter(idUsuario__in=ocupado))
        if ocupados and not quitar_ocupados:
            nombres = ', '.join(f'{x.idUsuario.Nombre} {x.idUsuario.Apellido}' for x in ocupados)
            raise ErrorPedido({'quitar_ocupados': f'No está libre en ese horario: {nombres}. Marcá «sacarlo del '
                                                  'pedido» y después asigná a otra persona, o elegí otro horario.'})
        PersonalPedido.objects.filter(pk__in=[x.pk for x in ocupados]).delete()
        if chofer_nuevo:
            pedido.personal.filter(Q(Funcion=PersonalPedido.CHOFER) | Q(idUsuario=chofer_nuevo)).delete()
            PersonalPedido.objects.create(idPedido=pedido, idUsuario=chofer_nuevo, Funcion=PersonalPedido.CHOFER)

        Reprogramacion.objects.create(
            idPedido=pedido, fecha_anterior=pedido.fecha_servicio, hora_anterior=pedido.hora_servicio,
            vehiculo_anterior_id=pedido.patente_vehiculo_id, fecha_nueva=fecha, hora_nueva=hora,
            vehiculo_nuevo=vehiculo, motivo=motivo, observacion=observacion or None, usuario=usuario)
        pedido.fecha_servicio, pedido.hora_servicio, pedido.patente_vehiculo = fecha, hora, vehiculo
        pedido.save(update_fields=['fecha_servicio', 'hora_servicio', 'patente_vehiculo'])
    return pedido


def telefono_whatsapp(telefono):
    """El teléfono como lo pide wa.me (código de país sin «+»): «387 411-2233» → «5493874112233».
    Vacío si no hay un número que sirva."""
    digitos = re.sub(r'\D', '', telefono or '')
    if digitos.startswith('54'):
        return digitos
    digitos = digitos.lstrip('0')
    return '549' + digitos if len(digitos) >= 8 else ''


def mensaje_reprogramacion(r):
    """Texto para avisarle al cliente por WhatsApp."""
    p, cliente = r.idPedido, r.idPedido.idUsuario
    antes = inicio_de(r.fecha_anterior, r.hora_anterior)
    ahora = inicio_de(r.fecha_nueva, r.hora_nueva)
    dias = ['lunes', 'martes', 'miércoles', 'jueves', 'viernes', 'sábado', 'domingo']
    cuando = lambda d: f'el {dias[d.weekday()]} {d:%d/%m} a las {d:%H:%M}'
    motivo = r.motivo_completo
    if r.motivo != 'Otro':
        motivo = motivo[0].lower() + motivo[1:]
    texto = (f'Hola {cliente.Nombre}, te escribimos de Mudanzas y Fletes Salta. Tu mudanza (pedido N° {p.pk}) '
             f'cambió de horario: era {cuando(timezone.localtime(antes))} y ahora es {cuando(timezone.localtime(ahora))}. '
             f'Motivo: {motivo}.')
    if r.vehiculo_nuevo_id != r.vehiculo_anterior_id:
        texto += f' Va el vehículo {r.vehiculo_nuevo_id}.'
    return texto + ' Disculpá las molestias.'
