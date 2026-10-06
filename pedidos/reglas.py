"""Reglas del pedido de mudanza (Hito 3).

Las vistas solo arman los datos y muestran el resultado: todo lo que decide si un
pedido es válido, cuánto cuesta y a qué estado pasa vive acá. Cada operación que
escribe corre en una transacción: o se guarda todo, o no se guarda nada.
"""
from datetime import timedelta
from decimal import Decimal, InvalidOperation

from django.db import transaction
from django.utils import timezone

from usuarios.models import DetallePedido, InventarioDetalle, Pedido, Servicio, Vehiculo

MAX_DIAS_ADELANTO = 365
MAX_CANTIDAD = 999
MAX_PESO_UNITARIO = Decimal('5000')
MAX_DIRECCION = 200


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


def _validar_direcciones(origen, destino, errores):
    for campo, valor, nombre in (('origen', origen, 'origen'), ('destino', destino, 'destino')):
        if not valor:
            errores[campo] = f'Escribí la dirección de {nombre}.'
        elif len(valor) > MAX_DIRECCION:
            errores[campo] = f'La dirección de {nombre} puede tener hasta {MAX_DIRECCION} caracteres.'
    if origen and destino and origen.lower() == destino.lower():
        errores['destino'] = 'El destino tiene que ser distinto del origen.'


def _validar_servicios(ids_servicios, errores):
    ids = {int(i) for i in ids_servicios or []}
    servicios = list(Servicio.objects.filter(id_servicio__in=ids, Activo=True))
    if not ids:
        errores['servicios'] = 'Elegí al menos un servicio.'
    elif len(servicios) != len(ids):
        errores['servicios'] = 'Uno de los servicios elegidos ya no está disponible.'
    return servicios


def _validar_items(items, errores):
    if not items:
        errores['inventario'] = 'Agregá al menos un objeto.'
        return []
    limpios = []
    for n, item in enumerate(items, start=1):
        descripcion = (item.get('descripcion') or '').strip()
        try:
            cantidad = int(item.get('cantidad'))
            peso = Decimal(str(item.get('peso')))
        except (TypeError, ValueError, InvalidOperation):
            errores['inventario'] = f'Objeto {n}: la cantidad y el peso tienen que ser números.'
            continue
        if not descripcion:
            errores['inventario'] = f'Objeto {n}: escribí qué es.'
        elif not 1 <= cantidad <= MAX_CANTIDAD:
            errores['inventario'] = f'Objeto {n}: la cantidad va de 1 a {MAX_CANTIDAD}.'
        elif not Decimal('0') < peso <= MAX_PESO_UNITARIO:
            errores['inventario'] = f'Objeto {n}: el peso tiene que ser mayor a 0 y de hasta {MAX_PESO_UNITARIO} kg.'
        else:
            limpios.append({'descripcion': descripcion[:100], 'cantidad': cantidad,
                            'peso': peso, 'fragil': bool(item.get('fragil'))})
    return limpios


def registrar_pedido(cliente, fecha_servicio, origen, destino, ids_servicios, patente, items):
    """Registra el pedido completo (cabecera, servicios e inventario) en una sola
    transacción y lo deja Pendiente. Si algo no es válido lanza ErrorPedido."""
    errores = {}
    origen, destino = (origen or '').strip(), (destino or '').strip()
    _validar_fecha(fecha_servicio, errores)
    _validar_direcciones(origen, destino, errores)
    servicios = _validar_servicios(ids_servicios, errores)
    limpios = _validar_items(items, errores)
    if not patente:
        errores['vehiculo'] = 'Elegí un vehículo.'
    if errores:
        raise ErrorPedido(errores)

    with transaction.atomic():
        # Bloquea el vehículo: si dos clientes lo eligen para el mismo día, el segundo espera
        # a que el primero termine y después lo encuentra ocupado.
        vehiculo = Vehiculo.objects.select_for_update().filter(patente=patente).first()
        if not vehiculo or not vehiculos_libres(fecha_servicio).filter(patente=patente).exists():
            raise ErrorPedido({'vehiculo': 'Ese vehículo no está libre para esa fecha. Elegí otro.'})
        peso_total = sum(i['cantidad'] * i['peso'] for i in limpios)
        if peso_total > vehiculo.capacidad_kg:
            raise ErrorPedido({'vehiculo': f'La carga ({peso_total} kg) supera la capacidad '
                                           f'del vehículo ({vehiculo.capacidad_kg} kg).'})

        pedido = Pedido.objects.create(
            patente_vehiculo=vehiculo, idUsuario=cliente, Fecha_pedido=timezone.localdate(),
            fecha_servicio=fecha_servicio, origen=origen, destino=destino,
            estado=Pedido.PENDIENTE, total=sum(s.Precio_base for s in servicios))
        DetallePedido.objects.bulk_create([
            DetallePedido(idPedido=pedido, idServicio=s, precio_unitario=s.Precio_base, subtotal=s.Precio_base)
            for s in servicios])
        InventarioDetalle.objects.bulk_create([
            InventarioDetalle(idPedido=pedido, Descripcion=i['descripcion'], Cantidad=i['cantidad'],
                              Peso=i['peso'], Fragil=i['fragil'])
            for i in limpios])
    return pedido
