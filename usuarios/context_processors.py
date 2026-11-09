from .permisos import get_usuario_actual, permisos_de


def seguridad(request):
    """Deja en todas las plantillas el usuario de la sesión, sus permisos y, a quien gestiona
    pedidos, las mudanzas que ya tendrían que haber terminado y nadie finalizó."""
    usuario = getattr(request, 'usuario', None) or get_usuario_actual(request)
    permisos = permisos_de(usuario)
    recordatorio, pendientes = [], 0
    if 'PED_GESTIONAR' in permisos:
        from pedidos.reglas import filtro_por_venir, recordatorio_finalizar
        from .models import Pedido
        recordatorio = recordatorio_finalizar()
        # el número al lado de «Pedidos» en el menú lateral: los que esperan que la empresa confirme
        pendientes = Pedido.objects.filter(filtro_por_venir(), estado=Pedido.PENDIENTE).count()
    return {'usuario_sesion': usuario, 'permisos': permisos, 'recordatorio_finalizar': recordatorio,
            # el personal (quien no pide mudanzas) usa el menú lateral; el cliente, el de arriba
            'menu_lateral': bool(usuario) and 'PED_REGISTRAR' not in permisos,
            'pedidos_pendientes': pendientes}
