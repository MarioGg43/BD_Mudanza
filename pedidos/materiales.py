"""Control de materiales: las reglas. Las usan las pantallas de Django y la API de React.

El stock solo cambia con un movimiento (MOVIMIENTOS_MATERIAL):

| Cuándo                        | Movimiento                                   | Stock         |
|-------------------------------|----------------------------------------------|---------------|
| Compra o reposición           | Ingreso                                      | suma          |
| El chofer toca «Empezamos»    | Salida (lo sugerido por los servicios)       | resta         |
| El chofer toca «Terminamos»   | Consumo (lo gastado), Devolución (lo que     | la Devolución |
|                               | sobró o volvió) y Pérdida (lo que no volvió) | suma          |
| Se anula una mudanza en curso | Devolución de todo lo que salió              | suma          |
| Corrección del inventario     | Ajuste (con signo y motivo)                  | suma o resta  |

Si al empezar no alcanza el stock, sale lo que hay y se avisa cuánto faltó. Cuando un material
queda por debajo de su mínimo, se avisa al administrador (regla 5 de las notificaciones).
"""
from collections import OrderedDict

from django.db import transaction
from django.db.models import F, Sum

from usuarios.models import Material, MovimientoMaterial as Mov, Pedido


class ErrorMaterial(Exception):
    pass


# ------------------------------------------------------------------ cálculos
def sugeridos(pedido):
    """{material: cantidad} que sugieren los servicios del pedido (el principal y los adicionales)."""
    total = OrderedDict()
    for d in pedido.detalles.select_related('idServicio').prefetch_related('idServicio__recursos__idMaterial'):
        for r in d.idServicio.recursos.all():
            if r.idMaterial.Activo:
                total[r.idMaterial] = total.get(r.idMaterial, 0) + r.cant_sugerida
    return total


def enviados(pedido):
    """{material: cantidad} que salió para esta mudanza."""
    filas = (Mov.objects.filter(idPedido=pedido, tipo_mov=Mov.SALIDA).values('idMaterial')
             .annotate(total=Sum('cant_mov')))
    materiales = Material.objects.in_bulk([f['idMaterial'] for f in filas])
    return OrderedDict((materiales[f['idMaterial']], f['total']) for f in filas)


def ya_salieron(pedido):
    return Mov.objects.filter(idPedido=pedido, tipo_mov=Mov.SALIDA).exists()


def ya_se_cerro(pedido):
    return Mov.objects.filter(idPedido=pedido, tipo_mov__in=[Mov.CONSUMO, Mov.DEVOLUCION, Mov.PERDIDA]).exists()


def en_uso():
    """{id_material: cantidad} de reutilizables que están afuera, en mudanzas que no cerraron."""
    abiertas = Pedido.objects.filter(estado=Pedido.CONFIRMADO, inicio_real__isnull=False, fin_real__isnull=True)
    filas = (Mov.objects.filter(idPedido__in=abiertas, tipo_mov=Mov.SALIDA, idMaterial__reutilizable=True)
             .values('idMaterial').annotate(total=Sum('cant_mov')))
    return {f['idMaterial']: f['total'] for f in filas}


# ------------------------------------------------------------------ movimientos
def _mover(material, tipo, cantidad, usuario=None, pedido=None, observacion=''):
    """Registra el movimiento y actualiza el stock en la base (sin pisar otro cambio simultáneo)."""
    if not cantidad:
        return None
    mov = Mov.objects.create(idMaterial=material, idPedido=pedido, idUsuario=usuario, tipo_mov=tipo,
                             cant_mov=cantidad, observacion_mov=observacion[:200])
    efecto = Mov.EFECTO[tipo] * cantidad
    if efecto:
        Material.objects.filter(pk=material.pk).update(stock_material=F('stock_material') + efecto)
        material.refresh_from_db(fields=['stock_material'])
    return mov


def _revisar_minimos(materiales):
    from notificaciones import reglas as alertas  # regla 5: stock bajo
    for m in materiales:
        alertas.al_bajar_stock(m)


