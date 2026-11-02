"""La API que consume React: login por token, permisos y el ciclo del pedido del cliente."""
from datetime import timedelta
from unittest import mock

from django.core import signing

from pedidos.test_reglas import ADMIN, BaseReglas, obj
from usuarios.models import LogAuditoria, Pedido, Usuario


class ApiTest(BaseReglas):
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

    def test_login_devuelve_token_y_permisos(self):
        r = self.client.post('/api/auth/login', {'usuario': str(self.cliente.DNI), 'clave': 'Clave.123'},
                             content_type='application/json')
        self.assertEqual(r.status_code, 200)
        self.assertIn('PED_REGISTRAR', r.json()['usuario']['permisos'])

    def test_login_con_clave_mala(self):
        r = self.client.post('/api/auth/login', {'usuario': str(self.cliente.DNI), 'clave': 'otra'},
                             content_type='application/json')
        self.assertEqual(r.status_code, 401)

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
