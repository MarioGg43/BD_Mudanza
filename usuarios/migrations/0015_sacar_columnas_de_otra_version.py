"""Saca las columnas que dejó la versión del proyecto de José en una base que la corrió antes.

Si una base pasó por esa versión, quedan columnas que este sistema no usa y que no tienen valor por
defecto: al registrar un pedido MySQL pide «Notif_atraso_enviada» y falla. Acá, si existen, se
sacan; en una base que no pasó por esa versión no hace nada. También devuelve las duraciones de los
servicios principales si quedaron en las de esa versión (4, 5 y 6 horas).
"""
from django.db import migrations

COLUMNAS = [('PEDIDOS', 'Notif_atraso_enviada'), ('PEDIDOS', 'Estado_pago'),
            ('OBJETOS', 'medidas_objeto'), ('OBJETOS', 'volumen_m3_objeto')]
DURACIONES_VIEJAS = {'Flete urbano': 4, 'Mudanza local': 5, 'Mudanza nacional': 6}
DURACIONES = {'Flete urbano': 5, 'Mudanza local': 10, 'Mudanza nacional': 48}


def columnas_existentes(cursor, tabla):
    cursor.execute('SELECT column_name FROM information_schema.columns '
                   'WHERE table_schema = DATABASE() AND table_name = %s', [tabla])
    return {fila[0].lower() for fila in cursor.fetchall()}


def sacar_columnas(apps, schema_editor):
    if schema_editor.connection.vendor != 'mysql':
        return
    with schema_editor.connection.cursor() as cursor:
        for tabla, columna in COLUMNAS:
            if columna.lower() in columnas_existentes(cursor, tabla):
                cursor.execute(f'ALTER TABLE `{tabla}` DROP COLUMN `{columna}`')
    Servicio = apps.get_model('usuarios', 'Servicio')
    principales = {s.Tipo_servicio: s for s in Servicio.objects.filter(Categoria='Principal',
                                                                         Tipo_servicio__in=DURACIONES)}
    if principales and all(principales[t].Duracion_horas == h for t, h in DURACIONES_VIEJAS.items() if t in principales):
        for tipo, servicio in principales.items():
            servicio.Duracion_horas = DURACIONES[tipo]
            servicio.save(update_fields=['Duracion_horas'])


class Migration(migrations.Migration):
    atomic = False  # en MySQL los ALTER TABLE no van dentro de una transacción

    dependencies = [
        ('usuarios', '0014_camiones_por_tamano_y_adicionales'),
    ]

    operations = [
        migrations.RunPython(sacar_columnas, migrations.RunPython.noop),
    ]
