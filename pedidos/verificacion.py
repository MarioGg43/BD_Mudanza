"""Crear cuenta en dos pasos: el sistema manda un código de 6 números al correo y la cuenta se
crea recién cuando la persona lo escribe. Mientras tanto los datos esperan en la sesión (con la
clave ya cifrada), así no quedan cuentas a medio hacer en la base."""
import logging
import secrets
import time

from django.conf import settings
from django.contrib.auth.hashers import check_password, make_password
from django.core.mail import send_mail

log = logging.getLogger(__name__)

EN_SESION = 'registro_pendiente'
MINUTOS = 10           # cuánto dura el código
INTENTOS = 5           # cuántas veces se puede equivocar antes de tener que pedir otro
ESPERA_REENVIO = 60    # segundos entre un envío y el siguiente


class ErrorCodigo(Exception):
    """Un problema con el código, con el mensaje para la persona."""


def _nuevo_codigo():
    return f'{secrets.randbelow(10 ** 6):06d}'


def _enviar(datos, codigo):
    cuerpo = (f'Hola {datos["nombre"]}:\n\n'
              f'Tu código para terminar de crear tu cuenta es: {codigo}\n\n'
              f'Vence en {MINUTOS} minutos. Si no pediste crear una cuenta, ignorá este correo.\n\n'
              'Mudanzas y Fletes Salta')
    send_mail('Mudanzas y Fletes Salta · Tu código para crear la cuenta', cuerpo, None, [datos['correo']])
    if settings.DEBUG:  # en la computadora de desarrollo queda en el registro del servidor, por si no hay internet
        log.warning('Código de verificación para %s: %s', datos['correo'], codigo)


def iniciar(request, datos):
    """Guarda los datos en espera y manda el código. Si el correo no sale, lanza la excepción
    y no queda nada en espera."""
    codigo = _nuevo_codigo()
    _enviar(datos, codigo)
    ahora = time.time()
    request.session[EN_SESION] = {'datos': datos, 'codigo': make_password(codigo), 'vence': ahora + MINUTOS * 60,
                                  'intentos': 0, 'enviado': ahora}


def pendiente(request):
    """Lo que está esperando el código, o None si no hay nada o ya venció."""
    p = request.session.get(EN_SESION)
    if not p:
        return None
    if time.time() > p['vence']:
        cancelar(request)
        return None
    return p


def cancelar(request):
    request.session.pop(EN_SESION, None)


def segundos_para_reenviar(p):
    return max(0, int(p['enviado'] + ESPERA_REENVIO - time.time()))


def reenviar(request):
    p = pendiente(request)
    if not p:
        raise ErrorCodigo('El código venció. Completá el formulario de nuevo.')
    espera = segundos_para_reenviar(p)
    if espera:
        raise ErrorCodigo(f'Esperá {espera} segundos para pedir otro código.')
    codigo = _nuevo_codigo()
    _enviar(p['datos'], codigo)
    ahora = time.time()
    p.update(codigo=make_password(codigo), vence=ahora + MINUTOS * 60, intentos=0, enviado=ahora)
    request.session[EN_SESION] = p


def confirmar(request, codigo):
    """Devuelve los datos si el código es el correcto. Si no, lanza ErrorCodigo."""
    p = pendiente(request)
    if not p:
        raise ErrorCodigo('El código venció. Completá el formulario de nuevo.')
    codigo = ''.join(c for c in (codigo or '') if c.isdigit())
    if len(codigo) != 6:
        raise ErrorCodigo('El código tiene 6 números.')
    if p['intentos'] >= INTENTOS:
        raise ErrorCodigo('Te equivocaste muchas veces. Pedí un código nuevo.')
    if not check_password(codigo, p['codigo']):
        p['intentos'] += 1
        request.session[EN_SESION] = p
        quedan = INTENTOS - p['intentos']
        raise ErrorCodigo(f'El código no es correcto. Te quedan {quedan} intentos.' if quedan
                          else 'Te equivocaste muchas veces. Pedí un código nuevo.')
    cancelar(request)
    return p['datos']


def correo_tapado(correo):
    """«elena.delgado4@gmail.com» → «el***********@gmail.com»: se ve a dónde fue sin mostrarlo entero."""
    usuario, _, dominio = correo.partition('@')
    return usuario[:2] + '*' * max(len(usuario) - 2, 3) + '@' + dominio
