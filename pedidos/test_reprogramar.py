"""Reprogramar un pedido: cambio de fecha, hora o vehículo con motivo, historial y aviso al cliente."""
from datetime import time

from pedidos import reglas
from pedidos.test_reglas import ADMIN, CLIENTE, BaseReglas
from usuarios.models import Pedido, Reprogramacion, Usuario

DEMORA = 'Demora en una mudanza anterior'


class ReprogramarTest(BaseReglas):
    def setUp(self):
        self.chofer = Usuario.objects.get(DNI=40987654)
        self.ayudante = Usuario.objects.get(DNI=38999888)
        self.p = self.registrar(id_servicio=self.flete.id_servicio)  # mañana de 9 a 14 en AD-321-JK

    def reprogramar(self, **cambios):
        datos = dict(fecha=self.dia(2), hora=time(10, 0), patente='AD-321-JK', motivo=DEMORA, observacion='')
        datos.update(cambios)
        return reglas.reprogramar(self.p.pk, self.admin, **datos)

    def assertRechaza(self, campo, **cambios):
        with self.assertRaises(reglas.ErrorPedido) as ctx:
            self.reprogramar(**cambios)
        self.assertIn(campo, ctx.exception.errores)
        self.assertFalse(Reprogramacion.objects.exists())
        return ctx.exception.errores[campo]

    def test_cambia_el_horario_y_guarda_el_historial(self):
        self.reprogramar(observacion='  el camión volvió tarde  ')
        self.p.refresh_from_db()
        self.assertEqual((self.p.fecha_servicio, self.p.hora_servicio), (self.dia(2), time(10, 0)))
        r = self.p.reprogramaciones.get()
        self.assertEqual((r.fecha_anterior, r.hora_anterior, r.fecha_nueva, r.hora_nueva),
                         (self.dia(), time(9, 0), self.dia(2), time(10, 0)))
        self.assertEqual((r.vehiculo_anterior_id, r.vehiculo_nuevo_id, r.usuario), ('AD-321-JK', 'AD-321-JK', self.admin))
        self.assertEqual(r.motivo_completo, 'Demora en una mudanza anterior (el camión volvió tarde)')
        self.assertFalse(r.visto_cliente)

    def test_motivo_de_la_lista_y_otro_con_observacion(self):
        self.assertRechaza('motivo', motivo='Porque sí')
        self.assertRechaza('observacion', motivo='Otro', observacion='x')
        r = self.reprogramar(motivo='Otro', observacion='Corte de calle por un desfile').reprogramaciones.get()
        self.assertEqual(r.motivo_completo, 'Corte de calle por un desfile')

    def test_fecha_pasada_o_mismo_horario(self):
        self.assertRechaza('fecha_servicio', fecha=self.dia(-1))
        self.assertRechaza('__all__', fecha=self.dia(), hora=time(9, 0))

    def test_el_vehiculo_tiene_que_estar_libre(self):
        self.registrar(patente='AD-321-JK', fecha_servicio=self.dia(2), hora_servicio=time(8, 0))  # 8 a 18
        mensaje = self.assertRechaza('vehiculo')
        self.assertIn('AD-321-JK no está libre', mensaje)
        self.reprogramar(patente='AE-123-CD', motivo='Problema técnico del vehículo')  # con otro vehículo sí
        self.p.refresh_from_db()
        self.assertEqual(self.p.patente_vehiculo_id, 'AE-123-CD')
        self.assertEqual(self.p.reprogramaciones.get().vehiculo_anterior_id, 'AD-321-JK')

    def test_solo_cambiar_el_vehiculo(self):
        self.reprogramar(fecha=self.dia(), hora=time(9, 0), patente='AE-123-CD', motivo='Problema técnico del vehículo')
        self.assertEqual(Pedido.objects.get(pk=self.p.pk).patente_vehiculo_id, 'AE-123-CD')

    def test_personal_ocupado_avisa_o_se_saca(self):
        reglas.asignar_personal(self.p.pk, self.chofer.pk, [self.ayudante.pk])
        reglas.confirmar(self.p.pk)
        otra = self.registrar(patente='AE-123-CD', fecha_servicio=self.dia(2), hora_servicio=time(8, 0))
        reglas.asignar_personal(otra.pk, self.chofer.pk)                 # Luciana ya trabaja ese día de 8 a 18
        mensaje = self.assertRechaza('quitar_ocupados')
        self.assertIn('Luciana Fernandez', mensaje)
        self.assertNotIn('Lucas', mensaje)
        self.reprogramar(quitar_ocupados=True)
        self.assertEqual([x.idUsuario for x in self.p.personal.all()], [self.ayudante])
        self.assertTrue(Pedido.objects.filter(reglas.filtro_sin_chofer(), pk=self.p.pk).exists())  # aviso «Sin chofer»

    def test_no_se_reprograma_un_anulado(self):
        reglas.anular(self.p.pk, self.admin, 'El cliente canceló')
        with self.assertRaises(reglas.ErrorPedido):
            self.reprogramar()

    def test_un_vencido_reprogramado_se_puede_confirmar(self):
        Pedido.objects.filter(pk=self.p.pk).update(fecha_servicio=self.dia(-1))
        self.assertTrue(Pedido.objects.get(pk=self.p.pk).vencido)
        self.reprogramar(motivo='Pedido del cliente')
        self.assertEqual(self.confirmar(self.p).estado, Pedido.CONFIRMADO)

    def test_telefono_whatsapp(self):
        for entrada, salida in [('3874112233', '5493874112233'), ('0387 411-2233', '5493874112233'),
                                ('+54 9 387 411 2233', '5493874112233'), ('', ''), (None, ''), ('123', '')]:
            self.assertEqual(reglas.telefono_whatsapp(entrada), salida, entrada)

    def test_mensaje_para_el_cliente(self):
        self.reprogramar(patente='AE-123-CD')
        texto = reglas.mensaje_reprogramacion(self.p.reprogramaciones.get())
        dias = ['lunes', 'martes', 'miércoles', 'jueves', 'viernes', 'sábado', 'domingo']
        self.assertTrue(texto.startswith('Hola María, te escribimos de Mudanzas y Fletes Salta.'))
        self.assertIn(f'era el {dias[self.dia().weekday()]} {self.dia():%d/%m} a las 09:00', texto)
        self.assertIn(f'ahora es el {dias[self.dia(2).weekday()]} {self.dia(2):%d/%m} a las 10:00', texto)
        self.assertIn('Motivo: demora en una mudanza anterior.', texto)
        self.assertIn('Va el vehículo AE-123-CD.', texto)


