from django.db import migrations


def completar_pedidos_existentes(apps, schema_editor):
    """Los pedidos cargados antes del Hito 3 no tenían fecha de servicio, direcciones
    ni precios: se completan para que la consulta y el comprobante los muestren bien."""
    Pedido = apps.get_model('usuarios', 'Pedido')
    InventarioDetalle = apps.get_model('usuarios', 'InventarioDetalle')
    for pedido in Pedido.objects.all():
        total = 0
        for detalle in pedido.detalles.select_related('idServicio'):
            detalle.precio_unitario = detalle.subtotal = detalle.idServicio.Precio_base
            detalle.save(update_fields=['precio_unitario', 'subtotal'])
            total += detalle.subtotal
        pedido.fecha_servicio = pedido.Fecha_pedido
        pedido.origen = pedido.origen or 'Sin dato'
        pedido.destino = pedido.destino or 'Sin dato'
        pedido.estado = 'Finalizado'
        pedido.total = total
        pedido.save()
    InventarioDetalle.objects.filter(Descripcion='').update(Descripcion='Sin descripción')


class Migration(migrations.Migration):
    dependencies = [('usuarios', '0002_hito3_pedidos')]
    operations = [migrations.RunPython(completar_pedidos_existentes, migrations.RunPython.noop)]
