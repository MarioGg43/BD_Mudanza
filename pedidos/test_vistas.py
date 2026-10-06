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