class ReprogramarPantallasTest(BaseReglas):
    def setUp(self):
        self.p = self.registrar(id_servicio=self.flete.id_servicio)

    def entrar(self, dni):
        s = self.client.session
        s['usuario_dni'], s['usuario_rol'] = dni, Usuario.objects.get(DNI=dni).idRol.nom_rol
        s.save()

    def test_el_admin_reprograma_y_ve_el_historial_con_whatsapp(self):
        self.entrar(ADMIN)
        self.assertContains(self.client.get(f'/pedidos/{self.p.pk}/'), f'/pedidos/{self.p.pk}/reprogramar/')
        r = self.client.get(f'/pedidos/{self.p.pk}/reprogramar/?motivo={DEMORA}')
        self.assertEqual(r.context['form']['motivo'].value(), DEMORA)
        r = self.client.post(f'/pedidos/{self.p.pk}/reprogramar/', {
            'fecha_servicio': self.dia(3).isoformat(), 'hora_servicio': '16:00', 'vehiculo': 'AD-321-JK',
            'motivo': 'Clima', 'observacion': ''})
        self.assertRedirects(r, f'/pedidos/{self.p.pk}/', fetch_redirect_response=False)
        r = self.client.get(f'/pedidos/{self.p.pk}/')
        self.assertContains(r, 'Cambios de horario')
        self.assertContains(r, 'https://wa.me/5493874112233?text=Hola%20Mar%C3%ADa')
        self.assertContains(r, 'el cliente todavía no lo vio')
        self.assertFalse(Reprogramacion.objects.get().visto_cliente)  # que lo abra el admin no cuenta

    def test_error_vuelve_al_formulario(self):
        self.entrar(ADMIN)
        r = self.client.post(f'/pedidos/{self.p.pk}/reprogramar/', {
            'fecha_servicio': self.dia(3).isoformat(), 'hora_servicio': '16:00', 'vehiculo': 'AD-321-JK',
            'motivo': 'Otro', 'observacion': ''})
        self.assertEqual(r.status_code, 200)
        self.assertIn('observacion', r.context['form'].errors)

    def test_el_cliente_ve_el_cambio_una_vez_como_nuevo(self):
        reglas.reprogramar(self.p.pk, self.admin, self.dia(3), time(16, 0), 'AD-321-JK', 'Clima')
        self.entrar(CLIENTE)
        self.assertContains(self.client.get('/pedidos/'), 'Cambió el horario')
        r = self.client.get(f'/pedidos/{self.p.pk}/')
        self.assertContains(r, 'Tu mudanza cambió de horario.')
        self.assertContains(r, '>Nuevo</span>')
        self.assertNotContains(r, 'wa.me')  # el botón de WhatsApp es para la empresa
        self.assertTrue(Reprogramacion.objects.get().visto_cliente)
        self.assertNotContains(self.client.get('/pedidos/'), 'Cambió el horario')
        r = self.client.get(f'/pedidos/{self.p.pk}/')
        self.assertContains(r, 'Tu mudanza cambió de horario.')  # el aviso sigue, sin «Nuevo»
        self.assertNotContains(r, '>Nuevo</span>')

    def test_el_cliente_no_puede_reprogramar(self):
        self.entrar(CLIENTE)
        self.assertEqual(self.client.get(f'/pedidos/{self.p.pk}/reprogramar/').status_code, 403)


