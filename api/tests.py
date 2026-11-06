"""La API que consume React: login por token, permisos y el ciclo del pedido del cliente."""
from datetime import timedelta
from unittest import mock

from django.core import signing

from pedidos.test_reglas import ADMIN, BaseReglas, obj
from usuarios.models import LogAuditoria, Pedido, Usuario


class ApiBase(BaseReglas):
    """Claves conocidas para el cliente y el administrador, y el login por la API."""
    def setUp(self):
        for dni in (self.cliente.DNI, ADMIN):
            u = Usuario.objects.get(DNI=dni)
            u.set_clave('Clave.123')
            u.DebeCambiarClave = False
            u.save()

    def entrar(self, usuario):
        r = self.client.post('/api/auth/login', {'usuario': usuario, 'clave': 'Clave.123'},
                             content_type='application/json')
        self.assertEqual(r.status_code, 200, r.content)
        return {'HTTP_AUTHORIZATION': 'Bearer ' + r.json()['token']}

    def datos(self, **cambios):
        d = {'fecha_servicio': self.dia(3).isoformat(), 'hora_servicio': '09:00',
             'origen': 'Av. Belgrano 100, Salta', 'destino': 'Mitre 50, Cerrillos',
             'servicio': self.local.id_servicio, 'adicionales': [self.embalaje.id_servicio], 'vehiculo': 'AD-321-JK',
             'inventario': [{'objeto': obj('Heladera').pk, 'cantidad': 1, 'fragil': True},
                            {'objeto': obj('Otro').pk, 'cantidad': 1, 'observacion': 'Piano'}]}
        d.update(cambios)
        return d


