# Hito 3 — Ajustes: plan de implementación

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Objetivo:** un servicio por pedido, la hora de inicio, el inventario con lista fija y sin peso, y los colores de la app móvil en todas las pantallas.

**Especificación:** `docs/superpowers/specs/2026-10-05-hito3-ajustes-design.md`

## Restricciones globales

- Stack: Django + Docker + MySQL. No se agregan dependencias.
- Los comandos de Django corren en el contenedor: `docker exec mudanzas_web python manage.py ...`.
- Al terminar cada tarea, toda la suite en verde (`docker exec mudanzas_web python manage.py test`) y `makemigrations --check --dry-run` sin cambios.
- Textos en español rioplatense.
- Colores exactos de la sección 5 de la especificación de ajustes.

---

### Tarea A: Un servicio, hora de inicio e inventario sin peso

**Archivos:** `usuarios/models.py`, migración nueva `usuarios/migrations/0004_*.py` (generada), `usuarios/management/commands/init_data.py`, `pedidos/reglas.py`, `pedidos/forms.py`, `pedidos/views.py`, `pedidos/templates/pedidos/{nuevo,_fila_inventario,detalle,lista,comprobante}.html`, las pruebas de `pedidos/test_reglas.py`, `pedidos/test_vistas.py`, `pedidos/test_servicios.py`, `vehiculos/tests.py`, `usuarios/tests.py`, `README.md`, `docs/sql/esquema_mudanzas.sql`.

**Interfaces que cambian:**
- `reglas.OBJETOS_INVENTARIO`: tupla de str con los 19 objetos de la especificación, en ese orden.
- `reglas.HORA_DESDE = time(7, 0)` y `reglas.HORA_HASTA = time(20, 0)`.
- `reglas.registrar_pedido(cliente, fecha_servicio, hora_servicio, origen, destino, id_servicio, patente, items)`:
  - `id_servicio` es un int (o None);
  - cada item es `{'descripcion': str, 'cantidad': int, 'fragil': bool}`;
  - claves de error: `fecha_servicio`, `hora_servicio`, `origen`, `destino`, `servicio`, `inventario`, `vehiculo`.
- `Pedido.hora_servicio`: `TimeField(default=time(9, 0), db_column='Hora_servicio', verbose_name='Hora de inicio')`.
- Se eliminan `InventarioDetalle.Peso`, `Pedido.peso_total` y el control de capacidad. `InventarioDetalle.__str__` pasa a devolver `f'{self.Cantidad} x {self.Descripcion}'`.
- `PedidoForm`:
  - el campo `servicio` es un `ModelChoiceField` con `RadioSelect` sobre los servicios activos (reemplaza a `servicios`);
  - suma `hora_servicio`: `TimeField` con widget `<input type="time">` y `format='%H:%M'`, step 900;
  - `vehiculo` queda igual.
- `ItemInventarioForm`: `descripcion` pasa a ser un `ChoiceField` con `[('', 'Elegí un objeto')] + [(o, o) for o in reglas.OBJETOS_INVENTARIO]`; suma `cantidad` y `fragil`; deja de tener `peso`.

**Reglas nuevas en `registrar_pedido`:**
- Hora: obligatoria (`'Elegí la hora de inicio.'`). Fuera de 07:00 a 20:00: `'La mudanza puede empezar entre las 07:00 y las 20:00.'`. Si `fecha_servicio` es hoy y la hora no es posterior a `timezone.localtime().time()`: `'Para hoy, elegí una hora que todavía no pasó.'`.
- Servicio: `None` da `'Elegí un servicio.'`; inexistente o inactivo da `'Ese servicio ya no está disponible.'` (clave `servicio`).
- Inventario: si la descripción no está en `OBJETOS_INVENTARIO`, `f'Objeto {n}: elegilo de la lista.'`. La cantidad sigue entre 1 y 999. Sin items: `'Agregá al menos un objeto.'`.
- Se quitan las validaciones de peso y de capacidad. Lo demás sigue igual: fecha de hoy a un año, origen y destino distintos, vehículo libre bajo `select_for_update` y la transacción.
- La cabecera guarda `hora_servicio` y `total = servicio.Precio_base`. Crea un solo `DetallePedido` con el precio copiado.

**Pantallas:**
- `nuevo.html`:
  - Servicios: radios, cada uno con `data-precio`; el total en vivo es el precio del elegido.
  - La sección 1 suma la hora.
  - Las filas de inventario tienen select de objeto, cantidad y frágil, sin peso ni peso total.
  - Vehículos: la opción muestra `patente · tipo · marca · hasta X kg / Y m³`, solo como dato. El JSON de `vehiculos-libres` suma `capacidad_m3`.
- `detalle.html` y `comprobante.html`: «Fecha: dd/mm/aaaa a las HH:MM». La tabla de inventario queda con Objeto, Cantidad y Frágil, sin peso total.
- `lista.html`: la columna «Mudanza» muestra fecha y hora.

**Datos:** `init_data` crea el pedido de ejemplo con `hora_servicio=time(9, 0)` y el inventario `Descripcion='Cajas', Cantidad=42, Fragil=True`, sin Peso. La migración 0004 se genera con `makemigrations usuarios --name hito3_ajustes`. Después se regenera `docs/sql/esquema_mudanzas.sql` con `sqlmigrate` de 0001, 0002 y 0004, siguiendo el mismo procedimiento de la Tarea 10 del plan anterior.

