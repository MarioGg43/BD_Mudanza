import { useEffect, useRef, useState } from 'react';
import flatpickr from 'flatpickr';
import { Spanish } from 'flatpickr/dist/l10n/es';
import 'flatpickr/dist/flatpickr.min.css';

/* Fecha y hora del pedido, como en las pantallas de Django (usuarios/static/js/fecha_hora.js):
   - la fecha con un calendario en castellano que no deja elegir días pasados ni más de un año;
   - la hora en una lista cada 15 minutos; si el día es hoy, las horas que ya pasaron quedan apagadas.
   El servidor revisa lo mismo (reglas._validar_fecha y _validar_hora): esto solo evita el error. */

const dos = (n) => String(n).padStart(2, '0');
export const hoyISO = () => { const d = new Date(); return `${d.getFullYear()}-${dos(d.getMonth() + 1)}-${dos(d.getDate())}`; };
const enUnAnio = () => { const d = new Date(); d.setDate(d.getDate() + 365); return `${d.getFullYear()}-${dos(d.getMonth() + 1)}-${dos(d.getDate())}`; };
const HORAS = Array.from({ length: 24 * 4 }, (_, i) => `${dos(Math.floor(i / 4))}:${dos((i % 4) * 15)}`);

// El calendario lindo en castellano. Flatpickr tampoco es de React: se arma una vez y se destruye al salir.
export function Calendario({ id, name, value, onChange, error, sinLimites, corto, placeholder = 'Elegí el día', minDate, className = '' }) {
  const input = useRef(null);
  const fp = useRef(null);
  // Flatpickr se arma una sola vez: con esto siempre llama a la versión actual de onChange
  const alCambiar = useRef(onChange);
  alCambiar.current = onChange;
  useEffect(() => {
    fp.current = flatpickr(input.current, {
      locale: Spanish,
      dateFormat: 'Y-m-d',            // lo que se manda al servidor
      altInput: true,
      // lo que ve la persona: «martes 17 de noviembre de 2026»; en los filtros, corta: «17/11/2026»
      altFormat: corto ? 'd/m/Y' : 'l j \\de F \\de Y',
      altInputClass: `form-control ${className} ${error ? 'is-invalid' : ''}`,
      onReady: (_, __, instancia) => { instancia.altInput.id = id || name; instancia.altInput.placeholder = placeholder; },
      minDate: sinLimites ? minDate || null : hoyISO(),
      maxDate: sinLimites ? null : enUnAnio(),
      disableMobile: true,            // el mismo calendario también en el celular
      formatDate: (fecha, formato) => (formato === 'Y-m-d'
        ? flatpickr.formatDate(fecha, formato)
        : flatpickr.formatDate(fecha, formato, Spanish).toLowerCase()),
      onChange: (_, texto) => alCambiar.current({ target: { name, value: texto } }),
    });
    return () => fp.current?.destroy();
  }, []);
  // si cambia desde afuera (al cargar un pedido), se refleja en el calendario
  useEffect(() => { if (fp.current && fp.current.input.value !== value) fp.current.setDate(value || null, false); }, [value]);
  useEffect(() => { fp.current?.altInput?.classList.toggle('is-invalid', Boolean(error)); }, [error]);
  useEffect(() => { if (sinLimites && fp.current) fp.current.set('minDate', minDate || null); }, [minDate]);
  // el campo real (AAAA-MM-DD) va oculto; la persona ve y usa el de Flatpickr («jueves 12 de noviembre»)
  return <input ref={input} type="hidden" name={name} defaultValue={value} placeholder={placeholder} />;
}

// La lista de horas cada 15 minutos. Si elegiste hoy, las horas que ya pasaron aparecen apagadas.
export function SelectorHora({ id, name, value, onChange, fecha, error }) {
  const [, setTic] = useState(0);
  // si la página queda abierta, cada minuto se apaga la hora que va pasando
  useEffect(() => { const t = setInterval(() => setTic((n) => n + 1), 60000); return () => clearInterval(t); }, []);
  const esHoy = fecha === hoyISO();
  const ahora = new Date();
  const yaPaso = `${dos(ahora.getHours())}:${dos(ahora.getMinutes())}`;
  const horas = value && !HORAS.includes(value) ? [...HORAS, value].sort() : HORAS;  // un pedido viejo con otra hora la conserva
  const primera = horas.find((h) => !(esHoy && h <= yaPaso));
  // si la hora elegida quedó en el pasado (cambió el día a hoy), se borra
  useEffect(() => { if (esHoy && value && value <= yaPaso) onChange({ target: { name, value: '' } }); }, [fecha]);
  return (
    <>
      <select id={id || name} name={name} className={`form-select ${error ? 'is-invalid' : ''}`} value={value} onChange={onChange}>
        <option value="">Elegí la hora</option>
        {horas.map((h) => <option key={h} value={h} disabled={esHoy && h <= yaPaso}>{h}</option>)}
      </select>
      {esHoy && <div className="form-text">{primera ? `Para hoy, desde las ${primera}.` : 'Hoy ya no quedan horarios: elegí otro día.'}</div>}
    </>
  );
}
