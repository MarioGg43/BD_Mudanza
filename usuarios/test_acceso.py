"""Un rol armado a medida habilita exactamente lo que se le tildó."""
import io

from django.core.management import call_command
from django.test import TestCase

from usuarios.models import Permiso, PermisoRol, Rol, Usuario
from usuarios.utils import hash_password

ADMIN, CHOFER, AYUDANTE, CLIENTE = 35123456, 40987654, 38999888, 29876543


class BaseAcceso(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command('init_data', stdout=io.StringIO())
        cls.recepcion = Rol.objects.create(nom_rol='Recepcionista', desc_rol='Atiende a los clientes')
        for c in ('USR_CONSULTAR', 'USR_CREAR', 'PED_CONSULTAR', 'PED_GESTIONAR'):
            PermisoRol.objects.create(idRol=cls.recepcion, idPermiso=Permiso.objects.get(nom_permiso=c))
        cls.vacio = Rol.objects.create(nom_rol='Sin nada')
        for dni, usuario, rol in ((20111222, 'recepcion', cls.recepcion), (20333444, 'vacio', cls.vacio)):
            Usuario.objects.create(DNI=dni, Nombre='Test', Apellido=usuario, Correo=f'{usuario}@mail.com',
                                   NombreUsuario=usuario, Clave=hash_password('Clave123!'),
                                   DebeCambiarClave=False, idRol=rol)

    def entrar(self, dni):
        s = self.client.session
        s['usuario_dni'] = dni
        s.save()


class RolAMedidaTest(BaseAcceso):
    def setUp(self):
        self.entrar(20111222)

    def test_entra_al_panel_y_da_de_alta(self):
        self.assertEqual(self.client.get('/panel/').status_code, 200)
        r = self.client.post('/usuarios/alta/', {'dni': '30111222', 'apellido': 'Pérez', 'nombre': 'Ana',
                                                 'correo': 'ana@mail.com', 'clave': 'Cliente123!',
                                                 'idRol': Rol.objects.get(nom_rol='Cliente').id_rol})
        self.assertTrue(r.json()['ok'])

    def test_lo_que_no_se_le_tildo_da_403(self):
        for url in (f'/usuarios/{CHOFER}/baja/', f'/usuarios/{CHOFER}/cambiar-rol/',
                    f'/usuarios/{CHOFER}/restablecer-clave/', f'/usuarios/{CHOFER}/modificar-correo/'):
            self.assertEqual(self.client.post(url).status_code, 403, url)
        self.assertEqual(self.client.get('/vehiculos/').status_code, 403)

    def test_pedidos_confirma_pero_no_anula(self):
        self.assertEqual(self.client.get('/pedidos/').status_code, 200)
        p = Usuario.objects.get(DNI=CLIENTE).pedidos.first()
        self.assertEqual(self.client.get(f'/pedidos/{p.pk}/anular/').status_code, 403)

    def test_login_lo_lleva_al_panel(self):
        self.client.get('/logout/')
        r = self.client.post('/login/', {'usuario': 'recepcion', 'clave': 'Clave123!'})
        self.assertRedirects(r, '/panel/')


class PantallaInicioTest(BaseAcceso):
    def test_cada_rol_inicial_llega_a_su_pantalla(self):
        for dni, destino in ((ADMIN, '/panel/'), (CLIENTE, '/pedidos/'), (CHOFER, '/portal/'),
                             (AYUDANTE, '/portal/')):
            self.entrar(dni)
            self.assertRedirects(self.client.get('/'), destino, msg_prefix=str(dni))

    def test_un_rol_sin_permisos_llega_a_sin_permisos(self):
        self.entrar(20333444)
        self.assertRedirects(self.client.get('/'), '/sin-permisos/')
        self.assertContains(self.client.get('/sin-permisos/'), 'todavía no tiene pantallas asignadas')
        self.assertRedirects(self.client.get('/panel/'), '/sin-permisos/')
        self.assertRedirects(self.client.get('/portal/'), '/sin-permisos/')

    def test_sin_permisos_requiere_sesion(self):
        self.assertRedirects(self.client.get('/sin-permisos/'), '/login/')


class GestorActivoTest(BaseAcceso):
    def setUp(self):
        self.entrar(ADMIN)
        self.admin_rol = Rol.objects.get(nom_rol='Administrador')

    def test_no_se_da_de_baja_al_unico_gestor(self):
        # el recepcionista recibe USR_BAJA; el admin es el único gestor de roles
        PermisoRol.objects.create(idRol=self.recepcion, idPermiso=Permiso.objects.get(nom_permiso='USR_BAJA'))
        self.entrar(20111222)
        r = self.client.post(f'/usuarios/{ADMIN}/baja/')
        self.assertEqual(r.status_code, 400)
        self.assertEqual(r.json()['error'],
                         'El sistema tiene que quedar con al menos un usuario activo que pueda gestionar roles.')
        self.assertTrue(Usuario.objects.get(DNI=ADMIN).Activo)

    def test_cambiar_rol_no_deja_al_sistema_sin_gestor(self):
        from usuarios.reglas_roles import error_cambio_rol_gestor, MENSAJE_SIN_GESTOR
        admin = Usuario.objects.get(DNI=ADMIN)
        chofer_rol = Rol.objects.get(nom_rol='Chofer')
        self.assertEqual(error_cambio_rol_gestor(admin, chofer_rol), MENSAJE_SIN_GESTOR)
        Usuario.objects.filter(DNI=CHOFER).update(idRol=self.admin_rol)
        self.assertIsNone(error_cambio_rol_gestor(admin, chofer_rol))

    def test_baja_del_unico_gestor_por_regla(self):
        from usuarios.reglas_roles import error_baja_gestor, MENSAJE_SIN_GESTOR
        admin = Usuario.objects.get(DNI=ADMIN)
        self.assertEqual(error_baja_gestor(admin), MENSAJE_SIN_GESTOR)
        self.assertIsNone(error_baja_gestor(Usuario.objects.get(DNI=CHOFER)))


class InicioParcialTest(BaseAcceso):
    def test_solo_registrar_va_a_pedir_mudanza(self):
        PermisoRol.objects.create(idRol=self.vacio, idPermiso=Permiso.objects.get(nom_permiso='PED_REGISTRAR'))
        self.entrar(20333444)
        self.assertRedirects(self.client.get('/'), '/pedidos/nuevo/')

    def test_gestionar_sin_consultar_y_portal_va_al_portal(self):
        for c in ('PED_GESTIONAR', 'MUDANZAS_OPERAR'):
            PermisoRol.objects.create(idRol=self.vacio, idPermiso=Permiso.objects.get(nom_permiso=c))
        self.entrar(20333444)
        self.assertRedirects(self.client.get('/'), '/portal/')

    def test_cambiar_rol_del_unico_gestor_por_http(self):
        PermisoRol.objects.create(idRol=self.recepcion, idPermiso=Permiso.objects.get(nom_permiso='USR_CAMBIAR_ROL'))
        self.entrar(20111222)
        r = self.client.post(f'/usuarios/{ADMIN}/cambiar-rol/', {'idRol': Rol.objects.get(nom_rol='Chofer').id_rol})
        self.assertEqual(r.status_code, 400)
        self.assertEqual(r.json()['error'],
                         'El sistema tiene que quedar con al menos un usuario activo que pueda gestionar roles.')


class MenuYBotonesTest(BaseAcceso):
    def test_menu_del_recepcionista(self):
        self.entrar(20111222)
        r = self.client.get('/pedidos/')
        self.assertContains(r, 'href="/panel/"')
        self.assertContains(r, 'href="/pedidos/"')
        self.assertNotContains(r, 'href="/vehiculos/"')
        self.assertNotContains(r, 'href="/servicios/"')
        self.assertNotContains(r, 'href="/pedidos/nuevo/"')

    def test_menu_del_cliente(self):
        self.entrar(CLIENTE)
        r = self.client.get('/pedidos/')
        self.assertContains(r, 'Mis pedidos')
        self.assertContains(r, 'href="/pedidos/nuevo/"')
        self.assertNotContains(r, 'href="/panel/"')

    def test_panel_sin_usr_baja_no_muestra_baja(self):
        self.entrar(20111222)
        r = self.client.get('/panel/')
        self.assertContains(r, 'Alta de Usuario')
        self.assertNotContains(r, 'abrirModalBaja(\'')
        self.assertNotContains(r, 'abrirModalRestablecer(\'')
        self.entrar(ADMIN)
        self.assertContains(self.client.get('/panel/'), 'abrirModalBaja(\'')
