/* Un campo de formulario con su etiqueta, su ayuda y su error (los de la API vienen por campo).
   Según las props dibuja un input, un select (con `opciones`) o un textarea (tipo="textarea"). */
export function Campo({ label, name, error, ayuda, col = 'col-12', tipo = 'text', opciones, vacio, ...props }) {
  const clase = `${opciones ? 'form-select' : 'form-control'} ${error ? 'is-invalid' : ''}`;
  let control;
  if (opciones) {
    control = (
      <select id={name} name={name} className={clase} {...props}>
        {vacio !== undefined && <option value="">{vacio}</option>}
        {opciones.map((o) => <option key={o.value} value={o.value}>{o.label}</option>)}
      </select>
    );
  } else if (tipo === 'textarea') {
    control = <textarea id={name} name={name} className={clase} rows={3} {...props} />;
  } else {
    control = <input id={name} name={name} type={tipo} className={clase} {...props} />;
  }
  return (
    <div className={col}>
      <label htmlFor={name} className="form-label">{label}</label>
      {control}
      {ayuda && !error && <div className="form-text">{ayuda}</div>}
      {error && <div className="invalid-feedback">{error}</div>}
    </div>
  );
}

// Convierte una lista de textos en las opciones de <Campo>
export const opcionesDe = (lista) => lista.map((x) => ({ value: x, label: x }));
