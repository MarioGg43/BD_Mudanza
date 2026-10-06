"""Pruebas de las reglas del pedido. Usan los datos de init_data:
Mudanza local $185.000, Flete urbano $75.000; AD-321-JK (1600 kg) y AE-123-CD
(5000 kg) disponibles; AC-789-GH en mantenimiento; AF-456-EF en viaje."""
import io
from datetime import timedelta
from decimal import Decimal
from unittest import mock

from django.core.management import call_command
from django.db import IntegrityError
from django.test import TestCase
from django.utils import timezone

from pedidos import reglas
from usuarios.models import DetallePedido, Pedido, Servicio, Usuario

CLIENTE, ADMIN = 29876543, 35123456


class BaseReglas(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command('init_data', stdout=io.StringIO())
        cls.cliente = Usuario.objects.get(DNI=CLIENTE)
        cls.admin = Usuario.objects.get(DNI=ADMIN)
        cls.local = Servicio.objects.get(Tipo_servicio='Mudanza local')
        cls.flete = Servicio.objects.get(Tipo_servicio='Flete urbano')

    def dia(self, dias=1):
        return timezone.localdate() + timedelta(days=dias)

    def registrar(self, **cambios):
        datos = dict(
            cliente=self.cliente, fecha_servicio=self.dia(), origen='Av. Belgrano 100, Salta',
            destino='Mitre 50, Cerrillos', ids_servicios=[self.local.id_servicio, self.flete.id_servicio],
            patente='AD-321-JK',
            items=[{'descripcion': 'Heladera', 'cantidad': 1, 'peso': Decimal('80'), 'fragil': True},
                   {'descripcion': 'Cajas', 'cantidad': 10, 'peso': Decimal('12.5'), 'fragil': False}])
        datos.update(cambios)
        return reglas.registrar_pedido(**datos)

    def assertRechaza(self, campo, **cambios):
        antes = Pedido.objects.count()
        with self.assertRaises(reglas.ErrorPedido) as ctx:
            self.registrar(**cambios)
        self.assertIn(campo, ctx.exception.errores)
        self.assertEqual(Pedido.objects.count(), antes)


class RegistrarPedidoTest(BaseReglas):
    def test_registra_el_pedido_completo(self):
        p = self.registrar()
        self.assertEqual(p.estado, Pedido.PENDIENTE)
        self.assertEqual(p.Fecha_pedido, timezone.localdate())
        self.assertEqual(p.idUsuario, self.cliente)
        self.assertEqual(p.total, Decimal('260000'))
        self.assertEqual(
            sorted((d.idServicio.Tipo_servicio, d.precio_unitario, d.subtotal) for d in p.detalles.all()),
            [('Flete urbano', 75000, 75000), ('Mudanza local', 185000, 185000)])
        self.assertEqual(sorted(i.Descripcion for i in p.inventario.all()), ['Cajas', 'Heladera'])
        self.assertEqual(p.peso_total, Decimal('205'))

    def test_el_precio_queda_fijo_en_el_pedido(self):
        p = self.registrar()
        Servicio.objects.filter(pk=self.local.pk).update(Precio_base=999999)
        self.assertEqual(p.detalles.get(idServicio=self.local).precio_unitario, 185000)

    def test_fecha_pasada(self):
        self.assertRechaza('fecha_servicio', fecha_servicio=self.dia(-1))

    def test_fecha_a_mas_de_un_anio(self):
        self.assertRechaza('fecha_servicio', fecha_servicio=self.dia(366))

    def test_se_puede_para_hoy(self):
        self.assertEqual(self.registrar(fecha_servicio=self.dia(0)).estado, Pedido.PENDIENTE)

    def test_origen_vacio(self):
        self.assertRechaza('origen', origen='   ')

    def test_destino_igual_al_origen(self):
        self.assertRechaza('destino', destino='AV. BELGRANO 100, SALTA')

    def test_sin_servicios(self):
        self.assertRechaza('servicios', ids_servicios=[])

    def test_servicio_inactivo(self):
        Servicio.objects.filter(pk=self.flete.pk).update(Activo=False)
        self.assertRechaza('servicios')

    def test_sin_objetos(self):
        self.assertRechaza('inventario', items=[])

    def test_objeto_sin_descripcion(self):
        self.assertRechaza('inventario', items=[{'descripcion': '', 'cantidad': 1, 'peso': 5}])

    def test_cantidad_fuera_de_rango(self):
        self.assertRechaza('inventario', items=[{'descripcion': 'Sillas', 'cantidad': 0, 'peso': 5}])
        self.assertRechaza('inventario', items=[{'descripcion': 'Sillas', 'cantidad': 1000, 'peso': 1}])

    def test_peso_fuera_de_rango(self):
        self.assertRechaza('inventario', items=[{'descripcion': 'Sillas', 'cantidad': 1, 'peso': 0}])
        self.assertRechaza('inventario', items=[{'descripcion': 'Piano', 'cantidad': 1, 'peso': 5001}])

    def test_sin_vehiculo(self):
        self.assertRechaza('vehiculo', patente='')

    def test_vehiculo_en_mantenimiento(self):
        self.assertRechaza('vehiculo', patente='AC-789-GH')

    def test_carga_supera_la_capacidad(self):
        self.assertRechaza('vehiculo', items=[{'descripcion': 'Máquinas', 'cantidad': 2, 'peso': 850}])

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
    def test_confirmar_y_finalizar(self):
        p = self.registrar()
        self.assertEqual(reglas.confirmar(p.pk).estado, Pedido.CONFIRMADO)
        self.assertEqual(reglas.finalizar(p.pk).estado, Pedido.FINALIZADO)
        self.assertEqual(Pedido.objects.get(pk=p.pk).estado, Pedido.FINALIZADO)

    def test_no_se_finaliza_un_pendiente(self):
        p = self.registrar()
        with self.assertRaises(reglas.ErrorPedido):
            reglas.finalizar(p.pk)
        self.assertEqual(Pedido.objects.get(pk=p.pk).estado, Pedido.PENDIENTE)

    def test_no_se_confirma_dos_veces(self):
        p = self.registrar()
        reglas.confirmar(p.pk)
        with self.assertRaises(reglas.ErrorPedido):
            reglas.confirmar(p.pk)

    def test_anular_guarda_fecha_motivo_y_usuario_y_libera_el_vehiculo(self):
        p = self.registrar()
        reglas.confirmar(p.pk)
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
        self.p1 = self.registrar(fecha_servicio=self.dia(1), ids_servicios=[self.local.id_servicio])
        self.p2 = self.registrar(fecha_servicio=self.dia(5), ids_servicios=[self.flete.id_servicio])
        reglas.confirmar(self.p2.pk)
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
