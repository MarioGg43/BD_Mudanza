"""Parcial N° 2 (M3): los umbrales iniciales de las reglas de notificación y el permiso para
cambiarlos (CFG_GESTIONAR), para el Administrador. Después se cambian desde la pantalla de
configuración: no están escritos en el código."""
from django.db import migrations

PARAMETROS = [
    ('horas_sin_confirmar', '48', 'Regla 1: avisar si un pedido sigue pendiente a menos de estas horas de la mudanza'),
    ('correo_empresa', '', 'Regla 1: correo de la empresa que recibe el aviso de pedidos sin confirmar'),
    ('minutos_atraso', '60', 'Regla 2: avisar si una mudanza confirmada pasó su fin estimado hace más de estos minutos'),
    ('cancelaciones_cliente', '3', 'Regla 3: avisar cuando un cliente llega a esta cantidad de cancelaciones...'),
    ('dias_cancelaciones', '90', 'Regla 3: ...en estos últimos días'),
    ('correo_al_cliente', '1', 'Regla 4: mandarle un correo al cliente cuando se confirma o reprograma su mudanza (1 = sí, 0 = no)'),
]


def agregar(apps, schema_editor):
    Configuracion = apps.get_model('usuarios', 'Configuracion')
    for clave, valor, descripcion in PARAMETROS:
        Configuracion.objects.get_or_create(clave=clave, defaults={'valor': valor, 'descripcion': descripcion})
    Permiso = apps.get_model('usuarios', 'Permiso')
    permiso, _ = Permiso.objects.get_or_create(
        nom_permiso='CFG_GESTIONAR', defaults={'desc_permiso': 'Cambiar los umbrales de las alertas y notificaciones'})
    admin = apps.get_model('usuarios', 'Rol').objects.filter(nom_rol='Administrador').first()
    if admin:
        apps.get_model('usuarios', 'PermisoRol').objects.get_or_create(idRol=admin, idPermiso=permiso)


def quitar(apps, schema_editor):
    apps.get_model('usuarios', 'Configuracion').objects.filter(clave__in=[c for c, _, _ in PARAMETROS]).delete()
    apps.get_model('usuarios', 'Permiso').objects.filter(nom_permiso='CFG_GESTIONAR').delete()


class Migration(migrations.Migration):
    dependencies = [('usuarios', '0019_alertas_configuracion_y_notificacion')]
    operations = [migrations.RunPython(agregar, quitar)]
