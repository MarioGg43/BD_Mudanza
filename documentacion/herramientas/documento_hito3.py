"""Genera el documento que explica el Hito 3 punto por punto de la consigna.

Uso: python documentacion/herramientas/documento_hito3.py
Necesita python-docx y las capturas en Descargas\\Capturas Hito3.
"""
import pathlib

from docx import Document
from docx.enum.section import WD_SECTION
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor

CAPTURAS = pathlib.Path(r'C:\Users\gaboo\Downloads\Capturas Hito3')
SALIDA = pathlib.Path(r'C:\Users\gaboo\Downloads\Hito3_Explicacion_Grupo5.docx')

NARANJA = RGBColor(0xC0, 0x4F, 0x00)
TINTA = RGBColor(0x23, 0x1A, 0x15)
GRIS = RGBColor(0x5E, 0x52, 0x4B)
FONDO_TABLA = 'FFF0E2'

doc = Document()
for s in doc.sections:
    s.page_height, s.page_width = Cm(29.7), Cm(21)
    s.left_margin = s.right_margin = Cm(2.5)
    s.top_margin = s.bottom_margin = Cm(2.2)

estilo = doc.styles['Normal']
estilo.font.name = 'Calibri'
estilo.font.size = Pt(11)
estilo.font.color.rgb = TINTA
estilo.paragraph_format.space_after = Pt(6)
estilo.paragraph_format.line_spacing = 1.15
for nombre, tam in (('Heading 1', 16), ('Heading 2', 13)):
    h = doc.styles[nombre]
    h.font.name = 'Calibri'
    h.font.size = Pt(tam)
    h.font.bold = True
    h.font.color.rgb = NARANJA
    h.paragraph_format.space_before = Pt(14)
    h.paragraph_format.space_after = Pt(6)
    h.paragraph_format.keep_with_next = True


def parrafo(texto='', negrita_inicial=None, cursiva=False, color=None, tam=None, centrado=False):
    p = doc.add_paragraph()
    if negrita_inicial:
        r = p.add_run(negrita_inicial)
        r.bold = True
    r = p.add_run(texto)
    r.italic = cursiva
    if color:
        r.font.color.rgb = color
    if tam:
        r.font.size = Pt(tam)
    if centrado:
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    return p


def vinetas(items):
    for item in items:
        p = doc.add_paragraph(style='List Bullet')
        if isinstance(item, tuple):
            p.add_run(item[0]).bold = True
            p.add_run(item[1])
        else:
            p.add_run(item)
        p.paragraph_format.space_after = Pt(3)


def sombrear(celda, color):
    tc = celda._tc.get_or_add_tcPr()
    shd = OxmlElement('w:shd')
    shd.set(qn('w:val'), 'clear')
    shd.set(qn('w:color'), 'auto')
    shd.set(qn('w:fill'), color)
    tc.append(shd)


def tabla(encabezado, filas, anchos):
    t = doc.add_table(rows=1, cols=len(encabezado))
    t.style = 'Table Grid'
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    for i, texto in enumerate(encabezado):
        c = t.rows[0].cells[i]
        c.text = ''
        r = c.paragraphs[0].add_run(texto)
        r.bold = True
        r.font.size = Pt(10)
        sombrear(c, FONDO_TABLA)
    for fila in filas:
        celdas = t.add_row().cells
        for i, texto in enumerate(fila):
            celdas[i].text = ''
            r = celdas[i].paragraphs[0].add_run(texto)
            r.font.size = Pt(10)
    for fila in t.rows:
        for i, ancho in enumerate(anchos):
            fila.cells[i].width = Cm(ancho)
    doc.add_paragraph().paragraph_format.space_after = Pt(2)
    return t


def captura(archivo, pie):
    ruta = CAPTURAS / archivo
    if not ruta.exists():
        parrafo(f'[Falta la captura {archivo}]', color=RGBColor(0xB3, 0x0B, 0x0B))
        return
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.keep_with_next = True
    p.add_run().add_picture(str(ruta), width=Cm(15.5))
    pie_p = parrafo(pie, cursiva=True, color=GRIS, tam=9, centrado=True)
    pie_p.paragraph_format.space_after = Pt(12)


