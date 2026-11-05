import { Link, NavLink, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

export function Navbar() {
  const { usuario, puede, salir } = useAuth();
  const navigate = useNavigate();

  const cerrar = () => {
    salir();
    navigate('/');
  };

  return (
    <header className="navbar-brand-custom text-white py-3 mb-4">
      <div className="container d-flex flex-wrap gap-3 justify-content-between align-items-center">
        <Link to="/" className="text-white text-decoration-none fs-5 fw-bold d-flex align-items-center">
          <span className="logo-pastilla me-2"><img src="/logo.png" alt="" /></span>
          Mudanzas y Fletes Salta
        </Link>
        <nav className="menu-marca d-flex flex-wrap align-items-center gap-1 fw-semibold">
          {usuario ? (
            <>
              {puede('PED_CONSULTAR') && <NavLink to="/pedidos" end>{puede('PED_GESTIONAR') ? 'Pedidos' : 'Mis pedidos'}</NavLink>}
              {puede('PED_REGISTRAR') && <NavLink to="/pedidos/nuevo">Pedir mudanza</NavLink>}
              {/* lo que todavía no está en React (usuarios, vehículos, servicios...) sigue en Django */}
              {puede('PED_GESTIONAR') && (
                <a href={`${window.location.protocol}//${window.location.hostname}:8002/`} target="_blank" rel="noopener noreferrer"
                   title="Usuarios, roles, vehículos, servicios y auditoría (abre el sistema en Django)">
                  Más secciones <i className="bi bi-box-arrow-up-right small" />
                </a>
              )}
              <span className="ms-2 text-white-50 text-capitalize d-none d-md-inline">{usuario.nombre}</span>
              <button type="button" className="btn btn-sm btn-light ms-2" onClick={cerrar}>
                <i className="bi bi-box-arrow-right me-1" />Salir
              </button>
            </>
          ) : (
            <>
              <Link to="/#servicios" className="d-none d-md-inline">Servicios</Link>
              <Link to="/#como-funciona" className="d-none d-md-inline">Cómo funciona</Link>
              <Link to="/#contacto" className="d-none d-md-inline">Contacto</Link>
              <NavLink to="/login" className="ms-md-2">Ingresar</NavLink>
              <Link to="/registro" className="btn btn-sm btn-light ms-1">Registrarme</Link>
            </>
          )}
        </nav>
      </div>
    </header>
  );
}
