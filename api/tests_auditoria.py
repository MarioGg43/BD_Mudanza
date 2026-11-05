"""La API del log de auditoría: frases legibles, filtros, enlaces a React y el PDF."""
from pedidos import reglas
from pedidos.test_reglas import ADMIN, CLIENTE
from usuarios.auditoria import con_usuario
from .tests import ApiBase


class ApiAuditoriaTest(ApiBase):
    def setUp(self):
        super().setUp()
        self.h = self.entrar(str(ADMIN))
        self.p = self.registrar()
        with con_usuario(self.admin):
            reglas.anular(self.p.pk, self.admin, 'El cliente no responde')

    def test_frase_cambios_y_enlace(self):
        r = self.client.get('/api/auditoria', {'tabla': 'PEDIDOS', 'accion': 'Anulación'}, **self.h).json()
        log = r['registros'][0]
        self.assertEqual(log['frase'], f'Carlos Sarmiento anuló el pedido N° {self.p.pk}')
        self.assertEqual(log['detalle'], 'El cliente no responde')
        self.assertEqual(log['link'], f'/pedidos/{self.p.pk}')
        self.assertIn(['Estado', 'Pendiente', 'Anulado'], log['cambios'])

    def test_filtro_por_registro_y_fechas_al_reves(self):
        r = self.client.get('/api/auditoria', {'registro': '999999'}, **self.h).json()
        self.assertEqual(r['total'], 0)
        r = self.client.get('/api/auditoria', {'desde': '2026-12-01', 'hasta': '2026-01-01'}, **self.h).json()
        self.assertIn('hasta', r['errores'])

    def test_opciones_y_pdf(self):
        o = self.client.get('/api/auditoria/opciones', **self.h).json()
        self.assertIn('Anulación', o['acciones'])
        r = self.client.get('/api/auditoria/pdf', **self.h)
        self.assertEqual((r.status_code, r['Content-Type']), (200, 'application/pdf'))

    def test_el_cliente_no_entra(self):
        self.assertEqual(self.client.get('/api/auditoria', **self.entrar(str(CLIENTE))).status_code, 403)
