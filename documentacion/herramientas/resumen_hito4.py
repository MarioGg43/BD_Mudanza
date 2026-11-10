"""Genera el Word con el estado del Hito 4 (Taller de Programación) y lo que se sumó del proyecto de José.

Uso: python documentacion/herramientas/resumen_hito4.py "<ruta de salida>.docx"  (necesita python-docx)
"""
import sys

from docx import Document
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Pt, RGBColor

SALIDA = sys.argv[1]
NARANJA = RGBColor(0xC0, 0x4F, 0x00)
TINTA = RGBColor(0x23, 0x1A, 0x15)
# Color de la columna «Estado»
ESTADOS = {'Ya estaba': 'D9F2E3', 'Agregado ahora': 'FFE3C7', 'Falta': 'F9D6D6'}

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


def tabla(encabezado, filas, anchos=None, col_estado=None):
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
            if i == col_estado:
                fondo(celdas[i], next((c for e, c in ESTADOS.items() if v.startswith(e)), 'FFFFFF'))
                for r in celdas[i].paragraphs[0].runs:
                    r.bold = True
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
t = doc.add_heading('Hito 4 · Taller de Programación', 0)
for r in t.runs:
    r.font.color.rgb = TINTA
p = doc.add_paragraph('Mudanzas y Fletes Salta · Grupo 5 · Estado al 28/10/2026 (con capturas y borrador del DER)')
p.runs[0].italic = True
parrafo('Este documento marca qué pide la consigna del Hito 4 y cómo lo cumple el sistema: qué ya estaba, qué '
        'se agregó ahora y qué falta entregar. También explica qué se trajo del proyecto que adelantó José y '
        'qué no, y por qué.')
lista([('Ya estaba: ', 'el sistema lo cumplía antes de este hito.'),
       ('Agregado ahora: ', 'se programó para este hito (incluye lo que se trajo del proyecto de José).'),
       ('Falta: ', 'son entregables que arma el grupo (dibujos, documento y capturas).')])

# ---------------------------------------------------------------- proceso
titulo('1. El proceso elegido: pedido de mudanza')
parrafo('Es el proceso principal del negocio y abarca todas sus etapas: el cliente registra el pedido, el '
        'administrador asigna chofer y ayudantes, lo confirma y lo finaliza. En el medio se puede reprogramar '
        '(cambio de horario o de camión, con motivo) o anular (con motivo). Nada se borra.')
tabla(['Tabla', 'Rol en el proceso'], [
    ['PEDIDOS', 'Cabecera: número y fecha automáticos, cliente, vehículo, fecha y hora, duración, total, estado'],
    ['DETALLE_PEDIDOS', 'Detalle: un renglón por servicio (principal y adicionales) con el precio del día'],
    ['INVENTARIO_DETALLES', 'Detalle: qué hay que llevar (objeto del catálogo, cantidad, frágil)'],
    ['PERSONAL_PEDIDO', 'Detalle: chofer y ayudantes de la mudanza'],
    ['REPROGRAMACIONES', 'Historial de cambios de horario o de vehículo'],
    ['USUARIOS, VEHICULOS, SERVICIOS, OBJETOS', 'Tablas maestras (todas con su ABM), relacionadas por clave foránea'],
    ['LOG_AUDITORIA', 'Toda modificación o anulación de cualquier tabla'],
], [150, 310])

