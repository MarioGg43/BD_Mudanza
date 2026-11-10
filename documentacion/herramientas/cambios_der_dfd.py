"""Genera el Word con los cambios pendientes del DER y de los DFD (Grupo 5).

Uso: python documentacion/herramientas/cambios_der_dfd.py "<ruta de salida>.docx"  (necesita python-docx)
"""
import sys

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Pt, RGBColor

SALIDA = sys.argv[1]
NARANJA = RGBColor(0xC0, 0x4F, 0x00)
TINTA = RGBColor(0x23, 0x1A, 0x15)

doc = Document()
st = doc.styles['Normal']
st.font.name = 'Calibri'
st.font.size = Pt(10.5)
for s in doc.sections:
    s.left_margin = s.right_margin = Pt(54)
    s.top_margin = s.bottom_margin = Pt(50)


def fondo(celda, color):
    tc = celda._tc.get_or_add_tcPr()
    sh = OxmlElement('w:shd')
    sh.set(qn('w:val'), 'clear')
    sh.set(qn('w:color'), 'auto')
    sh.set(qn('w:fill'), color)
    tc.append(sh)


def titulo(texto, nivel=1):
    h = doc.add_heading(texto, level=nivel)
    for r in h.runs:
        r.font.color.rgb = NARANJA if nivel > 1 else TINTA
    return h


def parrafo(texto, negrita_inicio=None):
    p = doc.add_paragraph()
    if negrita_inicio:
        p.add_run(negrita_inicio).bold = True
    p.add_run(texto)
    return p


def lista(items):
    for it in items:
        p = doc.add_paragraph(style='List Bullet')
        if isinstance(it, tuple):
            p.add_run(it[0]).bold = True
            p.add_run(it[1])
        else:
            p.add_run(it)


def tabla(encabezado, filas, anchos=None):
    t = doc.add_table(rows=1, cols=len(encabezado))
    t.style = 'Table Grid'
    for i, h in enumerate(encabezado):
        c = t.rows[0].cells[i]
        c.text = ''
        run = c.paragraphs[0].add_run(h)
        run.bold = True
        run.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)
        fondo(c, 'C04F00')
    for fila in filas:
        celdas = t.add_row().cells
        for i, v in enumerate(fila):
            celdas[i].text = v
    for fila in t.rows:
        for c in fila.cells:
            for p in c.paragraphs:
                for r in p.runs:
                    r.font.size = Pt(9.5)
    if anchos:
        for fila in t.rows:
            for i, w in enumerate(anchos):
                fila.cells[i].width = Pt(w)
    doc.add_paragraph()
    return t


# ---------------------------------------------------------------- portada
t = doc.add_heading('Cambios pendientes en el DER y los DFD', 0)
for r in t.runs:
    r.font.color.rgb = TINTA
p = doc.add_paragraph('Mudanzas y Fletes Salta · Grupo 5 · Actualizado al 09/11/2026')
p.runs[0].italic = True
parrafo('Este documento junta todo lo que hay que agregar o corregir en el DER de alto refinamiento '
        'y en los DFD del documento oficial para que coincidan con lo que ya hace el sistema y con '
        'las reglas de notación del grupo. Está dividido en: (1) cambios obligatorios porque el sistema '
        'ya funciona así, (2) correcciones de notación en los DFD, (3) DFD que faltan y (4) lo que quedó '
        'fuera del alcance.')

parrafo('Reglas de notación que se usan para revisar (las acordadas con el profesor):', None)
lista([
    'Los procesos se nombran con verbo en infinitivo («Registrar un Pedido»).',
    'Los flujos se nombran con un sustantivo que nombra el dato («Datos del pedido», «Patente»). '
    'Nunca con una acción: «solicitud», «confirmación», «validación», «asignación» y «aviso» están mal.',
    'Para consultar un almacén: flecha de ida con la clave (DNI, patente, id) y flecha de vuelta con los datos.',
    'Una flecha sola hacia un almacén significa que se guarda algo.',
    'Un almacén nunca confirma, avisa ni valida.',
    'Un proceso hace una sola tarea.',
])

# ---------------------------------------------------------------- DER
titulo('1. DER: cambios obligatorios (el sistema ya funciona así)')

titulo('1.1 Tabla nueva: OBJETOS (catálogo del inventario)', 2)
parrafo('La profesora pidió que el inventario no sea texto libre, para evitar variantes como «mesa», '
        '«meza» o «Mesa». El cliente ahora elige el objeto de una lista; lo que no está va como «Otro» '
        'con la observación obligatoria. El administrador amplía la lista desde la pantalla «Objetos».')
tabla(['Campo', 'Tipo', 'Clave', 'Descripción'], [
    ['id_objeto', 'INT', 'PK', 'Identificador del objeto'],
    ['nom_objeto', 'VARCHAR(100)', 'Único', 'Nombre (Heladera, Mesa, Cajas, Otro…)'],
    ['estado_objeto', 'BOOLEAN', '', 'Activo / dado de baja (baja lógica)'],
], [90, 90, 50, 230])

