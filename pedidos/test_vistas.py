"""Pruebas de las pantallas del pedido: permisos, consulta y detalle."""
import io
from datetime import datetime, time, timedelta
from unittest import mock

from django.core.management import call_command
from django.test import TestCase
from django.utils import timezone

from pedidos import reglas
from pedidos.permisos import tiene_permiso
from usuarios.models import Objeto, Pedido, Rol, Servicio, Usuario
from usuarios.utils import hash_password

ADMIN, CHOFER, CLIENTE = 35123456, 40987654, 29876543


def id_obj(nombre):
    return str(Objeto.objects.get(nom_objeto=nombre).pk)


class BaseVistas(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command('init_data', stdout=io.StringIO())
        cls.cliente = Usuario.objects.get(DNI=CLIENTE)
        cls.otro = Usuario.objects.create(
            DNI=31555666, Nombre='Jorge', Apellido='Herrera', Correo='jorge.herrera@ejemplo.com',
            NombreUsuario='herreraj', Clave=hash_password('Cliente123!'), DebeCambiarClave=False,
            idRol=Rol.objects.get(nom_rol='Cliente'))
        cls.local = Servicio.objects.get(Tipo_servicio='Mudanza local')

    def entrar(self, dni):
        s = self.client.session
        s['usuario_dni'] = dni
        s['usuario_rol'] = Usuario.objects.get(DNI=dni).idRol.nom_rol
        s.save()

    def pedido_de(self, cliente, dias=1, patente='AD-321-JK'):
        return reglas.registrar_pedido(
            cliente, timezone.localdate() + timedelta(days=dias), time(9, 0), 'Origen 1', 'Destino 2',
            self.local.id_servicio, patente,
            [{'objeto': Objeto.objects.get(nom_objeto='Cajas'), 'cantidad': 2, 'fragil': False}])


class PermisosTest(BaseVistas):
    def test_tiene_permiso_segun_la_tabla(self):
        admin, chofer = Usuario.objects.get(DNI=ADMIN), Usuario.objects.get(DNI=CHOFER)
        self.assertTrue(tiene_permiso(self.cliente, 'PED_REGISTRAR'))
        self.assertFalse(tiene_permiso(self.cliente, 'PED_ANULAR'))
        self.assertTrue(tiene_permiso(admin, 'PED_ANULAR'))
        self.assertFalse(tiene_permiso(admin, 'PED_REGISTRAR'))
        self.assertFalse(tiene_permiso(chofer, 'PED_CONSULTAR'))

    def test_sin_sesion_va_al_login(self):
        self.assertRedirects(self.client.get('/pedidos/'), '/login/')

    def test_chofer_no_entra(self):
        self.entrar(CHOFER)
        self.assertEqual(self.client.get('/pedidos/').status_code, 403)

    def test_login_del_cliente_va_a_sus_pedidos(self):
        r = self.client.post('/login/', {'usuario': 'gomezm', 'clave': 'Cliente123!'})
        self.assertRedirects(r, '/pedidos/')

    def test_el_portal_manda_al_cliente_a_sus_pedidos(self):
        self.entrar(CLIENTE)
        self.assertRedirects(self.client.get('/portal/'), '/pedidos/')


class ConsultaTest(BaseVistas):
    def setUp(self):
        self.mio = self.pedido_de(self.cliente)
        self.ajeno = self.pedido_de(self.otro, dias=2)

    def test_el_cliente_ve_solo_los_suyos(self):
        self.entrar(CLIENTE)
        r = self.client.get('/pedidos/')
        ids = [p.pk for p in r.context['pedidos']]
        self.assertIn(self.mio.pk, ids)
        self.assertNotIn(self.ajeno.pk, ids)
        self.assertNotIn('cliente', r.context['form'].fields)

    def test_el_admin_ve_todos_y_filtra_por_cliente(self):
        self.entrar(ADMIN)
        r = self.client.get('/pedidos/')
        self.assertEqual(len(r.context['pedidos']), 3)
        r = self.client.get('/pedidos/', {'cliente': self.otro.id_usuario})
        self.assertEqual([p.pk for p in r.context['pedidos']], [self.ajeno.pk])

    def test_filtros_por_fecha_estado_y_servicio(self):
        self.entrar(ADMIN)
        hoy = timezone.localdate()
        r = self.client.get('/pedidos/', {'desde': (hoy + timedelta(days=2)).isoformat(),
                                          'estado': 'Pendiente', 'servicio': self.local.id_servicio})
        self.assertEqual([p.pk for p in r.context['pedidos']], [self.ajeno.pk])

    def test_detalle_propio(self):
        self.entrar(CLIENTE)
        r = self.client.get(f'/pedidos/{self.mio.pk}/')
        self.assertContains(r, 'Origen 1')
        self.assertContains(r, 'Pendiente')

    def test_detalle_ajeno_da_404(self):
        self.entrar(CLIENTE)
        self.assertEqual(self.client.get(f'/pedidos/{self.ajeno.pk}/').status_code, 404)

    def test_el_admin_ve_cualquier_detalle(self):
        self.entrar(ADMIN)
        self.assertEqual(self.client.get(f'/pedidos/{self.ajeno.pk}/').status_code, 200)


class RegistrarPantallaTest(BaseVistas):
    def datos(self, **cambios):
        manana = (timezone.localdate() + timedelta(days=1)).isoformat()
        d = {'fecha_servicio': manana, 'hora_servicio': '10:15', 'origen': 'Av. Belgrano 100',
             'destino': 'Mitre 50', 'servicio': self.local.id_servicio, 'vehiculo': 'AD-321-JK',
             'inv-TOTAL_FORMS': '2', 'inv-INITIAL_FORMS': '0', 'inv-MIN_NUM_FORMS': '1', 'inv-MAX_NUM_FORMS': '50',
             'inv-0-objeto': id_obj('Heladera'), 'inv-0-cantidad': '1', 'inv-0-fragil': 'on',
             'inv-1-objeto': id_obj('Cajas'), 'inv-1-cantidad': '10'}
        d.update(cambios)
        return d

    def test_el_cliente_registra_y_va_al_detalle(self):
        self.entrar(CLIENTE)
        r = self.client.post('/pedidos/nuevo/', self.datos())
        p = Pedido.objects.latest('id_pedido')
        self.assertRedirects(r, f'/pedidos/{p.pk}/', fetch_redirect_response=False)
        self.assertEqual((p.idUsuario, p.estado, p.total), (self.cliente, 'Pendiente', 185000))
        self.assertEqual(p.hora_servicio, time(10, 15))
        self.assertEqual(p.detalles.get().idServicio, self.local)
        self.assertEqual(p.inventario.count(), 2)
        detalle = self.client.get(r.url)
        self.assertContains(detalle, f'Pedido N° {p.pk} registrado')
        self.assertContains(detalle, 'a las 10:15')
        self.assertContains(self.client.get('/pedidos/'), '10:15')

    def test_el_formulario_ofrece_un_servicio_y_la_lista_de_objetos(self):
        self.entrar(CLIENTE)
        r = self.client.get('/pedidos/nuevo/')
        self.assertContains(r, 'type="radio"')
        self.assertContains(r, 'name="hora_servicio"')
        self.assertContains(r, '<select name="inv-0-objeto"')
        bolsos = id_obj('Bolsos y valijas')
        self.assertContains(r, f'<option value="{bolsos}">Bolsos y valijas</option>', html=True)
        self.assertNotContains(r, '<datalist')  # ya no se escribe el nombre
        self.assertContains(r, 'name="inv-0-observacion"')
        self.assertNotContains(r, 'Peso total')

    def test_registra_con_adicionales_y_el_comprobante_los_lista(self):
        self.entrar(CLIENTE)
        embalaje = Servicio.objects.get(Tipo_servicio='Embalaje')
        self.client.post('/pedidos/nuevo/', self.datos(adicionales=[embalaje.id_servicio]))
        p = Pedido.objects.latest('id_pedido')
        self.assertEqual(p.total, 185000)
        self.assertEqual([d.idServicio for d in p.detalles.all()], [self.local, embalaje])
        r = self.client.get(f'/pedidos/{p.pk}/comprobante/')
        self.assertContains(r, 'Mudanza local')
        self.assertContains(r, 'Embalaje <i>(adicional)</i>', html=True)

    def test_el_formulario_separa_principales_de_adicionales(self):
        self.entrar(CLIENTE)
        r = self.client.get('/pedidos/nuevo/')
        principales = [str(s) for s in r.context['servicios']]
        adicionales = [str(s) for s in r.context['adicionales']]
        self.assertIn('Flete urbano', principales)
        self.assertNotIn('Embalaje', principales)
        self.assertIn('Embalaje', adicionales)
        self.assertContains(r, 'type="checkbox" name="adicionales"')
        self.assertContains(r, '>Embalaje</label>')  # sin precio

    def test_otro_con_observacion(self):
        self.entrar(CLIENTE)
        r = self.client.post('/pedidos/nuevo/', self.datos(**{
            'inv-0-objeto': id_obj('Otro'), 'inv-0-observacion': 'Piano vertical, se desarma'}))
        p = Pedido.objects.latest('id_pedido')
        self.assertRedirects(r, f'/pedidos/{p.pk}/', fetch_redirect_response=False)
        self.assertTrue(p.inventario.filter(idObjeto__nom_objeto='Otro',
                                            Observacion='Piano vertical, se desarma').exists())
        self.assertContains(self.client.get(r.url), 'Piano vertical, se desarma')
        self.assertContains(self.client.get(f'/pedidos/{p.pk}/comprobante/'), 'Piano vertical, se desarma')

    def test_un_nombre_escrito_a_mano_no_se_acepta(self):
        self.entrar(CLIENTE)
        antes = Pedido.objects.count()
        r = self.client.post('/pedidos/nuevo/', self.datos(**{'inv-0-objeto': 'Meza'}))
        self.assertEqual(r.status_code, 200)
        self.assertEqual(Pedido.objects.count(), antes)

    def test_error_de_reglas_vuelve_al_formulario_con_los_datos(self):
        self.entrar(CLIENTE)
        self.pedido_de(self.otro)  # ocupa AD-321-JK mañana
        antes = Pedido.objects.count()
        r = self.client.post('/pedidos/nuevo/', self.datos())
        self.assertEqual(r.status_code, 200)
        self.assertIn('vehiculo', r.context['form'].errors)
        self.assertContains(r, 'Av. Belgrano 100')
        self.assertEqual(Pedido.objects.count(), antes)

    def test_sin_objetos(self):
        self.entrar(CLIENTE)
        r = self.client.post('/pedidos/nuevo/', self.datos(**{
            'inv-TOTAL_FORMS': '1', 'inv-0-objeto': '', 'inv-0-cantidad': ''}))
        self.assertEqual(r.status_code, 200)
        self.assertTrue(r.context['items'].non_form_errors() or r.context['items'].errors[0])

    def test_el_admin_no_registra(self):
        self.entrar(ADMIN)
        self.assertEqual(self.client.get('/pedidos/nuevo/').status_code, 403)

    def test_vehiculos_libres_en_json(self):
        self.entrar(CLIENTE)
        self.pedido_de(self.otro)  # ocupa AD-321-JK mañana
        manana = (timezone.localdate() + timedelta(days=1)).isoformat()
        r = self.client.get('/pedidos/vehiculos-libres/', {'fecha': manana}).json()
        self.assertEqual([v['patente'] for v in r['vehiculos']], ['AE-123-CD'])
        self.assertEqual(r['vehiculos'][0]['capacidad_kg'], 5000.0)
        self.assertIn('capacidad_m3', r['vehiculos'][0])
        self.assertEqual(self.client.get('/pedidos/vehiculos-libres/', {'fecha': 'mal'}).json(), {'vehiculos': []})


class AccionesTest(BaseVistas):
    def setUp(self):
        self.p = self.pedido_de(self.cliente)

    def test_el_admin_confirma_y_finaliza(self):
        self.entrar(ADMIN)
        self.assertRedirects(self.client.post(f'/pedidos/{self.p.pk}/confirmar/'), f'/pedidos/{self.p.pk}/')
        inicio = timezone.make_aware(datetime.combine(self.p.fecha_servicio, self.p.hora_servicio))
        with mock.patch('django.utils.timezone.now', return_value=inicio + timedelta(hours=1)):
            self.assertContains(self.client.get(f'/pedidos/{self.p.pk}/'), '/finalizar/')
            self.client.post(f'/pedidos/{self.p.pk}/finalizar/')
        self.assertEqual(Pedido.objects.get(pk=self.p.pk).estado, 'Finalizado')

    def test_antes_de_la_mudanza_no_hay_boton_finalizar(self):
        self.entrar(ADMIN)
        reglas.confirmar(self.p.pk)
        r = self.client.get(f'/pedidos/{self.p.pk}/')
        self.assertNotContains(r, '/finalizar/')
        self.assertContains(r, 'Se puede finalizar desde el')
        r = self.client.post(f'/pedidos/{self.p.pk}/finalizar/', follow=True)
        self.assertContains(r, 'La mudanza todavía no empezó')
        self.assertEqual(Pedido.objects.get(pk=self.p.pk).estado, 'Confirmado')

    def test_transicion_invalida_muestra_el_error(self):
        self.entrar(ADMIN)
        r = self.client.post(f'/pedidos/{self.p.pk}/finalizar/', follow=True)
        self.assertContains(r, 'No se puede finalizar')
        self.assertEqual(Pedido.objects.get(pk=self.p.pk).estado, 'Pendiente')

    def test_las_acciones_son_solo_por_post(self):
        self.entrar(ADMIN)
        self.assertEqual(self.client.get(f'/pedidos/{self.p.pk}/confirmar/').status_code, 405)

    def test_el_admin_anula_con_motivo(self):
        self.entrar(ADMIN)
        self.assertContains(self.client.get(f'/pedidos/{self.p.pk}/anular/'), 'Motivo')
        r = self.client.post(f'/pedidos/{self.p.pk}/anular/', {'motivo': 'Pedido duplicado'})
        self.assertRedirects(r, f'/pedidos/{self.p.pk}/')
        p = Pedido.objects.get(pk=self.p.pk)
        self.assertEqual((p.estado, p.motivo_anulacion, p.usuario_anulacion.DNI), ('Anulado', 'Pedido duplicado', ADMIN))

    def test_motivo_corto(self):
        self.entrar(ADMIN)
        r = self.client.post(f'/pedidos/{self.p.pk}/anular/', {'motivo': 'no'})
        self.assertEqual(r.status_code, 200)
        self.assertIn('motivo', r.context['form'].errors)
        self.assertEqual(Pedido.objects.get(pk=self.p.pk).estado, 'Pendiente')

    def test_el_cliente_no_confirma_ni_anula(self):
        self.entrar(CLIENTE)
        self.assertEqual(self.client.post(f'/pedidos/{self.p.pk}/confirmar/').status_code, 403)
        self.assertEqual(self.client.post(f'/pedidos/{self.p.pk}/anular/', {'motivo': 'Me arrepentí'}).status_code, 403)
        self.assertEqual(Pedido.objects.get(pk=self.p.pk).estado, 'Pendiente')

    def test_un_cliente_con_ped_anular_no_anula_un_pedido_ajeno(self):
        from usuarios.models import Permiso, PermisoRol
        PermisoRol.objects.create(idRol=Rol.objects.get(nom_rol='Cliente'),
                                  idPermiso=Permiso.objects.get(nom_permiso='PED_ANULAR'))
        self.entrar(self.otro.DNI)
        self.assertEqual(self.client.get(f'/pedidos/{self.p.pk}/anular/').status_code, 404)
        r = self.client.post(f'/pedidos/{self.p.pk}/anular/', {'motivo': 'Lo anulo yo'})
        self.assertEqual(r.status_code, 404)
        p = Pedido.objects.get(pk=self.p.pk)
        self.assertEqual((p.estado, p.motivo_anulacion), ('Pendiente', None))

    def test_botones_segun_el_perfil(self):
        self.entrar(ADMIN)
        r = self.client.get(f'/pedidos/{self.p.pk}/')
        self.assertContains(r, 'Confirmar')
        self.assertContains(r, 'Anular')
        self.entrar(CLIENTE)
        r = self.client.get(f'/pedidos/{self.p.pk}/')
        self.assertNotContains(r, '/confirmar/')
        self.assertNotContains(r, '/anular/')


class ComprobanteTest(BaseVistas):
    def setUp(self):
        self.p = self.pedido_de(self.cliente)

    def test_el_cliente_imprime_el_suyo(self):
        self.entrar(CLIENTE)
        r = self.client.get(f'/pedidos/{self.p.pk}/comprobante/')
        self.assertContains(r, f'Pedido N° {self.p.pk}')
        self.assertContains(r, 'Mudanza local')
        self.assertContains(r, '185.000,00')
        self.assertContains(r, 'a las 09:00')
        self.assertNotContains(r, 'Peso total')
        self.assertContains(r, 'window.print()')

    def test_el_comprobante_ajeno_da_404(self):
        ajeno = self.pedido_de(self.otro, dias=2)
        self.entrar(CLIENTE)
        self.assertEqual(self.client.get(f'/pedidos/{ajeno.pk}/comprobante/').status_code, 404)

    def test_muestra_la_anulacion(self):
        reglas.anular(self.p.pk, Usuario.objects.get(DNI=ADMIN), 'Pedido duplicado')
        self.entrar(ADMIN)
        r = self.client.get(f'/pedidos/{self.p.pk}/comprobante/')
        self.assertContains(r, 'ANULADO')
        self.assertContains(r, 'Pedido duplicado')

    def test_el_chofer_no_emite(self):
        self.entrar(CHOFER)
        self.assertEqual(self.client.get(f'/pedidos/{self.p.pk}/comprobante/').status_code, 403)


class RegistroClienteTest(BaseVistas):
    def datos(self, **cambios):
        d = {'dni': '33444555', 'apellido': 'Herrera', 'nombre': 'Juan Pablo', 'correo': 'JP@Mail.com',
             'telefono': '3874000000', 'clave': 'Cliente123!', 'clave2': 'Cliente123!'}
        d.update(cambios)
        return d

    def test_crea_la_cuenta_y_entra(self):
        r = self.client.post('/registro/', self.datos())
        self.assertRedirects(r, '/pedidos/')
        u = Usuario.objects.get(DNI=33444555)
        self.assertEqual(u.NombreUsuario, 'herreraj1')  # herreraj ya existe
        self.assertEqual((u.idRol.nom_rol, u.DebeCambiarClave, u.Correo), ('Cliente', False, 'jp@mail.com'))
        self.assertTrue(u.verificar_clave('Cliente123!'))
        self.assertNotEqual(u.Clave, 'Cliente123!')
        self.assertEqual(self.client.session['usuario_dni'], 33444555)

    def test_rechaza_repetidos_y_clave_debil(self):
        for cambios, campo in [({'dni': str(CLIENTE)}, 'dni'),
                               ({'correo': 'maria.gomez@ejemplo.com'}, 'correo'),
                               ({'clave': 'debil', 'clave2': 'debil'}, 'clave'),
                               ({'clave2': 'Otra123!'}, 'clave2')]:
            r = self.client.post('/registro/', self.datos(**cambios))
            self.assertEqual(r.status_code, 200, cambios)
            self.assertIn(campo, r.context['form'].errors, cambios)
        self.assertFalse(Usuario.objects.filter(DNI=33444555).exists())

    def test_el_login_ofrece_crear_cuenta(self):
        self.assertContains(self.client.get('/login/'), '/registro/')


class RevisionFinalTest(BaseVistas):
    def test_el_filtro_rechaza_un_rango_invertido(self):
        self.entrar(ADMIN)
        hoy = timezone.localdate()
        r = self.client.get('/pedidos/', {'desde': hoy + timedelta(days=5), 'hasta': hoy + timedelta(days=1)})
        self.assertIn('hasta', r.context['form'].errors)

    def test_no_se_ofrece_anular_un_pedido_ya_anulado(self):
        p = self.pedido_de(self.cliente)
        reglas.anular(p.pk, Usuario.objects.get(DNI=ADMIN), 'Pedido duplicado')
        self.entrar(ADMIN)
        self.assertRedirects(self.client.get(f'/pedidos/{p.pk}/anular/'), f'/pedidos/{p.pk}/')

    def test_registro_con_sesion_abierta_redirige(self):
        self.entrar(CLIENTE)
        self.assertRedirects(self.client.get('/registro/'), '/pedidos/')

    def test_registro_rota_la_sesion(self):
        s = self.client.session
        s['visita'] = 1
        s.save()
        antes = self.client.session.session_key
        datos = RegistroClienteTest.datos(self, dni='33444555')
        self.client.post('/registro/', datos)
        self.assertNotEqual(self.client.session.session_key, antes)
        self.assertEqual(self.client.session['usuario_dni'], 33444555)


class DescargasPdfTest(BaseVistas):
    def setUp(self):
        self.mio = self.pedido_de(self.cliente)
        self.ajeno = self.pedido_de(self.otro, dias=2)

    def assertEsPdf(self, r, nombre):
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r['Content-Type'], 'application/pdf')
        self.assertEqual(r['Content-Disposition'], f'attachment; filename="{nombre}"')
        self.assertTrue(r.content.startswith(b'%PDF'))

    def test_comprobante_en_pdf(self):
        self.entrar(CLIENTE)
        r = self.client.get(f'/pedidos/{self.mio.pk}/comprobante/pdf/')
        self.assertEsPdf(r, f'Comprobante-pedido-{self.mio.pk}.pdf')

    def test_comprobante_ajeno_da_404(self):
        self.entrar(CLIENTE)
        self.assertEqual(self.client.get(f'/pedidos/{self.ajeno.pk}/comprobante/pdf/').status_code, 404)

    def test_el_chofer_no_descarga_el_comprobante(self):
        self.entrar(CHOFER)
        self.assertEqual(self.client.get(f'/pedidos/{self.mio.pk}/comprobante/pdf/').status_code, 403)

    def test_botones_de_descarga(self):
        self.entrar(CLIENTE)
        self.assertContains(self.client.get(f'/pedidos/{self.mio.pk}/comprobante/'),
                            f'/pedidos/{self.mio.pk}/comprobante/pdf/')
        self.assertContains(self.client.get(f'/pedidos/{self.mio.pk}/'), f'/pedidos/{self.mio.pk}/comprobante/pdf/')
        self.assertContains(self.client.get('/pedidos/', {'estado': 'Pendiente'}),
                            '/pedidos/descargar/?estado=Pendiente')

    def test_lista_en_pdf_con_los_filtros(self):
        self.entrar(ADMIN)
        r = self.client.get('/pedidos/descargar/', {'estado': 'Pendiente', 'servicio': self.local.id_servicio})
        self.assertEsPdf(r, 'Pedidos.pdf')
        self.assertEqual(sorted(p.pk for p in r.context['pedidos']), sorted([self.mio.pk, self.ajeno.pk]))
        self.assertIn(('Estado', 'Pendiente'), r.context['filtros_usados'])

    def test_el_cliente_descarga_solo_los_suyos(self):
        self.entrar(CLIENTE)
        r = self.client.get('/pedidos/descargar/')
        ids = [p.pk for p in r.context['pedidos']]
        self.assertIn(self.mio.pk, ids)
        self.assertNotIn(self.ajeno.pk, ids)

    def test_la_lista_pdf_pide_sesion_y_permiso(self):
        self.assertRedirects(self.client.get('/pedidos/descargar/'), '/login/')
        self.entrar(CHOFER)
        self.assertEqual(self.client.get('/pedidos/descargar/').status_code, 403)


