from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from .models import Perfil, Permiso, Usuario, PerfilPermiso, Vehiculo
from .utils import hash_password, generate_username, validate_strong_password

class Hito2RequerimientosTestCase(TestCase):
    def setUp(self):
        self.client = Client()

        # Perfiles
        self.perfil_admin = Perfil.objects.create(NombrePerfil='Administrador', Descripcion='Admin total')
        self.perfil_chofer = Perfil.objects.create(NombrePerfil='Chofer', Descripcion='Chofer de mudanzas')
        self.perfil_ayudante = Perfil.objects.create(NombrePerfil='Ayudante de Carga', Descripcion='Ayudante operativo')

        # Permisos
        self.perm_crear = Permiso.objects.create(NombrePermiso='USR_CREAR', Descripcion='Crear usuario')
        self.perm_operar = Permiso.objects.create(NombrePermiso='MUDANZAS_OPERAR', Descripcion='Operar mudanzas')

        PerfilPermiso.objects.create(idPerfil=self.perfil_admin, idPermiso=self.perm_crear)
        PerfilPermiso.objects.create(idPerfil=self.perfil_chofer, idPermiso=self.perm_operar)

        # Usuario Admin para sesión
        self.admin_user = Usuario.objects.create(
            DNI=30111222,
            Apellido='Admin',
            Nombre='Super',
            Correo='admin@mudanzassalta.com.ar',
            NombreUsuario='admins',
            Clave=hash_password('AdminPass123!'),
            Activo=True,
            DebeCambiarClave=False,
            idPerfil=self.perfil_admin
        )

    def test_01_generacion_automatica_nombre_usuario(self):
        """El nombre de usuario se genera automáticamente con Apellido + primera letra del primer nombre"""
        usr = generate_username('Saavedra', 'José')
        self.assertEqual(usr, 'saavedraj')

        usr2 = generate_username('Pérez García', 'Juan Carlos')
        self.assertEqual(usr2, 'perezj')

    def test_02_validacion_clave_robusta(self):
        """La clave debe tener 8+ caracteres, mayúscula, minúscula, número y caracter especial"""
        valida, _ = validate_strong_password('ClaveSegura123!')
        self.assertTrue(valida)

        # Menos de 8 caracteres
        valida, msg = validate_strong_password('Ab1!')
        self.assertFalse(valida)

        # Sin mayúscula
        valida, msg = validate_strong_password('clavesegura123!')
        self.assertFalse(valida)

        # Sin número
        valida, msg = validate_strong_password('ClaveSeguraExtra!')
        self.assertFalse(valida)

        # Sin caracter especial
        valida, msg = validate_strong_password('ClaveSegura123')
        self.assertFalse(valida)

    def test_03_alta_usuario_cumple_todas_las_condiciones(self):
        """Alta de usuario registra DNI numérico, hash SHA-256, Activo=True y DebeCambiarClave=True"""
        session = self.client.session
        session['usuario_dni'] = self.admin_user.DNI
        session['usuario_perfil'] = 'Administrador'
        session.save()

        response = self.client.post(reverse('alta_usuario'), {
            'dni': 44555666,
            'apellido': 'Flores',
            'nombre': 'Mario',
            'correo': 'mario.flores@mudanzassalta.com',
            'clave': 'PasswordSegura2026!',
            'idPerfil': self.perfil_chofer.idPerfil
        })
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['ok'])
        self.assertEqual(data['usuario'], 'floresm')

        # Verificar en base de datos
        usr = Usuario.objects.get(DNI=44555666)
        self.assertEqual(usr.NombreUsuario, 'floresm')
        self.assertEqual(usr.Clave, hash_password('PasswordSegura2026!'))
        self.assertTrue(usr.Activo)
        self.assertTrue(usr.DebeCambiarClave) # Debe exigir cambio en el primer login
        self.assertIsNotNone(usr.FechaUltimaModificacion)
        self.assertIsNone(usr.FechaBaja)

    def test_04_modificacion_solo_permite_editar_correo(self):
        """La modificación de usuario solo actualiza el correo y actualiza FechaUltimaModificacion"""
        usr = Usuario.objects.create(
            DNI=41222333,
            Apellido='Aramayo',
            Nombre='Mateo',
            Correo='mateo.original@test.com',
            NombreUsuario='aramayom',
            Clave=hash_password('Aramayo123!'),
            Activo=True,
            DebeCambiarClave=False,
            idPerfil=self.perfil_chofer
        )
        fecha_antigua = usr.FechaUltimaModificacion

        response = self.client.post(reverse('modificar_correo', args=[usr.DNI]), {
            'correo': 'mateo.nuevo@mudanzassalta.com'
        })
        self.assertEqual(response.status_code, 200)

        usr.refresh_from_db()
        self.assertEqual(usr.Correo, 'mateo.nuevo@mudanzassalta.com')
        # Apellido y nombre quedan inalterados
        self.assertEqual(usr.Apellido, 'Aramayo')
        self.assertEqual(usr.Nombre, 'Mateo')

    def test_05_baja_usuario_pasa_activo_a_no_y_asienta_fecha_baja(self):
        """Baja de usuario: cambia Activo a False y guarda FechaBaja"""
        usr = Usuario.objects.create(
            DNI=39888777,
            Apellido='Bravo',
            Nombre='Miqueas',
            Correo='bravom@test.com',
            NombreUsuario='bravom',
            Clave=hash_password('Bravo123!'),
            Activo=True,
            DebeCambiarClave=False,
            idPerfil=self.perfil_ayudante
        )
        self.assertTrue(usr.Activo)
        self.assertIsNone(usr.FechaBaja)

        response = self.client.post(reverse('baja_usuario', args=[usr.DNI]))
        self.assertEqual(response.status_code, 200)

        usr.refresh_from_db()
        self.assertFalse(usr.Activo)
        self.assertIsNotNone(usr.FechaBaja)

    def test_06_restablecer_clave_exige_cambio_en_proximo_login(self):
        """Restablecimiento de clave: asigna nueva clave con hash y pasa DebeCambiarClave a True"""
        usr = Usuario.objects.create(
            DNI=37111444,
            Apellido='Amador',
            Nombre='Lucas',
            Correo='amadorl@test.com',
            NombreUsuario='amadorl',
            Clave=hash_password('ClaveVieja123!'),
            Activo=True,
            DebeCambiarClave=False,
            idPerfil=self.perfil_chofer
        )

        response = self.client.post(reverse('restablecer_clave', args=[usr.DNI]), {
            'nueva_clave': 'NuevaTempClave2026!'
        })
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['ok'])

        usr.refresh_from_db()
        self.assertEqual(usr.Clave, hash_password('NuevaTempClave2026!'))
        self.assertTrue(usr.DebeCambiarClave)

    def test_07_login_interceptor_exige_cambio_de_clave(self):
        """Si DebeCambiarClave está en True, el Login no deja pasar hasta que el usuario cambie su clave"""
        Usuario.objects.create(
            DNI=36000111,
            Apellido='Tester',
            Nombre='Juan',
            Correo='tester@test.com',
            NombreUsuario='testerj',
            Clave=hash_password('ClaveTemporal123!'),
            Activo=True,
            DebeCambiarClave=True,
            idPerfil=self.perfil_chofer
        )

        # Login con clave provisoria
        response = self.client.post(reverse('login'), {
            'usuario': 'testerj',
            'clave': 'ClaveTemporal123!'
        })
        # Debe renderizar pantalla exigiendo cambio obligatorio
        self.assertContains(response, 'Seguridad Obligatoria')
        self.assertContains(response, '36000111')

        # Enviar cambio de clave obligatorio
        cambio_resp = self.client.post(reverse('cambiar_clave_obligatoria'), {
            'dni': 36000111,
            'clave_actual': 'ClaveTemporal123!',
            'nueva_clave': 'Definitiva2026!',
            'confirmar_clave': 'Definitiva2026!'
        })
        self.assertEqual(cambio_resp.status_code, 302) # Redirige al portal

        usr = Usuario.objects.get(DNI=36000111)
        self.assertFalse(usr.DebeCambiarClave)
        self.assertEqual(usr.Clave, hash_password('Definitiva2026!'))

    def test_08_crud_vehiculos_continuidad_hito_1(self):
        """El módulo de Flota Vehicular permite alta, edición y baja lógica a Fuera de Servicio"""
        veh = Vehiculo.objects.create(
            patente='AB-123-CD',
            marca_modelo='Scania P310',
            tipo_vehiculo='Camión Pesado',
            capacidad_kg=12000.0,
            capacidad_m3=45.0,
            estado='Disponible',
            kilometraje=150000.0,
            anio=2021
        )
        self.assertEqual(veh.estado, 'Disponible')

        # Modificación
        resp = self.client.post(reverse('modificar_vehiculo', args=[veh.id_vehiculo]), {
            'marca_modelo': 'Scania P310 Semi',
            'tipo_vehiculo': 'Camión Pesado',
            'capacidad_kg': '14000',
            'capacidad_m3': '50',
            'estado': 'En Viaje',
            'kilometraje': '152000'
        })
        self.assertEqual(resp.status_code, 200)
        veh.refresh_from_db()
        self.assertEqual(veh.estado, 'En Viaje')
        self.assertEqual(veh.capacidad_kg, 14000.0)

        # Baja (Fuera de Servicio)
        resp_baja = self.client.post(reverse('baja_vehiculo', args=[veh.id_vehiculo]))
        self.assertEqual(resp_baja.status_code, 200)
        veh.refresh_from_db()
        self.assertEqual(veh.estado, 'Fuera de Servicio')