titulo('1.2 INVENTARIO_DETALLES', 2)
tabla(['Cambio', 'Antes', 'Después'], [
    ['Campo nuevo', '—', 'Cantidad_declarada INT (lo que declaró el cliente, si el chofer lo corrigió; 0 = no lo declaró)'],
    ['Reemplazar campo', 'desc_inventario VARCHAR(100)', 'id_objeto INT (FK → OBJETOS)'],
    ['Se mantienen', 'Cantidad, obser_inventario, Fragil, id_pedido', 'Igual'],
    ['Relación nueva', '—', 'OBJETOS 1 : N INVENTARIO_DETALLES'],
], [100, 170, 190])

titulo('1.3 SERVICIOS: principal y adicionales', 2)
parrafo('Un pedido lleva un servicio principal (Mudanza local, Mudanza nacional o Flete urbano) y, '
        'opcionales, adicionales con su precio (Embalaje $25.000, Desarmado y armado de muebles $35.000, '
        'Ayudante extra $20.000).')
tabla(['Campo nuevo', 'Tipo', 'Valores'], [
    ['categoria_servicio', 'VARCHAR(10)', 'Principal / Adicional'],
    ['Duracion_horas', 'SMALLINT (puede ser nulo)', 'Horas que ocupa el vehículo y el personal: de 5 a 120 '
                                                   '(5 días). Solo los principales; los adicionales quedan vacíos'],
], [140, 100, 220])
parrafo('El precio del principal es el de un camión chico: con uno mediano se suma un 25 % y con uno '
        'grande, un 50 % (ver VEHICULOS). Estado_servicio (BOOLEAN) ya está en el DER. '
        'Duraciones cargadas: Flete urbano 5 h, Mudanza local 10 h, Mudanza nacional 48 h.')

titulo('1.4 DETALLE_PEDIDOS: precio del día', 2)
parrafo('Hay una fila por cada servicio del pedido (el principal y los adicionales). El sistema guarda el '
        'precio que tenía el servicio el día del pedido, para que si después cambia el precio el '
        'comprobante viejo no cambie.')
tabla(['Campo nuevo', 'Tipo', 'Descripción'], [
    ['precio_unitario', 'DECIMAL', 'Precio del servicio el día del pedido (el principal, con el recargo del camión)'],
    ['subtotal', 'DECIMAL', 'Igual al precio (no hay cantidades por servicio)'],
], [120, 80, 260])

titulo('1.5 PEDIDOS: fechas, duración, total y anulación', 2)
parrafo('En el DER, «Fec_pedido» no deja claro si es el día en que se pidió o el día de la mudanza. '
        'El sistema guarda las dos.')
tabla(['Campo', 'Tipo', 'Descripción'], [
    ['Fec_pedido', 'DATE', 'Día en que el cliente registró el pedido'],
    ['Fec_servicio (nuevo)', 'DATE', 'Día de la mudanza'],
    ['Hora_pedido', 'TIME', 'Hora de inicio de la mudanza (ya está)'],
    ['Duracion_horas (nuevo)', 'SMALLINT', 'Copia de la duración del servicio principal al pedir (si el '
                                           'servicio cambia, el pedido no). Fin = inicio + duración'],
    ['Total_pedido (nuevo)', 'DECIMAL', 'Principal con el recargo del camión + adicionales (calculado)'],
    ['id_usuario_anulacion (nuevo)', 'INT (FK → USUARIOS)', 'Quién anuló el pedido'],
    ['Recargo_pedido, Motivo_recargo (nuevos)', 'DECIMAL, VARCHAR(200)', 'Recargo que carga el chofer en el relevamiento '
                                                                       '(se suma al total) y su motivo'],
    ['Inicio_real, Fin_real (nuevos)', 'DATETIME', 'Hora real en que el chofer marcó «Empezamos» y «Terminamos» '
                                                 'desde el portal (al terminar, el pedido queda Finalizado)'],
    ['Lat_origen, Lon_origen, Lat_destino, Lon_destino (nuevos)', 'DECIMAL(9,6)',
     'El punto exacto de cada dirección (latitud y longitud), si el cliente lo marcó en el mapa o confirmó el '
     'que encontró el sistema («¿Es acá?»). Opcionales: sin punto, el mapa busca la dirección por el texto'],
], [140, 110, 210])
parrafo('Estados posibles de Estado_pedido: Pendiente, Confirmado, Finalizado, Anulado. «Vencido», '
        '«Para finalizar» y «Atrasada» NO son estados guardados: el sistema los calcula con la fecha, la '
        'hora y la duración, así que no van en el DER. Atrasada = confirmada, pasó su fin estimado sin '
        'finalizar y el mismo vehículo o personal tiene otra mudanza dentro de las 12 horas siguientes.')

titulo('1.6 VEHICULOS: tipo y chofer', 2)
tabla(['Campo', 'Tipo', 'Descripción'], [
    ['tipo_vehiculo (nuevo)', 'VARCHAR(50)', 'Lista cerrada por tamaño: Camión Chico (+0 %), Camión Mediano '
                                             '(+25 %) y Camión Grande (+50 % sobre el servicio principal)'],
    ['id_chofer (nuevo)', 'INT (FK → USUARIOS)', 'Chofer asignado al vehículo (puede estar vacío)'],
    ['observaciones_vehiculo (nuevo)', 'TEXT', 'Notas del vehículo'],
], [140, 110, 210])
parrafo('Opción si la profesora lo pide: pasar el tipo a una tabla TIPO_VEHICULO (id_tipo_veh, nom_tipo_veh), '
        'igual que ESTADO_VEHICULO.')

