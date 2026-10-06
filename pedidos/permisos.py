"""Permisos del Hito 3: se consultan en PERMISOS_ROLES, no por el nombre del rol."""
from functools import wraps

from django.http import HttpResponseForbidden
from django.shortcuts import redirect

from usuarios.models import PermisoRol
from usuarios.views import get_usuario_actual


def tiene_permiso(usuario, nombre):
    return PermisoRol.objects.filter(idRol_id=usuario.idRol_id, idPermiso__nom_permiso=nombre).exists()


def requiere_permiso(nombre):
    """Sin sesión manda al login; sin el permiso responde 403.
    Deja el usuario en request.usuario para que la vista no lo vuelva a buscar."""
    def decorador(vista):
        @wraps(vista)
        def envoltura(request, *args, **kwargs):
            usuario = get_usuario_actual(request)
            if not usuario:
                return redirect('login')
            if not tiene_permiso(usuario, nombre):
                return HttpResponseForbidden('No tenés permiso para esta operación.')
            request.usuario = usuario
            return vista(request, *args, **kwargs)
        return envoltura
    return decorador