# ---------------------------------------------------------------- consigna
titulo('2. La consigna, punto por punto')
C = 'Ya estaba'
A = 'Agregado ahora'
tabla(['Lo que pide el Hito 4', 'Estado', 'Cómo lo cumple el sistema'], [
    ['1 proceso completo, de principio a fin', C,
     'Registrar → asignar personal → confirmar → finalizar. También reprogramar y anular.'],
    ['Al menos 3 tablas con FK y cabecera–detalle', C,
     'PEDIDOS con DETALLE_PEDIDOS, INVENTARIO_DETALLES y PERSONAL_PEDIDO.'],
    ['ABM de las tablas maestras', C, 'Servicios, Objetos, Vehículos, Usuarios y Roles.'],
    ['Número de comprobante y fecha automáticos', C, 'N° de pedido y fecha del pedido los pone el sistema.'],
    ['Usuario automático (el logueado)', C,
     'El pedido queda a nombre del cliente que entró; la anulación, la reprogramación y la auditoría guardan quién fue.'],
    ['Datos relacionados con listas o buscadores', C,
     'Servicio y adicionales con opciones, vehículos libres en una lista, objetos con la ventana guiada, personal '
     'libre en listas. Nunca se escribe una clave foránea a mano.'],
    ['Validaciones (obligatorios, tipos, rangos, disponibilidad)', C,
     'Fecha hasta 1 año, hora futura, direcciones distintas, cantidad 1 a 999, duración 5 a 120 h, «Otro» '
     'que no esté en la lista, vehículo y personal libres en el horario.'],
    ['Cálculos automáticos', A,
     'Total = servicio principal con recargo por tamaño del camión (+0, +25 o +50 %) + adicionales a su precio. '
     'Hora de fin = inicio + duración. Antes el total era solo el principal.'],
    ['Estado automático al registrar', C, 'Queda «Pendiente».'],
    ['Actualiza lo afectado, con transacciones', C,
     'El vehículo y el personal quedan ocupados en ese horario. Todo se guarda en una transacción con bloqueo: '
     'si algo falla no queda nada a medias.'],
    ['Anulación: estado Anulado, fecha, motivo y usuario, sin borrar', C,
     'Libera el vehículo y el personal (revierte lo ocupado). El pedido queda guardado.'],
    ['log_auditoria en toda modificación o anulación', A,
     'Tabla LOG_AUDITORIA automática para todas las tablas: valores anteriores y nuevos, fecha y hora, usuario. '
     'Pantalla «Auditoría» con filtros (permiso AUD_CONSULTAR).'],
    ['Consulta con filtros (fechas, estado, dato relacionado) y detalle', C,
     'Filtros por rango de fechas, estado y avisos, servicio, cliente y vehículo; detalle de cada pedido.'],
    ['Comprobante imprimible o PDF', C, 'Comprobante en pantalla y en PDF; listado de pedidos en PDF.'],
    ['Permisos por perfil, con al menos una acción restringida', C,
     'El cliente registra, consulta y baja su comprobante, pero no anula ni confirma. Los permisos se editan por rol.'],
], [150, 75, 235], col_estado=1)

titulo('Entregables', 2)
tabla(['Entregable', 'Estado', 'Dónde está o qué falta'], [
    ['Documento de avance del proyecto', 'Falta', 'Lo arma el grupo; este documento sirve de base.'],
    ['DER (cambió)', 'Agregado ahora (borrador)',
     '«DER_borrador_Mudanzas_Grupo5.drawio»: las 17 tablas reales con PK, FK y relaciones, armado desde la base. '
     'Revisarlo y darle el estilo del grupo. Los cambios explicados están en «Cambios_pendientes_DER_DFD_Grupo5.docx».'],
    ['DFD del proceso', 'Falta dibujar', 'Registrar un Pedido, Anular y Reprogramar; correcciones en el mismo Word.'],
    ['Scripts de base de datos actualizados', A,
     'documentacion/base_de_datos/01_estructura.sql (todas las tablas) y 02_datos_maestros.sql (roles, permisos, '
     'servicios, objetos, vehículos). Probados en una base vacía.'],
    ['Capturas del proceso completo', 'Agregado ahora',
     'Carpeta «Capturas»: 28 pantallas numeradas en orden (registración con la ventana de objetos, consulta con '
     'filtros, asignar y confirmar, reprogramar, anulación, comprobante y PDF, auditoría, ABM y permisos).'],
], [150, 75, 235], col_estado=1)

# ---------------------------------------------------------------- José
titulo('3. Lo que se trajo del proyecto de José')
parrafo('José partió de la versión del 27/10 y le sumó varias ideas. Se trajeron rehechas sobre la versión '
        'actual, sin migraciones que borren datos y con sus pruebas:')
