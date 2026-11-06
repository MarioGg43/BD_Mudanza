"""Reglas del ABM de usuarios (Hito 2). Las usan el panel de Django (views.py) y la API de React
(api/views_usuarios.py), así una regla se escribe una sola vez.
`actor` es quien hace la operación: no puede actuar sobre roles con más permisos que el suyo."""
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.utils import timezone

from .models import Rol, Usuario
from .permisos import puede_actuar_sobre_rol
from .reglas_roles import (error_baja_gestor, error_cambio_rol_gestor, error_cruce_cliente,
                           error_restablecer_clave)
from .utils import generate_temp_password, hash_password, nombre_usuario_libre, validate_strong_password

MENSAJE_ROL_SUPERIOR = 'No podés operar sobre un rol con más permisos administrativos que el tuyo.'


class ErrorUsuario(Exception):
    """Un error para mostrarle a la persona; `status` es el código HTTP (400 o 403)."""

    def __init__(self, mensaje, status=400):
        self.status = status
        super().__init__(mensaje)


def _puede(actor, rol):
    if not puede_actuar_sobre_rol(actor, rol):
        raise ErrorUsuario(MENSAJE_ROL_SUPERIOR, 403)


def crear_usuario(actor, dni, apellido, nombre, correo, clave, id_rol):
    """Alta con usuario automático (apellido + inicial) y cambio de clave obligatorio al entrar."""
    correo = (correo or '').strip().lower()
    apellido, nombre = (apellido or '').strip(), (nombre or '').strip()
    if Usuario.objects.filter(DNI=dni).exists():
        raise ErrorUsuario(f'El DNI {dni} ya se encuentra registrado.')
    if Usuario.objects.filter(Correo=correo).exists():
        raise ErrorUsuario(f'El correo {correo} ya se encuentra en uso.')
    valida, msg = validate_strong_password(clave)
    if not valida:
        raise ErrorUsuario(f'Clave no válida: {msg}')
    rol = Rol.objects.filter(id_rol=id_rol).first()
    if rol is None:
        raise ErrorUsuario('El rol indicado no existe.')
    _puede(actor, rol)
    return Usuario.objects.create(
        DNI=dni, Apellido=apellido, Nombre=nombre, Correo=correo,
        NombreUsuario=nombre_usuario_libre(apellido, nombre), Clave=hash_password(clave),
        Activo=True, DebeCambiarClave=True, idRol=rol)


def modificar_correo(actor, usuario, correo):
    """Por consigna del Hito 2, la modificación solo cambia el correo."""
    _puede(actor, usuario.idRol)
    correo = (correo or '').strip().lower()
    try:
        validate_email(correo)
    except ValidationError:
        raise ErrorUsuario('Escribí un correo válido.')
    if Usuario.objects.filter(Correo=correo).exclude(pk=usuario.pk).exists():
        raise ErrorUsuario('El correo ya pertenece a otro usuario.')
    usuario.Correo = correo
    usuario.save()
    return usuario


def dar_de_baja(actor, usuario):
    """Baja lógica: queda inactivo con la fecha de baja."""
    if usuario.pk == actor.pk:
        raise ErrorUsuario('No podes darte de baja a vos mismo.')
    _puede(actor, usuario.idRol)
    error = error_baja_gestor(usuario)
    if error:
        raise ErrorUsuario(error)
    from pedidos.reglas import tiene_pedidos_activos  # pedidos depende de usuarios
    if tiene_pedidos_activos(idUsuario=usuario):
        raise ErrorUsuario('El usuario tiene pedidos pendientes o confirmados. Anulalos antes de darlo de baja.')
    usuario.Activo = False
    usuario.FechaBaja = timezone.now()
    usuario.save()
    return usuario


def reactivar(actor, usuario):
    _puede(actor, usuario.idRol)
    usuario.Activo = True
    usuario.FechaBaja = None
    usuario.save()
    return usuario


