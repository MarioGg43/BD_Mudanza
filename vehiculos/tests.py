"""Pruebas del CRUD de vehículos (Hito 1) sobre la tabla VEHICULOS del DER."""
import io

from django.core.management import call_command
from django.test import TestCase

from usuarios.models import Objeto, Usuario, Vehiculo, Pedido

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
        base = {'patente': ' ab 999 zz ', 'marca_modelo': 'Fiat Ducato', 'tipo_vehiculo': 'Furgón Urbano',
                'capacidad_kg': '1500', 'capacidad_m3': '10', 'estado': 'Disponible',
                'kilometraje': '0', 'anio': '2024', 'chofer_asignado': '', 'observaciones': ''}
        base.update(cambios)
        return base

    def test_inicio_es_publico(self):
        self.assertEqual(self.client.get('/').status_code, 200)

    def test_la_portada_es_para_clientes(self):
        r = self.client.get('/')
        self.assertContains(r, 'Pedí tu mudanza')
        self.assertContains(r, 'href="/registro/"')
        self.assertContains(r, 'href="/login/"')
        self.assertNotContains(r, 'href="/vehiculos/"')  # la flota es interna
        self.assertNotContains(r, 'Ver Vehículos')

    def test_la_portada_muestra_los_servicios_activos_con_precio(self):
        from usuarios.models import Servicio
        Servicio.objects.filter(Tipo_servicio='Mudanza nacional').update(Activo=False)
        r = self.client.get('/')
        self.assertContains(r, 'Mudanza local')
        self.assertContains(r, '185.000')
        self.assertContains(r, 'Mantas, film y cintas')
        self.assertNotContains(r, 'Mudanza nacional')

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

    def test_el_tipo_se_elige_de_una_lista(self):
        self.entrar(ADMIN)
        r = self.client.get('/vehiculos/crear/')
        self.assertContains(r, '<select name="tipo_vehiculo"')
        r = self.client.post('/vehiculos/crear/', self.datos(tipo_vehiculo='Camion'))
        self.assertEqual(r.status_code, 200)
        self.assertIn('tipo_vehiculo', r.context['form'].errors)
        self.assertFalse(Vehiculo.objects.filter(patente='AB999ZZ').exists())

    def test_valores_fuera_de_rango(self):
        self.entrar(ADMIN)
        for campo, valor in [('capacidad_kg', '50'), ('capacidad_kg', '50000'), ('capacidad_m3', '120'),
                             ('kilometraje', '2500000'), ('anio', '1970'), ('anio', '2099')]:
            r = self.client.post('/vehiculos/crear/', self.datos(**{campo: valor}))
            self.assertIn(campo, r.context['form'].errors, (campo, valor))
        self.assertFalse(Vehiculo.objects.filter(patente='AB999ZZ').exists())

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
            'AD-321-JK', [{'objeto': Objeto.objects.get(nom_objeto='Cajas'), 'cantidad': 2, 'fragil': False}])
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


class AgendaDelVehiculoTest(TestCase):
    """Desde el vehículo se ven sus pedidos: los próximos y el historial."""
    setUpTestData = VehiculosTest.setUpTestData
    entrar = VehiculosTest.entrar

    def setUp(self):
        from datetime import time, timedelta
        from django.utils import timezone
        from pedidos import reglas
        from usuarios.models import Servicio
        self.proximo = reglas.registrar_pedido(
            Usuario.objects.get(DNI=29876543), timezone.localdate() + timedelta(days=3), time(8, 30),
            'Av. Belgrano 100', 'Mitre 50', Servicio.objects.get(Tipo_servicio='Flete urbano').id_servicio,
            'AE-123-CD', [{'objeto': Objeto.objects.get(nom_objeto='Mesa'), 'cantidad': 1}])
        self.viejo = Pedido.objects.get(patente_vehiculo='AE-123-CD', estado=Pedido.FINALIZADO)  # el de init_data

    def test_el_detalle_separa_proximos_e_historial(self):
        self.entrar(ADMIN)
        r = self.client.get('/vehiculos/AE-123-CD/')
        self.assertEqual(list(r.context['proximos']), [self.proximo])
        self.assertEqual(list(r.context['para_cerrar']), [])
        self.assertEqual(list(r.context['historial']), [self.viejo])
        self.assertContains(r, 'Gómez, María')
        self.assertContains(r, f'href="/pedidos/{self.proximo.pk}/"')
        self.assertContains(r, 'href="/pedidos/?vehiculo=AE-123-CD"')

    def test_la_tarjeta_muestra_la_cantidad(self):
        self.entrar(ADMIN)
        r = self.client.get('/vehiculos/')
        self.assertContains(r, 'Pedidos (2)')
        self.assertContains(r, 'href="/vehiculos/AE-123-CD/"')

    def test_filtro_por_vehiculo_en_la_lista_de_pedidos(self):
        self.entrar(ADMIN)
        r = self.client.get('/pedidos/', {'vehiculo': 'AE-123-CD'})
        self.assertEqual({p.pk for p in r.context['pedidos']}, {self.proximo.pk, self.viejo.pk})
        r = self.client.get('/pedidos/', {'vehiculo': 'AD-321-JK'})
        self.assertEqual(list(r.context['pedidos']), [])
        pdf = self.client.get('/pedidos/descargar/', {'vehiculo': 'AE-123-CD'})
        self.assertEqual(pdf.status_code, 200)

    def test_el_cliente_no_filtra_por_vehiculo(self):
        self.entrar(29876543)
        self.assertNotIn('vehiculo', self.client.get('/pedidos/').context['form'].fields)

    def test_el_chofer_no_entra(self):
        self.entrar(40987654)
        self.assertEqual(self.client.get('/vehiculos/AE-123-CD/').status_code, 403)

    def test_patente_inexistente(self):
        self.entrar(ADMIN)
        self.assertEqual(self.client.get('/vehiculos/ZZ999ZZ/').status_code, 404)


