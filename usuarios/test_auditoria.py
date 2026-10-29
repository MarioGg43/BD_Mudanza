"""Log de auditoría (Hito 4): toda modificación o anulación deja valores anteriores, actuales,
fecha y hora y usuario."""
import io
import json
from datetime import time, timedelta

from django.core.management import call_command
from django.test import TestCase
from django.utils import timezone

from pedidos import reglas
from usuarios.auditoria import con_usuario
from usuarios.models import LogAuditoria, Objeto, Pedido, Usuario, Vehiculo

ADMIN, CLIENTE = 35123456, 29876543


class AuditoriaTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command('init_data', stdout=io.StringIO())
        cls.admin = Usuario.objects.get(DNI=ADMIN)
        cls.cliente = Usuario.objects.get(DNI=CLIENTE)

    def entrar(self, dni):
        s = self.client.session
        s['usuario_dni'], s['usuario_rol'] = dni, Usuario.objects.get(DNI=dni).idRol.nom_rol
        s.save()

    def pedido(self):
        return reglas.registrar_pedido(
            self.cliente, timezone.localdate() + timedelta(days=1), time(9, 0), 'A 1, Salta', 'B 2, Salta',
            reglas.Servicio.objects.get(Tipo_servicio='Flete urbano').pk, 'AD-321-JK',
            [{'objeto': Objeto.objects.get(nom_objeto='Cajas'), 'cantidad': 2}])

    def ultimo(self):
        return LogAuditoria.objects.first()

    def test_una_modificacion_guarda_antes_despues_y_usuario(self):
        v = Vehiculo.objects.get(patente='AD-321-JK')
        with con_usuario(self.admin):
            v.marca_modelo = 'Renault Master 2.3'
            v.save()
        log = self.ultimo()
        self.assertEqual((log.tabla, log.id_registro, log.accion, log.usuario), ('VEHICULOS', 'AD-321-JK', 'Modificación', self.admin))
        self.assertEqual(json.loads(log.valores_anteriores), {'marca_modelo': 'Renault Master Furgón'})
        self.assertEqual(json.loads(log.valores_nuevos), {'marca_modelo': 'Renault Master 2.3'})
        self.assertLess(timezone.now() - log.fecha_hora, timedelta(minutes=1))

    def test_las_altas_y_los_guardados_sin_cambios_no_se_registran(self):
        antes = LogAuditoria.objects.count()
        p = self.pedido()
        p.save()
        self.assertEqual(LogAuditoria.objects.count(), antes)

    def test_anular_un_pedido_por_la_pantalla(self):
        p = self.pedido()
        self.entrar(ADMIN)
        self.client.post(f'/pedidos/{p.pk}/anular/', {'motivo': 'El cliente canceló'})
        log = LogAuditoria.objects.get(tabla='PEDIDOS', accion='Anulación')
        self.assertEqual((log.id_registro, log.usuario), (str(p.pk), self.admin))  # el usuario logueado
        self.assertEqual(json.loads(log.valores_anteriores)['estado'], 'Pendiente')
        nuevos = json.loads(log.valores_nuevos)
        self.assertEqual((nuevos['estado'], nuevos['motivo_anulacion']), ('Anulado', 'El cliente canceló'))

    def test_baja_y_reactivacion(self):
        o = Objeto.objects.get(nom_objeto='Plantas')
        with con_usuario(self.admin):
            o.Activo = False
            o.save()
            o.Activo = True
            o.save()
        self.assertEqual([l.accion for l in LogAuditoria.objects.filter(tabla='OBJETOS')], ['Reactivación', 'Baja'])

    def test_reasignar_personal_registra_lo_que_se_saca(self):
        p = self.pedido()
        chofer = Usuario.objects.get(DNI=40987654)
        reglas.asignar_personal(p.pk, chofer.pk)
        reglas.asignar_personal(p.pk, chofer.pk)  # reemplaza: borra la fila anterior
        log = LogAuditoria.objects.get(tabla='PERSONAL_PEDIDO')
        self.assertEqual(log.accion, 'Eliminación')
        self.assertEqual(json.loads(log.valores_anteriores)['Funcion'], 'Chofer')

    def test_la_clave_no_se_guarda_y_el_ultimo_acceso_no_cuenta(self):
        u = Usuario.objects.get(DNI=40987654)
        u.FechaUltimoAcceso = timezone.now()
        u.save()
        self.assertFalse(LogAuditoria.objects.filter(tabla='USUARIOS').exists())
        u.set_clave('OtraClave123!')
        u.save()
        log = LogAuditoria.objects.get(tabla='USUARIOS')
        self.assertEqual(json.loads(log.valores_anteriores), {'Clave': '(oculta)'})

    def test_pantalla_con_filtros_y_permisos(self):
        p = self.pedido()
        with con_usuario(self.admin):
            reglas.anular(p.pk, self.admin, 'Prueba de auditoría')
        self.entrar(ADMIN)
        r = self.client.get('/auditoria/', {'tabla': 'PEDIDOS', 'accion': 'Anulación'})
        self.assertContains(r, 'Prueba de auditoría')
        self.assertContains(r, 'Sarmiento, Carlos')
        self.assertEqual(r.context['pagina'].paginator.count, 1)
        self.assertEqual(self.client.get('/auditoria/', {'tabla': 'VEHICULOS'}).context['pagina'].paginator.count, 0)
        self.entrar(CLIENTE)
        self.assertEqual(self.client.get('/auditoria/').status_code, 403)


