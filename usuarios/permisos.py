"""Control de acceso de todo el sistema: se consulta PERMISOS_ROLES, nunca el nombre del rol."""
from functools import wraps

from django.http import HttpResponseForbidden, JsonResponse
from django.shortcuts import redirect

from .models import PermisoRol, Usuario

# Catálogo fijo: desde la pantalla de roles los permisos se asignan, no se crean,
# porque un permiso que el código no controla no tendría ningún efecto.
CATALOGO = [
    ('Usuarios', 'USR_CONSULTAR', 'Ver el panel de usuarios'),
    ('Usuarios', 'USR_CREAR', 'Dar de alta usuarios'),
    ('Usuarios', 'USR_EDITAR_CORREO', 'Modificar el correo de un usuario'),
    ('Usuarios', 'USR_CAMBIAR_ROL', 'Cambiar el rol de un usuario'),
    ('Usuarios', 'USR_BAJA', 'Dar de baja y reactivar usuarios'),
    ('Usuarios', 'USR_RESET_CLAVE', 'Restablecer la clave de un usuario'),
    ('Roles', 'ROL_GESTIONAR', 'Ver, crear y editar roles y sus permisos'),
    ('Vehículos', 'VEH_GESTIONAR', 'Alta, modificación y baja de vehículos'),
    ('Personal', 'MUDANZAS_OPERAR', 'Ver el portal del personal y sus vehículos asignados'),
    ('Pedidos', 'PED_REGISTRAR', 'Registrar pedidos de mudanza'),
    ('Pedidos', 'PED_CONSULTAR', 'Consultar pedidos'),
    ('Pedidos', 'PED_GESTIONAR', 'Confirmar y finalizar pedidos (y ver los de todos)'),
    ('Pedidos', 'PED_ANULAR', 'Anular pedidos'),
    ('Pedidos', 'PED_COMPROBANTE', 'Emitir el comprobante del pedido'),
    ('Servicios', 'SRV_GESTIONAR', 'Alta, modificación y baja de servicios'),
]

# Permisos administrativos: quien no los tiene no puede crear, editar ni
# restablecer a un usuario cuyo rol sí los tiene (evita la escalada de privilegios).
PERMISOS_SENSIBLES = frozenset(
    [c for area, c, _ in CATALOGO if area in ('Usuarios', 'Roles', 'Vehículos', 'Servicios')]
    + ['PED_GESTIONAR', 'PED_ANULAR'])

PERMISOS_INICIALES = {
    'Administrador': [c for _, c, _ in CATALOGO if c != 'PED_REGISTRAR'],
    'Chofer': ['MUDANZAS_OPERAR'],
    'Ayudante de Carga': ['MUDANZAS_OPERAR'],
    'Cliente': ['PED_REGISTRAR', 'PED_CONSULTAR', 'PED_COMPROBANTE'],
}


def get_usuario_actual(request):
    dni = request.session.get('usuario_dni')
    if not dni:
        return None
    try:
        return Usuario.objects.select_related('idRol').get(DNI=dni, Activo=True)
    except Usuario.DoesNotExist:
        return None


def permisos_de(usuario):
    """Códigos de permiso del rol del usuario (se calculan una vez por objeto)."""
    if usuario is None:
        return set()
    if not hasattr(usuario, '_permisos'):
        usuario._permisos = set(PermisoRol.objects.filter(idRol_id=usuario.idRol_id)
                                .values_list('idPermiso__nom_permiso', flat=True))
    return usuario._permisos


def tiene_permiso(usuario, codigo):
    return codigo in permisos_de(usuario)


def puede_actuar_sobre_rol(actor, rol):
    """Quien gestiona roles puede todo; el resto, solo sobre roles cuyos permisos
    administrativos ya tiene."""
    propios = permisos_de(actor)
    if 'ROL_GESTIONAR' in propios:
        return True
    del_rol = set(PermisoRol.objects.filter(idRol=rol).values_list('idPermiso__nom_permiso', flat=True))
    return (del_rol & PERMISOS_SENSIBLES) <= propios


def requiere_permiso(codigo):
    """Para pantallas: sin sesión manda al login; sin el permiso responde 403."""
    def decorador(vista):
        @wraps(vista)
        def envoltura(request, *args, **kwargs):
            usuario = get_usuario_actual(request)
            if not usuario:
                return redirect('login')
            if not tiene_permiso(usuario, codigo):
                return HttpResponseForbidden('No tenés permiso para esta operación.')
            request.usuario = usuario
            return vista(request, *args, **kwargs)
        return envoltura
    return decorador


def requiere_permiso_api(codigo):
    """Para las operaciones JSON del panel: 401 sin sesión, 403 sin el permiso."""
    def decorador(vista):
        @wraps(vista)
        def envoltura(request, *args, **kwargs):
            usuario = get_usuario_actual(request)
            if not usuario:
                return JsonResponse({'ok': False, 'error': 'Debe iniciar sesion.'}, status=401)
            if not tiene_permiso(usuario, codigo):
                return JsonResponse({'ok': False, 'error': 'No tenés permiso para esta operación.'}, status=403)
            request.usuario = usuario
            return vista(request, *args, **kwargs)
        return envoltura
    return decorador


def pantalla_inicio(usuario):
    """La primera pantalla que le corresponde según sus permisos."""
    p = permisos_de(usuario)
    if 'USR_CONSULTAR' in p:
        return redirect('admin_dashboard')
    if 'PED_CONSULTAR' in p:
        return redirect('pedidos_lista')
    if 'PED_REGISTRAR' in p:
        return redirect('pedidos_nuevo')
    if 'MUDANZAS_OPERAR' in p:
        return redirect('usuario_portal')
    return redirect('sin_permisos')
