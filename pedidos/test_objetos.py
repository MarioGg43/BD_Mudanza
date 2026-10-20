"""ABM del catálogo de objetos que el cliente elige para el inventario."""
import io

from django.core.management import call_command
from django.test import TestCase

from usuarios.models import Objeto, PermisoRol, Usuario

ADMIN, CLIENTE = 35123456, 29876543


class ObjetosTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command('init_data', stdout=io.StringIO())

    def entrar(self, dni):
        s = self.client.session
        s['usuario_dni'] = dni
        s['usuario_rol'] = Usuario.objects.get(DNI=dni).idRol.nom_rol
        s.save()

    def test_el_admin_tiene_el_permiso(self):
        self.assertTrue(PermisoRol.objects.filter(idRol__nom_rol='Administrador',
                                                  idPermiso__nom_permiso='OBJ_GESTIONAR').exists())

    def test_lista_y_menu(self):
        self.entrar(ADMIN)
        r = self.client.get('/objetos/')
        self.assertContains(r, 'Bolsos y valijas')
        self.assertContains(r, 'href="/objetos/"')

    def test_alta_normaliza_el_nombre(self):
        self.entrar(ADMIN)
        r = self.client.post('/objetos/nuevo/', {'nom_objeto': '  piano   vertical ', 'Activo': 'on'})
        self.assertRedirects(r, '/objetos/')
        self.assertTrue(Objeto.objects.filter(nom_objeto='Piano vertical', Activo=True).exists())

    def test_no_se_repite_aunque_cambien_las_mayusculas(self):
        self.entrar(ADMIN)
        r = self.client.post('/objetos/nuevo/', {'nom_objeto': 'MESA', 'Activo': 'on'})
        self.assertEqual(r.status_code, 200)
        self.assertIn('nom_objeto', r.context['form'].errors)

    def test_otro_es_fijo(self):
        self.entrar(ADMIN)
        otro = Objeto.objects.get(nom_objeto='Otro')
        self.assertRedirects(self.client.post(f'/objetos/{otro.pk}/baja/'), '/objetos/')
        otro.refresh_from_db()
        self.assertTrue(otro.Activo)
        self.assertRedirects(self.client.get(f'/objetos/{otro.pk}/editar/'), '/objetos/')
        r = self.client.post('/objetos/nuevo/', {'nom_objeto': 'otro', 'Activo': 'on'})
        self.assertIn('nom_objeto', r.context['form'].errors)

    def test_baja_logica_lo_saca_del_formulario(self):
        self.entrar(ADMIN)
        mesa = Objeto.objects.get(nom_objeto='Mesa')
        self.client.post(f'/objetos/{mesa.pk}/baja/')
        mesa.refresh_from_db()
        self.assertFalse(mesa.Activo)
        self.entrar(CLIENTE)
        self.assertNotContains(self.client.get('/pedidos/nuevo/'), '>Mesa</option>')

    def test_el_cliente_no_entra(self):
        self.entrar(CLIENTE)
        self.assertEqual(self.client.get('/objetos/').status_code, 403)