titulo('1.7 Tabla nueva: PERSONAL_PEDIDO (ya está en el sistema)', 2)
parrafo('El documento dice que RECURSOS_ASIGNADOS «asocia los empleados», pero en el DER solo relaciona '
        'servicio con materiales. El sistema ya guarda qué chofer y qué ayudantes van a cada mudanza en '
        'esta tabla: el chofer es obligatorio para confirmar el pedido y una persona no puede estar en dos '
        'mudanzas cuyos horarios se crucen.')
tabla(['Campo', 'Tipo', 'Clave'], [
    ['id_personal_pedido', 'INT', 'PK'],
    ['id_pedido', 'INT', 'FK → PEDIDOS'],
    ['id_usuario', 'INT', 'FK → USUARIOS (chofer o ayudante)'],
    ['funcion_personal', 'VARCHAR(10)', 'Chofer / Ayudante'],
], [160, 80, 220])
parrafo('Relaciones: PEDIDOS 1 : N PERSONAL_PEDIDO y USUARIOS 1 : N PERSONAL_PEDIDO.')

titulo('1.8 Tabla nueva: REPROGRAMACIONES (ya está en el sistema)', 2)
parrafo('Cuando una mudanza cambia de fecha, hora o vehículo (por ejemplo, por una demora en la mudanza '
        'anterior o un problema técnico), PEDIDOS guarda el horario nuevo y esta tabla guarda el historial: '
        'de cuándo a cuándo, por qué y quién lo hizo. El cliente ve el cambio en «Mis pedidos».')
tabla(['Campo', 'Tipo', 'Clave / descripción'], [
    ['id_reprogramacion', 'INT', 'PK'],
    ['id_pedido', 'INT', 'FK → PEDIDOS'],
    ['Fecha_anterior, Hora_anterior', 'DATE, TIME', 'Horario de antes'],
    ['patente_anterior', 'VARCHAR(15)', 'FK → VEHICULOS (vehículo de antes)'],
    ['Fecha_nueva, Hora_nueva', 'DATE, TIME', 'Horario nuevo'],
    ['patente_nueva', 'VARCHAR(15)', 'FK → VEHICULOS (puede ser el mismo)'],
    ['Motivo_reprog', 'VARCHAR(40)', 'Lista cerrada: Demora en una mudanza anterior, Problema técnico del '
                                     'vehículo, Clima, Pedido del cliente, Falta de personal, Otro'],
    ['Observacion_reprog', 'VARCHAR(200)', 'Obligatoria con «Otro»'],
    ['id_usuario', 'INT', 'FK → USUARIOS (quién reprogramó)'],
    ['Fec_reprog', 'DATETIME', 'Cuándo se hizo'],
    ['Visto_cliente', 'BOOLEAN', 'Si el cliente ya abrió el pedido después del cambio'],
], [150, 90, 220])
parrafo('Relaciones: PEDIDOS 1 : N REPROGRAMACIONES, VEHICULOS 1 : N REPROGRAMACIONES (dos veces: '
        'anterior y nuevo) y USUARIOS 1 : N REPROGRAMACIONES.')

titulo('1.9 Tabla nueva: LOG_AUDITORIA (pedido del Hito 4)', 2)
parrafo('Cada modificación, anulación, baja, reactivación o borrado de un registro de cualquier tabla deja '
        'una fila con los valores de antes y los de después, la fecha y hora y el usuario logueado. Se llena '
        'sola (no depende de cada pantalla) y se consulta con filtros en la pantalla «Auditoría» (permiso '
        'AUD_CONSULTAR). La clave de los usuarios nunca se guarda: figura como «(oculta)».')
tabla(['Campo', 'Tipo', 'Clave / descripción'], [
    ['id_log', 'INT', 'PK'],
    ['tabla_log', 'VARCHAR(60)', 'Tabla del registro (PEDIDOS, USUARIOS, VEHICULOS, …)'],
    ['id_registro_log', 'VARCHAR(60)', 'Clave del registro modificado (texto: la de VEHICULOS es la patente)'],
    ['accion_log', 'VARCHAR(20)', 'Modificación, Anulación, Baja, Reactivación o Eliminación'],
    ['valores_anteriores_log', 'TEXT (JSON)', 'Los campos que cambiaron, con su valor anterior'],
    ['valores_nuevos_log', 'TEXT (JSON)', 'Los mismos campos con su valor nuevo'],
    ['fec_hora_log', 'DATETIME', 'Fecha y hora'],
    ['id_usuario', 'INT', 'FK → USUARIOS (quién lo hizo; vacío si fue el sistema)'],
], [150, 90, 220])
parrafo('Relación: USUARIOS 1 : N LOG_AUDITORIA. No tiene FK a las demás tablas a propósito: guarda el nombre '
        'de la tabla y la clave como texto para poder auditar cualquiera.')

