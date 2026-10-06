"""Pruebas de las pantallas del pedido: permisos, consulta y detalle."""
import io
from datetime import timedelta
from decimal import Decimal

from django.core.management import call_command
from django.test import TestCase
from django.utils import timezone

from pedidos import reglas
from pedidos.permisos import tiene_permiso
from usuarios.models import Pedido, Rol, Servicio, Usuario
from usuarios.utils import hash_password

ADMIN, CHOFER, CLIENTE = 35123456, 40987654, 29876543


class BaseVistas(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command('init_data', stdout=io.StringIO())
        cls.cliente = Usuario.objects.get(DNI=CLIENTE)
        cls.otro = Usuario.objects.create(
            DNI=31555666, Nombre='Jorge', Apellido='Herrera', Correo='jorge.herrera@ejemplo.com',
            NombreUsuario='herreraj', Clave=hash_password('Cliente123!'), DebeCambiarClave=False,
            idRol=Rol.objects.get(nom_rol='Cliente'))
        cls.local = Servicio.objects.get(Tipo_servicio='Mudanza local')

    def entrar(self, dni):
        s = self.client.session
        s['usuario_dni'] = dni
        s['usuario_rol'] = Usuario.objects.get(DNI=dni).idRol.nom_rol
        s.save()

    def pedido_de(self, cliente, dias=1, patente='AD-321-JK'):
        return reglas.registrar_pedido(
            cliente, timezone.localdate() + timedelta(days=dias), 'Origen 1', 'Destino 2',
            [self.local.id_servicio], patente,
            [{'descripcion': 'Cajas', 'cantidad': 2, 'peso': Decimal('10'), 'fragil': False}])


class PermisosTest(BaseVistas):
    def test_tiene_permiso_segun_la_tabla(self):
        admin, chofer = Usuario.objects.get(DNI=ADMIN), Usuario.objects.get(DNI=CHOFER)
        self.assertTrue(tiene_permiso(self.cliente, 'PED_REGISTRAR'))
        self.assertFalse(tiene_permiso(self.cliente, 'PED_ANULAR'))
        self.assertTrue(tiene_permiso(admin, 'PED_ANULAR'))
        self.assertFalse(tiene_permiso(admin, 'PED_REGISTRAR'))
        self.assertFalse(tiene_permiso(chofer, 'PED_CONSULTAR'))

    def test_sin_sesion_va_al_login(self):
        self.assertRedirects(self.client.get('/pedidos/'), '/login/')

    def test_chofer_no_entra(self):
        self.entrar(CHOFER)
        self.assertEqual(self.client.get('/pedidos/').status_code, 403)

    def test_login_del_cliente_va_a_sus_pedidos(self):
        r = self.client.post('/login/', {'usuario': 'gomezm', 'clave': 'Cliente123!'})
        self.assertRedirects(r, '/pedidos/')

    def test_el_portal_manda_al_cliente_a_sus_pedidos(self):
        self.entrar(CLIENTE)
        self.assertRedirects(self.client.get('/portal/'), '/pedidos/')


class ConsultaTest(BaseVistas):
    def setUp(self):
        self.mio = self.pedido_de(self.cliente)
        self.ajeno = self.pedido_de(self.otro, dias=2)

    def test_el_cliente_ve_solo_los_suyos(self):
        self.entrar(CLIENTE)
        r = self.client.get('/pedidos/')
        ids = [p.pk for p in r.context['pedidos']]
        self.assertIn(self.mio.pk, ids)
        self.assertNotIn(self.ajeno.pk, ids)
        self.assertNotIn('cliente', r.context['form'].fields)

    def test_el_admin_ve_todos_y_filtra_por_cliente(self):
        self.entrar(ADMIN)
        r = self.client.get('/pedidos/')
        self.assertEqual(len(r.context['pedidos']), 3)
        r = self.client.get('/pedidos/', {'cliente': self.otro.id_usuario})
        self.assertEqual([p.pk for p in r.context['pedidos']], [self.ajeno.pk])

    def test_filtros_por_fecha_estado_y_servicio(self):
        self.entrar(ADMIN)
        hoy = timezone.localdate()
        r = self.client.get('/pedidos/', {'desde': (hoy + timedelta(days=2)).isoformat(),
                                          'estado': 'Pendiente', 'servicio': self.local.id_servicio})
        self.assertEqual([p.pk for p in r.context['pedidos']], [self.ajeno.pk])

    def test_detalle_propio(self):
        self.entrar(CLIENTE)
        r = self.client.get(f'/pedidos/{self.mio.pk}/')
        self.assertContains(r, 'Origen 1')
        self.assertContains(r, 'Pendiente')

    def test_detalle_ajeno_da_404(self):
        self.entrar(CLIENTE)
        self.assertEqual(self.client.get(f'/pedidos/{self.ajeno.pk}/').status_code, 404)

    def test_el_admin_ve_cualquier_detalle(self):
        self.entrar(ADMIN)
        self.assertEqual(self.client.get(f'/pedidos/{self.ajeno.pk}/').status_code, 200)


class RegistrarPantallaTest(BaseVistas):
    def datos(self, **cambios):
        manana = (timezone.localdate() + timedelta(days=1)).isoformat()
        d = {'fecha_servicio': manana, 'origen': 'Av. Belgrano 100', 'destino': 'Mitre 50',
             'servicios': [self.local.id_servicio], 'vehiculo': 'AD-321-JK',
             'inv-TOTAL_FORMS': '2', 'inv-INITIAL_FORMS': '0', 'inv-MIN_NUM_FORMS': '1', 'inv-MAX_NUM_FORMS': '50',
             'inv-0-descripcion': 'Heladera', 'inv-0-cantidad': '1', 'inv-0-peso': '80', 'inv-0-fragil': 'on',
             'inv-1-descripcion': 'Cajas', 'inv-1-cantidad': '10', 'inv-1-peso': '12.5'}
        d.update(cambios)
        return d

    def test_el_cliente_registra_y_va_al_detalle(self):
        self.entrar(CLIENTE)
        r = self.client.post('/pedidos/nuevo/', self.datos())
        p = Pedido.objects.latest('id_pedido')
        self.assertRedirects(r, f'/pedidos/{p.pk}/', fetch_redirect_response=False)
        self.assertEqual((p.idUsuario, p.estado, p.total), (self.cliente, 'Pendiente', 185000))
        self.assertEqual(p.inventario.count(), 2)
        self.assertContains(self.client.get(r.url), f'Pedido N° {p.pk} registrado')

    def test_error_de_reglas_vuelve_al_formulario_con_los_datos(self):
        self.entrar(CLIENTE)
        antes = Pedido.objects.count()
        r = self.client.post('/pedidos/nuevo/', self.datos(**{'inv-0-peso': '1700'}))
        self.assertEqual(r.status_code, 200)
        self.assertIn('vehiculo', r.context['form'].errors)
        self.assertContains(r, 'Av. Belgrano 100')
        self.assertEqual(Pedido.objects.count(), antes)

    def test_sin_objetos(self):
        self.entrar(CLIENTE)
        r = self.client.post('/pedidos/nuevo/', self.datos(**{
            'inv-TOTAL_FORMS': '1', 'inv-0-descripcion': '', 'inv-0-cantidad': '', 'inv-0-peso': ''}))
        self.assertEqual(r.status_code, 200)
        self.assertTrue(r.context['items'].non_form_errors() or r.context['items'].errors[0])

    def test_el_admin_no_registra(self):
        self.entrar(ADMIN)
        self.assertEqual(self.client.get('/pedidos/nuevo/').status_code, 403)

    def test_vehiculos_libres_en_json(self):
        self.entrar(CLIENTE)
        self.pedido_de(self.otro)  # ocupa AD-321-JK mañana
        manana = (timezone.localdate() + timedelta(days=1)).isoformat()
        r = self.client.get('/pedidos/vehiculos-libres/', {'fecha': manana}).json()
        self.assertEqual([v['patente'] for v in r['vehiculos']], ['AE-123-CD'])
        self.assertEqual(r['vehiculos'][0]['capacidad_kg'], 5000.0)
        self.assertEqual(self.client.get('/pedidos/vehiculos-libres/', {'fecha': 'mal'}).json(), {'vehiculos': []})
