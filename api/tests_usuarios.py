"""La API de usuarios y roles, con los mismos candados que el panel de Django."""
from pedidos.test_reglas import ADMIN, CLIENTE
from usuarios.models import Rol, Usuario
from .tests import ApiBase

NUEVO = {'dni': 30555666, 'apellido': 'Ríos', 'nombre': 'Pablo', 'correo': 'pablo.rios@ejemplo.com',
         'clave': 'Clave.123', 'id_rol': None}


class ApiUsuariosTest(ApiBase):
    def setUp(self):
        super().setUp()
        self.h = self.entrar(str(ADMIN))
        self.chofer_rol = Rol.objects.get(nom_rol='Chofer')

    def mandar(self, metodo, url, datos=None):
        return getattr(self.client, metodo)(url, datos or {}, content_type='application/json', **self.h)

    def test_lista_con_roles_y_permisos(self):
        r = self.client.get('/api/usuarios', **self.h).json()
        yo = next(u for u in r['usuarios'] if u['dni'] == ADMIN)
        self.assertTrue(yo['soy_yo'])
        self.assertTrue(r['puede']['crear'])

    def test_alta_baja_reactivar_correo_rol_y_clave(self):
        r = self.mandar('post', '/api/usuarios', {**NUEVO, 'id_rol': self.chofer_rol.pk})
        self.assertEqual(r.status_code, 201, r.content)
        self.assertTrue(r.json()['debe_cambiar_clave'])
        dni = NUEVO['dni']
        self.assertEqual(self.mandar('post', '/api/usuarios', {**NUEVO, 'id_rol': self.chofer_rol.pk}).status_code, 400)
        self.assertEqual(self.mandar('put', f'/api/usuarios/{dni}/correo', {'correo': 'no-es-correo'}).status_code, 400)
        r = self.mandar('put', f'/api/usuarios/{dni}/correo', {'correo': 'Pablo.Nuevo@ejemplo.com'})
        self.assertEqual(r.json()['correo'], 'pablo.nuevo@ejemplo.com')
        ayudante = Rol.objects.get(nom_rol='Ayudante de Carga').pk
        r = self.mandar('put', f'/api/usuarios/{dni}/rol', {'id_rol': ayudante})
        self.assertEqual((r.json()['rol'], r.json()['rol_anterior']), ('Ayudante de Carga', 'Chofer'))
        cliente = Rol.objects.get(nom_rol='Cliente').pk
        self.assertEqual(self.mandar('put', f'/api/usuarios/{dni}/rol', {'id_rol': cliente}).status_code, 400)
        r = self.mandar('post', f'/api/usuarios/{dni}/clave')
        self.assertTrue(r.json()['clave_provisoria'])
        self.assertEqual(self.mandar('post', f'/api/usuarios/{dni}/baja').status_code, 200)
        self.assertFalse(Usuario.objects.get(DNI=dni).Activo)
        self.assertEqual(self.mandar('post', f'/api/usuarios/{dni}/reactivar').status_code, 200)
        self.assertTrue(Usuario.objects.get(DNI=dni).Activo)

    def test_candados(self):
        self.assertEqual(self.mandar('post', f'/api/usuarios/{ADMIN}/baja').status_code, 400)  # a sí mismo
        self.assertEqual(self.mandar('post', f'/api/usuarios/{CLIENTE}/clave').status_code, 400)  # de un cliente
        self.assertEqual(self.client.get('/api/usuarios', **self.entrar(str(CLIENTE))).status_code, 403)

    def test_roles(self):
        r = self.client.get('/api/roles', **self.h).json()
        self.assertTrue(any(c['codigo'] == 'ROL_GESTIONAR' for c in r['catalogo']))
        r = self.mandar('post', '/api/roles', {'nombre': 'Secretaría', 'descripcion': 'Atiende pedidos',
                                               'permisos': ['PED_CONSULTAR', 'PED_GESTIONAR']})
        self.assertEqual(r.status_code, 201, r.content)
        nuevo = r.json()['id']
        r = self.mandar('put', f'/api/roles/{nuevo}', {'nombre': 'Secretaría', 'permisos': ['INVENTADO']})
        self.assertIn('permisos', r.json()['errores'])
        cliente = Rol.objects.get(nom_rol='Cliente').pk
        r = self.mandar('put', f'/api/roles/{cliente}', {'nombre': 'Clientes', 'permisos': ['PED_CONSULTAR']})
        self.assertIn('nombre', r.json()['errores'])  # rol del sistema: no se renombra
        self.assertEqual(self.mandar('delete', f'/api/roles/{cliente}').status_code, 400)
        self.assertEqual(self.mandar('delete', f'/api/roles/{nuevo}').status_code, 200)
