"""Pruebas del CRUD de vehículos (Hito 1) sobre la tabla VEHICULOS del DER."""
import io

from django.core.management import call_command
from django.test import TestCase

from usuarios.models import Usuario, Vehiculo, Pedido

ADMIN, CHOFER = 35123456, 40987654


class VehiculosTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command('init_data', stdout=io.StringIO())

    def entrar(self, dni):
        s = self.client.session
        s['usuario_dni'] = dni
        s.save()

    def datos(self, **cambios):
        base = {'patente': ' ab 999 zz ', 'marca_modelo': 'Fiat Ducato', 'tipo_vehiculo': 'Furgón',
                'capacidad_kg': '1500', 'capacidad_m3': '10', 'estado': 'Disponible',
                'kilometraje': '0', 'anio': '2024', 'chofer_asignado': '', 'observaciones': ''}
        base.update(cambios)
        return base

    def test_inicio_es_publico(self):
        self.assertEqual(self.client.get('/').status_code, 200)

    def test_con_sesion_la_portada_lleva_a_la_pantalla_de_cada_rol(self):
        # la portada (Ver vehículos / Ingresar) es solo para visitantes
        for dni, destino in ((29876543, '/pedidos/'), (ADMIN, '/panel/'), (CHOFER, '/portal/')):
            self.entrar(dni)
            self.assertRedirects(self.client.get('/'), destino, msg_prefix=str(dni))

    def test_sin_sesion_va_al_login(self):
        for url in ['/vehiculos/', '/vehiculos/crear/', '/vehiculos/editar/AE-123-CD/']:
            self.assertRedirects(self.client.get(url), '/login/', msg_prefix=url)
        self.assertRedirects(self.client.post('/vehiculos/baja/AE-123-CD/'), '/login/')

    def test_chofer_no_entra(self):
        self.entrar(CHOFER)
        self.assertEqual(self.client.get('/vehiculos/').status_code, 403)
        self.assertEqual(self.client.post('/vehiculos/crear/', self.datos()).status_code, 403)
        self.assertFalse(Vehiculo.objects.filter(patente='AB999ZZ').exists())

    def test_lista(self):
        self.entrar(ADMIN)
        r = self.client.get('/vehiculos/')
        self.assertEqual(len(r.context['vehiculos']), 4)
        self.assertContains(r, 'Luciana')  # chofer asignado al AE-123-CD

    def test_alta_normaliza_la_patente(self):
        self.entrar(ADMIN)
        r = self.client.post('/vehiculos/crear/', self.datos())
        self.assertRedirects(r, '/vehiculos/')
        self.assertTrue(Vehiculo.objects.filter(patente='AB999ZZ').exists())

    def test_alta_patente_repetida(self):
        self.entrar(ADMIN)
        r = self.client.post('/vehiculos/crear/', self.datos(patente='ae-123-cd'))
        self.assertEqual(r.status_code, 200)
        self.assertEqual(Vehiculo.objects.count(), 4)

    def test_solo_choferes_activos_en_el_combo(self):
        self.entrar(ADMIN)
        opciones = self.client.get('/vehiculos/crear/').context['form'].fields['chofer_asignado'].queryset
        self.assertEqual([u.DNI for u in opciones], [CHOFER])
        r = self.client.post('/vehiculos/crear/', self.datos(chofer_asignado=Usuario.objects.get(DNI=ADMIN).pk))
        self.assertEqual(r.status_code, 200)  # el admin no es chofer: el formulario lo rechaza

    def test_editar_no_cambia_la_patente(self):
        # antes, cambiar la patente creaba un vehículo nuevo y dejaba el viejo
        self.entrar(ADMIN)
        r = self.client.post('/vehiculos/editar/AD-321-JK/',
                             self.datos(patente='ZZ-000-ZZ', marca_modelo='Renault Master 2024'))
        self.assertRedirects(r, '/vehiculos/')
        self.assertEqual(Vehiculo.objects.count(), 4)
        self.assertEqual(Vehiculo.objects.get(pk='AD-321-JK').marca_modelo, 'Renault Master 2024')

    def test_baja_logica_conserva_el_pedido(self):
        self.entrar(ADMIN)
        self.assertRedirects(self.client.post('/vehiculos/baja/AE-123-CD/'), '/vehiculos/')
        v = Vehiculo.objects.get(pk='AE-123-CD')
        self.assertEqual(v.estado, 'Fuera de Servicio')
        self.assertTrue(Pedido.objects.filter(patente_vehiculo=v).exists())

    def test_baja_solo_por_post(self):
        self.entrar(ADMIN)
        self.assertEqual(self.client.get('/vehiculos/baja/AE-123-CD/').status_code, 405)

    def test_la_pantalla_de_edicion_conserva_el_chofer(self):
        # se envían exactamente los campos que dibuja la pantalla, con sus valores
        self.entrar(ADMIN)
        form = self.client.get('/vehiculos/editar/AE-123-CD/').context['form']
        html = self.client.get('/vehiculos/editar/AE-123-CD/').content.decode()
        enviados = {n: form[n].value() or '' for n in form.fields
                    if f'name="{n}"' in html and not form.fields[n].disabled}
        self.client.post('/vehiculos/editar/AE-123-CD/', enviados)
        self.assertEqual(Vehiculo.objects.get(pk='AE-123-CD').chofer_asignado.DNI, CHOFER)


class PedidosActivosTest(TestCase):
    """Un vehículo con pedidos activos a futuro no sale de servicio."""
    setUpTestData = VehiculosTest.setUpTestData
    entrar = VehiculosTest.entrar
    datos = VehiculosTest.datos

    def setUp(self):
        from datetime import time, timedelta
        from django.utils import timezone
        from pedidos import reglas
        from usuarios.models import Servicio
        self.reglas = reglas
        self.pedido = reglas.registrar_pedido(
            Usuario.objects.get(DNI=29876543), timezone.localdate() + timedelta(days=1), time(9, 0),
            'Origen 1', 'Destino 2', Servicio.objects.get(Tipo_servicio='Mudanza local').id_servicio,
            'AD-321-JK', [{'descripcion': 'Cajas', 'cantidad': 2, 'fragil': False}])
        self.entrar(ADMIN)

    def test_la_baja_se_rechaza(self):
        self.assertRedirects(self.client.post('/vehiculos/baja/AD-321-JK/'), '/vehiculos/')
        self.assertEqual(Vehiculo.objects.get(pk='AD-321-JK').estado, 'Disponible')

    def test_no_pasa_a_mantenimiento(self):
        r = self.client.post('/vehiculos/editar/AD-321-JK/', self.datos(
            patente='AD-321-JK', estado='En Mantenimiento', marca_modelo='Renault Master'))
        self.assertEqual(r.status_code, 200)
        self.assertIn('estado', r.context['form'].errors)
        self.assertEqual(Vehiculo.objects.get(pk='AD-321-JK').estado, 'Disponible')

    def test_anulado_el_pedido_la_baja_funciona(self):
        self.reglas.anular(self.pedido.pk, Usuario.objects.get(DNI=ADMIN), 'Pedido duplicado')
        self.client.post('/vehiculos/baja/AD-321-JK/')
        self.assertEqual(Vehiculo.objects.get(pk='AD-321-JK').estado, 'Fuera de Servicio')
