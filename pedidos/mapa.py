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
import unicodedata
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from django.conf import settings
from django.core.cache import cache

log = logging.getLogger(__name__)

URL_ORS = 'https://api.openrouteservice.org'
SALTA = (-65.4117, -24.7821)  # lon, lat: la búsqueda prefiere direcciones cerca de Salta
# el rectángulo que contiene a la provincia de Salta: las direcciones se buscan primero acá
SALTA_PROVINCIA = {'boundary.rect.min_lon': -68.6, 'boundary.rect.max_lon': -62.3,
                   'boundary.rect.min_lat': -26.4, 'boundary.rect.max_lat': -22.0}
UN_DIA = 60 * 60 * 24
ESPERA = 10  # segundos máximos por consulta


class ErrorMapa(Exception):
    """Algo que se le puede mostrar a la persona (dirección no encontrada, servicio caído...)."""


def puntos(pedido):
    """(punto de origen, punto de destino) del pedido: (lat, lon) o None si no se marcó en el mapa."""
    def punto(lat, lon):
        return (float(lat), float(lon)) if lat is not None and lon is not None else None
    return punto(pedido.lat_origen, pedido.lon_origen), punto(pedido.lat_destino, pedido.lon_destino)


def como_llegar(origen, destino, punto_origen=None, punto_destino=None):
    """Enlace de Google Maps con el recorrido cargado. En el celular abre la app de Maps.
    No necesita clave: es la forma pública de armar un enlace de indicaciones. Si hay punto exacto,
    va el punto (Google lleva a la puerta); si no, el texto de la dirección."""
    def lugar(texto, punto):
        return f'{punto[0]:.6f},{punto[1]:.6f}' if punto else texto
    return 'https://www.google.com/maps/dir/?' + urlencode(
        {'api': 1, 'origin': lugar(origen, punto_origen), 'destination': lugar(destino, punto_destino),
         'travelmode': 'driving'})


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
        try:
            detalle = e.read().decode(errors='ignore')
        except Exception:  # noqa: BLE001 - sin cuerpo, se decide solo por el código
            detalle = ''
        if e.code == 429 or 'quota' in detalle.lower():  # OpenRouteService avisa la cuota agotada con 403
            raise ErrorMapa('Se alcanzó el límite de consultas del mapa. Probá en un rato.') from e
        if e.code in (401, 403):
            raise ErrorMapa('La clave de OpenRouteService no es válida.') from e
        raise ErrorMapa('El servicio de mapas no pudo armar el recorrido.') from e
    except (URLError, TimeoutError, ValueError) as e:
        log.warning('Sin respuesta de OpenRouteService: %s', e)
        raise ErrorMapa('No hay conexión con el servicio de mapas.') from e


def _sin_acentos(texto):
    return ''.join(c for c in unicodedata.normalize('NFD', texto.lower()) if unicodedata.category(c) != 'Mn')


def _buscar(direccion, **limites):
    datos = _pedir(f'{URL_ORS}/geocode/search?' + urlencode({
        'text': direccion, 'boundary.country': 'AR', 'size': 1,
        'focus.point.lon': SALTA[0], 'focus.point.lat': SALTA[1], **limites}))
    lugares = datos.get('features') or []
    return lugares[0] if lugares else None


def _nombra_otro_lugar(direccion, lugar):
    """Si la persona escribió, después de la coma, la ciudad o la provincia del resultado de afuera de
    Salta («Mitre 50, Córdoba»), es una mudanza a otra provincia y vale ese resultado. Solo cuenta lo
    que va después de la coma: «entre 20 de febrero y 25 de mayo» nombra calles, no el pueblo
    25 de Mayo de Misiones."""
    p = lugar.get('properties', {})
    if p.get('region_a') == 'SA' or (p.get('region') or '').lower() == 'salta' or ',' not in direccion:
        return False
    texto = _sin_acentos(direccion.split(',', 1)[1])
    return any(n and len(n) > 3 and _sin_acentos(n) in texto
               for n in (p.get('locality'), p.get('localadmin'), p.get('county'), p.get('region')))


def geocodificar(direccion):
    """(lon, lat, etiqueta) de la dirección. Primero busca dentro de la provincia de Salta: sin ese
    límite, el servicio elegía calles con el mismo nombre en otras provincias («Belgrano 100» en
    Santiago del Estero). Solo sale de Salta si no encuentra nada adentro o si la persona escribió
    la ciudad o la provincia de afuera (mudanzas nacionales)."""
    en_salta = _buscar(direccion, **SALTA_PROVINCIA)
    # en todo el país solo si después de la coma hay una ciudad que no es Salta («Mitre 50, Córdoba»).
    # Si no se nombró otra ciudad y en Salta no aparece, no se usa lo primero que haya en el país:
    # «entre 20 de febrero y 25 de mayo» terminaba en un pueblo de Misiones, a más de 1.000 km
    if ',' in direccion and not _menciona_salta(direccion.split(',', 1)[1]):
        en_pais = _buscar(direccion)
        if en_pais is not None and _nombra_otro_lugar(direccion, en_pais):
            en_salta = en_pais
    if en_salta is None:
        raise ErrorMapa(f'No encontramos «{direccion}» en Salta. Si es en otra provincia, agregá la ciudad '
                        'después de una coma (por ejemplo «Mitre 50, Córdoba»), o marcala en el mapa.')
    lon, lat = en_salta['geometry']['coordinates'][:2]
    return lon, lat, en_salta.get('properties', {}).get('label', direccion)


def _menciona_salta(direccion):
    return 'salta' in _sin_acentos(direccion)


def ubicar(direccion):
    """Dónde cae una dirección escrita a mano, para que el cliente lo confirme («¿Es acá?»):
    {'lat', 'lon', 'etiqueta'}. Se guarda un día en la caché."""
    if not settings.ORS_API_KEY:
        raise ErrorMapa('El mapa todavía no está configurado (falta la clave de OpenRouteService).')
    clave_cache = 'ubicar:' + hashlib.sha256(direccion.strip().lower().encode()).hexdigest()
    guardado = cache.get(clave_cache)
    if guardado:
        return guardado
    lon, lat, etiqueta = geocodificar(direccion)
    resultado = {'lat': lat, 'lon': lon, 'etiqueta': etiqueta.removesuffix(', Argentina')}
    cache.set(clave_cache, resultado, UN_DIA)
    return resultado


def recorrido(origen, destino, punto_origen=None, punto_destino=None):
    """El recorrido en camión entre las dos direcciones, listo para la pantalla:
    {'origen': {...}, 'destino': {...}, 'ruta': <GeoJSON LineString>, 'km': 12.3, 'minutos': 25}.
    Si viene el punto exacto de una dirección (lat, lon), se usa ese y no se busca el texto.
    Lanza ErrorMapa si falta la clave, no encuentra una dirección o el servicio falla."""
    if not settings.ORS_API_KEY:
        raise ErrorMapa('El mapa todavía no está configurado (falta la clave de OpenRouteService).')
    # «recorrido2»: los guardados con la búsqueda vieja (que se iba a otras provincias) no se usan más
    clave_cache = 'recorrido2:' + hashlib.sha256(f'{origen}|{destino}|{punto_origen}|{punto_destino}'.encode()).hexdigest()
    guardado = cache.get(clave_cache)
    if guardado:
        return guardado

    def ubicado(texto, punto):
        return (punto[1], punto[0], texto) if punto else geocodificar(texto)
    lon_o, lat_o, etiqueta_o = ubicado(origen, punto_origen)
    lon_d, lat_d, etiqueta_d = ubicado(destino, punto_destino)
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