tabla(['Idea de José', 'Cómo quedó'], [
    ['Camiones por tamaño con recargo', 'Camión Chico (+0 %), Mediano (+25 %) y Grande (+50 %) sobre el servicio '
     'principal. Una migración solo cambia el tipo de cada vehículo.'],
    ['Adicionales con precio', 'Embalaje $25.000, Desarmado y armado $35.000, Ayudante extra $20.000 (editables). '
     'El total los suma y el formulario lo calcula en vivo.'],
    ['Recordatorio para finalizar', 'En todas las pantallas del administrador: mudanzas que ya debían terminar, con '
     'botón «Finalizar» que vuelve a la misma pantalla. Marca las que tienen otra mudanza esperando.'],
    ['Ver u ocultar la clave', 'Un botón con un ojo en todos los campos de clave del sistema.'],
    ['Elegir chofer al reasignar', 'En «Reprogramar»: campo Chofer (tiene que estar libre en el horario nuevo). '
     'El precio no cambia aunque vaya un camión más grande.'],
    ['Personal de muestra', 'Comando «personal_muestra» que solo agrega (3 administradores, 2 choferes, 8 ayudantes '
     'en total). Ya está cargado.'],
    ['Claves con PBKDF2', 'Hecho completo: las claves nuevas se guardan con PBKDF2 (con sal) y las viejas se '
     'actualizan solas cuando la persona entra.'],
], [130, 330])

titulo('Lo que no se trajo (para decidir en grupo)', 2)
tabla(['Idea de José', 'Por qué no'], [
    ['Duración de 4 a 6 h según camión y bultos', 'Las mudanzas nacionales quedaban en 6 h y el grupo había acordado '
     'un mínimo de 5 h y varios días para las grandes. Sigue la duración por servicio (5, 10 y 48 h, editables).'],
    ['Correos al cliente (atraso y reasignación)', 'Los correos quedaron fuera del alcance. En su lugar: aviso en '
     '«Mis pedidos» y botón de WhatsApp con el mensaje armado.'],
    ['Migraciones que crean y borran usuarios', 'Una migración corre en cualquier base donde se instale el sistema: '
     'la 0015 borraba a todos los usuarios menos uno. Se reemplazó por el comando que solo agrega.'],
    ['«Reasignar pedido»', 'Ya existe «Reprogramar», más completo (motivo de una lista, historial y aviso al '
     'cliente). Se le sumó la elección de chofer.'],
    ['Estado de pago', 'No tenía pantalla. Conviene hacerlo junto con los cobros (COBRANZAS ya está en el DER).'],
    ['Volumen y medidas de los objetos', 'José mismo lo sacó de las pantallas.'],
], [130, 330])
parrafo('Importante: para seguir trabajando, conviene partir de la rama «permisos-editables» del repositorio '
        '(tiene todo) y no de la copia anterior, así no se duplica nada.')

# ---------------------------------------------------------------- probar
titulo('4. Cómo probarlo y sacar las capturas')
lista([('Administrador: ', 'DNI 35123456 (Admin123!). Pedidos, reprogramar, anular, auditoría.'),
       ('Cliente: ', 'DNI 29876543 (Cliente123!). Pedir mudanza, mis pedidos, comprobante.'),
       ('Chofer: ', 'DNI 40987654 (Usuario123!). Portal con sus mudanzas.')])
lista(['Las capturas se pueden volver a sacar con: python documentacion/herramientas/capturas_hito4.py',
       'Registración: como cliente, «Pedir mudanza», elegir un camión mediano y un adicional y mirar el total.',
       'Consulta: como administrador, «Pedidos» con filtros de fecha, estado y cliente, y abrir el detalle.',
       'Anulación: desde el detalle, «Anular» con un motivo; después mirarlo en «Auditoría».',
       'Comprobante: «Comprobante» y «Descargar PDF» desde el detalle.'])

doc.save(SALIDA)
print('ok', SALIDA)
