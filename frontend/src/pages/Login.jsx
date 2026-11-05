import { useState } from 'react';
import { Link, Navigate, useLocation } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

// Segundo paso del login cuando la clave es provisoria (la dio la empresa al crear el usuario
// o al restablecerla): la persona elige una suya y entra.
function CambiarClave({ ident, clave, onVolver }) {
  const { cambiarClave } = useAuth();
  const [nueva, setNueva] = useState('');
  const [confirmar, setConfirmar] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const distintas = confirmar && nueva !== confirmar;

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      await cambiarClave({ usuario: ident, clave, nueva, confirmar });
    } catch (err) {
      setError(err.message);
      setLoading(false);
    }
  };

  return (
    <>
      <div className="alert alert-warning small">
        <i className="bi bi-key me-1" />Tu clave es <b>provisoria</b>: te la dio la empresa. Elegí una nueva para entrar.
      </div>
      {error && <div className="alert alert-danger small" role="alert">{error}</div>}
      <form onSubmit={handleSubmit} noValidate>
        <div className="mb-3">
          <label htmlFor="nueva" className="form-label">Clave nueva</label>
          <input id="nueva" type="password" className="form-control" autoComplete="new-password" autoFocus
                 value={nueva} onChange={(e) => setNueva(e.target.value)} disabled={loading} />
          <div className="form-text">8 o más caracteres, con mayúscula, minúscula, número y un caracter especial.</div>
        </div>
        <div className="mb-3">
          <label htmlFor="confirmar" className="form-label">Repetí la clave nueva</label>
          <input id="confirmar" type="password" className={`form-control ${distintas ? 'is-invalid' : ''}`} autoComplete="new-password"
                 value={confirmar} onChange={(e) => setConfirmar(e.target.value)} disabled={loading} />
          {distintas && <div className="invalid-feedback">Las dos claves no coinciden.</div>}
        </div>
        <button type="submit" className="btn btn-primary w-100 py-2" disabled={loading || !nueva || !confirmar || distintas}>
          {loading ? 'Guardando...' : 'Guardar clave y entrar'}
        </button>
        <button type="button" className="btn btn-link w-100 mt-2" onClick={onVolver} disabled={loading}>Volver</button>
      </form>
    </>
  );
}

export function Login() {
  const { usuario, login, inicio } = useAuth();
  const location = useLocation();
  const [ident, setIdent] = useState('');
  const [clave, setClave] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [provisoria, setProvisoria] = useState(false);

  // Con sesión: vuelve a donde quería ir o a su primera pantalla (el chofer, a su portal)
  if (usuario) return <Navigate to={location.state?.desde || inicio} replace />;

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      await login(ident.trim(), clave);
    } catch (err) {
      // la API avisa que la clave es provisoria: se pasa al formulario para cambiarla
      if (err.errores?.cambiar_clave) setProvisoria(true);
      else setError(err.message);
      setLoading(false);
    }
  };

  return (
    <div className="card-panel p-4 mx-auto" style={{ maxWidth: 420 }}>
      <div className="text-center mb-4">
        <span className="logo-pastilla logo-pastilla-lg"><img src="/logo.png" alt="Mudanzas y Fletes Salta" /></span>
        <h1 className="h4 fw-bold mt-3 mb-1">{provisoria ? 'Elegí tu clave' : 'Iniciar sesión'}</h1>
        <p className="text-muted small mb-0">{provisoria ? `Usuario: ${ident.trim()}` : 'Entrá para pedir tu mudanza o ver cómo va.'}</p>
      </div>

      {provisoria ? (
        <CambiarClave ident={ident.trim()} clave={clave} onVolver={() => { setProvisoria(false); setClave(''); }} />
      ) : (
        <>
          {error && <div className="alert alert-danger small" role="alert">{error}</div>}
          <form onSubmit={handleSubmit} noValidate>
            <div className="mb-3">
              <label htmlFor="usuario" className="form-label">DNI, usuario o correo</label>
              <input id="usuario" type="text" className="form-control" autoComplete="username" required
                     value={ident} onChange={(e) => setIdent(e.target.value)} disabled={loading} />
            </div>
            <div className="mb-3">
              <label htmlFor="clave" className="form-label">Contraseña</label>
              <input id="clave" type="password" className="form-control" autoComplete="current-password" required
                     value={clave} onChange={(e) => setClave(e.target.value)} disabled={loading} />
            </div>
            <button type="submit" className="btn btn-primary w-100 py-2" disabled={loading || !ident || !clave}>
              {loading ? (
                <><span className="spinner-border spinner-border-sm me-2" aria-hidden="true" />Conectando...</>
              ) : 'Ingresar'}
            </button>
          </form>
          <p className="text-center small mt-3 mb-0">
            ¿No tenés cuenta? <Link to="/registro" className="fw-semibold">Registrate</Link>
          </p>
        </>
      )}
    </div>
  );
}
