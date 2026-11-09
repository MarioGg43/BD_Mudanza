"""Módulo de Analítica y Visualización (Parcial N° 2, M1) — Mudanzas y Fletes Salta.

Se conecta a la MISMA base MySQL del sistema (con su conector nativo, mysql-connector-python),
lee las tablas transaccionales (PEDIDOS, DETALLE_PEDIDOS, SERVICIOS), las transforma con pandas,
calcula indicadores con numpy y genera con matplotlib cuatro gráficos de tipos distintos y un
tablero, cada uno respondiendo una pregunta de negocio. Los gráficos se guardan como PNG y, al
lado, una tabla CSV con los datos de cada uno.

| N° | Pregunta de negocio                                              | Gráfico                    |
|----|------------------------------------------------------------------|----------------------------|
| 1  | ¿Cómo se comportó cada servicio mes a mes?                        | Barras agrupadas           |
| 2  | ¿Qué servicios concentran la facturación?                         | Donut (participación)      |
| 3  | ¿Estamos cumpliendo el objetivo mensual de facturación?           | Líneas con tendencia       |
| 4  | ¿En qué días y horarios se concentran las mudanzas?               | Heatmap día × hora         |
| 5  | Tablero ejecutivo con los indicadores principales (opcional)      | Panel con GridSpec         |

Uso (parametrizado y reproducible):
    python analitica/analitica.py                                  # desde el 1/1 del año hasta hoy
    python analitica/analitica.py --desde 2026-03-01 --hasta 2026-08-31 --objetivo 8000000
    docker exec mudanzas_web python analitica/analitica.py         # dentro de Docker

La conexión sale de las variables DB_HOST, DB_PORT, DB_NAME, DB_USER y DB_PASSWORD (las tiene el
contenedor de Django) o, si no están, del archivo .env del proyecto apuntando al puerto 3308.
"""
import argparse
import os
from datetime import date, datetime
from zoneinfo import ZoneInfo
from pathlib import Path

import matplotlib

matplotlib.use('Agg')  # sin ventana: solo archivos PNG (sirve también dentro de Docker)
import matplotlib.pyplot as plt  # noqa: E402
import mysql.connector  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from matplotlib.colors import LinearSegmentedColormap  # noqa: E402
from matplotlib.gridspec import GridSpec  # noqa: E402
from matplotlib.ticker import FuncFormatter  # noqa: E402

RAIZ = Path(__file__).resolve().parent.parent
ZONA = 'America/Argentina/Salta'  # la base guarda las horas reales en UTC (Django, USE_TZ)

# ---------------------------------------------------------------- estilo
# Paleta categórica en orden fijo (validada para daltonismo); cada servicio conserva su color
# en todos los gráficos. Los colores de estado (sobre / bajo el objetivo) no se usan para series.
SERIES = ['#2a78d6', '#eb6834', '#1baf7a', '#eda100', '#e87ba4', '#008300']
OTROS = '#b9b7b0'
BUENO, CRITICO, OBJETIVO = '#0ca30c', '#d03b3b', '#898781'
TINTA, TINTA_2, MUTED, GRILLA, EJE, FONDO = '#0b0b0b', '#52514e', '#898781', '#e1e0d9', '#c3c2b7', '#fcfcfb'
AZULES = LinearSegmentedColormap.from_list(
    'azules', ['#f3f7fd', '#cde2fb', '#9ec5f4', '#6da7ec', '#3987e5', '#256abf', '#184f95', '#0d366b'])
MESES = ['ene', 'feb', 'mar', 'abr', 'may', 'jun', 'jul', 'ago', 'sep', 'oct', 'nov', 'dic']
DIAS = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo']

