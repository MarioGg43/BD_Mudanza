from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.http import require_POST, require_GET
from django.utils import timezone
import json

from .models import Usuario, Rol, Permiso, Vehiculo
from .permisos import (  # noqa: F401
    get_usuario_actual, pantalla_inicio, puede_actuar_sobre_rol, requiere_permiso, requiere_permiso_api,
    tiene_permiso,
)
from .reglas_roles import (
    error_baja_gestor, error_cambio_rol_gestor, error_cruce_cliente, error_restablecer_clave,
)
from .utils import (
    hash_password, generate_username, validate_strong_password, generate_temp_password,
    nombre_usuario_libre,
)

MENSAJE_ROL_SUPERIOR = 'No podés operar sobre un rol con más permisos administrativos que el tuyo.'


def _rol_superior():
    return JsonResponse({'ok': False, 'error': MENSAJE_ROL_SUPERIOR}, status=403)


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

    # el formulario se puede enviar directo, sin pasar por el login
    if not usuario.Activo:
        return render(request, 'login.html', {'error': 'El usuario se encuentra dado de baja (Inactivo).'})

    if not usuario.verificar_clave(clave_actual):
        return render(request, 'login.html', {
            'cambio_obligatorio': True,
            'dni_cambio': dni,
            'clave_actual': clave_actual,
            'error_cambio': 'La clave actual no coincide.'
        })

    if nueva_clave != confirmar_clave:
        return render(request, 'login.html', {
            'cambio_obligatorio': True,
            'dni_cambio': dni,
            'clave_actual': clave_actual,
            'error_cambio': 'Las contraseñas no coinciden.'
        })

    valida, msg = validate_strong_password(nueva_clave)
    if not valida:
        return render(request, 'login.html', {
            'cambio_obligatorio': True,
            'dni_cambio': dni,
            'clave_actual': clave_actual,
            'error_cambio': msg
        })

    usuario.set_clave(nueva_clave)
    usuario.DebeCambiarClave = False
    usuario.save()

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
    ident = request.POST.get('identificador', '').strip()
    deseada = request.POST.get('clave_deseada', '').strip()

    usuario = None
    if ident.isdigit():
        usuario = Usuario.objects.filter(DNI=int(ident)).first()
    if not usuario:
        usuario = Usuario.objects.filter(NombreUsuario=ident.lower()).first()
    if not usuario:
        usuario = Usuario.objects.filter(Correo=ident.lower()).first()

    if not usuario:
        return JsonResponse({'ok': False, 'error': 'No se encontró ningún usuario con ese DNI, Usuario o Correo.'}, status=404)

    if not usuario.Activo:
        return JsonResponse({'ok': False, 'error': 'El usuario está dado de baja.'}, status=403)

    if deseada:
        valida, msg = validate_strong_password(deseada)
        if not valida:
            return JsonResponse({'ok': False, 'error': msg}, status=400)
        nueva_clave = deseada
    else:
        nueva_clave = generate_temp_password(10)

    usuario.set_clave(nueva_clave)
    usuario.DebeCambiarClave = True
    usuario.save()

    return JsonResponse({
        'ok': True,
        'usuario': usuario.NombreUsuario,
        'clave_provisoria': nueva_clave
    })

# ---- DASHBOARD DE ADMINISTRADOR (CRUD USUARIOS; LA FLOTA ESTÁ EN /vehiculos/) ----
def admin_dashboard(request):
    usuario_actual = get_usuario_actual(request)
    if not usuario_actual:
        return redirect('login')
    if not tiene_permiso(usuario_actual, 'USR_CONSULTAR'):
        return pantalla_inicio(usuario_actual)

    solo_activos = request.GET.get('activos') == '1'
    usuarios = Usuario.objects.select_related('idRol')
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

    permisos = usuario_actual.idRol.permisos.all()
    vehiculos = Vehiculo.objects.filter(chofer_asignado=usuario_actual)
    return render(request, 'usuario_portal.html', {
        'usuario_actual': usuario_actual,
        'permisos_rol': permisos,
        'vehiculos': vehiculos,
    })

def sin_permisos(request):
    if not get_usuario_actual(request):
        return redirect('login')
    return render(request, 'sin_permisos.html')

# ---- OPERACIONES CRUD ----
@require_POST
@requiere_permiso_api('USR_CREAR')
def alta_usuario(request):
    try:
        dni = int(request.POST.get('dni'))
        apellido = request.POST.get('apellido', '').strip()
        nombre = request.POST.get('nombre', '').strip()
        correo = request.POST.get('correo', '').strip().lower()
        clave = request.POST.get('clave', '')
        id_rol = int(request.POST.get('idRol'))

        if Usuario.objects.filter(DNI=dni).exists():
            return JsonResponse({'ok': False, 'error': f'El DNI {dni} ya se encuentra registrado.'}, status=400)

        if Usuario.objects.filter(Correo=correo).exists():
            return JsonResponse({'ok': False, 'error': f'El correo {correo} ya se encuentra en uso.'}, status=400)

        valida, msg = validate_strong_password(clave)
        if not valida:
            return JsonResponse({'ok': False, 'error': f'Clave no válida: {msg}'}, status=400)

        rol = get_object_or_404(Rol, id_rol=id_rol)
        if not puede_actuar_sobre_rol(request.usuario, rol):
            return _rol_superior()

        # Regla: Apellido + primera letra del primer nombre
        final_user = nombre_usuario_libre(apellido, nombre)

        nuevo = Usuario.objects.create(
            DNI=dni,
            Apellido=apellido,
            Nombre=nombre,
            Correo=correo,
            NombreUsuario=final_user,
            Clave=hash_password(clave),
            Activo=True,
            DebeCambiarClave=True, # Por regla estricta: exige cambio en próximo login
            idRol=rol
        )

        return JsonResponse({'ok': True, 'usuario': nuevo.NombreUsuario})
    except Exception as e:
        return JsonResponse({'ok': False, 'error': str(e)}, status=400)

