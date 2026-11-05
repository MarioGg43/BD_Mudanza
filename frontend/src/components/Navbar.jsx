import { Link, NavLink, useNavigate } from 'react-router-dom';
import { Dropdown } from 'react-bootstrap';
import { useAuth } from '../context/AuthContext';

// Las secciones de administración, cada una con el permiso que hace falta para verla
const SECCIONES = [
  { permiso: 'VEH_GESTIONAR', to: '/vehiculos', texto: 'Vehículos', icono: 'bi-truck' },
  { permiso: 'SRV_GESTIONAR', to: '/servicios', texto: 'Servicios', icono: 'bi-list-check' },
  { permiso: 'OBJ_GESTIONAR', to: '/objetos', texto: 'Objetos', icono: 'bi-box-seam' },
  { permiso: 'USR_CONSULTAR', to: '/usuarios', texto: 'Usuarios', icono: 'bi-people' },
  { permiso: 'ROL_GESTIONAR', to: '/roles', texto: 'Roles y permisos', icono: 'bi-shield-lock' },
  { permiso: 'MUDANZAS_OPERAR', to: '/portal', texto: 'Mis mudanzas (portal)', icono: 'bi-person-workspace' },
];

export function Navbar() {
  const { usuario, puede, salir } = useAuth();
  const navigate = useNavigate();
  // el chofer ve su portal en la barra; dentro de «Administración» solo lo ve quien gestiona
  const secciones = SECCIONES.filter((s) => puede(s.permiso) && (s.to !== '/portal' || puede('PED_GESTIONAR')));

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
              {/* el portal del personal; el administrador lo tiene en «Administración» */}
              {puede('MUDANZAS_OPERAR') && !puede('PED_GESTIONAR') && <NavLink to="/portal">Mis mudanzas</NavLink>}
              {(secciones.length > 0 || puede('AUD_CONSULTAR')) && (
                <Dropdown align="end">
                  <Dropdown.Toggle as="button" type="button" className="menu-desplegable">Administración</Dropdown.Toggle>
                  <Dropdown.Menu>
                    {secciones.map((s) => (
                      <Dropdown.Item key={s.to} as={NavLink} to={s.to}><i className={`bi ${s.icono} me-2`} />{s.texto}</Dropdown.Item>
                    ))}
                    {/* la auditoría todavía está en el sistema de Django */}
                    {puede('AUD_CONSULTAR') && (
                      <>
                        <Dropdown.Divider />
                        <Dropdown.Item href={`${window.location.protocol}//${window.location.hostname}:8002/auditoria/`} target="_blank" rel="noopener noreferrer">
                          <i className="bi bi-journal-text me-2" />Auditoría <i className="bi bi-box-arrow-up-right small" />
                        </Dropdown.Item>
                      </>
                    )}
                  </Dropdown.Menu>
                </Dropdown>
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
