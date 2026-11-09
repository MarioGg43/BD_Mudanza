"""ABM de roles y sus candados."""
import io

from django.core.management import call_command
from django.test import TestCase

from usuarios.models import PermisoRol, Rol, Usuario

ADMIN, CHOFER, CLIENTE = 35123456, 40987654, 29876543


def codigos(rol):
    return set(PermisoRol.objects.filter(idRol=rol).values_list('idPermiso__nom_permiso', flat=True))


class RolesTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command('init_data', stdout=io.StringIO())

    def setUp(self):
        s = self.client.session
        s['usuario_dni'] = ADMIN
        s.save()

    def test_lista_con_permisos_y_usuarios(self):
        r = self.client.get('/roles/')
        self.assertContains(r, 'Administrador')
        self.assertContains(r, 'title="ROL_GESTIONAR"')        # el código, al pasar el mouse
        self.assertContains(r, 'Ver, crear y editar roles y sus permisos')  # lo que se lee
        self.assertContains(r, '18 permisos')                     # el administrador (todos menos registrar pedidos), plegado
        self.assertContains(r, 'Registrar pedidos de mudanza')    # el cliente, a la vista
        self.assertContains(r, 'Nuevo rol')

    def test_crear_rol_con_permisos(self):
        r = self.client.post('/roles/nuevo/', {'nombre': 'Recepcionista', 'descripcion': 'Atiende',
                                               'permisos': ['USR_CONSULTAR', 'PED_CONSULTAR']})
        self.assertRedirects(r, '/roles/')
        self.assertEqual(codigos(Rol.objects.get(nom_rol='Recepcionista')), {'USR_CONSULTAR', 'PED_CONSULTAR'})

    def test_editar_permisos(self):
        rol = Rol.objects.create(nom_rol='Recepcionista')
        self.client.post(f'/roles/{rol.pk}/editar/', {'nombre': 'Recepción', 'permisos': ['PED_GESTIONAR']})
        rol.refresh_from_db()
        self.assertEqual((rol.nom_rol, codigos(rol)), ('Recepción', {'PED_GESTIONAR'}))

    def test_nombre_repetido(self):
        r = self.client.post('/roles/nuevo/', {'nombre': 'chofer', 'permisos': []})
        self.assertIn('nombre', r.context['form'].errors)

    def test_no_se_renombra_un_rol_del_sistema(self):
        cliente = Rol.objects.get(nom_rol='Cliente')
        r = self.client.post(f'/roles/{cliente.pk}/editar/', {'nombre': 'Clientes', 'permisos': ['PED_CONSULTAR']})
        self.assertIn('nombre', r.context['form'].errors)
        self.assertTrue(Rol.objects.filter(nom_rol='Cliente').exists())

    def test_se_editan_los_permisos_de_un_rol_del_sistema(self):
        chofer = Rol.objects.get(nom_rol='Chofer')
        self.client.post(f'/roles/{chofer.pk}/editar/', {'nombre': 'Chofer',
                                                          'permisos': ['MUDANZAS_OPERAR', 'PED_CONSULTAR']})
        self.assertEqual(codigos(chofer), {'MUDANZAS_OPERAR', 'PED_CONSULTAR'})

    def test_eliminar_rol_sin_usuarios(self):
        rol = Rol.objects.create(nom_rol='Temporal')
        self.assertRedirects(self.client.post(f'/roles/{rol.pk}/eliminar/'), '/roles/')
        self.assertFalse(Rol.objects.filter(pk=rol.pk).exists())

    def test_no_se_elimina_con_usuarios_ni_del_sistema(self):
        ayudante = Rol.objects.get(nom_rol='Ayudante de Carga')  # tiene a romerol
        self.client.post(f'/roles/{ayudante.pk}/eliminar/')
        self.assertTrue(Rol.objects.filter(pk=ayudante.pk).exists())
        chofer_sin_usuarios = Rol.objects.get(nom_rol='Chofer')
        Usuario.objects.filter(idRol=chofer_sin_usuarios).update(idRol=ayudante)
        self.client.post(f'/roles/{chofer_sin_usuarios.pk}/eliminar/')
        self.assertTrue(Rol.objects.filter(pk=chofer_sin_usuarios.pk).exists())

    def test_eliminar_solo_por_post(self):
        rol = Rol.objects.create(nom_rol='Temporal')
        self.assertEqual(self.client.get(f'/roles/{rol.pk}/eliminar/').status_code, 405)

    def test_no_te_podes_quitar_rol_gestionar(self):
        admin = Rol.objects.get(nom_rol='Administrador')
        r = self.client.post(f'/roles/{admin.pk}/editar/', {'nombre': 'Administrador', 'permisos': ['USR_CONSULTAR']})
        self.assertIn('No podés quitarte el permiso de gestionar roles.', r.context['form'].errors['permisos'])
        self.assertIn('ROL_GESTIONAR', codigos(admin))

    def test_solo_con_rol_gestionar(self):
        s = self.client.session
        s['usuario_dni'] = CLIENTE
        s.save()
        self.assertEqual(self.client.get('/roles/').status_code, 403)

    def test_menu_muestra_roles_al_admin(self):
        self.assertContains(self.client.get('/pedidos/'), 'href="/roles/"')

    def test_regla_sin_gestor_al_editar(self):
        from usuarios.reglas_roles import ErrorRol, MENSAJE_SIN_GESTOR, guardar_rol
        from usuarios.models import Permiso
        gestor = Rol.objects.create(nom_rol='Gestor')
        PermisoRol.objects.create(idRol=gestor, idPermiso=Permiso.objects.get(nom_permiso='ROL_GESTIONAR'))
        Usuario.objects.filter(DNI=CHOFER).update(idRol=gestor)
        admin_rol = Rol.objects.get(nom_rol='Administrador')
        PermisoRol.objects.filter(idRol=admin_rol, idPermiso__nom_permiso='ROL_GESTIONAR').delete()
        actor = Usuario.objects.get(DNI=ADMIN)  # ya no gestiona, pero lo usamos como actor de la regla
        with self.assertRaises(ErrorRol) as ctx:
            guardar_rol(gestor, 'Gestor', '', [], actor)
        self.assertEqual(ctx.exception.errores['permisos'], MENSAJE_SIN_GESTOR)

    def test_el_panel_tiene_un_solo_enlace_a_roles(self):
        self.assertEqual(self.client.get('/panel/').content.decode().count('href="/roles/"'), 1)

    def test_al_rol_cliente_no_se_le_dan_permisos_de_administracion(self):
        cliente = Rol.objects.get(nom_rol='Cliente')
        r = self.client.post(f'/roles/{cliente.pk}/editar/', {
            'nombre': 'Cliente', 'permisos': ['PED_REGISTRAR', 'PED_CONSULTAR', 'USR_CONSULTAR']})
        self.assertIn('Al rol Cliente solo se le pueden dar permisos sobre sus propios pedidos',
                      r.context['form'].errors['permisos'][0])
        self.assertNotIn('USR_CONSULTAR', codigos(cliente))
        r = self.client.post(f'/roles/{cliente.pk}/editar/', {
            'nombre': 'Cliente', 'permisos': ['PED_REGISTRAR', 'PED_CONSULTAR', 'PED_ANULAR', 'PED_COMPROBANTE']})
        self.assertRedirects(r, '/roles/')