titulo('1.10 Tabla nueva: NOTIFICACION (Parcial N° 2, M3)', 2)
parrafo('Cada aviso que genera una regla de notificación queda guardado acá: aparece en la campanita y en la '
        'bandeja del perfil destino (o de un usuario puntual, como el cliente). Las columnas que pide la consigna '
        'son id, fecha, tipo, mensaje, destino_perfil, leída y fecha_lectura; el sistema agrega cuatro más.')
tabla(['Campo', 'Tipo', 'Clave / descripción'], [
    ['id_notificacion', 'INT', 'PK'],
    ['fecha_notif', 'DATETIME', 'Cuándo se generó'],
    ['tipo_notif', 'VARCHAR(40)', 'Pedido sin confirmar, Mudanza atrasada, Cliente con cancelaciones, '
                                  'Mudanza confirmada, Mudanza reprogramada, Stock bajo'],
    ['mensaje_notif', 'VARCHAR(300)', 'El texto del aviso'],
    ['id_rol_destino', 'INT', 'FK → ROLES (destino_perfil: a qué perfil le llega)'],
    ['leida_notif', 'BOOLEAN', 'Si ya se leyó'],
    ['fecha_lectura_notif', 'DATETIME', 'Cuándo se leyó (vacío si no)'],
    ['id_usuario_destino (agregado)', 'INT', 'FK → USUARIOS. Para un usuario puntual (el cliente); vacío = todo el perfil'],
    ['enlace_notif (agregado)', 'VARCHAR(200)', 'A qué pantalla lleva (el pedido)'],
    ['clave_notif (agregado)', 'VARCHAR(80)', 'Única. Ej.: «sin_confirmar:18». Impide que la misma alerta se cree dos veces'],
    ['correo_notif (agregado)', 'VARCHAR(200)', 'A quién se mandó el correo y si salió bien'],
], [150, 90, 220])
parrafo('Relaciones: ROLES 1 : N NOTIFICACION y USUARIOS 1 : N NOTIFICACION.')

titulo('1.11 Tabla nueva: CONFIGURACION (Parcial N° 2, M3)', 2)
parrafo('Los umbrales de las reglas de notificación. La consigna pide que no estén escritos en el código: se '
        'cambian desde la pantalla «Umbrales de alertas» (permiso CFG_GESTIONAR) y cada cambio queda en LOG_AUDITORIA.')
tabla(['Campo', 'Tipo', 'Clave / descripción'], [
    ['id_configuracion', 'INT', 'PK'],
    ['clave_conf', 'VARCHAR(60)', 'Único. Nombre del parámetro'],
    ['valor_conf', 'VARCHAR(150)', 'El valor (número o correo)'],
    ['descripcion_conf', 'VARCHAR(200)', 'Qué controla'],
], [150, 90, 220])
parrafo('Filas que se cargan: horas_sin_confirmar (48), correo_empresa (vacío), minutos_atraso (60), '
        'cancelaciones_cliente (3), dias_cancelaciones (90) y correo_al_cliente (1 = sí). No tiene relaciones: '
        'las reglas la leen por la clave.')

titulo('1.12 Tabla nueva: MATERIALES (control de materiales)', 2)
parrafo('El catálogo de lo que se lleva a las mudanzas (mantas, correas, film, cajas…) con su stock. El stock no '
        'se escribe a mano: cambia solo con un movimiento (1.14), así siempre queda quién lo cambió y por qué.')
tabla(['Campo', 'Tipo', 'Clave / descripción'], [
    ['id_material', 'INT', 'PK'],
    ['nom_material', 'VARCHAR(60)', 'Único. Ej.: «Mantas acolchadas»'],
    ['unidad_material', 'VARCHAR(20)', 'unidades, rollos, kits…'],
    ['stock_material', 'INT', 'Cuánto hay en el depósito'],
    ['stock_min_material', 'INT', 'Si el stock baja de este número, avisa al administrador (regla 5)'],
    ['reutilizable_material', 'BOOLEAN', 'Sí: sale con la mudanza y vuelve (mantas, correas). No: se gasta (film, cajas)'],
    ['estado_material', 'BOOLEAN', 'Baja lógica: dado de baja ya no sale en las mudanzas'],
], [150, 90, 220])

titulo('1.13 RECURSOS_ASIGNADOS: el material deja de ser texto', 2)
parrafo('Antes guardaba los materiales del servicio como texto libre («Mantas, film y cintas»). Ahora apunta a '
        'MATERIALES y dice cuánto se sugiere llevar en cada mudanza con ese servicio.')
tabla(['Campo', 'Tipo', 'Clave / descripción'], [
    ['id_recursos_asignados', 'INT', 'PK'],
    ['id_servicio', 'INT', 'FK → SERVICIOS'],
    ['id_material', 'INT', 'FK → MATERIALES (reemplaza la columna de texto «Materiales», que se saca)'],
    ['cant_sugerida', 'SMALLINT', 'Cuánto se lleva por mudanza. Ej.: Mudanza local → 12 mantas'],
], [150, 90, 220])
parrafo('Un material aparece una sola vez por servicio (único id_servicio + id_material). Relaciones: '
        'SERVICIOS 1 : N RECURSOS_ASIGNADOS y MATERIALES 1 : N RECURSOS_ASIGNADOS (es la tabla intermedia de la '
        'relación N : M entre servicios y materiales).')