def numerar_paginas():
    for seccion in doc.sections:
        p = seccion.footer.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
        for tipo, texto in (('begin', None), (None, 'PAGE'), ('end', None)):
            r = p.add_run()
            if tipo:
                f = OxmlElement('w:fldChar')
                f.set(qn('w:fldCharType'), tipo)
                r._r.append(f)
            else:
                ins = OxmlElement('w:instrText')
                ins.set(qn('xml:space'), 'preserve')
                ins.text = texto
                r._r.append(ins)
            r.font.size = Pt(9)
            r.font.color.rgb = GRIS


# ---------------- Portada ----------------
for _ in range(5):
    doc.add_paragraph()
parrafo('Instituto Superior del Milagro N° 8207', color=GRIS, tam=12, centrado=True)
parrafo('Tecnicatura Superior en Análisis de Sistemas', color=GRIS, tam=12, centrado=True)
parrafo('Taller de Programación', color=GRIS, tam=12, centrado=True)
doc.add_paragraph()
p = parrafo('HITO N° 3', color=NARANJA, tam=28, centrado=True)
p.runs[0].bold = True
p = parrafo('Proceso completo: el pedido de mudanza', tam=18, centrado=True)
p.runs[0].bold = True
parrafo('Qué pedía la consigna y cómo lo resolvimos, punto por punto', color=GRIS, tam=12, centrado=True)
for _ in range(6):
    doc.add_paragraph()
parrafo('Sistema para Mudanzas y Fletes Salta', tam=12, centrado=True)
parrafo('Grupo 5 · 2026', tam=12, centrado=True)
doc.add_paragraph().add_run().add_break(WD_BREAK.PAGE)

# ---------------- 1. Resumen ----------------
doc.add_heading('1. Qué pedía el hito', level=1)
parrafo('La consigna pide desarrollar, con el mismo lenguaje, framework y base de datos de los hitos '
        'anteriores, un proceso completo del sistema: el proceso principal del negocio, desde que empieza '
        'hasta que termina. Nosotros usamos Django (Python), MySQL y Docker, igual que en los hitos 1 y 2.')
parrafo('Elegimos el pedido de mudanza porque es lo que hace la empresa todos los días: un cliente pide '
        'una mudanza, la empresa la confirma, la realiza y la da por terminada, o la anula si no se hace.')

doc.add_heading('Resumen: cada requisito y dónde está resuelto', level=2)
tabla(['La consigna pide', 'Cómo lo resolvimos', 'Captura'], [
    ['Un proceso completo con 3 tablas relacionadas, cabecera y detalle',
     'PEDIDOS (cabecera) con DETALLE_PEDIDOS e INVENTARIO_DETALLES (detalles), relacionadas con USUARIOS, VEHICULOS y SERVICIOS', '03, 04'],
    ['ABM de las tablas maestras que falten', 'ABM de SERVICIOS (vehículos y usuarios ya estaban de los hitos 1 y 2)', '14'],
    ['Número de comprobante y fecha automáticos', 'El número de pedido y la fecha de registro los pone el sistema', '04'],
    ['Usuario automático', 'El pedido queda a nombre del cliente que inició sesión', '04, 05'],
    ['Datos relacionados por listas', 'Servicio con opciones, vehículo con lista desplegable, objetos con sugerencias', '03'],
    ['Validaciones', 'Campos obligatorios, tipos, rangos y disponibilidad del vehículo', '03'],
    ['Cálculos automáticos', 'Precio copiado, subtotal y total del pedido', '03, 12'],
    ['Estado automático', 'Todo pedido nace «Pendiente»', '04'],
    ['Actualizar entidades con transacciones', 'El vehículo queda reservado ese día; todo se guarda junto o no se guarda nada', '03, 11'],
    ['Anulación sin borrar', 'Estado «Anulado» con fecha, motivo y usuario; el vehículo se libera', '10, 11, 13'],
    ['Consulta con filtros y detalle', 'Filtros por fechas, estado, servicio y cliente; detalle de cada pedido', '05, 06, 07'],
    ['Comprobante imprimible o PDF', 'Comprobante con botón «Imprimir / Guardar PDF»', '12, 13'],
    ['Permisos por perfil, con una acción restringida', 'Permisos de la tabla PERMISOS: el cliente registra pero no confirma ni anula', '08, 15'],
], [5.2, 8.3, 2.5])