class AuditoriaLegibleTest(AuditoriaTest):
    def test_fechas_en_hora_local_y_usuarios_por_nombre(self):
        p = self.pedido()
        with con_usuario(self.admin):
            reglas.anular(p.pk, self.admin, 'Prueba de formato')
        self.entrar(ADMIN)
        r = self.client.get('/auditoria/', {'accion': 'Anulación'})
        log = r.context['pagina'][0]
        cambios = dict((c, (a, d)) for c, a, d in log.cambios)
        self.assertEqual(cambios['Anulado por'], ('—', 'Carlos Sarmiento'))
        self.assertEqual(cambios['Fecha de anulación'][1], timezone.localtime(Pedido.objects.get(pk=p.pk).fecha_anulacion)
                         .strftime('%d/%m/%Y %H:%M'))
        self.assertEqual(cambios['Estado'], ('Pendiente', 'Anulado'))
        self.assertEqual((log.frase, log.detalle), (f'Carlos Sarmiento anuló el pedido N° {p.pk}', 'Prueba de formato'))
        self.assertEqual(log.link, f'/pedidos/{p.pk}/')
        self.assertContains(r, f'Carlos Sarmiento anuló el pedido N° {p.pk}')

    def test_frases_y_plata(self):
        from usuarios.models import Servicio
        s = Servicio.objects.get(Tipo_servicio='Ayudante extra')
        with con_usuario(self.admin):
            s.Precio_base = 22500
            s.save()
            p = self.pedido()
            reglas.asignar_personal(p.pk, Usuario.objects.get(DNI=40987654).pk)
            reglas.confirmar(p.pk)
            reglas.reprogramar(p.pk, self.admin, p.fecha_servicio, time(11, 0), 'AD-321-JK', 'Clima')
        self.entrar(ADMIN)
        logs = list(self.client.get('/auditoria/').context['pagina'])
        frases = {l.frase: l.cambios for l in logs}
        # aunque cambie un solo dato, va en las columnas Antes / Después
        self.assertEqual(frases[f'Carlos Sarmiento reprogramó el pedido N° {p.pk}'], [('Hora de inicio', '09:00', '11:00')])
        self.assertEqual(frases[f'Carlos Sarmiento confirmó el pedido N° {p.pk}'], [('Estado', 'Pendiente', 'Confirmado')])
        self.assertEqual(frases['Carlos Sarmiento modificó el servicio «Ayudante extra»'], [('Precio', '$20.000', '$22.500')])
        self.assertTrue(all(l.detalle == '' for l in logs))  # el texto de abajo de la frase es solo para el motivo

    def test_sin_permiso_muestra_una_pantalla_y_no_texto_suelto(self):
        self.entrar(CLIENTE)
        r = self.client.get('/auditoria/')
        self.assertEqual(r.status_code, 403)
        self.assertContains(r, 'No tenés permiso para esta operación', status_code=403)
        self.assertContains(r, 'Volver', status_code=403)


class AuditoriaPdfTest(AuditoriaTest):
    def test_descarga_el_pdf_con_los_filtros(self):
        p = self.pedido()
        with con_usuario(self.admin):
            reglas.anular(p.pk, self.admin, 'Prueba del PDF')
        self.entrar(ADMIN)
        self.assertContains(self.client.get('/auditoria/?accion=Anulación'), '/auditoria/descargar/?accion=')
        r = self.client.get('/auditoria/descargar/', {'accion': 'Anulación'})
        self.assertEqual((r.status_code, r['Content-Type']), (200, 'application/pdf'))
        self.assertTrue(r.content.startswith(b'%PDF'))
        self.entrar(CLIENTE)
        self.assertEqual(self.client.get('/auditoria/descargar/').status_code, 403)
