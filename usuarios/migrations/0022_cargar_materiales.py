"""Control de materiales: carga el catálogo inicial con su stock (como un ingreso, así queda
registrado) y pasa los materiales de cada servicio, que hasta ahora eran texto («Mantas, film y
cintas»), a materiales de verdad con su cantidad sugerida por mudanza. Agrega el permiso
MAT_GESTIONAR para el Administrador."""
import re

from django.db import migrations

# nombre, unidad, reutilizable, stock inicial, stock mínimo
CATALOGO = [
    ('Mantas acolchadas', 'unidades', True, 60, 20),
    ('Correas', 'unidades', True, 30, 10),
    ('Kit de herramientas', 'kits', True, 4, 2),
    ('Film stretch', 'rollos', False, 40, 10),
    ('Cinta de embalar', 'rollos', False, 80, 20),
    ('Zunchos', 'rollos', False, 15, 5),
    ('Cajas de cartón', 'unidades', False, 200, 50),
    ('Papel burbuja', 'rollos', False, 20, 6),
]
# cuánto se sugiere llevar por mudanza, según el servicio
SUGERIDOS = {
    'Mudanza local': [('Mantas acolchadas', 12), ('Film stretch', 2), ('Cinta de embalar', 3)],
    'Mudanza nacional': [('Mantas acolchadas', 20), ('Film stretch', 4), ('Cinta de embalar', 5), ('Zunchos', 2)],
    'Flete urbano': [('Correas', 6), ('Mantas acolchadas', 6)],
    'Embalaje': [('Cajas de cartón', 20), ('Papel burbuja', 2), ('Cinta de embalar', 3)],
    'Desarmado y armado de muebles': [('Kit de herramientas', 1)],
}
# para servicios que cargó el administrador: qué palabra del texto viejo es qué material
PALABRAS = {'manta': 'Mantas acolchadas', 'correa': 'Correas', 'herramienta': 'Kit de herramientas',
            'film': 'Film stretch', 'cinta': 'Cinta de embalar', 'zuncho': 'Zunchos', 'caja': 'Cajas de cartón',
            'burbuja': 'Papel burbuja'}


def cargar(apps, schema_editor):
    Material = apps.get_model('usuarios', 'Material')
    Movimiento = apps.get_model('usuarios', 'MovimientoMaterial')
    Recurso = apps.get_model('usuarios', 'RecursoAsignado')
    Servicio = apps.get_model('usuarios', 'Servicio')

    materiales = {}
    for nombre, unidad, reutilizable, stock, minimo in CATALOGO:
        m, creado = Material.objects.get_or_create(nom_material=nombre, defaults={
            'unidad_material': unidad, 'reutilizable': reutilizable, 'stock_material': stock, 'stock_min_material': minimo})
        if creado:
            Movimiento.objects.create(idMaterial=m, tipo_mov='Ingreso', cant_mov=stock, observacion_mov='Stock inicial')
        materiales[nombre] = m

    for servicio in Servicio.objects.all():
        viejos = list(Recurso.objects.filter(idServicio=servicio, idMaterial__isnull=True))
        if servicio.Tipo_servicio in SUGERIDOS:
            nuevos = SUGERIDOS[servicio.Tipo_servicio]
        else:  # se interpreta el texto: «Mantas, film y cintas» → mantas, film, cinta
            nuevos = []
            for r in viejos:
                for parte in re.split(r',| y ', r.Materiales.lower()):
                    parte = parte.strip()
                    if not parte:
                        continue
                    nombre = next((n for clave, n in PALABRAS.items() if clave in parte), None)
                    if nombre is None:  # algo que no está en el catálogo: se agrega con stock 0
                        nombre = parte.capitalize()[:60]
                        materiales.setdefault(nombre, Material.objects.get_or_create(nom_material=nombre)[0])
                    if nombre not in [n for n, _ in nuevos]:
                        nuevos.append((nombre, 1))
        for r in viejos:
            r.delete()
        for nombre, cantidad in nuevos:
            Recurso.objects.get_or_create(idServicio=servicio, idMaterial=materiales[nombre],
                                          defaults={'cant_sugerida': cantidad, 'Materiales': ''})

    Permiso = apps.get_model('usuarios', 'Permiso')
    permiso, _ = Permiso.objects.get_or_create(
        nom_permiso='MAT_GESTIONAR', defaults={'desc_permiso': 'Gestionar los materiales y su stock'})
    admin = apps.get_model('usuarios', 'Rol').objects.filter(nom_rol='Administrador').first()
    if admin:
        apps.get_model('usuarios', 'PermisoRol').objects.get_or_create(idRol=admin, idPermiso=permiso)


def volver(apps, schema_editor):
    """Vuelve al texto: cada servicio con los nombres de sus materiales."""
    Recurso = apps.get_model('usuarios', 'RecursoAsignado')
    for r in Recurso.objects.filter(idMaterial__isnull=False):
        r.Materiales = r.idMaterial.nom_material[:50]
        r.save()
    apps.get_model('usuarios', 'Permiso').objects.filter(nom_permiso='MAT_GESTIONAR').delete()


class Migration(migrations.Migration):
    dependencies = [('usuarios', '0021_materiales_y_movimientos')]
    operations = [migrations.RunPython(cargar, volver)]
