"""Bandeja de notificaciones y configuración de los umbrales (Parcial N° 2, M3)."""
from django.contrib import messages
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST

from usuarios.models import Configuracion
from usuarios.permisos import get_usuario_actual, requiere_permiso

from . import reglas

# qué tipo de valor lleva cada parámetro y entre qué límites (se valida al guardar)
LIMITES = {
    'horas_sin_confirmar': (1, 720), 'minutos_atraso': (5, 1440),
    'cancelaciones_cliente': (1, 50), 'dias_cancelaciones': (1, 730), 'correo_al_cliente': (0, 1),
}


def bandeja(request):
    usuario = get_usuario_actual(request)
    if not usuario:
        return redirect('login')
    todas = reglas.de_usuario(usuario).select_related('destino_perfil')
    ver = request.GET.get('ver', 'sin_leer')
    lista = todas.filter(leida=False) if ver == 'sin_leer' else todas
    pagina = Paginator(lista, 20).get_page(request.GET.get('pagina'))
    return render(request, 'notificaciones/bandeja.html', {
        'pagina': pagina, 'ver': ver, 'sin_leer': todas.filter(leida=False).count(), 'total': todas.count()})


@require_POST
def abrir(request, id_notificacion):
    """Marca la notificación como leída y lleva a lo que avisa (el pedido)."""
    usuario = get_usuario_actual(request)
    if not usuario:
        return redirect('login')
    notif = get_object_or_404(reglas.de_usuario(usuario), pk=id_notificacion)  # ajena = 404
    if not notif.leida:
        notif.leida, notif.fecha_lectura = True, timezone.now()
        notif.save(update_fields=['leida', 'fecha_lectura'])
    destino = notif.enlace if request.POST.get('ir') and notif.enlace else ''
    if destino and url_has_allowed_host_and_scheme(destino, allowed_hosts={request.get_host()}):
        return redirect(destino)
    return redirect(request.POST.get('volver') or 'notificaciones_bandeja')


@require_POST
def leer_todas(request):
    usuario = get_usuario_actual(request)
    if not usuario:
        return redirect('login')
    n = reglas.de_usuario(usuario).filter(leida=False).update(leida=True, fecha_lectura=timezone.now())
    messages.success(request, f'Marcaste {n} notificaci{"ones" if n != 1 else "ón"} como leída{"s" if n != 1 else ""}.')
    return redirect('notificaciones_bandeja')


@requiere_permiso('CFG_GESTIONAR')
def configuracion(request):
    parametros = list(Configuracion.objects.all())
    errores = {}
    if request.method == 'POST':
        nuevos = {}
        for p in parametros:
            valor = request.POST.get(p.clave, '').strip()
            if p.clave in LIMITES:
                minimo, maximo = LIMITES[p.clave]
                if not valor.isdigit() or not minimo <= int(valor) <= maximo:
                    errores[p.clave] = f'Tiene que ser un número entero de {minimo} a {maximo}.'
            elif valor and '@' not in valor:
                errores[p.clave] = 'Escribí un correo válido o dejalo vacío.'
            nuevos[p.clave] = valor
        if not errores:
            for p in parametros:
                if p.valor != nuevos[p.clave]:
                    p.valor = nuevos[p.clave]
                    p.save(update_fields=['valor'])  # queda en la auditoría: quién cambió qué umbral
            messages.success(request, 'Guardamos los umbrales. Las reglas los usan desde ahora.')
            return redirect('notificaciones_configuracion')
        for p in parametros:
            p.valor = nuevos[p.clave]
    return render(request, 'notificaciones/configuracion.html', {
        'parametros': parametros, 'errores': errores, 'limites': LIMITES})


@require_POST
@requiere_permiso('CFG_GESTIONAR')
def evaluar_ahora(request):
    """Corre ya la tarea programada (para la defensa: no hace falta esperar 15 minutos)."""
    nuevas = reglas.evaluar_programadas()
    total = sum(nuevas.values())
    detalle = ', '.join(f'{regla}: {n}' for regla, n in nuevas.items())
    messages.success(request, f'Evaluamos las reglas programadas: {total} aviso{"s" if total != 1 else ""} '
                              f'nuevo{"s" if total != 1 else ""} ({detalle}).')
    return redirect('notificaciones_configuracion')
