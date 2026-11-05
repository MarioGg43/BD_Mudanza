"""La API de los ABM: vehículos, servicios y objetos, con las mismas validaciones que Django."""
from pedidos.test_reglas import ADMIN, CLIENTE, obj
from usuarios.models import Objeto, Servicio, Vehiculo
from .tests import ApiBase

VEHICULO = {'patente': 'ab 123 cd', 'marca_modelo': 'Iveco Daily', 'tipo_vehiculo': 'Camión Mediano',
            'capacidad_kg': 3500, 'capacidad_m3': 20, 'estado': 'Disponible', 'kilometraje': 1000, 'anio': 2020,
            'chofer_asignado': None, 'observaciones': ''}


class ApiAbmTest(ApiBase):
    def setUp(self):
        super().setUp()
        self.h = self.entrar(str(ADMIN))

    def mandar(self, metodo, url, datos=None):
        return getattr(self.client, metodo)(url, datos or {}, content_type='application/json', **self.h)

    def test_vehiculo_alta_edicion_y_baja(self):
        r = self.mandar('post', '/api/vehiculos', VEHICULO)
        self.assertEqual(r.status_code, 201, r.content)
        self.assertEqual(r.json()['patente'], 'AB123CD')  # se guarda en mayúsculas y sin espacios
        r = self.mandar('post', '/api/vehiculos', {**VEHICULO, 'patente': 'XX1', 'capacidad_kg': 99999})
        self.assertIn('capacidad_kg', r.json()['errores'])
        r = self.mandar('put', '/api/vehiculos/AB123CD', {**VEHICULO, 'patente': 'OTRA', 'marca_modelo': 'Iveco 2'})
        self.assertEqual(r.status_code, 200, r.content)
        self.assertEqual(Vehiculo.objects.get(pk='AB123CD').marca_modelo, 'Iveco 2')
        self.assertFalse(Vehiculo.objects.filter(pk='OTRA').exists())  # la patente no cambia
        self.assertEqual(self.mandar('post', '/api/vehiculos/AB123CD/baja').status_code, 200)
        self.assertEqual(Vehiculo.objects.get(pk='AB123CD').estado, 'Fuera de Servicio')

    def test_no_baja_vehiculo_con_pedidos_activos(self):
        self.registrar()
        self.assertEqual(self.mandar('post', '/api/vehiculos/AD-321-JK/baja').status_code, 400)

    def test_lista_y_agenda_del_vehiculo(self):
        p = self.registrar()
        lista = self.client.get('/api/vehiculos', **self.h).json()
        self.assertIn('Camión Grande', lista['tipos'])
        d = self.client.get('/api/vehiculos/AD-321-JK', **self.h).json()
        self.assertIn(p.pk, [x['id'] for x in d['agenda']['proximos']])

    def test_servicio_alta_con_materiales_y_baja(self):
        r = self.mandar('post', '/api/servicios', {'Tipo_servicio': 'Guardamuebles', 'Categoria': 'Adicional',
                                                  'Precio_base': 15000, 'Activo': True, 'materiales': 'Film, cintas'})
        self.assertEqual(r.status_code, 201, r.content)
        self.assertEqual(r.json()['materiales'], 'Film, cintas')
        r = self.mandar('post', '/api/servicios', {'Tipo_servicio': 'Mal', 'Categoria': 'Principal',
                                                  'Precio_base': 0, 'Duracion_horas': 2, 'Activo': True})
        self.assertEqual(set(r.json()['errores']), {'Precio_base', 'Duracion_horas'})
        self.assertEqual(self.mandar('post', f'/api/servicios/{self.embalaje.pk}/baja').status_code, 200)
        self.assertFalse(Servicio.objects.get(pk=self.embalaje.pk).Activo)

    def test_objetos_sin_repetidos_y_otro_fijo(self):
        r = self.mandar('post', '/api/objetos', {'nom_objeto': 'piano', 'Activo': True})
        self.assertEqual((r.status_code, r.json()['nom_objeto']), (201, 'Piano'))
        r = self.mandar('post', '/api/objetos', {'nom_objeto': 'sillas', 'Activo': True})
        self.assertIn('nom_objeto', r.json()['errores'])  # ya existe «Sillas»
        otro = obj('Otro').pk
        self.assertEqual(self.mandar('post', f'/api/objetos/{otro}/baja').status_code, 400)
        self.assertEqual(self.mandar('put', f'/api/objetos/{otro}', {'nom_objeto': 'X', 'Activo': True}).status_code, 400)
        self.assertEqual(self.mandar('post', f'/api/objetos/{obj("Piano").pk}/baja').status_code, 200)
        self.assertFalse(Objeto.objects.get(nom_objeto='Piano').Activo)

    def test_el_cliente_no_entra(self):
        h = self.entrar(str(CLIENTE))
        for url in ('/api/vehiculos', '/api/servicios', '/api/objetos'):
            self.assertEqual(self.client.get(url, **h).status_code, 403)
