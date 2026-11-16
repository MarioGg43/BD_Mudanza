import { Navigate, Outlet, useLocation } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

// El «patovica» de las pantallas: sin sesión te manda a entrar; sin permiso te muestra el aviso.
export function RutaPrivada({ permiso }) {
  const { usuario, puede } = useAuth();
  const location = useLocation();
  if (!usuario) return <Navigate to="/login" replace state={{ desde: location.pathname }} />;
  const permisos = Array.isArray(permiso) ? permiso : [permiso];
  if (permiso && !permisos.some(puede)) {
    return (
      <div className="alert alert-warning mx-auto" style={{ maxWidth: 600 }}>
        <i className="bi bi-shield-lock me-1" />No tenés permiso para entrar a esta pantalla.
      </div>
    );
  }
  return <Outlet />;
}