plt.rcParams.update({
    'figure.facecolor': FONDO, 'axes.facecolor': FONDO, 'savefig.facecolor': FONDO,
    'font.family': 'sans-serif', 'font.sans-serif': ['Segoe UI', 'DejaVu Sans', 'Arial'],
    'font.size': 10, 'text.color': TINTA, 'axes.labelcolor': TINTA_2, 'xtick.color': TINTA_2,
    'ytick.color': TINTA_2, 'axes.edgecolor': EJE, 'axes.titleweight': 'bold', 'axes.titlesize': 13,
    'axes.titlelocation': 'left', 'axes.titlepad': 12, 'axes.spines.top': False, 'axes.spines.right': False,
    'axes.grid': True, 'grid.color': GRILLA, 'grid.linewidth': 0.6, 'axes.axisbelow': True,
    'legend.frameon': False,
})


def pesos(valor, _=None):
    """$ 1.234.567 (formato argentino) para los ejes y las etiquetas."""
    return '$ ' + f'{valor:,.0f}'.replace(',', '.')


def millones(valor, _=None):
    return f'$ {valor / 1e6:,.1f} M'.replace('.', ',')


# ---------------------------------------------------------------- conexión y lectura
def datos_de_conexion(args):
    """Los datos de la base: argumentos > variables de entorno > .env del proyecto."""
    env = {}
    archivo = RAIZ / '.env'
    if archivo.exists():
        for linea in archivo.read_text(encoding='utf-8').splitlines():
            if '=' in linea and not linea.lstrip().startswith('#'):
                clave, valor = linea.split('=', 1)
                env[clave.strip()] = valor.strip()
    en_docker = bool(os.environ.get('DB_HOST'))
    return {
        'host': args.host or os.environ.get('DB_HOST') or 'localhost',
        'port': int(args.puerto or os.environ.get('DB_PORT') or (3306 if en_docker else 3308)),
        'database': os.environ.get('DB_NAME') or env.get('MYSQL_DATABASE', 'mudanzas_db'),
        'user': os.environ.get('DB_USER') or env.get('MYSQL_USER', 'mudanzas_user'),
        'password': os.environ.get('DB_PASSWORD') or env.get('MYSQL_PASSWORD', ''),
    }


def leer(conexion, sql, parametros=()):
    """Una consulta SQL a un DataFrame de pandas (con el cursor del conector nativo)."""
    cursor = conexion.cursor()
    cursor.execute(sql, parametros)
    columnas = [c[0] for c in cursor.description]
    df = pd.DataFrame(cursor.fetchall(), columns=columnas)
    cursor.close()
    return df


def cargar(conexion, desde, hasta):
    """Lee pedidos y servicios del período y arma un DataFrame por pedido con su servicio principal."""
    pedidos = leer(conexion, """
        SELECT p.id_pedido, p.Fecha_servicio AS fecha, p.Hora_servicio AS hora, p.Estado_pedido AS estado,
               p.Total_pedido AS total, p.Recargo_pedido AS recargo, p.Duracion_horas AS horas_estimadas,
               p.Inicio_real AS inicio_real, p.Fin_real AS fin_real
        FROM PEDIDOS p
        WHERE p.Fecha_servicio BETWEEN %s AND %s
    """, (desde, hasta))
    detalle = leer(conexion, """
        SELECT d.id_pedido, s.Tipo_servicio AS servicio, s.Categoria AS categoria, d.Subtotal AS subtotal
        FROM DETALLE_PEDIDOS d
        JOIN SERVICIOS s ON s.id_servicio = d.id_servicio
        JOIN PEDIDOS p ON p.id_pedido = d.id_pedido
        WHERE p.Fecha_servicio BETWEEN %s AND %s
    """, (desde, hasta))
    if pedidos.empty:
        raise SystemExit(f'No hay pedidos entre {desde} y {hasta}. Probá con otro rango o cargá los datos de prueba.')

    # ---- transformación con pandas
    pedidos['fecha'] = pd.to_datetime(pedidos['fecha'])
    pedidos['total'] = pedidos['total'].astype(float)
    pedidos['recargo'] = pedidos['recargo'].astype(float)
    # la hora de la base llega como timedelta (TIME de MySQL): se suma a la fecha
    pedidos['inicio'] = pedidos['fecha'] + pd.to_timedelta(pedidos['hora'])
    pedidos['hora_inicio'] = pedidos['inicio'].dt.hour
    pedidos['dia_semana'] = pedidos['inicio'].dt.dayofweek  # 0 = lunes
    for col in ('inicio_real', 'fin_real'):
        pedidos[col] = (pd.to_datetime(pedidos[col]).dt.tz_localize('UTC').dt.tz_convert(ZONA).dt.tz_localize(None))
    pedidos['demora_min'] = (pedidos['inicio_real'] - pedidos['inicio']).dt.total_seconds() / 60
    pedidos['horas_reales'] = (pedidos['fin_real'] - pedidos['inicio_real']).dt.total_seconds() / 3600

    detalle['subtotal'] = detalle['subtotal'].astype(float)
    principal = detalle[detalle['categoria'] == 'Principal'][['id_pedido', 'servicio']]
    pedidos = pedidos.merge(principal, on='id_pedido', how='left')  # merge: el servicio principal de cada pedido
    return pedidos, detalle


