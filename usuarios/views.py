from django.contrib import messages
from django.db.models import Count
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.http import require_POST, require_GET
from django.utils import timezone
import json

from .models import Usuario, Rol, Permiso, Pedido, Vehiculo
from .permisos import (  # noqa: F401
    get_usuario_actual, pantalla_inicio, puede_actuar_sobre_rol, requiere_permiso, requiere_permiso_api,
    tiene_permiso,
)
from . import operaciones
from .utils import generate_username

# ---- LOGIN Y AUTENTICACIÓN ----
def login_view(request):
    if request.method == 'POST':
        ident = request.POST.get('usuario', '').strip()
        clave = request.POST.get('clave', '')

        if not ident or not clave:
            return render(request, 'login.html', {'error': 'Por favor complete todos los campos.'})

        usuario = None
        if ident.isdigit():
            usuario = Usuario.objects.filter(DNI=int(ident)).first()
        if not usuario:
            usuario = Usuario.objects.filter(NombreUsuario=ident.lower()).first()
        if not usuario:
            usuario = Usuario.objects.filter(Correo=ident.lower()).first()

        if not usuario or not usuario.verificar_clave(clave):
            return render(request, 'login.html', {'error': 'Usuario o contraseña incorrectos.'})

        if not usuario.Activo:
            return render(request, 'login.html', {'error': 'El usuario se encuentra dado de baja (Inactivo).'})

        # Si DebeCambiarClave está en True, se muestra el formulario de cambio obligatorio
        if usuario.DebeCambiarClave:
            return render(request, 'login.html', {
                'cambio_obligatorio': True,
                'dni_cambio': usuario.DNI,
                'clave_actual': clave,
            })

        # Guardar sesión
        usuario.registrar_acceso()
        request.session.cycle_key()
        request.session['usuario_dni'] = usuario.DNI
        request.session['usuario_rol'] = usuario.idRol.nom_rol

        return pantalla_inicio(usuario)

    return render(request, 'login.html')

@require_POST
def cambiar_clave_obligatoria(request):
    dni = request.POST.get('dni')
    clave_actual = request.POST.get('clave_actual')
    nueva_clave = request.POST.get('nueva_clave')
    confirmar_clave = request.POST.get('confirmar_clave')

    usuario = get_object_or_404(Usuario, DNI=dni)

    # el formulario se puede enviar directo, sin pasar por el login: se revisa todo de nuevo
    # (las reglas están en operaciones.py y las usa también la API de React)
    try:
        operaciones.cambiar_clave_provisoria(usuario, clave_actual, nueva_clave, confirmar_clave)
    except operaciones.ErrorUsuario as e:
        if e.status == 403:
            return render(request, 'login.html', {'error': str(e)})
        return render(request, 'login.html', {
            'cambio_obligatorio': True,
            'dni_cambio': dni,
            'clave_actual': clave_actual,
            'error_cambio': str(e),
        })

    # Iniciar sesión directamente
    usuario.registrar_acceso()
    request.session.cycle_key()
    request.session['usuario_dni'] = usuario.DNI
    request.session['usuario_rol'] = usuario.idRol.nom_rol

    return pantalla_inicio(usuario)

def logout_view(request):
    request.session.flush()
    return redirect('login')

# ---- RECUPERACIÓN / OLVIDÉ MI CONTRASEÑA ----
@require_POST
def olvide_clave_view(request):
    """Solo clientes: con el DNI y el correo de la cuenta (los dos) eligen una clave nueva.
    No se genera ni se muestra ninguna clave, y al personal se la restablece el administrador.
    Antes alcanzaba con el DNI de cualquiera (incluido el administrador) y la clave nueva se
    mostraba en pantalla. La regla está en operaciones.py y la usa también la API de React."""
    try:
        usuario = operaciones.recuperar_clave_cliente(
            request.POST.get('dni', '').strip(), request.POST.get('correo', ''),
            request.POST.get('nueva_clave', ''), request.POST.get('confirmar_clave', ''))
    except operaciones.ErrorUsuario as e:
        return JsonResponse({'ok': False, 'error': str(e)}, status=e.status)
    return JsonResponse({'ok': True, 'usuario': usuario.NombreUsuario})

