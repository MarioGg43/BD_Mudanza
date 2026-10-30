"""«Empezamos» / «Terminamos»: el chofer marca la hora real de la mudanza desde el portal."""
from datetime import datetime, time, timedelta
from unittest import mock

from django.utils import timezone

from pedidos import reglas
from pedidos.test_reglas import ADMIN, BaseReglas
from usuarios.auditoria import con_usuario
from usuarios.models import LogAuditoria, Pedido, Usuario


class EmpezamosTest(BaseReglas):
    def setUp(self):
        self.chofer = Usuario.objects.get(DNI=40987654)
        self.ayudante = Usuario.objects.get(DNI=38999888)
        self.p = self.registrar(id_servicio=self.flete.id_servicio)  # mañana de 9 a 14
        reglas.asignar_personal(self.p.pk, self.chofer.pk, [self.ayudante.pk])
        reglas.confirmar(self.p.pk)

    def a_las(self, hora, minuto=0, dias=1):
        momento = timezone.make_aware(datetime.combine(self.dia(dias), time(hora, minuto)))
        return mock.patch('django.utils.timezone.now', return_value=momento)

    def entrar(self, dni):
        s = self.client.session
        s['usuario_dni'], s['usuario_rol'] = dni, Usuario.objects.get(DNI=dni).idRol.nom_rol
        s.save()

    def test_el_chofer_empieza_y_termina_y_el_pedido_se_finaliza(self):
        with self.a_las(9, 10):
            reglas.marcar_inicio(self.p.pk, self.chofer)
        self.p.refresh_from_db()
        self.assertTrue(self.p.en_curso)
        with self.a_las(13, 40):
            reglas.marcar_fin(self.p.pk, self.chofer)
        self.p.refresh_from_db()
        self.assertEqual(self.p.estado, Pedido.FINALIZADO)
        self.assertEqual(timezone.localtime(self.p.fin_real).time(), time(13, 40))
        self.assertFalse(self.p.en_curso)

    def test_se_puede_empezar_desde_dos_horas_antes(self):
        with self.a_las(6, 59):
            with self.assertRaises(reglas.ErrorPedido) as ctx:
                reglas.marcar_inicio(self.p.pk, self.chofer)
            self.assertIn('Todavía es temprano', str(ctx.exception))
        with self.a_las(7, 0):
            reglas.marcar_inicio(self.p.pk, self.chofer)

    def test_solo_el_chofer_de_esa_mudanza(self):
        with self.a_las(9):
            for quien in (self.ayudante, Usuario.objects.get(DNI=ADMIN)):
                with self.assertRaises(reglas.ErrorPedido) as ctx:
                    reglas.marcar_inicio(self.p.pk, quien)
                self.assertIn('Solo el chofer', str(ctx.exception))

    def test_no_se_marca_dos_veces_ni_se_termina_sin_empezar_ni_un_pendiente(self):
        with self.a_las(9):
            with self.assertRaises(reglas.ErrorPedido):
                reglas.marcar_fin(self.p.pk, self.chofer)
            reglas.marcar_inicio(self.p.pk, self.chofer)
            with self.assertRaises(reglas.ErrorPedido):
                reglas.marcar_inicio(self.p.pk, self.chofer)
        q = self.registrar(id_servicio=self.flete.id_servicio, hora_servicio=time(15, 0))
        reglas.asignar_personal(q.pk, self.chofer.pk)  # queda pendiente
        with self.a_las(15):
            with self.assertRaises(reglas.ErrorPedido):
                reglas.marcar_inicio(q.pk, self.chofer)

    def test_si_empiezan_tarde_el_fin_esperado_se_corre(self):
        with self.a_las(10, 30):
            reglas.marcar_inicio(self.p.pk, self.chofer)  # una hora y media tarde
        self.p.refresh_from_db()
        self.assertEqual(timezone.localtime(self.p.fin_esperado).time(), time(15, 30))
        with self.a_las(15, 0):
            self.assertEqual(reglas.recordatorio_finalizar(), [])   # todavía no debería haber terminado
        with self.a_las(15, 31):
            self.assertEqual([p.pk for p in reglas.recordatorio_finalizar()], [self.p.pk])

    def test_portal_botones_solo_para_el_chofer_y_la_mudanza_no_desaparece_a_la_hora(self):
        with self.a_las(9, 5):
            self.entrar(40987654)
            r = self.client.get('/portal/')
            self.assertContains(r, 'Empezamos')                         # ya empezó el horario y sigue a la vista
            r = self.client.post(f'/pedidos/{self.p.pk}/empezar/')
            self.assertRedirects(r, '/portal/', fetch_redirect_response=False)
            r = self.client.get('/portal/')
            self.assertContains(r, 'En curso desde las 09:05')
            self.assertContains(r, 'Terminamos')
            self.entrar(38999888)                                       # el ayudante
            r = self.client.get('/portal/')
            self.assertContains(r, 'En curso desde las 09:05')
            self.assertNotContains(r, 'Terminamos</button>')
            r = self.client.post(f'/pedidos/{self.p.pk}/terminar/', follow=True)
            self.assertContains(r, 'Solo el chofer')
        self.p.refresh_from_db()
        self.assertEqual(self.p.estado, Pedido.CONFIRMADO)

    def test_queda_en_la_auditoria_y_el_admin_lo_ve(self):
        with self.a_las(9), con_usuario(self.chofer):
            reglas.marcar_inicio(self.p.pk, self.chofer)
        log = LogAuditoria.objects.get(tabla='PEDIDOS', usuario=self.chofer)
        self.entrar(ADMIN)
        with self.a_las(9, 30):
            r = self.client.get('/auditoria/')
            self.assertContains(r, f'Luciana Fernandez marcó «Empezamos» en el pedido N° {self.p.pk}')
            self.assertContains(self.client.get('/pedidos/'), 'En curso')
            self.assertContains(self.client.get(f'/pedidos/{self.p.pk}/'), 'Real (lo marcó el chofer)')
        self.assertEqual(log.accion, 'Modificación')
