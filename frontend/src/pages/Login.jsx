import { useState } from 'react';
import { Link, Navigate, useLocation, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

export function Login() {
  const { usuario, login } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [ident, setIdent] = useState('');
  const [clave, setClave] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  if (usuario) return <Navigate to="/pedidos" replace />;

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      await login(ident.trim(), clave);
      navigate(location.state?.desde || '/pedidos', { replace: true });
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="card-panel p-4 mx-auto" style={{ maxWidth: 420 }}>
      <div className="text-center mb-4">
        <span className="logo-pastilla logo-pastilla-lg"><img src="/logo.png" alt="Mudanzas y Fletes Salta" /></span>
        <h1 className="h4 fw-bold mt-3 mb-1">Iniciar sesión</h1>
        <p className="text-muted small mb-0">Entrá para pedir tu mudanza o ver cómo va.</p>
      </div>

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
    </div>
  );
}