# ---- DASHBOARD DE ADMINISTRADOR (CRUD USUARIOS; LA FLOTA ESTÁ EN /vehiculos/) ----
def admin_dashboard(request):
    usuario_actual = get_usuario_actual(request)
    if not usuario_actual:
        return redirect('login')
    if not tiene_permiso(usuario_actual, 'USR_CONSULTAR'):
        return pantalla_inicio(usuario_actual)

    solo_activos = request.GET.get('activos') == '1'
    usuarios = Usuario.objects.select_related('idRol').annotate(cant_pedidos=Count('pedidos'))
    if solo_activos:
        usuarios = usuarios.filter(Activo=True)
    usuarios = usuarios.order_by('Apellido', 'Nombre')

    roles = Rol.objects.all().order_by('id_rol')
    # en los selectores solo se ofrecen los roles que este usuario puede asignar
    roles_asignables = [r for r in roles if puede_actuar_sobre_rol(usuario_actual, r)]

    return render(request, 'admin_dashboard.html', {
        'usuario_actual': usuario_actual,
        'usuarios': usuarios,
        'roles': roles,
        'roles_asignables': roles_asignables,
        'solo_activos': solo_activos,
    })

# ---- PORTAL DE USUARIO OPERATIVO ----
def usuario_portal(request):
    usuario_actual = get_usuario_actual(request)
    if not usuario_actual:
        return redirect('login')
    if not tiene_permiso(usuario_actual, 'MUDANZAS_OPERAR'):
        return pantalla_inicio(usuario_actual)

    from django.db.models import Q
    from datetime import timedelta
    from pedidos.reglas import filtro_por_venir, se_puede_empezar  # pedidos depende de usuarios
    from pedidos.mapa import como_llegar
    permisos = usuario_actual.idRol.permisos.all()
    vehiculos = Vehiculo.objects.filter(chofer_asignado=usuario_actual)
    # sus mudanzas por venir y las confirmadas de los últimos días que todavía no se finalizaron
    # (las que están en curso), sin precios
    recientes = Q(estado=Pedido.CONFIRMADO, fecha_servicio__gte=timezone.localdate() - timedelta(days=5))
    mudanzas = list(Pedido.objects.filter(filtro_por_venir() | recientes, personal__idUsuario=usuario_actual)
                    .distinct().select_related('patente_vehiculo', 'idUsuario')
                    .prefetch_related('detalles__idServicio', 'inventario__idObjeto', 'personal__idUsuario')
                    .order_by('fecha_servicio', 'hora_servicio'))
    ahora = timezone.now()
    for p in mudanzas:
        # solo el chofer de esa mudanza marca «Empezamos» / «Terminamos»
        p.soy_chofer = any(x.idUsuario_id == usuario_actual.pk and x.Funcion == 'Chofer' for x in p.personal.all())
        sin_empezar = p.soy_chofer and p.estado == Pedido.CONFIRMADO and not p.inicio_real
        p.puede_empezar = sin_empezar and se_puede_empezar(p, ahora)
        p.empieza_tarde = p.puede_empezar and ahora > p.inicio               # ya pasó la hora y no empezaron
        p.ya_paso = sin_empezar and timezone.localtime(ahora).date() > p.fecha_servicio
        p.como_llegar = como_llegar(p.origen, p.destino)  # abre Google Maps con el recorrido
    return render(request, 'usuario_portal.html', {
        'usuario_actual': usuario_actual,
        'permisos_rol': permisos,
        'vehiculos': vehiculos,
        'mudanzas': mudanzas,
        'en_curso': sum(1 for p in mudanzas if p.en_curso),
    })

# ---- MI CUENTA: cada persona ve sus datos y cambia su clave; el cliente, también su correo y teléfono ----
def mi_cuenta(request):
    usuario = get_usuario_actual(request)
    if not usuario:
        return redirect('login')
    # el personal no cambia su correo solo: eso lo hace el administrador (Hito 2)
    edita_datos = tiene_permiso(usuario, 'PED_REGISTRAR')
    errores, datos = {}, {'correo': usuario.Correo, 'telefono': usuario.Telefono or ''}
    if request.method == 'POST':
        accion = request.POST.get('accion')
        try:
            if accion == 'datos' and edita_datos:
                datos = {'correo': request.POST.get('correo', ''), 'telefono': request.POST.get('telefono', '')}
                operaciones.actualizar_mis_datos(usuario, datos['correo'], datos['telefono'])
                messages.success(request, 'Guardamos tus datos.')
                return redirect('mi_cuenta')
            if accion == 'clave':
                operaciones.cambiar_mi_clave(usuario, request.POST.get('actual', ''),
                                             request.POST.get('nueva', ''), request.POST.get('confirmar', ''))
                messages.success(request, 'Listo, cambiamos tu clave. La próxima vez entrá con la nueva.')
                return redirect('mi_cuenta')
        except operaciones.ErrorUsuario as e:
            errores = {'accion': accion, (e.campo or 'general'): str(e)}
    return render(request, 'mi_cuenta.html', {
        'usuario_actual': usuario, 'edita_datos': edita_datos, 'datos': datos, 'errores': errores})