titulo('1.14 Tabla nueva: MOVIMIENTOS_MATERIAL', 2)
parrafo('Cada entrada o salida de stock. Es el historial del material y lo que permite saber qué se llevó y qué '
        'volvió de cada mudanza.')
tabla(['Campo', 'Tipo', 'Clave / descripción'], [
    ['id_mov_material', 'INT', 'PK'],
    ['id_material', 'INT', 'FK → MATERIALES'],
    ['id_pedido', 'INT', 'FK → PEDIDOS (vacío en compras y ajustes)'],
    ['id_usuario', 'INT', 'FK → USUARIOS (quién lo registró; vacío si fue el sistema)'],
    ['tipo_mov', 'VARCHAR(15)', 'Ingreso, Salida, Devolución, Consumo, Pérdida, Ajuste'],
    ['cant_mov', 'INT', 'Cantidad (en un Ajuste puede ser negativa)'],
    ['fec_mov', 'DATETIME', 'Fecha y hora'],
    ['observacion_mov', 'VARCHAR(200)', 'Ej.: «Stock inicial», «Faltaron 2», motivo del ajuste'],
], [150, 90, 220])
tabla(['Movimiento', 'Cuándo', 'Efecto en el stock'], [
    ['Ingreso', 'El administrador carga una compra', 'Suma'],
    ['Salida', 'El chofer toca «Empezamos»: sale lo sugerido por los servicios (si no alcanza, lo que hay)', 'Resta'],
    ['Devolución', 'Al «Terminamos»: lo que vuelve (reutilizables) o sobra (consumibles); o se anula una mudanza en curso', 'Suma'],
    ['Consumo', 'Al «Terminamos»: lo que se gastó de un consumible', 'No cambia (ya salió)'],
    ['Pérdida', 'Al «Terminamos»: un reutilizable que no volvió', 'No cambia (ya salió)'],
    ['Ajuste', 'El administrador corrige después de contar (con motivo)', 'Suma o resta'],
], [80, 290, 90])
parrafo('Relaciones: MATERIALES 1 : N MOVIMIENTOS_MATERIAL, PEDIDOS 1 : N MOVIMIENTOS_MATERIAL y '
        'USUARIOS 1 : N MOVIMIENTOS_MATERIAL.')

titulo('1.15 PERMISOS: cuatro permisos nuevos (son filas, no cambia la estructura)', 2)
tabla(['Permiso', 'Para qué', 'Quién lo tiene'], [
    ['REP_CONSULTAR', 'Ver los reportes de desempeño del personal y de cambios y cancelaciones', 'Administrador'],
    ['REP_FINANZAS', 'Ver el reporte con montos (uso e ingresos de la flota). Es el «reporte sensible '
                     'restringido por perfil» que pide la consigna', 'Administrador'],
    ['CFG_GESTIONAR', 'Cambiar los umbrales de las alertas (CONFIGURACION)', 'Administrador'],
    ['MAT_GESTIONAR', 'Gestionar los materiales, cargar compras y ajustes y ver los movimientos', 'Administrador'],
], [110, 260, 90])
parrafo('Los reportes consolidados (M2) y la analítica (M1) no agregan tablas: leen PEDIDOS, DETALLE_PEDIDOS, '
        'SERVICIOS, PERSONAL_PEDIDO, REPROGRAMACIONES y VEHICULOS.')

titulo('1.16 Diferencias entre el DER del documento y el sistema', 2)
parrafo('El DER del documento tiene 16 tablas y el sistema trabaja con las del DER anterior. Estas tablas '
        'están en el DER pero el sistema todavía no las usa (hay que programarlas o explicarlo):')
lista([('ESTADO_USUARIO: ', 'el sistema usa Estado_usuario (BOOLEAN) dentro de USUARIOS.'),
       ('ESTADO_VEHICULO: ', 'el sistema usa una lista fija de estados dentro de VEHICULOS.'),
       ('COMPROBANTES: ', 'el sistema arma el comprobante en pantalla y en PDF desde PEDIDOS, sin guardarlo aparte.')])

# ---------------------------------------------------------------- DFD
titulo('2. DFD: correcciones de notación')

titulo('2.1 Registrar un Pedido (DFD principal)', 2)
tabla(['Qué está', 'Problema', 'Cómo corregirlo'], [
    ['No figura el inventario', 'El cliente carga qué hay que llevar y no hay almacén para eso',
     'Agregar almacenes OBJETOS (consulta: «Objetos disponibles») e INVENTARIO_DETALLES (guarda: «Objetos del pedido»)'],
    ['«Selección de servicio» / «Selección Vehículo» hacia los almacenes',
     'A un almacén se le manda la clave para consultar, no una «selección»',
     'Hacia Servicios: «id_servicio»; hacia Vehículos: «Patente»'],
    ['Un solo servicio', 'Ahora hay principal + adicionales', '«Servicios elegidos» (id_servicio principal + adicionales)'],
    ['Disponibilidad del vehículo', 'Depende de los pedidos que se cruzan con ese horario',
     'Consultar Pedidos con «Fecha, hora y duración» y que vuelvan los «Vehículos ocupados»'],
    ['«Confirmación pedido» (Administrador y Usuario)', '«Confirmación» es una acción',
     'Para el administrador: «Pedido confirmado» o «Estado del pedido»; al cliente le llega el «Comprobante»'],
    ['«Datos servicio», «Datos vehículo», «Datos usuario» hacia Pedidos', 'Está bien, pero son 3 flechas para un solo guardado',
     'Unificar en una flecha «Datos del pedido» hacia Pedidos'],
], [130, 150, 180])

