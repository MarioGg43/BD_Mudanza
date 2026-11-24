"""Los datos que escribe la gente: lo que se acepta, cómo queda guardado y lo que se rechaza
(DNI, nombres, teléfono, correo, patente, nombres del catálogo y motivos)."""
import io

from django.core.management import call_command
from django.test import TestCase

from usuarios import validaciones as v
from usuarios.models import Rol, Usuario, Vehiculo

ADMIN = 35123456


class ReglasTest(TestCase):
    def rechaza(self, funcion, *valores, **kwargs):
        for valor in valores:
            with self.assertRaises(v.DatoInvalido, msg=repr(valor)):
                funcion(valor, **kwargs)

    def test_dni(self):
        self.assertEqual(v.dni(' 42123456 '), 42123456)
        self.assertEqual(v.dni(1234567), 1234567)
        self.rechaza(v.dni, '', '42.123.456', '1231235678', '123456', '42a23456')

    def test_nombre_y_apellido(self):
        self.assertEqual(v.persona('  maría   de la paz '), 'María de la Paz')
        self.assertEqual(v.persona("o'brien"), "O'Brien")
        self.assertEqual(v.persona('pérez-gómez'), 'Pérez-Gómez')
        self.rechaza(v.persona, '', 'mario12', 'flores123', 'a', 'aaaa', 'Bcdfg', 'Juan_Carlos', 'x' * 51)

    def test_telefono(self):
        self.assertEqual(v.telefono('387 4112233'), '387 4112233')
        self.assertEqual(v.telefono('+54 9 387 411-2233'), '+54 9 387 411-2233')
        # con el código del país que agrega el selector de la pantalla (Chile, Uruguay)
        self.assertEqual(v.telefono('+56 9 1234 5678'), '+56 9 1234 5678')
        self.assertEqual(v.telefono('+598 9123 4567'), '+598 9123 4567')
        self.assertIsNone(v.telefono('  '))
        self.rechaza(v.telefono, 'fernandezl', '4112233', '12345678901234', '387+4112233')
        with self.assertRaises(v.DatoInvalido):
            v.telefono('', obligatorio=True)

    def test_correo(self):
        self.assertEqual(v.correo(' Juan.Gomez@Gmail.COM '), 'juan.gomez@gmail.com')
        self.rechaza(v.correo, '', 'juan', 'juan@', 'juan@gmail', 'juan gomez@gmail.com')

    def test_patente(self):
        self.assertEqual(v.patente('ab 123 cd'), 'AB123CD')
        self.assertEqual(v.patente('abc123'), 'ABC123')
        self.assertEqual(v.patente('ae-123-cd'), 'AE-123-CD')
        self.rechaza(v.patente, '', '123', 'ABCD1234', 'A1B2C3', 'AB12CD')

    def test_nombres_del_catalogo_y_textos(self):
        self.assertEqual(v.nombre_de_algo('  Camión   3/4 '), 'Camión 3/4')
        self.rechaza(v.nombre_de_algo, '', '12345', '...', 'aaaaaa')
        self.assertEqual(v.texto_con_sentido('Se rompió el camión'), 'Se rompió el camión')
        self.rechaza(v.texto_con_sentido, '.....', '12345', 'aaaaa')


class PantallasTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command('init_data', stdout=io.StringIO())

    def entrar(self, dni):
        s = self.client.session
        s['usuario_dni'] = dni
        s.save()

    def datos(self, **cambios):
        base = {'dni': '30111222', 'apellido': 'pérez', 'nombre': 'ana laura', 'correo': 'Ana@Mail.com',
                'telefono': '387 4112233', 'clave': 'Cliente123!', 'clave2': 'Cliente123!'}
        base.update(cambios)
        return base

    def test_crear_cuenta_rechaza_lo_que_no_tiene_sentido(self):
        # el caso de la exposición: DNI de 10 números, números en el nombre y el usuario en el teléfono
        r = self.client.post('/registro/', self.datos(dni='1231235678', apellido='mario12', nombre='flores123',
                                                       telefono='fernandezl'))
        self.assertEqual(r.status_code, 200)
        for mensaje in ('El DNI tiene 7 u 8 números.', 'El apellido lleva solo letras',
                        'El nombre lleva solo letras', 'El teléfono lleva solo números'):
            self.assertContains(r, mensaje)
        self.assertFalse(Usuario.objects.filter(Correo='ana@mail.com').exists())

    def test_crear_cuenta_guarda_los_datos_prolijos(self):
        from pedidos.test_vistas import registrar_y_confirmar
        self.assertRedirects(registrar_y_confirmar(self.client, self.datos()), '/pedidos/', fetch_redirect_response=False)
        u = Usuario.objects.get(DNI=30111222)
        self.assertEqual((u.Apellido, u.Nombre, u.Correo, u.Telefono),
                         ('Pérez', 'Ana Laura', 'ana@mail.com', '387 4112233'))

    def test_alta_del_administrador_sin_errores_tecnicos(self):
        self.entrar(ADMIN)
        rol = Rol.objects.get(nom_rol='Chofer').id_rol
        r = self.client.post('/usuarios/alta/', {'dni': '42a', 'apellido': 'Gómez', 'nombre': 'Juan',
                                                 'correo': 'juan@mail.com', 'clave': 'Chofer123!', 'idRol': rol})
        self.assertEqual(r.status_code, 400)
        self.assertEqual(r.json()['error'], 'El DNI lleva solo números, sin puntos ni espacios.')
        r = self.client.post('/usuarios/alta/', {'dni': '42123456', 'apellido': 'Gomez1', 'nombre': 'Juan',
                                                 'correo': 'juan@mail.com', 'clave': 'Chofer123!', 'idRol': rol})
        self.assertIn('El apellido lleva solo letras', r.json()['error'])
        self.assertFalse(Usuario.objects.filter(DNI=42123456).exists())

    def test_las_pantallas_de_tailwind_muestran_el_aviso_de_lo_que_se_hizo(self):
        # Usuarios, el portal del chofer y «Terminamos» usan la otra plantilla base: antes no mostraban los avisos
        self.entrar(ADMIN)
        self.assertTrue(self.client.post('/usuarios/40987654/reactivar/').json()['ok'])
        r = self.client.get('/panel/')
        self.assertContains(r, 'id="avisos"')
        self.assertContains(r, 'está activo otra vez.')

    def test_solo_activos_se_queda_en_usuarios(self):
        # antes llevaba a «/», que ahora es la página de la empresa
        self.entrar(ADMIN)
        Usuario.objects.filter(DNI=40987654).update(Activo=False)
        r = self.client.get('/panel/')
        self.assertNotContains(r, "'/?activos=1'")
        self.assertContains(r, 'url.searchParams.set(\'activos\'')
        self.assertIn(40987654, [u.DNI for u in r.context['usuarios']])
        self.assertNotIn(40987654, [u.DNI for u in self.client.get('/panel/?activos=1').context['usuarios']])

    def test_patente_con_formato_y_sin_repetir_aunque_cambien_los_guiones(self):
        from vehiculos.forms import VehiculoForm
        base = {'marca_modelo': 'Fiat Ducato', 'tipo_vehiculo': 'Camión Chico', 'capacidad_kg': '1500',
                'capacidad_m3': '10', 'estado': 'Disponible', 'kilometraje': '0', 'anio': '2024'}
        existente = Vehiculo.objects.first().patente
        for patente, error in (('12', 'La patente es como'), (existente.replace('-', ''), 'Ya hay un vehículo')):
            form = VehiculoForm({**base, 'patente': patente})
            self.assertFalse(form.is_valid())
            self.assertIn(error, form.errors['patente'][0])
        form = VehiculoForm({**base, 'patente': 'zz 999 zz', 'marca_modelo': '1234'})
        self.assertFalse(form.is_valid())
        self.assertIn('marca_modelo', form.errors)
