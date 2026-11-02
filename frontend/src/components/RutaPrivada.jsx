import { Navigate, Outlet, useLocation } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

// Sin sesión manda al login (y vuelve a donde quería ir); sin el permiso muestra el aviso.
export function RutaPrivada({ permiso }) {
  const { usuario, puede } = useAuth();
  const location = useLocation();
  if (!usuario) return <Navigate to="/login" replace state={{ desde: location.pathname }} />;
  if (permiso && !puede(permiso)) {
    return (
      <div className="alert alert-warning mx-auto" style={{ maxWidth: 600 }}>
        <i className="bi bi-shield-lock me-1" />No tenés permiso para entrar a esta pantalla.
      </div>
    );
  }
  return <Outlet />;
}