def colores_por_servicio(detalle):
    """Cada servicio tiene un color fijo (los principales primero), igual en todos los gráficos."""
    orden = (detalle.drop_duplicates('servicio')
             .assign(principal=lambda d: d['categoria'] != 'Principal')
             .sort_values(['principal', 'servicio'])['servicio'].tolist())
    return {s: SERIES[i] if i < len(SERIES) else OTROS for i, s in enumerate(orden)}


# ---------------------------------------------------------------- gráfico 1: barras agrupadas
def grafico_barras(ax, finalizados, colores):
    """¿Cómo se comportó cada servicio principal mes a mes? (pivot_table + barras agrupadas)."""
    tabla = (finalizados.assign(mes=finalizados['fecha'].dt.to_period('M'))
             .pivot_table(index='mes', columns='servicio', values='id_pedido', aggfunc='count', fill_value=0))
    servicios = [s for s in colores if s in tabla.columns]
    tabla = tabla[servicios]
    x = np.arange(len(tabla))
    ancho = 0.8 / len(servicios)
    for i, servicio in enumerate(servicios):
        ax.bar(x + (i - (len(servicios) - 1) / 2) * ancho, tabla[servicio], width=ancho * 0.9,
               color=colores[servicio], label=servicio, edgecolor=FONDO, linewidth=1)
    ax.set_xticks(x, [f'{MESES[p.month - 1]}\n{p.year}' if p.month == 1 or i == 0 else MESES[p.month - 1]
                      for i, p in enumerate(tabla.index)])
    ax.set_ylabel('Mudanzas finalizadas')
    ax.grid(axis='x', visible=False)
    ax.legend(ncols=len(servicios), loc='upper left', fontsize=9)
    ax.set_ylim(0, tabla.values.max() * 1.25)
    return tabla