titulo('2.2 Gestionar Vehículo', 2)
tabla(['Qué está', 'Problema', 'Cómo corregirlo'], [
    ['«Confirmación Vehículo», «Confirmación Baja», «Modificación Vehículo» saliendo del almacén',
     'Un almacén nunca confirma', 'Sacarlas. Si hace falta mostrar algo, que vuelva «Datos del vehículo»'],
    ['«Solicitud Alta», «Solicitud Baja»', '«Solicitud» es una acción',
     'Hacia el proceso: «Datos del vehículo» (alta) y «Patente» (baja)'],
    ['Datos del vehículo', 'Falta el tipo y el chofer', 'Agregar tipo_vehiculo e id_chofer a la estructura'],
    ['Alta, modificación y baja en un solo proceso', 'Regla: un proceso = una tarea',
     'Consultarlo con el profesor; si lo exige, separar en Registrar / Modificar / Dar de baja Vehículo'],
], [150, 130, 180])

titulo('2.3 Gestionar Usuario', 2)
tabla(['Qué está', 'Problema', 'Cómo corregirlo'], [
    ['«Aviso Baja» saliendo del almacén Usuarios', 'Un almacén no avisa', 'Sacarla'],
    ['«Baja usuario», «Usuario nuevo»', 'Nombran acciones', '«DNI del usuario» (baja) y «Datos del usuario» (alta)'],
], [150, 130, 180])

titulo('2.4 Validar Usuario', 2)
tabla(['Qué está', 'Problema', 'Cómo corregirlo'], [
    ['«Validación Credenciales» (desde Usuarios y hacia Roles)', 'Un almacén no valida y «validación» es una acción',
     'Hacia Usuarios: «Usuario o DNI»; de vuelta: «Credenciales del usuario» (clave cifrada, estado, id_rol)'],
    ['Hacia Roles', 'Se manda la clave para consultar', '«id_rol» y de vuelta «Rol del usuario»'],
], [150, 130, 180])

titulo('2.5 Asignar Rol', 2)
tabla(['Qué está', 'Problema', 'Cómo corregirlo'], [
    ['«modificar permisos» (desde Administrador)', 'Es un verbo', '«Permisos del rol»'],
    ['«permiso modificado», «rol asignado» saliendo de los almacenes', 'El almacén no confirma lo que se guardó',
     'Sacarlas; las flechas hacia el almacén ya muestran que se guarda'],
    ['Asigna roles y también edita permisos', 'Son dos tareas',
     'Separar: «Asignar Rol» (a un usuario) y «Editar Permisos del Rol» (pantalla Roles)'],
], [150, 130, 180])

titulo('2.6 Asignar Recursos al Pedido', 2)
tabla(['Qué está', 'Problema', 'Cómo corregirlo'], [
    ['«Asignación de usuario»', 'Es una acción', '«Personal asignado» (id_pedido, id_usuario)'],
    ['Entidad externa «usuarios» con el mismo nombre que el almacén', 'Se confunde', 'Llamar a la entidad «Personal»'],
    ['El personal se guarda en «recursos asignados»', 'Esa tabla es servicio–materiales',
     'Guardar en el almacén nuevo PERSONAL_PEDIDO (consulta: «Horario de la mudanza» → «Personal ocupado»)'],
    ['«Usuario actualizado», «Vehículo actualizado»', 'El proceso no modifica usuarios ni vehículos',
     'Revisar: si solo se asignan, sacarlas'],
], [150, 130, 180])

