from .permisos import get_usuario_actual, permisos_de


def seguridad(request):
    """Deja en todas las plantillas el usuario de la sesión, sus permisos y, a quien gestiona
    pedidos, las mudanzas que ya tendrían que haber terminado y nadie finalizó."""
    usuario = getattr(request, 'usuario', None) or get_usuario_actual(request)
    permisos = permisos_de(usuario)
    recordatorio = []
    if 'PED_GESTIONAR' in permisos:
        from pedidos.reglas import recordatorio_finalizar
        recordatorio = recordatorio_finalizar()
    return {'usuario_sesion': usuario, 'permisos': permisos, 'recordatorio_finalizar': recordatorio}
