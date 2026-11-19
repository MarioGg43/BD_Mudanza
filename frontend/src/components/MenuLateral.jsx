import { useEffect, useState } from 'react';
import { Link, NavLink, useLocation, useNavigate } from 'react-router-dom';
import axios from 'axios';
import { api } from '../services/api';
import { useAuth } from '../context/AuthContext';

// Todas las opciones del menú. Cada una se muestra solo si el rol tiene el permiso que pide.
const GRUPOS = [
  { titulo: 'Principal', opciones: [
    { to: '/tablero', texto: 'Tablero', icono: 'bi-speedometer2', permiso: 'PED_GESTIONAR' },
    { to: '/notificaciones', texto: 'Notificaciones', icono: 'bi-bell', numero: 'sin_leer', rojo: true, end: true },
  ] },
  { titulo: 'Operación', opciones: [
    { to: '/pedidos', texto: 'Pedidos', icono: 'bi-box-seam', permiso: 'PED_CONSULTAR', numero: 'pendientes' },
    { to: '/portal', texto: 'Portal del personal', icono: 'bi-person-badge', permiso: 'MUDANZAS_OPERAR' },
  ] },
  { titulo: 'Catálogo', opciones: [
    { to: '/vehiculos', texto: 'Vehículos', icono: 'bi-truck', permiso: 'VEH_GESTIONAR' },
    { to: '/servicios', texto: 'Servicios', icono: 'bi-tags', permiso: 'SRV_GESTIONAR' },
    { to: '/objetos', texto: 'Objetos', icono: 'bi-archive', permiso: 'OBJ_GESTIONAR' },
    { to: '/materiales', texto: 'Materiales', icono: 'bi-boxes', permiso: 'MAT_GESTIONAR', numero: 'materiales_bajos' },
  ] },
  { titulo: 'Análisis', opciones: [
    { to: '/reportes', texto: 'Reportes', icono: 'bi-bar-chart-line', permiso: ['REP_CONSULTAR', 'REP_FINANZAS'] },
    { to: '/auditoria', texto: 'Auditoría', icono: 'bi-clock-history', permiso: 'AUD_CONSULTAR' },
  ] },
  { titulo: 'Seguridad', opciones: [
    { to: '/usuarios', texto: 'Usuarios', icono: 'bi-people', permiso: 'USR_CONSULTAR' },
    { to: '/roles', texto: 'Roles', icono: 'bi-shield-lock', permiso: 'ROL_GESTIONAR' },
    { to: '/notificaciones/umbrales', texto: 'Umbrales de alertas', icono: 'bi-sliders', permiso: 'CFG_GESTIONAR' },
  ] },
];

// «Catálogo › Materiales» para la barra de arriba, según la ruta
export function ubicacion(pathname) {
  if (pathname.startsWith('/mi-cuenta')) return ['Cuenta', 'Mi cuenta'];
  if (pathname.startsWith('/notificaciones/umbrales')) return ['Seguridad', 'Umbrales de alertas'];
  for (const g of GRUPOS) {
    const o = g.opciones.find((x) => pathname === x.to || pathname.startsWith(`${x.to}/`));
    if (o) return [g.titulo, o.texto];
  }
  return ['Principal', 'Mudanzas y Fletes Salta'];
}

// Los números del menú (pedidos por confirmar, materiales bajos…): se piden al cambiar de pantalla y cada minuto
export function useNumerosMenu() {
  // key cambia en cada navegación, también al volver a la misma pantalla después de confirmar algo
  const { pathname, key } = useLocation();
  const [numeros, setNumeros] = useState({});
  useEffect(() => {
    const controller = new AbortController();
    const pedir = () => api.get('/menu', { signal: controller.signal }).then((r) => setNumeros(r.data))
      .catch((err) => { if (!axios.isCancel(err)) setNumeros({}); });
    pedir();
    const cada = setInterval(pedir, 60000);
    window.addEventListener('notificaciones-cambiaron', pedir);
    return () => { controller.abort(); clearInterval(cada); window.removeEventListener('notificaciones-cambiaron', pedir); };
  }, [pathname, key]);
  return numeros;
}

/* Menú lateral del personal (administrador, chofer, ayudante), igual que en Django: las opciones
   agrupadas por sección y plegables, con el número de lo pendiente al lado. En el celular se
   esconde y se abre con el botón de las tres rayas. El cliente sigue con el menú de arriba. */