# ---------------- 2. Proceso ----------------
doc.add_heading('2. El proceso: de punta a punta', level=1)
parrafo('El pedido pasa por estos estados. Cada cambio de estado queda guardado; nunca se borra un pedido.')
tabla(['Estado', 'Quién lo produce', 'Qué significa'], [
    ['Pendiente', 'Sistema, al registrar', 'El cliente pidió la mudanza; falta que la empresa la confirme'],
    ['Confirmado', 'Administrador', 'La empresa aceptó el pedido y lo va a realizar'],
    ['Finalizado', 'Administrador', 'La mudanza se hizo; es el final normal del proceso'],
    ['Anulado', 'Administrador', 'El pedido no se realiza; se guarda fecha, motivo y quién lo anuló'],
], [3, 4.5, 8.5])
parrafo('Se puede anular un pedido Pendiente o Confirmado. Un pedido Finalizado o ya Anulado no cambia más.')

# ---------------- 3. Tablas ----------------
doc.add_heading('3. Tablas relacionadas: cabecera y detalle', level=1)
parrafo('La consigna pide al menos tres tablas unidas por claves foráneas, con una estructura de cabecera y detalle '
        '(maestro–detalle). La cabecera guarda los datos generales de la operación y los detalles guardan sus renglones.')
tabla(['Tabla', 'Papel', 'Qué guarda'], [
    ['PEDIDOS', 'Cabecera', 'Número, fecha de registro, fecha y hora de la mudanza, direcciones, estado, total, cliente, vehículo y datos de anulación'],
    ['DETALLE_PEDIDOS', 'Detalle', 'El servicio contratado con su precio y subtotal'],
    ['INVENTARIO_DETALLES', 'Detalle', 'Cada objeto a llevar: qué es, cantidad, si es frágil y una observación'],
    ['USUARIOS', 'Relacionada', 'El cliente que hizo el pedido y el administrador que lo anuló (dos claves foráneas)'],
    ['VEHICULOS', 'Relacionada', 'El vehículo asignado (por su patente)'],
    ['SERVICIOS', 'Relacionada', 'El servicio elegido: Flete urbano, Mudanza local o Mudanza nacional'],
], [4, 2.8, 9.2])

# ---------------- 4. ABM ----------------
doc.add_heading('4. ABM de las tablas maestras', level=1)
parrafo('ABM significa Alta, Baja y Modificación. Una tabla maestra guarda los datos fijos con los que se arma el '
        'negocio, que cambian poco y que otros registros usan. En cambio, las tablas de movimientos registran lo que '
        'pasa todos los días.')
tabla(['Tipo', 'Tablas', 'Ejemplo'], [
    ['Maestras', 'SERVICIOS, VEHICULOS, USUARIOS', '«Mudanza local cuesta $185.000», «el camión AE-123-CD carga 5.000 kg»'],
    ['Movimientos', 'PEDIDOS, DETALLE_PEDIDOS, INVENTARIO_DETALLES', '«El 20/10 María pidió una Mudanza local con el camión AE-123-CD»'],
], [2.8, 5.7, 7.5])
parrafo('La consigna pide el ABM de las maestras que el proceso necesite, siempre que no se hayan hecho antes. '
        'Vehículos ya tenía ABM desde el Hito 1 y usuarios desde el Hito 2, así que hicimos el de servicios:')
vinetas([
    ('Alta: ', 'crear un servicio con su precio y los materiales que incluye.'),
    ('Modificación: ', 'cambiar nombre, precio o materiales.'),
    ('Baja lógica: ', 'el servicio no se borra; deja de ofrecerse en los pedidos nuevos, pero los pedidos viejos lo '
                     'conservan con el precio de ese momento.'),
])
captura('14-abm-servicios.png', 'Captura 14. ABM de servicios (solo el administrador).')

# ---------------- 5. Registración ----------------
doc.add_heading('5. La registración del pedido', level=1)
parrafo('El cliente registra su pedido en una sola pantalla, en cuatro partes: cuándo y dónde, servicio, qué hay que '
        'llevar y vehículo.')
captura('03-registrar-pedido-formulario.png', 'Captura 03. Formulario para pedir una mudanza.')

doc.add_heading('Número de comprobante y fecha: automáticos', level=2)
parrafo('El número de pedido lo asigna la base de datos (es la clave autoincremental) y la fecha de registro es la del '
        'día en que se carga. El cliente no los escribe.')

