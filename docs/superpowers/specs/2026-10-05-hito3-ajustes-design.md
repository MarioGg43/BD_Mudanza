# Hito 3 — Ajustes pedidos por el grupo

Fecha: 05/10/2026. Rama: `hito3-pedidos`. Modifica la especificación
`2026-10-05-hito3-pedidos-design.md`; lo que no se menciona acá sigue igual.

## 1. Un solo servicio por pedido

El cliente elige **un** servicio (Mudanza local, Mudanza nacional o Flete urbano),
con opciones excluyentes. Se mantiene la estructura cabecera–detalle: el pedido
lleva una fila en DETALLE_PEDIDOS y una o más filas en INVENTARIO_DETALLES. El total
del pedido es el precio del servicio elegido. El servidor rechaza un servicio
inexistente o inactivo con la clave de error `servicio`.

## 2. Hora de inicio de la mudanza

PEDIDOS suma `Hora_servicio` (TIME). Se carga en «Cuándo y dónde» y es obligatoria.
- Tiene que estar entre las 07:00 y las 20:00, inclusive.
- Si la mudanza es para hoy, la hora tiene que ser posterior a la actual.

Se muestra junto a la fecha en la consulta, el detalle y el comprobante. La
disponibilidad del vehículo sigue siendo por día: un vehículo, un pedido por día.

## 3. Inventario con lista fija y sin peso

Cada objeto se elige de una lista fija definida en el sistema
(`reglas.OBJETOS_INVENTARIO`): Heladera, Cocina, Lavarropas, Microondas,
Cama 1 plaza, Cama 2 plazas, Colchón, Ropero, Cómoda, Mesa, Sillas, Sillón,
Televisor, Escritorio, Biblioteca, Cajas, Bolsos y valijas, Bicicleta y Plantas.
Cada fila tiene objeto, cantidad (de 1 a 999) y frágil. Un objeto que no esté en
la lista se rechaza.

El **peso se elimina**: la columna `Peso` sale de INVENTARIO_DETALLES, y con ella el
peso total y el control de capacidad del vehículo. La capacidad del vehículo se
sigue mostrando, pero solo como dato.

## 4. Comprobante

Sin cambios funcionales. Se quitan solo la columna de peso y el peso total.

## 5. Colores: identidad de la app móvil en todas las pantallas

Son los colores del manual de identidad, los mismos que usa `app-movil/styles.css`:

| Token | Valor |
|---|---|
| naranja | `#FF7A00` |
| rojo | `#E10E0E` |
| coral | `#FC7753` |
| amarillo | `#FFC107` |
| degradé de marca | `linear-gradient(128deg, #FF8A00 0%, #FF5E08 48%, #E10E0E 100%)` |
| naranja oscuro / suave | `#C04F00` / `#FFF0E2` |
| tinta / tinta 2 / tinta 3 | `#231A15` / `#5E524B` / `#9A8D85` |
| línea | `#EEE4DD` |
| fondo | `#FAF6F3` |
| tarjeta | `#FFFFFF` |
| letra | Poppins (Google Fonts) |

- **Estados:** Pendiente sobre amarillo (`#FFF2C9` / texto `#875600`), Confirmado
  azul (`#E5EEFC` / `#1E5BB8`), Finalizado verde (`#E2F3E9` / `#17784A`), Anulado
  gris (`#EFE9E4` / `#5E524B`).
- **Encabezado:** el degradé de marca con el logo en blanco.
- **Botones principales:** el degradé, o naranja sólido, con el texto en blanco.
- **Alcance:** todas las pantallas. Son las de estilo Bootstrap (portada, vehículos,
  pedidos, servicios, crear cuenta, comprobante) y las de estilo Tailwind (login,
  panel del administrador y portal del personal), que hoy son oscuras y pasan a ser
  claras.
- Una sola hoja de estilos de marca compartida: `usuarios/static/css/marca.css`.

## 6. Fuera de alcance (posible a futuro)

Que el cliente adjunte fotos de los objetos para que la empresa defina el precio
final o si algo se desarma.
