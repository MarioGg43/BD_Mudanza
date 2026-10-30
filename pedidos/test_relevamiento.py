"""Relevamiento del chofer (cantidades reales, objetos no declarados, adicionales y recargo) y
edición de servicios por el administrador."""
from datetime import datetime, time
from decimal import Decimal
from unittest import mock

from django.utils import timezone

from pedidos import reglas
from pedidos.test_reglas import ADMIN, BaseReglas, obj
from usuarios.models import Pedido, Usuario


class RelevamientoTest(BaseReglas):
    def setUp(self):
        self.chofer = Usuario.objects.get(DNI=40987654)
        self.ayudante = Usuario.objects.get(DNI=38999888)
        # flete mañana de 9 a 14 en AD-321-JK (camión chico): 1 heladera y 10 cajas → $75.000
        self.p = self.registrar(id_servicio=self.flete.id_servicio)
        reglas.asignar_personal(self.p.pk, self.chofer.pk, [self.ayudante.pk])
        reglas.confirmar(self.p.pk)
        self.heladera = self.p.inventario.get(idObjeto__nom_objeto='Heladera')
        self.cajas = self.p.inventario.get(idObjeto__nom_objeto='Cajas')

    def a_las(self, hora, minuto=0, dias=1):
        momento = timezone.make_aware(datetime.combine(self.dia(dias), time(hora, minuto)))
        return mock.patch('django.utils.timezone.now', return_value=momento)

    def empezar(self):
        with self.a_las(9):
            reglas.marcar_inicio(self.p.pk, self.chofer)

    def entrar(self, dni):
        s = self.client.session
        s['usuario_dni'], s['usuario_rol'] = dni, Usuario.objects.get(DNI=dni).idRol.nom_rol
        s.save()

    def test_corrige_agrega_suma_adicional_y_recargo(self):
        self.empezar()
        reglas.relevamiento(self.p.pk, self.chofer, {self.cajas.pk: 25, self.heladera.pk: 1},
                            [{'objeto': obj('Sillas'), 'cantidad': 6},
                             {'objeto': obj('Otro'), 'cantidad': 1, 'observacion': 'Piano'}],
                            [self.embalaje.id_servicio], 30000, 'Eran 25 cajas y había sillas y un piano')
        self.p.refresh_from_db()
        self.cajas.refresh_from_db()
        self.heladera.refresh_from_db()
        self.assertEqual((self.cajas.Cantidad, self.cajas.cantidad_declarada), (25, 10))
        self.assertIsNone(self.heladera.cantidad_declarada)                   # no cambió
        self.assertEqual(self.p.inventario.get(idObjeto__nom_objeto='Sillas').cantidad_declarada, 0)
        self.assertEqual(self.p.total, Decimal('130000'))                      # 75.000 + 25.000 + 30.000
        self.assertEqual(self.p.motivo_recargo, 'Eran 25 cajas y había sillas y un piano')

    def test_validaciones(self):
        with self.assertRaises(reglas.ErrorPedido):            # antes de «Empezamos»
            reglas.relevamiento(self.p.pk, self.chofer, {self.cajas.pk: 12})
        self.empezar()
        with self.assertRaises(reglas.ErrorPedido):            # el ayudante no
            reglas.relevamiento(self.p.pk, self.ayudante, {self.cajas.pk: 12})
        for kwargs, campo in [(dict(recargo=5000), 'motivo'), (dict(recargo=-1, motivo='nada que ver'), 'recargo'),
                              (dict(nuevos=[{'objeto': obj('Cajas'), 'cantidad': 3}]), 'inventario'),
                              (dict(reales={self.cajas.pk: 0, self.heladera.pk: 0}), 'inventario')]:
            with self.assertRaises(reglas.ErrorPedido) as ctx:
                reglas.relevamiento(self.p.pk, self.chofer, kwargs.pop('reales', {}), **kwargs)
            self.assertIn(campo, ctx.exception.errores, kwargs)
        self.p.refresh_from_db()
        self.assertEqual(self.p.total, 75000)                  # nada quedó a medias

    def test_pantalla_del_chofer_y_comprobante(self):
        self.empezar()
        self.entrar(40987654)
        with self.a_las(9, 30):
            self.assertContains(self.client.get('/portal/'), 'Relevamiento')
            r = self.client.get(f'/pedidos/{self.p.pk}/relevamiento/')
            self.assertContains(r, 'Lo que declaró el cliente')
            r = self.client.post(f'/pedidos/{self.p.pk}/relevamiento/', {
                f'real-{self.cajas.pk}': '14', f'real-{self.heladera.pk}': '1',
                'nuevo-0-objeto': str(obj('Colchón').pk), 'nuevo-0-cantidad': '2',
                'recargo': '15000', 'motivo': 'Más cajas y dos colchones'})
            self.assertRedirects(r, '/portal/', fetch_redirect_response=False)
        self.entrar(ADMIN)
        r = self.client.get(f'/pedidos/{self.p.pk}/comprobante/')
        self.assertContains(r, '14 <i>(declaró 10)</i>', html=True)
        self.assertContains(r, 'Recargo <i>(Más cajas y dos colchones)</i>', html=True)
        self.assertContains(r, '$90.000,00')

    def test_el_ayudante_no_entra_al_relevamiento(self):
        self.empezar()
        self.entrar(38999888)
        with self.a_las(9, 30):
            r = self.client.get(f'/pedidos/{self.p.pk}/relevamiento/')
        self.assertRedirects(r, '/portal/', fetch_redirect_response=False)


class EditarServiciosTest(BaseReglas):
    def setUp(self):
        self.p = self.registrar(id_servicio=self.flete.id_servicio, ids_adicionales=[self.embalaje.id_servicio])

    def test_cambia_principal_y_adicionales_y_recalcula(self):
        reglas.editar_servicios(self.p.pk, self.local.id_servicio, [self.armado.id_servicio])
        self.p.refresh_from_db()
        self.assertEqual(self.p.duracion_horas, 10)
        self.assertEqual(sorted(d.idServicio.Tipo_servicio for d in self.p.detalles.all()),
                         ['Desarmado y armado de muebles', 'Mudanza local'])
        self.assertEqual(self.p.total, 185000 + 35000)

    def test_si_dura_mas_el_vehiculo_tiene_que_seguir_libre(self):
        self.registrar(id_servicio=self.flete.id_servicio, hora_servicio=time(14, 0))  # el mismo camión a las 14
        with self.assertRaises(reglas.ErrorPedido) as ctx:
            reglas.editar_servicios(self.p.pk, self.local.id_servicio)               # 10 h: hasta las 19
        self.assertIn('no está libre', ctx.exception.errores['servicio'])

    def test_pantalla_del_admin(self):
        s = self.client.session
        s['usuario_dni'], s['usuario_rol'] = ADMIN, 'Administrador'
        s.save()
        self.assertContains(self.client.get(f'/pedidos/{self.p.pk}/'), 'Editar servicios')
        r = self.client.post(f'/pedidos/{self.p.pk}/servicios/', {'servicio': self.flete.id_servicio,
                                                                  'adicionales': [self.armado.id_servicio]})
        self.assertRedirects(r, f'/pedidos/{self.p.pk}/', fetch_redirect_response=False)
        self.assertEqual(Pedido.objects.get(pk=self.p.pk).total, 75000 + 35000)
