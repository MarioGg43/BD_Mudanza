"""«Mi cuenta»: cada persona ve sus datos y cambia su clave; el cliente, también su correo y teléfono."""
import io

from django.core.management import call_command
from django.test import TestCase

from usuarios.models import Usuario

CLIENTE, ADMIN, CHOFER = 29876543, 35123456, 40987654
URL = '/mi-cuenta/'


class MiCuentaTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command('init_data', stdout=io.StringIO())

    def entrar(self, dni):
        s = self.client.session
        s['usuario_dni'] = dni
        s.save()

    def test_sin_sesion_va_al_login(self):
        self.assertRedirects(self.client.get(URL), '/login/')

    def test_muestra_sus_datos_y_esta_en_el_menu(self):
        self.entrar(CLIENTE)
        r = self.client.get(URL)
        self.assertContains(r, '29876543')
        self.assertContains(r, 'name="correo"')
        self.assertContains(r, 'href="/mi-cuenta/"')

    def test_el_cliente_cambia_correo_y_telefono(self):
        self.entrar(CLIENTE)
        r = self.client.post(URL, {'accion': 'datos', 'correo': ' Maria.Nueva@Ejemplo.com ', 'telefono': '387 4112233'})
        self.assertRedirects(r, URL)
        u = Usuario.objects.get(DNI=CLIENTE)
        self.assertEqual((u.Correo, u.Telefono), ('maria.nueva@ejemplo.com', '387 4112233'))

    def test_correo_de_otro_o_telefono_raro(self):
        self.entrar(CLIENTE)
        otro = Usuario.objects.get(DNI=ADMIN).Correo
        r = self.client.post(URL, {'accion': 'datos', 'correo': otro, 'telefono': ''})
        self.assertContains(r, 'Ese correo ya lo usa otra cuenta.')
        r = self.client.post(URL, {'accion': 'datos', 'correo': 'maria@ejemplo.com', 'telefono': 'llamame'})
        self.assertContains(r, 'Escribí un teléfono válido')
        self.assertNotEqual(Usuario.objects.get(DNI=CLIENTE).Correo, 'maria@ejemplo.com')

    def test_el_personal_no_cambia_su_correo(self):
        # al personal el correo se lo cambia el administrador (Hito 2)
        self.entrar(CHOFER)
        antes = Usuario.objects.get(DNI=CHOFER).Correo
        r = self.client.get(URL)
        self.assertNotContains(r, 'name="correo"')
        self.assertContains(r, 'pedíselo al administrador')
        self.client.post(URL, {'accion': 'datos', 'correo': 'otro@ejemplo.com', 'telefono': ''})
        self.assertEqual(Usuario.objects.get(DNI=CHOFER).Correo, antes)

    def test_cambiar_la_clave(self):
        self.entrar(CLIENTE)
        r = self.client.post(URL, {'accion': 'clave', 'actual': 'Cliente123!', 'nueva': 'Mudanza2026!', 'confirmar': 'Mudanza2026!'})
        self.assertRedirects(r, URL)
        u = Usuario.objects.get(DNI=CLIENTE)
        self.assertTrue(u.verificar_clave('Mudanza2026!'))
        self.assertFalse(u.verificar_clave('Cliente123!'))

    def test_la_clave_tiene_sus_controles(self):
        self.entrar(CLIENTE)
        casos = [
            ({'actual': 'MalaClave1!', 'nueva': 'Mudanza2026!', 'confirmar': 'Mudanza2026!'}, 'La clave actual no coincide.'),
            ({'actual': 'Cliente123!', 'nueva': 'Mudanza2026!', 'confirmar': 'Otra2026!'}, 'Las dos claves nuevas no coinciden.'),
            ({'actual': 'Cliente123!', 'nueva': 'corta', 'confirmar': 'corta'}, 'is-invalid'),
            ({'actual': 'Cliente123!', 'nueva': 'Cliente123!', 'confirmar': 'Cliente123!'}, 'tiene que ser distinta de la actual'),
        ]
        for datos, mensaje in casos:
            self.assertContains(self.client.post(URL, {'accion': 'clave', **datos}), mensaje, msg_prefix=mensaje)
        self.assertTrue(Usuario.objects.get(DNI=CLIENTE).verificar_clave('Cliente123!'))

    def test_el_cambio_queda_en_la_auditoria(self):
        from usuarios.models import LogAuditoria
        self.entrar(CLIENTE)
        self.client.post(URL, {'accion': 'datos', 'correo': 'maria.g@ejemplo.com', 'telefono': ''})
        log = LogAuditoria.objects.order_by('-pk').first()
        self.assertEqual((log.tabla, log.usuario.DNI), ('USUARIOS', CLIENTE))  # quién lo cambió: ella misma
        self.assertIn('maria.g@ejemplo.com', log.valores_nuevos)
