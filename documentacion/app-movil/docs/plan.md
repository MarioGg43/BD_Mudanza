# App móvil Mudanzas Salta — plan de implementación

> Ejecución inline en esta sesión (sin subagentes: el usuario no los pidió). Sin git: la
> carpeta no es un repositorio, así que no hay commits; cada tarea cierra con su verificación.

**Goal:** prototipo navegable de la app móvil completa (19 pantallas, 3 roles) publicado como
Artifact, con copia local y guía para importar a Figma.

**Architecture:** SPA en JavaScript sin frameworks, con router por hash. La lógica de negocio va
en funciones puras (`logic.js`) testeadas con Node; el estado vive en un store con localStorage;
cada pantalla es una función `render(ctx) → HTML` más sus manejadores, de modo que la galería
puede renderizar cualquier pantalla con datos fijos.

**Tech Stack:** HTML + CSS + JS vanilla, Google Fonts (Poppins), Node 24 (`node --test`) para la
lógica, Edge headless para capturas.

## Global Constraints
- Identidad: Poppins; `--naranja:#FF7A00`, `--rojo:#E10E0E`, `--coral:#FC7753`, `--amarillo:#FFC107`; degradé naranja→rojo.
- Pantalla de diseño: 390 × 844 px. En pantallas de menos de 500 px, la app ocupa todo el ancho sin marco.
- Todo texto visible en español rioplatense (voseo).
- localStorage siempre dentro de try/catch; la app funciona aunque falle.
- Scripts externos solo de los CDN permitidos; fuentes solo de Google Fonts.
- Sin datos personales reales: los datos de ejemplo son los del `init_data` del sistema y otros inventados.

## Archivos (carpeta de trabajo `scratchpad/app/`)
| Archivo | Responsabilidad |
|---|---|
| `index.html` | Esqueleto: marco del celular, panel lateral de demo, carga de CSS y JS |
| `styles.css` | Tokens y componentes (appbar, tabbar, tarjetas, campos, badges, hojas, modales, toasts, galería) |
| `logic.js` | Funciones puras: usuario automático, validaciones, totales, transiciones de estado, candados, formatos |
| `data.js` | `buildSeed(today)`: datos de ejemplo con fechas relativas a hoy |
| `store.js` | `Store`: carga/guarda/reinicia el estado y ejecuta las acciones de negocio usando `logic.js` |
| `ui.js` | `esc`, íconos SVG, componentes HTML, `toast`, `sheet`, `confirmDialog` |
| `screens-auth.js` | Inicio, login, registro, recuperar y cambiar clave, perfil |
| `screens-cliente.js` | Inicio, pedir mudanza (5 pasos), mis pedidos, detalle |
| `screens-admin.js` | Panel, pedidos, detalle, asignar, cobro, vehículos (CRUD), usuarios, servicios |
| `screens-empleado.js` | Mis mudanzas, detalle con iniciar/finalizar |
| `app.js` | Tabla de rutas, guardas por rol, render y delegación de eventos |
| `gallery.js` | `#/pantallas`: todas las vistas estáticas con su título |
| `img/` | `logo-color.png`, `logo-blanco.png`, `icono.png` |
| `tests/logic.test.js` | Tests de `logic.js` |

## Interfaces compartidas
- `window.Logic`: `username(apellido, nombre, existentes) → string`, `validarClave(clave) → string|null`,
  `validarCorreo(c) → bool`, `validarPatente(p) → bool`, `totalPedido(pedido, servicios) → number`,
  `saldoPedido(pedido, servicios, cobranzas) → number`, `puedeDarDeBaja(actor, objetivo, usuarios) → string|null`,
  `siguienteEstado(estado, accion) → string|null`, `money(n) → "$ 185.000"`, `fecha(iso) → "jue 1 oct"`.
- `window.Store`: `state`, `session`, `load()`, `save()`, `reset()`, `login(ident, clave)`, `logout()`, y una acción por
  proceso (`registrarCliente`, `recuperarClave`, `cambiarClave`, `modificarPerfil`, `crearPedido`, `confirmarPedido`,
  `rechazarPedido`, `asignarRecursos`, `registrarCobro`, `guardarVehiculo`, `bajaVehiculo`, `altaUsuario`,
  `modificarCorreo`, `cambiarRol`, `restablecerClave`, `bajaUsuario`, `reactivarUsuario`, `guardarServicio`,
  `iniciarMudanza`, `finalizarMudanza`). Las acciones devuelven `{ok:true, ...}` o `{ok:false, error}`.
- Pantallas: `Screens[nombre] = { title, role, render(ctx) → html, bind?(root, ctx) }`, con
  `ctx = { state, session, params, go(ruta), refresh() }`.

## Tareas
1. **Lógica pura con tests.** `logic.js` + `tests/logic.test.js`. Verificar: `node --test` en verde, cubriendo
   usuario automático (tildes, duplicados), clave fuerte, patente vieja y Mercosur, totales/saldo, transiciones
   y candados.
2. **Datos y store.** `data.js`, `store.js`. Verificar con un script de Node: login de los 4 roles, romerol
   pide cambio de clave, crear pedido → confirmar → asignar → iniciar → finalizar, cobro que deja saldo 0, baja
   del último administrador rechazada.
3. **Base visual y router.** `index.html`, `styles.css`, `ui.js`, `app.js`, imágenes del logo. Verificar en el
   navegador: marco del celular, panel de demo, navegación por hash y guardas (sin sesión va al login).
4. **Pantallas sin sesión y perfil.** Verificar en el navegador cada validación y los accesos rápidos.
5. **Cliente.** Verificar el pedido completo de punta a punta y que aparece en Mis pedidos.
6. **Administrador.** Verificar confirmar/rechazar, asignar, cobro, CRUD de vehículos, usuarios con candados,
   servicios.
7. **Empleado.** Verificar iniciar y finalizar, y que el cliente ve el cambio de estado.
8. **Galería y publicación.** `gallery.js`; publicar el Artifact; copiar a `Descargas\App Mudanzas Movil\`;
   capturas PNG por pantalla con Edge headless; revisar en ancho de celular (375 px).
9. **Guía para Figma.** Word corto con html.to.design (importar), Prototype (conectar) y la app de Figma
   (probar en el celular), más la opción de importar las PNG.