# ---------------------------------------------------------------- gráfico 2: donut
def grafico_donut(ax, detalle_fin, colores, recargos=0.0, max_porciones=5):
    """¿Qué servicios concentran la facturación? (groupby + participación %). Los recargos del
    relevamiento son una porción más, así el total coincide con la facturación del tablero."""
    por_servicio = detalle_fin.groupby('servicio')['subtotal'].sum()
    if recargos:
        por_servicio['Recargos del relevamiento'] = recargos
    por_servicio = por_servicio.sort_values(ascending=False)
    if len(por_servicio) > max_porciones:  # los chicos se juntan en «Otros»
        por_servicio = pd.concat([por_servicio.iloc[:max_porciones - 1],
                                  pd.Series({'Otros': por_servicio.iloc[max_porciones - 1:].sum()})])
    total = por_servicio.sum()
    porcentajes = por_servicio / total * 100
    cuñas, _ = ax.pie(por_servicio, colors=[colores.get(s, OTROS) for s in por_servicio.index], startangle=90,
                      counterclock=False, wedgeprops={'width': 0.38, 'edgecolor': FONDO, 'linewidth': 2})
    # etiqueta directa en cada porción (nombre y %), con texto en tinta, no en el color de la serie
    for cuña, nombre, pct in zip(cuñas, por_servicio.index, porcentajes):
        angulo = np.deg2rad((cuña.theta1 + cuña.theta2) / 2)
        x, y = np.cos(angulo), np.sin(angulo)
        ax.annotate(f'{nombre}\n{pct:.1f} %'.replace('.', ','), xy=(0.81 * x, 0.81 * y), xytext=(1.22 * x, 1.18 * y),
                    ha='left' if x >= 0 else 'right', va='center', fontsize=9, color=TINTA,
                    arrowprops={'arrowstyle': '-', 'color': MUTED, 'linewidth': 0.8})
    ax.text(0, 0.08, millones(total), ha='center', va='center', fontsize=15, fontweight='bold')
    ax.text(0, -0.16, 'facturado', ha='center', va='center', fontsize=9, color=TINTA_2)
    ax.set_aspect('equal')
    ax.grid(False)
    return por_servicio.rename('facturacion').to_frame().assign(porcentaje=porcentajes.round(2))


# ---------------------------------------------------------------- gráfico 3: líneas con tendencia
def grafico_objetivo(ax, finalizados, objetivo, hasta, etiquetas=True):
    """¿Estamos cumpliendo el objetivo mensual? (resample mensual + tendencia con numpy.polyfit).
    Si el período corta a mitad de mes, ese último mes está incompleto: se marca aparte y no
    cuenta ni para la tendencia ni para los meses cumplidos."""
    mensual = finalizados.set_index('fecha')['total'].resample('MS').sum()
    incompleto = (pd.Timestamp(hasta) + pd.offsets.MonthEnd(0)).date() != hasta
    completos = mensual.iloc[:-1] if incompleto and len(mensual) > 1 else mensual
    x = np.arange(len(completos))
    ax.fill_between(completos.index, completos, objetivo, where=completos >= objetivo, interpolate=True,
                    color=BUENO, alpha=0.16, label='Sobre el objetivo', linewidth=0)
    ax.fill_between(completos.index, completos, objetivo, where=completos < objetivo, interpolate=True,
                    color=CRITICO, alpha=0.14, label='Bajo el objetivo', linewidth=0)
    ax.axhline(objetivo, color=OBJETIVO, linewidth=1.5, linestyle=(0, (5, 4)), label=f'Objetivo ({millones(objetivo)})')
    ax.plot(completos.index, completos, color=SERIES[0], linewidth=2, marker='o', markersize=5,
            markeredgecolor=FONDO, markeredgewidth=1.5, label='Facturación real')
    if incompleto and len(mensual) > 1:  # el mes en curso: punteado y con el punto hueco
        ax.plot(mensual.index[-2:], mensual.iloc[-2:], color=SERIES[0], linewidth=1.5, linestyle=(0, (2, 3)))
        ax.plot(mensual.index[-1], mensual.iloc[-1], marker='o', markersize=7, color=FONDO,
                markeredgecolor=SERIES[0], markeredgewidth=1.8, linestyle='none', label='Mes en curso (incompleto)')
    if len(completos) >= 3:  # tendencia lineal de los meses completos: hacia dónde va la facturación
        pendiente, ordenada = np.polyfit(x, completos.values, 1)
        ax.plot(completos.index, pendiente * x + ordenada, color='#184f95', linewidth=1.2, linestyle=':',
                label=f'Tendencia ({"+" if pendiente >= 0 else "−"}{millones(abs(pendiente))} por mes)')
    if etiquetas:  # etiqueta directa solo en el mejor y el peor mes completo y en el último
        for fecha in {completos.idxmax(), completos.idxmin(), mensual.index[-1]}:
            ax.annotate(millones(mensual[fecha]), (fecha, mensual[fecha]), textcoords='offset points',
                        xytext=(0, 9 if mensual[fecha] >= objetivo else -15), ha='center', fontsize=8.5, color=TINTA)
    ax.yaxis.set_major_formatter(FuncFormatter(millones))
    ax.set_xticks(mensual.index, [MESES[f.month - 1] for f in mensual.index])
    ax.grid(axis='x', visible=False)
    ax.legend(loc='upper left', bbox_to_anchor=(0, 1.02), ncols=3, fontsize=8.5)
    ax.set_ylim(0, max(mensual.max(), objetivo) * 1.3)
    cumplidos = int((completos >= objetivo).sum())
    tabla = mensual.rename('facturacion').to_frame().assign(
        objetivo=objetivo, cumplido=mensual >= objetivo,
        mes_completo=[True] * len(completos) + [False] * (len(mensual) - len(completos)))
    return tabla, cumplidos, len(completos)


