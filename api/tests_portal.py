"""La API del portal del personal: sus mudanzas, «Empezamos», relevamiento y «Terminamos»."""
from datetime import timedelta
from unittest import mock

from pedidos.test_reglas import ADMIN, CLIENTE, obj
from usuarios.models import Pedido, Usuario
from .tests import ApiBase

CHOFER = 40987654


class ApiPortalTest(ApiBase):
    def setUp(self):
        super().setUp()
        chofer = Usuario.objects.get(DNI=CHOFER)
        chofer.set_clave('Clave.123')
        chofer.DebeCambiarClave = False
        chofer.save()
        self.h = self.entrar(str(CHOFER))
        self.p = self.registrar(fecha_servicio=self.dia(2))
        self.confirmar(self.p)  # le asigna a Luciana como chofer

    def mandar(self, url, datos=None):
        return self.client.post(url, datos or {}, content_type='application/json', **self.h)

    def test_ve_sus_mudanzas_sin_precios(self):
        r = self.client.get('/api/portal', **self.h).json()
        m = next(x for x in r['mudanzas'] if x['id'] == self.p.pk)
        self.assertTrue(m['soy_chofer'])
        self.assertFalse(m['puede_empezar'])  # todavía faltan dos días
        self.assertNotIn('total', m)

    def test_empezar_relevamiento_y_terminar(self):
        momento = self.p.inicio - timedelta(hours=1)
        with mock.patch('django.utils.timezone.now', return_value=momento):
            self.assertTrue(self.client.get('/api/portal', **self.h).json()['mudanzas'][0]['puede_empezar'])
            self.assertEqual(self.mandar(f'/api/portal/{self.p.pk}/empezar').status_code, 200)
            datos = self.client.get(f'/api/portal/{self.p.pk}/relevamiento', **self.h).json()
            heladera = next(i for i in datos['items'] if i['nombre'] == 'Heladera')
            r = self.mandar(f'/api/portal/{self.p.pk}/relevamiento', {
                'reales': {heladera['id']: 2},
                'nuevos': [{'objeto': obj('Otro').pk, 'cantidad': 1, 'observacion': 'Piano'}],
                'adicionales': [self.embalaje.pk], 'recargo': 20000, 'motivo': 'Había un piano'})
            self.assertEqual(r.status_code, 200, r.content)
            self.p.refresh_from_db()
            self.assertEqual(self.p.recargo, 20000)
            item = self.p.inventario.get(idObjeto__nom_objeto='Heladera')
            self.assertEqual((item.Cantidad, item.cantidad_declarada), (2, 1))
            self.assertEqual(self.mandar(f'/api/portal/{self.p.pk}/terminar').status_code, 200)
        self.p.refresh_from_db()
        self.assertEqual(self.p.estado, Pedido.FINALIZADO)

    def test_relevamiento_con_errores(self):
        with mock.patch('django.utils.timezone.now', return_value=self.p.inicio):
            self.mandar(f'/api/portal/{self.p.pk}/empezar')
            r = self.mandar(f'/api/portal/{self.p.pk}/relevamiento', {
                'nuevos': [{'objeto': obj('Otro').pk, 'cantidad': 1, 'observacion': 'heladeras'}],
                'recargo': 5000, 'motivo': ''})
        self.assertEqual(set(r.json()['errores']), {'inventario', 'motivo'})

    def test_no_empieza_antes_ni_si_no_es_el_chofer(self):
        r = self.mandar(f'/api/portal/{self.p.pk}/empezar')
        self.assertEqual(r.status_code, 400)  # todavía es temprano
        self.assertEqual(self.client.get(f'/api/portal/{self.p.pk}/relevamiento', **self.h).status_code, 403)
        self.assertEqual(self.client.get('/api/portal', **self.entrar(str(CLIENTE))).status_code, 403)
        # el administrador ve el portal (tiene el permiso) pero no es el chofer: no marca
        self.assertEqual(self.client.post(f'/api/portal/{self.p.pk}/empezar', **self.entrar(str(ADMIN))).status_code, 400)