def registrar_ingreso(material, cantidad, usuario, observacion=''):
    """Compra o reposición."""
    if not isinstance(cantidad, int) or not 1 <= cantidad <= 100000:
        raise ErrorMaterial('La cantidad tiene que ser un número entero de 1 a 100.000.')
    with transaction.atomic():
        return _mover(material, Mov.INGRESO, cantidad, usuario, observacion=observacion or 'Compra')


def registrar_ajuste(material, cantidad, usuario, motivo):
    """Corrige el inventario (por ejemplo, después de contar): suma o resta, siempre con motivo."""
    motivo = (motivo or '').strip()
    if not isinstance(cantidad, int) or cantidad == 0:
        raise ErrorMaterial('Indicá cuánto suma (número positivo) o cuánto resta (negativo).')
    if len(motivo) < 5:
        raise ErrorMaterial('Contá el motivo del ajuste (al menos 5 caracteres).')
    if material.stock_material + cantidad < 0:
        raise ErrorMaterial(f'No se pueden restar {-cantidad}: hay {material.stock_material} en stock.')
    with transaction.atomic():
        mov = _mover(material, Mov.AJUSTE, cantidad, usuario, observacion=motivo)
    _revisar_minimos([material])
    return mov


def registrar_salida(pedido, usuario):
    """Al «Empezamos»: sale lo sugerido por los servicios. Si no alcanza el stock, sale lo que hay.
    Devuelve [(material, sugerido, llevado)] para avisarle al chofer si faltó algo."""
    if ya_salieron(pedido):
        return []
    resultado = []
    with transaction.atomic():
        for material, cantidad in sugeridos(pedido).items():
            material = Material.objects.select_for_update().get(pk=material.pk)
            llevado = min(cantidad, max(material.stock_material, 0))
            _mover(material, Mov.SALIDA, llevado, usuario, pedido,
                   '' if llevado == cantidad else f'Faltaron {cantidad - llevado}')
            resultado.append((material, cantidad, llevado))
    _revisar_minimos([m for m, _, _ in resultado])
    return resultado


def registrar_cierre(pedido, usuario, usados=None):
    """Al «Terminamos» (o cuando el administrador finaliza): por cada material que salió,
    los consumibles se registran como gastados y lo que sobró vuelve; los reutilizables vuelven y
    los que faltan quedan como pérdida. `usados` es {id_material: cantidad}: lo que se gastó de
    cada consumible o lo que volvió de cada reutilizable. Si no viene, se toma todo gastado
    (consumibles) y todo devuelto (reutilizables)."""
    if ya_se_cerro(pedido):
        return
    usados = usados or {}
    with transaction.atomic():
        for material, salio in enviados(pedido).items():
            dato = usados.get(material.pk, salio)
            if not isinstance(dato, int) or not 0 <= dato <= salio:
                raise ErrorMaterial(f'{material}: la cantidad tiene que ser de 0 a {salio}.')
            if material.reutilizable:  # dato = cuántos volvieron
                _mover(material, Mov.DEVOLUCION, dato, usuario, pedido)
                _mover(material, Mov.PERDIDA, salio - dato, usuario, pedido, 'No volvió de la mudanza')
            else:  # dato = cuántos se gastaron
                _mover(material, Mov.CONSUMO, dato, usuario, pedido)
                _mover(material, Mov.DEVOLUCION, salio - dato, usuario, pedido, 'Sobró')


def devolver_todo(pedido, usuario):
    """Si se anula una mudanza que ya había salido, vuelve todo lo que se llevó."""
    if not ya_salieron(pedido) or ya_se_cerro(pedido):
        return
    with transaction.atomic():
        for material, salio in enviados(pedido).items():
            _mover(material, Mov.DEVOLUCION, salio, usuario, pedido, 'Mudanza anulada')


def faltantes(pedido):
    """[(material, sugerido, hay)] de lo que no alcanza para esta mudanza (para el portal)."""
    return [(m, c, m.stock_material) for m, c in sugeridos(pedido).items() if m.stock_material < c]


def bajo_minimo():
    return Material.objects.filter(Activo=True, stock_material__lt=F('stock_min_material'))

