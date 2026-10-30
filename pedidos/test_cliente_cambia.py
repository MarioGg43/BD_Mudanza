"""El cliente modifica o cancela su pedido hasta 24 h antes; si estaba confirmado vuelve a Pendiente."""
from datetime import datetime, time, timedelta
from unittest import mock

from django.utils import timezone

from pedidos import reglas
from pedidos.test_reglas import CLIENTE, BaseReglas, obj
from usuarios.models import Pedido, Reprogramacion, Usuario


class ClienteCambiaTest(BaseReglas):
    def setUp(self):
        self.chofer = Usuario.objects.get(DNI=40987654)
        self.p = self.registrar(fecha_servicio=self.dia(3), id_servicio=self.flete.id_servicio)  # en 3 días a las 9
        reglas.asignar_personal(self.p.pk, self.chofer.pk)
        reglas.confirmar(self.p.pk)

    def modificar(self, **cambios):
        datos = dict(fecha_servicio=self.dia(3), hora_servicio=time(14, 0), origen='Av. Belgrano 100, Salta',
                     destino='Mitre 50, Cerrillos', id_servicio=self.local.id_servicio, patente='AD-321-JK',
                     items=[{'objeto': obj('Heladera'), 'cantidad': 1, 'fragil': True},
                            {'objeto': obj('Sillas'), 'cantidad': 6, 'fragil': False}],
                     ids_adicionales=[self.embalaje.id_servicio])
        datos.update(cambios)
        return reglas.modificar_pedido(self.p.pk, self.cliente, **datos)

    def entrar(self, dni):
        s = self.client.session
        s['usuario_dni'], s['usuario_rol'] = dni, Usuario.objects.get(DNI=dni).idRol.nom_rol
        s.save()

    def test_modifica_todo_vuelve_a_pendiente_y_queda_el_cambio_de_horario(self):
        self.modificar()
        self.p.refresh_from_db()
        self.assertEqual((self.p.estado, self.p.hora_servicio, self.p.duracion_horas), (Pedido.PENDIENTE, time(14, 0), 10))
        self.assertEqual(self.p.total, 185000 + 25000)
        self.assertEqual(sorted(i.idObjeto.nom_objeto for i in self.p.inventario.all()), ['Heladera', 'Sillas'])
        r = self.p.reprogramaciones.get()
        self.assertEqual((r.motivo, r.usuario, r.visto_cliente), ('Pedido del cliente', self.cliente, True))
        self.assertEqual(self.p.chofer, self.chofer)        # sigue libre: se queda

    def test_no_dentro_de_las_24_horas(self):
        momento = self.p.inicio - timedelta(hours=23)
        with mock.patch('django.utils.timezone.now', return_value=momento):
            with self.assertRaises(reglas.ErrorPedido):
                self.modificar(fecha_servicio=self.dia(5))
            with self.assertRaises(reglas.ErrorPedido):
                reglas.cancelar_por_cliente(self.p.pk, self.cliente, 'Ya no me mudo')

    def test_la_fecha_nueva_tambien_con_24_horas(self):
        if timezone.localtime().hour >= 22:
            self.skipTest('muy tarde para armar el caso')
        with self.assertRaises(reglas.ErrorPedido) as ctx:
            self.modificar(fecha_servicio=timezone.localdate(), hora_servicio=time(23, 0))
        self.assertIn('fecha_servicio', ctx.exception.errores)

    def test_otro_cliente_no_puede(self):
        otro = Usuario.objects.create(DNI=31222333, Nombre='Ana', Apellido='Paz', Correo='ana.paz@ejemplo.com',
                                      NombreUsuario='paza', Clave='x', idRol=self.cliente.idRol)
        with self.assertRaises(reglas.ErrorPedido):
            reglas.modificar_pedido(self.p.pk, otro, self.dia(3), time(9, 0), 'A 1', 'B 2', self.flete.id_servicio,
                                    'AD-321-JK', [{'objeto': obj('Cajas'), 'cantidad': 1}])

    def test_cancela(self):
        reglas.cancelar_por_cliente(self.p.pk, self.cliente, 'Conseguí quien me ayude')
        self.p.refresh_from_db()
        self.assertEqual((self.p.estado, self.p.usuario_anulacion, self.p.motivo_anulacion),
                         (Pedido.ANULADO, self.cliente, 'Conseguí quien me ayude'))

    def test_pantallas_del_cliente(self):
        self.entrar(CLIENTE)
        r = self.client.get(f'/pedidos/{self.p.pk}/')
        self.assertContains(r, f'/pedidos/{self.p.pk}/modificar/')
        self.assertContains(r, f'/pedidos/{self.p.pk}/cancelar/')
        r = self.client.get(f'/pedidos/{self.p.pk}/modificar/')
        self.assertContains(r, f'Modificar pedido N° {self.p.pk}')
        self.assertEqual(len(r.context['items_iniciales']), 2)            # lo que ya tenía cargado
        datos = {'fecha_servicio': self.dia(4).isoformat(), 'hora_servicio': '10:00', 'origen': 'Av. Belgrano 100, Salta',
                 'destino': 'Mitre 50, Cerrillos', 'servicio': self.flete.id_servicio, 'vehiculo': 'AD-321-JK',
                 'inv-TOTAL_FORMS': '1', 'inv-INITIAL_FORMS': '0', 'inv-MIN_NUM_FORMS': '1', 'inv-MAX_NUM_FORMS': '50',
                 'inv-0-objeto': obj('Cajas').pk, 'inv-0-cantidad': '20'}
        r = self.client.post(f'/pedidos/{self.p.pk}/modificar/', datos)
        self.assertRedirects(r, f'/pedidos/{self.p.pk}/', fetch_redirect_response=False)
        self.p.refresh_from_db()
        self.assertEqual((self.p.fecha_servicio, self.p.estado), (self.dia(4), Pedido.PENDIENTE))
        libres = self.client.get('/pedidos/vehiculos-libres/', {'fecha': self.dia(4).isoformat(), 'hora': '10:00',
                                                                'servicio': self.flete.id_servicio, 'pedido': self.p.pk}).json()
        self.assertIn('AD-321-JK', [v['patente'] for v in libres['vehiculos']])  # su propio camión cuenta como libre
        r = self.client.post(f'/pedidos/{self.p.pk}/cancelar/', {'motivo': 'Al final no me mudo'})
        self.assertRedirects(r, f'/pedidos/{self.p.pk}/', fetch_redirect_response=False)
        self.assertEqual(Pedido.objects.get(pk=self.p.pk).estado, Pedido.ANULADO)

    def test_el_admin_no_ve_los_botones_del_cliente(self):
        s = self.client.session
        s['usuario_dni'], s['usuario_rol'] = 35123456, 'Administrador'
        s.save()
        self.assertNotContains(self.client.get(f'/pedidos/{self.p.pk}/'), f'/pedidos/{self.p.pk}/modificar/')
