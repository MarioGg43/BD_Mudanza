from usuarios.permisos import get_usuario_actual


def sin_leer(request):
    """La cantidad de notificaciones sin leer, para el número de la campanita del menú."""
    usuario = getattr(request, 'usuario', None) or get_usuario_actual(request)
    if not usuario:
        return {}
    from .reglas import de_usuario
    return {'notificaciones_sin_leer': de_usuario(usuario).filter(leida=False).count()}
