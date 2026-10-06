from .permisos import get_usuario_actual, permisos_de


def seguridad(request):
    """Deja en todas las plantillas el usuario de la sesión y sus permisos."""
    usuario = getattr(request, 'usuario', None) or get_usuario_actual(request)
    return {'usuario_sesion': usuario, 'permisos': permisos_de(usuario)}
