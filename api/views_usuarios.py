"""Controladores REST de usuarios y roles. Las reglas están en usuarios/operaciones.py y
usuarios/reglas_roles.py, las mismas que usa el panel de Django."""
from django.db.models import Count
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.utils import timezone

from usuarios import operaciones
from usuarios.models import Rol, Usuario
from usuarios.permisos import CATALOGO, puede_actuar_sobre_rol, tiene_permiso
from usuarios.reglas_roles import ROLES_DEL_SISTEMA, ErrorRol, eliminar_rol, guardar_rol
from usuarios.utils import generate_username
from .autenticacion import endpoint, error, leer_json


def _fecha(dt):
    return timezone.localtime(dt).strftime('%d/%m/%Y %H:%M') if dt else None


def _usuario(u):
    return {'dni': u.DNI, 'apellido': u.Apellido, 'nombre': u.Nombre, 'correo': u.Correo,
            'telefono': u.Telefono or '', 'usuario': u.NombreUsuario, 'rol': u.idRol.nom_rol, 'id_rol': u.idRol_id,
            'activo': u.Activo, 'debe_cambiar_clave': u.DebeCambiarClave,
            'ultimo_acceso': _fecha(u.FechaUltimoAcceso), 'baja': _fecha(u.FechaBaja)}


def _operacion(funcion, *args):
    """Llama a una regla de usuarios y convierte su error en la respuesta HTTP."""
    try:
        return funcion(*args), None
    except operaciones.ErrorUsuario as e:
        return None, error(str(e), e.status)


# ------------------------------------------------------------------ usuarios

@endpoint('USR_CONSULTAR', metodos=('GET', 'POST'))
def usuarios(request):
    """GET /api/usuarios: todos, con lo que el que consulta puede hacer. POST: alta (USR_CREAR)."""
    actor = request.usuario
    if request.method == 'POST':
        if not tiene_permiso(actor, 'USR_CREAR'):
            return error('No tenés permiso para esta operación.', 403)
        d = leer_json(request)
        try:
            dni = int(d.get('dni'))
        except (TypeError, ValueError):
            return error('Revisá los datos marcados.', errores={'dni': 'Escribí el DNI, solo números.'})
        faltan = {c: 'Completá este dato.' for c in ('apellido', 'nombre', 'correo', 'clave', 'id_rol')
                  if not str(d.get(c) or '').strip()}
        if faltan:
            return error('Revisá los datos marcados.', errores=faltan)
        nuevo, respuesta = _operacion(operaciones.crear_usuario, actor, dni, d.get('apellido'), d.get('nombre'),
                                      d.get('correo'), d.get('clave'), d.get('id_rol'))
        return respuesta or JsonResponse(_usuario(nuevo), status=201)

    lista = Usuario.objects.select_related('idRol').annotate(cant_pedidos=Count('pedidos')).order_by('Apellido', 'Nombre')
    roles = list(Rol.objects.order_by('id_rol'))
    return JsonResponse({
        'usuarios': [{**_usuario(u), 'cant_pedidos': u.cant_pedidos,
                      'puede_operar': puede_actuar_sobre_rol(actor, u.idRol), 'soy_yo': u.pk == actor.pk}
                     for u in lista],
        # en los selectores solo se ofrecen los roles que este usuario puede asignar
        'roles': [{'id': r.id_rol, 'nombre': r.nom_rol} for r in roles if puede_actuar_sobre_rol(actor, r)],
        'puede': {p: tiene_permiso(actor, c) for p, c in (
            ('crear', 'USR_CREAR'), ('correo', 'USR_EDITAR_CORREO'), ('rol', 'USR_CAMBIAR_ROL'),
            ('baja', 'USR_BAJA'), ('clave', 'USR_RESET_CLAVE'))},
    })


@endpoint('USR_CREAR')
def nombre_usuario(request):
    """GET /api/usuarios/nombre?apellido=&nombre=: cómo va a quedar el usuario automático."""
    return JsonResponse({'usuario': generate_username(request.GET.get('apellido', ''), request.GET.get('nombre', ''))})