class EnlacesAPedidosTest(TestCase):
    setUpTestData = VehiculosTest.setUpTestData
    entrar = VehiculosTest.entrar

    def test_el_panel_lleva_a_los_pedidos_del_cliente(self):
        self.entrar(ADMIN)
        cliente = Usuario.objects.get(DNI=29876543)
        self.assertContains(self.client.get('/panel/'), f'href="/pedidos/?cliente={cliente.id_usuario}"')

    def test_servicios_muestra_cuantos_pedidos(self):
        from usuarios.models import Servicio
        self.entrar(ADMIN)
        local = Servicio.objects.get(Tipo_servicio='Mudanza local')
        self.assertContains(self.client.get('/servicios/'), f'href="/pedidos/?servicio={local.id_servicio}"')


class SinChoferTest(TestCase):
    setUpTestData = VehiculosTest.setUpTestData
    entrar = VehiculosTest.entrar

    def setUp(self):
        from datetime import time, timedelta
        from django.utils import timezone
        from pedidos import reglas
        from usuarios.models import Servicio
        reglas.registrar_pedido(
            Usuario.objects.get(DNI=29876543), timezone.localdate() + timedelta(days=2), time(9, 0),
            'Origen 1', 'Destino 2', Servicio.objects.get(Tipo_servicio='Flete urbano').id_servicio,
            'AD-321-JK', [{'objeto': Objeto.objects.get(nom_objeto='Cajas'), 'cantidad': 1}])
        self.entrar(ADMIN)

    def test_avisa_en_la_lista_y_en_el_detalle(self):
        r = self.client.get('/vehiculos/')
        self.assertContains(r, 'Mudanzas sin chofer asignado')
        self.assertEqual([v.patente for v in r.context['sin_chofer']], ['AD-321-JK'])
        detalle = self.client.get('/vehiculos/AD-321-JK/')
        self.assertContains(detalle, '1 mudanza sin chofer asignado')
        self.assertContains(detalle, 'Sin asignar')

    def test_el_chofer_habitual_no_alcanza_hace_falta_el_del_pedido(self):
        Vehiculo.objects.filter(pk='AD-321-JK').update(chofer_asignado=Usuario.objects.get(DNI=CHOFER))
        self.assertEqual(len(self.client.get('/vehiculos/').context['sin_chofer']), 1)

    def test_con_chofer_en_el_pedido_no_avisa(self):
        from pedidos import reglas
        pedido = Pedido.objects.get(patente_vehiculo='AD-321-JK', estado='Pendiente')
        reglas.asignar_personal(pedido.pk, Usuario.objects.get(DNI=CHOFER).pk)
        r = self.client.get('/vehiculos/')
        self.assertEqual(r.context['sin_chofer'], [])
        detalle = self.client.get('/vehiculos/AD-321-JK/')
        self.assertNotContains(detalle, 'sin chofer asignado')
        self.assertContains(detalle, 'Luciana Fernandez')

    def test_la_etiqueta_dice_chofer_habitual(self):
        r = self.client.get('/vehiculos/editar/AD-321-JK/')
        self.assertContains(r, 'Chofer habitual')
        self.assertContains(r, 'se sugiere al asignar el personal')


class ParaCerrarTest(TestCase):
    """Un pedido que ya pasó sin cerrarse no es «próximo» ni cuenta para el aviso de chofer."""
    setUpTestData = VehiculosTest.setUpTestData
    entrar = VehiculosTest.entrar

    def test_separa_lo_que_ya_paso(self):
        from datetime import time, timedelta
        from django.utils import timezone
        from pedidos import reglas
        from usuarios.models import Servicio
        nuevo = lambda dias: reglas.registrar_pedido(
            Usuario.objects.get(DNI=29876543), timezone.localdate() + timedelta(days=dias), time(9, 0),
            'A 1', 'B 2', Servicio.objects.get(Tipo_servicio='Flete urbano').id_servicio,
            'AD-321-JK', [{'objeto': Objeto.objects.get(nom_objeto='Cajas'), 'cantidad': 1}])
        hecho, vencido, futuro = nuevo(1), nuevo(2), nuevo(3)
        reglas.asignar_personal(hecho.pk, Usuario.objects.get(DNI=CHOFER).pk)
        reglas.confirmar(hecho.pk)
        ayer = timezone.localdate() - timedelta(days=1)
        Pedido.objects.filter(pk__in=[hecho.pk, vencido.pk]).update(fecha_servicio=ayer)
        self.entrar(ADMIN)
        r = self.client.get('/vehiculos/AD-321-JK/')
        self.assertEqual(list(r.context['proximos']), [futuro])
        self.assertEqual({p.pk for p in r.context['para_cerrar']}, {hecho.pk, vencido.pk})
        self.assertContains(r, 'Para cerrar')
        sin_chofer = self.client.get('/vehiculos/').context['sin_chofer']
        self.assertEqual([(v.patente, v.mudanzas_sin_chofer) for v in sin_chofer], [('AD-321-JK', 1)])
