"""Inventario con objetos de un catálogo (tabla OBJETOS) y tipo de vehículo de una lista cerrada.

Lo que ya estaba cargado se pasa solo: el texto que coincide con un objeto del catálogo
se vincula a ese objeto; el resto queda como «Otro» y su texto pasa a la observación.
"""
import django.db.models.deletion
from django.db import migrations, models

OBJETOS_INICIALES = [
    'Heladera', 'Cocina', 'Lavarropas', 'Microondas', 'Cama 1 plaza', 'Cama 2 plazas', 'Colchón',
    'Ropero', 'Cómoda', 'Mesa', 'Sillas', 'Sillón', 'Televisor', 'Escritorio', 'Biblioteca',
    'Cajas', 'Bolsos y valijas', 'Bicicleta', 'Plantas', 'Otro',
]
TIPOS = ['Utilitario Mediano', 'Furgón Urbano', 'Camión Liviano', 'Camión Pesado']


def objetos_y_tipos(apps, schema_editor):
    Objeto = apps.get_model('usuarios', 'Objeto')
    InventarioDetalle = apps.get_model('usuarios', 'InventarioDetalle')
    Vehiculo = apps.get_model('usuarios', 'Vehiculo')

    catalogo = {}
    for nombre in OBJETOS_INICIALES:
        catalogo[nombre.lower()] = Objeto.objects.get_or_create(nom_objeto=nombre)[0]
    otro = catalogo['otro']
    for item in InventarioDetalle.objects.all():
        texto = (item.Descripcion or '').strip()
        objeto = catalogo.get(texto.lower())
        if objeto is None:
            objeto = otro
            if texto and texto.lower() != 'sin descripción':
                partes = [texto] + ([item.Observacion] if item.Observacion else [])
                item.Observacion = '; '.join(partes)[:200]
        item.idObjeto = objeto
        item.save(update_fields=['idObjeto', 'Observacion'])

    for v in Vehiculo.objects.exclude(tipo_vehiculo__in=TIPOS):
        texto = (v.tipo_vehiculo or '').lower()
        if v.capacidad_kg and v.capacidad_kg >= 4000:
            v.tipo_vehiculo = 'Camión Pesado'
        elif 'furg' in texto:
            v.tipo_vehiculo = 'Furgón Urbano'
        elif 'util' in texto:
            v.tipo_vehiculo = 'Utilitario Mediano'
        else:
            v.tipo_vehiculo = 'Camión Liviano'
        v.save(update_fields=['tipo_vehiculo'])


class Migration(migrations.Migration):
    dependencies = [('usuarios', '0007_servicios_adicionales')]

    operations = [
        migrations.CreateModel(
            name='Objeto',
            fields=[
                ('id_objeto', models.AutoField(primary_key=True, serialize=False)),
                ('nom_objeto', models.CharField(db_column='nom_objeto', max_length=100, unique=True,
                                                verbose_name='Objeto')),
                ('Activo', models.BooleanField(db_column='estado_objeto', default=True, verbose_name='Activo')),
            ],
            options={'db_table': 'OBJETOS', 'verbose_name': 'Objeto', 'verbose_name_plural': 'Objetos',
                     'ordering': ['nom_objeto']},
        ),
        migrations.AddField(
            model_name='inventariodetalle',
            name='idObjeto',
            field=models.ForeignKey(db_column='id_objeto', null=True, on_delete=django.db.models.deletion.PROTECT,
                                    related_name='inventarios', to='usuarios.objeto', verbose_name='Objeto'),
        ),
        migrations.RunPython(objetos_y_tipos, migrations.RunPython.noop),
        migrations.RemoveField(model_name='inventariodetalle', name='Descripcion'),
        migrations.AlterField(
            model_name='inventariodetalle',
            name='idObjeto',
            field=models.ForeignKey(db_column='id_objeto', on_delete=django.db.models.deletion.PROTECT,
                                    related_name='inventarios', to='usuarios.objeto', verbose_name='Objeto'),
        ),
        migrations.AlterField(
            model_name='vehiculo',
            name='tipo_vehiculo',
            field=models.CharField(choices=[(t, t) for t in TIPOS], max_length=50, verbose_name='Tipo de vehículo'),
        ),
    ]
