"""Pruebas de los reportes consolidados (Parcial N° 2, M2)."""
import io
from datetime import date, datetime, time, timedelta
from decimal import Decimal

from django.core.management import call_command
from django.test import TestCase
from django.utils import timezone

from pedidos import reglas
from reportes import consultas
from usuarios.models import (Objeto, Pedido, PermisoRol, Reprogramacion, Rol, Servicio, Usuario, Vehiculo)

ADMIN, CHOFER, CLIENTE = 35123456, 40987654, 29876543


class BaseReportes(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command('init_data', stdout=io.StringIO())
        cls.cliente = Usuario.objects.get(DNI=CLIENTE)
        cls.chofer = Usuario.objects.get(DNI=CHOFER)
        cls.admin = Usuario.objects.get(DNI=ADMIN)
        cls.local = Servicio.objects.get(Tipo_servicio='Mudanza local')
        # una mudanza hecha (30 min tarde, 2 h más larga) y una anulada, en el pasado
        cls.hecha = cls._pedido(dias=-10, chofer=cls.chofer)
        inicio = cls.hecha.inicio
        Pedido.objects.filter(pk=cls.hecha.pk).update(
            estado=Pedido.FINALIZADO, inicio_real=inicio + timedelta(minutes=30),
            fin_real=inicio + timedelta(minutes=30, hours=cls.hecha.duracion_horas + 2), recargo=Decimal('15000'))
        cls.anulada = cls._pedido(dias=-5)
        Pedido.objects.filter(pk=cls.anulada.pk).update(
            estado=Pedido.ANULADO, fecha_anulacion=timezone.now() - timedelta(days=6), motivo_anulacion='Duplicado',
            usuario_anulacion=cls.cliente)
        Reprogramacion.objects.create(
            idPedido=cls.hecha, fecha_anterior=cls.hecha.fecha_servicio - timedelta(days=2), hora_anterior=time(9),
            vehiculo_anterior=cls.hecha.patente_vehiculo, fecha_nueva=cls.hecha.fecha_servicio, hora_nueva=time(9),
            vehiculo_nuevo=cls.hecha.patente_vehiculo, motivo='Clima', usuario=cls.admin,
            fecha_registro=timezone.now() - timedelta(days=12))

    @classmethod
    def _pedido(cls, dias, chofer=None):
        # se registra para dentro de unos días y se lleva al pasado (registrar no deja fechas pasadas)
        p = reglas.registrar_pedido(
            cls.cliente, timezone.localdate() + timedelta(days=3), time(9, 0), 'Origen 1', 'Destino 2',
            cls.local.id_servicio, 'AD-321-JK', [{'objeto': Objeto.objects.get(nom_objeto='Cajas'), 'cantidad': 2, 'fragil': False}])
        if chofer:
            reglas.asignar_personal(p.pk, chofer.pk)
        Pedido.objects.filter(pk=p.pk).update(fecha_servicio=timezone.localdate() + timedelta(days=dias))
        p.refresh_from_db()
        return p

    def entrar(self, dni):
        s = self.client.session
        s['usuario_dni'] = dni
        s.save()

    def rango(self):
        hoy = timezone.localdate()
        return hoy - timedelta(days=30), hoy


class ConsultasTest(BaseReportes):
    def test_desempeno_cruza_personal_y_horas_reales(self):
        datos = consultas.desempeno_personal(*self.rango())
        fila = next(f for f in datos['filas'] if f['empleado'].startswith('Fernandez'))
        self.assertEqual(fila['mudanzas'], 1)
        self.assertAlmostEqual(fila['reales'] - fila['estimadas'], 2, places=2)  # duró 2 h más
        self.assertAlmostEqual(fila['demora'], 30)                                # empezó 30 min tarde
        self.assertEqual(fila['tarde'], 1)
        self.assertEqual(datos['totales']['mudanzas'], 1)

    def test_flota_suma_ingresos_y_cuenta_anuladas(self):
        datos = consultas.uso_flota(*self.rango())
        fila = next(f for f in datos['filas'] if f['patente'] == 'AD-321-JK')
        self.assertEqual((fila['hechas'], fila['anuladas']), (1, 1))
        self.assertEqual(fila['ingresos'], Pedido.objects.get(pk=self.hecha.pk).total)
        self.assertEqual(fila['recargos'], Decimal('15000'))
        self.assertEqual(datos['totales']['participacion'], 100.0)
        self.assertEqual(consultas.uso_flota(*self.rango(), tipo=Vehiculo.GRANDE)['filas'], [])

    def test_cambios_junta_reprogramaciones_y_anulaciones(self):
        datos = consultas.cambios_y_cancelaciones(*self.rango())
        self.assertEqual(sorted(e['tipo'] for e in datos['filas']), ['Anulación', 'Reprogramación'])
        self.assertEqual(next(e for e in datos['filas'] if e['tipo'] == 'Anulación')['quien'], 'el cliente')
        self.assertEqual({(r['motivo'], r['cantidad']) for r in datos['resumen']}, {('Clima', 1), ('Duplicado', 1)})
        solo = consultas.cambios_y_cancelaciones(*self.rango(), tipo='Anulación')
        self.assertEqual([e['tipo'] for e in solo['filas']], ['Anulación'])

    def test_fuera_del_rango_no_cuenta(self):
        hoy = timezone.localdate()
        self.assertEqual(consultas.desempeno_personal(hoy - timedelta(days=3), hoy)['filas'], [])


class PantallasTest(BaseReportes):
    def test_el_administrador_ve_los_tres_y_el_menu(self):
        self.entrar(ADMIN)
        r = self.client.get('/reportes/')
        for clave in ('personal', 'flota', 'cambios'):
            self.assertContains(r, f'href="/reportes/{clave}/"')
        self.assertContains(r, 'href="/reportes/"')  # en el menú

    def test_grilla_con_totales_y_filtros(self):
        self.entrar(ADMIN)
        desde, hasta = self.rango()
        r = self.client.get('/reportes/flota/', {'desde': desde.isoformat(), 'hasta': hasta.isoformat(), 'tipo': ''})
        self.assertContains(r, 'class="fila-total"')
        self.assertContains(r, 'AD-321-JK')
        self.assertContains(r, '$15.000,00')  # recargos, con formato argentino

    def test_sin_fechas_toma_desde_el_1_de_enero(self):
        self.entrar(ADMIN)
        r = self.client.get('/reportes/personal/')
        self.assertEqual(r.context['form'].cleaned_data['desde'], date(timezone.localdate().year, 1, 1))

    def test_hasta_anterior_a_desde(self):
        self.entrar(ADMIN)
        r = self.client.get('/reportes/personal/', {'desde': '2026-05-10', 'hasta': '2026-05-01'})
        self.assertContains(r, 'no puede ser anterior')
        self.assertIsNone(r.context['datos'])

    def test_paginado(self):
        self.entrar(ADMIN)
        r = self.client.get('/reportes/cambios/', {'pagina': 99})
        self.assertEqual(r.context['pagina'].number, 1)  # una página que no existe muestra la última

    def test_el_pdf_lleva_filtros_y_quien_lo_emitio(self):
        self.entrar(ADMIN)
        desde, hasta = self.rango()
        r = self.client.get('/reportes/cambios/pdf/', {'desde': desde.isoformat(), 'hasta': hasta.isoformat(), 'tipo': ''})
        self.assertEqual(r['Content-Type'], 'application/pdf')
        self.assertTrue(r.content.startswith(b'%PDF'))
        self.assertIn('Cambios_y_cancelaciones.pdf', r['Content-Disposition'])

    def test_permisos_por_perfil(self):
        # el cliente y el chofer no ven reportes; sin sesión, al login
        self.assertRedirects(self.client.get('/reportes/'), '/login/')
        for dni in (CLIENTE, CHOFER):
            self.entrar(dni)
            self.assertEqual(self.client.get('/reportes/personal/').status_code, 403)
        # un rol con REP_CONSULTAR pero sin REP_FINANZAS no ve el reporte con montos (el sensible)
        rol = Rol.objects.create(nom_rol='Supervisor', desc_rol='Ve reportes sin montos')
        from usuarios.models import Permiso
        PermisoRol.objects.create(idRol=rol, idPermiso=Permiso.objects.get(nom_permiso='REP_CONSULTAR'))
        Usuario.objects.filter(DNI=CHOFER).update(idRol=rol)
        self.entrar(CHOFER)
        self.assertEqual(self.client.get('/reportes/personal/').status_code, 200)
        self.assertEqual(self.client.get('/reportes/flota/').status_code, 403)
        self.assertEqual(self.client.get('/reportes/flota/pdf/').status_code, 403)
        self.assertNotContains(self.client.get('/reportes/'), 'href="/reportes/flota/"')

    def test_reporte_que_no_existe(self):
        self.entrar(ADMIN)
        self.assertEqual(self.client.get('/reportes/inventado/').status_code, 404)


class DatosDemoTest(TestCase):
    """El comando de datos de prueba carga pedidos del pasado y los borra sin tocar los reales."""

    @classmethod
    def setUpTestData(cls):
        call_command('init_data', stdout=io.StringIO())

    def test_carga_y_borra_solo_los_de_prueba(self):
        reales = Pedido.objects.count()
        call_command('cargar_datos_demo', cantidad=40, stdout=io.StringIO())
        demo = Pedido.objects.filter(idUsuario__Correo__endswith='@demo.mudanzassalta.com.ar')
        self.assertEqual(demo.count(), 40)
        self.assertFalse(demo.filter(fecha_servicio__gte=timezone.localdate()).exists())   # todo del pasado
        self.assertFalse(demo.exclude(estado__in=[Pedido.FINALIZADO, Pedido.ANULADO]).exists())
        from usuarios.models import LogAuditoria
        antes = LogAuditoria.objects.count()
        call_command('cargar_datos_demo', borrar=True, stdout=io.StringIO())
        self.assertEqual(Pedido.objects.count(), reales)
        self.assertEqual(LogAuditoria.objects.count(), antes)  # borrar datos de prueba no ensucia la auditoría


class TableroYMenuLateralTest(BaseReportes):
    def test_el_tablero_del_administrador(self):
        self.entrar(ADMIN)
        r = self.client.get('/tablero/')
        self.assertContains(r, 'Mudanzas del mes')
        self.assertContains(r, 'id="datos-tablero"')                  # los datos de los gráficos
        self.assertContains(r, f'href="/pedidos/{self.hecha.pk}/"', count=0)  # una mudanza pasada no es «próxima»
        datos = r.context['graficos']
        self.assertEqual(len(datos['dias']['etiquetas']), 30 + 7)     # 30 días + los próximos 7
        # la finalizada cuenta como «Finalizadas» en su día, no como «Sin finalizar»
        i = datos['dias']['etiquetas'].index(next(e for e in datos['dias']['etiquetas']
                                                  if e.endswith(self.hecha.fecha_servicio.strftime('%d/%m'))))
        self.assertGreaterEqual(datos['dias']['finalizadas'][i], 1)
        self.assertEqual(len(datos['dias']['sin_finalizar']), 30 + 7)
        self.assertIn('Mudanza local', datos['servicios']['etiquetas'])
        self.assertEqual(len(self.client.get('/tablero/', {'periodo': '7'}).context['graficos']['dias']['etiquetas']), 14)
        self.assertEqual(len(self.client.get('/tablero/', {'periodo': 'raro'}).context['graficos']['dias']['etiquetas']), 37)

    def test_solo_quien_gestiona_pedidos(self):
        for dni in (CLIENTE, CHOFER):
            self.entrar(dni)
            self.assertEqual(self.client.get('/tablero/').status_code, 403)

    def test_menu_lateral_para_el_personal_y_de_arriba_para_el_cliente(self):
        self.entrar(ADMIN)
        r = self.client.get('/pedidos/')
        self.assertContains(r, 'class="lateral"')
        self.assertContains(r, 'body class="con-lateral"')
        self.assertContains(r, 'href="/tablero/"')
        self.entrar(CHOFER)
        r = self.client.get('/portal/')
        self.assertContains(r, 'class="lateral"')
        self.assertNotContains(r, 'href="/tablero/"')                 # el chofer no ve el tablero
        self.assertNotContains(r, 'href="/panel/"')
        self.entrar(CLIENTE)
        r = self.client.get('/pedidos/')
        self.assertNotContains(r, 'class="lateral"')
        self.assertContains(r, 'class="cabecera"')
