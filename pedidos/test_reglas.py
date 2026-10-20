"""Pruebas de las reglas del pedido. Usan los datos de init_data:
Mudanza local $185.000, Flete urbano $75.000; AD-321-JK (1600 kg) y AE-123-CD
(5000 kg) disponibles; AC-789-GH en mantenimiento; AF-456-EF en viaje."""
import io
from datetime import datetime, time, timedelta
from unittest import mock

from django.core.management import call_command
from django.db import IntegrityError
from django.test import TestCase
from django.utils import timezone

from pedidos import reglas
from usuarios.models import DetallePedido, Objeto, Pedido, Servicio, Usuario

CLIENTE, ADMIN = 29876543, 35123456


def obj(nombre):
    return Objeto.objects.get(nom_objeto=nombre)


class BaseReglas(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command('init_data', stdout=io.StringIO())
        cls.cliente = Usuario.objects.get(DNI=CLIENTE)
        cls.admin = Usuario.objects.get(DNI=ADMIN)
        cls.local = Servicio.objects.get(Tipo_servicio='Mudanza local')
        cls.flete = Servicio.objects.get(Tipo_servicio='Flete urbano')
        cls.embalaje = Servicio.objects.get(Tipo_servicio='Embalaje')
        cls.armado = Servicio.objects.get(Tipo_servicio='Desarmado y armado de muebles')

    def dia(self, dias=1):
        return timezone.localdate() + timedelta(days=dias)

    def confirmar(self, pedido):
        """Para confirmar hace falta el chofer: se asigna a Luciana Fernández (la chofer de init_data)."""
        reglas.asignar_personal(pedido.pk, Usuario.objects.get(DNI=40987654).pk)
        return reglas.confirmar(pedido.pk)

    def registrar(self, **cambios):
        datos = dict(
            cliente=self.cliente, fecha_servicio=self.dia(), hora_servicio=time(9, 0),
            origen='Av. Belgrano 100, Salta', destino='Mitre 50, Cerrillos',
            id_servicio=self.local.id_servicio, patente='AD-321-JK',
            items=[{'objeto': obj('Heladera'), 'cantidad': 1, 'fragil': True},
                   {'objeto': obj('Cajas'), 'cantidad': 10, 'fragil': False}])
        datos.update(cambios)
        return reglas.registrar_pedido(**datos)

    def assertRechaza(self, campo, mensaje=None, **cambios):
        antes = Pedido.objects.count()
        with self.assertRaises(reglas.ErrorPedido) as ctx:
            self.registrar(**cambios)
        self.assertIn(campo, ctx.exception.errores)
        if mensaje:
            self.assertEqual(ctx.exception.errores[campo], mensaje)
        self.assertEqual(Pedido.objects.count(), antes)


class RegistrarPedidoTest(BaseReglas):
    def test_registra_el_pedido_completo(self):
        p = self.registrar()
        self.assertEqual(p.estado, Pedido.PENDIENTE)
        self.assertEqual(p.Fecha_pedido, timezone.localdate())
        self.assertEqual(p.idUsuario, self.cliente)
        self.assertEqual(p.hora_servicio, time(9, 0))
        self.assertEqual(sorted((i.idObjeto.nom_objeto, i.Cantidad, i.Fragil) for i in p.inventario.all()),
                         [('Cajas', 10, False), ('Heladera', 1, True)])

    def test_un_solo_detalle_y_el_total_es_el_precio_del_servicio(self):
        p = self.registrar(id_servicio=self.flete.id_servicio)
        detalle = p.detalles.get()
        self.assertEqual((detalle.idServicio, detalle.precio_unitario, detalle.subtotal),
                         (self.flete, 75000, 75000))
        self.assertEqual(p.total, self.flete.Precio_base)

    def test_los_adicionales_se_anotan_sin_precio(self):
        p = self.registrar(id_servicio=self.flete.id_servicio,
                           ids_adicionales=[self.armado.id_servicio, self.embalaje.id_servicio])
        self.assertEqual([(d.idServicio, d.precio_unitario, d.subtotal) for d in p.detalles.all()],
                         [(self.flete, 75000, 75000), (self.armado, 0, 0), (self.embalaje, 0, 0)])
        self.assertEqual(p.total, 75000)

    def test_un_adicional_con_precio_cargado_igual_va_sin_precio(self):
        Servicio.objects.filter(pk=self.embalaje.pk).update(Precio_base=40000)
        p = self.registrar(ids_adicionales=[self.embalaje.id_servicio])
        self.assertEqual(p.total, 185000)

    def test_un_adicional_repetido_cuenta_una_vez(self):
        p = self.registrar(ids_adicionales=[self.embalaje.id_servicio, self.embalaje.id_servicio])
        self.assertEqual(p.detalles.count(), 2)

    def test_un_adicional_no_puede_ser_el_principal(self):
        self.assertRechaza('servicio', 'Ese servicio ya no está disponible.', id_servicio=self.embalaje.id_servicio)

    def test_un_principal_no_puede_ir_como_adicional(self):
        self.assertRechaza('adicionales', ids_adicionales=[self.flete.id_servicio])

    def test_adicional_dado_de_baja(self):
        Servicio.objects.filter(pk=self.embalaje.pk).update(Activo=False)
        self.assertRechaza('adicionales', 'Alguno de los adicionales elegidos ya no está disponible.',
                           ids_adicionales=[self.embalaje.id_servicio])

    def test_el_precio_queda_fijo_en_el_pedido(self):
        p = self.registrar()
        Servicio.objects.filter(pk=self.local.pk).update(Precio_base=999999)
        self.assertEqual(p.detalles.get(idServicio=self.local).precio_unitario, 185000)

    def test_fecha_pasada(self):
        self.assertRechaza('fecha_servicio', fecha_servicio=self.dia(-1))

    def test_fecha_a_mas_de_un_anio(self):
        self.assertRechaza('fecha_servicio', fecha_servicio=self.dia(366))

    def test_se_puede_para_hoy(self):
        if timezone.localtime().time() >= time(23, 59):
            self.skipTest('A las 23:59 ya no queda hora válida para hoy.')
        p = self.registrar(fecha_servicio=self.dia(0), hora_servicio=time(23, 59))
        self.assertEqual(p.estado, Pedido.PENDIENTE)

    def test_hora_vacia(self):
        self.assertRechaza('hora_servicio', 'Elegí la hora de inicio.', hora_servicio=None)

    def test_cualquier_hora_incluso_de_madrugada(self):
        # el grupo pidió horario libre: en el centro conviene mudarse de madrugada
        self.assertEqual(self.registrar(hora_servicio=time(3, 30)).hora_servicio, time(3, 30))
        p = self.registrar(hora_servicio=time(23, 45), fecha_servicio=self.dia(2))
        self.assertEqual(p.hora_servicio, time(23, 45))

    def test_para_hoy_una_hora_que_ya_paso(self):
        ahora = timezone.localtime()
        if ahora.hour == 0:
            self.skipTest('Recién empezado el día no hay una hora anterior de hoy.')
        hora = (ahora - timedelta(hours=1)).time()
        self.assertRechaza('hora_servicio', 'Para hoy, elegí una hora que todavía no pasó.',
                           fecha_servicio=self.dia(0), hora_servicio=hora)

    def test_para_hoy_con_el_reloj_fijo_a_las_15(self):
        # La misma regla sin depender de la hora en que corre la prueba
        ahora = timezone.make_aware(datetime.combine(timezone.localdate(), time(15, 0)))
        with mock.patch('django.utils.timezone.now', return_value=ahora):
            self.assertRechaza('hora_servicio', 'Para hoy, elegí una hora que todavía no pasó.',
                               fecha_servicio=self.dia(0), hora_servicio=time(15, 0))
            p = self.registrar(fecha_servicio=self.dia(0), hora_servicio=time(15, 15))
        self.assertEqual(p.hora_servicio, time(15, 15))

    def test_origen_vacio(self):
        self.assertRechaza('origen', origen='   ')

    def test_destino_igual_al_origen(self):
        self.assertRechaza('destino', destino='AV. BELGRANO 100, SALTA')

    def test_sin_servicio(self):
        self.assertRechaza('servicio', 'Elegí un servicio.', id_servicio=None)

    def test_servicio_inexistente(self):
        self.assertRechaza('servicio', 'Ese servicio ya no está disponible.', id_servicio=999999)

    def test_servicio_inactivo(self):
        Servicio.objects.filter(pk=self.flete.pk).update(Activo=False)
        self.assertRechaza('servicio', 'Ese servicio ya no está disponible.', id_servicio=self.flete.id_servicio)

    def test_sin_objetos(self):
        self.assertRechaza('inventario', 'Agregá al menos un objeto.', items=[])

    def test_otro_con_observacion(self):
        p = self.registrar(items=[
            {'objeto': obj('Otro'), 'cantidad': 1, 'fragil': True,
             'observacion': ' Piano vertical; se desarma '},
            {'objeto': obj('Cajas'), 'cantidad': 4}])
        self.assertEqual(sorted((i.idObjeto.nom_objeto, i.Observacion) for i in p.inventario.all()),
                         [('Cajas', None), ('Otro', 'Piano vertical; se desarma')])

    def test_otro_sin_observacion(self):
        self.assertRechaza('inventario', 'Objeto 1: si elegís «Otro», contá en la observación qué es.',
                           items=[{'objeto': obj('Otro'), 'cantidad': 1, 'observacion': '  '}])

    def test_objeto_sin_elegir(self):
        self.assertRechaza('inventario', 'Objeto 1: elegí qué es de la lista.',
                           items=[{'objeto': None, 'cantidad': 1}])

    def test_no_se_puede_escribir_un_objeto_que_no_esta_en_la_lista(self):
        self.assertRechaza('inventario', 'Objeto 1: ese objeto ya no está en la lista. Elegí otro.',
                           items=[{'objeto': 'Meza', 'cantidad': 1}])

    def test_objeto_dado_de_baja(self):
        Objeto.objects.filter(nom_objeto='Mesa').update(Activo=False)
        self.assertRechaza('inventario', 'Objeto 1: ese objeto ya no está en la lista. Elegí otro.',
                           items=[{'objeto': obj('Mesa'), 'cantidad': 1}])

    def test_el_mismo_objeto_dos_veces(self):
        self.assertRechaza('inventario', 'Ya agregaste «Mesa»: sumá la cantidad en una sola fila.',
                           items=[{'objeto': obj('Mesa'), 'cantidad': 1}, {'objeto': obj('Mesa'), 'cantidad': 2}])

    def test_otro_puede_repetirse(self):
        p = self.registrar(items=[{'objeto': obj('Otro'), 'cantidad': 1, 'observacion': 'Piano'},
                                  {'objeto': obj('Otro'), 'cantidad': 1, 'observacion': 'Acuario'}])
        self.assertEqual(p.inventario.count(), 2)

    def test_observacion_demasiado_larga(self):
        self.assertRechaza('inventario', 'Objeto 1: la observación puede tener hasta 200 caracteres.',
                           items=[{'objeto': obj('Mesa'), 'cantidad': 1, 'observacion': 'x' * 201}])

    def test_cantidad_fuera_de_rango(self):
        self.assertRechaza('inventario', items=[{'objeto': obj('Sillas'), 'cantidad': 0}])
        self.assertRechaza('inventario', items=[{'objeto': obj('Sillas'), 'cantidad': 1000}])

    def test_el_catalogo_inicial_de_objetos(self):
        self.assertEqual(Objeto.objects.count(), 20)
        self.assertTrue(obj('Otro').es_otro)
        self.assertTrue(Objeto.objects.filter(nom_objeto='Bolsos y valijas', Activo=True).exists())

    def test_sin_vehiculo(self):
        self.assertRechaza('vehiculo', patente='')

    def test_vehiculo_en_mantenimiento(self):
        self.assertRechaza('vehiculo', patente='AC-789-GH')

    def test_vehiculo_ocupado_ese_dia(self):
        self.registrar()
        self.assertRechaza('vehiculo')
        self.assertEqual(self.registrar(fecha_servicio=self.dia(2)).estado, Pedido.PENDIENTE)

    def test_si_falla_a_mitad_de_camino_no_queda_nada(self):
        pedidos, detalles = Pedido.objects.count(), DetallePedido.objects.count()
        with mock.patch('pedidos.reglas.InventarioDetalle.objects.bulk_create',
                        side_effect=IntegrityError('falla simulada')):
            with self.assertRaises(IntegrityError):
                self.registrar()
        self.assertEqual(Pedido.objects.count(), pedidos)
        self.assertEqual(DetallePedido.objects.count(), detalles)


class VehiculosLibresTest(BaseReglas):
    def patentes(self, fecha):
        return set(reglas.vehiculos_libres(fecha).values_list('patente', flat=True))

    def test_solo_los_disponibles(self):
        self.assertEqual(self.patentes(self.dia()), {'AD-321-JK', 'AE-123-CD'})

    def test_un_pedido_activo_ocupa_el_vehiculo_ese_dia(self):
        self.registrar()
        self.assertEqual(self.patentes(self.dia()), {'AE-123-CD'})
        self.assertEqual(self.patentes(self.dia(2)), {'AD-321-JK', 'AE-123-CD'})

    def test_un_pedido_anulado_no_ocupa(self):
        p = self.registrar()
        Pedido.objects.filter(pk=p.pk).update(estado=Pedido.ANULADO)
        self.assertIn('AD-321-JK', self.patentes(self.dia()))


class TransicionesTest(BaseReglas):
    def despues_de(self, pedido, minutos):
        # un reloj fijo a tantos minutos del inicio de la mudanza (negativo = antes)
        inicio = timezone.make_aware(datetime.combine(pedido.fecha_servicio, pedido.hora_servicio))
        return mock.patch('django.utils.timezone.now', return_value=inicio + timedelta(minutes=minutos))

    def test_confirmar_y_finalizar(self):
        p = self.registrar()
        self.assertEqual(self.confirmar(p).estado, Pedido.CONFIRMADO)
        with self.despues_de(p, 60):
            self.assertEqual(reglas.finalizar(p.pk).estado, Pedido.FINALIZADO)
        self.assertEqual(Pedido.objects.get(pk=p.pk).estado, Pedido.FINALIZADO)

    def test_no_se_finaliza_antes_de_que_empiece_la_mudanza(self):
        p = self.registrar(hora_servicio=time(17, 13))
        self.confirmar(p)
        with self.despues_de(p, -1):
            with self.assertRaises(reglas.ErrorPedido) as ctx:
                reglas.finalizar(p.pk)
        fecha = p.fecha_servicio.strftime('%d/%m/%Y')
        self.assertEqual(str(ctx.exception),
                         f'La mudanza todavía no empezó: se puede finalizar desde el {fecha} a las 17:13.')
        self.assertEqual(Pedido.objects.get(pk=p.pk).estado, Pedido.CONFIRMADO)
        with self.despues_de(p, 0):
            self.assertEqual(reglas.finalizar(p.pk).estado, Pedido.FINALIZADO)

    def test_no_se_finaliza_un_pendiente(self):
        p = self.registrar()
        with self.assertRaises(reglas.ErrorPedido):
            reglas.finalizar(p.pk)
        self.assertEqual(Pedido.objects.get(pk=p.pk).estado, Pedido.PENDIENTE)

    def test_no_se_confirma_dos_veces(self):
        p = self.registrar()
        self.confirmar(p)
        with self.assertRaises(reglas.ErrorPedido):
            self.confirmar(p)

    def test_anular_guarda_fecha_motivo_y_usuario_y_libera_el_vehiculo(self):
        p = self.registrar()
        self.confirmar(p)
        reglas.anular(p.pk, self.admin, '  El cliente suspendió la mudanza  ')
        p.refresh_from_db()
        self.assertEqual(p.estado, Pedido.ANULADO)
        self.assertEqual(p.motivo_anulacion, 'El cliente suspendió la mudanza')
        self.assertEqual(p.usuario_anulacion, self.admin)
        self.assertIsNotNone(p.fecha_anulacion)
        self.assertIn('AD-321-JK', reglas.vehiculos_libres(p.fecha_servicio).values_list('patente', flat=True))
        self.assertTrue(Pedido.objects.filter(pk=p.pk).exists())  # no se borra

    def test_motivo_invalido(self):
        p = self.registrar()
        for motivo in ['', 'nop', 'x' * 201]:
            with self.assertRaises(reglas.ErrorPedido) as ctx:
                reglas.anular(p.pk, self.admin, motivo)
            self.assertIn('motivo', ctx.exception.errores)
        self.assertEqual(Pedido.objects.get(pk=p.pk).estado, Pedido.PENDIENTE)

    def test_no_se_anula_un_finalizado_ni_un_anulado(self):
        finalizado = Pedido.objects.get(estado=Pedido.FINALIZADO)  # el de init_data
        with self.assertRaises(reglas.ErrorPedido):
            reglas.anular(finalizado.pk, self.admin, 'Motivo de prueba')
        p = self.registrar()
        reglas.anular(p.pk, self.admin, 'Motivo de prueba')
        with self.assertRaises(reglas.ErrorPedido):
            reglas.anular(p.pk, self.admin, 'Otra vez')


class FiltrarPedidosTest(BaseReglas):
    def setUp(self):
        self.p1 = self.registrar(fecha_servicio=self.dia(1), id_servicio=self.local.id_servicio)
        self.p2 = self.registrar(fecha_servicio=self.dia(5), id_servicio=self.flete.id_servicio)
        self.confirmar(self.p2)
        self.viejo = Pedido.objects.get(estado=Pedido.FINALIZADO)  # 20/09/2026, Mudanza local

    def ids(self, **filtros):
        return [p.pk for p in reglas.filtrar_pedidos(Pedido.objects.all(), **filtros)]

    def test_sin_filtros_del_mas_nuevo_al_mas_viejo(self):
        self.assertEqual(self.ids(), [self.p2.pk, self.p1.pk, self.viejo.pk])

    def test_por_rango_de_fechas_del_servicio(self):
        self.assertEqual(self.ids(desde=self.dia(2)), [self.p2.pk])
        self.assertEqual(self.ids(hasta=self.dia(2)), [self.p1.pk, self.viejo.pk])
        self.assertEqual(self.ids(desde=self.dia(0), hasta=self.dia(2)), [self.p1.pk])

    def test_por_estado(self):
        self.assertEqual(self.ids(estado=Pedido.CONFIRMADO), [self.p2.pk])

    def test_por_servicio(self):
        self.assertEqual(self.ids(id_servicio=self.local.id_servicio), [self.p1.pk, self.viejo.pk])

    def test_por_cliente(self):
        self.assertEqual(self.ids(id_cliente=self.admin.id_usuario), [])
        self.assertEqual(len(self.ids(id_cliente=self.cliente.id_usuario)), 3)

    def test_filtros_combinados(self):
        self.assertEqual(self.ids(estado=Pedido.PENDIENTE, id_servicio=self.local.id_servicio), [self.p1.pk])


class VencidosTest(BaseReglas):
    """Un pendiente cuya fecha y hora ya pasaron está vencido: se marca y no se confirma."""

    def vencer(self, pedido, dias=1):
        Pedido.objects.filter(pk=pedido.pk).update(fecha_servicio=self.dia(-dias))
        pedido.refresh_from_db()
        return pedido

    def test_pendiente_con_fecha_pasada(self):
        p = self.vencer(self.registrar())
        self.assertTrue(p.vencido)

    def test_a_futuro_o_confirmado_no_esta_vencido(self):
        p = self.registrar()
        self.assertFalse(p.vencido)
        self.confirmar(p)
        p = self.vencer(Pedido.objects.get(pk=p.pk))
        self.assertFalse(p.vencido)  # confirmado y ya empezó: se finaliza, no está vencido

    def test_vence_hoy_cuando_pasa_la_hora(self):
        ahora = timezone.localtime()
        p = self.registrar()
        Pedido.objects.filter(pk=p.pk).update(fecha_servicio=ahora.date(),
                                              hora_servicio=(ahora - timedelta(minutes=5)).time())
        p.refresh_from_db()
        self.assertTrue(p.vencido)

    def test_no_se_confirma_un_vencido(self):
        p = self.vencer(self.registrar())
        with self.assertRaises(reglas.ErrorPedido) as ctx:
            reglas.confirmar(p.pk)
        self.assertIn('vencido', str(ctx.exception))
        p.refresh_from_db()
        self.assertEqual(p.estado, Pedido.PENDIENTE)

    def test_un_vencido_se_puede_anular(self):
        p = self.vencer(self.registrar())
        self.assertEqual(reglas.anular(p.pk, self.admin, 'Nadie lo confirmó a tiempo').estado, Pedido.ANULADO)

    def test_filtro_de_vencidos(self):
        vencido = self.vencer(self.registrar())
        self.registrar(fecha_servicio=self.dia(3))
        ids = list(reglas.filtrar_pedidos(Pedido.objects.all(), estado=reglas.VENCIDO).values_list('pk', flat=True))
        self.assertEqual(ids, [vencido.pk])


class AvisosTest(BaseReglas):
    def test_para_finalizar(self):
        p = self.registrar()
        self.confirmar(p)
        Pedido.objects.filter(pk=p.pk).update(fecha_servicio=self.dia(-1))
        p.refresh_from_db()
        self.assertTrue(p.para_finalizar)
        self.assertEqual(list(reglas.filtrar_pedidos(Pedido.objects.all(), estado=reglas.PARA_FINALIZAR)), [p])
        reglas.finalizar(p.pk)
        self.assertEqual(reglas.contar_avisos()[reglas.PARA_FINALIZAR], 0)

    def test_por_confirmar_solo_los_proximos_dias(self):
        cerca = self.registrar(fecha_servicio=self.dia(2))
        self.registrar(fecha_servicio=self.dia(3))  # todavía hay tiempo
        lejos_confirmado = self.registrar(fecha_servicio=self.dia(1), patente='AE-123-CD')
        self.confirmar(lejos_confirmado)
        ids = [p.pk for p in reglas.filtrar_pedidos(Pedido.objects.all(), estado=reglas.POR_CONFIRMAR)]
        self.assertEqual(ids, [cerca.pk])

    def test_un_vencido_no_cuenta_como_por_confirmar(self):
        p = self.registrar()
        Pedido.objects.filter(pk=p.pk).update(fecha_servicio=self.dia(-1))
        avisos = reglas.contar_avisos()
        self.assertEqual((avisos[reglas.VENCIDO], avisos[reglas.POR_CONFIRMAR]), (1, 0))


class VehiculoPorDiaTest(BaseReglas):
    def test_un_pendiente_vencido_no_ocupa_el_vehiculo(self):
        p = self.registrar(fecha_servicio=self.dia(0), hora_servicio=(timezone.localtime() + timedelta(hours=1)).time()) \
            if timezone.localtime().hour < 23 else None
        if p is None:
            self.skipTest('muy tarde para armar el caso en el mismo día')
        self.assertNotIn('AD-321-JK', reglas.vehiculos_libres(self.dia(0)).values_list('patente', flat=True))
        Pedido.objects.filter(pk=p.pk).update(hora_servicio=(timezone.localtime() - timedelta(minutes=1)).time())
        if timezone.localtime().hour == 0 and timezone.localtime().minute == 0:
            self.skipTest('cambio de día')
        self.assertIn('AD-321-JK', reglas.vehiculos_libres(self.dia(0)).values_list('patente', flat=True))

    def test_motivo_cuando_no_hay_vehiculos(self):
        self.registrar()                               # ocupa AD-321-JK mañana
        self.registrar(patente='AE-123-CD')            # y AE-123-CD
        self.assertEqual(list(reglas.vehiculos_libres(self.dia())), [])
        self.assertEqual(reglas.motivo_sin_vehiculos(self.dia()),
                         'Los 2 vehículos disponibles ya tienen una mudanza ese día. Probá con otra fecha.')


class AsignarPersonalTest(BaseReglas):
    """Un chofer obligatorio, ayudantes opcionales y una mudanza por persona por día."""

    def setUp(self):
        from usuarios.models import PersonalPedido, Rol
        from usuarios.utils import hash_password
        self.PersonalPedido = PersonalPedido
        self.chofer = Usuario.objects.get(DNI=40987654)
        self.ayudante = Usuario.objects.get(DNI=38999888)
        self.chofer2 = Usuario.objects.create(
            DNI=30111222, Nombre='Pablo', Apellido='Ruiz', Correo='pablo.ruiz@ejemplo.com', NombreUsuario='ruizp',
            Clave=hash_password('Usuario123!'), idRol=Rol.objects.get(nom_rol='Chofer'))

    def test_asigna_chofer_y_ayudante(self):
        p = self.registrar()
        reglas.asignar_personal(p.pk, self.chofer.pk, [self.ayudante.pk])
        self.assertEqual([(x.idUsuario, x.Funcion) for x in p.personal.all()],
                         [(self.chofer, 'Chofer'), (self.ayudante, 'Ayudante')])

    def test_reasignar_reemplaza(self):
        p = self.registrar()
        reglas.asignar_personal(p.pk, self.chofer.pk, [self.ayudante.pk])
        reglas.asignar_personal(p.pk, self.chofer2.pk)
        self.assertEqual([x.idUsuario for x in p.personal.all()], [self.chofer2])

    def test_sin_chofer_no_se_confirma(self):
        p = self.registrar()
        with self.assertRaises(reglas.ErrorPedido) as ctx:
            reglas.confirmar(p.pk)
        self.assertEqual(str(ctx.exception), 'Asigná el chofer antes de confirmar el pedido.')

    def test_el_chofer_es_obligatorio(self):
        p = self.registrar()
        with self.assertRaises(reglas.ErrorPedido) as ctx:
            reglas.asignar_personal(p.pk, None)
        self.assertEqual(ctx.exception.errores['chofer'], 'Elegí el chofer.')

    def test_una_persona_una_mudanza_por_dia(self):
        uno = self.registrar()
        reglas.asignar_personal(uno.pk, self.chofer.pk, [self.ayudante.pk])
        dos = self.registrar(patente='AE-123-CD')
        with self.assertRaises(reglas.ErrorPedido) as ctx:
            reglas.asignar_personal(dos.pk, self.chofer.pk)
        self.assertEqual(ctx.exception.errores['chofer'], 'Ese chofer no está libre ese día. Elegí otro.')
        with self.assertRaises(reglas.ErrorPedido) as ctx:
            reglas.asignar_personal(dos.pk, self.chofer2.pk, [self.ayudante.pk])
        self.assertIn('ayudantes', ctx.exception.errores)
        reglas.asignar_personal(dos.pk, self.chofer2.pk)  # con otro chofer sí
        otro_dia = self.registrar(fecha_servicio=self.dia(2))
        reglas.asignar_personal(otro_dia.pk, self.chofer.pk)  # y el mismo chofer otro día también

    def test_anular_libera_al_personal(self):
        uno = self.registrar()
        reglas.asignar_personal(uno.pk, self.chofer.pk)
        reglas.anular(uno.pk, self.admin, 'El cliente canceló')
        self.assertIn(self.chofer, reglas.personal_libre(uno.fecha_servicio, reglas.ROL_CHOFER))

    def test_un_chofer_dado_de_baja_no_se_ofrece(self):
        Usuario.objects.filter(pk=self.chofer2.pk).update(Activo=False)
        self.assertNotIn(self.chofer2, reglas.personal_libre(self.dia(), reglas.ROL_CHOFER))

    def test_un_cliente_no_puede_ser_chofer(self):
        p = self.registrar()
        with self.assertRaises(reglas.ErrorPedido):
            reglas.asignar_personal(p.pk, self.cliente.pk)

    def test_no_se_asigna_a_un_pedido_anulado_o_que_ya_empezo(self):
        p = self.registrar()
        reglas.anular(p.pk, self.admin, 'El cliente canceló')
        with self.assertRaises(reglas.ErrorPedido):
            reglas.asignar_personal(p.pk, self.chofer.pk)
        q = self.registrar(fecha_servicio=self.dia(3))
        Pedido.objects.filter(pk=q.pk).update(fecha_servicio=self.dia(-1))
        with self.assertRaises(reglas.ErrorPedido):
            reglas.asignar_personal(q.pk, self.chofer.pk)

    def test_aviso_confirmados_sin_chofer(self):
        p = self.confirmar(self.registrar())
        self.assertEqual(reglas.contar_avisos()[reglas.SIN_CHOFER], 0)
        self.PersonalPedido.objects.filter(idPedido=p).delete()  # como los confirmados de antes de la regla
        self.assertEqual(reglas.contar_avisos()[reglas.SIN_CHOFER], 1)
