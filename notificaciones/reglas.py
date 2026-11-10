"""Reglas de notificación del Parcial N° 2 (M3).

Cada regla, cuando se cumple su condición, crea una Notificacion (que aparece en la campanita
y en la bandeja del perfil destino) y, algunas, mandan también un correo.

| Regla | Cuándo se evalúa                                   | A quién avisa                    | Umbral (tabla CONFIGURACION)           |
|-------|----------------------------------------------------|----------------------------------|----------------------------------------|
| 1     | Tarea programada (evaluar_alertas)                 | Administrador + correo a empresa | horas_sin_confirmar, correo_empresa    |
| 2     | Tarea programada (evaluar_alertas)                 | Administrador                    | minutos_atraso                         |
| 3     | En tiempo real, al anular un pedido                | Administrador                    | cancelaciones_cliente, dias_cancelaciones |
| 4     | En tiempo real, al confirmar o reprogramar         | El cliente + correo al cliente   | correo_al_cliente                      |

¿Cómo no se dispara dos veces? Cada notificación tiene una clave única en la base (por ejemplo
«sin_confirmar:123»). Si la regla vuelve a cumplirse para lo mismo, get_or_create encuentra la que
ya existe y no crea otra; el correo solo sale cuando la notificación es nueva.
"""
import logging
from datetime import timedelta

from django.conf import settings
from django.core.mail import send_mail
from django.db import IntegrityError, transaction
from django.urls import reverse
from django.utils import timezone

from usuarios.models import Configuracion, Notificacion, Pedido, Rol

log = logging.getLogger(__name__)

SIN_CONFIRMAR, ATRASADA, CANCELACIONES, CONFIRMADO, REPROGRAMADO, STOCK_BAJO = (
    'Pedido sin confirmar', 'Mudanza atrasada', 'Cliente con cancelaciones', 'Mudanza confirmada',
    'Mudanza reprogramada', 'Stock bajo')


# ------------------------------------------------------------------ configuración
def parametro(clave, por_defecto=''):
    """El valor de un umbral de la tabla CONFIGURACION (como texto)."""
    fila = Configuracion.objects.filter(clave=clave).first()
    return fila.valor.strip() if fila else por_defecto


def parametro_entero(clave, por_defecto):
    try:
        return int(parametro(clave, str(por_defecto)))
    except ValueError:
        return por_defecto


# ------------------------------------------------------------------ crear y mandar
def notificar(clave, tipo, mensaje, perfil, usuario=None, enlace='', correo_a=None, asunto=''):
    """Crea la notificación si todavía no existe una con esa clave. Si es nueva y hay un correo
    de destino, lo manda cuando la operación se guarda. Devuelve (notificación, es_nueva)."""
    rol = Rol.objects.filter(nom_rol=perfil).first()
    if not rol:
        return None, False
    try:
        with transaction.atomic():
            notif, nueva = Notificacion.objects.get_or_create(clave=clave, defaults={
                'tipo': tipo, 'mensaje': mensaje[:300], 'destino_perfil': rol, 'destino_usuario': usuario,
                'enlace': enlace})
    except IntegrityError:  # otra evaluación la creó al mismo tiempo: ya existe
        return Notificacion.objects.get(clave=clave), False
    if nueva and correo_a:
        # se manda después de guardar: si la operación se deshace, no sale un correo de algo que no pasó
        transaction.on_commit(lambda: _mandar_correo(notif.pk, correo_a, asunto or tipo, mensaje, enlace))
    return notif, nueva


def _mandar_correo(id_notif, destino, asunto, mensaje, enlace):
    url = f'{settings.SITIO_URL}{enlace}' if enlace else settings.SITIO_URL
    cuerpo = (f'{mensaje}\n\nPodés verlo en el sistema: {url}\n\n'
              'Mudanzas y Fletes Salta · Este es un aviso automático, no hace falta responderlo.')
    try:
        send_mail(f'Mudanzas y Fletes Salta · {asunto}', cuerpo, None, [destino])
        estado = f'Enviado a {destino}'
    except Exception as e:  # el aviso queda en la bandeja aunque el correo falle
        log.warning('No se pudo mandar el correo a %s: %s', destino, e)
        estado = f'No se pudo enviar a {destino}'
    Notificacion.objects.filter(pk=id_notif).update(correo=estado[:200])


def _cliente(p):
    return f'{p.idUsuario.Nombre} {p.idUsuario.Apellido}'


def _cuando(p):
    ini = timezone.localtime(p.inicio)
    return f'{ini:%d/%m/%Y} a las {ini:%H:%M}'


# ------------------------------------------------------------------ regla 1 (programada)
def pedidos_sin_confirmar(ahora=None):
    """Pendientes cuya mudanza empieza dentro de las próximas `horas_sin_confirmar` horas."""
    ahora = ahora or timezone.now()
    horas = parametro_entero('horas_sin_confirmar', 48)
    correo = parametro('correo_empresa')
    nuevas = 0
    candidatos = (Pedido.objects.filter(estado=Pedido.PENDIENTE,
                                        fecha_servicio__range=(timezone.localdate(ahora), (ahora + timedelta(hours=horas)).date()))
                  .select_related('idUsuario'))
    for p in candidatos:
        if not ahora <= p.inicio <= ahora + timedelta(hours=horas):
            continue
        faltan = round((p.inicio - ahora).total_seconds() / 3600)
        _, nueva = notificar(
            f'sin_confirmar:{p.pk}', SIN_CONFIRMAR,
            f'El pedido N° {p.pk} de {_cliente(p)} sigue pendiente y la mudanza es el {_cuando(p)} '
            f'(faltan {faltan} h). Confirmalo o avisale al cliente.',
            'Administrador', enlace=reverse('pedidos_detalle', args=[p.pk]), correo_a=correo or None,
            asunto=f'Pedido N° {p.pk} sin confirmar')
        nuevas += nueva
    return nuevas


