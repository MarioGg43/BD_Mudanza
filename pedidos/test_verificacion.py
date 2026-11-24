"""Crear cuenta con el código del correo: la cuenta se crea recién cuando se escribe el código."""
import io
import re
from unittest import mock

from django.core import mail
from django.core.management import call_command
from django.test import TestCase

from usuarios.models import Usuario

from . import verificacion

DATOS = {'dni': '30111222', 'apellido': 'Pérez', 'nombre': 'Ana', 'correo': 'ana@mail.com',
         'telefono': '+54 387 4112233', 'clave': 'Cliente123!', 'clave2': 'Cliente123!'}


class CodigoPorCorreoTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command('init_data', stdout=io.StringIO())

    def pedir(self, **cambios):
        return self.client.post('/registro/', {**DATOS, **cambios})

    def codigo(self):
        return re.search(r'\b(\d{6})\b', mail.outbox[-1].body).group(1)

    def confirmar(self, codigo):
        return self.client.post('/registro/verificar/', {'codigo': codigo})

    def test_la_cuenta_se_crea_recien_con_el_codigo(self):
        self.assertRedirects(self.pedir(), '/registro/verificar/')
        self.assertFalse(Usuario.objects.filter(DNI=30111222).exists())       # todavía no
        self.assertEqual(mail.outbox[0].to, ['ana@mail.com'])
        self.assertNotIn('Cliente123!', str(self.client.session[verificacion.EN_SESION]))  # la clave va cifrada
        r = self.client.get('/registro/verificar/')
        self.assertContains(r, 'an***@mail.com')
        self.assertRedirects(self.confirmar(self.codigo()), '/pedidos/', fetch_redirect_response=False)
        u = Usuario.objects.get(DNI=30111222)
        self.assertEqual((u.Telefono, u.idRol.nom_rol), ('+54 387 4112233', 'Cliente'))
        self.assertTrue(u.verificar_clave('Cliente123!'))
        self.assertEqual(self.client.session['usuario_dni'], 30111222)

    def test_el_telefono_es_obligatorio(self):
        r = self.pedir(telefono='')
        self.assertContains(r, 'Escribí el teléfono.')
        self.assertEqual(len(mail.outbox), 0)

    def test_codigo_equivocado_y_demasiados_intentos(self):
        self.pedir()
        bueno = self.codigo()
        malo = '000000' if bueno != '000000' else '111111'
        self.assertContains(self.confirmar(malo), 'Te quedan 4 intentos')
        self.assertContains(self.confirmar('12'), 'El código tiene 6 números.')
        for _ in range(4):
            r = self.confirmar(malo)
        self.assertContains(r, 'Pedí un código nuevo')
        self.assertContains(self.confirmar(bueno), 'Pedí un código nuevo')  # ya no sirve ni el correcto
        self.assertFalse(Usuario.objects.filter(DNI=30111222).exists())

    def test_el_codigo_vence(self):
        self.pedir()
        codigo = self.codigo()
        s = self.client.session
        s[verificacion.EN_SESION]['vence'] = 0
        s.save()
        r = self.confirmar(codigo)
        self.assertRedirects(r, '/registro/', fetch_redirect_response=False)
        self.assertFalse(Usuario.objects.filter(DNI=30111222).exists())

    def test_pedir_otro_codigo_espera_un_minuto_y_reemplaza_al_anterior(self):
        self.pedir()
        primero = self.codigo()
        self.assertContains(self.client.post('/registro/verificar/', {'accion': 'reenviar'}), 'Esperá')
        s = self.client.session
        s[verificacion.EN_SESION]['enviado'] -= verificacion.ESPERA_REENVIO
        s.save()
        self.assertRedirects(self.client.post('/registro/verificar/', {'accion': 'reenviar'}), '/registro/verificar/')
        self.assertEqual(len(mail.outbox), 2)
        segundo = self.codigo()
        if segundo != primero:
            self.assertContains(self.confirmar(primero), 'no es correcto')
        self.assertRedirects(self.confirmar(segundo), '/pedidos/', fetch_redirect_response=False)

    def test_si_el_correo_no_sale_no_queda_nada_esperando(self):
        with mock.patch('pedidos.verificacion.send_mail', side_effect=OSError('sin conexión')):
            r = self.pedir()
        self.assertContains(r, 'No pudimos mandar el código')
        self.assertNotIn(verificacion.EN_SESION, self.client.session)

    def test_si_otro_uso_el_correo_mientras_tanto_no_se_duplica(self):
        self.pedir()
        codigo = self.codigo()
        Usuario.objects.filter(DNI=29876543).update(Correo='ana@mail.com')
        self.assertRedirects(self.confirmar(codigo), '/registro/', fetch_redirect_response=False)
        self.assertFalse(Usuario.objects.filter(DNI=30111222).exists())