def sin_permisos(request):
    if not get_usuario_actual(request):
        return redirect('login')
    return render(request, 'sin_permisos.html')

# ---- OPERACIONES CRUD (las reglas están en operaciones.py; las usa también la API de React) ----
def _fallo(e):
    return JsonResponse({'ok': False, 'error': str(e)}, status=e.status)


@require_POST
@requiere_permiso_api('USR_CREAR')
def alta_usuario(request):
    try:
        dni = int(request.POST.get('dni'))
        id_rol = int(request.POST.get('idRol'))
    except (TypeError, ValueError) as e:
        return JsonResponse({'ok': False, 'error': str(e)}, status=400)
    get_object_or_404(Rol, id_rol=id_rol)
    try:
        nuevo = operaciones.crear_usuario(request.usuario, dni, request.POST.get('apellido'), request.POST.get('nombre'),
                                          request.POST.get('correo'), request.POST.get('clave', ''), id_rol)
    except operaciones.ErrorUsuario as e:
        return _fallo(e)
    return JsonResponse({'ok': True, 'usuario': nuevo.NombreUsuario})


@require_POST
@requiere_permiso_api('USR_EDITAR_CORREO')
def modificar_correo(request, dni):
    # Regla estricta Hito 2: La Modificación solo permite editar el Correo
    usuario = get_object_or_404(Usuario, DNI=dni)
    try:
        operaciones.modificar_correo(request.usuario, usuario, request.POST.get('correo', ''))
    except operaciones.ErrorUsuario as e:
        return _fallo(e)
    return JsonResponse({'ok': True, 'nuevo_correo': usuario.Correo})


@require_POST
@requiere_permiso_api('USR_BAJA')
def baja_usuario(request, dni):
    # Regla estricta Hito 2: Cambiar Activo a (no) y asentar FechaBaja
    try:
        operaciones.dar_de_baja(request.usuario, get_object_or_404(Usuario, DNI=dni))
    except operaciones.ErrorUsuario as e:
        return _fallo(e)
    return JsonResponse({'ok': True})


@require_POST
@requiere_permiso_api('USR_BAJA')
def reactivar_usuario(request, dni):
    try:
        operaciones.reactivar(request.usuario, get_object_or_404(Usuario, DNI=dni))
    except operaciones.ErrorUsuario as e:
        return _fallo(e)
    return JsonResponse({'ok': True})


@require_POST
@requiere_permiso_api('USR_RESET_CLAVE')
def restablecer_clave(request, dni):
    usuario = get_object_or_404(Usuario, DNI=dni)
    try:
        clave = operaciones.restablecer_clave(request.usuario, usuario, request.POST.get('nueva_clave', ''))
    except operaciones.ErrorUsuario as e:
        return _fallo(e)
    return JsonResponse({'ok': True, 'clave_temporal': clave, 'usuario': usuario.NombreUsuario})


@require_POST
@requiere_permiso_api('USR_CAMBIAR_ROL')
def cambiar_rol(request, dni):
    """Asigna otro rol al usuario. Va aparte de la modificacion de correo,
    que por consigna solo puede editar el correo."""
    usuario = get_object_or_404(Usuario, DNI=dni)
    try:
        anterior = operaciones.cambiar_rol(request.usuario, usuario, request.POST.get('idRol'))
    except operaciones.ErrorUsuario as e:
        return _fallo(e)
    return JsonResponse({'ok': True, 'usuario': usuario.NombreUsuario,
                         'anterior': anterior.nom_rol, 'nuevo': usuario.idRol.nom_rol})

@require_GET
@requiere_permiso_api('USR_CREAR')
def preview_username_view(request):
    ape = request.GET.get('apellido', '')
    nom = request.GET.get('nombre', '')
    return JsonResponse({'NombreUsuario': generate_username(ape, nom)})
