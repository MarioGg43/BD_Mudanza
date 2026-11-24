// Validación mientras se escribe, para todos los formularios del sistema.
// - Lo que no va directamente no se puede escribir (una letra en el DNI, un número en el nombre).
// - Debajo del campo aparece un cartel que dice qué está mal y cómo arreglarlo; cuando está bien, se va.
// - El formulario no se envía mientras haya errores, y te lleva al primero.
// Las mismas reglas están en el servidor (usuarios/validaciones.py), por si alguien se lo saltea.
// Cada campo dice su regla con data-validar="..."; si no la dice, se deduce por su nombre o tipo.
(function () {
  const LETRA = 'A-Za-zÁÉÍÓÚÜÑáéíóúüñ';
  const PERSONA = new RegExp(`^[${LETRA}]+(?:[ '\\-][${LETRA}]+)*$`);
  const NO_PERSONA = new RegExp(`[^${LETRA} '\\-]`, 'g');
  const CORREO = /^[^\s@]+@[^\s@]+\.[a-z]{2,}$/i;
  const PATENTE = /^(?:[A-Z]{2}-?\d{3}-?[A-Z]{2}|[A-Z]{3}-?\d{3})$/;
  const letras = (t) => (t.match(new RegExp(`[${LETRA}]`, 'g')) || []).length;
  const repite = (t, veces) => new RegExp(`([${LETRA}])\\1{${veces - 1},}`, 'i').test(t);
  const miles = (n) => Number(n).toLocaleString('es-AR');

  // ---- estilos (sirven igual en las pantallas con Bootstrap y en las de Tailwind) ----
  const estilo = document.createElement('style');
  estilo.textContent = `
    .v-burbuja{position:relative;margin-top:7px;padding:6px 10px;border-radius:8px;font-size:.8rem;line-height:1.35;
      background:#FEF0EF;color:#B42318;border:1px solid #F4B4AE;font-weight:500;text-align:left}
    .v-burbuja::before,.v-burbuja::after{content:'';position:absolute;left:14px;border:6px solid transparent;border-top:0}
    .v-burbuja::before{top:-6px;border-bottom-color:#F4B4AE}
    .v-burbuja::after{top:-5px;border-bottom-color:#FEF0EF}
    .v-burbuja.v-aviso{background:#FFF6E5;color:#93530B;border-color:#F7CF8D}
    .v-burbuja.v-aviso::before{border-bottom-color:#F7CF8D}.v-burbuja.v-aviso::after{border-bottom-color:#FFF6E5}
    .v-burbuja[hidden]{display:none}
    .v-mal{border-color:#D92D20!important;box-shadow:0 0 0 3px rgba(217,45,32,.14)!important}
    .v-bien{border-color:#12B76A!important}`;
  document.head.appendChild(estilo);

  // ---- qué regla tiene cada campo ----
  const POR_NOMBRE = {
    dni: 'dni', altadni: 'dni', olvidodni: 'dni',
    telefono: 'telefono',
    nueva_clave: 'clave-nueva', nueva: 'clave-nueva', altaclave: 'clave-nueva', olvidonueva: 'clave-nueva',
    restablecernuevaclave: 'clave-nueva',
    confirmar_clave: 'repetir', confirmar: 'repetir', clave2: 'repetir', olvidoconfirmar: 'repetir',
    altaapellido: 'persona', altanombre: 'persona',
    patente: 'patente',
    marca_modelo: 'nombre-cosa', nom_objeto: 'nombre-cosa', nom_material: 'nombre-cosa', tipo_servicio: 'nombre-cosa',
    unidad_material: 'nombre-cosa',
    motivo: 'texto', observacion: 'texto', observaciones: 'texto', detalleobjeto: 'texto', queesotro: 'nombre-cosa',
  };
  const PAREJA = { confirmar_clave: 'nueva_clave', confirmar: 'nueva', clave2: 'clave', olvidoconfirmar: 'olvidoNueva' };

  function clave(c) { return (c.name || c.id || '').toLowerCase(); }

  function regla(c) {
    if (c.dataset.validar) return c.dataset.validar;
    if (c.type === 'hidden' || c.type === 'checkbox' || c.type === 'radio' || c.type === 'submit') return '';
    let k = clave(c);
    const id = (c.id || '').toLowerCase();
    if (POR_NOMBRE[id]) k = id;
    if (/-observacion$/.test(k)) return 'texto';
    if ((k === 'apellido' || k === 'nombre') && c.form && c.form.querySelector('[name="dni"]')) return 'persona';
    if (k === 'nombre' && c.form && c.form.querySelector('[name="permisos"]')) return 'nombre-cosa';
    if (k === 'descripcion' && c.form && c.form.querySelector('[name="permisos"]')) return 'texto';
    if (POR_NOMBRE[k]) return POR_NOMBRE[k];
    if (c.type === 'email') return 'correo';
    if (c.type === 'number') return 'numero';
    return '';
  }

  function que(c) {
    if (c.dataset.que) return c.dataset.que;
    return /apellido/i.test(c.name || c.id) ? 'apellido' : 'nombre';
  }

  function pareja(c) {
    const ref = c.dataset.igualA || PAREJA[clave(c)] || PAREJA[(c.id || '').toLowerCase()];
    if (!ref) return null;
    return document.getElementById(ref) || (c.form && c.form.querySelector(`[name="${ref}"]`));
  }

  // ---- lo que no se puede escribir: se saca en el momento y se avisa ----
  function limpiar(c) {
    const r = regla(c);
    const antes = c.value;
    let v = antes;
    let aviso = '';
    if (r === 'codigo') {
      v = v.replace(/\D/g, '').slice(0, 6);
      if (v !== antes) aviso = 'El código lleva solo números.';
    } else if (r === 'dni') {
      v = v.replace(/\D/g, '');
      if (v !== antes) aviso = 'El DNI lleva solo números, sin puntos ni espacios.';
      if (v.length > 8) { v = v.slice(0, 8); aviso = 'El DNI tiene como máximo 8 números.'; }
    } else if (r === 'persona') {
      v = v.replace(NO_PERSONA, '').replace(/ {2,}/g, ' ').replace(/^[ '\-]+/, '');
      if (v !== antes) aviso = `El ${que(c)} lleva solo letras (puede tener espacios, apóstrofo o guion).`;
    } else if (r === 'telefono') {
      if (c._pais && v.trim().startsWith('+')) { separarCodigo(c); return ''; }
      v = v.replace(/[^\d +\-]/g, '').replace(/(?!^)\+/g, '');
      if (v !== antes) aviso = 'El teléfono lleva solo números, espacios o guiones (y un + al principio).';
    } else if (r === 'correo') {
      v = v.replace(/\s/g, '');
      if (v !== antes) aviso = 'El correo no lleva espacios.';
    } else if (r === 'patente') {
      v = v.toUpperCase().replace(/[^A-Z0-9\- ]/g, '');
      if (v.toUpperCase() !== antes.toUpperCase()) aviso = 'La patente lleva solo letras y números.';
    }
    if (v !== antes) {
      const pos = c.selectionStart - (antes.length - v.length);
      c.value = v;
      try { c.setSelectionRange(pos, pos); } catch (e) { /* algunos tipos no lo permiten */ }
    }
    return aviso;
  }

  // nombre y apellido: cada palabra empieza con mayúscula mientras se escribe («maría» → «María»),
  // salvo «de», «del», «la», «las», «los» e «y» en el medio («María de la Paz»)
  function mayusculaInicial(c) {
    const v = c.value;
    const nuevo = v.replace(new RegExp(`(^|[ '\\-])([${LETRA}]+)`, 'g'), (m, sep, palabra, pos) => {
      const resto = v.slice(pos + m.length);
      const enMedio = pos > 0 && /^(de|del|la|las|los|y)$/i.test(palabra) && resto.startsWith(' ');
      return sep + (enMedio ? palabra.toLowerCase() : palabra[0].toUpperCase() + palabra.slice(1));
    });
    if (nuevo !== v) {
      const inicio = c.selectionStart;
      const fin = c.selectionEnd;
      c.value = nuevo;
      try { c.setSelectionRange(inicio, fin); } catch (e) { /* algunos tipos no lo permiten */ }
    }
  }

  // en los campos numéricos el navegador deja escribir «e», «+», «-» y comas: se frenan antes
  function teclaNumero(e) {
    const c = e.target;
    if (!(c instanceof HTMLInputElement) || regla(c) !== 'numero' || !e.data) return;
    const sinNegativos = c.min !== '' && Number(c.min) >= 0;
    const entero = !c.step || c.step === '1';
    for (const ch of e.data) {
      if (/\d/.test(ch)) continue;
      if (ch === '-' && !sinNegativos) continue;
      if ((ch === '.' || ch === ',') && !entero) continue;
      e.preventDefault();
      mostrar(c, sinNegativos && ch === '-' ? 'Tiene que ser un número de 0 en adelante.'
        : entero ? 'Escribí solo números enteros.' : 'Escribí solo números.', true);
      return;
    }
  }

  // ---- qué está mal ----
  function problema(c) {
    if (c.disabled || c.closest('[hidden]') || (c.type !== 'hidden' && c.offsetParent === null && c.type !== 'radio')) return '';
    const r = regla(c);
    const v = (c.value || '').trim();
    if (c.type === 'radio') {
      if (!c.required || !c.form) return '';
      const grupo = c.form.querySelectorAll(`input[type="radio"][name="${c.name}"]`);
      return [...grupo].some((x) => x.checked) ? '' : 'Elegí una opción.';
    }
    if (!v) {
      if (r === 'repetir' && pareja(c) && pareja(c).value) return 'Repetí la clave.';
      if (c.required) return c.tagName === 'SELECT' ? 'Elegí una opción.' : 'Completá este campo.';
      return '';
    }
    switch (r) {
      case 'dni':
        if (!/^\d+$/.test(v)) return 'El DNI lleva solo números, sin puntos ni espacios.';
        if (v.replace(/^0+/, '').length < 7 || v.length > 8) return 'El DNI tiene 7 u 8 números.';
        break;
      case 'persona': {
        const q = que(c);
        const t = v.replace(/\s+/g, ' ');
        if (!PERSONA.test(t)) return `El ${q} lleva solo letras (puede tener espacios, apóstrofo o guion).`;
        if (letras(t) < 2) return `El ${q} tiene que tener al menos 2 letras.`;
        if (t.length > 50) return `El ${q} puede tener hasta 50 caracteres.`;
        if (repite(t, 3) || !/[aeiouáéíóúü]/i.test(t)) return `Revisá el ${q}: no parece un ${q} real.`;
        break;
      }
      case 'telefono': {
        const n = (v.match(/\d/g) || []).length;
        if (c._pais) {
          const [, nombre, codigo, min, max, ayuda] = c._pais;
          if (!/^[\d \-]+$/.test(v)) return 'El teléfono lleva solo números, espacios o guiones.';
          if (n < min || n > max) {
            return ayuda ? `Escribí el ${ayuda}: son ${min} números.`
              : `Para ${nombre} el número tiene ${min === max ? min : `${min} a ${max}`} números, sin el ${codigo}.`;
          }
          break;
        }
        if (!/^\+?[\d \-]+$/.test(v)) return 'El teléfono lleva solo números, espacios o guiones (y un + al principio).';
        if (n < 10 || n > 13) return 'Escribí el teléfono con código de área: 10 números, por ejemplo 387 4112233.';
        break;
      }
      case 'codigo':
        if (!/^\d{6}$/.test(v)) return 'El código tiene 6 números.';
        break;
      case 'correo':
        if (!CORREO.test(v)) return 'Escribí un correo válido, por ejemplo nombre@gmail.com.';
        break;
      case 'clave-nueva': {
        const falta = [];
        if (v.length < 8) falta.push('8 caracteres');
        if (!/[A-Z]/.test(v)) falta.push('una mayúscula');
        if (!/[a-z]/.test(v)) falta.push('una minúscula');
        if (!/\d/.test(v)) falta.push('un número');
        if (!/[^A-Za-z0-9]/.test(v)) falta.push('un carácter especial (!@#$%&*-_)');
        if (falta.length) return 'A la clave le falta: ' + falta.join(', ') + '.';
        break;
      }
      case 'repetir': {
        const p = pareja(c);
        if (p && p.value !== c.value) return 'Las claves no coinciden.';
        break;
      }
      case 'patente':
        if (!PATENTE.test(v.toUpperCase().replace(/ /g, ''))) return 'La patente es como AB123CD o ABC123.';
        break;
      case 'nombre-cosa': {
        const minimo = Number(c.dataset.minLetras || 2);
        if (letras(v) < minimo) return `Tiene que tener al menos ${minimo} letras.`;
        if (repite(v, 4)) return 'Revisá: tiene una letra repetida muchas veces.';
        break;
      }
      case 'texto':
        if (letras(v) < 3 || repite(v, 4)) return 'Escribilo con palabras (al menos 3 letras).';
        break;
      case 'numero': {
        if (c.validity && c.validity.badInput) return 'Escribí solo números.';
        const n = Number(v.replace(',', '.'));
        if (Number.isNaN(n)) return 'Escribí solo números.';
        const min = c.min !== '' ? Number(c.min) : null;
        const max = c.max !== '' ? Number(c.max) : null;
        if (min !== null && max !== null && (n < min || n > max)) return `Tiene que ser de ${miles(min)} a ${miles(max)}.`;
        if (min !== null && n < min) return `Tiene que ser ${miles(min)} o más.`;
        if (max !== null && n > max) return `Tiene que ser ${miles(max)} o menos.`;
        if ((!c.step || c.step === '1') && !Number.isInteger(n)) return 'Escribí un número entero.';
        break;
      }
    }
    const minimo = Number(c.getAttribute('minlength') || 0);
    if (minimo && v.length < minimo) return `Escribí al menos ${minimo} caracteres.`;
    const maximo = Number(c.getAttribute('maxlength') || 0);
    if (maximo && v.length > maximo) return `Puede tener hasta ${maximo} caracteres.`;
    return '';
  }

  // ---- el cartel ----
  function ancla(c) {
    if (c.type === 'radio' && c.form) {
      const grupo = c.form.querySelectorAll(`input[type="radio"][name="${c.name}"]`);
      const ultimo = grupo[grupo.length - 1];
      return ultimo.closest('.form-check') || ultimo.parentElement;
    }
    const padre = c.parentElement;
    if (padre && (padre.classList.contains('input-group') || padre.classList.contains('v-tel') || padre.dataset.verClaveEnvoltura !== undefined
        || (padre.tagName === 'SPAN' && padre.style.position === 'relative'))) return padre;
    return c;
  }

  function burbuja(c) {
    const a = ancla(c);
    let b = a.nextElementSibling;
    if (!b || !b.classList.contains('v-burbuja')) {
      b = document.createElement('div');
      b.className = 'v-burbuja';
      b.setAttribute('role', 'alert');
      b.hidden = true;
      a.insertAdjacentElement('afterend', b);
    }
    return b;
  }

  function mostrar(c, mensaje, temporal) {
    const b = burbuja(c);
    clearTimeout(b._t);
    if (!mensaje) {
      b.hidden = true;
      c.classList.remove('v-mal');
      if ((c.value || '').trim() && regla(c)) c.classList.add('v-bien');
      else c.classList.remove('v-bien');
      c.removeAttribute('aria-invalid');
      return;
    }
    b.textContent = mensaje;
    b.classList.toggle('v-aviso', !!temporal);
    b.hidden = false;
    if (temporal) {
      b._t = setTimeout(() => revisar(c), 2600);
    } else {
      c.classList.add('v-mal');
      c.classList.remove('v-bien');
      c.setAttribute('aria-invalid', 'true');
    }
  }

  // el error que mandó el servidor se esconde cuando la persona empieza a corregir ese campo
  function ocultarErrorDelServidor(c) {
    c.classList.remove('is-invalid');
    const caja = c.closest('.col-md-6, .col-md-4, .col-md-3, .col-12, .mb-3, .col, div');
    if (caja) caja.querySelectorAll('.invalid-feedback, .errorlist').forEach((e) => { e.style.display = 'none'; });
  }

  function revisar(c) {
    mostrar(c, problema(c));
  }

  function campos(form) {
    return [...form.querySelectorAll('input, select, textarea')].filter((c) => c.type !== 'hidden' && c.type !== 'submit' && c.type !== 'button');
  }

  // lo que se escribe o se pega: se frena antes de entrar y solo se deja pasar lo que va
  const PERMITIDO = {
    dni: /\d/, codigo: /\d/, telefono: /[\d +\-]/, persona: new RegExp(`[${LETRA} '\\-]`), patente: /[A-Za-z0-9\- ]/, correo: /\S/,
  };
  function teclaTexto(e) {
    const c = e.target;
    if (!(c instanceof HTMLInputElement) || !e.data || !/^insert/.test(e.inputType)) return;
    const r = regla(c);
    const ok = PERMITIDO[r];
    if (!ok) return;
    let filtrado = [...e.data].filter((ch) => ok.test(ch)).join('');
    if (r === 'telefono' && !e.data.trim().startsWith('+') && (c.selectionStart > 0 || c.value.includes('+'))) filtrado = filtrado.replace(/\+/g, '');
    if (r === 'patente') filtrado = filtrado.toUpperCase();
    const maximo = Number(c.getAttribute('maxlength') || 0);
    const libre = maximo ? maximo - (c.value.length - (c.selectionEnd - c.selectionStart)) : Infinity;
    if (filtrado.length > libre) filtrado = filtrado.slice(0, Math.max(libre, 0));
    if (filtrado === e.data) return;
    e.preventDefault();
    if (filtrado) {
      c.setRangeText(filtrado, c.selectionStart, c.selectionEnd, 'end');
      c.dispatchEvent(new Event('input', { bubbles: true }));
    }
    const avisos = {
      dni: filtrado.length < [...e.data].filter((ch) => /\d/.test(ch)).length
        ? 'El DNI tiene como máximo 8 números.' : 'El DNI lleva solo números, sin puntos ni espacios.',
      codigo: 'El código lleva solo números.',
      telefono: 'El teléfono lleva solo números, espacios o guiones (y un + al principio).',
      persona: `El ${que(c)} lleva solo letras (puede tener espacios, apóstrofo o guion).`,
      patente: 'La patente lleva solo letras y números.',
      correo: 'El correo no lleva espacios.',
    };
    mostrar(c, avisos[r], true);
  }

  // ---- eventos (en el documento, así sirven también para los campos que se agregan después) ----
  document.addEventListener('beforeinput', teclaNumero, true);
  document.addEventListener('beforeinput', teclaTexto, true);

  document.addEventListener('input', (e) => {
    const c = e.target;
    if (!(c instanceof HTMLInputElement || c instanceof HTMLTextAreaElement)) return;
    if (c.type === 'checkbox' || c.type === 'radio') return;
    ocultarErrorDelServidor(c);
    c.dataset.vTocado = '1';
    const aviso = limpiar(c);
    if (regla(c) === 'persona') mayusculaInicial(c);
    if (aviso) mostrar(c, aviso, true);
    else revisar(c);
    // si cambia la clave, la repetida se vuelve a revisar
    if (regla(c) === 'clave-nueva' && c.form) {
      c.form.querySelectorAll('input').forEach((o) => { if (regla(o) === 'repetir' && pareja(o) === c && o.value) revisar(o); });
    }
  }, true);

  document.addEventListener('change', (e) => {
    const c = e.target;
    if (c instanceof HTMLSelectElement || (c instanceof HTMLInputElement && c.type === 'radio')) {
      ocultarErrorDelServidor(c);
      revisar(c);
    }
  }, true);

  document.addEventListener('focusout', (e) => {
    const c = e.target;
    if (!(c instanceof HTMLInputElement || c instanceof HTMLTextAreaElement || c instanceof HTMLSelectElement)) return;
    if (c.type === 'checkbox' || c.type === 'radio' || c.readOnly) return;
    // al salir del campo se deja prolijo: sin espacios de más y los nombres con mayúscula
    if (c.tagName !== 'SELECT' && c.type !== 'password' && c.value !== c.value.trim()) c.value = c.value.replace(/\s+/g, ' ').trim();
    if (regla(c) === 'persona' && c.value) {
      c.value = c.value.split(' ').map((p, i) => (i && /^(de|del|la|las|los|y)$/i.test(p) ? p.toLowerCase()
        : p.toLowerCase().replace(new RegExp(`(^|['\\-])([${LETRA}])`, 'g'), (m, a, b) => a + b.toUpperCase()))).join(' ');
    }
    if (regla(c) === 'correo') c.value = c.value.toLowerCase();
    if (c.dataset.vTocado || c.value) revisar(c);
  }, true);

  // al enviar: si algo está mal, no se envía y se va al primer error
  document.addEventListener('submit', (e) => {
    const form = e.target;
    if (!(form instanceof HTMLFormElement) || form.dataset.sinValidar !== undefined) return;
    let primero = null;
    for (const c of campos(form)) {
      const m = problema(c);
      if (m) {
        mostrar(c, m);
        if (!primero) primero = c;
      }
    }
    if (primero) {
      e.preventDefault();
      e.stopImmediatePropagation();
      primero.scrollIntoView({ behavior: 'smooth', block: 'center' });
      primero.focus({ preventScroll: true });
    }
  }, true);

  // ---- teléfono con selector de país: bandera, código (+54) y una flecha para elegir otro ----
  // En el campo se escribe el número sin el código; al enviar se guarda «+54 387 4112233».
  const PAISES = [
    ['ar', 'Argentina', '+54', 10, 10, 'código de área y número, sin el 0 ni el 15 (ej. 387 4112233)'],
    ['bo', 'Bolivia', '+591', 8, 8], ['br', 'Brasil', '+55', 10, 11], ['cl', 'Chile', '+56', 9, 9],
    ['co', 'Colombia', '+57', 10, 10], ['es', 'España', '+34', 9, 9], ['us', 'Estados Unidos', '+1', 10, 10],
    ['it', 'Italia', '+39', 9, 11], ['mx', 'México', '+52', 10, 10], ['py', 'Paraguay', '+595', 9, 9],
    ['pe', 'Perú', '+51', 9, 9], ['uy', 'Uruguay', '+598', 8, 8],
  ];
  const estiloTel = document.createElement('style');
  estiloTel.textContent = `
    .v-tel{display:flex;align-items:stretch;position:relative}
    .v-tel>input{flex:1;min-width:0;border-top-left-radius:0!important;border-bottom-left-radius:0!important}
    .v-tel-boton{display:flex;align-items:center;gap:6px;padding:0 10px;border:1px solid #d6d0c8;border-right:0;
      border-radius:.5rem 0 0 .5rem;background:#fff;cursor:pointer;font:inherit;font-size:.9rem;color:#3b322b;white-space:nowrap}
    .v-tel-boton:focus{outline:2px solid #FF7A00;outline-offset:-2px}
    .v-tel-bandera{width:22px;height:16px;object-fit:cover;border-radius:2px;box-shadow:0 0 0 1px rgba(0,0,0,.12)}
    .v-tel-sigla{font-size:.7rem;font-weight:700;background:#eee;border-radius:3px;padding:1px 4px}
    .v-tel-flecha{font-size:.7rem;opacity:.6}
    .v-tel-lista{position:absolute;z-index:1060;top:calc(100% + 4px);left:0;width:260px;max-height:260px;overflow:auto;
      background:#fff;border:1px solid #d6d0c8;border-radius:10px;box-shadow:0 10px 30px rgba(0,0,0,.15);padding:4px;margin:0;list-style:none}
    .v-tel-lista li{display:flex;align-items:center;gap:8px;padding:7px 9px;border-radius:7px;cursor:pointer;font-size:.9rem}
    .v-tel-lista li:hover,.v-tel-lista li[aria-selected="true"]{background:#FFF0E2}
    .v-tel-lista .v-tel-codigo{margin-left:auto;color:#7a6f66;font-variant-numeric:tabular-nums}`;
  document.head.appendChild(estiloTel);

  function bandera(codigo) {
    const img = document.createElement('img');
    img.className = 'v-tel-bandera';
    img.alt = '';
    img.src = `https://flagcdn.com/w40/${codigo}.png`;
    img.onerror = () => {  // sin internet: la sigla del país en lugar de la bandera
      const s = document.createElement('span');
      s.className = 'v-tel-sigla';
      s.textContent = codigo.toUpperCase();
      img.replaceWith(s);
    };
    return img;
  }

  function elegirPais(c, pais) {
    c._pais = pais;
    const boton = c._botonPais;
    boton.replaceChildren(bandera(pais[0]), document.createTextNode(pais[2]));
    const flecha = document.createElement('span');
    flecha.className = 'v-tel-flecha';
    flecha.textContent = '▼';
    boton.append(flecha);
    boton.setAttribute('aria-label', `País del teléfono: ${pais[1]} (${pais[2]}). Cambiar`);
    c.placeholder = pais[0] === 'ar' ? 'Ej. 387 4112233' : 'Número sin el código del país';
    if (c.value) revisar(c);
  }

  function separarCodigo(c) {
    // «+54 387 4112233» → Argentina y «387 4112233» (al cargar la página o si alguien lo pega con el código)
    const v = c.value.trim();
    if (!v.startsWith('+')) return;
    const pais = [...PAISES].sort((a, b) => b[2].length - a[2].length).find((p) => v.replace(/\s/g, '').startsWith(p[2]));
    if (!pais) return;
    elegirPais(c, pais);
    c.value = v.slice(v.indexOf(pais[2]) + pais[2].length).replace(/^[\s\-]+/, '').replace(/^9\s?(?=\d{10}$)/, '');
  }

  function prepararTelefono(c) {
    if (c._botonPais || c.closest('.v-tel')) return;
    const caja = document.createElement('div');
    caja.className = 'v-tel';
    c.parentNode.insertBefore(caja, c);
    const boton = document.createElement('button');
    boton.type = 'button';
    boton.className = 'v-tel-boton';
    boton.setAttribute('aria-haspopup', 'listbox');
    caja.append(boton, c);
    c._botonPais = boton;
    elegirPais(c, PAISES[0]);
    separarCodigo(c);
    boton.addEventListener('click', () => {
      const abierta = caja.querySelector('.v-tel-lista');
      if (abierta) { abierta.remove(); return; }
      const lista = document.createElement('ul');
      lista.className = 'v-tel-lista';
      lista.setAttribute('role', 'listbox');
      PAISES.forEach((p) => {
        const li = document.createElement('li');
        li.setAttribute('role', 'option');
        li.tabIndex = 0;
        li.setAttribute('aria-selected', p === c._pais ? 'true' : 'false');
        const nombre = document.createElement('span');
        nombre.textContent = p[1];
        const codigo = document.createElement('span');
        codigo.className = 'v-tel-codigo';
        codigo.textContent = p[2];
        li.append(bandera(p[0]), nombre, codigo);
        const elegir = () => { elegirPais(c, p); lista.remove(); c.focus(); };
        li.addEventListener('click', elegir);
        li.addEventListener('keydown', (e) => {
          if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); elegir(); }
          if (e.key === 'Escape') { lista.remove(); boton.focus(); }
          if (e.key === 'ArrowDown') { e.preventDefault(); (li.nextElementSibling || li).focus(); }
          if (e.key === 'ArrowUp') { e.preventDefault(); (li.previousElementSibling || li).focus(); }
        });
        lista.append(li);
      });
      caja.append(lista);
      (lista.querySelector('[aria-selected="true"]') || lista.firstChild).focus();
    });
    document.addEventListener('click', (e) => {
      if (!caja.contains(e.target)) caja.querySelector('.v-tel-lista')?.remove();
    });
  }

  // al enviar, el número se guarda con el código del país
  document.addEventListener('submit', (e) => {
    if (e.defaultPrevented) return;
    e.target.querySelectorAll?.('input').forEach((c) => {
      if (c._pais && c.value.trim() && !c.value.trim().startsWith('+')) c.value = `${c._pais[2]} ${c.value.trim()}`;
    });
  });

  // largos máximos y teclados del celular para los campos que se conocen
  function preparar() {
    document.querySelectorAll('input').forEach((c) => { if (regla(c) === 'telefono') prepararTelefono(c); });
    const largos = { dni: 8, telefono: 20, persona: 50, correo: 150, patente: 9 };
    document.querySelectorAll('input, textarea').forEach((c) => {
      const r = regla(c);
      if (largos[r] && !c.getAttribute('maxlength')) c.setAttribute('maxlength', largos[r]);
      if (r === 'dni') { c.setAttribute('inputmode', 'numeric'); if (c.type === 'number') c.type = 'text'; }
      if (r === 'telefono') c.setAttribute('inputmode', 'tel');
      if (r === 'clave-nueva' || r === 'repetir') c.setAttribute('autocomplete', 'new-password');
    });
    // los mensajes los da este archivo, no los globitos del navegador (que salen recién al enviar)
    document.querySelectorAll('form').forEach((f) => { if (f.dataset.sinValidar === undefined) f.noValidate = true; });
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', preparar);
  else preparar();
})();
