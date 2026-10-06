"""Catálogo de permisos, datos iniciales y migración de datos."""
import importlib
import io

from django.apps import apps
from django.core.management import call_command
from django.test import TestCase

from usuarios.models import Permiso, PermisoRol, Rol
from usuarios.permisos import CATALOGO, PERMISOS_INICIALES, permisos_de, tiene_permiso
from usuarios.models import Usuario

CODIGOS = [c for _, c, _ in CATALOGO]


def permisos_del_rol(nombre):
    return set(PermisoRol.objects.filter(idRol__nom_rol=nombre)
               .values_list('idPermiso__nom_permiso', flat=True))


class CatalogoTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command('init_data', stdout=io.StringIO())

    def test_catalogo_de_15_permisos(self):
        self.assertEqual(len(CODIGOS), 15)
        self.assertEqual(set(Permiso.objects.values_list('nom_permiso', flat=True)), set(CODIGOS))
        self.assertNotIn('MUDANZAS_ADMIN', CODIGOS)

    def test_permisos_iniciales(self):
        for rol, codigos in PERMISOS_INICIALES.items():
            self.assertEqual(permisos_del_rol(rol), set(codigos), rol)
        self.assertNotIn('PED_REGISTRAR', PERMISOS_INICIALES['Administrador'])
        self.assertEqual(len(PERMISOS_INICIALES['Administrador']), 14)

    def test_init_data_no_repone_un_permiso_quitado(self):
        PermisoRol.objects.filter(idRol__nom_rol='Administrador', idPermiso__nom_permiso='USR_BAJA').delete()
        call_command('init_data', stdout=io.StringIO())
        self.assertNotIn('USR_BAJA', permisos_del_rol('Administrador'))

    def test_permisos_de_y_tiene_permiso(self):
        admin = Usuario.objects.get(DNI=35123456)
        self.assertIn('ROL_GESTIONAR', permisos_de(admin))
        self.assertTrue(tiene_permiso(admin, 'VEH_GESTIONAR'))
        self.assertFalse(tiene_permiso(admin, 'PED_REGISTRAR'))
        self.assertEqual(permisos_de(None), set())


class MigracionDatosTest(TestCase):
    def test_actualiza_una_base_vieja(self):
        call_command('init_data', stdout=io.StringIO())
        # simular la base anterior: MUDANZAS_ADMIN y sin los tres permisos nuevos
        Permiso.objects.filter(nom_permiso__in=['USR_CONSULTAR', 'USR_CAMBIAR_ROL', 'ROL_GESTIONAR']).delete()
        Permiso.objects.filter(nom_permiso='VEH_GESTIONAR').update(nom_permiso='MUDANZAS_ADMIN')
        migracion = importlib.import_module('usuarios.migrations.0006_permisos_editables')
        migracion.adelante(apps, None)
        self.assertFalse(Permiso.objects.filter(nom_permiso='MUDANZAS_ADMIN').exists())
        self.assertTrue({'USR_CONSULTAR', 'USR_CAMBIAR_ROL', 'ROL_GESTIONAR', 'VEH_GESTIONAR'}
                        <= permisos_del_rol('Administrador'))
        self.assertEqual(Permiso.objects.count(), 15)
