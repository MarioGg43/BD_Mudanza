"""Pruebas del mapa del recorrido. OpenRouteService se simula: no hace falta internet ni clave."""
from unittest import mock

from django.core.cache import cache
from django.test import override_settings

from pedidos import mapa
from pedidos.test_vistas import ADMIN, CHOFER, BaseVistas

AYUDANTE = 38999888

GEOCODIFICADO = {
    'Origen 1': {'features': [{'geometry': {'coordinates': [-65.41, -24.78]}, 'properties': {'label': 'Origen 1, Salta'}}]},
    'Destino 2': {'features': [{'geometry': {'coordinates': [-65.39, -24.80]}, 'properties': {'label': 'Destino 2, Salta'}}]},
}
RUTA = {'features': [{'geometry': {'type': 'LineString', 'coordinates': [[-65.41, -24.78], [-65.39, -24.80]]},
                      'properties': {'summary': {'distance': 12345.6, 'duration': 1530}}}]}


def ors_simulado(url, cuerpo=None):
    """Responde como OpenRouteService: geocodificación por el texto buscado, o la ruta."""
    if '/geocode/' in url:
        for direccion, respuesta in GEOCODIFICADO.items():
            if direccion.replace(' ', '+') in url:
                return respuesta
        return {'features': []}
    return RUTA


@override_settings(ORS_API_KEY='clave-de-prueba')
class RecorridoTest(BaseVistas):
    def setUp(self):
        cache.clear()
        self.pedido = self.con_chofer(self.pedido_de(self.cliente))
        self.url = f'/pedidos/{self.pedido.pk}/recorrido/'

    def test_el_cliente_ve_el_recorrido_con_km_y_tiempo(self):
        self.entrar(self.cliente.DNI)
        with mock.patch.object(mapa, '_pedir', side_effect=ors_simulado):
            datos = self.client.get(self.url).json()
        self.assertTrue(datos['ok'])
        self.assertEqual(datos['km'], 12.3)
        self.assertEqual(datos['minutos'], 26)
        self.assertEqual(datos['origen']['etiqueta'], 'Origen 1, Salta')
        self.assertEqual(datos['ruta']['type'], 'LineString')  # GeoJSON, lo dibuja Leaflet
        self.assertIn('google.com/maps/dir/', datos['como_llegar'])

    def test_el_mismo_recorrido_no_se_vuelve_a_consultar(self):
        self.entrar(self.cliente.DNI)
        with mock.patch.object(mapa, '_pedir', side_effect=ors_simulado) as ors:
            self.client.get(self.url)
            self.client.get(self.url)
        self.assertEqual(ors.call_count, 3)  # 2 direcciones + 1 ruta, una sola vez

    def test_quien_puede_verlo(self):
        with mock.patch.object(mapa, '_pedir', side_effect=ors_simulado):
            for dni, estado in ((self.cliente.DNI, 200), (ADMIN, 200), (CHOFER, 200),
                                (self.otro.DNI, 404), (AYUDANTE, 404)):  # otro cliente / no asignado
                self.entrar(dni)
                self.assertEqual(self.client.get(self.url).status_code, estado, msg=str(dni))
        self.client.logout()
        self.assertEqual(self.client.get(self.url).status_code, 401)

    def test_direccion_que_no_existe(self):
        self.pedido.origen = 'Calle Inventada 999'
        self.pedido.save()
        self.entrar(self.cliente.DNI)
        with mock.patch.object(mapa, '_pedir', side_effect=ors_simulado):
            datos = self.client.get(self.url).json()
        self.assertFalse(datos['ok'])
        self.assertIn('No encontramos «Calle Inventada 999»', datos['error'])
        self.assertIn('google.com/maps/dir/', datos['como_llegar'])  # el botón sigue andando

    def test_direcciones_vagas_en_el_mismo_punto(self):
        # «zona norte» y «zona este» las ubica en el mismo lugar: no se muestra un recorrido de 0 km
        self.pedido.destino = 'Origen 1'
        self.pedido.save()
        self.entrar(self.cliente.DNI)
        with mock.patch.object(mapa, '_pedir', side_effect=ors_simulado) as ors:
            datos = self.client.get(self.url).json()
        self.assertFalse(datos['ok'])
        self.assertIn('caen en el mismo punto', datos['error'])
        self.assertEqual(ors.call_count, 2)  # ni se pide la ruta

    def test_servicio_caido(self):
        self.entrar(self.cliente.DNI)
        with mock.patch.object(mapa, '_pedir', side_effect=mapa.ErrorMapa('No hay conexión con el servicio de mapas.')):
            datos = self.client.get(self.url).json()
        self.assertFalse(datos['ok'])
        self.assertEqual(datos['error'], 'No hay conexión con el servicio de mapas.')

    @override_settings(ORS_API_KEY='')
    def test_sin_clave_avisa_y_no_consulta(self):
        self.entrar(self.cliente.DNI)
        with mock.patch.object(mapa, '_pedir') as ors:
            datos = self.client.get(self.url).json()
        ors.assert_not_called()
        self.assertFalse(datos['ok'])
        self.assertIn('falta la clave', datos['error'])

    def test_el_detalle_trae_el_mapa_y_el_portal_el_boton(self):
        self.entrar(self.cliente.DNI)
        r = self.client.get(f'/pedidos/{self.pedido.pk}/')
        self.assertContains(r, f'data-mapa-recorrido="{self.url}"')
        self.assertContains(r, 'Cómo llegar')
        self.entrar(CHOFER)
        self.assertContains(self.client.get('/portal/'),
                            'https://www.google.com/maps/dir/?api=1&amp;origin=Origen+1&amp;destination=Destino+2')


class ComoLlegarTest(BaseVistas):
    def test_el_enlace_lleva_las_dos_direcciones(self):
        self.assertEqual(mapa.como_llegar('Zuviría 150, Salta', 'Av. Belgrano 1250'),
                         'https://www.google.com/maps/dir/?api=1&origin=Zuvir%C3%ADa+150%2C+Salta'
                         '&destination=Av.+Belgrano+1250&travelmode=driving')
