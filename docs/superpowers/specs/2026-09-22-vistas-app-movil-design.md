# Diseño de las vistas de la app móvil — Mudanzas y Fletes Salta

Materia: Desarrollo Web. Grupo 5. Fecha: 2026-09-22.

## Objetivo

Diseñar las pantallas de una app móvil según la consigna "Diseño de vistas": cinco vistas obligatorias, con estilo visual consistente entre todas. El entregable final del alumno se arma en Visily; este mockup es la referencia visual que se copia ahí.

La app es de uso interno: la usa el personal de la empresa, no el cliente final.

## Identidad visual

La misma que ya usa el sistema web del CRUD de vehículos, para que todo el proyecto se vea de una sola familia.

| Elemento | Valor |
|---|---|
| Naranja principal | `#ea580c` |
| Naranja oscuro | `#c2410c` |
| Degradé | `#dc2f02 → #e85d04 → #f48c06 → #faa307` |
| Fondo | `#f8fafc` |
| Texto | `#1e293b` |
| Texto secundario | `#64748b` |
| Tipografía | Inter |
| Tamaño de pantalla | 390 × 844 px |

Estados del vehículo: verde `#16a34a` Disponible, ámbar `#d97706` En viaje, gris `#64748b` En mantenimiento.

## Pantallas

Ocho en total: las cinco que pide la consigna más tres que la propia consigna implica (formulario de alta, confirmación de borrado y detalle).

1. **Inicio (splash)** — Fondo con degradé. Logo en tarjeta blanca, nombre de la empresa y misión en dos líneas. Botón blanco "Comenzar".
2. **Login** — Correo y contraseña (con ojito para mostrarla), "¿Olvidaste tu contraseña?", botón "Iniciar sesión", enlace a registro.
3. **Registro** — Nombre completo, correo, contraseña y confirmación, con la regla de 8 caracteres a la vista. Botón "Registrarse" y vuelta al login.
4. **Vehículos (CRUD)** — Encabezado naranja, buscador por patente o modelo, filtros por estado, lista de tarjetas con patente, marca y modelo, capacidad, etiqueta de estado e íconos ver / editar / eliminar. Botón flotante "+". Navegación inferior: Inicio, Vehículos, Perfil.
5. **Detalle del vehículo** — Ficha completa de una unidad, con sus datos y accesos a editar y eliminar.
6. **Agregar vehículo** — Formulario: patente, marca y modelo, tipo, capacidad en kg, capacidad en m³ y estado. Botones "Cancelar" y "Guardar vehículo".
7. **Confirmar eliminación** — Cartel sobre el listado, con la patente en el texto y botones "Cancelar" y "Eliminar".
8. **Perfil** — Avatar con inicial, nombre y rol. Nombre, correo y teléfono editables. "Guardar cambios" y "Cerrar sesión".

## Misión (texto aprobado)

> Trasladamos tu casa o tu oficina, en Salta y a todo el país, con la seguridad de que cada cosa llega como salió.

## Entregable

Una página web con las ocho pantallas lado a lado, publicada como artifact, más las imágenes sueltas de cada pantalla para tener de referencia al copiarlas en Visily.

## Decisiones tomadas

- **Tabla del CRUD: Vehículos.** Ya existe ese CRUD en Django, así que los campos y estados son los reales.
- **Alta fidelidad, no wireframe.** La consigna pide que el diseño refleje la identidad de la empresa.
- **El mockup no es la entrega.** La entrega se arma en Visily; esto es la referencia.
