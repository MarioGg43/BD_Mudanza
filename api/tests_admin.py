"""La API del administrador: lista con avisos, personal, confirmar, servicios, reprogramar y anular."""
from pedidos.test_reglas import ADMIN, CLIENTE
from usuarios.models import Pedido, PersonalPedido, Usuario
from .tests import ApiBase

CHOFER = 40987654


class ApiAdminTest(ApiBase):
    def setUp(self):
        super().setUp()
        self.admin_h = self.entrar(str(ADMIN))
        self.p = self.registrar(fecha_servicio=self.dia(3))

    def url(self, accion=''):
        return f'/api/pedidos/{self.p.pk}' + (f'/{accion}' if accion else '')

    def test_lista_con_avisos_y_opciones(self):
        r = self.client.get('/api/pedidos', **self.admin_h).json()
        self.assertIn('Vencido', r['avisos'])
        fila = next(f for f in r['pedidos'] if f['id'] == self.p.pk)
        self.assertFalse(fila['tiene_chofer'])
        o = self.client.get('/api/admin/opciones', **self.admin_h).json()
        self.assertIn('AD-321-JK', o['vehiculos'])

    def test_detalle_trae_la_gestion_solo_al_administrador(self):
        d = self.client.get(self.url(), **self.admin_h).json()
        self.assertEqual(d['gestion']['cliente']['dni'], CLIENTE)
        self.assertTrue(d['gestion']['puede_asignar'])
        cliente_h = self.entrar(str(CLIENTE))
        self.assertIsNone(self.client.get(self.url(), **cliente_h).json()['gestion'])

    def test_asignar_y_confirmar(self):
        # sin chofer no se confirma
        self.assertEqual(self.client.post(self.url('confirmar'), **self.admin_h).status_code, 400)
        libres = self.client.get(self.url('personal'), **self.admin_h).json()
        chofer = Usuario.objects.get(DNI=CHOFER).pk
        self.assertIn(chofer, [c['id'] for c in libres['choferes']])
        r = self.client.put(self.url('personal'), {'chofer': chofer, 'ayudantes': []},
                            content_type='application/json', **self.admin_h)
        self.assertEqual(r.status_code, 200, r.content)
        self.assertTrue(PersonalPedido.objects.filter(idPedido=self.p, Funcion='Chofer').exists())
        self.assertEqual(self.client.post(self.url('confirmar'), **self.admin_h).status_code, 200)
        self.p.refresh_from_db()
        self.assertEqual(self.p.estado, Pedido.CONFIRMADO)
        # todavía no empezó: no se puede finalizar
        self.assertEqual(self.client.post(self.url('finalizar'), **self.admin_h).status_code, 400)

    def test_editar_servicios(self):
        r = self.client.put(self.url('servicios'), {'servicio': self.local.pk, 'adicionales': [self.embalaje.pk]},
                            content_type='application/json', **self.admin_h)
        self.assertEqual(r.status_code, 200, r.content)
        self.assertEqual(self.p.detalles.count(), 2)

    def test_reprogramar(self):
        o = self.client.get(self.url('reprogramar'), {'fecha': self.dia(5).isoformat(), 'hora': '10:00'},
                            **self.admin_h).json()
        self.assertIn('Clima', o['motivos'])
        r = self.client.post(self.url('reprogramar'), {
            'fecha_servicio': self.dia(5).isoformat(), 'hora_servicio': '10:00', 'vehiculo': 'AD-321-JK',
            'motivo': 'Clima'}, content_type='application/json', **self.admin_h)
        self.assertEqual(r.status_code, 200, r.content)
        d = self.client.get(self.url(), **self.admin_h).json()
        self.assertEqual(len(d['gestion']['reprogramaciones']), 1)
        self.assertTrue(d['gestion']['whatsapp'].startswith('https://wa.me/'))
        r = self.client.post(self.url('reprogramar'), {'fecha_servicio': self.dia(5).isoformat(),
                             'hora_servicio': '10:00', 'vehiculo': 'AD-321-JK', 'motivo': 'Inventado'},
                             content_type='application/json', **self.admin_h)
        self.assertIn('motivo', r.json()['errores'])

    def test_anular(self):
        r = self.client.post(self.url('anular'), {'motivo': 'no'}, content_type='application/json', **self.admin_h)
        self.assertIn('motivo', r.json()['errores'])
        r = self.client.post(self.url('anular'), {'motivo': 'El cliente no responde'},
                             content_type='application/json', **self.admin_h)
        self.assertEqual(r.status_code, 200)
        self.p.refresh_from_db()
        self.assertEqual(self.p.estado, Pedido.ANULADO)

    def test_el_cliente_no_puede_gestionar(self):
        h = self.entrar(str(CLIENTE))
        for accion in ('confirmar', 'finalizar', 'anular'):
            self.assertEqual(self.client.post(self.url(accion), **h).status_code, 403)
        self.assertEqual(self.client.get(self.url('personal'), **h).status_code, 403)
