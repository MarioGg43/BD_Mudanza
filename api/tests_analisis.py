"""La API del Parcial N° 2: tablero, reportes con PDF, notificaciones y umbrales."""
from pedidos.test_reglas import ADMIN, CLIENTE
from usuarios.models import Configuracion, Notificacion
from .tests import ApiBase


class ApiAnalisisTest(ApiBase):
    def setUp(self):
        super().setUp()
        self.h = self.entrar(str(ADMIN))

    def test_tablero(self):
        r = self.client.get('/api/tablero', {'periodo': '7'}, **self.h).json()
        self.assertEqual(len(r['graficos']['dias']['etiquetas']), 14)
        self.assertIn('finalizadas', r['graficos']['dias'])
        self.assertTrue(r['mes']['facturacion'].startswith('$'))
        self.assertEqual(self.client.get('/api/tablero', **self.entrar(str(CLIENTE))).status_code, 403)

    def test_reportes_grilla_y_pdf(self):
        lista = self.client.get('/api/reportes', **self.h).json()['reportes']
        self.assertEqual([x['clave'] for x in lista], ['personal', 'flota', 'cambios'])
        r = self.client.get('/api/reportes/flota', **self.h).json()
        self.assertEqual(r['columnas'][0]['titulo'], 'Patente')
        r = self.client.get('/api/reportes/flota', {'desde': '2026-12-01', 'hasta': '2026-01-01'}, **self.h)
        self.assertEqual(r.status_code, 400)
        self.assertIn('hasta', r.json()['errores'])
        pdf = self.client.get('/api/reportes/cambios/pdf', **self.h)
        self.assertEqual((pdf.status_code, pdf['Content-Type']), (200, 'application/pdf'))
        self.assertEqual(self.client.get('/api/reportes/nada', **self.h).status_code, 404)
        self.assertEqual(self.client.get('/api/reportes', **self.entrar(str(CLIENTE))).status_code, 403)

    def test_notificaciones_de_cada_uno(self):
        p = self.registrar()
        self.confirmar(p)  # regla 4: le avisa al cliente
        hc = self.entrar(str(CLIENTE))
        r = self.client.get('/api/notificaciones', **hc).json()
        self.assertEqual(r['sin_leer'], 1)
        n = r['notificaciones'][0]
        self.assertEqual((n['tipo'], n['enlace']), ('Mudanza confirmada', f'/pedidos/{p.pk}'))
        self.assertEqual(self.client.get('/api/notificaciones/contar', **self.h).json()['sin_leer'], 0)  # no es del admin
        self.assertEqual(self.client.post(f'/api/notificaciones/{n["id"]}/leer', **self.h).status_code, 404)
        self.client.post(f'/api/notificaciones/{n["id"]}/leer', **hc)
        self.assertTrue(Notificacion.objects.get(pk=n['id']).leida)
        self.assertEqual(self.client.get('/api/notificaciones/contar', **hc).json()['sin_leer'], 0)

    def test_umbrales(self):
        r = self.client.get('/api/configuracion', **self.h).json()
        self.assertIn('horas_sin_confirmar', [p['clave'] for p in r['parametros']])
        mal = self.client.put('/api/configuracion', {'horas_sin_confirmar': '0'}, content_type='application/json', **self.h)
        self.assertEqual(mal.status_code, 400)
        ok = self.client.put('/api/configuracion', {'horas_sin_confirmar': '24'}, content_type='application/json', **self.h)
        self.assertEqual(ok.status_code, 200)
        self.assertEqual(Configuracion.objects.get(clave='horas_sin_confirmar').valor, '24')
        self.assertIn('total', self.client.post('/api/alertas/evaluar', **self.h).json())
        self.assertEqual(self.client.get('/api/configuracion', **self.entrar(str(CLIENTE))).status_code, 403)