# ---------------------------------------------------------------- DFD que faltan
titulo('3. DFD que faltan (el sistema ya los tiene)')
tabla(['Proceso', 'Quién lo estimula', 'Almacenes'], [
    ['Registrar Cliente', 'Cliente (se crea la cuenta)', 'Usuarios, Roles'],
    ['Gestionar Servicios', 'Administrador (con los materiales y la cantidad por mudanza)',
     'Servicios, Recursos asignados, Materiales'],
    ['Gestionar Objetos', 'Administrador', 'Objetos'],
    ['Confirmar Pedido', 'Administrador', 'Pedidos'],
    ['Finalizar Pedido', 'Administrador (solo desde la fecha y hora de la mudanza)', 'Pedidos'],
    ['Anular Pedido', 'Administrador (con motivo; queda quién y cuándo)', 'Pedidos'],
    ['Relevamiento de la Mudanza', 'Chofer al llegar: cantidades reales, objetos no declarados, adicionales y recargo',
     'Pedidos, Inventario detalles, Detalle pedidos, Objetos, Servicios'],
    ['Editar Servicios del Pedido', 'Administrador (el total se recalcula)', 'Pedidos, Detalle pedidos, Servicios'],
    ['Modificar Pedido', 'Cliente hasta 24 h antes (vuelve a Pendiente)',
     'Pedidos, Detalle pedidos, Inventario detalles, Vehículos, Reprogramaciones'],
    ['Cancelar Pedido', 'Cliente hasta 24 h antes (queda Anulado con su motivo)', 'Pedidos'],
    ['Registrar Inicio y Fin de la Mudanza', 'Chofer de esa mudanza (desde el portal; los ayudantes no). '
                                             'Dispara la salida y el cierre de materiales (3.2)',
     'Pedidos, Personal pedido'],
    ['Consultar Auditoría', 'Administrador (filtros por fecha, tabla, acción, usuario y registro)', 'Log auditoría'],
    ['Reprogramar Pedido', 'Administrador (con motivo de una lista). Sale hacia el Cliente: «Horario nuevo '
                           'de la mudanza» (no «Aviso de cambio de horario»: «aviso» es una acción)',
     'Pedidos, Reprogramaciones, Vehículos, Personal pedido, Notificación'],
    ['Consultar Pedidos', 'Administrador (todos, con los avisos: atrasadas, vencidos, para finalizar, por '
                          'confirmar, sin chofer) o Cliente (los suyos), con filtros',
     'Pedidos, Usuarios, Servicios, Vehículos, Personal pedido'],
    ['Emitir Comprobante', 'Administrador o Cliente', 'Pedidos, Detalle pedidos, Inventario detalles'],
], [130, 190, 140])

titulo('3.1 DFD nuevos por el Parcial N° 2 y lo que se agregó después del Hito 4', 2)
parrafo('Con las mismas reglas: flujos con sustantivos que nombran el dato y almacenes que nunca confirman ni avisan. '
        'Las entidades externas nuevas son «Reloj del sistema» (la tarea programada que corre cada 15 minutos), '
        '«Servidor de correo» (Gmail) y «Servicio de mapas» (OpenRouteService).')
tabla(['Proceso', 'Quién lo estimula', 'Almacenes', 'Flujos principales'], [
    ['Evaluar Alertas Programadas', 'Reloj del sistema (cada 15 minutos)', 'Pedidos, Configuración, Notificación',
     'Hacia Configuración: «Clave del parámetro» → «Umbral». Hacia Pedidos: «Fecha y hora actual» → «Pedidos '
     'pendientes y confirmados». Guarda en Notificación: «Datos de la notificación». Al Servidor de correo: '
     '«Correo del pedido sin confirmar»'],
    ['Registrar Notificación de Cancelaciones', 'Se dispara al Anular o Cancelar un Pedido', 'Pedidos, Configuración, '
     'Notificación', 'Hacia Pedidos: «id del cliente» → «Pedidos anulados del cliente». Guarda: «Datos de la notificación»'],
    ['Registrar Notificación al Cliente', 'Se dispara al Confirmar o Reprogramar un Pedido', 'Configuración, Notificación',
     'Guarda: «Datos de la notificación». Al Servidor de correo: «Correo de la mudanza confirmada» / «Correo del '
     'horario nuevo»'],
    ['Consultar Notificaciones', 'Cualquier usuario (bandeja y campanita)', 'Notificación',
     'Hacia Notificación: «Perfil y id del usuario» → «Notificaciones del usuario». Al leer, guarda: «Fecha de lectura»'],
    ['Configurar Umbrales', 'Administrador', 'Configuración', 'Guarda: «Valores de los umbrales»'],
    ['Consultar Reporte Consolidado', 'Administrador (el de la flota solo con REP_FINANZAS)',
     'Pedidos, Personal pedido, Reprogramaciones, Vehículos, Detalle pedidos',
     'Del Administrador: «Rango de fechas y filtro». Sale: «Reporte» (pantalla y PDF)'],
    ['Generar Gráficos de Analítica', 'Administrador (corre el script)', 'Pedidos, Detalle pedidos, Servicios',
     'Del Administrador: «Rango de fechas y objetivo mensual». Sale: «Gráficos del período» (PNG)'],
    ['Consultar Tablero', 'Administrador (pantalla de inicio)', 'Pedidos, Vehículos, Detalle pedidos, Servicios, '
     'Personal pedido', 'Del Administrador: «Período». Sale: «Indicadores y gráficos del período»'],
    ['Actualizar Datos de la Cuenta', 'Cliente («Mi cuenta»)', 'Usuarios', 'Guarda: «Correo y teléfono del cliente»'],
    ['Cambiar Clave', 'Cualquier usuario («Mi cuenta»)', 'Usuarios',
     'Hacia Usuarios: «DNI del usuario» → «Clave cifrada». Guarda: «Clave nueva cifrada»'],
    ['Recuperar Clave', 'Cliente («¿Olvidaste tu contraseña?»)', 'Usuarios, Roles',
     'Hacia Usuarios: «DNI y correo» → «Datos del usuario». Guarda: «Clave nueva cifrada»'],
    ['Consultar Recorrido', 'Administrador, Cliente o Chofer (detalle del pedido)', 'Pedidos',
     'Hacia Pedidos: «id_pedido» → «Direcciones y puntos del pedido». Al Servicio de mapas: «Puntos de origen y '
     'destino» (o las direcciones, si no tienen punto) → «Ruta, distancia y duración»'],
    ['Obtener Dirección del Mapa', 'Cliente (al registrar el pedido)', '—',
     'Al Servicio de mapas: «Coordenadas del punto» → «Dirección del punto». Es parte de Registrar un Pedido'],
    ['Ubicar Dirección Escrita', 'Cliente (al escribir la dirección a mano)', '—',
     'Al Servicio de mapas: «Dirección escrita» → «Punto de la dirección». Al Cliente: «Punto propuesto» '
     '(«¿Es acá?»). Es parte de Registrar un Pedido'],
], [105, 105, 100, 150])
parrafo('Registrar un Pedido y Modificar Pedido guardan en Pedidos, además de las direcciones, los «Puntos de '
        'origen y destino» cuando el cliente los marcó en el mapa.')
