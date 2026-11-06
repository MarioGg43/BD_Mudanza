import { useState } from 'react';
import { Link, Navigate, useLocation } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { CampoClave } from '../components/CampoClave';

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
          <CampoClave id="nueva" autoComplete="new-password" autoFocus
                      value={nueva} onChange={(e) => setNueva(e.target.value)} disabled={loading} />
          <div className="form-text">8 o más caracteres, con mayúscula, minúscula, número y un caracter especial.</div>
        </div>
        <div className="mb-3">
          <label htmlFor="confirmar" className="form-label">Repetí la clave nueva</label>
          <CampoClave id="confirmar" invalido={Boolean(distintas)} autoComplete="new-password"
                      value={confirmar} onChange={(e) => setConfirmar(e.target.value)} disabled={loading} />
          {distintas && <div className="invalid-feedback d-block">Las dos claves no coinciden.</div>}
        </div>
        <button type="submit" className="btn btn-primary w-100 py-2" disabled={loading || !nueva || !confirmar || distintas}>
          {loading ? 'Guardando...' : 'Guardar clave y entrar'}
        </button>
        <button type="button" className="btn btn-link w-100 mt-2" onClick={onVolver} disabled={loading}>Volver</button>
      </form>
    </>
  );
}

// «¿Olvidaste tu contraseña?» (clientes): con el DNI y el correo de la cuenta se elige una clave
// nueva y se entra. Al personal le restablece la clave el administrador.
function OlvideClave({ onVolver }) {
  const { recuperarClave } = useAuth();
  const [datos, setDatos] = useState({ dni: '', correo: '', nueva: '', confirmar: '' });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const distintas = datos.confirmar && datos.nueva !== datos.confirmar;
  const cambiar = (e) => setDatos({ ...datos, [e.target.name]: e.target.value });

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      await recuperarClave({ ...datos, dni: datos.dni.trim(), correo: datos.correo.trim() });
    } catch (err) {
      setError(err.message);
      setLoading(false);
    }
  };

  return (
    <>
      {error && <div className="alert alert-danger small" role="alert">{error}</div>}
      <form onSubmit={handleSubmit} noValidate>
        <div className="mb-3">
          <label htmlFor="dni" className="form-label">DNI</label>
          <input id="dni" name="dni" type="text" inputMode="numeric" className="form-control" autoComplete="username" autoFocus
                 value={datos.dni} onChange={cambiar} disabled={loading} />
        </div>
        <div className="mb-3">
          <label htmlFor="correo" className="form-label">Correo de tu cuenta</label>
          <input id="correo" name="correo" type="email" className="form-control" autoComplete="email"
                 value={datos.correo} onChange={cambiar} disabled={loading} />
        </div>
        <div className="mb-3">
          <label htmlFor="nueva" className="form-label">Clave nueva</label>
          <CampoClave id="nueva" name="nueva" autoComplete="new-password" value={datos.nueva} onChange={cambiar} disabled={loading} />
          <div className="form-text">8 o más caracteres, con mayúscula, minúscula, número y un caracter especial.</div>
        </div>
        <div className="mb-3">
          <label htmlFor="confirmar" className="form-label">Repetí la clave nueva</label>
          <CampoClave id="confirmar" name="confirmar" autoComplete="new-password" invalido={Boolean(distintas)}
                      value={datos.confirmar} onChange={cambiar} disabled={loading} />
          {distintas && <div className="invalid-feedback d-block">Las dos claves no coinciden.</div>}
        </div>
        <button type="submit" className="btn btn-primary w-100 py-2"
                disabled={loading || !datos.dni || !datos.correo || !datos.nueva || !datos.confirmar || distintas}>
          {loading ? 'Guardando...' : 'Guardar clave y entrar'}
        </button>
        <button type="button" className="btn btn-link w-100 mt-2" onClick={onVolver} disabled={loading}>Volver a iniciar sesión</button>
        <p className="small text-muted text-center mb-0">¿Trabajás en la empresa? Pedile al administrador que te restablezca la clave.</p>
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
  // qué se muestra: el login, el paso de la clave provisoria o «¿Olvidaste tu contraseña?»
  const [modo, setModo] = useState('login');

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
      if (err.errores?.cambiar_clave) setModo('provisoria');
      else setError(err.message);
      setLoading(false);
    }
  };

  const volver = () => { setModo('login'); setClave(''); setError(null); };
  const TITULOS = {
    login: ['Iniciar sesión', 'Entrá para pedir tu mudanza o ver cómo va.'],
    provisoria: ['Elegí tu clave', `Usuario: ${ident.trim()}`],
    olvide: ['¿Olvidaste tu contraseña?', 'Poné el DNI y el correo de tu cuenta y elegí una clave nueva.'],
  };

  return (
    <div className="card-panel p-4 mx-auto" style={{ maxWidth: 420 }}>
      <div className="text-center mb-4">
        <span className="logo-pastilla logo-pastilla-lg"><img src="/logo.png" alt="Mudanzas y Fletes Salta" /></span>
        <h1 className="h4 fw-bold mt-3 mb-1">{TITULOS[modo][0]}</h1>
        <p className="text-muted small mb-0">{TITULOS[modo][1]}</p>
      </div>

      {modo === 'provisoria' && <CambiarClave ident={ident.trim()} clave={clave} onVolver={volver} />}
      {modo === 'olvide' && <OlvideClave onVolver={volver} />}
      {modo === 'login' && (
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
              <CampoClave id="clave" autoComplete="current-password" required
                          value={clave} onChange={(e) => setClave(e.target.value)} disabled={loading} />
              <div className="text-end mt-1">
                <button type="button" className="btn btn-link btn-sm p-0" onClick={() => { setModo('olvide'); setError(null); }}>
                  ¿Olvidaste tu contraseña?
                </button>
              </div>
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
