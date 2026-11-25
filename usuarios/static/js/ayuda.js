// La ayuda «?» al lado de las palabras del sistema («Vencido», «Relevamiento», «Ticket promedio»…):
// al tocarla aparece un globito que explica qué significa. En la computadora también al pasar el mouse.
// En el HTML: <button type="button" class="ayuda" data-ayuda="Explicación" aria-label="¿Qué es…?">?</button>
(function () {
  const estilo = document.createElement('style');
  estilo.textContent = `
    .ayuda{all:unset;box-sizing:border-box;display:inline-grid;place-items:center;width:1.15rem;height:1.15rem;margin-left:.3rem;
      border-radius:50%;background:#FFF0E2;color:#C04F00;border:1px solid #F3C9A5;font-size:.72rem;font-weight:700;
      cursor:help;vertical-align:.1em;line-height:1;text-transform:none;letter-spacing:0}
    .ayuda:hover,.ayuda[aria-expanded="true"]{background:#FF7A00;color:#fff;border-color:#FF7A00}
    .ayuda:focus-visible{outline:2px solid #FF7A00;outline-offset:2px}
    .ayuda-globo{position:fixed;z-index:1600;max-width:280px;padding:.6rem .75rem;border-radius:10px;background:#2b211a;color:#fff;
      font-size:.85rem;line-height:1.4;box-shadow:0 10px 25px rgba(0,0,0,.25);font-weight:400;text-transform:none;letter-spacing:0;
      animation:ay-aparece .12s ease-out;pointer-events:none}
    @keyframes ay-aparece{from{opacity:0;transform:translateY(3px)}to{opacity:1;transform:none}}`;
  document.head.appendChild(estilo);

  let globo = null;
  let dueno = null;
  let fijo = false;  // abierto con un clic (queda hasta otro clic); si no, se va al sacar el mouse

  function cerrar() {
    if (globo) globo.remove();
    if (dueno) dueno.setAttribute('aria-expanded', 'false');
    globo = null;
    dueno = null;
    fijo = false;
  }

  function abrir(b) {
    if (dueno === b) return;
    cerrar();
    dueno = b;
    globo = document.createElement('div');
    globo.className = 'ayuda-globo';
    globo.setAttribute('role', 'tooltip');
    globo.id = 'ayuda-globo';
    globo.textContent = b.dataset.ayuda;
    document.body.append(globo);
    b.setAttribute('aria-expanded', 'true');
    b.setAttribute('aria-describedby', 'ayuda-globo');
    const r = b.getBoundingClientRect();
    const g = globo.getBoundingClientRect();
    let left = Math.min(Math.max(8, r.left + r.width / 2 - g.width / 2), window.innerWidth - g.width - 8);
    let top = r.bottom + 8;
    if (top + g.height > window.innerHeight - 8) top = r.top - g.height - 8;  // si no entra abajo, va arriba
    globo.style.left = `${left}px`;
    globo.style.top = `${top}px`;
  }

  document.addEventListener('click', (e) => {
    const b = e.target.closest && e.target.closest('.ayuda[data-ayuda]');
    if (b) {
      e.preventDefault();
      e.stopPropagation();  // dentro de un título que ordena la tabla, no la ordena
      if (dueno === b && fijo) cerrar();
      else { abrir(b); fijo = true; }
      return;
    }
    cerrar();
  }, true);
  document.addEventListener('mouseover', (e) => {
    const b = e.target.closest && e.target.closest('.ayuda[data-ayuda]');
    if (b && matchMedia('(hover: hover)').matches) abrir(b);
  });
  document.addEventListener('mouseout', (e) => {
    const b = e.target.closest && e.target.closest('.ayuda[data-ayuda]');
    if (b && b === dueno && !fijo && !b.contains(e.relatedTarget)) cerrar();
  });
  document.addEventListener('keydown', (e) => { if (e.key === 'Escape') cerrar(); });
  window.addEventListener('scroll', cerrar, true);
  window.addEventListener('resize', cerrar);
})();
