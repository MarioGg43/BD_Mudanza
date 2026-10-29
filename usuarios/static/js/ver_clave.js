// Botón con un ojo en todos los campos de clave para mostrar u ocultar lo escrito
// (idea del proyecto de José; acá se arma una sola vez para todo el sistema).
(function () {
  function agregar(campo) {
    if (campo.dataset.verClave) return;
    campo.dataset.verClave = '1';
    const envoltura = document.createElement('span');
    envoltura.style.position = 'relative';
    envoltura.style.display = 'block';
    campo.parentNode.insertBefore(envoltura, campo);
    envoltura.appendChild(campo);
    campo.style.paddingRight = '2.5rem';
    const boton = document.createElement('button');
    boton.type = 'button';
    boton.setAttribute('aria-label', 'Mostrar la clave');
    boton.title = 'Mostrar u ocultar la clave';
    boton.textContent = '👁';
    Object.assign(boton.style, {
      position: 'absolute', right: '.5rem', top: '50%', transform: 'translateY(-50%)', border: '0',
      background: 'transparent', cursor: 'pointer', fontSize: '1rem', lineHeight: '1', opacity: '.6', padding: '.25rem',
    });
    boton.addEventListener('click', () => {
      const mostrar = campo.type === 'password';
      campo.type = mostrar ? 'text' : 'password';
      boton.style.opacity = mostrar ? '1' : '.6';
      boton.setAttribute('aria-label', mostrar ? 'Ocultar la clave' : 'Mostrar la clave');
    });
    envoltura.appendChild(boton);
  }
  function revisar() { document.querySelectorAll('input[type="password"]').forEach(agregar); }
  document.addEventListener('DOMContentLoaded', revisar);
  revisar();
})();
