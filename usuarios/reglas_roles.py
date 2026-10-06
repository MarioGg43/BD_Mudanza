"""Reglas de roles: candados para que el sistema nunca quede sin quien lo administre."""
from .models import Usuario

ROLES_DEL_SISTEMA = ('Administrador', 'Cliente', 'Chofer')
MENSAJE_SIN_GESTOR = 'El sistema tiene que quedar con al menos un usuario activo que pueda gestionar roles.'


def gestores_activos():
    """Usuarios activos cuyo rol tiene ROL_GESTIONAR."""
    return Usuario.objects.filter(Activo=True, idRol__permisos__nom_permiso='ROL_GESTIONAR').distinct()


def _es_gestor(usuario):
    return usuario.Activo and gestores_activos().filter(pk=usuario.pk).exists()


def error_baja_gestor(usuario):
    if _es_gestor(usuario) and not gestores_activos().exclude(pk=usuario.pk).exists():
        return MENSAJE_SIN_GESTOR
    return None


def error_cambio_rol_gestor(usuario, nuevo_rol):
    nuevo_gestiona = nuevo_rol.permisos.filter(nom_permiso='ROL_GESTIONAR').exists()
    if not nuevo_gestiona and error_baja_gestor(usuario):
        return MENSAJE_SIN_GESTOR
    return None
