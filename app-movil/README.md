# App móvil Mudanzas Salta (prototipo)

Prototipo navegable de la app móvil: 35 pantallas, tres roles (cliente, administrador, empleado), con la identidad del manual (Poppins, naranja #FF7A00 → rojo #E10E0E). JavaScript sin frameworks; los datos se guardan en el navegador.

- **Publicado:** https://claude.ai/artifact/9vJxwT88TZboVHaoA5akPq (para actualizarlo, publicar `index.html` pasando esa URL).
- **Copia para usar sin internet:** `Descargas\App Mudanzas Movil\index.html` (incluye las capturas).
- **Figma:** archivo "Vistas", importado con html.to.design desde la página `#figma`.

## Archivos

| Archivo | Qué hace |
|---|---|
| `index.html` | Página en formato Artifact (sin doctype; se envuelve al publicar) |
| `logic.js` | Reglas de negocio puras: usuario automático, clave fuerte, patentes, totales, estados, candados |
| `data.js` | Datos de ejemplo (los del `init_data` del sistema, con fechas relativas a hoy) |
| `store.js` | Estado de la demo y una acción por proceso |
| `ui.js`, `styles.css` | Componentes y estilos |
| `screens-*.js` | Pantallas por rol |
| `app.js` | Rutas, permisos por rol y eventos |
| `gallery.js` | `#pantallas` (todas), `#figma` y `#figma-1`…`#figma-5` (para importar a Figma), `#vista-<id>` (una sola, para capturas) |
| `tests/` | Pruebas de la lógica y de los procesos |
| `herramientas/` | Scripts de apoyo (armar `local.html`, sacar capturas, generar las guías de Word) |
| `docs/` | Diseño aprobado y plan de trabajo |

## Comandos

Correr las pruebas (23):

```
node --test tests/logic.test.js tests/store.test.js
```

Armar `local.html` para abrir la app con doble clic:

```
python herramientas/build_local.py
```

Sacar las capturas de las 35 pantallas (necesita un servidor local en 8765 y Edge):

```
python -m http.server 8765 --bind 127.0.0.1
python herramientas/shots.py
```

## Usuarios de prueba

`sarmientoc` / `Admin123!` (administrador), `fernandezl` / `Usuario123!` (chofer), `romerol` / `Temporal123!` (ayudante, pide cambiar la clave), `gomezm` / `Cliente123!` (cliente).
