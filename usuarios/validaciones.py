"""Reglas de los datos que escribe la gente (DNI, nombres, teléfono, correo, textos).
Las usan los formularios de Django, las operaciones de usuarios y la API de React, así la
regla se escribe una sola vez. En el navegador, validar.js hace lo mismo mientras se escribe;
esto es la segunda barrera, por si alguien se lo saltea."""
import re

from django.core.exceptions import ValidationError
from django.core.validators import validate_email

LETRA = 'A-Za-zÁÉÍÓÚÜÑáéíóúüñ'
PERSONA = re.compile(rf"^[{LETRA}]+(?:[ '\-][{LETRA}]+)*$")
PATENTE = re.compile(r'^(?:[A-Z]{2}-?\d{3}-?[A-Z]{2}|[A-Z]{3}-?\d{3})$')
MINUSCULAS = {'de', 'del', 'la', 'las', 'los', 'y'}


class DatoInvalido(ValueError):
    """Un dato mal escrito, con el mensaje para la persona."""


def letras(texto):
    return sum(c.isalpha() for c in texto or '')


def repite_letras(texto, veces=3):
    """True si tiene la misma letra veces o más seguidas («aaaa»): no es un nombre ni un texto."""
    return re.search(rf'([{LETRA}])\1{{{veces - 1},}}', texto or '', re.IGNORECASE) is not None


def dni(valor):
    """7 u 8 números, sin puntos. Devuelve el número."""
    texto = str(valor if valor is not None else '').strip()
    if not texto:
        raise DatoInvalido('Escribí el DNI.')
    if not texto.isdigit():
        raise DatoInvalido('El DNI lleva solo números, sin puntos ni espacios.')
    if not 7 <= len(texto.lstrip('0')) <= 8:
        raise DatoInvalido('El DNI tiene 7 u 8 números.')
    return int(texto)


def persona(valor, que='nombre'):
    """Nombre o apellido: letras (con tildes), y entre palabras un espacio, un apóstrofo o un
    guion. De 2 a 50 caracteres. Devuelve el texto prolijo: «maría  de la paz» → «María de la Paz»."""
    texto = ' '.join((valor or '').split())
    if not texto:
        raise DatoInvalido(f'Escribí el {que}.')
    if not PERSONA.match(texto):
        raise DatoInvalido(f'El {que} lleva solo letras (puede tener espacios, apóstrofo o guion).')
    if letras(texto) < 2:
        raise DatoInvalido(f'El {que} tiene que tener al menos 2 letras.')
    if len(texto) > 50:
        raise DatoInvalido(f'El {que} puede tener hasta 50 caracteres.')
    if repite_letras(texto) or not re.search('[aeiouáéíóúü]', texto, re.IGNORECASE):
        raise DatoInvalido(f'Revisá el {que}: no parece un {que} real.')
    palabras = texto.split(' ')
    return ' '.join(p.lower() if i and p.lower() in MINUSCULAS else _capitalizar(p) for i, p in enumerate(palabras))


def _capitalizar(palabra):
    # «o'brien» → «O'Brien», «pérez-gómez» → «Pérez-Gómez»
    return re.sub(rf"(^|['\-])([{LETRA}])", lambda m: m.group(1) + m.group(2).upper(), palabra.lower())


def telefono(valor, obligatorio=False):
    """Con código de área: de 10 a 13 números (387 4112233, +54 9 387 4112233). Se aceptan
    espacios, guiones y un + al principio. Vacío → None, salvo que sea obligatorio."""
    texto = ' '.join((valor or '').split())
    if not texto:
        if obligatorio:
            raise DatoInvalido('Escribí el teléfono.')
        return None
    if not re.match(r'^\+?[\d -]+$', texto):
        raise DatoInvalido('El teléfono lleva solo números, espacios o guiones (y un + al principio).')
    digitos = sum(c.isdigit() for c in texto)
    if not 10 <= digitos <= 13:
        raise DatoInvalido('Escribí el teléfono con código de área: 10 números, por ejemplo 387 4112233.')
    return texto


def correo(valor):
    texto = (valor or '').strip().lower()
    if not texto:
        raise DatoInvalido('Escribí el correo.')
    try:
        validate_email(texto)
    except ValidationError:
        raise DatoInvalido('Escribí un correo válido, por ejemplo nombre@gmail.com.')
    if len(texto) > 150:
        raise DatoInvalido('El correo puede tener hasta 150 caracteres.')
    return texto


def nombre_de_algo(valor, que='nombre', minimo=2, maximo=100):
    """El nombre de un servicio, un objeto, un material, un rol o un modelo de vehículo: puede
    llevar números («Camión 3/4»), pero tiene que tener letras y no ser una letra repetida."""
    texto = ' '.join((valor or '').split())
    if not texto:
        raise DatoInvalido(f'Escribí el {que}.')
    if letras(texto) < minimo:
        raise DatoInvalido(f'El {que} tiene que tener al menos {minimo} letras.')
    if len(texto) > maximo:
        raise DatoInvalido(f'El {que} puede tener hasta {maximo} caracteres.')
    if repite_letras(texto, 4):
        raise DatoInvalido(f'Revisá el {que}: tiene una letra repetida muchas veces.')
    return texto


def texto_con_sentido(valor, que='el texto', minimo_letras=3):
    """Un motivo o una observación: que tenga palabras y no sea «.....» o «aaaa»."""
    texto = ' '.join((valor or '').split())
    if letras(texto) < minimo_letras or repite_letras(texto, 4):
        raise DatoInvalido(f'Escribí {que} con palabras (al menos {minimo_letras} letras).')
    return texto


def patente(valor):
    """AB123CD (Mercosur) o ABC123, con o sin guiones. Se guarda en mayúsculas y sin espacios."""
    texto = (valor or '').strip().upper().replace(' ', '')
    if not texto:
        raise DatoInvalido('Escribí la patente.')
    if not PATENTE.match(texto):
        raise DatoInvalido('La patente es como AB123CD o ABC123.')
    return texto


def para_form(funcion, *args, **kwargs):
    """Lo mismo, pero con el error de los formularios de Django."""
    from django import forms
    try:
        return funcion(*args, **kwargs)
    except DatoInvalido as e:
        raise forms.ValidationError(str(e))
