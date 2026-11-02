"""Login por token para el frontend en React.

El token es el DNI firmado con la SECRET_KEY y con fecha (django.core.signing): no se puede
falsificar ni cambiar, vence a las HORAS_TOKEN y no necesita una tabla. React lo guarda y lo
manda en cada pedido HTTP como «Authorization: Bearer <token>»."""
import json
from functools import wraps

from django.core import signing
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from usuarios.auditoria import con_usuario
from usuarios.models import Usuario
from usuarios.permisos import permisos_de, tiene_permiso

HORAS_TOKEN = 12
_SAL = 'api.token'


def crear_token(usuario):
    return signing.TimestampSigner(salt=_SAL).sign(str(usuario.DNI))


def usuario_del_token(token):
    try:
        dni = signing.TimestampSigner(salt=_SAL).unsign(token, max_age=HORAS_TOKEN * 3600)
    except signing.BadSignature:  # también cuando venció (SignatureExpired)
        return None
    return Usuario.objects.select_related('idRol').filter(DNI=dni, Activo=True).first()


def datos_usuario(usuario):
    """Lo que React necesita saber de quien entró: quién es y qué puede hacer."""
    return {'dni': usuario.DNI, 'nombre': usuario.Nombre, 'apellido': usuario.Apellido,
            'correo': usuario.Correo, 'rol': usuario.idRol.nom_rol, 'permisos': sorted(permisos_de(usuario))}


def error(mensaje, status=400, errores=None):
    return JsonResponse({'error': mensaje, 'errores': errores or {}}, status=status)


def leer_json(request):
    try:
        datos = json.loads(request.body or b'{}')
    except ValueError:
        return {}
    return datos if isinstance(datos, dict) else {}


def publico(metodos=('POST',)):
    """Para el login y el registro: sin token."""
    def decorador(vista):
        @csrf_exempt
        @wraps(vista)
        def envoltura(request, *args, **kwargs):
            if request.method not in metodos:
                return error('Método no permitido.', 405)
            return vista(request, *args, **kwargs)
        return envoltura
    return decorador


def endpoint(permiso=None, metodos=('GET',)):
    """Para cada operación de la API: método permitido, token válido (401) y permiso (403).
    Sin CSRF: el token viaja en un encabezado, no en una cookie, así que otra página no puede usarlo.
    El usuario queda registrado para el log de auditoría, igual que con la sesión."""
    def decorador(vista):
        @csrf_exempt
        @wraps(vista)
        def envoltura(request, *args, **kwargs):
            if request.method not in metodos:
                return error('Método no permitido.', 405)
            encabezado = request.headers.get('Authorization', '')
            token = encabezado[7:] if encabezado.startswith('Bearer ') else ''
            usuario = usuario_del_token(token) if token else None
            if not usuario:
                return error('Tu sesión venció o no iniciaste sesión.', 401)
            if permiso and not tiene_permiso(usuario, permiso):
                return error('No tenés permiso para esta operación.', 403)
            request.usuario = usuario
            with con_usuario(usuario):
                return vista(request, *args, **kwargs)
        return envoltura
    return decorador
