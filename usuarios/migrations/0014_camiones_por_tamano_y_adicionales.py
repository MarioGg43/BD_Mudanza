"""Tipos de vehículo por tamaño (Camión Chico, Mediano o Grande) y adicionales con precio.

Idea del proyecto de José, rehecha sin tocar usuarios ni pedidos: solo pasa cada vehículo al
tamaño que le corresponde y pone precio a los adicionales que todavía no tienen.
"""
from decimal import Decimal

from django.db import migrations, models

CHICO, MEDIANO, GRANDE = 'Camión Chico', 'Camión Mediano', 'Camión Grande'
PRECIOS_ADICIONALES = {'Embalaje': Decimal('25000'), 'Desarmado y armado de muebles': Decimal('35000'),
                       'Ayudante extra': Decimal('20000')}


def tamano(tipo, capacidad_kg):
    if tipo == 'Furgón Urbano' or (capacidad_kg and capacidad_kg <= 1800):
        return CHICO
    if tipo == 'Camión Pesado' or (capacidad_kg and capacidad_kg >= 4500):
        return GRANDE
    return MEDIANO


def adelante(apps, schema_editor):
    Vehiculo = apps.get_model('usuarios', 'Vehiculo')
    Servicio = apps.get_model('usuarios', 'Servicio')
    for v in Vehiculo.objects.exclude(tipo_vehiculo__in=[CHICO, MEDIANO, GRANDE]):
        v.tipo_vehiculo = tamano(v.tipo_vehiculo, v.capacidad_kg)
        v.save(update_fields=['tipo_vehiculo'])
    for s in Servicio.objects.filter(Categoria='Adicional', Precio_base=0, Tipo_servicio__in=PRECIOS_ADICIONALES):
        s.Precio_base = PRECIOS_ADICIONALES[s.Tipo_servicio]
        s.save(update_fields=['Precio_base'])


class Migration(migrations.Migration):

    dependencies = [
        ('usuarios', '0013_log_auditoria'),
    ]

    operations = [
        migrations.AlterField(
            model_name='vehiculo',
            name='tipo_vehiculo',
            field=models.CharField(choices=[('Camión Chico', 'Camión Chico'), ('Camión Mediano', 'Camión Mediano'),
                                            ('Camión Grande', 'Camión Grande')],
                                   max_length=50, verbose_name='Tipo de vehículo'),
        ),
        migrations.RunPython(adelante, migrations.RunPython.noop),
    ]
