from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.http import require_POST, require_GET
from django.utils import timezone
import json

from .models import Usuario, Rol, Permiso, Vehiculo
from .utils import (
    hash_password, generate_username, validate_strong_password, generate_temp_password
)

def get_usuario_actual(request):
    dni = request.session.get('usuario_dni')
    if not dni:
        return None
    try:
        return Usuario.objects.select_related('idRol').get(DNI=dni, Activo=True)
    except Usuario.DoesNotExist:
        return None

def solo_admin(request):
    """Controla que quien llama sea un administrador activo.

    Devuelve (usuario, None) si puede seguir, o (None, respuesta de error).
    Se usa en todas las operaciones del panel, porque las direcciones se
    pueden llamar directo sin pasar por la pantalla.
    """
    actual = get_usuario_actual(request)
    if not actual:
        return None, JsonResponse({'ok': False, 'error': 'Debe iniciar sesion.'}, status=401)
    if actual.idRol.nom_rol.lower() != 'administrador':
        return None, JsonResponse({'ok': False, 'error': 'Se requiere el rol Administrador.'}, status=403)
    return actual, None


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
        request.session['usuario_dni'] = usuario.DNI
        request.session['usuario_rol'] = usuario.idRol.nom_rol

        if usuario.idRol.nom_rol.lower() == 'administrador':
            return redirect('admin_dashboard')
        else:
            return redirect('usuario_portal')

    return render(request, 'login.html')

@require_POST
def cambiar_clave_obligatoria(request):
    dni = request.POST.get('dni')
    clave_actual = request.POST.get('clave_actual')
    nueva_clave = request.POST.get('nueva_clave')
    confirmar_clave = request.POST.get('confirmar_clave')

    usuario = get_object_or_404(Usuario, DNI=dni)

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
    request.session['usuario_dni'] = usuario.DNI
    request.session['usuario_rol'] = usuario.idRol.nom_rol

    if usuario.idRol.nom_rol.lower() == 'administrador':
        return redirect('admin_dashboard')
    else:
        return redirect('usuario_portal')

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

# ---- DASHBOARD DE ADMINISTRADOR (CRUD USUARIOS HITO 2 + FLOTA HITO 1) ----
def admin_dashboard(request):
    usuario_actual = get_usuario_actual(request)
    if not usuario_actual:
        return redirect('login')
    if usuario_actual.idRol.nom_rol.lower() != 'administrador':
        return redirect('usuario_portal')

    solo_activos = request.GET.get('activos') == '1'
    usuarios = Usuario.objects.select_related('idRol')
    if solo_activos:
        usuarios = usuarios.filter(Activo=True)
    usuarios = usuarios.order_by('Apellido', 'Nombre')

    roles = Rol.objects.all().order_by('id_rol')
    vehiculos = Vehiculo.objects.select_related('chofer_asignado').order_by('patente')
    choferes = Usuario.objects.filter(idRol__nom_rol='Chofer', Activo=True)

    return render(request, 'admin_dashboard.html', {
        'usuario_actual': usuario_actual,
        'usuarios': usuarios,
        'roles': roles,
        'solo_activos': solo_activos,
        'vehiculos': vehiculos,
        'choferes': choferes,
    })

# ---- PORTAL DE USUARIO OPERATIVO ----
def usuario_portal(request):
    usuario_actual = get_usuario_actual(request)
    if not usuario_actual:
        return redirect('login')
    
    permisos = usuario_actual.idRol.permisos.all()
    vehiculos = Vehiculo.objects.filter(chofer_asignado=usuario_actual)
    return render(request, 'usuario_portal.html', {
        'usuario_actual': usuario_actual,
        'permisos': permisos,
        'vehiculos': vehiculos,
    })

