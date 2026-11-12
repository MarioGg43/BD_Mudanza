// Genera usuarios/static/css/tailwind.min.css, el CSS de las pantallas que usan usuarios/templates/base.html.
// Antes se cargaba el compilador de Tailwind desde cdn.tailwindcss.com y armaba los estilos en cada visita;
// ahora se arma una sola vez, con las clases que aparecen en las plantillas, el JavaScript y el código Python.
//
// Volver a generarlo (después de agregar clases de Tailwind nuevas), desde la raíz del proyecto:
//   npx tailwindcss@3.4.17 -c documentacion/herramientas/tailwind/tailwind.config.js \
//     -i documentacion/herramientas/tailwind/entrada.css -o usuarios/static/css/tailwind.min.css --minify
const path = require('path');
const raiz = path.join(__dirname, '..', '..', '..');
const apps = '{usuarios,pedidos,reportes,notificaciones,vehiculos,core}';
module.exports = {
  content: [
    path.join(raiz, apps, '**', 'templates', '**', '*.html'),
    path.join(raiz, apps, 'static', '**', '*.js'),
    path.join(raiz, apps, '**', '*.py'),
  ],
  theme: { extend: {} },
  plugins: [],
};
