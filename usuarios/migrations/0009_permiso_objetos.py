from django.db import migrations


def adelante(apps, schema_editor):
    """Quien ya gestionaba servicios recibe también el catálogo de objetos.
    En una base vacía no hay roles: init_data asigna el permiso al crearlos."""
    Permiso = apps.get_model('usuarios', 'Permiso')
    PermisoRol = apps.get_model('usuarios', 'PermisoRol')
    nuevo, _ = Permiso.objects.get_or_create(
        nom_permiso='OBJ_GESTIONAR', defaults={'desc_permiso': 'Alta, modificación y baja del catálogo de objetos'})
    for pr in PermisoRol.objects.filter(idPermiso__nom_permiso='SRV_GESTIONAR'):
        PermisoRol.objects.get_or_create(idRol_id=pr.idRol_id, idPermiso=nuevo)


class Migration(migrations.Migration):
    dependencies = [('usuarios', '0008_catalogo_objetos')]
    operations = [migrations.RunPython(adelante, migrations.RunPython.noop)]
