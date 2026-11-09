# Módulo de Analítica (Parcial N° 2, M1)

`analitica.py` lee la base MySQL del sistema con `mysql-connector-python`, transforma los datos con
**pandas**, calcula indicadores con **numpy** y genera con **matplotlib** cuatro gráficos de tipos
distintos y un tablero ejecutivo, en PNG, cada uno con su tabla de datos en CSV (`graficos/datos/`).

| Archivo | Pregunta de negocio | Tipo |
|---|---|---|
| `1_barras_servicios_por_mes.png` | ¿Cómo se comportó cada servicio mes a mes? | Barras agrupadas |
| `2_donut_participacion.png` | ¿Qué servicios concentran la facturación? | Donut |
| `3_lineas_objetivo.png` | ¿Estamos cumpliendo el objetivo mensual? | Líneas con tendencia |
| `4_heatmap_dia_hora.png` | ¿En qué días y horarios se concentran las mudanzas? | Heatmap |
| `5_tablero_ejecutivo.png` | Indicadores principales en una vista | Tablero (GridSpec) |

## Cómo se corre

Con Docker (es lo que se muestra en la defensa):

```bash
docker exec mudanzas_web python analitica/analitica.py
docker exec mudanzas_web python analitica/analitica.py --desde 2026-03-01 --hasta 2026-08-31 --objetivo 8000000
```

Sin Docker, con Python 3.11 o más y la base levantada en el puerto 3308:

```bash
pip install numpy pandas matplotlib mysql-connector-python
python analitica/analitica.py
```

Parámetros: `--desde` y `--hasta` (AAAA-MM-DD; por defecto del 1 de enero a hoy), `--objetivo`
(facturación mensual en pesos, por defecto 7.000.000) y `--salida` (carpeta de los PNG).

Para tener datos suficientes en los gráficos se pueden cargar pedidos de prueba del pasado:
`docker exec mudanzas_web python manage.py cargar_datos_demo` (y `--borrar` para sacarlos).

## Decisiones

- **pandas y no solo SQL:** SQL trae los datos; pandas hace lo que en SQL sería largo o
  dependiente del motor: `pivot_table` (mes × servicio y día × hora), `resample` mensual, `merge`
  del servicio principal y el pasaje de las horas UTC de la base a la hora de Salta.
- **numpy:** sumas, media, desvío, percentiles (p50 y p90 de la demora y del ticket), la
  tendencia (`polyfit`) y los montos inusuales (más de 3 desvíos sobre la media).
- **El mes en curso** se marca aparte (punteado y con el punto hueco) y no cuenta para la
  tendencia ni para los meses cumplidos, porque está incompleto.
- **Colores:** paleta categórica en orden fijo, validada para daltonismo; cada servicio conserva
  su color en todos los gráficos, y los números van como texto (etiquetas y CSV), no solo en el color.
