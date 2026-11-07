"""El recorrido de una mudanza en el mapa, con OpenRouteService (https://openrouteservice.org).

1. Geocodificación: convierte cada dirección («Zuviría 150, Salta») en coordenadas.
2. Ruta: pide el camino para camión (perfil driving-hgv) entre las dos coordenadas. Vuelve
   en formato GeoJSON, que Leaflet dibuja directo en el mapa, con los km y el tiempo de viaje.

La clave de la API va en la variable de entorno ORS_API_KEY (archivo .env, que no se sube a git).
Sin clave, o si el servicio no responde, la pantalla muestra igual el enlace «Cómo llegar».
Los resultados se guardan un día en la caché de Django: el mismo pedido no vuelve a consultar.
"""
import hashlib
import json
import logging
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from django.conf import settings
from django.core.cache import cache

log = logging.getLogger(__name__)

URL_ORS = 'https://api.openrouteservice.org'
SALTA = (-65.4117, -24.7821)  # lon, lat: la búsqueda prefiere direcciones cerca de Salta
UN_DIA = 60 * 60 * 24
ESPERA = 10  # segundos máximos por consulta


class ErrorMapa(Exception):
    """Algo que se le puede mostrar a la persona (dirección no encontrada, servicio caído...)."""


def como_llegar(origen, destino):
    """Enlace de Google Maps con el recorrido cargado. En el celular abre la app de Maps.
    No necesita clave: es la forma pública de armar un enlace de indicaciones."""
    return 'https://www.google.com/maps/dir/?' + urlencode(
        {'api': 1, 'origin': origen, 'destination': destino, 'travelmode': 'driving'})


def _pedir(url, cuerpo=None):
    clave = settings.ORS_API_KEY
    pedido = Request(url, data=json.dumps(cuerpo).encode() if cuerpo is not None else None,
                     headers={'Authorization': clave, 'Content-Type': 'application/json',
                              'Accept': 'application/json, application/geo+json'})
    try:
        with urlopen(pedido, timeout=ESPERA) as r:
            return json.loads(r.read().decode())
    except HTTPError as e:
        log.warning('OpenRouteService respondió %s en %s', e.code, url.split('?')[0])
        if e.code in (401, 403):
            raise ErrorMapa('La clave de OpenRouteService no es válida.') from e
        if e.code == 429:
            raise ErrorMapa('Se alcanzó el límite diario de consultas del mapa. Probá más tarde.') from e
        raise ErrorMapa('El servicio de mapas no pudo armar el recorrido.') from e
    except (URLError, TimeoutError, ValueError) as e:
        log.warning('Sin respuesta de OpenRouteService: %s', e)
        raise ErrorMapa('No hay conexión con el servicio de mapas.') from e


def geocodificar(direccion):
    """(lon, lat, etiqueta) de la dirección, buscando en Argentina y cerca de Salta."""
    datos = _pedir(f'{URL_ORS}/geocode/search?' + urlencode({
        'text': direccion, 'boundary.country': 'AR', 'size': 1,
        'focus.point.lon': SALTA[0], 'focus.point.lat': SALTA[1]}))
    lugares = datos.get('features') or []
    if not lugares:
        raise ErrorMapa(f'No encontramos «{direccion}» en el mapa.')
    lon, lat = lugares[0]['geometry']['coordinates'][:2]
    return lon, lat, lugares[0].get('properties', {}).get('label', direccion)


def recorrido(origen, destino):
    """El recorrido en camión entre las dos direcciones, listo para la pantalla:
    {'origen': {...}, 'destino': {...}, 'ruta': <GeoJSON LineString>, 'km': 12.3, 'minutos': 25}.
    Lanza ErrorMapa si falta la clave, no encuentra una dirección o el servicio falla."""
    if not settings.ORS_API_KEY:
        raise ErrorMapa('El mapa todavía no está configurado (falta la clave de OpenRouteService).')
    clave_cache = 'recorrido:' + hashlib.sha256(f'{origen}|{destino}'.encode()).hexdigest()
    guardado = cache.get(clave_cache)
    if guardado:
        return guardado

    lon_o, lat_o, etiqueta_o = geocodificar(origen)
    lon_d, lat_d, etiqueta_d = geocodificar(destino)
    if abs(lon_o - lon_d) < 0.0005 and abs(lat_o - lat_d) < 0.0005:  # unos 50 metros
        # pasa con direcciones vagas («zona norte», «zona este»): el servicio las ubica en el mismo
        # punto y el recorrido daría 0 km, que confunde más de lo que ayuda
        raise ErrorMapa('Las dos direcciones caen en el mismo punto del mapa. Revisá que tengan calle, '
                        'número y localidad.')
    datos = _pedir(f'{URL_ORS}/v2/directions/driving-hgv/geojson',
                   {'coordinates': [[lon_o, lat_o], [lon_d, lat_d]]})
    try:
        tramo = datos['features'][0]
        resumen = tramo['properties']['summary']
    except (KeyError, IndexError) as e:
        raise ErrorMapa('El servicio de mapas no encontró un camino entre las dos direcciones.') from e
    resultado = {
        'origen': {'lat': lat_o, 'lon': lon_o, 'etiqueta': etiqueta_o},
        'destino': {'lat': lat_d, 'lon': lon_d, 'etiqueta': etiqueta_d},
        'ruta': tramo['geometry'],
        'km': round(resumen.get('distance', 0) / 1000, 1),
        'minutos': round(resumen.get('duration', 0) / 60),
    }
    cache.set(clave_cache, resultado, UN_DIA)
    return resultado


def direccion_de(lat, lon):
    """La dirección de un punto que la persona tocó en el mapa (geocodificación inversa):
    «Avenida Belgrano 1250, Salta». Lanza ErrorMapa si no hay clave o no encuentra nada cerca."""
    if not settings.ORS_API_KEY:
        raise ErrorMapa('El mapa todavía no está configurado (falta la clave de OpenRouteService).')
    clave_cache = f'direccion:{lat:.5f},{lon:.5f}'
    guardada = cache.get(clave_cache)
    if guardada:
        return guardada
    datos = _pedir(f'{URL_ORS}/geocode/reverse?' + urlencode({
        'point.lat': lat, 'point.lon': lon, 'size': 1, 'boundary.country': 'AR'}))
    lugares = datos.get('features') or []
    if not lugares:
        raise ErrorMapa('No encontramos una dirección en ese punto. Probá tocando sobre una calle.')
    p = lugares[0].get('properties', {})
    calle = ' '.join(x for x in (p.get('street'), p.get('housenumber')) if x) or p.get('name', '')
    localidad = p.get('locality') or p.get('localadmin') or p.get('county') or ''
    partes = [x for x in (calle, localidad) if x]
    direccion = ', '.join(dict.fromkeys(partes)) or p.get('label', '').removesuffix(', Argentina')
    if not direccion:
        raise ErrorMapa('No encontramos una dirección en ese punto. Probá tocando sobre una calle.')
    cache.set(clave_cache, direccion, UN_DIA)
    return direccion
