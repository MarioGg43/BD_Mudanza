// Ordenar las tablas tocando el título de la columna: un toque ordena, otro lo da vuelta.
// La flecha marca el sentido (▲ de menor a mayor, ▼ de mayor a menor).
// - <table data-ordenable>: se ordena en la pantalla (listas que se ven enteras).
// - <table data-ordenable="servidor">: las listas que van por páginas (Pedidos) se ordenan en el
//   servidor, así el orden vale para todas las páginas; cada título dice su campo con data-orden="...".
// La fila de totales (tfoot) queda siempre al final. Las columnas sin título (botones) no se ordenan.
(function () {
  const estilo = document.createElement('style');
  estilo.textContent = `
    .orden-btn{all:unset;cursor:pointer;display:inline-flex;align-items:center;gap:4px;white-space:nowrap;font:inherit;color:inherit}
    .orden-btn:hover{color:#C04F00}
    .orden-btn:focus-visible{outline:2px solid #FF7A00;outline-offset:2px;border-radius:3px}
    .orden-flecha{font-size:.75em;opacity:.35}
    th[aria-sort="ascending"] .orden-flecha, th[aria-sort="descending"] .orden-flecha{opacity:1;color:#C04F00}
    .text-end .orden-btn, .text-right .orden-btn{justify-content:flex-end}`;
  document.head.appendChild(estilo);

  // «1.342,0 h», «-6,7 %», «$75.000,00», «16 min» → número; «19/11/2026 16:00» → fecha; si no, texto
  function valor(celda) {
    const t = (celda.dataset.orden ?? celda.innerText).trim();
    if (!t || t === '—' || t === '-') return null;
    const f = t.match(/^(\d{2})\/(\d{2})\/(\d{4})(?:\D+(\d{2}):(\d{2}))?/);
    if (f) return new Date(+f[3], +f[2] - 1, +f[1], +(f[4] || 0), +(f[5] || 0)).getTime();
    const n = t.replace(/^\$\s?/, '').match(/^-?[\d.]+(,\d+)?(?=\s|%|$|[a-zA-Z³×])/);
    if (n) return Number(n[0].replace(/\./g, '').replace(',', '.'));
    return t.toLocaleLowerCase('es');
  }

  function comparar(a, b, sentido) {
    if (a === null && b === null) return 0;
    if (a === null) return 1;   // los vacíos van siempre al final
    if (b === null) return -1;
    const r = typeof a === 'number' && typeof b === 'number' ? a - b : String(a).localeCompare(String(b), 'es', { numeric: true });
    return r * sentido;
  }

  function flecha(th, sentido) {
    th.setAttribute('aria-sort', sentido === 1 ? 'ascending' : sentido === -1 ? 'descending' : 'none');
    th.querySelector('.orden-flecha').textContent = sentido === 1 ? '▲' : sentido === -1 ? '▼' : '↕';
  }

  function preparar(tabla) {
    if (tabla.dataset.ordenPreparada) return;
    tabla.dataset.ordenPreparada = '1';
    const enServidor = tabla.dataset.ordenable === 'servidor';
    const titulos = [...tabla.querySelectorAll('thead tr:last-child th')];
    const actual = new URLSearchParams(location.search).get('orden') || '';
    titulos.forEach((th, col) => {
      const texto = th.innerText.trim();
      if (!texto || th.dataset.sinOrden !== undefined || /^acciones$/i.test(texto)) return;
      if (enServidor && !th.dataset.orden) return;
      const boton = document.createElement('button');
      boton.type = 'button';
      boton.className = 'orden-btn';
      boton.title = `Ordenar por ${texto.toLowerCase()}`;
      // el «?» de ayuda queda afuera del botón de ordenar (un botón no va adentro de otro)
      const ayudas = [...th.querySelectorAll('.ayuda')];
      ayudas.forEach((a) => a.remove());
      boton.append(...th.childNodes);
      const f = document.createElement('span');
      f.className = 'orden-flecha';
      f.setAttribute('aria-hidden', 'true');
      boton.append(f);
      th.append(boton, ...ayudas);
      if (enServidor) {
        const campo = th.dataset.orden;
        flecha(th, actual === campo ? 1 : actual === `-${campo}` ? -1 : 0);
        boton.addEventListener('click', () => {
          const url = new URL(location.href);
          // el primer toque ordena de mayor a menor (lo más nuevo, lo más caro); el segundo, al revés
          url.searchParams.set('orden', actual === `-${campo}` ? campo : `-${campo}`);
          url.searchParams.delete('pagina');
          location.href = url.pathname + url.search;
        });
        return;
      }
      flecha(th, 0);
      boton.addEventListener('click', () => {
        const cuerpo = tabla.tBodies[0];
        const filas = [...cuerpo.rows].filter((r) => r.cells.length > col);
        const numerica = filas.some((r) => typeof valor(r.cells[col]) === 'number');
        const antes = th.getAttribute('aria-sort');
        // primer toque: los números de mayor a menor y los textos de la A a la Z
        const sentido = antes === 'none' ? (numerica ? -1 : 1) : antes === 'ascending' ? -1 : 1;
        titulos.forEach((otro) => { if (otro !== th && otro.querySelector('.orden-flecha')) flecha(otro, 0); });
        flecha(th, sentido);
        filas.map((r) => [r, valor(r.cells[col])])
          .sort((a, b) => comparar(a[1], b[1], sentido))
          .forEach(([r]) => cuerpo.appendChild(r));
      });
    });
  }

  function todas() { document.querySelectorAll('table[data-ordenable]').forEach(preparar); }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', todas);
  else todas();
})();
