import { useState } from 'react';

/* Un campo de contraseña con el «ojito» para ver lo que se escribió. Recibe las mismas props que
   un <input> (id, value, onChange, autoComplete...) y `invalido` para pintarlo de rojo. */
export function CampoClave({ invalido, className = '', ...props }) {
  const [ver, setVer] = useState(false);
  return (
    <div className={`input-group ${invalido ? 'has-validation' : ''}`}>
      <input {...props} type={ver ? 'text' : 'password'} className={`form-control ${invalido ? 'is-invalid' : ''} ${className}`} />
      <button type="button" className="btn btn-outline-secondary boton-ojo" onClick={() => setVer(!ver)}
              aria-label={ver ? 'Ocultar la contraseña' : 'Mostrar la contraseña'} aria-pressed={ver}
              title={ver ? 'Ocultar la contraseña' : 'Mostrar la contraseña'} disabled={props.disabled}>
        <i className={`bi ${ver ? 'bi-eye-slash' : 'bi-eye'}`} aria-hidden="true" />
      </button>
    </div>
  );
}