# ---------------------------------------------------------------- gráfico 4: heatmap
def grafico_heatmap(ax, activos, anotar=True):
    """¿En qué días y horarios se concentran las mudanzas? (pivot_table día × hora + imshow)."""
    horas = list(range(int(activos['hora_inicio'].min()), int(activos['hora_inicio'].max()) + 1))
    matriz = (activos.pivot_table(index='dia_semana', columns='hora_inicio', values='id_pedido', aggfunc='count')
              .reindex(index=range(7), columns=horas).fillna(0))
    valores = matriz.values
    imagen = ax.imshow(valores, cmap=AZULES, aspect='auto', vmin=0)
    ax.set_xticks(range(len(horas)), [f'{h:02d}' for h in horas])
    ax.set_yticks(range(7), DIAS)
    ax.set_xlabel('Hora de inicio')
    ax.grid(False)
    for lado in ax.spines.values():
        lado.set_visible(False)
    if anotar:  # el número en cada celda (blanco sobre las oscuras)
        tope = valores.max() or 1
        for i in range(valores.shape[0]):
            for j in range(valores.shape[1]):
                if valores[i, j]:
                    ax.text(j, i, int(valores[i, j]), ha='center', va='center', fontsize=8,
                            color='#ffffff' if valores[i, j] > tope * 0.55 else TINTA)
    return matriz.astype(int), imagen


# ---------------------------------------------------------------- indicadores (numpy)
def indicadores(pedidos, finalizados):
    totales = finalizados['total'].to_numpy()
    demoras = finalizados['demora_min'].dropna().to_numpy()
    media, desvio = (np.mean(totales), np.std(totales)) if len(totales) else (0, 0)
    return {
        'facturacion': float(np.sum(totales)),
        'mudanzas': int(len(finalizados)),
        'ticket_promedio': float(media),
        'ticket_p90': float(np.percentile(totales, 90)) if len(totales) else 0,
        'cancelacion_pct': float(np.mean(pedidos['estado'] == 'Anulado') * 100),
        'demora_p50': float(np.percentile(demoras, 50)) if len(demoras) else 0,
        'demora_p90': float(np.percentile(demoras, 90)) if len(demoras) else 0,
        # montos inusuales: más de 3 desvíos sobre la media (para revisar si hubo un error de carga)
        'inusuales': int(np.sum(totales > media + 3 * desvio)) if desvio else 0,
    }


def tarjeta(ax, titulo, valor, detalle):
    ax.axis('off')
    ax.text(0.02, 0.72, titulo, fontsize=9.5, color=TINTA_2, transform=ax.transAxes)
    ax.text(0.02, 0.32, valor, fontsize=19, fontweight='bold', color=TINTA, transform=ax.transAxes)
    ax.text(0.02, 0.05, detalle, fontsize=8.5, color=MUTED, transform=ax.transAxes)


