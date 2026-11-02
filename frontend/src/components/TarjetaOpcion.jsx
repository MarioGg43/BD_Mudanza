/* Una opción que se elige tocando la tarjeta entera. Por dentro sigue siendo un radio o un
   checkbox de verdad (oculto a la vista, no al teclado ni al lector de pantalla). */
export function TarjetaOpcion({ tipo = 'radio', id, name, checked, onChange, icono, iconoClase = '', titulo, children }) {
  return (
    <label htmlFor={id} className={`opcion h-100 ${checked ? 'opcion-elegida' : ''}`}>
      <input id={id} type={tipo} name={name} className="opcion-input" checked={checked} onChange={onChange} />
      {checked && <i className="bi bi-check-circle-fill opcion-tilde" aria-hidden="true" />}
      {icono && <i className={`bi ${icono} opcion-icono ${iconoClase}`} aria-hidden="true" />}
      <span className="opcion-titulo">{titulo}</span>
      {children}
    </label>
  );
}