parrafo('Los procesos que ya estaban y cambian: Confirmar Pedido y Reprogramar Pedido suman la salida hacia '
        '«Registrar Notificación al Cliente»; Anular Pedido y Cancelar Pedido, hacia «Registrar Notificación de '
        'Cancelaciones».')
parrafo('Si el profesor de Análisis y Diseño pide el modelo C4, estos cambios también aparecen ahí: tres sistemas '
        'externos nuevos (Servidor de correo, Servicio de mapas y la librería de gráficos Chart.js que se carga '
        'desde un CDN) y un contenedor nuevo: la tarea programada de alertas.')

titulo('3.2 DFD nuevos por el control de materiales', 2)
parrafo('Almacenes nuevos: Materiales y Movimientos material. Recursos asignados ahora guarda «id_servicio, '
        'id_material y cantidad sugerida» en vez del texto.')
tabla(['Proceso', 'Quién lo estimula', 'Almacenes', 'Flujos principales'], [
    ['Gestionar Materiales', 'Administrador', 'Materiales, Movimientos material',
     'Del Administrador: «Datos del material» (y «Stock inicial»). Guarda en Materiales: «Datos del material»; '
     'en Movimientos: «Ingreso inicial»'],
    ['Registrar Ingreso de Material', 'Administrador (una compra)', 'Materiales, Movimientos material',
     'Del Administrador: «id_material y cantidad comprada». Guarda: «Datos del ingreso» y «Stock nuevo»'],
    ['Registrar Ajuste de Inventario', 'Administrador (después de contar)', 'Materiales, Movimientos material',
     'Del Administrador: «id_material, diferencia y motivo». Hacia Materiales: «id_material» → «Stock actual». '
     'Guarda: «Datos del ajuste» y «Stock nuevo»'],
    ['Registrar Salida de Materiales', 'Se dispara cuando el chofer marca «Empezamos»',
     'Detalle pedidos, Recursos asignados, Materiales, Movimientos material',
     'Hacia Detalle pedidos: «id_pedido» → «Servicios del pedido». Hacia Recursos asignados: «id_servicio» → '
     '«Materiales sugeridos». Guarda: «Datos de la salida» y «Stock nuevo». Al Chofer: «Materiales faltantes»'],
    ['Registrar Cierre de Materiales', 'Chofer al marcar «Terminamos» (cuenta lo usado y lo que volvió)',
     'Movimientos material, Materiales',
     'Del Chofer: «Cantidades usadas y devueltas». Hacia Movimientos: «id_pedido» → «Materiales que salieron». '
     'Guarda: «Datos del consumo, la devolución y la pérdida» y «Stock nuevo»'],
    ['Registrar Notificación de Stock Bajo', 'Se dispara cuando un movimiento deja un material bajo su mínimo',
     'Materiales, Configuración, Notificación',
     'Hacia Materiales: «id_material» → «Stock y stock mínimo». Guarda: «Datos de la notificación». Al Servidor '
     'de correo: «Correo de stock bajo»'],
    ['Consultar Movimientos de Material', 'Administrador', 'Movimientos material, Materiales',
     'Del Administrador: «id_material». Sale: «Historial del material»'],
], [105, 105, 100, 150])
parrafo('Procesos que ya estaban y cambian: Anular Pedido, si la mudanza ya había salido, guarda en Movimientos '
        'material la «Devolución de lo que salió»; Asignar Recursos al Pedido sigue siendo solo el personal '
        '(los materiales salen con «Empezamos», no al asignar).')

titulo('4. Fuera del alcance: cobros (decidido el 09/11/2026)', 1)
parrafo('El grupo decidió que los cobros quedan totalmente fuera del alcance del sistema. Por eso:')
lista([
    ('DER: ', 'sacar las tablas COBRANZAS y DETALLE_COBRANZAS y sus relaciones con PEDIDOS.'),
    ('DFD: ', 'no hace falta ningún DFD de cobros; si algún diagrama menciona un almacén «Cobranzas», sacarlo.'),
    ('Documento y presentación: ', 'sacar la cobranza de los objetivos, el alcance y los requerimientos, y '
                                   'agregarla en «Fuera del alcance».'),
    ('Sistema: ', 'ya se sacaron de la base (migración 0025, 10/11/2026). Solo tenían la fila del pedido de '
                  'ejemplo y ninguna pantalla las usaba.'),
])

doc.save(SALIDA)
print('ok', SALIDA)