def restablecer_clave(actor, usuario, nueva=''):
    """Pone una clave provisoria (la elegida o una al azar) y exige cambiarla al entrar."""
    _puede(actor, usuario.idRol)
    error = error_restablecer_clave(usuario)
    if error:
        raise ErrorUsuario(error)
    nueva = (nueva or '').strip()
    if nueva:
        valida, msg = validate_strong_password(nueva)
        if not valida:
            raise ErrorUsuario(msg)
    clave = nueva or generate_temp_password(10)
    usuario.set_clave(clave)
    usuario.DebeCambiarClave = True
    usuario.save()
    return clave


def cambiar_clave_provisoria(usuario, actual, nueva, confirmar):
    """La persona reemplaza la clave provisoria que le dio la empresa por una suya. Valida
    la clave actual, que las dos nuevas coincidan, que sea fuerte y que no repita la provisoria."""
    if not usuario.Activo:
        raise ErrorUsuario('El usuario se encuentra dado de baja (Inactivo).', 403)
    if not usuario.verificar_clave(actual):
        raise ErrorUsuario('La clave actual no coincide.')
    if nueva != confirmar:
        raise ErrorUsuario('Las contraseñas no coinciden.')
    valida, msg = validate_strong_password(nueva)
    if not valida:
        raise ErrorUsuario(msg)
    if (nueva or '').strip() == (actual or '').strip():
        raise ErrorUsuario('La clave nueva tiene que ser distinta de la provisoria.')
    usuario.set_clave(nueva)
    usuario.DebeCambiarClave = False
    usuario.save()
    return usuario


MENSAJE_DATOS_NO_COINCIDEN = 'El DNI y el correo no coinciden con ninguna cuenta de cliente.'


def recuperar_clave_cliente(dni, correo, nueva, confirmar):
    """«Olvidé mi contraseña» para clientes: con el DNI y el correo de la cuenta (tienen que
    coincidir los dos) elige una clave nueva. No se muestra ni se genera ninguna clave. Al
    personal le restablece la clave el administrador. Si los datos no coinciden, el mensaje es
    el mismo exista o no la cuenta, para no revelar quién está registrado."""
    usuario = Usuario.objects.select_related('idRol').filter(
        DNI=dni, Correo=(correo or '').strip().lower()).first() if str(dni or '').isdigit() else None
    if usuario is None or usuario.idRol.nom_rol != 'Cliente':
        raise ErrorUsuario(MENSAJE_DATOS_NO_COINCIDEN)
    if not usuario.Activo:
        raise ErrorUsuario('El usuario se encuentra dado de baja (Inactivo).', 403)
    if nueva != confirmar:
        raise ErrorUsuario('Las contraseñas no coinciden.')
    valida, msg = validate_strong_password(nueva)
    if not valida:
        raise ErrorUsuario(msg)
    usuario.set_clave(nueva)
    usuario.DebeCambiarClave = False
    usuario.save()
    return usuario


def cambiar_rol(actor, usuario, id_rol):
    """Devuelve el rol anterior."""
    if usuario.pk == actor.pk:
        raise ErrorUsuario('No podes cambiar tu propio rol.')
    rol = Rol.objects.filter(id_rol=id_rol).first() if str(id_rol or '').isdigit() else None
    if rol is None:
        raise ErrorUsuario('El rol indicado no existe.')
    if not (puede_actuar_sobre_rol(actor, usuario.idRol) and puede_actuar_sobre_rol(actor, rol)):
        raise ErrorUsuario(MENSAJE_ROL_SUPERIOR, 403)
    anterior = usuario.idRol
    if anterior.pk == rol.pk:
        raise ErrorUsuario(f'{usuario.NombreUsuario} ya tiene el rol {rol.nom_rol}.')
    error = error_cruce_cliente(usuario, rol) or error_cambio_rol_gestor(usuario, rol)
    if error:
        raise ErrorUsuario(error)
    usuario.idRol = rol
    usuario.save()
    return anterior
