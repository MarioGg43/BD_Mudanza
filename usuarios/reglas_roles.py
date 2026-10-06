"""Reglas de roles: candados para que el sistema nunca quede sin quien lo administre."""
from django.db import transaction

from .models import Permiso, PermisoRol, Rol, Usuario
from .permisos import CATALOGO

# init_data vuelve a crear por nombre estos cuatro roles, así que no se renombran ni eliminan
ROLES_DEL_SISTEMA = ('Administrador', 'Cliente', 'Chofer', 'Ayudante de Carga')
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


CODIGOS_VALIDOS = {c for _, c, _ in CATALOGO}


class ErrorRol(Exception):
    def __init__(self, errores):
        if isinstance(errores, str):
            errores = {'__all__': errores}
        self.errores = errores
        super().__init__(' '.join(errores.values()))


def guardar_rol(rol, nombre, descripcion, codigos, actor):
    """Crea (rol=None) o edita un rol y deja exactamente esos permisos."""
    nombre = (nombre or '').strip()
    descripcion = (descripcion or '').strip() or None
    codigos = set(codigos or [])
    errores = {}
    if codigos - CODIGOS_VALIDOS:
        errores['permisos'] = 'Hay permisos que no existen.'
    if not nombre:
        errores['nombre'] = 'Escribí el nombre del rol.'
    elif len(nombre) > 100:
        errores['nombre'] = 'El nombre puede tener hasta 100 caracteres.'
    elif Rol.objects.filter(nom_rol__iexact=nombre).exclude(pk=getattr(rol, 'pk', None)).exists():
        errores['nombre'] = 'Ya existe un rol con ese nombre.'
    if rol and rol.nom_rol in ROLES_DEL_SISTEMA and nombre != rol.nom_rol:
        errores['nombre'] = f'«{rol.nom_rol}» es un rol del sistema: no se le puede cambiar el nombre.'
    if descripcion and len(descripcion) > 100:
        errores['descripcion'] = 'La descripción puede tener hasta 100 caracteres.'
    if rol and 'ROL_GESTIONAR' not in codigos and rol.permisos.filter(nom_permiso='ROL_GESTIONAR').exists():
        if actor.idRol_id == rol.pk:
            errores['permisos'] = 'No podés quitarte el permiso de gestionar roles.'
        elif not gestores_activos().exclude(idRol=rol).exists():
            errores['permisos'] = MENSAJE_SIN_GESTOR
    if errores:
        raise ErrorRol(errores)
    with transaction.atomic():
        if rol is None:
            rol = Rol.objects.create(nom_rol=nombre, desc_rol=descripcion)
        else:
            rol.nom_rol, rol.desc_rol = nombre, descripcion
            rol.save()
        PermisoRol.objects.filter(idRol=rol).exclude(idPermiso__nom_permiso__in=codigos).delete()
        for p in Permiso.objects.filter(nom_permiso__in=codigos):
            PermisoRol.objects.get_or_create(idRol=rol, idPermiso=p)
    return rol


def eliminar_rol(rol):
    """Solo roles que no son del sistema y no tienen usuarios (nada los referencia)."""
    if rol.nom_rol in ROLES_DEL_SISTEMA:
        raise ErrorRol(f'«{rol.nom_rol}» es un rol del sistema y no se puede eliminar.')
    cantidad = rol.usuarios.count()
    if cantidad:
        raise ErrorRol(f'«{rol.nom_rol}» tiene {cantidad} usuario(s). Cambiales el rol antes de eliminarlo.')
    with transaction.atomic():
        PermisoRol.objects.filter(idRol=rol).delete()
        rol.delete()
