// La campanita: al tocarla se despliegan los últimos avisos ahí mismo, sin salir de la pantalla.
// Cada aviso lleva a lo que avisa (y queda leído). Abajo, «Ver todas» y «Marcar todas como leídas».
// Con Ctrl o el botón del medio se sigue abriendo la bandeja completa, como un enlace común.
(function () {
  const estilo = document.createElement('style');
  estilo.textContent = `
    .cp-panel{position:fixed;z-index:1500;width:min(360px,calc(100vw - 1.5rem));background:#fff;border-radius:14px;
      box-shadow:0 18px 45px rgba(0,0,0,.2);border:1px solid #efe3d8;overflow:hidden;font-size:.9rem;color:#2b211a;
      animation:cp-baja .14s ease-out}
    @keyframes cp-baja{from{opacity:0;transform:translateY(-6px)}to{opacity:1;transform:none}}
    .cp-cabeza{display:flex;justify-content:space-between;align-items:baseline;padding:.8rem 1rem;
      background:linear-gradient(128deg,#FF8A00,#FF5E08 55%,#E10E0E);color:#fff}
    .cp-cabeza span{font-size:.8rem;opacity:.9}
    .cp-lista{list-style:none;margin:0;padding:.25rem 0;max-height:min(360px,60vh);overflow:auto}
    .cp-lista form{margin:0}
    .cp-aviso{all:unset;box-sizing:border-box;display:block;width:100%;padding:.6rem 1rem;cursor:pointer;border-bottom:1px solid #f4ece4}
    .cp-aviso:hover,.cp-aviso:focus-visible{background:#FFF6EE}
    .cp-aviso:focus-visible{outline:2px solid #FF7A00;outline-offset:-2px}
    .cp-tipo{display:flex;align-items:center;gap:.4rem;font-size:.75rem;color:#8a7a6d;margin-bottom:.15rem}
    .cp-punto{width:.5rem;height:.5rem;border-radius:50%;background:#E10E0E;flex:none}
    .cp-mensaje{display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden;line-height:1.35}
    .cp-sin-leer .cp-mensaje{font-weight:600}
    .cp-vacio{margin:0;padding:1.25rem 1rem;color:#7a6a5d;text-align:center}
    .cp-pie{display:flex;justify-content:space-between;align-items:center;gap:.5rem;padding:.6rem 1rem;background:#FBF7F3}
    .cp-pie a,.cp-pie button{all:unset;cursor:pointer;color:#C04F00;font-weight:600;font-size:.85rem}
    .cp-pie a:hover,.cp-pie button:hover{text-decoration:underline}
    .cp-cargando{padding:1.25rem;text-align:center;color:#7a6a5d}`;
  document.head.appendChild(estilo);

  let panel = null;
  let campana = null;

  function cerrar() {
    if (!panel) return;
    panel.remove();
    panel = null;
    if (campana) campana.setAttribute('aria-expanded', 'false');
  }

  function ubicar() {
    if (!panel || !campana) return;
    const r = campana.getBoundingClientRect();
    panel.style.top = `${r.bottom + 8}px`;
    const derecha = Math.max(12, window.innerWidth - r.right - 8);
    panel.style.right = `${derecha}px`;
  }

  async function abrir(link) {
    cerrar();
    campana = link;
    panel = document.createElement('div');
    panel.className = 'cp-panel';
    panel.setAttribute('role', 'dialog');
    panel.setAttribute('aria-label', 'Últimas notificaciones');
    panel.innerHTML = '<div class="cp-cargando">Cargando…</div>';
    document.body.append(panel);
    link.setAttribute('aria-expanded', 'true');
    ubicar();
    try {
      const volver = location.pathname + location.search;
      const r = await fetch(`/notificaciones/ultimas/?volver=${encodeURIComponent(volver)}`, { credentials: 'same-origin' });
      if (!r.ok) throw new Error(r.status);
      if (panel) panel.innerHTML = await r.text();
    } catch (e) {
      location.href = link.href;  // si algo falla, la bandeja completa
      return;
    }
    const primero = panel && panel.querySelector('.cp-aviso, .cp-pie a');
    if (primero) primero.focus();
  }

  document.addEventListener('click', (e) => {
    const link = e.target.closest && e.target.closest('a[data-campanita]');
    if (link) {
      if (e.ctrlKey || e.metaKey || e.shiftKey || e.button !== 0) return;
      e.preventDefault();
      if (panel && campana === link) cerrar();
      else abrir(link);
      return;
    }
    if (panel && !panel.contains(e.target)) cerrar();
  });
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape' && panel) { cerrar(); if (campana) campana.focus(); }
  });
  window.addEventListener('resize', ubicar);
  window.addEventListener('scroll', ubicar, true);
})();