doc.add_heading('Usuario: automático', level=2)
parrafo('El pedido queda a nombre del usuario que inició sesión. No hay un campo para elegir el cliente: el sistema lo toma de la sesión.')

doc.add_heading('Datos relacionados: por listas, nunca claves a mano', level=2)
vinetas([
    ('Servicio: ', 'opciones excluyentes con su precio. Se elige uno solo.'),
    ('Vehículo: ', 'lista desplegable que muestra solo los vehículos libres en la fecha elegida; se actualiza al cambiar la fecha.'),
    ('Objetos: ', 'caja de texto con sugerencias (heladera, cocina, cajas, camas…). Si el objeto no está en la lista, se escribe.'),
])

doc.add_heading('Validaciones', level=2)
parrafo('Se controlan en la pantalla y de nuevo en el servidor, para que no se puedan saltear:')
tabla(['Dato', 'Regla'], [
    ['Fecha de la mudanza', 'Obligatoria, de hoy en adelante y como máximo a un año'],
    ['Hora de inicio', 'Obligatoria; cualquier hora (en el centro conviene de madrugada). Si es para hoy, posterior a la hora actual'],
    ['Origen y destino', 'Obligatorios, hasta 200 caracteres y distintos entre sí'],
    ['Servicio', 'Obligatorio, uno solo y activo'],
    ['Objetos', 'Al menos uno; nombre de hasta 100 caracteres, cantidad entera de 1 a 999, observación opcional de hasta 200'],
    ['Vehículo', 'Obligatorio, en estado «Disponible» y sin otro pedido activo ese día'],
], [4, 12])

doc.add_heading('Cálculos automáticos', level=2)
parrafo('Al registrar, el sistema copia el precio del servicio al detalle del pedido, calcula el subtotal y el total. '
        'El precio queda fijo en el pedido: si después se cambia el precio del servicio, el pedido no cambia.')

doc.add_heading('Estado automático', level=2)
parrafo('Todo pedido nuevo queda «Pendiente» hasta que la empresa lo confirme.')
captura('04-pedido-registrado.png', 'Captura 04. Pedido registrado: número, fecha, estado Pendiente y total calculados por el sistema.')

# ---------------- 6. Transacciones ----------------
doc.add_heading('6. Actualización de entidades y transacciones', level=1)
parrafo('Registrar un pedido ocupa el vehículo ese día: ese vehículo deja de aparecer como libre para esa fecha. '
        'Al anular el pedido, el vehículo vuelve a quedar libre. Así se actualiza la disponibilidad, que es la entidad '
        'afectada por el proceso.')
parrafo('Para garantizar la integridad, cada operación corre dentro de una transacción:')
vinetas([
    ('Todo o nada: ', 'la cabecera, el detalle y el inventario se guardan juntos. Si algo falla a mitad de camino, '
                     'la base vuelve atrás y no queda un pedido a medias.'),
    ('Sin dobles reservas: ', 'antes de guardar, el sistema bloquea el vehículo y vuelve a comprobar que siga libre. '
                             'Si dos clientes eligen el mismo vehículo para el mismo día al mismo tiempo, el segundo '
                             'recibe un aviso para elegir otro.'),
    ('Sin dejar pedidos sueltos: ', 'no se puede dar de baja un vehículo ni un cliente que tenga pedidos activos a futuro.'),
])

# ---------------- 7. Anulación ----------------
doc.add_heading('7. Anulación', level=1)
parrafo('Anular no borra el pedido: lo pasa a «Anulado» y guarda la fecha, el motivo (obligatorio, de 5 a 200 '
        'caracteres) y el usuario que lo anuló. El efecto que había generado se revierte: el vehículo queda libre '
        'para esa fecha. En todo el sistema no existe ninguna opción que elimine pedidos.')
captura('10-anular-pedido-motivo.png', 'Captura 10. Pantalla para anular, con el motivo.')
captura('11-pedido-anulado.png', 'Captura 11. Pedido anulado con fecha, usuario y motivo.')

# ---------------- 8. Consulta ----------------
doc.add_heading('8. Formulario de consulta', level=1)
parrafo('La consulta tiene filtros por rango de fechas (de la mudanza), estado, servicio y cliente, y desde cada '
        'pedido se entra a su detalle. El administrador ve todos los pedidos; el cliente ve solo los suyos y no '
        'tiene el filtro de cliente.')
