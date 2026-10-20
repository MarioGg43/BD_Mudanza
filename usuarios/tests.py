"""Pruebas del Hito 2 sobre el modelo del DER.

Usan los datos de init_data (los mismos que levanta Docker):
  sarmientoc / Admin123!    Administrador  DNI 35123456
  fernandezl / Usuario123!  Chofer         DNI 40987654
  romerol    / Temporal123! Ayudante       DNI 38999888 (debe cambiar la clave)
"""
import io
from datetime import time

from django.core.management import call_command
from django.db import connection
from django.test import TestCase

from .models import (
    Rol, Permiso, PermisoRol, Usuario, Vehiculo, Pedido,
    DetallePedido, InventarioDetalle, Cobranza, DetalleCobranza, Servicio, Objeto,
)
from .utils import generate_username, validate_strong_password, hash_password

ADMIN, CHOFER, AYUDANTE = 35123456, 40987654, 38999888


class BaseHito2(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command('init_data', stdout=io.StringIO())

    def entrar(self, dni):
        """Abre sesión como lo hace el login, sin pasar por la pantalla."""
        s = self.client.session
        s['usuario_dni'] = dni
        s['usuario_rol'] = Usuario.objects.get(DNI=dni).idRol.nom_rol
        s.save()

    def alta(self, **datos):
        base = {'dni': '30111222', 'apellido': 'Pérez', 'nombre': 'Ana Laura',
                'correo': 'APEREZ@mail.com', 'clave': 'Cliente123!',
                'idRol': Rol.objects.get(nom_rol='Chofer').id_rol}
        base.update(datos)
        return self.client.post('/usuarios/alta/', base)


class EstructuraDERTest(BaseHito2):
    def test_las_13_tablas_del_der_existen(self):
        tablas = {t.upper() for t in connection.introspection.table_names()}
        der = {'PERMISOS', 'PERMISOS_ROLES', 'ROLES', 'USUARIOS', 'SUELDOS', 'VEHICULOS',
               'SERVICIOS', 'RECURSOS_ASIGNADOS', 'PEDIDOS', 'DETALLE_PEDIDOS',
               'INVENTARIO_DETALLES', 'DETALLE_COBRANZAS', 'COBRANZAS'}
        self.assertEqual(der - tablas, set())

    def test_datos_iniciales(self):
        self.assertEqual(Rol.objects.count(), 4)
        self.assertEqual(Usuario.objects.count(), 4)
        self.assertEqual(Vehiculo.objects.count(), 4)
        self.assertEqual(Permiso.objects.count(), 16)
        # el administrador tiene todos los permisos menos registrar pedidos
        self.assertEqual(PermisoRol.objects.filter(idRol__nom_rol='Administrador').count(), 15)
        self.assertEqual(PermisoRol.objects.filter(idRol__nom_rol='Chofer').count(), 1)

    def test_pedido_de_ejemplo_completo(self):
        pedido = Pedido.objects.get()
        self.assertEqual(pedido.patente_vehiculo.patente, 'AE-123-CD')
        self.assertTrue(DetallePedido.objects.filter(idPedido=pedido).exists())
        self.assertTrue(InventarioDetalle.objects.filter(idPedido=pedido).exists())
        self.assertTrue(DetalleCobranza.objects.filter(idPedido=pedido).exists())
        self.assertEqual(Cobranza.objects.count(), 1)

    def test_init_data_se_puede_correr_dos_veces(self):
        call_command('init_data', stdout=io.StringIO())
        self.assertEqual(Usuario.objects.count(), 4)
        self.assertEqual(Pedido.objects.count(), 1)


class UtilidadesTest(TestCase):
    def test_usuario_automatico(self):
        self.assertEqual(generate_username('Sarmiento', 'Carlos'), 'sarmientoc')
        self.assertEqual(generate_username('Gómez Pérez', 'María José'), 'gomezm')
        self.assertEqual(generate_username("D'Angelo", 'Ñato'), 'dangelon')

    def test_clave_fuerte(self):
        self.assertTrue(validate_strong_password('Admin123!')[0])
        for mala in ['Ab1!', 'admin123!', 'ADMIN123!', 'Adminxxx!', 'Admin1234']:
            self.assertFalse(validate_strong_password(mala)[0], mala)

    def test_clave_se_guarda_hasheada(self):
        h = hash_password('Admin123!')
        self.assertEqual(len(h), 64)
        self.assertNotIn('Admin123!', h)


class LoginTest(BaseHito2):
    def test_login_admin_va_al_panel(self):
        r = self.client.post('/login/', {'usuario': 'sarmientoc', 'clave': 'Admin123!'})
        self.assertRedirects(r, '/panel/')
        self.assertIsNotNone(Usuario.objects.get(DNI=ADMIN).FechaUltimoAcceso)

    def test_login_con_dni_o_correo(self):
        r = self.client.post('/login/', {'usuario': str(CHOFER), 'clave': 'Usuario123!'})
        self.assertRedirects(r, '/portal/')
        self.client.get('/logout/')
        r = self.client.post('/login/', {'usuario': 'LUCIANA.F@mudanzassalta.com.ar', 'clave': 'Usuario123!'})
        self.assertRedirects(r, '/portal/')

    def test_clave_incorrecta(self):
        r = self.client.post('/login/', {'usuario': 'sarmientoc', 'clave': 'otra'})
        self.assertContains(r, 'incorrectos')
        self.assertNotIn('usuario_dni', self.client.session)

    def test_usuario_dado_de_baja_no_entra(self):
        Usuario.objects.filter(DNI=CHOFER).update(Activo=False)
        r = self.client.post('/login/', {'usuario': 'fernandezl', 'clave': 'Usuario123!'})
        self.assertContains(r, 'dado de baja')
        self.assertNotIn('usuario_dni', self.client.session)

    def test_logout_cierra_la_sesion(self):
        self.entrar(ADMIN)
        self.client.get('/logout/')
        self.assertRedirects(self.client.get('/panel/'), '/login/')


class CambioObligatorioTest(BaseHito2):
    def cambiar(self, actual='Temporal123!', nueva='Nueva123!', confirmar=None):
        return self.client.post('/cambiar-clave-obligatoria/', {
            'dni': AYUDANTE, 'clave_actual': actual, 'nueva_clave': nueva,
            'confirmar_clave': confirmar or nueva})

    def test_login_pide_cambio(self):
        r = self.client.post('/login/', {'usuario': 'romerol', 'clave': 'Temporal123!'})
        self.assertTrue(r.context['cambio_obligatorio'])
        self.assertNotIn('usuario_dni', self.client.session)

    def test_cambio_correcto_entra_al_portal(self):
        self.assertRedirects(self.cambiar(), '/portal/')
        u = Usuario.objects.get(DNI=AYUDANTE)
        self.assertFalse(u.DebeCambiarClave)
        self.assertTrue(u.verificar_clave('Nueva123!'))

    def test_cambio_falla_y_despues_funciona(self):
        # bug corregido: el segundo intento fallaba porque se perdía la clave actual
        r = self.cambiar(nueva='Nueva123!', confirmar='Distinta123!')
        self.assertContains(r, 'no coinciden')
        r = self.cambiar(nueva='debil')
        self.assertTrue(r.context['cambio_obligatorio'])
        self.assertEqual(r.context['clave_actual'], 'Temporal123!')
        self.assertRedirects(self.cambiar(), '/portal/')

    def test_clave_actual_incorrecta(self):
        self.assertContains(self.cambiar(actual='Otra123!'), 'no coincide')

    def test_usuario_dado_de_baja_no_puede_cambiar_ni_entrar(self):
        Usuario.objects.filter(DNI=AYUDANTE).update(Activo=False)
        r = self.cambiar()
        self.assertNotIn('usuario_dni', self.client.session)
        self.assertTrue(Usuario.objects.get(DNI=AYUDANTE).verificar_clave('Temporal123!'))


class CrudUsuariosTest(BaseHito2):
    def setUp(self):
        self.entrar(ADMIN)

    def test_alta_genera_usuario_y_exige_cambio(self):
        r = self.alta()
        self.assertEqual(r.json(), {'ok': True, 'usuario': 'pereza'})
        u = Usuario.objects.get(DNI=30111222)
        self.assertEqual(u.Correo, 'aperez@mail.com')
        self.assertTrue(u.DebeCambiarClave)
        self.assertTrue(u.verificar_clave('Cliente123!'))
        self.assertNotEqual(u.Clave, 'Cliente123!')

    def test_alta_usuario_repetido_suma_numero(self):
        self.alta()
        r = self.alta(dni='30111223', correo='otra@mail.com')
        self.assertEqual(r.json()['usuario'], 'pereza1')

    def test_alta_rechaza_dni_correo_y_clave(self):
        self.assertEqual(self.alta(dni=str(CHOFER)).status_code, 400)
        self.assertEqual(self.alta(correo='luciana.f@mudanzassalta.com.ar').status_code, 400)
        self.assertEqual(self.alta(clave='debil').status_code, 400)
        self.assertFalse(Usuario.objects.filter(DNI=30111222).exists())

    def test_modificar_correo(self):
        r = self.client.post(f'/usuarios/{CHOFER}/modificar-correo/', {'correo': 'Nuevo@Mail.com'})
        self.assertTrue(r.json()['ok'])
        self.assertEqual(Usuario.objects.get(DNI=CHOFER).Correo, 'nuevo@mail.com')

    def test_modificar_correo_repetido(self):
        r = self.client.post(f'/usuarios/{CHOFER}/modificar-correo/',
                             {'correo': 'carlos.sarmiento@mudanzassalta.com.ar'})
        self.assertEqual(r.status_code, 400)

    def test_baja_logica_y_reactivacion(self):
        self.assertTrue(self.client.post(f'/usuarios/{CHOFER}/baja/').json()['ok'])
        u = Usuario.objects.get(DNI=CHOFER)
        self.assertFalse(u.Activo)
        self.assertIsNotNone(u.FechaBaja)
        self.assertTrue(self.client.post(f'/usuarios/{CHOFER}/reactivar/').json()['ok'])
        u.refresh_from_db()
        self.assertTrue(u.Activo)
        self.assertIsNone(u.FechaBaja)

    def test_restablecer_clave(self):
        r = self.client.post(f'/usuarios/{CHOFER}/restablecer-clave/').json()
        u = Usuario.objects.get(DNI=CHOFER)
        self.assertTrue(u.verificar_clave(r['clave_temporal']))
        self.assertTrue(u.DebeCambiarClave)

    def test_cambiar_rol(self):
        ayudante = Rol.objects.get(nom_rol='Ayudante de Carga')
        r = self.client.post(f'/usuarios/{CHOFER}/cambiar-rol/', {'idRol': ayudante.id_rol}).json()
        self.assertEqual((r['anterior'], r['nuevo']), ('Chofer', 'Ayudante de Carga'))
        self.assertEqual(Usuario.objects.get(DNI=CHOFER).idRol, ayudante)

    def test_cambiar_rol_invalido_o_igual(self):
        chofer = Rol.objects.get(nom_rol='Chofer')
        self.assertEqual(self.client.post(f'/usuarios/{CHOFER}/cambiar-rol/', {'idRol': chofer.id_rol}).status_code, 400)
        self.assertEqual(self.client.post(f'/usuarios/{CHOFER}/cambiar-rol/', {'idRol': 999}).status_code, 400)

    def test_vista_previa_usuario(self):
        r = self.client.get('/usuarios/preview-username/', {'apellido': 'Gómez', 'nombre': 'María'})
        self.assertEqual(r.json()['NombreUsuario'], 'gomezm')

    def test_panel_lista_usuarios_y_filtro_activos(self):
        Usuario.objects.filter(DNI=CHOFER).update(Activo=False)
        self.assertEqual(len(self.client.get('/panel/').context['usuarios']), 4)
        self.assertEqual(len(self.client.get('/panel/?activos=1').context['usuarios']), 3)


class BajaConPedidosActivosTest(BaseHito2):
    def setUp(self):
        self.entrar(ADMIN)
        from datetime import timedelta
        from django.utils import timezone
        from pedidos import reglas
        self.reglas = reglas
        self.pedido = reglas.registrar_pedido(
            Usuario.objects.get(DNI=29876543), timezone.localdate() + timedelta(days=1), time(9, 0),
            'Origen 1', 'Destino 2', Servicio.objects.get(Tipo_servicio='Mudanza local').id_servicio,
            'AD-321-JK', [{'objeto': Objeto.objects.get(nom_objeto='Cajas'), 'cantidad': 2, 'fragil': False}])

    def test_no_se_da_de_baja_con_pedido_activo(self):
        r = self.client.post('/usuarios/29876543/baja/')
        self.assertEqual(r.status_code, 400)
        self.assertTrue(Usuario.objects.get(DNI=29876543).Activo)

    def test_anulado_el_pedido_se_da_de_baja(self):
        self.reglas.anular(self.pedido.pk, Usuario.objects.get(DNI=ADMIN), 'Pedido duplicado')
        self.assertTrue(self.client.post('/usuarios/29876543/baja/').json()['ok'])


class CandadosTest(BaseHito2):
    def setUp(self):
        self.entrar(ADMIN)

    def test_no_se_da_de_baja_a_si_mismo(self):
        self.assertEqual(self.client.post(f'/usuarios/{ADMIN}/baja/').status_code, 400)
        self.assertTrue(Usuario.objects.get(DNI=ADMIN).Activo)

    def test_no_se_cambia_el_rol_a_si_mismo(self):
        chofer = Rol.objects.get(nom_rol='Chofer')
        r = self.client.post(f'/usuarios/{ADMIN}/cambiar-rol/', {'idRol': chofer.id_rol})
        self.assertEqual(r.status_code, 400)

    def test_baja_de_admin_si_quedan_otros(self):
        admin_rol = Rol.objects.get(nom_rol='Administrador')
        Usuario.objects.filter(DNI=CHOFER).update(idRol=admin_rol)
        self.assertTrue(self.client.post(f'/usuarios/{CHOFER}/baja/').json()['ok'])


class PermisosTest(BaseHito2):
    """Las operaciones del panel exigen administrador activo del lado del servidor."""
    OPERACIONES = [
        ('post', '/usuarios/alta/'),
        ('post', f'/usuarios/{AYUDANTE}/modificar-correo/'),
        ('post', f'/usuarios/{AYUDANTE}/baja/'),
        ('post', f'/usuarios/{AYUDANTE}/reactivar/'),
        ('post', f'/usuarios/{AYUDANTE}/restablecer-clave/'),
        ('post', f'/usuarios/{AYUDANTE}/cambiar-rol/'),
        ('get', '/usuarios/preview-username/'),
    ]

    def llamar_todas(self):
        return [getattr(self.client, m)(url).status_code for m, url in self.OPERACIONES]

    def test_sin_sesion_401(self):
        self.assertEqual(set(self.llamar_todas()), {401})

    def test_chofer_403(self):
        self.entrar(CHOFER)
        self.assertEqual(set(self.llamar_todas()), {403})

    def test_admin_dado_de_baja_pierde_la_sesion(self):
        self.entrar(ADMIN)
        Usuario.objects.filter(DNI=ADMIN).update(Activo=False)
        self.assertEqual(set(self.llamar_todas()), {401})

    def test_pantallas(self):
        self.assertRedirects(self.client.get('/panel/'), '/login/')
        self.assertRedirects(self.client.get('/portal/'), '/login/')
        self.entrar(CHOFER)
        self.assertRedirects(self.client.get('/panel/'), '/portal/')
        r = self.client.get('/portal/')
        self.assertEqual(r.status_code, 200)
        self.assertEqual([v.patente for v in r.context['vehiculos']], ['AE-123-CD'])


class OlvideClaveTest(BaseHito2):
    def test_genera_clave_provisoria(self):
        r = self.client.post('/olvide-clave/', {'identificador': 'fernandezl'}).json()
        u = Usuario.objects.get(DNI=CHOFER)
        self.assertTrue(u.verificar_clave(r['clave_provisoria']))
        self.assertTrue(u.DebeCambiarClave)

    def test_usuario_inexistente_o_de_baja(self):
        self.assertEqual(self.client.post('/olvide-clave/', {'identificador': 'nadie'}).status_code, 404)
        Usuario.objects.filter(DNI=CHOFER).update(Activo=False)
        self.assertEqual(self.client.post('/olvide-clave/', {'identificador': 'fernandezl'}).status_code, 403)


class DatosHito3Test(BaseHito2):
    def test_rol_cliente_y_permisos(self):
        cliente = Rol.objects.get(nom_rol='Cliente')
        self.assertEqual(
            set(PermisoRol.objects.filter(idRol=cliente).values_list('idPermiso__nom_permiso', flat=True)),
            {'PED_REGISTRAR', 'PED_CONSULTAR', 'PED_COMPROBANTE'})
        admin = set(PermisoRol.objects.filter(idRol__nom_rol='Administrador')
                    .values_list('idPermiso__nom_permiso', flat=True))
        self.assertTrue({'PED_CONSULTAR', 'PED_GESTIONAR', 'PED_ANULAR',
                         'PED_COMPROBANTE', 'SRV_GESTIONAR'} <= admin)
        self.assertNotIn('PED_REGISTRAR', admin)

    def test_clienta_de_prueba(self):
        u = Usuario.objects.get(NombreUsuario='gomezm')
        self.assertEqual((u.DNI, u.idRol.nom_rol, u.DebeCambiarClave), (29876543, 'Cliente', False))
        self.assertTrue(u.verificar_clave('Cliente123!'))

    def test_pedido_de_ejemplo_con_campos_nuevos(self):
        p = Pedido.objects.get()
        self.assertEqual(p.idUsuario.NombreUsuario, 'gomezm')
        self.assertEqual(p.estado, Pedido.FINALIZADO)
        self.assertEqual(p.total, 185000)
        self.assertTrue(p.origen and p.destino)
        detalle = p.detalles.get()
        self.assertEqual((detalle.precio_unitario, detalle.subtotal), (185000, 185000))
        self.assertEqual(p.hora_servicio, time(9, 0))
        item = p.inventario.get()
        self.assertEqual((item.idObjeto.nom_objeto, item.Cantidad, item.Fragil), ('Cajas', 42, True))
        self.assertEqual(str(item), '42 x Cajas')

    def test_servicios_activos_por_defecto(self):
        self.assertFalse(Servicio.objects.filter(Activo=False).exists())


class PortalTest(BaseHito2):
    def test_el_portal_muestra_el_nombre_de_los_permisos(self):
        self.entrar(CHOFER)
        self.assertContains(self.client.get('/portal/'), 'MUDANZAS_OPERAR')