@endpoint('USR_EDITAR_CORREO', metodos=('PUT',))
def correo(request, dni):
    u = get_object_or_404(Usuario, DNI=dni)
    hecho, respuesta = _operacion(operaciones.modificar_correo, request.usuario, u, leer_json(request).get('correo'))
    return respuesta or JsonResponse(_usuario(hecho))


@endpoint('USR_CAMBIAR_ROL', metodos=('PUT',))
def rol_de_usuario(request, dni):
    u = get_object_or_404(Usuario.objects.select_related('idRol'), DNI=dni)
    anterior, respuesta = _operacion(operaciones.cambiar_rol, request.usuario, u, leer_json(request).get('id_rol'))
    return respuesta or JsonResponse({**_usuario(u), 'rol_anterior': anterior.nom_rol})


@endpoint('USR_BAJA', metodos=('POST',))
def baja_usuario(request, dni):
    hecho, respuesta = _operacion(operaciones.dar_de_baja, request.usuario, get_object_or_404(Usuario, DNI=dni))
    return respuesta or JsonResponse(_usuario(hecho))


@endpoint('USR_BAJA', metodos=('POST',))
def reactivar_usuario(request, dni):
    hecho, respuesta = _operacion(operaciones.reactivar, request.usuario, get_object_or_404(Usuario, DNI=dni))
    return respuesta or JsonResponse(_usuario(hecho))


@endpoint('USR_RESET_CLAVE', metodos=('POST',))
def clave(request, dni):
    """POST {nueva?}: clave provisoria (la elegida o una al azar); la devuelve una sola vez."""
    u = get_object_or_404(Usuario.objects.select_related('idRol'), DNI=dni)
    nueva, respuesta = _operacion(operaciones.restablecer_clave, request.usuario, u, leer_json(request).get('nueva'))
    return respuesta or JsonResponse({'usuario': u.NombreUsuario, 'clave_provisoria': nueva})


# ------------------------------------------------------------------ roles

def _rol(r):
    return {'id': r.id_rol, 'nombre': r.nom_rol, 'descripcion': r.desc_rol or '',
            'permisos': sorted(r.permisos.values_list('nom_permiso', flat=True)),
            'del_sistema': r.nom_rol in ROLES_DEL_SISTEMA}


def _guardar_rol(request, rol):
    d = leer_json(request)
    permisos = d.get('permisos') if isinstance(d.get('permisos'), list) else []
    try:
        guardado = guardar_rol(rol, d.get('nombre'), d.get('descripcion'), permisos, request.usuario)
    except ErrorRol as e:
        return error(str(e) if '__all__' in e.errores else 'Revisá los datos marcados.', errores=e.errores)
    return JsonResponse(_rol(guardado), status=200 if rol else 201)


@endpoint('ROL_GESTIONAR', metodos=('GET', 'POST'))
def roles(request):
    """GET /api/roles: los roles con sus permisos y el catálogo de permisos. POST: alta."""
    if request.method == 'POST':
        return _guardar_rol(request, None)
    lista = Rol.objects.annotate(cantidad=Count('usuarios', distinct=True)).prefetch_related('permisos').order_by('id_rol')
    return JsonResponse({
        'roles': [{**_rol(r), 'usuarios': r.cantidad} for r in lista],
        'catalogo': [{'area': a, 'codigo': c, 'descripcion': d} for a, c, d in CATALOGO],
    })


@endpoint('ROL_GESTIONAR', metodos=('PUT', 'DELETE'))
def rol(request, id_rol):
    r = get_object_or_404(Rol, pk=id_rol)
    if request.method == 'PUT':
        return _guardar_rol(request, r)
    try:
        eliminar_rol(r)
    except ErrorRol as e:
        return error(str(e))
    return JsonResponse({'id': id_rol, 'eliminado': True})