**Pruebas (TDD):** adaptar las pruebas existentes a la firma nueva, borrar las de peso y capacidad, y agregar:
- hora vacía, a las 06:59, a las 20:01, y hoy en una hora que ya pasó (para hoy usar `timezone.localtime() - 1 h`, y saltear la prueba si eso cae antes de las 07:00);
- hora válida a las 07:00 y a las 20:00;
- servicio None, servicio inexistente y servicio inactivo;
- objeto fuera de la lista;
- que el pedido creado tenga un solo detalle y `total == Precio_base`;
- en pantalla: el POST con `servicio` (radio) y `hora_servicio` registra el pedido, y la vista muestra la hora en el detalle.

README: en «Reglas del Hito 3», cambiar la línea de validaciones (sin peso ni capacidad; un servicio; hora de 07 a 20) y nombrar la lista fija de objetos.

**Commit:** `Use one service per order, add the start time and a fixed item list without weight`

---

### Tarea B: Identidad de la app móvil en las pantallas Bootstrap

**Archivos:**
- Crear: `usuarios/static/css/marca.css`.
- Modificar: `vehiculos/templates/vehiculos/base.html`, `vehiculos/templates/vehiculos/inicio.html`, las plantillas de `vehiculos/` y `pedidos/` donde haga falta, y `pedidos/templates/pedidos/comprobante.html`.

**Qué hacer:**
1. `marca.css`:
   - Define los tokens de la sección 5 de la especificación como variables CSS (`--naranja`, `--rojo`, `--coral`, `--amarillo`, `--grad`, `--naranja-osc`, `--naranja-suave`, `--tinta`, `--tinta-2`, `--tinta-3`, `--linea`, `--fondo`, `--card`) y la letra Poppins.
   - Pisa Bootstrap:
     - `body`: fondo `--fondo`, color `--tinta`, Poppins.
     - `.btn-success` y `.btn-primary`: degradé de marca, texto blanco, sin borde; hover un poco más oscuro.
     - `.btn-warning`: amarillo con texto tinta. `.btn-outline-*`: borde `--linea`.
     - `a`: `--naranja-osc`.
     - `.card-panel`: fondo blanco, borde `--linea`, radio 16px, sombra suave.
     - Focus visible de 2.5px en naranja. `.form-check-input:checked` en naranja.
     - Badges de estado `.estado-pendiente`, `.estado-confirmado`, `.estado-finalizado` y `.estado-anulado` con los pares de colores de la especificación.
     - Encabezado `.navbar-brand-custom` con el degradé de marca.
   - La hoja se usa también en la Tarea C, así que conviene escribir tokens y clases reutilizables.
2. `vehiculos/base.html`:
   - Carga Poppins (Google Fonts, pesos 400/500/600/700) y `{% static 'css/marca.css' %}` después de Bootstrap.
   - Saca el `<style>` inline que hoy define naranja quemado, marrón e Inter.
   - El encabezado usa el degradé con el logo. Los enlaces del menú quedan en blanco, el activo con subrayado o fondo translúcido.
3. `pedidos/_estado.html`: las clases `estado-*` reemplazan a `text-bg-*`.
4. `inicio.html` (portada): el bloque principal usa el degradé y botones blancos o claros.
5. `comprobante.html`:
   - el borde del encabezado y los títulos pasan a naranja/rojo de marca;
   - Poppins con respaldo Arial;
   - debe seguir siendo legible al imprimir en blanco y negro.

**Verificación:** la suite en verde (la Tarea B no cambia la lógica). Captura o descripción del controlador en el navegador de `/`, `/vehiculos/`, `/pedidos/`, `/pedidos/nuevo/`, `/servicios/` y `/registro/`.

**Commit:** `Apply the mobile app brand colors to the Bootstrap pages`

---

### Tarea C: Login, panel y portal en claro con la misma identidad

**Archivos:** `usuarios/templates/base.html`, `usuarios/templates/login.html`, `usuarios/templates/admin_dashboard.html`, `usuarios/templates/usuario_portal.html`, `usuarios/static/css/palette.css` (o reemplazarlo por `marca.css`).

**Qué hacer:**
- Estas pantallas usan Tailwind por CDN, con fondos oscuros escritos a mano (`bg-[#121316]`, `bg-[#1c1e24]`, `bg-[#252833]`, `border-gray-700/800`, `text-gray-100/300/400`, `text-white`, etc.).
- Pasarlas a tema claro con los tokens de `marca.css`:
  - fondo `--fondo`, tarjetas blancas con borde `--linea`;
  - texto `--tinta` / `--tinta-2`;
  - encabezados con el degradé de marca y el logo en blanco;
  - botones principales con el degradé;
  - tablas con encabezado `--naranja-suave`;
  - modales con fondo blanco;
  - inputs con fondo blanco y borde `--linea`, y focus naranja.
- Cargar Poppins y `marca.css` en `usuarios/templates/base.html`.
- Conservar todos los `id`, `name`, `onclick` y las funciones JS: solo cambian las clases y los estilos.
- Las clases propias de `palette.css` (`text-harvest-orange`, `text-amber-gold`, `text-racing-red`, `grad-brand`, `btn-primary`, `btn-flame`, etc.) se reasignan a los tokens nuevos para que el amarillo y el texto blanco se lean sobre fondo claro. Por ejemplo, `text-amber-gold` sobre blanco pasa a `--naranja-osc`.
- No cambia ninguna funcionalidad. La suite tiene que seguir en verde: las pruebas del Hito 2 buscan textos, no clases.

**Verificación:** la suite en verde. El controlador revisa `/login/` (incluido el modal «¿Olvidaste tu contraseña?»), `/panel/` (con los modales de alta, modificar correo y restablecer clave) y `/portal/` (como `fernandezl`).

**Commit:** `Move the login, admin panel and staff portal to the light brand theme`
