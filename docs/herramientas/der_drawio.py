"""Borrador del DER en draw.io, armado desde los modelos reales (tablas, columnas, PK, FK y relaciones).

Se corre dentro del contenedor, porque lee los modelos de Django:
    docker exec mudanzas_web python docs/herramientas/der_drawio.py docs/der_borrador.drawio

Cada tabla es una caja con sus columnas (PK y FK marcadas) y cada clave foránea una relación 1 a N
con la notación pata de gallo. La posición de las tablas está pensada para leerse de arriba abajo:
seguridad, el pedido en el centro y sus detalles abajo. Es un borrador para revisar y retocar.
"""
import os
import sys
from html import escape
from xml.sax.saxutils import quoteattr

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
import django  # noqa: E402

django.setup()
from django.apps import apps  # noqa: E402
from django.db import connection  # noqa: E402

ANCHO = 230
# (tabla, columna, fila) de la grilla; las tablas nuevas respecto del DER del documento van en otro color
POSICIONES = {
    'ROLES': (0, 0), 'PERMISOS_ROLES': (1, 0), 'PERMISOS': (2, 0), 'SERVICIOS': (5, 0), 'RECURSOS_ASIGNADOS': (6, 0),
    'SUELDOS': (0, 1), 'USUARIOS': (1, 1), 'VEHICULOS': (3, 1),
    'LOG_AUDITORIA': (0, 2), 'PERSONAL_PEDIDO': (1, 2), 'PEDIDOS': (3, 2), 'DETALLE_PEDIDOS': (5, 2),
    'REPROGRAMACIONES': (2, 3), 'INVENTARIO_DETALLES': (3, 3), 'OBJETOS': (4, 3),
    'DETALLE_COBRANZAS': (5, 3), 'COBRANZAS': (6, 3),
}
NUEVAS = {'OBJETOS', 'PERSONAL_PEDIDO', 'REPROGRAMACIONES', 'LOG_AUDITORIA'}
X0, Y0, DX, FILAS_Y = 40, 60, 290, [70, 360, 800, 1240]


def tipo_sql(campo):
    t = (campo.db_type(connection) or '').upper()
    return t.replace('INTEGER', 'INT').replace(' AUTO_INCREMENT', '')


def main(salida):
    modelos = {m._meta.db_table: m for m in apps.get_app_config('usuarios').get_models()}
    celdas, ids, alto = [], {}, {}
    for n, (tabla, (col, fila)) in enumerate(POSICIONES.items(), start=2):
        m = modelos[tabla]
        filas = []
        for f in m._meta.concrete_fields:
            marca = 'PK' if f.primary_key else ('FK' if f.is_relation else '')
            nombre = f.db_column or f.column
            filas.append(f'<tr><td style="width:24px;font-weight:bold;color:#C04F00">{marca}</td>'
                         f'<td style="{"font-weight:bold;text-decoration:underline" if f.primary_key else ""}">'
                         f'{escape(nombre)}</td><td style="color:#7a6a60;text-align:right">{escape(tipo_sql(f))}</td></tr>')
        cabecera = '#7A3D00' if tabla in NUEVAS else '#C04F00'
        html = (f'<div style="background:{cabecera};color:#fff;font-weight:bold;padding:4px 6px;font-size:12px">'
                f'{tabla}</div><table style="width:100%;font-size:10px;border-collapse:collapse">{"".join(filas)}</table>')
        h = 26 + 15 * len(filas)
        x, y = X0 + col * DX, FILAS_Y[fila]
        ids[tabla], alto[tabla] = str(n), h
        celdas.append(f'<mxCell id="{n}" value={quoteattr(html)} style="rounded=0;whiteSpace=wrap;html=1;'
                      f'overflow=fill;verticalAlign=top;align=left;spacing=0;fillColor=#FFFFFF;strokeColor={cabecera};" vertex="1" '
                      f'parent="1"><mxGeometry x="{x}" y="{y}" width="{ANCHO}" height="{h}" as="geometry"/></mxCell>')
    n = 100
    for tabla, m in ((t, modelos[t]) for t in POSICIONES):
        for f in m._meta.concrete_fields:
            if not f.is_relation:
                continue
            padre = f.related_model._meta.db_table
            if padre not in ids:
                continue
            n += 1
            opcional = 'ERzeroToOne' if f.null else 'ERmandOne'
            celdas.append(f'<mxCell id="{n}" value="" style="edgeStyle=orthogonalEdgeStyle;'
                          f'rounded=0;html=1;endArrow=ERmany;startArrow={opcional};endFill=0;startFill=0;'
                          f'strokeColor=#5E524B;fontSize=9;fontColor=#5E524B;labelBackgroundColor=#FFFFFF;" edge="1" '
                          f'parent="1" source="{ids[padre]}" target="{ids[tabla]}"><mxGeometry relative="1" as="geometry"/>'
                          f'</mxCell>')
    nota = ('<b>DER — Mudanzas y Fletes Salta (Grupo 5)</b><br>Borrador generado desde la base real. '
            'En marrón oscuro, las tablas nuevas respecto del DER del documento. PK = clave primaria, FK = foránea. '
            'Las relaciones son 1 a N (pata de gallo del lado N).')
    celdas.append(f'<mxCell id="99" value={quoteattr(nota)} style="text;html=1;whiteSpace=wrap;fontSize=12;" vertex="1" '
                  f'parent="1"><mxGeometry x="{X0}" y="10" width="900" height="40" as="geometry"/></mxCell>')
    xml = ('<mxfile host="app.diagrams.net" type="device"><diagram name="DER" id="der">'
           '<mxGraphModel dx="1400" dy="900" grid="1" gridSize="10" guides="1" page="1" pageWidth="2100" '
           'pageHeight="2100"><root><mxCell id="0"/><mxCell id="1" parent="0"/>' + ''.join(celdas) +
           '</root></mxGraphModel></diagram></mxfile>')
    with open(salida, 'w', encoding='utf-8') as fh:
        fh.write(xml)
    print('ok', salida, len(POSICIONES), 'tablas')


if __name__ == '__main__':
    main(sys.argv[1])
