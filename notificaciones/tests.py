"""Pruebas de las notificaciones y alertas (Parcial N° 2, M3)."""
import io
from datetime import time, timedelta

from django.core import mail
from django.core.management import call_command
from django.test import TestCase, override_settings
from django.utils import timezone

from notificaciones import reglas as alertas
from pedidos import reglas
from usuarios.models import Configuracion, Notificacion, Objeto, Pedido, Servicio, Usuario

ADMIN, CHOFER, CLIENTE = 35123456, 40987654, 29876543


@override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
class BaseAlertas(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command('init_data', stdout=io.StringIO())
        cls.cliente = Usuario.objects.get(DNI=CLIENTE)
        cls.admin = Usuario.objects.get(DNI=ADMIN)
        cls.chofer = Usuario.objects.get(DNI=CHOFER)
        cls.local = Servicio.objects.get(Tipo_servicio='Mudanza local')

    def pedido(self, dias=3, hora=time(9), patente='AD-321-JK'):
        return reglas.registrar_pedido(
            self.cliente, timezone.localdate() + timedelta(days=dias), hora, 'Origen 1', 'Destino 2',
            self.local.id_servicio, patente, [{'objeto': Objeto.objects.get(nom_objeto='Cajas'), 'cantidad': 2, 'fragil': False}])

    def config(self, clave, valor):
        Configuracion.objects.filter(clave=clave).update(valor=str(valor))

    def entrar(self, dni):
        s = self.client.session
        s['usuario_dni'] = dni
        s.save()


class ConfiguracionTest(BaseAlertas):
    def test_los_umbrales_estan_en_la_tabla(self):
        claves = set(Configuracion.objects.values_list('clave', flat=True))
        self.assertTrue({'horas_sin_confirmar', 'minutos_atraso', 'cancelaciones_cliente', 'dias_cancelaciones',
                         'correo_empresa', 'correo_al_cliente'} <= claves)

    def test_solo_el_administrador_cambia_los_umbrales(self):
        self.entrar(CLIENTE)
        self.assertEqual(self.client.get('/notificaciones/configuracion/').status_code, 403)
        self.entrar(ADMIN)
        datos = {c.clave: c.valor for c in Configuracion.objects.all()}
        r = self.client.post('/notificaciones/configuracion/', {**datos, 'horas_sin_confirmar': '72'})
        self.assertRedirects(r, '/notificaciones/configuracion/')
        self.assertEqual(alertas.parametro_entero('horas_sin_confirmar', 0), 72)
        r = self.client.post('/notificaciones/configuracion/', {**datos, 'horas_sin_confirmar': 'mucho'})
        self.assertContains(r, 'Tiene que ser un número entero')
        self.assertEqual(alertas.parametro_entero('horas_sin_confirmar', 0), 72)


class Regla1SinConfirmarTest(BaseAlertas):
    def test_avisa_dentro_del_umbral_y_manda_correo_a_la_empresa(self):
        self.config('correo_empresa', 'empresa@ejemplo.com')
        cerca, lejos = self.pedido(dias=1), self.pedido(dias=6, patente='AE-123-CD')
        with self.captureOnCommitCallbacks(execute=True):
            self.assertEqual(alertas.pedidos_sin_confirmar(), 1)
        n = Notificacion.objects.get(clave=f'sin_confirmar:{cerca.pk}')
        self.assertEqual((n.tipo, n.destino_perfil.nom_rol), (alertas.SIN_CONFIRMAR, 'Administrador'))
        self.assertFalse(Notificacion.objects.filter(clave=f'sin_confirmar:{lejos.pk}').exists())
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, ['empresa@ejemplo.com'])
        self.assertIn(f'Pedido N° {cerca.pk} sin confirmar', mail.outbox[0].subject)
        self.assertIn('Enviado a empresa@ejemplo.com', Notificacion.objects.get(pk=n.pk).correo)

    def test_no_se_dispara_dos_veces(self):
        self.config('correo_empresa', 'empresa@ejemplo.com')
        self.pedido(dias=1)
        with self.captureOnCommitCallbacks(execute=True):
            alertas.pedidos_sin_confirmar()
            self.assertEqual(alertas.pedidos_sin_confirmar(), 0)  # la segunda vez no crea nada
        call_command('evaluar_alertas', stdout=io.StringIO())
        self.assertEqual(Notificacion.objects.filter(tipo=alertas.SIN_CONFIRMAR).count(), 1)
        self.assertEqual(len(mail.outbox), 1)                         # un solo correo

    def test_el_umbral_es_el_de_la_configuracion(self):
        self.pedido(dias=4)
        self.assertEqual(alertas.pedidos_sin_confirmar(), 0)          # 48 h por defecto
        self.config('horas_sin_confirmar', 24 * 5)
        self.assertEqual(alertas.pedidos_sin_confirmar(), 1)


class Regla2AtrasadaTest(BaseAlertas):
    def test_confirmada_que_paso_su_fin_y_nadie_finalizo(self):
        p = self.pedido(dias=2)
        reglas.asignar_personal(p.pk, self.chofer.pk)
        reglas.confirmar(p.pk)
        Notificacion.objects.all().delete()  # el aviso de confirmación al cliente no es parte de esta prueba
        Pedido.objects.filter(pk=p.pk).update(fecha_servicio=timezone.localdate() - timedelta(days=1))
        self.assertEqual(alertas.mudanzas_atrasadas(), 1)
        self.assertEqual(Notificacion.objects.get().tipo, alertas.ATRASADA)
        self.config('minutos_atraso', 60 * 24 * 3)                    # con 3 días de tolerancia no avisaría
        Notificacion.objects.all().delete()
        self.assertEqual(alertas.mudanzas_atrasadas(), 0)