export function MenuLateral({ abierto, onCerrar, numeros }) {
  const { usuario, puede, salir } = useAuth();
  const navigate = useNavigate();
  const { pathname } = useLocation();
  const tiene = (p) => !p || [].concat(p).some(puede);
  // al cambiar de pantalla en el celular, el menú se cierra
  useEffect(() => { onCerrar(); }, [pathname]);

  return (
    <>
      <aside className={`lateral ${abierto ? 'abierto' : ''}`} aria-label="Menú principal">
        <Link to="/" className="lateral-marca">
          <span className="logo-pastilla"><img src="/logo.png" alt="" /></span>
          <span><b>Mudanzas y Fletes Salta</b><small>Panel de gestión</small></span>
        </Link>

        {puede('PED_GESTIONAR') ? (
          <Link to="/pedidos" className="lateral-accion"><i className="bi bi-clipboard-check" /><span>Pedidos por confirmar</span><b>{numeros.pendientes ?? 0}</b></Link>
        ) : puede('MUDANZAS_OPERAR') && (
          <Link to="/portal" className="lateral-accion"><i className="bi bi-truck" /><span>Mis mudanzas</span><i className="bi bi-arrow-right" /></Link>
        )}

        <nav className="lateral-menu">
          {GRUPOS.map((g) => {
            const opciones = g.opciones.filter((o) => tiene(o.permiso));
            if (!opciones.length) return null;
            return (
              <details key={g.titulo} className="lateral-grupo" open>
                <summary className="lateral-seccion">{g.titulo}<i className="bi bi-chevron-down" /></summary>
                {opciones.map((o) => (
                  <NavLink key={o.to} to={o.to} end={o.end} className={({ isActive }) => (isActive ? 'activo' : '')}>
                    <i className={`bi ${o.icono}`} />{o.texto}
                    {o.numero && numeros[o.numero] > 0 && <span className={`lateral-numero ${o.rojo ? 'rojo' : ''}`}>{numeros[o.numero]}</span>}
                  </NavLink>
                ))}
              </details>
            );
          })}
        </nav>

        <div className="lateral-usuario">
          <span className="lateral-avatar" aria-hidden="true">{usuario.nombre[0]?.toUpperCase()}</span>
          <Link to="/mi-cuenta" className="lateral-usuario-datos"><b className="text-capitalize">{usuario.nombre} {usuario.apellido}</b><small>{usuario.rol}</small></Link>
          <button type="button" className="lateral-salir" title="Salir" aria-label="Cerrar la sesión" onClick={() => { salir(); navigate('/'); }}>
            <i className="bi bi-box-arrow-right" />
          </button>
        </div>
      </aside>
      {abierto && <div className="lateral-fondo" onClick={onCerrar} aria-hidden="true" />}
    </>
  );
}

// La barra de arriba del personal: dónde está, la hora, las mudanzas en curso y la campanita
export function BarraSuperior({ onAbrirMenu, numeros }) {
  const { usuario, puede } = useAuth();
  const { pathname } = useLocation();
  const [seccion, titulo] = ubicacion(pathname);
  const [ahora, setAhora] = useState(new Date());
  useEffect(() => { const t = setInterval(() => setAhora(new Date()), 60000); return () => clearInterval(t); }, []);
  const fecha = ahora.toLocaleString('es-AR', { weekday: 'short', day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit', hourCycle: 'h23' })
    .replace(',', '').replace('.', '');
  const sinLeer = numeros.sin_leer || 0;
  return (
    <header className="barra-superior">
      <button type="button" className="barra-boton solo-celular" onClick={onAbrirMenu} aria-label="Abrir el menú"><i className="bi bi-list" /></button>
      <div className="barra-titulo">
        <b>{titulo}</b>
        <small>{seccion} <i className="bi bi-chevron-right" /> {titulo}</small>
      </div>
      <div className="barra-derecha">
        <span className="barra-fecha"><i className="bi bi-clock me-1" />{fecha}</span>
        {puede('PED_GESTIONAR') && (
          <Link to="/pedidos" className={`barra-estado ${numeros.en_curso ? 'activo' : ''}`} title="Mudanzas en curso ahora">
            <span className="punto-vivo" />{numeros.en_curso ? `${numeros.en_curso} en curso` : 'Sin mudanzas en curso'}
          </Link>
        )}
        <Link to="/notificaciones" className="barra-boton" aria-label={`Notificaciones${sinLeer ? `: ${sinLeer} sin leer` : ''}`}>
          <i className={`bi bi-bell${sinLeer ? '-fill' : ''}`} />{sinLeer > 0 && <span className="barra-numero">{sinLeer > 99 ? '99+' : sinLeer}</span>}
        </Link>
        <Link to="/mi-cuenta" className="barra-usuario">
          <span className="lateral-avatar chico" aria-hidden="true">{usuario.nombre[0]?.toUpperCase()}</span>
          <span className="solo-ancho text-capitalize">{usuario.nombre}</span>
        </Link>
      </div>
    </header>
  );
}