class ReprogramarConChoferTest(ReprogramarTest):
    """Al reprogramar se puede poner otro chofer (idea del proyecto de José)."""

    def test_cambia_el_chofer_ocupado_por_uno_libre(self):
        from usuarios.models import Rol
        from usuarios.utils import hash_password
        otro = Usuario.objects.create(
            DNI=30111222, Nombre='Pablo', Apellido='Ruiz', Correo='pablo.ruiz@ejemplo.com', NombreUsuario='ruizp',
            Clave=hash_password('Usuario123!'), idRol=Rol.objects.get(nom_rol='Chofer'))
        reglas.asignar_personal(self.p.pk, self.chofer.pk, [self.ayudante.pk])
        ocupa = self.registrar(patente='AE-123-CD', fecha_servicio=self.dia(2), hora_servicio=time(8, 0))
        reglas.asignar_personal(ocupa.pk, self.chofer.pk)              # Luciana ocupada en el horario nuevo
        with self.assertRaises(reglas.ErrorPedido) as ctx:
            self.reprogramar(id_chofer=self.chofer.pk)                   # ella no sirve
        self.assertIn('chofer', ctx.exception.errores)
        self.reprogramar(id_chofer=otro.pk)                              # Pablo sí, sin marcar «sacarlo»
        self.assertEqual(self.p.chofer, otro)
        self.assertEqual([x.idUsuario for x in self.p.personal.filter(Funcion='Ayudante')], [self.ayudante])

    def test_el_precio_no_cambia_aunque_vaya_un_camion_mas_grande(self):
        total = self.p.total
        self.reprogramar(patente='AE-123-CD', motivo='Problema técnico del vehículo')
        self.p.refresh_from_db()
        self.assertEqual(self.p.total, total)
