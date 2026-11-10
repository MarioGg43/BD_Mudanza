"""Controladores REST de los ABM: vehículos, servicios y el catálogo de objetos.
Validan con los mismos formularios de Django que las pantallas viejas (VehiculoForm, ServicioForm,
ObjetoForm), así las reglas son exactamente las mismas: rangos, patente en mayúsculas, «Otro» fijo,
nombres repetidos, etc. Las bajas son lógicas: nada se borra porque los pedidos lo referencian."""
from django.db.models import Count, Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404

from pedidos import reglas
from pedidos.forms import ObjetoForm, ServicioTextoForm as ServicioForm, materiales_texto
from usuarios.models import Objeto, Pedido, Servicio, Usuario, Vehiculo
from usuarios.permisos import tiene_permiso
from vehiculos.forms import VehiculoForm
from .autenticacion import endpoint, error, leer_json


def _guardar(form):
    """Guarda el formulario o devuelve 400 con un mensaje por campo."""
    if not form.is_valid():
        return None, error('Revisá los datos marcados.', errores={k: ' '.join(v) for k, v in form.errors.items()})
    return form.save(), None


def _numero(valor):
    return float(valor) if valor is not None else None


# ------------------------------------------------------------------ vehículos

def _vehiculo(v):
    return {'patente': v.patente, 'marca_modelo': v.marca_modelo, 'tipo_vehiculo': v.tipo_vehiculo,
            'capacidad_kg': _numero(v.capacidad_kg), 'capacidad_m3': _numero(v.capacidad_m3), 'estado': v.estado,
            'kilometraje': _numero(v.kilometraje), 'anio': v.anio, 'recargo': v.recargo,
            'chofer_asignado': v.chofer_asignado_id, 'observaciones': v.observaciones or '',
            'chofer': f'{v.chofer_asignado.Nombre} {v.chofer_asignado.Apellido}' if v.chofer_asignado else None}


def _opciones_vehiculo():
    return {'tipos': Vehiculo.TIPOS, 'estados': [e for e, _ in Vehiculo._meta.get_field('estado').choices],
            'choferes': [{'id': u.id_usuario, 'nombre': f'{u.Apellido}, {u.Nombre}'} for u in
                         Usuario.objects.filter(idRol__nom_rol='Chofer', Activo=True).order_by('Apellido', 'Nombre')]}


@endpoint('VEH_GESTIONAR', metodos=('GET', 'POST'))
def vehiculos(request):
    """GET /api/vehiculos: la flota con sus avisos. POST: alta."""
    if request.method == 'POST':
        vehiculo, respuesta = _guardar(VehiculoForm(leer_json(request)))
        return respuesta or JsonResponse(_vehiculo(vehiculo), status=201)
    sin_chofer = Pedido.objects.filter(reglas.filtro_por_venir_sin_chofer()).values('pk')
    flota = (Vehiculo.objects.select_related('chofer_asignado')
             .annotate(cant_pedidos=Count('pedidos'),
                       mudanzas_sin_chofer=Count('pedidos', filter=Q(pedidos__in=sin_chofer)))
             .order_by('patente'))
    return JsonResponse({'vehiculos': [{**_vehiculo(v), 'cant_pedidos': v.cant_pedidos,
                                        'mudanzas_sin_chofer': v.mudanzas_sin_chofer} for v in flota],
                         **_opciones_vehiculo()})


def _fila_pedido(p):
    return {'id': p.id_pedido, 'fecha_servicio': p.fecha_servicio.isoformat(), 'horario': p.horario,
            'estado': p.estado, 'vencido': p.vencido, 'en_curso': p.en_curso,
            'cliente': f'{p.idUsuario.Apellido}, {p.idUsuario.Nombre}', 'chofer': (
                f'{p.chofer.Nombre} {p.chofer.Apellido}' if p.chofer else None)}


@endpoint('VEH_GESTIONAR', metodos=('GET', 'PUT'))
def vehiculo(request, patente):
    """GET /api/vehiculos/<patente>: datos y agenda. PUT: modificación (la patente no cambia)."""
    v = get_object_or_404(Vehiculo.objects.select_related('chofer_asignado'), pk=patente)
    if request.method == 'PUT':
        datos = {**leer_json(request), 'patente': v.patente}
        guardado, respuesta = _guardar(VehiculoForm(datos, instance=v))
        return respuesta or JsonResponse(_vehiculo(guardado))
    agenda = None
    if tiene_permiso(request.usuario, 'PED_GESTIONAR'):
        pedidos = v.pedidos.select_related('idUsuario').prefetch_related('personal__idUsuario')
        agenda = {
            'proximos': [_fila_pedido(p) for p in pedidos.filter(reglas.filtro_por_venir())
                         .order_by('fecha_servicio', 'hora_servicio')],
            'para_cerrar': [_fila_pedido(p) for p in pedidos.filter(reglas.filtro_para_finalizar() | reglas.filtro_vencidos())
                            .order_by('fecha_servicio', 'hora_servicio')],
            'historial': [_fila_pedido(p) for p in pedidos.exclude(estado__in=Pedido.ACTIVOS)
                          .order_by('-fecha_servicio', '-hora_servicio')[:30]],
        }
    return JsonResponse({**_vehiculo(v), 'agenda': agenda, **_opciones_vehiculo()})


