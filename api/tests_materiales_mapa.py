"""La API de materiales, del mapa y del «Terminamos» con cantidades (tanda 2 de React)."""
from datetime import datetime, time
from unittest import mock

from django.core.cache import cache
from django.test import override_settings
from django.utils import timezone

from pedidos import mapa
from pedidos.test_mapa import ors_simulado
from pedidos.test_reglas import ADMIN, CLIENTE
from usuarios.models import Material, MovimientoMaterial as Mov, Pedido, Usuario
from .tests import ApiBase

CHOFER = 40987654


@override_settings(ORS_API_KEY='clave-de-prueba')
class ApiMaterialesMapaTest(ApiBase):
    def setUp(self):
        super().setUp()
        cache.clear()
        chofer = Usuario.objects.get(DNI=CHOFER)
        chofer.set_clave('Clave.123')
        chofer.DebeCambiarClave = False
        chofer.save()
        self.h = self.entrar(str(ADMIN))

    def test_el_catalogo_dice_que_incluye_cada_servicio(self):
        r = self.client.get('/api/catalogo', **self.entrar(str(CLIENTE))).json()
        flete = next(s for s in r['principales'] if s['nombre'] == 'Flete urbano')
        self.assertEqual(flete['incluye'], 'correas ×6, mantas acolchadas ×6')
        self.assertTrue(r['mapa_activo'])

    def test_el_pedido_guarda_el_punto_y_el_recorrido_lo_usa(self):
        hc = self.entrar(str(CLIENTE))
        datos = self.datos(origen='Origen 1', destino='Destino 2', puntos={'origen': {'lat': -24.79, 'lon': -65.41}})
        r = self.client.post('/api/pedidos', datos, content_type='application/json', **hc)
        self.assertEqual(r.status_code, 201, r.content)
        p = Pedido.objects.get(pk=r.json()['id'])
        self.assertEqual(float(p.lat_origen), -24.79)
        d = self.client.get(f'/api/pedidos/{p.pk}', **hc).json()
        self.assertEqual(d['puntos']['origen'], {'lat': -24.79, 'lon': -65.41})
        self.assertIsNone(d['materiales'])  # el cliente no ve el stock
        with mock.patch.object(mapa, '_pedir', side_effect=ors_simulado) as ors:
            rec = self.client.get(f'/api/pedidos/{p.pk}/recorrido', **hc).json()
        self.assertTrue(rec['ok'])
        self.assertEqual(ors.call_count, 2)  # solo el destino y la ruta: el origen ya tiene punto
        self.assertEqual(self.client.get(f'/api/pedidos/{p.pk}/recorrido', **self.entrar(str(ADMIN))).status_code, 200)

    def test_buscar_direcciones(self):
        hc = self.entrar(str(CLIENTE))
        with mock.patch.object(mapa, '_pedir', side_effect=ors_simulado):
            r = self.client.get('/api/mapa/ubicar', {'direccion': 'Origen 1'}, **hc).json()
        self.assertEqual((r['ok'], r['lat'], r['lon']), (True, -24.78, -65.41))
        self.assertEqual(self.client.get('/api/mapa/direccion', {'lat': '40', 'lon': '-3'}, **hc).status_code, 400)

    def test_materiales_alta_ingreso_ajuste_y_baja(self):
        r = self.client.get('/api/materiales', **self.h).json()
        self.assertIn('Mantas acolchadas', [m['nombre'] for m in r['materiales']])
        nuevo = self.client.post('/api/materiales', {'nom_material': 'esquineros', 'unidad_material': 'unidades',
                                                     'stock_min_material': 10, 'stock_inicial': 40}, content_type='application/json', **self.h)
        self.assertEqual(nuevo.status_code, 201, nuevo.content)
        m = nuevo.json()
        self.assertEqual((m['nombre'], m['stock']), ('Esquineros', 40))
        mov = lambda **d: self.client.post(f'/api/materiales/{m["id"]}/movimiento', d, content_type='application/json', **self.h)
        self.assertEqual(mov(tipo='Ingreso', cantidad=15, observacion='Compra').json()['stock'], 55)
        self.assertEqual(mov(tipo='Ajuste', cantidad=-2, observacion='').status_code, 400)  # sin motivo
        self.assertEqual(mov(tipo='Ajuste', cantidad=-2, observacion='Conteo del viernes').json()['stock'], 53)
        ficha = self.client.get(f'/api/materiales/{m["id"]}', **self.h).json()
        self.assertEqual([x['tipo'] for x in ficha['movimientos']], ['Ajuste', 'Ingreso', 'Ingreso'])
        editado = self.client.put(f'/api/materiales/{m["id"]}', {'stock_min_material': 60}, content_type='application/json', **self.h).json()
        self.assertTrue(editado['bajo_minimo'])
        self.assertFalse(self.client.post(f'/api/materiales/{m["id"]}/baja', **self.h).json()['activo'])
        self.assertEqual(self.client.get('/api/materiales', **self.entrar(str(CLIENTE))).status_code, 403)

    def test_el_chofer_ve_los_materiales_y_termina_contandolos(self):
        p = self.registrar(id_servicio=self.flete.id_servicio)  # mañana a las 9: correas ×6 y mantas ×6
        self.confirmar(p)
        hch = self.entrar(str(CHOFER))
        m = next(x for x in self.client.get('/api/portal', **hch).json()['mudanzas'] if x['id'] == p.pk)
        self.assertEqual({x['nombre'] for x in m['materiales']}, {'Correas', 'Mantas acolchadas'})
        momento = timezone.make_aware(datetime.combine(self.dia(), time(9, 0)))
        with mock.patch('django.utils.timezone.now', return_value=momento):
            self.assertEqual(self.client.post(f'/api/portal/{p.pk}/empezar', **hch).status_code, 200)
            salieron = self.client.get(f'/api/portal/{p.pk}/terminar', **hch).json()['materiales']
            correas = next(x for x in salieron if x['nombre'] == 'Correas')
            self.assertEqual((correas['salio'], correas['reutilizable']), (6, True))
            mal = self.client.post(f'/api/portal/{p.pk}/terminar', {'usados': {correas['id']: 7}}, content_type='application/json', **hch)
            self.assertEqual(mal.status_code, 400)
            ok = self.client.post(f'/api/portal/{p.pk}/terminar', {'usados': {correas['id']: 4}}, content_type='application/json', **hch)
            self.assertEqual(ok.status_code, 200)
        self.assertEqual(Mov.objects.get(idPedido=p, tipo_mov=Mov.PERDIDA, idMaterial__nom_material='Correas').cant_mov, 2)
        self.assertEqual(Pedido.objects.get(pk=p.pk).estado, Pedido.FINALIZADO)
        d = self.client.get(f'/api/pedidos/{p.pk}', **self.h).json()
        self.assertIn('Pérdida', [x['tipo'] for x in d['materiales']['movimientos']])
