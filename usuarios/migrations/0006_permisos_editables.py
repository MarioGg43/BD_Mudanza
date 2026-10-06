from django.db import migrations

NUEVOS = [
    ('USR_CONSULTAR', 'Ver el panel de usuarios'),
    ('USR_CAMBIAR_ROL', 'Cambiar el rol de un usuario'),
    ('ROL_GESTIONAR', 'Ver, crear y editar roles y sus permisos'),
]


def adelante(apps, schema_editor):
    """Bases que ya existen: MUDANZAS_ADMIN pasa a VEH_GESTIONAR y el Administrador
    recibe los permisos nuevos. En una base vacía no hay roles y no asigna nada."""
    Permiso = apps.get_model('usuarios', 'Permiso')
    Rol = apps.get_model('usuarios', 'Rol')
    PermisoRol = apps.get_model('usuarios', 'PermisoRol')
    viejo = Permiso.objects.filter(nom_permiso='MUDANZAS_ADMIN').first()
    actual = Permiso.objects.filter(nom_permiso='VEH_GESTIONAR').first()
    if viejo and not actual:
        viejo.nom_permiso = 'VEH_GESTIONAR'
        viejo.desc_permiso = 'Alta, modificación y baja de vehículos'
        viejo.save()
    elif viejo:
        # ya existen los dos: los roles que tenían MUDANZAS_ADMIN pasan a VEH_GESTIONAR
        for pr in PermisoRol.objects.filter(idPermiso=viejo):
            PermisoRol.objects.get_or_create(idRol_id=pr.idRol_id, idPermiso=actual)
        PermisoRol.objects.filter(idPermiso=viejo).delete()
        viejo.delete()
    nuevos = [Permiso.objects.get_or_create(nom_permiso=c, defaults={'desc_permiso': d})[0] for c, d in NUEVOS]
    admin = Rol.objects.filter(nom_rol='Administrador').first()
    if admin:
        vehiculos = Permiso.objects.filter(nom_permiso='VEH_GESTIONAR').first()
        for p in nuevos + ([vehiculos] if vehiculos else []):
            PermisoRol.objects.get_or_create(idRol=admin, idPermiso=p)


class Migration(migrations.Migration):
    dependencies = [('usuarios', '0005_observacion_inventario')]
    operations = [migrations.RunPython(adelante, migrations.RunPython.noop)]