captura('07-consulta-filtrada-pendientes.png', 'Captura 07. Consulta filtrada: pedidos pendientes desde hoy.')
captura('05-mis-pedidos-cliente.png', 'Captura 05. Lo que ve el cliente: solo sus pedidos.')

# ---------------- 9. Comprobante ----------------
doc.add_heading('9. Comprobante', level=1)
parrafo('Cada pedido tiene su comprobante, con el logo, el número, las fechas, el estado, los datos del cliente, la '
        'mudanza, el servicio con su precio y total, y el inventario. Si el pedido está anulado, lo muestra con la fecha, '
        'el usuario y el motivo. El botón «Imprimir / Guardar PDF» abre la impresión del navegador, desde donde se '
        'imprime o se guarda como PDF.')
captura('12-comprobante.png', 'Captura 12. Comprobante de un pedido confirmado.')

# ---------------- 10. Permisos ----------------
doc.add_heading('10. Perfiles y permisos', level=1)
parrafo('El acceso a cada opción respeta los perfiles y permisos del Hito 2. Para este proceso se agregó el rol '
        'Cliente y seis permisos, que el sistema consulta en la tabla PERMISOS antes de cada operación:')
tabla(['Permiso', 'Administrador', 'Cliente', 'Chofer / Ayudante'], [
    ['PED_REGISTRAR (registrar)', '', 'Sí', ''],
    ['PED_CONSULTAR (consultar)', 'Sí, todos', 'Sí, solo los suyos', ''],
    ['PED_GESTIONAR (confirmar y finalizar)', 'Sí', '', ''],
    ['PED_ANULAR (anular)', 'Sí', '', ''],
    ['PED_COMPROBANTE (emitir comprobante)', 'Sí', 'Sí, solo los suyos', ''],
    ['SRV_GESTIONAR (ABM de servicios)', 'Sí', '', ''],
], [6.2, 3.2, 3.6, 3])
parrafo('La acción restringida por perfil es la que pide la consigna: el cliente puede registrar pero no puede '
        'confirmar ni anular. Si alguien sin permiso intenta entrar a una opción, el sistema lo rechaza; y un cliente '
        'que pide el pedido de otro recibe «no encontrado».')
captura('08-detalle-admin-con-acciones.png', 'Captura 08. El administrador ve Confirmar y Anular.')
captura('15-detalle-cliente-sin-anular.png', 'Captura 15. El cliente ve su pedido sin esos botones.')

# ---------------- 11. Entregables ----------------
doc.add_heading('11. Entregables', level=1)
tabla(['La consigna pide entregar', 'Dónde está'], [
    ['Documento de avance', 'Este documento'],
    ['DER (si cambió)', 'Cambió: PEDIDOS, DETALLE_PEDIDOS, INVENTARIO_DETALLES y SERVICIOS sumaron columnas, '
                        'e INVENTARIO_DETALLES perdió el peso. El detalle está en la página «Cambios DER y DFD del Hito 3»'],
    ['DFD del proceso desarrollado', 'DFD «Registrar un Pedido» rehecho con la notación del grupo, más los procesos de consulta y anulación'],
    ['Scripts de base de datos actualizados', 'documentacion/sql/esquema_mudanzas.sql, en el repositorio'],
    ['Capturas del proceso completo', 'Carpeta «Capturas Hito3» (15 imágenes); las principales están en este documento'],
], [5.5, 10.5])

doc.add_heading('Cómo probarlo', level=2)
parrafo('Con Docker Desktop abierto, desde la carpeta del proyecto: docker compose up -d. Después se entra a '
        'http://localhost:8002 con estos usuarios:')
tabla(['Usuario', 'Contraseña', 'Rol'], [
    ['sarmientoc', 'Admin123!', 'Administrador'],
    ['gomezm', 'Cliente123!', 'Cliente'],
    ['fernandezl', 'Usuario123!', 'Chofer'],
], [5, 5, 6])
parrafo('El sistema tiene 141 pruebas automáticas que verifican estas reglas sobre MySQL '
        '(docker exec mudanzas_web python manage.py test).', color=GRIS)

numerar_paginas()
doc.save(SALIDA)
print('ok', SALIDA)