# ---- OPERACIONES CRUD ----
@require_POST
def alta_usuario(request):
    _, err = solo_admin(request)
    if err:
        return err
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

        # Regla: Apellido + primera letra del primer nombre
        base_user = generate_username(apellido, nombre)
        final_user = base_user
        idx = 1
        while Usuario.objects.filter(NombreUsuario=final_user).exists():
            final_user = f"{base_user}{idx}"
            idx += 1

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
def modificar_correo(request, dni):
    _, err = solo_admin(request)
    if err:
        return err
    # Regla estricta Hito 2: La Modificación solo permite editar el Correo
    usuario = get_object_or_404(Usuario, DNI=dni)
    nuevo_correo = request.POST.get('correo', '').strip().lower()

    if Usuario.objects.filter(Correo=nuevo_correo).exclude(DNI=dni).exists():
        return JsonResponse({'ok': False, 'error': 'El correo ya pertenece a otro usuario.'}, status=400)

    usuario.Correo = nuevo_correo
    usuario.save() # auto_now actualiza automáticamente FechaUltimaModificacion
    return JsonResponse({'ok': True, 'nuevo_correo': usuario.Correo})

@require_POST
def baja_usuario(request, dni):
    # Regla estricta Hito 2: Cambiar Activo a (no) y asentar FechaBaja
    actual, err = solo_admin(request)
    if err:
        return err

    usuario = get_object_or_404(Usuario, DNI=dni)

    if usuario.DNI == actual.DNI:
        return JsonResponse({'ok': False, 'error': 'No podes darte de baja a vos mismo.'}, status=400)

    # el sistema no puede quedarse sin administradores activos
    if usuario.idRol.nom_rol.lower() == 'administrador':
        quedan = Usuario.objects.filter(
            idRol__nom_rol__iexact='Administrador', Activo=True
        ).exclude(DNI=usuario.DNI).count()
        if quedan == 0:
            return JsonResponse({
                'ok': False,
                'error': 'No se puede dar de baja al ultimo administrador activo.'
            }, status=400)

    usuario.Activo = False
    usuario.FechaBaja = timezone.now()
    usuario.save()
    return JsonResponse({'ok': True})

@require_POST
def reactivar_usuario(request, dni):
    _, err = solo_admin(request)
    if err:
        return err
    usuario = get_object_or_404(Usuario, DNI=dni)
    usuario.Activo = True
    usuario.FechaBaja = None
    usuario.save()
    return JsonResponse({'ok': True})

@require_POST
def restablecer_clave(request, dni):
    _, err = solo_admin(request)
    if err:
        return err
    usuario = get_object_or_404(Usuario, DNI=dni)
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
def cambiar_rol(request, dni):
    """Asigna otro rol al usuario. Va aparte de la modificacion de correo,
    que por consigna solo puede editar el correo."""
    actual, err = solo_admin(request)
    if err:
        return err

    usuario = get_object_or_404(Usuario, DNI=dni)

    if usuario.DNI == actual.DNI:
        return JsonResponse({'ok': False, 'error': 'No podes cambiar tu propio rol.'}, status=400)

    try:
        rol = Rol.objects.get(id_rol=int(request.POST.get('idRol')))
    except (Rol.DoesNotExist, TypeError, ValueError):
        return JsonResponse({'ok': False, 'error': 'El rol indicado no existe.'}, status=400)

    anterior = usuario.idRol
    if anterior.id_rol == rol.id_rol:
        return JsonResponse({'ok': False, 'error': f'{usuario.NombreUsuario} ya tiene el rol {rol.nom_rol}.'}, status=400)

    # Nota: no hace falta proteger al "ultimo administrador" aca. Quien ejecuta
    # esta accion ya es administrador activo, y no puede cambiarse el rol a si
    # mismo, asi que siempre queda al menos uno. El caso real de bloqueo se da
    # en la baja, y ahi si esta contemplado.

    usuario.idRol = rol
    usuario.save()

    return JsonResponse({'ok': True, 'usuario': usuario.NombreUsuario,
                         'anterior': anterior.nom_rol, 'nuevo': rol.nom_rol})

@require_GET
def preview_username_view(request):
    _, err = solo_admin(request)
    if err:
        return err
    ape = request.GET.get('apellido', '')
    nom = request.GET.get('nombre', '')
    return JsonResponse({'NombreUsuario': generate_username(ape, nom)})
