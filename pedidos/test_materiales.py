"""Control de materiales: el stock sale con «Empezamos», vuelve o se descuenta con «Terminamos»,
se corrige con ingresos y ajustes, y avisa cuando queda por debajo del mínimo (regla 5)."""
from datetime import datetime, time
from unittest import mock

from django.core import mail
from django.test import override_settings
from django.utils import timezone

from notificaciones import reglas as alertas
from pedidos import materiales, reglas
from pedidos.test_reglas import ADMIN, BaseReglas
from usuarios.models import Configuracion, Material, MovimientoMaterial as Mov, Notificacion, Pedido, Usuario

CHOFER = 40987654


def stock(nombre):
    return Material.objects.get(nom_material=nombre).stock_material


@override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
class MaterialesTest(BaseReglas):
    def setUp(self):
        self.chofer = Usuario.objects.get(DNI=CHOFER)
        # flete urbano: 6 correas y 6 mantas (las dos reutilizables) + embalaje: 20 cajas, 2 papel burbuja, 3 cintas
        self.p = self.registrar(id_servicio=self.flete.id_servicio, ids_adicionales=[self.embalaje.id_servicio])
        reglas.asignar_personal(self.p.pk, self.chofer.pk)
        reglas.confirmar(self.p.pk)

    def a_las(self, hora, minuto=0):
        momento = timezone.make_aware(datetime.combine(self.dia(), time(hora, minuto)))
        return mock.patch('django.utils.timezone.now', return_value=momento)

    def entrar(self, dni):
        s = self.client.session
        s['usuario_dni'], s['usuario_rol'] = dni, Usuario.objects.get(DNI=dni).idRol.nom_rol
        s.save()

    def empezar(self):
        with self.a_las(9):
            return reglas.marcar_inicio(self.p.pk, self.chofer)

    # ------------------------------------------------------------------ reglas
    def test_los_servicios_sugieren_cuanto_llevar(self):
        sugeridos = {m.nom_material: c for m, c in materiales.sugeridos(self.p).items()}
        self.assertEqual(sugeridos, {'Correas': 6, 'Mantas acolchadas': 6, 'Cajas de cartón': 20,
                                     'Papel burbuja': 2, 'Cinta de embalar': 3})

    def test_empezamos_saca_del_stock(self):
        antes = stock('Cajas de cartón'), stock('Mantas acolchadas')
        pedido = self.empezar()
        self.assertEqual(pedido.faltantes, [])
        self.assertEqual((stock('Cajas de cartón'), stock('Mantas acolchadas')), (antes[0] - 20, antes[1] - 6))
        self.assertEqual(Mov.objects.filter(idPedido=self.p, tipo_mov=Mov.SALIDA).count(), 5)
        self.assertEqual(materiales.en_uso()[Material.objects.get(nom_material='Mantas acolchadas').pk], 6)
        with self.a_las(9, 30):  # no sale dos veces aunque se llame de nuevo
            self.assertEqual(materiales.registrar_salida(self.p, self.chofer), [])

    def test_si_no_alcanza_sale_lo_que_hay_y_se_avisa(self):
        Material.objects.filter(nom_material='Correas').update(stock_material=4)
        pedido = self.empezar()
        self.assertEqual([(m.nom_material, s, l) for m, s, l in pedido.faltantes], [('Correas', 6, 4)])
        self.assertEqual(stock('Correas'), 0)
        self.assertEqual(Mov.objects.get(idPedido=self.p, idMaterial__nom_material='Correas').observacion_mov, 'Faltaron 2')

    def test_terminamos_devuelve_y_descuenta_lo_usado(self):
        self.empezar()
        mantas, cajas = Material.objects.get(nom_material='Mantas acolchadas'), Material.objects.get(nom_material='Cajas de cartón')
        antes = stock('Mantas acolchadas'), stock('Cajas de cartón')
        with self.a_las(13):
            reglas.marcar_fin(self.p.pk, self.chofer, {mantas.pk: 5, cajas.pk: 12})  # volvieron 5 mantas, se usaron 12 cajas
        self.assertEqual(stock('Mantas acolchadas'), antes[0] + 5)
        self.assertEqual(stock('Cajas de cartón'), antes[1] + 8)                     # sobraron 8
        self.assertEqual(Mov.objects.get(idPedido=self.p, tipo_mov=Mov.PERDIDA).cant_mov, 1)
        self.assertEqual(Mov.objects.get(idPedido=self.p, tipo_mov=Mov.CONSUMO, idMaterial=cajas).cant_mov, 12)
        self.assertEqual(materiales.en_uso(), {})

    def test_terminamos_no_acepta_mas_de_lo_que_salio(self):
        self.empezar()
        cajas = Material.objects.get(nom_material='Cajas de cartón')
        with self.a_las(13), self.assertRaises(reglas.ErrorPedido) as ctx:
            reglas.marcar_fin(self.p.pk, self.chofer, {cajas.pk: 21})
        self.assertIn('de 0 a 20', str(ctx.exception))
        self.p.refresh_from_db()
        self.assertEqual(self.p.estado, Pedido.CONFIRMADO)  # no se cerró nada

    def test_si_se_anula_en_curso_vuelve_todo(self):
        antes = stock('Cajas de cartón')
        self.empezar()
        reglas.anular(self.p.pk, Usuario.objects.get(DNI=ADMIN), 'El cliente suspendió la mudanza')
        self.assertEqual(stock('Cajas de cartón'), antes)
        self.assertEqual(Mov.objects.filter(idPedido=self.p, tipo_mov=Mov.DEVOLUCION).count(), 5)

    def test_ingreso_y_ajuste(self):
        film = Material.objects.get(nom_material='Film stretch')
        materiales.registrar_ingreso(film, 10, None)
        self.assertEqual(stock('Film stretch'), 50)
        with self.assertRaises(materiales.ErrorMaterial):
            materiales.registrar_ajuste(film, -3, None, 'mal')            # motivo muy corto
        with self.assertRaises(materiales.ErrorMaterial):
            materiales.registrar_ajuste(film, -51, None, 'Conteo del viernes')  # quedaría negativo
        materiales.registrar_ajuste(film, -3, None, 'Conteo del viernes')
        self.assertEqual(stock('Film stretch'), 47)

    # ------------------------------------------------------------------ regla 5
    def test_avisa_una_vez_cuando_baja_del_minimo_y_otra_despues_de_reponer(self):
        Configuracion.objects.update_or_create(clave='correo_empresa', defaults={'valor': 'empresa@ejemplo.com'})
        zunchos = Material.objects.get(nom_material='Zunchos')  # 15, mínimo 5
        with self.captureOnCommitCallbacks(execute=True):
            materiales.registrar_ajuste(zunchos, -11, None, 'Se mojaron en el depósito')
        self.assertEqual(Notificacion.objects.filter(tipo=alertas.STOCK_BAJO).count(), 1)
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn('Zunchos', mail.outbox[0].subject)
        materiales.registrar_ajuste(zunchos, -1, None, 'Otro rollo roto')  # sigue bajo: no repite
        self.assertEqual(Notificacion.objects.filter(tipo=alertas.STOCK_BAJO).count(), 1)
        materiales.registrar_ingreso(zunchos, 1, None)                     # repone poco: sigue bajo
        materiales.registrar_ajuste(zunchos, -1, None, 'Conteo de fin de mes')
        self.assertEqual(Notificacion.objects.filter(tipo=alertas.STOCK_BAJO).count(), 2)

    # ------------------------------------------------------------------ pantallas
    def test_pantalla_de_materiales_solo_con_permiso(self):
        self.entrar(CHOFER)
        self.assertNotEqual(self.client.get('/materiales/').status_code, 200)
        self.entrar(ADMIN)
        r = self.client.get('/materiales/')
        self.assertContains(r, 'Mantas acolchadas')
        self.assertContains(r, 'Bajo el mínimo')

    def test_alta_con_stock_inicial_y_carga_de_ingreso(self):
        self.entrar(ADMIN)
        r = self.client.post('/materiales/nuevo/', {'nom_material': 'esquineros', 'unidad_material': 'Unidades',
                                                    'stock_min_material': '10', 'stock_inicial': '40', 'Activo': 'on'})
        m = Material.objects.get(nom_material='Esquineros')
        self.assertRedirects(r, f'/materiales/{m.pk}/')
        self.assertEqual((m.stock_material, m.unidad_material, m.reutilizable), (40, 'unidades', False))
        self.assertEqual(m.movimientos.get().observacion_mov, 'Stock inicial')
        r = self.client.post(f'/materiales/{m.pk}/', {'tipo': 'Ingreso', 'cantidad': '15', 'observacion': 'Compra'})
        self.assertRedirects(r, f'/materiales/{m.pk}/')
        r = self.client.post(f'/materiales/{m.pk}/', {'tipo': 'Ajuste', 'cantidad': '-2', 'observacion': ''})
        self.assertContains(r, 'Contá el motivo')
        self.assertEqual(stock('Esquineros'), 55)
        r = self.client.post('/materiales/nuevo/', {'nom_material': 'ESQUINEROS', 'unidad_material': 'u',
                                                    'stock_min_material': '0'})
        self.assertContains(r, 'Ya hay un material con ese nombre')

    def test_el_chofer_ve_los_materiales_y_termina_con_el_formulario(self):
        self.entrar(CHOFER)
        with self.a_las(9):
            r = self.client.get('/portal/')
            self.assertContains(r, 'Cajas de cartón <b>×20</b>')
            self.client.post(f'/pedidos/{self.p.pk}/empezar/')
            correas = Material.objects.get(nom_material='Correas')
            r = self.client.get(f'/pedidos/{self.p.pk}/terminar/')
            self.assertContains(r, 'Volvieron')
            self.assertContains(r, 'Se usaron')
            datos = {f'mat_{m.pk}': c for m, c in materiales.enviados(self.p).items()}
            datos[f'mat_{correas.pk}'] = '4'
            r = self.client.post(f'/pedidos/{self.p.pk}/terminar/', datos, follow=True)
        self.assertContains(r, 'no volvieron: 2 correas')
        self.p.refresh_from_db()
        self.assertEqual(self.p.estado, Pedido.FINALIZADO)
        self.entrar(ADMIN)
        r = self.client.get(f'/pedidos/{self.p.pk}/')
        self.assertContains(r, 'No volvió de la mudanza')

    def test_servicio_por_api_con_texto(self):
        from pedidos.forms import leer_materiales_texto
        self.assertEqual([(m.nom_material, c) for m, c in leer_materiales_texto('mantas ×3, papel')],
                         [('Mantas acolchadas', 3), ('Papel burbuja', 1)])


class PrepararDemoTest(BaseReglas):
    def test_deja_una_mudanza_lista_y_el_papel_al_borde_del_minimo(self):
        import io
        from django.core.management import call_command
        dia = self.dia()
        manana = timezone.make_aware(datetime.combine(dia, time(8, 0)))
        with mock.patch('django.utils.timezone.now', return_value=manana):
            salida = io.StringIO()
            call_command('preparar_demo_materiales', stdout=salida)
            p = Pedido.objects.latest('pk')
            self.assertEqual((p.estado, p.hora_servicio, p.fecha_servicio), (Pedido.CONFIRMADO, time(9, 0), dia))
            self.assertIn('Empezamos', salida.getvalue())
            papel = Material.objects.get(nom_material='Papel burbuja')
            self.assertEqual(papel.stock_material, papel.stock_min_material + 1)
            reglas.marcar_inicio(p.pk, Usuario.objects.get(DNI=CHOFER))
        self.assertTrue(Notificacion.objects.filter(tipo=alertas.STOCK_BAJO, mensaje__contains='Papel burbuja').exists())