class VencidosPantallaTest(BaseVistas):
    def setUp(self):
        self.p = self.pedido_de(self.cliente)
        Pedido.objects.filter(pk=self.p.pk).update(fecha_servicio=timezone.localdate() - timedelta(days=2))

    def test_la_lista_avisa_y_filtra(self):
        self.entrar(ADMIN)
        r = self.client.get('/pedidos/')
        self.assertContains(r, 'vencido')
        self.assertContains(r, 'href="/pedidos/?estado=Vencido"')
        r = self.client.get('/pedidos/', {'estado': 'Vencido'})
        self.assertEqual([p.pk for p in r.context['pedidos']], [self.p.pk])

    def test_el_detalle_no_ofrece_confirmar(self):
        self.entrar(ADMIN)
        r = self.client.get(f'/pedidos/{self.p.pk}/')
        self.assertContains(r, 'Pedido vencido')
        self.assertNotContains(r, f'action="/pedidos/{self.p.pk}/confirmar/"')
        self.client.post(f'/pedidos/{self.p.pk}/confirmar/')
        self.p.refresh_from_db()
        self.assertEqual(self.p.estado, 'Pendiente')

    def test_el_cliente_ve_la_marca_pero_no_el_aviso_general(self):
        self.entrar(CLIENTE)
        r = self.client.get('/pedidos/')
        self.assertContains(r, '>Vencido</span>')
        self.assertNotContains(r, 'Ver vencidos')