def guardar(fig, carpeta, nombre, pie):
    fig.text(0.01, 0.005, pie, fontsize=7.5, color=MUTED)
    ruta = carpeta / nombre
    fig.savefig(ruta, dpi=150, bbox_inches='tight')
    plt.close(fig)
    return ruta


# ---------------------------------------------------------------- principal
def main():
    hoy = datetime.now(ZoneInfo(ZONA)).date()  # la de Salta, aunque el contenedor esté en UTC
    p = argparse.ArgumentParser(description='Gráficos ejecutivos de Mudanzas y Fletes Salta (Parcial N° 2, M1).')
    p.add_argument('--desde', type=date.fromisoformat, default=date(hoy.year, 1, 1), help='AAAA-MM-DD (por defecto el 1/1)')
    p.add_argument('--hasta', type=date.fromisoformat, default=hoy, help='AAAA-MM-DD (por defecto hoy)')
    p.add_argument('--objetivo', type=float, default=7_000_000, help='Objetivo de facturación mensual en pesos')
    p.add_argument('--salida', type=Path, default=RAIZ / 'analitica' / 'graficos', help='Carpeta de los PNG')
    p.add_argument('--host')
    p.add_argument('--puerto')
    args = p.parse_args()
    if args.desde > args.hasta:
        raise SystemExit('La fecha --desde no puede ser posterior a --hasta.')

    conexion = mysql.connector.connect(**datos_de_conexion(args))
    try:
        pedidos, detalle = cargar(conexion, args.desde, args.hasta)
    finally:
        conexion.close()

    finalizados = pedidos[pedidos['estado'] == 'Finalizado']
    activos = pedidos[pedidos['estado'] != 'Anulado']
    detalle_fin = detalle[detalle['id_pedido'].isin(finalizados['id_pedido'])]
    colores = colores_por_servicio(detalle)
    kpi = indicadores(pedidos, finalizados)
    carpeta = args.salida
    (carpeta / 'datos').mkdir(parents=True, exist_ok=True)
    periodo = f'{args.desde:%d/%m/%Y} al {args.hasta:%d/%m/%Y}'
    pie = f'Mudanzas y Fletes Salta · Fuente: base del sistema (PEDIDOS, DETALLE_PEDIDOS, SERVICIOS) · Período: {periodo}'
    archivos = []

    # 1. Barras agrupadas
    fig, ax = plt.subplots(figsize=(11, 5))
    tabla = grafico_barras(ax, finalizados, colores)
    ax.set_title('¿Cómo se comportó cada servicio mes a mes?', loc='left', pad=26)
    ax.text(0, 1.025, 'Mudanzas finalizadas por mes y servicio principal', transform=ax.transAxes, fontsize=9.5, color=TINTA_2)
    archivos.append(guardar(fig, carpeta, '1_barras_servicios_por_mes.png', pie))
    tabla.to_csv(carpeta / 'datos' / '1_servicios_por_mes.csv')

    # 2. Donut
    fig, ax = plt.subplots(figsize=(9, 6))
    participacion = grafico_donut(ax, detalle_fin, colores, recargos=float(finalizados['recargo'].sum()))
    ax.set_title('¿Qué servicios concentran la facturación?', loc='left', pad=24)
    archivos.append(guardar(fig, carpeta, '2_donut_participacion.png', pie))
    participacion.to_csv(carpeta / 'datos' / '2_participacion.csv')

    # 3. Líneas con tendencia contra el objetivo
    fig, ax = plt.subplots(figsize=(11, 5))
    mensual, cumplidos, meses = grafico_objetivo(ax, finalizados, args.objetivo, args.hasta)
    ax.set_title(f'¿Estamos cumpliendo el objetivo mensual? Se cumplió en {cumplidos} de {meses} meses completos\n', loc='left')
    archivos.append(guardar(fig, carpeta, '3_lineas_objetivo.png', pie))
    mensual.to_csv(carpeta / 'datos' / '3_facturacion_mensual.csv')

    # 4. Heatmap
    fig, ax = plt.subplots(figsize=(11, 4.8))
    matriz, imagen = grafico_heatmap(ax, activos)
    barra = fig.colorbar(imagen, ax=ax, fraction=0.025, pad=0.02)
    barra.set_label('Mudanzas', color=TINTA_2)
    barra.outline.set_visible(False)
    ax.set_title('¿En qué días y horarios se concentran las mudanzas?', loc='left')
    archivos.append(guardar(fig, carpeta, '4_heatmap_dia_hora.png', pie))
    matriz.rename(index=dict(enumerate(DIAS))).to_csv(carpeta / 'datos' / '4_dia_hora.csv')

    # 5. Tablero ejecutivo (GridSpec)
    fig = plt.figure(figsize=(16, 10))
    grilla = GridSpec(3, 4, figure=fig, height_ratios=[0.32, 1, 1], hspace=0.5, wspace=0.35, top=0.92)
    tarjeta(fig.add_subplot(grilla[0, 0]), 'Facturación', millones(kpi['facturacion']), f'{kpi["mudanzas"]} mudanzas finalizadas')
    tarjeta(fig.add_subplot(grilla[0, 1]), 'Ticket promedio', pesos(kpi['ticket_promedio']),
            f'el 10 % más caro supera {pesos(kpi["ticket_p90"])}')
    tarjeta(fig.add_subplot(grilla[0, 2]), 'Cancelación', f'{kpi["cancelacion_pct"]:.1f} %'.replace('.', ','),
            'de los pedidos del período se anularon')
    tarjeta(fig.add_subplot(grilla[0, 3]), 'Demora al empezar (mediana)', f'{kpi["demora_p50"]:.0f} min',
            f'el 10 % más tarde: más de {kpi["demora_p90"]:.0f} min')
    ax = fig.add_subplot(grilla[1, :3])
    grafico_objetivo(ax, finalizados, args.objetivo, args.hasta, etiquetas=False)
    ax.set_title('Facturación mensual contra el objetivo\n', loc='left', fontsize=11.5)
    ax = fig.add_subplot(grilla[1, 3])
    grafico_donut(ax, detalle_fin, colores, recargos=float(finalizados['recargo'].sum()), max_porciones=4)
    ax.set_title('Participación por servicio', loc='left', fontsize=11.5, pad=18)
    ax = fig.add_subplot(grilla[2, :2])
    grafico_barras(ax, finalizados, colores)
    ax.set_title('Mudanzas por mes y servicio\n', loc='left', fontsize=11.5)
    ax = fig.add_subplot(grilla[2, 2:])
    grafico_heatmap(ax, activos, anotar=False)
    ax.set_title('Concentración por día y hora', loc='left', fontsize=11.5)
    fig.suptitle(f'Tablero ejecutivo · Mudanzas y Fletes Salta · {periodo}', x=0.125, y=0.975, ha='left', fontsize=15, fontweight='bold')
    archivos.append(guardar(fig, carpeta, '5_tablero_ejecutivo.png', pie))

    # resumen en la consola
    print(f'Período {periodo}: {len(pedidos)} pedidos leídos de la base ({kpi["mudanzas"]} finalizados).')
    print(f'Facturación {pesos(kpi["facturacion"])} · ticket promedio {pesos(kpi["ticket_promedio"])} · '
          f'cancelación {kpi["cancelacion_pct"]:.1f} % · demora mediana {kpi["demora_p50"]:.0f} min · '
          f'montos inusuales (> 3 desvíos): {kpi["inusuales"]}')
    print(f'Objetivo de {pesos(args.objetivo)} por mes: cumplido en {cumplidos} de {meses} meses completos.')
    for ruta in archivos:
        print('  ->', ruta.relative_to(RAIZ) if ruta.is_relative_to(RAIZ) else ruta)


if __name__ == '__main__':
    main()
