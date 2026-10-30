"""Log de auditoría automático (Hito 4).

Cada vez que se modifica, anula, da de baja o borra un registro de cualquier tabla del sistema,
queda una fila en LOG_AUDITORIA con los valores de antes y los de después, la fecha y hora y el
usuario logueado. No hace falta llamarlo desde cada pantalla: lo hacen las señales de Django
sobre todos los modelos de esta app. Las altas no se registran (la consigna pide modificaciones
y anulaciones).
"""
import contextvars
import json

from django.core.serializers.json import DjangoJSONEncoder
from django.db.models.signals import post_delete, post_save, pre_save

# Quién está haciendo la operación en este pedido HTTP (lo pone el middleware)
_usuario = contextvars.ContextVar('usuario_auditoria', default=None)

# Campos que cambian solos y no dicen nada de lo que hizo la persona
IGNORADOS = {'FechaUltimoAcceso', 'FechaUltimaModificacion'}
# Campos que no se guardan en claro
OCULTOS = {'Clave'}


def usuario_actual():
    return _usuario.get()


def con_usuario(usuario):
    """Para scripts o pruebas: `with con_usuario(admin): ...` registra a ese usuario."""
    class _Contexto:
        def __enter__(self):
            self.token = _usuario.set(usuario)

        def __exit__(self, *exc):
            _usuario.reset(self.token)
    return _Contexto()


class AuditoriaMiddleware:
    """Deja el usuario de la sesión a mano para las señales."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        from .permisos import get_usuario_actual
        token = _usuario.set(get_usuario_actual(request))
        try:
            return self.get_response(request)
        finally:
            _usuario.reset(token)


def _valores(instancia):
    """{campo: valor} de las columnas del registro (las FK como su clave)."""
    datos = {}
    for campo in instancia._meta.concrete_fields:
        if campo.name in IGNORADOS:
            continue
        datos[campo.name] = getattr(instancia, campo.attname)
    return datos


def _json(datos):
    """Los valores en JSON; la clave se compara pero nunca se guarda."""
    return json.dumps({c: '(oculta)' if c in OCULTOS else v for c, v in datos.items()},
                      cls=DjangoJSONEncoder, ensure_ascii=False)


def _registrar(sender, instancia, accion, antes, despues):
    from .models import LogAuditoria
    usuario = usuario_actual()
    LogAuditoria.objects.create(
        tabla=sender._meta.db_table, id_registro=str(instancia.pk), accion=accion,
        valores_anteriores=_json(antes), valores_nuevos=_json(despues) if despues is not None else '',
        usuario=usuario if getattr(usuario, 'pk', None) else None)


def _auditable(sender):
    return sender._meta.app_label == 'usuarios' and sender.__name__ != 'LogAuditoria'


def antes_de_guardar(sender, instance, **kwargs):
    if not _auditable(sender) or instance._state.adding or instance.pk is None:
        return
    viejo = sender.objects.filter(pk=instance.pk).first()
    instance._auditoria_antes = _valores(viejo) if viejo else None


def despues_de_guardar(sender, instance, created, **kwargs):
    antes = getattr(instance, '_auditoria_antes', None)
    if created or not _auditable(sender) or antes is None:
        return
    instance._auditoria_antes = None
    ahora = _valores(instance)
    # por valor: 0 y 0.00 son lo mismo; el texto cubre tipos distintos (fecha y su texto)
    cambios = [c for c in ahora if c in antes and antes[c] != ahora[c] and str(antes[c]) != str(ahora[c])]
    if not cambios:
        return
    from .models import LogAuditoria
    accion = LogAuditoria.MODIFICACION
    if 'estado' in cambios and ahora.get('estado') == 'Anulado':
        accion = LogAuditoria.ANULACION
    elif 'Activo' in cambios:
        accion = LogAuditoria.REACTIVACION if ahora['Activo'] else LogAuditoria.BAJA
    _registrar(sender, instance, accion, {c: antes[c] for c in cambios}, {c: ahora[c] for c in cambios})


def despues_de_borrar(sender, instance, **kwargs):
    if not _auditable(sender):
        return
    from .models import LogAuditoria
    _registrar(sender, instance, LogAuditoria.ELIMINACION, _valores(instance), None)


def conectar():
    pre_save.connect(antes_de_guardar, dispatch_uid='auditoria_pre_save')
    post_save.connect(despues_de_guardar, dispatch_uid='auditoria_post_save')
    post_delete.connect(despues_de_borrar, dispatch_uid='auditoria_post_delete')