class Regla3CancelacionesTest(BaseAlertas):
    def test_avisa_al_llegar_al_limite_en_tiempo_real(self):
        self.config('cancelaciones_cliente', 2)
        p1, p2, p3 = self.pedido(dias=3), self.pedido(dias=5), self.pedido(dias=7)
        reglas.cancelar_por_cliente(p1.pk, self.cliente, 'Ya no me mudo')
        self.assertFalse(Notificacion.objects.filter(tipo=alertas.CANCELACIONES).exists())
        reglas.cancelar_por_cliente(p2.pk, self.cliente, 'Cambié de fecha')
        n = Notificacion.objects.get(tipo=alertas.CANCELACIONES)
        self.assertIn('ya tiene 2 pedidos anulados', n.mensaje)
        self.assertEqual(n.destino_perfil.nom_rol, 'Administrador')
        reglas.cancelar_por_cliente(p3.pk, self.cliente, 'Otra vez')    # la tercera: un aviso nuevo
        self.assertEqual(Notificacion.objects.filter(tipo=alertas.CANCELACIONES).count(), 2)


class Regla4AvisoAlClienteTest(BaseAlertas):
    def test_al_confirmar_le_llega_aviso_y_correo(self):
        p = self.pedido(dias=4)
        reglas.asignar_personal(p.pk, self.chofer.pk)
        with self.captureOnCommitCallbacks(execute=True):
            reglas.confirmar(p.pk)
        n = Notificacion.objects.get(clave=f'confirmado:{p.pk}')
        self.assertEqual(n.destino_usuario, self.cliente)
        self.assertEqual(mail.outbox[0].to, [self.cliente.Correo])
        self.assertIn('Confirmamos tu mudanza', mail.outbox[0].body)
        self.assertIn(f'/pedidos/{p.pk}/', mail.outbox[0].body)

    def test_sin_correo_si_la_configuracion_lo_apaga(self):
        self.config('correo_al_cliente', 0)
        p = self.pedido(dias=4)
        reglas.asignar_personal(p.pk, self.chofer.pk)
        with self.captureOnCommitCallbacks(execute=True):
            reglas.confirmar(p.pk)
        self.assertTrue(Notificacion.objects.filter(clave=f'confirmado:{p.pk}').exists())
        self.assertEqual(mail.outbox, [])

    def test_al_reprogramar(self):
        p = self.pedido(dias=4)
        with self.captureOnCommitCallbacks(execute=True):
            reglas.reprogramar(p.pk, self.admin, timezone.localdate() + timedelta(days=6), time(10), 'AD-321-JK', 'Clima')
        n = Notificacion.objects.get(tipo=alertas.REPROGRAMADO)
        self.assertIn('cambió de horario', n.mensaje)
        self.assertEqual(len(mail.outbox), 1)

    def test_si_el_correo_falla_la_operacion_sigue(self):
        p = self.pedido(dias=4)
        reglas.asignar_personal(p.pk, self.chofer.pk)
        with self.settings(EMAIL_BACKEND='notificaciones.tests.CorreoQueFalla'):
            with self.captureOnCommitCallbacks(execute=True):
                reglas.confirmar(p.pk)
        self.assertEqual(Pedido.objects.get(pk=p.pk).estado, Pedido.CONFIRMADO)
        self.assertIn('No se pudo enviar', Notificacion.objects.get(clave=f'confirmado:{p.pk}').correo)


class CorreoQueFalla:
    def __init__(self, *args, **kwargs):
        pass

    def send_messages(self, mensajes):
        raise ConnectionError('Gmail no responde')


class BandejaTest(BaseAlertas):
    def setUp(self):
        self.para_admin, _ = alertas.notificar('prueba:1', 'Prueba', 'Para el administrador', 'Administrador',
                                               enlace='/pedidos/')
        self.para_cliente, _ = alertas.notificar('prueba:2', 'Prueba', 'Para María', 'Cliente', usuario=self.cliente)

    def test_campanita_con_el_numero_y_cada_uno_ve_lo_suyo(self):
        self.entrar(ADMIN)
        r = self.client.get('/notificaciones/')
        self.assertContains(r, 'Para el administrador')
        self.assertNotContains(r, 'Para María')
        self.assertContains(r, 'class="barra-numero">1<')  # la campanita de la barra de arriba (menú lateral)
        self.entrar(CLIENTE)
        self.assertContains(self.client.get('/notificaciones/'), 'Para María')

    def test_abrir_la_marca_leida_y_lleva_al_enlace(self):
        self.entrar(ADMIN)
        r = self.client.post(f'/notificaciones/{self.para_admin.pk}/', {'ir': '1'})
        self.assertRedirects(r, '/pedidos/', fetch_redirect_response=False)
        n = Notificacion.objects.get(pk=self.para_admin.pk)
        self.assertTrue(n.leida)
        self.assertIsNotNone(n.fecha_lectura)
        self.assertNotContains(self.client.get('/notificaciones/'), 'campanita-numero')

    def test_no_puede_abrir_una_ajena(self):
        self.entrar(ADMIN)
        self.assertEqual(self.client.post(f'/notificaciones/{self.para_cliente.pk}/').status_code, 404)

    def test_marcar_todas(self):
        self.entrar(ADMIN)
        self.client.post('/notificaciones/leer-todas/')
        self.assertFalse(Notificacion.objects.filter(pk=self.para_admin.pk, leida=False).exists())
        self.assertTrue(Notificacion.objects.filter(pk=self.para_cliente.pk, leida=False).exists())

    def test_evaluar_ahora_desde_la_pantalla(self):
        self.pedido(dias=1)
        self.entrar(ADMIN)
        r = self.client.post('/notificaciones/evaluar/', follow=True)
        self.assertContains(r, '1 aviso nuevo')