class AvisosPantallaTest(BaseVistas):
    def test_la_lista_muestra_los_tres_avisos(self):
        hecho = self.pedido_de(self.cliente)
        reglas.confirmar(hecho.pk)
        Pedido.objects.filter(pk=hecho.pk).update(fecha_servicio=timezone.localdate() - timedelta(days=1))
        self.pedido_de(self.otro, dias=2)  # pendiente cercano
        vencido = self.pedido_de(self.otro, dias=5, patente='AE-123-CD')
        Pedido.objects.filter(pk=vencido.pk).update(fecha_servicio=timezone.localdate() - timedelta(days=3))
        self.entrar(ADMIN)
        r = self.client.get('/pedidos/')
        self.assertContains(r, '1</b> mudanza confirmada ya pasó')
        self.assertContains(r, 'href="/pedidos/?estado=Para+finalizar"')
        self.assertContains(r, 'href="/pedidos/?estado=Por+confirmar"')
        self.assertContains(r, 'href="/pedidos/?estado=Vencido"')
        self.assertContains(r, '>Para finalizar</span>')

    def test_sin_avisos_no_muestra_nada(self):
        self.entrar(ADMIN)
        r = self.client.get('/pedidos/')
        self.assertNotContains(r, 'Ver para finalizar')
        self.assertNotContains(r, 'Ver por confirmar')
