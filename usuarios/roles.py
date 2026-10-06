"""ABM de roles: cada rol con los permisos que se le tildan."""
from django.contrib import messages
from django.db.models import Count
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from .forms import RolForm
from .models import Rol
from .permisos import requiere_permiso
from .reglas_roles import ROLES_DEL_SISTEMA, ErrorRol, eliminar_rol, guardar_rol


@requiere_permiso('ROL_GESTIONAR')
def lista(request):
    roles = (Rol.objects.annotate(cantidad=Count('usuarios', distinct=True))
             .prefetch_related('permisos').order_by('id_rol'))
    return render(request, 'roles/lista.html', {'roles': roles, 'del_sistema': ROLES_DEL_SISTEMA})


def _guardar(request, rol, titulo):
    if request.method == 'POST':
        form = RolForm(request.POST)
        if form.is_valid():
            d = form.cleaned_data
            try:
                guardado = guardar_rol(rol, d['nombre'], d['descripcion'], d['permisos'], request.usuario)
            except ErrorRol as e:
                for campo, mensaje in e.errores.items():
                    form.add_error(campo if campo in form.fields else None, mensaje)
            else:
                messages.success(request, f'Rol «{guardado.nom_rol}» guardado.')
                return redirect('roles_lista')
    else:
        inicial = {}
        if rol:
            inicial = {'nombre': rol.nom_rol, 'descripcion': rol.desc_rol or '',
                       'permisos': list(rol.permisos.values_list('nom_permiso', flat=True))}
        form = RolForm(initial=inicial)
    return render(request, 'roles/form.html', {
        'form': form, 'titulo': titulo, 'rol': rol,
        'nombre_fijo': bool(rol and rol.nom_rol in ROLES_DEL_SISTEMA)})


@requiere_permiso('ROL_GESTIONAR')
def crear(request):
    return _guardar(request, None, 'Nuevo rol')


@requiere_permiso('ROL_GESTIONAR')
def editar(request, id_rol):
    rol = get_object_or_404(Rol, pk=id_rol)
    return _guardar(request, rol, f'Editar «{rol.nom_rol}»')


@requiere_permiso('ROL_GESTIONAR')
@require_POST
def eliminar(request, id_rol):
    rol = get_object_or_404(Rol, pk=id_rol)
    try:
        nombre = rol.nom_rol
        eliminar_rol(rol)
        messages.success(request, f'Rol «{nombre}» eliminado.')
    except ErrorRol as e:
        messages.error(request, str(e))
    return redirect('roles_lista')