@endpoint('VEH_GESTIONAR', metodos=('POST',))
def baja_vehiculo(request, patente):
    """POST /api/vehiculos/<patente>/baja: queda «Fuera de Servicio» (se reactiva editando el estado)."""
    v = get_object_or_404(Vehiculo, pk=patente)
    if reglas.tiene_pedidos_activos(patente_vehiculo=v):
        return error(f'El vehículo {v.patente} tiene pedidos pendientes o confirmados. '
                     'Anulalos o reasignalos antes de darlo de baja.')
    v.estado = 'Fuera de Servicio'
    v.save(update_fields=['estado'])
    return JsonResponse({'patente': v.patente, 'estado': v.estado})


# ------------------------------------------------------------------ servicios

def _servicio_abm(s):
    return {'id': s.id_servicio, 'Tipo_servicio': s.Tipo_servicio, 'Categoria': s.Categoria,
            'Precio_base': _numero(s.Precio_base), 'Duracion_horas': s.Duracion_horas, 'Activo': s.Activo,
            'materiales': materiales_texto(s)}


def _limites_servicio():
    return {'categorias': [c for c, _ in Servicio.CATEGORIAS], 'min_horas': reglas.MIN_HORAS, 'max_horas': reglas.MAX_HORAS}


@endpoint('SRV_GESTIONAR', metodos=('GET', 'POST'))
def servicios(request):
    """GET /api/servicios: todos (activos primero). POST: alta."""
    if request.method == 'POST':
        servicio, respuesta = _guardar(ServicioForm(leer_json(request)))
        return respuesta or JsonResponse(_servicio_abm(servicio), status=201)
    lista = (Servicio.objects.prefetch_related('recursos__idMaterial')
             .annotate(cant_pedidos=Count('detalles__idPedido', distinct=True))
             .order_by('-Activo', '-Categoria', 'Tipo_servicio'))
    return JsonResponse({'servicios': [{**_servicio_abm(s), 'cant_pedidos': s.cant_pedidos} for s in lista],
                         **_limites_servicio()})


@endpoint('SRV_GESTIONAR', metodos=('GET', 'PUT'))
def servicio(request, id_servicio):
    s = get_object_or_404(Servicio, pk=id_servicio)
    if request.method == 'PUT':
        guardado, respuesta = _guardar(ServicioForm(leer_json(request), instance=s))
        return respuesta or JsonResponse(_servicio_abm(guardado))
    return JsonResponse({**_servicio_abm(s), **_limites_servicio()})


@endpoint('SRV_GESTIONAR', metodos=('POST',))
def baja_servicio(request, id_servicio):
    """Deja de ofrecerse; los pedidos que ya lo tienen lo conservan."""
    s = get_object_or_404(Servicio, pk=id_servicio)
    s.Activo = False
    s.save(update_fields=['Activo'])
    return JsonResponse({'id': s.id_servicio, 'Activo': False})


# ------------------------------------------------------------------ objetos

def _objeto(o, usos=None):
    return {'id': o.id_objeto, 'nom_objeto': o.nom_objeto, 'Activo': o.Activo, 'otro': o.es_otro, 'usos': usos}


@endpoint('OBJ_GESTIONAR', metodos=('GET', 'POST'))
def objetos(request):
    """GET /api/objetos: el catálogo con cuántas veces se usó cada uno. POST: alta."""
    if request.method == 'POST':
        objeto, respuesta = _guardar(ObjetoForm(leer_json(request)))
        return respuesta or JsonResponse(_objeto(objeto), status=201)
    lista = Objeto.objects.annotate(usos=Count('inventarios')).order_by('-Activo', 'nom_objeto')
    return JsonResponse({'objetos': [_objeto(o, o.usos) for o in lista]})


@endpoint('OBJ_GESTIONAR', metodos=('PUT',))
def objeto(request, id_objeto):
    o = get_object_or_404(Objeto, pk=id_objeto)
    if o.es_otro:
        return error('«Otro» es fijo: es la opción para lo que no está en la lista.')
    guardado, respuesta = _guardar(ObjetoForm(leer_json(request), instance=o))
    return respuesta or JsonResponse(_objeto(guardado))


@endpoint('OBJ_GESTIONAR', metodos=('POST',))
def baja_objeto(request, id_objeto):
    o = get_object_or_404(Objeto, pk=id_objeto)
    if o.es_otro:
        return error('«Otro» no se puede dar de baja: es la opción para lo que no está en la lista.')
    o.Activo = False
    o.save(update_fields=['Activo'])
    return JsonResponse({'id': o.id_objeto, 'Activo': False})
