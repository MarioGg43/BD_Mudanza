"""La API de «Mi cuenta»: ver los datos, cambiarlos (solo el cliente) y cambiar la clave."""
from pedidos.test_reglas import ADMIN, CLIENTE
from usuarios.models import Usuario
from .tests import ApiBase


class ApiMiCuentaTest(ApiBase):
    def test_el_cliente_cambia_su_correo_y_su_clave(self):
        h = self.entrar(str(CLIENTE))
        self.assertTrue(self.client.get('/api/mi-cuenta', **h).json()['edita_datos'])
        r = self.client.put('/api/mi-cuenta', {'correo': 'nuevo@ejemplo.com', 'telefono': '3875551234'},
                            content_type='application/json', **h)
        self.assertEqual(r.json()['correo'], 'nuevo@ejemplo.com')
        mal = self.client.post('/api/mi-cuenta/clave', {'actual': 'otra', 'nueva': 'Nueva.1234', 'confirmar': 'Nueva.1234'},
                               content_type='application/json', **h)
        self.assertEqual(mal.json()['errores'], {'actual': 'La clave actual no coincide.'})
        ok = self.client.post('/api/mi-cuenta/clave', {'actual': 'Clave.123', 'nueva': 'Nueva.1234', 'confirmar': 'Nueva.1234'},
                              content_type='application/json', **h)
        self.assertEqual(ok.status_code, 200, ok.content)
        self.assertTrue(Usuario.objects.get(DNI=CLIENTE).verificar_clave('Nueva.1234'))

    def test_el_personal_no_cambia_su_correo(self):
        h = self.entrar(str(ADMIN))
        self.assertFalse(self.client.get('/api/mi-cuenta', **h).json()['edita_datos'])
        r = self.client.put('/api/mi-cuenta', {'correo': 'x@ejemplo.com'}, content_type='application/json', **h)
        self.assertEqual(r.status_code, 403)
