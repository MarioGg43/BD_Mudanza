"""RECURSOS_ASIGNADOS queda como en el DER nuevo: servicio + material + cantidad sugerida. Se saca
la columna de texto «Materiales» (la 0022 ya pasó todo a materiales) y el material pasa a ser
obligatorio, sin repetirse dentro de un mismo servicio."""
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [('usuarios', '0022_cargar_materiales')]

    operations = [
        migrations.RemoveField(model_name='recursoasignado', name='Materiales'),
        migrations.AlterField(
            model_name='recursoasignado', name='idMaterial',
            field=models.ForeignKey(db_column='id_material', on_delete=django.db.models.deletion.PROTECT,
                                    related_name='servicios', to='usuarios.material', verbose_name='Material'),
        ),
        migrations.AddConstraint(
            model_name='recursoasignado',
            constraint=models.UniqueConstraint(fields=('idServicio', 'idMaterial'), name='material_una_vez_por_servicio'),
        ),
    ]