@require_POST
@requiere_permiso_api('USR_EDITAR_CORREO')
def modificar_correo(request, dni):
    # Regla estricta Hito 2: La Modificación solo permite editar el Correo
    usuario = get_object_or_404(Usuario, DNI=dni)
    if not puede_actuar_sobre_rol(request.usuario, usuario.idRol):
        return _rol_superior()
    nuevo_correo = request.POST.get('correo', '').strip().lower()

    if Usuario.objects.filter(Correo=nuevo_correo).exclude(DNI=dni).exists():
        return JsonResponse({'ok': False, 'error': 'El correo ya pertenece a otro usuario.'}, status=400)

    usuario.Correo = nuevo_correo
    usuario.save() # auto_now actualiza automáticamente FechaUltimaModificacion
    return JsonResponse({'ok': True, 'nuevo_correo': usuario.Correo})

@require_POST
@requiere_permiso_api('USR_BAJA')
def baja_usuario(request, dni):
    # Regla estricta Hito 2: Cambiar Activo a (no) y asentar FechaBaja

    usuario = get_object_or_404(Usuario, DNI=dni)

    if usuario.DNI == request.usuario.DNI:
        return JsonResponse({'ok': False, 'error': 'No podes darte de baja a vos mismo.'}, status=400)

    if not puede_actuar_sobre_rol(request.usuario, usuario.idRol):
        return _rol_superior()

    error = error_baja_gestor(usuario)
    if error:
        return JsonResponse({'ok': False, 'error': error}, status=400)

    from pedidos.reglas import tiene_pedidos_activos
    if tiene_pedidos_activos(idUsuario=usuario):
        return JsonResponse({
            'ok': False,
            'error': 'El usuario tiene pedidos pendientes o confirmados. Anulalos antes de darlo de baja.'
        }, status=400)

    usuario.Activo = False
    usuario.FechaBaja = timezone.now()
    usuario.save()
    return JsonResponse({'ok': True})

@require_POST
@requiere_permiso_api('USR_BAJA')
def reactivar_usuario(request, dni):
    usuario = get_object_or_404(Usuario, DNI=dni)
    if not puede_actuar_sobre_rol(request.usuario, usuario.idRol):
        return _rol_superior()
    usuario.Activo = True
    usuario.FechaBaja = None
    usuario.save()
    return JsonResponse({'ok': True})

@require_POST
@requiere_permiso_api('USR_RESET_CLAVE')
def restablecer_clave(request, dni):
    usuario = get_object_or_404(Usuario, DNI=dni)
    if not puede_actuar_sobre_rol(request.usuario, usuario.idRol):
        return _rol_superior()
    error = error_restablecer_clave(usuario)
    if error:
        return JsonResponse({'ok': False, 'error': error}, status=400)
    nueva = request.POST.get('nueva_clave', '').strip()
    if nueva:
        valida, msg = validate_strong_password(nueva)
        if not valida:
            return JsonResponse({'ok': False, 'error': msg}, status=400)
        temp_clave = nueva
    else:
        temp_clave = generate_temp_password(10)

    usuario.set_clave(temp_clave)
    usuario.DebeCambiarClave = True # Exige cambio en próximo login
    usuario.save()

    return JsonResponse({
        'ok': True,
        'clave_temporal': temp_clave,
        'usuario': usuario.NombreUsuario
    })

@require_POST
@requiere_permiso_api('USR_CAMBIAR_ROL')
def cambiar_rol(request, dni):
    """Asigna otro rol al usuario. Va aparte de la modificacion de correo,
    que por consigna solo puede editar el correo."""

    usuario = get_object_or_404(Usuario, DNI=dni)

    if usuario.DNI == request.usuario.DNI:
        return JsonResponse({'ok': False, 'error': 'No podes cambiar tu propio rol.'}, status=400)

    try:
        rol = Rol.objects.get(id_rol=int(request.POST.get('idRol')))
    except (Rol.DoesNotExist, TypeError, ValueError):
        return JsonResponse({'ok': False, 'error': 'El rol indicado no existe.'}, status=400)

    if not (puede_actuar_sobre_rol(request.usuario, usuario.idRol)
            and puede_actuar_sobre_rol(request.usuario, rol)):
        return _rol_superior()

    anterior = usuario.idRol
    if anterior.id_rol == rol.id_rol:
        return JsonResponse({'ok': False, 'error': f'{usuario.NombreUsuario} ya tiene el rol {rol.nom_rol}.'}, status=400)

    error = error_cruce_cliente(usuario, rol) or error_cambio_rol_gestor(usuario, rol)
    if error:
        return JsonResponse({'ok': False, 'error': error}, status=400)

    usuario.idRol = rol
    usuario.save()

    return JsonResponse({'ok': True, 'usuario': usuario.NombreUsuario,
                         'anterior': anterior.nom_rol, 'nuevo': rol.nom_rol})

@require_GET
@requiere_permiso_api('USR_CREAR')
def preview_username_view(request):
    ape = request.GET.get('apellido', '')
    nom = request.GET.get('nombre', '')
    return JsonResponse({'NombreUsuario': generate_username(ape, nom)})
