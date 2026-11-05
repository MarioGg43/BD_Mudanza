import { useState } from 'react';
import { Link, Navigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

const CAMPOS = [
  { name: 'dni', label: 'DNI', type: 'text', col: 'col-sm-6', inputMode: 'numeric' },
  { name: 'telefono', label: 'Teléfono (opcional)', type: 'tel', col: 'col-sm-6' },
  { name: 'apellido', label: 'Apellido', type: 'text', col: 'col-sm-6' },
  { name: 'nombre', label: 'Nombre', type: 'text', col: 'col-sm-6' },
  { name: 'correo', label: 'Correo', type: 'email', col: 'col-12' },
  { name: 'clave', label: 'Clave', type: 'password', col: 'col-sm-6',
    ayuda: '8 o más caracteres, con mayúscula, minúscula, número y un caracter especial.' },
  { name: 'clave2', label: 'Repetir clave', type: 'password', col: 'col-sm-6' },
];

export function Registro() {
  const { usuario, registro, inicio } = useAuth();
  const [datos, setDatos] = useState(Object.fromEntries(CAMPOS.map((c) => [c.name, ''])));
  const [errores, setErrores] = useState({});
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);
  const [recien, setRecien] = useState(false); // se acaba de registrar: va directo a pedir la mudanza

  if (usuario) return <Navigate to={recien ? '/pedidos/nuevo' : inicio} replace />;

  const cambiar = (e) => setDatos({ ...datos, [e.target.name]: e.target.value });

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setRecien(true);
    try {
      await registro(datos);
    } catch (err) {
      setRecien(false);
      setError(err.message);
      setErrores(err.errores);
      setLoading(false);
    }
  };

  return (
    <div className="card-panel p-4 mx-auto" style={{ maxWidth: 640 }}>
      <h1 className="h4 fw-bold mb-1">Crear tu cuenta</h1>
      <p className="text-muted small mb-4">Con tu cuenta pedís la mudanza y seguís su estado.</p>
      {error && <div className="alert alert-danger small">{error}</div>}
      <form onSubmit={handleSubmit} noValidate>
        <div className="row g-3">
          {CAMPOS.map((c) => (
            <div key={c.name} className={c.col}>
              <label htmlFor={c.name} className="form-label">{c.label}</label>
              <input id={c.name} name={c.name} type={c.type} inputMode={c.inputMode}
                     className={`form-control ${errores[c.name] ? 'is-invalid' : ''}`}
                     value={datos[c.name]} onChange={cambiar} disabled={loading} />
              {c.ayuda && !errores[c.name] && <div className="form-text">{c.ayuda}</div>}
              {errores[c.name] && <div className="invalid-feedback">{errores[c.name]}</div>}
            </div>
          ))}
        </div>
        <div className="d-flex justify-content-between align-items-center mt-4">
          <Link to="/login" className="small">Ya tengo cuenta</Link>
          <button type="submit" className="btn btn-primary px-4" disabled={loading}>
            {loading ? 'Creando...' : 'Crear cuenta'}
          </button>
        </div>
      </form>
    </div>
  );
}