# ------------------------------------------------------------------ regla 2 (programada)
def mudanzas_atrasadas(ahora=None):
    """Confirmadas cuyo fin estimado pasó hace más de `minutos_atraso` minutos y nadie finalizó."""
    ahora = ahora or timezone.now()
    tolerancia = timedelta(minutes=parametro_entero('minutos_atraso', 60))
    nuevas = 0
    for p in (Pedido.objects.filter(estado=Pedido.CONFIRMADO, fecha_servicio__lte=timezone.localdate(ahora))
              .select_related('idUsuario')):
        if p.fin_esperado + tolerancia > ahora:
            continue
        _, nueva = notificar(
            f'atrasada:{p.pk}', ATRASADA,
            f'La mudanza N° {p.pk} de {_cliente(p)} tendría que haber terminado a las '
            f'{timezone.localtime(p.fin_esperado):%H:%M} del {timezone.localtime(p.fin_esperado):%d/%m} y nadie la finalizó.',
            'Administrador', enlace=reverse('pedidos_detalle', args=[p.pk]))
        nuevas += nueva
    return nuevas


def evaluar_programadas(ahora=None):
    """Lo que corre la tarea programada. Devuelve cuántas notificaciones nuevas hubo por regla."""
    return {SIN_CONFIRMAR: pedidos_sin_confirmar(ahora), ATRASADA: mudanzas_atrasadas(ahora)}


# ------------------------------------------------------------------ regla 3 (tiempo real)
def al_anular(pedido):
    """Si el cliente llegó a `cancelaciones_cliente` anulaciones en los últimos `dias_cancelaciones`
    días, se avisa al administrador. Cada anulación de más genera su propio aviso (la clave lleva
    la cantidad), pero la misma cantidad nunca avisa dos veces."""
    limite = parametro_entero('cancelaciones_cliente', 3)
    dias = parametro_entero('dias_cancelaciones', 90)
    cliente = pedido.idUsuario
    cantidad = Pedido.objects.filter(idUsuario=cliente, estado=Pedido.ANULADO,
                                     fecha_anulacion__gte=timezone.now() - timedelta(days=dias)).count()
    if cantidad < limite:
        return None
    notif, _ = notificar(
        f'cancelaciones:{cliente.pk}:{cantidad}', CANCELACIONES,
        f'{cliente.Nombre} {cliente.Apellido} (DNI {cliente.DNI}) ya tiene {cantidad} pedidos anulados en los '
        f'últimos {dias} días. El último fue el N° {pedido.pk}: «{pedido.motivo_anulacion}».',
        'Administrador', enlace=reverse('pedidos_detalle', args=[pedido.pk]))
    return notif


# ------------------------------------------------------------------ regla 4 (tiempo real)
def _al_cliente(pedido, clave, tipo, mensaje):
    cliente = pedido.idUsuario
    correo = cliente.Correo if parametro('correo_al_cliente', '1') == '1' else None
    notif, _ = notificar(clave, tipo, mensaje, cliente.idRol.nom_rol, usuario=cliente,
                         enlace=reverse('pedidos_detalle', args=[pedido.pk]), correo_a=correo,
                         asunto=f'{tipo} (pedido N° {pedido.pk})')
    return notif


def al_confirmar(pedido):
    return _al_cliente(pedido, f'confirmado:{pedido.pk}', CONFIRMADO,
                       f'¡Hola {pedido.idUsuario.Nombre}! Confirmamos tu mudanza N° {pedido.pk} para el '
                       f'{_cuando(pedido)}, de {pedido.origen} a {pedido.destino}.')


def al_reprogramar(pedido, reprogramacion):
    return _al_cliente(pedido, f'reprogramado:{reprogramacion.pk}', REPROGRAMADO,
                       f'Hola {pedido.idUsuario.Nombre}: tu mudanza N° {pedido.pk} cambió de horario. Ahora es el '
                       f'{_cuando(pedido)}. Motivo: {reprogramacion.motivo_completo}.')


# ------------------------------------------------------------------ regla 5 (tiempo real)
def al_bajar_stock(material):
    """Cuando un material queda por debajo de su stock mínimo (MATERIALES.stock_min_material),
    avisa al administrador y manda un correo a la empresa. No se repite hasta que se reponga: la
    clave lleva el último ingreso, así que después de una compra puede volver a avisar."""
    from usuarios.models import MovimientoMaterial
    material.refresh_from_db(fields=['stock_material', 'stock_min_material', 'Activo'])
    if not material.Activo or not material.bajo_minimo:
        return None
    ultimo = (MovimientoMaterial.objects.filter(idMaterial=material, tipo_mov=MovimientoMaterial.INGRESO)
              .order_by('-pk').values_list('pk', flat=True).first() or 0)
    notif, _ = notificar(
        f'stock_bajo:{material.pk}:{ultimo}', STOCK_BAJO,
        f'Quedan {material.stock_material} {material.unidad_material} de {material.nom_material} y el mínimo es '
        f'{material.stock_min_material}. Conviene reponer.',
        'Administrador', enlace=reverse('materiales_lista'), correo_a=parametro('correo_empresa') or None,
        asunto=f'Stock bajo de {material.nom_material}')
    return notif


# ------------------------------------------------------------------ bandeja
def de_usuario(usuario):
    """Las notificaciones que ve esta persona: las de su perfil (sin usuario puntual) y las suyas."""
    from django.db.models import Q
    return Notificacion.objects.filter(
        Q(destino_usuario=usuario) | Q(destino_usuario__isnull=True, destino_perfil_id=usuario.idRol_id))