class ApiTest(ApiBase):
    def test_login_devuelve_token_y_permisos(self):
        r = self.client.post('/api/auth/login', {'usuario': str(self.cliente.DNI), 'clave': 'Clave.123'},
                             content_type='application/json')
        self.assertEqual(r.status_code, 200)
        self.assertIn('PED_REGISTRAR', r.json()['usuario']['permisos'])

    def test_login_con_clave_mala(self):
        r = self.client.post('/api/auth/login', {'usuario': str(self.cliente.DNI), 'clave': 'otra'},
                             content_type='application/json')
        self.assertEqual(r.status_code, 401)

    def test_clave_provisoria(self):
        u = Usuario.objects.get(DNI=self.cliente.DNI)
        u.DebeCambiarClave = True
        u.save()
        r = self.client.post('/api/auth/login', {'usuario': str(u.DNI), 'clave': 'Clave.123'}, content_type='application/json')
        self.assertEqual(r.status_code, 403)
        self.assertIn('cambiar_clave', r.json()['errores'])
        cambio = {'usuario': str(u.DNI), 'clave': 'Clave.123', 'nueva': 'Nueva.456', 'confirmar': 'Otra.789'}
        r = self.client.post('/api/auth/cambiar-clave', cambio, content_type='application/json')
        self.assertEqual(r.json()['error'], 'Las contraseñas no coinciden.')
        r = self.client.post('/api/auth/cambiar-clave', {**cambio, 'nueva': 'Clave.123', 'confirmar': 'Clave.123'},
                             content_type='application/json')
        self.assertIn('distinta', r.json()['error'])
        r = self.client.post('/api/auth/cambiar-clave', {**cambio, 'clave': 'mala'}, content_type='application/json')
        self.assertEqual(r.status_code, 401)
        r = self.client.post('/api/auth/cambiar-clave', {**cambio, 'confirmar': 'Nueva.456'}, content_type='application/json')
        self.assertEqual(r.status_code, 200, r.content)
        self.assertTrue(r.json()['token'])
        u.refresh_from_db()
        self.assertFalse(u.DebeCambiarClave)
        self.assertTrue(u.verificar_clave('Nueva.456'))

    def test_olvide_mi_clave(self):
        datos = {'dni': str(self.cliente.DNI), 'correo': self.cliente.Correo.upper(), 'nueva': 'Nueva.456', 'confirmar': 'Nueva.456'}
        r = self.client.post('/api/auth/recuperar-clave', {**datos, 'correo': 'otro@ejemplo.com'}, content_type='application/json')
        self.assertEqual((r.status_code, r.json()['error']), (400, 'El DNI y el correo no coinciden con ninguna cuenta de cliente.'))
        r = self.client.post('/api/auth/recuperar-clave', {**datos, 'confirmar': 'Otra.789'}, content_type='application/json')
        self.assertEqual(r.json()['error'], 'Las contraseñas no coinciden.')
        r = self.client.post('/api/auth/recuperar-clave', datos, content_type='application/json')
        self.assertEqual(r.status_code, 200, r.content)
        self.assertTrue(r.json()['token'])
        self.assertTrue(Usuario.objects.get(DNI=self.cliente.DNI).verificar_clave('Nueva.456'))
        # el personal no recupera la clave por acá (se la restablece el administrador)
        admin = Usuario.objects.get(DNI=ADMIN)
        r = self.client.post('/api/auth/recuperar-clave', {**datos, 'dni': str(ADMIN), 'correo': admin.Correo},
                             content_type='application/json')
        self.assertEqual(r.status_code, 400)
        self.assertTrue(Usuario.objects.get(DNI=ADMIN).verificar_clave('Clave.123'))

    def test_sin_token_o_con_token_falso_da_401(self):
        self.assertEqual(self.client.get('/api/pedidos').status_code, 401)
        r = self.client.get('/api/pedidos', HTTP_AUTHORIZATION='Bearer 29876543:falso:token')
        self.assertEqual(r.status_code, 401)

    def test_token_vencido_da_401(self):
        h = self.entrar(str(self.cliente.DNI))
        with mock.patch('time.time', return_value=signing.time.time() + 13 * 3600):
            self.assertEqual(self.client.get('/api/auth/yo', **h).status_code, 401)

    def test_sin_permiso_da_403(self):
        h = self.entrar(str(ADMIN))  # el administrador no tiene PED_REGISTRAR
        self.assertEqual(self.client.get('/api/catalogo', **h).status_code, 403)

    def test_info_publica_sin_token(self):
        r = self.client.get('/api/publico')
        self.assertEqual(r.status_code, 200)
        datos = r.json()
        self.assertTrue(datos['principales'])
        self.assertTrue(all(c['recargo'] in (0, 25, 50) for c in datos['camiones']))
        self.assertEqual(self.client.post('/api/publico').status_code, 405)

    def test_catalogo_trae_otro_al_final(self):
        r = self.client.get('/api/catalogo', **self.entrar(str(self.cliente.DNI))).json()
        self.assertTrue(r['objetos'][-1]['otro'])
        self.assertTrue(r['principales'])

    def test_pedir_ver_modificar_y_cancelar(self):
        h = self.entrar(str(self.cliente.DNI))
        libres = self.client.get('/api/vehiculos-libres', {'fecha': self.dia(3).isoformat(), 'hora': '09:00',
                                                           'servicio': self.local.id_servicio}, **h).json()
        self.assertIn('AD-321-JK', [v['patente'] for v in libres['vehiculos']])

        r = self.client.post('/api/pedidos', self.datos(), content_type='application/json', **h)
        self.assertEqual(r.status_code, 201, r.content)
        id_pedido = r.json()['id']
        lista = self.client.get('/api/pedidos', **h).json()['pedidos']
        self.assertIn(id_pedido, [p['id'] for p in lista])
        d = self.client.get(f'/api/pedidos/{id_pedido}', **h).json()
        self.assertEqual((d['estado'], d['puede_cambiar']), ('Pendiente', True))
        self.assertEqual(sorted(i['nombre'] for i in d['inventario']), ['Heladera', 'Otro'])

        r = self.client.put(f'/api/pedidos/{id_pedido}', self.datos(hora_servicio='14:00', adicionales=[]),
                            content_type='application/json', **h)
        self.assertEqual(r.status_code, 200, r.content)
        self.assertEqual(Pedido.objects.get(pk=id_pedido).hora_servicio.hour, 14)

        r = self.client.post(f'/api/pedidos/{id_pedido}/cancelar', {'motivo': 'x'},
                             content_type='application/json', **h)
        self.assertEqual(r.status_code, 400)
        r = self.client.post(f'/api/pedidos/{id_pedido}/cancelar', {'motivo': 'Ya no me mudo'},
                             content_type='application/json', **h)
        self.assertEqual(r.status_code, 200)
        self.assertEqual(Pedido.objects.get(pk=id_pedido).estado, Pedido.ANULADO)
        # sin sesión de Django igual queda quién lo anuló en la auditoría
        log = LogAuditoria.objects.filter(tabla='PEDIDOS', id_registro=str(id_pedido)).latest('id_log')
        self.assertEqual(log.usuario_id, self.cliente.pk)

    def test_errores_por_campo(self):
        h = self.entrar(str(self.cliente.DNI))
        r = self.client.post('/api/pedidos', self.datos(destino='Av. Belgrano 100, Salta', inventario=[
            {'objeto': obj('Otro').pk, 'cantidad': 1, 'observacion': 'heladeras'}]),
            content_type='application/json', **h)
        self.assertEqual(r.status_code, 400)
        self.assertEqual(set(r.json()['errores']), {'destino', 'inventario'})

    def test_no_ve_pedidos_ajenos(self):
        p = self.registrar()
        otro = Usuario.objects.create(DNI=31222333, Nombre='Ana', Apellido='Paz', Correo='ana.paz@ejemplo.com',
                                      NombreUsuario='paza', Clave='x', idRol=self.cliente.idRol, DebeCambiarClave=False)
        otro.set_clave('Clave.123')
        otro.save()
        h = self.entrar('31222333')
        self.assertEqual(self.client.get(f'/api/pedidos/{p.pk}', **h).status_code, 404)
        self.assertEqual(self.client.get('/api/pedidos', **h).json()['pedidos'], [])

    def test_no_cambia_dentro_de_las_24_horas(self):
        p = self.registrar(fecha_servicio=self.dia(3))
        h = self.entrar(str(self.cliente.DNI))
        with mock.patch('django.utils.timezone.now', return_value=p.inicio - timedelta(hours=23)):
            r = self.client.post(f'/api/pedidos/{p.pk}/cancelar', {'motivo': 'Ya no me mudo'},
                                 content_type='application/json', **h)
        self.assertEqual(r.status_code, 400)

    def test_comprobante_pdf(self):
        p = self.registrar()
        r = self.client.get(f'/api/pedidos/{p.pk}/comprobante', **self.entrar(str(self.cliente.DNI)))
        self.assertEqual((r.status_code, r['Content-Type']), (200, 'application/pdf'))

    def test_registro_de_cliente(self):
        r = self.client.post('/api/auth/registro', {
            'dni': 30111222, 'apellido': 'Gómez', 'nombre': 'Laura', 'correo': 'laura@ejemplo.com',
            'telefono': '3874000000', 'clave': 'Clave.123', 'clave2': 'Clave.123'}, content_type='application/json')
        self.assertEqual(r.status_code, 201, r.content)
        self.assertEqual(r.json()['usuario']['rol'], 'Cliente')
        r = self.client.post('/api/auth/registro', {'dni': 30111222}, content_type='application/json')
        self.assertIn('dni', r.json()['errores'])
