"""Genera el Word con los cambios pendientes del DER y de los DFD (Grupo 5).

Uso: python docs/herramientas/cambios_der_dfd.py "<ruta de salida>.docx"  (necesita python-docx)
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
p = doc.add_paragraph('Mudanzas y Fletes Salta · Grupo 5 · Actualizado al 20/10/2026')
p.runs[0].italic = True
parrafo('Este documento junta todo lo que hay que agregar o corregir en el DER de alto refinamiento '
        'y en los DFD del documento oficial para que coincidan con lo que ya hace el sistema y con '
        'las reglas de notación del grupo. Está dividido en: (1) cambios obligatorios porque el sistema '
        'ya funciona así, (2) correcciones de notación en los DFD, (3) DFD que faltan y (4) mejoras '
        'futuras que todavía no se decidieron.')

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
    ['Reemplazar campo', 'desc_inventario VARCHAR(100)', 'id_objeto INT (FK → OBJETOS)'],
    ['Se mantienen', 'Cantidad, obser_inventario, Fragil, id_pedido', 'Igual'],
    ['Relación nueva', '—', 'OBJETOS 1 : N INVENTARIO_DETALLES'],
], [100, 170, 190])

titulo('1.3 SERVICIOS: principal y adicionales', 2)
parrafo('Un pedido lleva un servicio principal (Mudanza local, Mudanza nacional o Flete urbano) y, '
        'opcionales, adicionales sin precio (Embalaje, Desarmado y armado de muebles, Ayudante extra).')
tabla(['Campo nuevo', 'Tipo', 'Valores'], [
    ['categoria_servicio', 'VARCHAR(10)', 'Principal / Adicional'],
], [140, 100, 220])
parrafo('Precio_base de los adicionales queda en 0. Estado_servicio (BOOLEAN) ya está en el DER.')

titulo('1.4 DETALLE_PEDIDOS: precio del día', 2)
parrafo('Hay una fila por cada servicio del pedido (el principal y los adicionales). El sistema guarda el '
        'precio que tenía el servicio el día del pedido, para que si después cambia el precio el '
        'comprobante viejo no cambie.')
tabla(['Campo nuevo', 'Tipo', 'Descripción'], [
    ['precio_unitario', 'DECIMAL', 'Precio del servicio el día del pedido (0 en los adicionales)'],
    ['subtotal', 'DECIMAL', 'Igual al precio (no hay cantidades por servicio)'],
], [120, 80, 260])

titulo('1.5 PEDIDOS: fechas, total y anulación', 2)
parrafo('En el DER, «Fec_pedido» no deja claro si es el día en que se pidió o el día de la mudanza. '
        'El sistema guarda las dos.')
tabla(['Campo', 'Tipo', 'Descripción'], [
    ['Fec_pedido', 'DATE', 'Día en que el cliente registró el pedido'],
    ['Fec_servicio (nuevo)', 'DATE', 'Día de la mudanza'],
    ['Hora_pedido', 'TIME', 'Hora de inicio de la mudanza (ya está)'],
    ['Total_pedido (nuevo)', 'DECIMAL', 'Precio del servicio principal'],
    ['id_usuario_anulacion (nuevo)', 'INT (FK → USUARIOS)', 'Quién anuló el pedido'],
], [140, 110, 210])
parrafo('Estados posibles de Estado_pedido: Pendiente, Confirmado, Finalizado, Anulado. «Vencido» y '
        '«Para finalizar» NO son estados guardados: el sistema los calcula con la fecha y la hora, así '
        'que no van en el DER.')

titulo('1.6 VEHICULOS: tipo y chofer', 2)
tabla(['Campo', 'Tipo', 'Descripción'], [
    ['tipo_vehiculo (nuevo)', 'VARCHAR(50)', 'Lista cerrada: Utilitario Mediano, Furgón Urbano, Camión Liviano, '
                                             'Camión Pesado'],
    ['id_chofer (nuevo)', 'INT (FK → USUARIOS)', 'Chofer asignado al vehículo (puede estar vacío)'],
    ['observaciones_vehiculo (nuevo)', 'TEXT', 'Notas del vehículo'],
], [140, 110, 210])
parrafo('Opción si la profesora lo pide: pasar el tipo a una tabla TIPO_VEHICULO (id_tipo_veh, nom_tipo_veh), '
        'igual que ESTADO_VEHICULO.')

titulo('1.7 Tabla nueva: PERSONAL_PEDIDO (ya está en el sistema)', 2)
parrafo('El documento dice que RECURSOS_ASIGNADOS «asocia los empleados», pero en el DER solo relaciona '
        'servicio con materiales. El sistema ya guarda qué chofer y qué ayudantes van a cada mudanza en '
        'esta tabla: el chofer es obligatorio para confirmar el pedido y una persona hace una sola mudanza por día.')
tabla(['Campo', 'Tipo', 'Clave'], [
    ['id_personal_pedido', 'INT', 'PK'],
    ['id_pedido', 'INT', 'FK → PEDIDOS'],
    ['id_usuario', 'INT', 'FK → USUARIOS (chofer o ayudante)'],
    ['funcion_personal', 'VARCHAR(10)', 'Chofer / Ayudante'],
], [160, 80, 220])
parrafo('Relaciones: PEDIDOS 1 : N PERSONAL_PEDIDO y USUARIOS 1 : N PERSONAL_PEDIDO.')

titulo('1.8 Diferencias entre el DER del documento y el sistema', 2)
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
    ['Disponibilidad del vehículo', 'Depende de los pedidos de ese día',
     'Consultar Pedidos con «Fecha de la mudanza» y que vuelvan los «Vehículos ocupados»'],
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
     'Guardar en el almacén nuevo PERSONAL_PEDIDO (consulta: «Fecha de la mudanza» → «Personal ocupado»)'],
    ['«Usuario actualizado», «Vehículo actualizado»', 'El proceso no modifica usuarios ni vehículos',
     'Revisar: si solo se asignan, sacarlas'],
], [150, 130, 180])

# ---------------------------------------------------------------- DFD que faltan
titulo('3. DFD que faltan (el sistema ya los tiene)')
tabla(['Proceso', 'Quién lo estimula', 'Almacenes'], [
    ['Registrar Cliente', 'Cliente (se crea la cuenta)', 'Usuarios, Roles'],
    ['Gestionar Servicios', 'Administrador', 'Servicios, Recursos asignados'],
    ['Gestionar Objetos', 'Administrador', 'Objetos'],
    ['Confirmar Pedido', 'Administrador', 'Pedidos'],
    ['Finalizar Pedido', 'Administrador (solo desde la fecha y hora de la mudanza)', 'Pedidos'],
    ['Anular Pedido', 'Administrador (con motivo; queda quién y cuándo)', 'Pedidos'],
    ['Consultar Pedidos', 'Administrador (todos) o Cliente (los suyos), con filtros', 'Pedidos, Usuarios, Servicios, Vehículos'],
    ['Emitir Comprobante', 'Administrador o Cliente', 'Pedidos, Detalle pedidos, Inventario detalles'],
], [130, 190, 140])

# ---------------------------------------------------------------- futuro
titulo('4. Mejoras futuras (todavía no decididas)')
titulo('4.1 Control de materiales', 2)
tabla(['Tabla', 'Campos'], [
    ['MATERIALES (nueva)', 'id_material PK, nom_material, unidad_material, stock_material, stock_min_material, '
                           'reutilizable (BOOLEAN), estado_material'],
    ['RECURSOS_ASIGNADOS (cambia)', 'id_recursos_asignados PK, id_servicio FK, id_material FK (reemplaza el texto '
                                    '«Materiales»), cant_sugerida'],
    ['MOVIMIENTOS_MATERIAL (nueva)', 'id_mov_material PK, id_material FK, id_pedido FK (vacío si es compra), '
                                     'id_usuario FK, tipo_mov (Ingreso / Salida / Devolución), cant_mov, fec_mov'],
], [140, 320])
parrafo('DFD: cambiar «Asignar Recursos al Pedido» (registra la salida de materiales) y agregar '
        '«Registrar Ingreso de Material».')

titulo('4.2 Cobros (sin pagos en línea)', 2)
parrafo('Registrar el cobro al finalizar el pedido: monto y método de pago elegido de una lista fija '
        '(Efectivo, Transferencia, Tarjeta, Mercado Pago). Usa COBRANZAS y DETALLE_COBRANZAS, que ya '
        'están en el DER. Si se decide no hacerlo, hay que sacar esas tablas del DER y la cobranza del '
        'documento y la presentación.')

titulo('4.3 Duración de los servicios', 2)
parrafo('Hoy un vehículo hace una sola mudanza por día. Para permitir dos trabajos cortos en el mismo día: '
        'agregar a SERVICIOS «duracion_estimada» (mínimo 5 o 6 horas para un flete, un día para una mudanza '
        'local, varios días para una nacional) y cambiar la regla de disponibilidad de «por día» a «por horario».')

doc.save(SALIDA)
print('ok', SALIDA)
