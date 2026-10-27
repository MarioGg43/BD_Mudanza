"""Genera el Modelo C4 (niveles 1 a 3) de Mudanzas y Fletes Salta en formato Draw.io.

Una página por diagrama: Nivel 1, Nivel 2, Nivel 3 Backend y Nivel 3 Frontend. Sigue el
método de la cátedra (Análisis y Diseño II): 3 colores, login en los dos lados, sin personas
en el nivel 3 y frontend y backend conectados por Cliente API <-> Controladores.

Uso: python docs/herramientas/modelo_c4.py "<salida>.drawio" [carpeta para vistas previas SVG]
"""
import sys
from pathlib import Path
from xml.sax.saxutils import escape, quoteattr

AZUL = ('#E6F1FB', '#185FA5', '#0C447C')     # sistema propio, contenedores y componentes
GRIS = ('#F1EFE8', '#5F5E5A', '#2C2C2A')     # externos y cajas de referencia de otro contenedor
PURPURA = ('#EEEDFE', '#534AB7', '#3C3489')  # personas (solo niveles 1 y 2)


class Pagina:
    def __init__(self, nombre, ancho, alto):
        self.nombre, self.ancho, self.alto = nombre, ancho, alto
        self.celdas, self.cajas, self.n = [], {}, 2

    def _id(self):
        self.n += 1
        return f'c{self.n}'

    def caja(self, clave, x, y, w, h, colores, titulo, tipo='', desc='', forma=None):
        """forma: None (caja), 'persona' (figura C4 de persona) o 'cilindro' (base de datos)."""
        fondo, borde, tinta = colores
        html = f'<b>{escape(titulo)}</b>'
        if tipo:
            html += f'<br><span style="font-size:10px">[{escape(tipo)}]</span>'
        if desc:
            html += f'<br><span style="font-size:11px">{escape(desc)}</span>'
        formas = {
            None: 'rounded=1;arcSize=6;spacing=6;',
            'persona': 'shape=mxgraph.c4.person2;verticalAlign=bottom;spacingBottom=14;spacingLeft=8;spacingRight=8;',
            'cilindro': 'shape=cylinder3;boundedLbl=1;backgroundOutline=1;size=14;spacing=6;',
        }
        estilo = (f'{formas[forma]}whiteSpace=wrap;html=1;fillColor={fondo};strokeColor={borde};'
                  f'fontColor={tinta};fontSize=13;')
        i = self._id()
        self.celdas.append(f'<mxCell id="{i}" value={quoteattr(html)} style="{estilo}" vertex="1" parent="1">'
                           f'<mxGeometry x="{x}" y="{y}" width="{w}" height="{h}" as="geometry"/></mxCell>')
        self.cajas[clave] = (i, x, y, w, h, colores, titulo, tipo, desc)
        return i

    def limite(self, clave, x, y, w, h, texto, colores=AZUL):
        _, borde, tinta = colores
        estilo = (f'rounded=1;arcSize=2;whiteSpace=wrap;html=1;fillColor=none;dashed=1;dashPattern=8 4;'
                  f'strokeColor={borde};fontColor={tinta};fontSize=13;fontStyle=1;align=left;'
                  f'verticalAlign=top;spacingLeft=10;spacingTop=4;')
        i = self._id()
        self.celdas.append(f'<mxCell id="{i}" value={quoteattr(escape(texto))} style="{estilo}" vertex="1" parent="1">'
                           f'<mxGeometry x="{x}" y="{y}" width="{w}" height="{h}" as="geometry"/></mxCell>')
        self.cajas[clave] = (i, x, y, w, h, None, texto, '', '')
        return i

    def flecha(self, desde, hasta, texto='', salida=None, entrada=None, puntos=()):
        estilo = ('edgeStyle=orthogonalEdgeStyle;rounded=0;orthogonalLoop=1;html=1;endArrow=block;endFill=1;'
                  'strokeColor=#5F5E5A;fontColor=#444441;fontSize=11;labelBackgroundColor=#FFFFFF;')
        if salida:
            estilo += f'exitX={salida[0]};exitY={salida[1]};exitDx=0;exitDy=0;'
        if entrada:
            estilo += f'entryX={entrada[0]};entryY={entrada[1]};entryDx=0;entryDy=0;'
        i = self._id()
        valor = quoteattr(escape(texto).replace('\n', '<br>'))
        geo = '<mxGeometry relative="1" as="geometry">'
        if puntos:
            geo += '<Array as="points">' + ''.join(f'<mxPoint x="{x}" y="{y}"/>' for x, y in puntos) + '</Array>'
        geo += '</mxGeometry>'
        self.celdas.append(f'<mxCell id="{i}" value={valor} style="{estilo}" edge="1" parent="1" '
                           f'source="{self.cajas[desde][0]}" target="{self.cajas[hasta][0]}">{geo}</mxCell>')
        self._flechas = getattr(self, '_flechas', []) + [(desde, hasta, texto, salida, entrada, puntos)]

    def xml(self, n):
        return (f'<diagram id="pag{n}" name={quoteattr(self.nombre)}><mxGraphModel dx="1400" dy="900" grid="1" '
                f'gridSize="10" guides="1" tooltips="1" connect="1" arrows="1" fold="1" page="1" pageScale="1" '
                f'pageWidth="{self.ancho}" pageHeight="{self.alto}" math="0" shadow="0"><root>'
                f'<mxCell id="0"/><mxCell id="1" parent="0"/>' + ''.join(self.celdas) +
                '</root></mxGraphModel></diagram>')

    def svg(self):
        """Vista previa aproximada (cajas y flechas rectas) para revisar que nada se pise."""
        p = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{self.ancho}" height="{self.alto}" '
             f'font-family="Arial" font-size="12"><rect width="100%" height="100%" fill="#fff"/>']
        for i, x, y, w, h, col, tit, tipo, desc in self.cajas.values():
            if col is None:
                p.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="none" stroke="#185FA5" '
                         f'stroke-dasharray="8 4"/><text x="{x + 10}" y="{y + 18}" font-weight="bold" '
                         f'fill="#0C447C">{escape(tit)}</text>')
                continue
            p.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="6" fill="{col[0]}" stroke="{col[1]}"/>')
            lineas = [(tit, 'bold', 13)] + ([(f'[{tipo}]', 'normal', 10)] if tipo else [])
            palabras, linea = desc.split(), ''
            for pal in palabras:
                if len(linea + ' ' + pal) * 6.2 > w - 16:
                    lineas.append((linea.strip(), 'normal', 11)); linea = ''
                linea += ' ' + pal
            if linea.strip():
                lineas.append((linea.strip(), 'normal', 11))
            alto_txt = len(lineas) * 15
            yy = y + (h - alto_txt) / 2 + 12
            for t, peso, tam in lineas:
                p.append(f'<text x="{x + w / 2}" y="{yy}" text-anchor="middle" font-weight="{peso}" '
                         f'font-size="{tam}" fill="{col[2]}">{escape(t)}</text>')
                yy += 15
        for desde, hasta, texto, salida, entrada, puntos in getattr(self, '_flechas', []):
            a, b = self.cajas[desde], self.cajas[hasta]
            x1 = a[1] + a[3] * (salida[0] if salida else 0.5); y1 = a[2] + a[4] * (salida[1] if salida else 1)
            x2 = b[1] + b[3] * (entrada[0] if entrada else 0.5); y2 = b[2] + b[4] * (entrada[1] if entrada else 0)
            camino = [(x1, y1)] + (list(puntos) if puntos else
                                   ([(x1, y2)] if (salida and salida[0] in (0, 1)) is False and x1 != x2 and False else
                                    [(x1, (y1 + y2) / 2), (x2, (y1 + y2) / 2)] if y1 != y2 else [])) + [(x2, y2)]
            p.append('<polyline points="' + ' '.join(f'{x},{y}' for x, y in camino) + '" fill="none" stroke="#5F5E5A"/>'
                     f'<circle cx="{x2}" cy="{y2}" r="3" fill="#5F5E5A"/>')
            if texto:
                mx, my = camino[len(camino) // 2]
                for k, linea in enumerate(texto.splitlines()):
                    p.append(f'<text x="{mx + 4}" y="{my - 4 + k * 13}" font-size="11" fill="#444">{escape(linea)}</text>')
        return ''.join(p) + '</svg>'


# ======================================================================= Nivel 1 · Contexto
n1 = Pagina('Nivel 1 - Contexto', 920, 660)
n1.caja('cli', 40, 20, 240, 190, PURPURA, 'Cliente', 'Persona',
        'Pide su mudanza desde la web, carga lo que hay que llevar y sigue su pedido', forma='persona')
n1.caja('adm', 340, 20, 240, 190, PURPURA, 'Administrador', 'Persona',
        'Dueño de la empresa: confirma pedidos, asigna personal y gestiona todo el sistema', forma='persona')
n1.caja('per', 640, 20, 240, 190, PURPURA, 'Personal', 'Persona',
        'Chofer y ayudantes de carga: consultan las mudanzas que tienen asignadas', forma='persona')
n1.caja('sis', 260, 300, 400, 130, AZUL, 'Sistema Mudanzas y Fletes Salta', 'Sistema de software',
        'Gestiona pedidos de mudanza, agenda de vehículos y personal, clientes, servicios, comprobantes y avisos')
n1.caja('pdf', 340, 520, 240, 100, GRIS, 'Generador de PDF', 'Librería externa',
        'Arma el comprobante del pedido y los listados en PDF')
n1.flecha('cli', 'sis', 'Registra y consulta pedidos', entrada=(0.15, 0))
n1.flecha('adm', 'sis', 'Administra y confirma')
n1.flecha('per', 'sis', 'Consulta su agenda', entrada=(0.85, 0))
n1.flecha('sis', 'pdf', 'Genera comprobantes [PDF]')

# ======================================================================= Nivel 2 · Contenedores
n2 = Pagina('Nivel 2 - Contenedores', 1480, 740)
n2.caja('cli', 20, 170, 200, 150, PURPURA, 'Cliente', 'Persona', 'Pide y sigue su mudanza', forma='persona')
n2.caja('adm', 20, 340, 200, 150, PURPURA, 'Administrador', 'Persona', 'Gestiona todo el sistema', forma='persona')
n2.caja('per', 20, 510, 200, 150, PURPURA, 'Personal', 'Persona', 'Consulta su agenda', forma='persona')
n2.limite('lim', 360, 150, 750, 530, 'Sistema Mudanzas y Fletes Salta [Sistema de software]')
n2.caja('front', 400, 200, 280, 440, AZUL, 'Aplicación Web Frontend', 'HTML, CSS y JavaScript · Bootstrap',
        'Pantallas que ve cada usuario en el navegador: pedir mudanza, consultas, panel de administración y portal')
n2.caja('back', 800, 230, 280, 160, AZUL, 'Backend', 'Python · Django 5',
        'Reglas de negocio: login y permisos, pedidos, disponibilidad, asignación de personal, avisos y comprobantes')
n2.caja('bd', 800, 470, 280, 160, AZUL, 'Base de Datos', 'MySQL 8',
        'Guarda usuarios, roles y permisos, vehículos, servicios, objetos, pedidos y personal asignado', forma='cilindro')
n2.caja('pdf', 1240, 255, 200, 110, GRIS, 'Generador de PDF', 'xhtml2pdf · Librería externa',
        'Produce el comprobante y los listados')
n2.flecha('cli', 'front', 'Usa [HTTPS]', salida=(1, 0.7), entrada=(0, 75 / 440))
n2.flecha('adm', 'front', 'Usa [HTTPS]', salida=(1, 0.7), entrada=(0, 245 / 440))
n2.flecha('per', 'front', 'Usa [HTTPS]', salida=(1, 0.7), entrada=(0, 415 / 440))
n2.flecha('front', 'back', 'Envía pedidos\n[HTTPS / JSON]', salida=(1, 110 / 440), entrada=(0, 0.5))
n2.flecha('back', 'bd', 'Lee y escribe [SQL]')
n2.flecha('back', 'pdf', 'Invoca\n[Librería PDF]', salida=(1, 0.5), entrada=(0, 0.5))

# ======================================================================= Nivel 3 · Backend
n3b = Pagina('Nivel 3 - Componentes Backend', 1180, 1080)
n3b.caja('capi', 300, 20, 280, 80, GRIS, 'Cliente API', 'Componente del Frontend Web',
         'Envía los pedidos de las pantallas')
n3b.limite('lim', 20, 130, 1140, 760, 'Contenedor: Backend [Python · Django 5]')
n3b.caja('ctrl', 300, 180, 280, 100, AZUL, 'Controladores', 'Vistas y URLs de Django',
         'Reciben los pedidos del frontend y los derivan al módulo correcto')
n3b.caja('seg', 660, 180, 200, 100, AZUL, 'Seguridad / Autenticación', 'USUARIOS',
         'Valida usuario y clave y controla la sesión')
n3b.caja('perm', 940, 180, 200, 100, AZUL, 'Control de Permisos', 'PERMISOS · PERMISOS_ROLES',
         'Verifica que el rol pueda hacer cada acción')
n3b.limite('neg', 40, 330, 1100, 400, 'Capa de lógica de negocio · un módulo por responsabilidad')
modulos = [
    ('Gestión de Usuarios', 'USUARIOS · SUELDOS', 'Alta, baja, correo y clave del personal'),
    ('Gestión de Roles', 'ROLES · PERMISOS_ROLES', 'Crea roles y elige sus permisos'),
    ('Registro de Clientes', 'USUARIOS', 'Alta de la cuenta del cliente desde la web'),
    ('Gestión de Vehículos', 'VEHICULOS', 'Alta, cambios, baja lógica y chofer habitual'),
    ('Gestión de Servicios', 'SERVICIOS · RECURSOS_ASIGNADOS', 'Servicios principales y adicionales'),
    ('Gestión de Objetos', 'OBJETOS', 'Catálogo de objetos del inventario'),
    ('Registro de Pedidos', 'PEDIDOS · DETALLE_PEDIDOS · INVENTARIO_DETALLES', 'Valida y guarda el pedido completo'),
    ('Disponibilidad', 'PEDIDOS · VEHICULOS · PERSONAL_PEDIDO', 'Vehículos y personal libres por día'),
    ('Estados del Pedido', 'PEDIDOS', 'Confirma, finaliza o anula con motivo'),
    ('Asignación de Personal', 'PERSONAL_PEDIDO', 'Asigna chofer y ayudantes a cada pedido'),
    ('Consulta de Pedidos', 'PEDIDOS', 'Filtros y avisos: vencidos, para finalizar, sin chofer'),
    ('Agenda del Personal', 'PERSONAL_PEDIDO · PEDIDOS', 'Próximas mudanzas de cada empleado'),
    ('Emisión de Documentos', 'PEDIDOS · DETALLE_PEDIDOS', 'Arma el comprobante y el listado de pedidos'),
]
for k, (t, tablas, d) in enumerate(modulos):
    n3b.caja(f'm{k}', 60 + (k % 5) * 214, 370 + (k // 5) * 118, 198, 104, AZUL, t, tablas, d)
n3b.caja('datos', 450, 770, 280, 100, AZUL, 'Acceso a Datos', 'ORM de Django',
         'Único componente que lee y guarda en la base vía SQL')
n3b.caja('bd', 450, 950, 280, 100, AZUL, 'Base de Datos', 'Contenedor: MySQL 8', '15 tablas', forma='cilindro')
n3b.caja('pdf', 860, 950, 260, 100, GRIS, 'Generador de PDF', 'xhtml2pdf · Librería externa',
         'Produce el comprobante y los listados')
n3b.flecha('capi', 'ctrl', 'Envía pedidos [HTTPS / JSON]')
n3b.flecha('ctrl', 'seg', 'Valida\nla sesión', salida=(1, 0.5), entrada=(0, 0.5))
n3b.flecha('seg', 'perm', 'Consulta\npermisos', salida=(1, 0.5), entrada=(0, 0.5))
n3b.flecha('ctrl', 'neg', 'Invoca', salida=(0.5, 1), entrada=(0.3636, 0))
n3b.flecha('neg', 'datos', 'Usa', salida=(0.5, 1), entrada=(0.5, 0))
n3b.flecha('datos', 'bd', 'Lee y escribe [SQL]')
n3b.flecha('m12', 'pdf', 'Invoca [Librería PDF]', salida=(1, 0.5), entrada=(0.5, 0), puntos=[(990, 658)])

# ======================================================================= Nivel 3 · Frontend
n3f = Pagina('Nivel 3 - Componentes Frontend', 1320, 1000)
n3f.limite('lim', 20, 20, 1280, 800, 'Contenedor: Aplicación Web Frontend [HTML, CSS y JavaScript]')
n3f.limite('pub', 40, 70, 240, 420, 'Vistas públicas')
n3f.caja('portada', 60, 110, 200, 100, AZUL, 'Portada', 'Solo lectura', 'Muestra los servicios de la empresa')
n3f.caja('login', 60, 230, 200, 110, AZUL, 'Pantalla de Login', 'Usuario o DNI y clave',
         'Ingreso y cambio de clave obligatorio')
n3f.caja('registro', 60, 360, 200, 110, AZUL, 'Registro de Cliente', 'Formulario', 'El cliente crea su cuenta')
n3f.limite('cli', 300, 70, 240, 420, 'Vistas del cliente')
n3f.caja('pedir', 320, 110, 200, 100, AZUL, 'Pedir Mudanza', 'Formulario',
         'Fecha, servicios, objetos y vehículo libre')
n3f.caja('mis', 320, 230, 200, 110, AZUL, 'Mis Pedidos', 'Solo lectura', 'Lista y detalle de sus pedidos')
n3f.caja('comp', 320, 360, 200, 110, AZUL, 'Comprobante', 'Solo lectura', 'Ver e imprimir o bajar en PDF')
n3f.limite('adm', 560, 70, 470, 540, 'Panel de administración (solo con permiso)')
pantallas = [
    ('Usuarios', 'Alta, baja, correo y clave'), ('Roles y Permisos', 'Tilda los permisos de cada rol'),
    ('Vehículos y Agenda', 'Flota y pedidos de cada vehículo'), ('Servicios', 'Principales y adicionales'),
    ('Objetos', 'Catálogo del inventario'), ('Pedidos y Avisos', 'Filtros, avisos y PDF'),
    ('Detalle del Pedido', 'Confirmar, finalizar o anular'), ('Asignar Personal', 'Chofer y ayudantes'),
]
for k, (t, d) in enumerate(pantallas):
    n3f.caja(f'a{k}', 580 + (k % 2) * 220, 110 + (k // 2) * 120, 200, 100, AZUL, t, '', d)
n3f.limite('por', 1050, 70, 230, 170, 'Portal del personal')
n3f.caja('agenda', 1065, 110, 200, 110, AZUL, 'Mis Próximas Mudanzas', 'Solo lectura',
         'Fecha, direcciones, equipo y qué llevar')
n3f.caja('capi', 520, 680, 300, 110, AZUL, 'Cliente API', 'Formularios y fetch / JSON',
         'Centraliza la comunicación de todas las pantallas con el backend')
n3f.caja('ctrl', 520, 880, 300, 100, GRIS, 'Controladores', 'Componente del Backend', 'Reciben los pedidos')
n3f.flecha('pub', 'capi', 'Envía credenciales\ny consulta', salida=(0.5, 1), entrada=(0, 0.3), puntos=[(160, 713)])
n3f.flecha('cli', 'capi', 'Envía pedidos\ny consulta', salida=(0.5, 1), entrada=(0.2, 0), puntos=[(420, 640), (580, 640)])
n3f.flecha('adm', 'capi', 'Envía comandos\ny datos', salida=(0.3, 1), entrada=(0.8, 0), puntos=[(701, 645), (760, 645)])
n3f.flecha('por', 'capi', 'Solicita datos', salida=(0.5, 1), entrada=(1, 0.3), puntos=[(1165, 713)])
n3f.flecha('capi', 'ctrl', 'Envía pedidos [HTTPS / JSON]')

PAGINAS = [n1, n2, n3b, n3f]

if __name__ == '__main__':
    salida = Path(sys.argv[1])
    salida.write_text('<mxfile host="app.diagrams.net" type="device">' +
                      ''.join(p.xml(i + 1) for i, p in enumerate(PAGINAS)) + '</mxfile>', encoding='utf-8')
    if len(sys.argv) > 2:
        carpeta = Path(sys.argv[2]); carpeta.mkdir(parents=True, exist_ok=True)
        for i, p in enumerate(PAGINAS, start=1):
            (carpeta / f'nivel_{i}.svg').write_text(p.svg(), encoding='utf-8')
    print('ok', salida)
