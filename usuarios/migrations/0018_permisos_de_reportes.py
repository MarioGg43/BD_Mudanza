"""Parcial N° 2 (M2): los permisos de los reportes consolidados, para el Administrador.

init_data solo da permisos al crear un rol; en una base que ya existe, esta migración los agrega.
REP_FINANZAS es el «reporte sensible restringido por perfil» que pide la consigna."""
from django.db import migrations

NUEVOS = [
    ('REP_CONSULTAR', 'Ver los reportes del personal y de cambios y cancelaciones'),
    ('REP_FINANZAS', 'Ver el reporte con montos (uso e ingresos de la flota)'),
]


def agregar(apps, schema_editor):
    Permiso = apps.get_model('usuarios', 'Permiso')
    Rol = apps.get_model('usuarios', 'Rol')
    PermisoRol = apps.get_model('usuarios', 'PermisoRol')
    admin = Rol.objects.filter(nom_rol='Administrador').first()
    for codigo, descripcion in NUEVOS:
        permiso, _ = Permiso.objects.get_or_create(nom_permiso=codigo, defaults={'desc_permiso': descripcion})
        if admin:
            PermisoRol.objects.get_or_create(idRol=admin, idPermiso=permiso)


def quitar(apps, schema_editor):
    apps.get_model('usuarios', 'Permiso').objects.filter(nom_permiso__in=[c for c, _ in NUEVOS]).delete()


class Migration(migrations.Migration):
    dependencies = [('usuarios', '0017_relevamiento_y_recargo')]
    operations = [migrations.RunPython(agregar, quitar)]
