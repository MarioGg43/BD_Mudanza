import { Link, useLocation } from 'react-router-dom';

export function NotFound() {
  const location = useLocation();
  return (
    <div className="card-panel p-5 text-center mx-auto" style={{ maxWidth: 560 }}>
      <h1 className="h3 fw-bold">Página no encontrada</h1>
      <p className="text-muted my-3">La dirección <code>{location.pathname}</code> no existe.</p>
      <Link to="/" className="btn btn-primary">Volver al inicio</Link>
    </div>
  );
}
