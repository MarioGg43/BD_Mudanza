"""ABM de servicios (tabla maestra del Hito 3) con sus materiales."""
import io
from datetime import time, timedelta

from django.core.management import call_command
from django.test import TestCase
from django.utils import timezone

from pedidos import reglas
from usuarios.models import Servicio, Usuario

ADMIN, CLIENTE = 35123456, 29876543


class ServiciosTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command('init_data', stdout=io.StringIO())

    def entrar(self, dni):
        s = self.client.session
        s['usuario_dni'] = dni
        s['usuario_rol'] = Usuario.objects.get(DNI=dni).idRol.nom_rol
        s.save()

    def test_lista(self):
        self.entrar(ADMIN)
        r = self.client.get('/servicios/')
        self.assertContains(r, 'Mudanza nacional')
        self.assertContains(r, 'Mantas, film y cintas')

    def test_alta_con_materiales(self):
        self.entrar(ADMIN)
        r = self.client.post('/servicios/nuevo/', {'Tipo_servicio': 'Guardamuebles', 'Categoria': 'Adicional',
                                                   'Precio_base': '', 'Activo': 'on',
                                                   'materiales': 'Cajas, burbujas ,  cinta'})
        self.assertRedirects(r, '/servicios/')
        s = Servicio.objects.get(Tipo_servicio='Guardamuebles')
        self.assertEqual((s.Categoria, s.Precio_base), (Servicio.ADICIONAL, 0))
        self.assertEqual(sorted(s.recursos.values_list('Materiales', flat=True)), ['Cajas', 'burbujas', 'cinta'])

    def test_precio_tiene_que_ser_positivo(self):
        self.entrar(ADMIN)
        r = self.client.post('/servicios/nuevo/', {'Tipo_servicio': 'Gratis', 'Categoria': 'Principal',
                                                   'Precio_base': '0', 'materiales': ''})
        self.assertEqual(r.status_code, 200)
        self.assertIn('Precio_base', r.context['form'].errors)

    def test_material_demasiado_largo(self):
        self.entrar(ADMIN)
        r = self.client.post('/servicios/nuevo/', {'Tipo_servicio': 'X', 'Precio_base': '1', 'materiales': 'a' * 51})
        self.assertIn('materiales', r.context['form'].errors)

    def test_editar_reemplaza_los_materiales(self):
        self.entrar(ADMIN)
        s = Servicio.objects.get(Tipo_servicio='Flete urbano')
        self.client.post(f'/servicios/{s.pk}/editar/', {'Tipo_servicio': 'Flete urbano', 'Categoria': 'Principal', 'Precio_base': '80000',
                                                        'Activo': 'on', 'materiales': 'Correas'})
        s.refresh_from_db()
        self.assertEqual(s.Precio_base, 80000)
        self.assertEqual(list(s.recursos.values_list('Materiales', flat=True)), ['Correas'])

    def test_baja_logica_conserva_los_pedidos_viejos(self):
        self.entrar(ADMIN)
        s = Servicio.objects.get(Tipo_servicio='Mudanza local')
        self.assertRedirects(self.client.post(f'/servicios/{s.pk}/baja/'), '/servicios/')
        s.refresh_from_db()
        self.assertFalse(s.Activo)
        self.assertTrue(s.detalles.exists())  # el pedido de ejemplo lo sigue teniendo
        with self.assertRaises(reglas.ErrorPedido):
            reglas.registrar_pedido(
                Usuario.objects.get(DNI=CLIENTE), timezone.localdate() + timedelta(days=1), time(9, 0),
                'A 1', 'B 2', s.id_servicio, 'AD-321-JK', [{'descripcion': 'Cajas', 'cantidad': 1}])

    def test_la_categoria_es_obligatoria(self):
        self.entrar(ADMIN)
        r = self.client.post('/servicios/nuevo/', {'Tipo_servicio': 'X', 'Precio_base': '1', 'materiales': ''})
        self.assertIn('Categoria', r.context['form'].errors)

    def test_un_adicional_no_guarda_precio(self):
        self.entrar(ADMIN)
        self.client.post('/servicios/nuevo/', {'Tipo_servicio': 'Seguro', 'Categoria': 'Adicional',
                                               'Precio_base': '9999', 'Activo': 'on', 'materiales': ''})
        self.assertEqual(Servicio.objects.get(Tipo_servicio='Seguro').Precio_base, 0)

    def test_la_lista_muestra_la_categoria(self):
        self.entrar(ADMIN)
        r = self.client.get('/servicios/')
        self.assertContains(r, '<td>Adicional</td>', html=True)
        self.assertContains(r, 'Embalaje')
        self.assertContains(r, 'Sin precio')

    def test_el_cliente_no_entra(self):
        self.entrar(CLIENTE)
        self.assertEqual(self.client.get('/servicios/').status_code, 403)
