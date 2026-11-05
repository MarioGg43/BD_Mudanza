import { useState } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { useCarga } from '../../hooks/useCarga';
import { abmService } from '../../services/abmService';
import { ConfirmarAccion } from '../../components/ConfirmarAccion';
import { LoadingSpinner } from '../../components/LoadingSpinner';
import { ErrorAlert } from '../../components/ErrorAlert';

// Qué ventana está abierta: { tipo: 'correo' | 'rol' | 'clave' | 'baja' | 'reactivar', usuario, valor }
export function Usuarios() {
  const location = useLocation();
  const { datos, loading, error, refetch } = useCarga((signal) => abmService.usuarios(signal), []);
  const [ventana, setVentana] = useState(null);
  const [aviso, setAviso] = useState(location.state?.aviso);
  const [clave, setClave] = useState(null); // la clave provisoria recién generada (se muestra una vez)
  const [buscar, setBuscar] = useState('');
  const [rol, setRol] = useState('');
  const [soloActivos, setSoloActivos] = useState(false);

  if (loading) return <LoadingSpinner texto="Cargando usuarios..." />;
  if (error) return <ErrorAlert message={error} onRetry={refetch} />;
  const { puede } = datos;

  const q = buscar.trim().toLowerCase();
  const visibles = datos.usuarios.filter((u) => (!soloActivos || u.activo) && (!rol || u.rol === rol)
    && (!q || `${u.apellido} ${u.nombre} ${u.usuario} ${u.dni} ${u.correo}`.toLowerCase().includes(q)));

  const hecho = (texto) => {
    setAviso(texto);
    setVentana(null);
    refetch();
  };
  const u = ventana?.usuario;
  const ACCIONES = {
    correo: { titulo: `Cambiar el correo de ${u?.usuario}`, boton: 'Guardar',
      accion: async () => { await abmService.cambiarCorreo(u.dni, ventana.valor); hecho(`Correo de ${u.usuario} actualizado.`); } },
    rol: { titulo: `Cambiar el rol de ${u?.usuario}`, boton: 'Cambiar rol',
      accion: async () => { const r = await abmService.cambiarRol(u.dni, ventana.valor); hecho(`${u.usuario} pasó de ${r.rol_anterior} a ${r.rol}.`); } },
    clave: { titulo: `Restablecer la clave de ${u?.usuario}`, boton: 'Generar clave provisoria',
      accion: async () => { const r = await abmService.restablecerClave(u.dni); setClave(r); hecho(null); } },
    baja: { titulo: `Dar de baja a ${u?.usuario}`, boton: 'Dar de baja', clase: 'btn-danger',
      accion: async () => { await abmService.bajaUsuario(u.dni); hecho(`${u.usuario} quedó dado de baja.`); } },
    reactivar: { titulo: `Reactivar a ${u?.usuario}`, boton: 'Reactivar',
      accion: async () => { await abmService.reactivarUsuario(u.dni); hecho(`${u.usuario} está activo de nuevo.`); } },
  };
  const abrir = (tipo, usuario, valor = '') => { setClave(null); setVentana({ tipo, usuario, valor }); };

  return (
    <div>
      <div className="d-flex flex-wrap justify-content-between align-items-center gap-2 mb-4">
        <div>
          <h1 className="h3 fw-bold mb-1">Usuarios</h1>
          <p className="text-muted mb-0">El personal y los clientes. Las bajas son lógicas: nadie se borra.</p>
        </div>
        {puede.crear && <Link to="/usuarios/nuevo" className="btn btn-primary"><i className="bi bi-person-plus me-1" />Nuevo usuario</Link>}
      </div>
      {aviso && <div className="alert alert-success">{aviso}</div>}
      {clave && (
        <div className="alert alert-warning">
          <i className="bi bi-key me-1" />Clave provisoria de <b>{clave.usuario}</b>: <code className="fs-6">{clave.clave_provisoria}</code>.
          Pasásela por un medio seguro: al entrar la tiene que cambiar. No se vuelve a mostrar.
        </div>
      )}

      <div className="card-panel p-3 mb-3">
        <div className="row g-2 align-items-center">
          <div className="col-md-6">
            <input type="search" className="form-control form-control-sm" placeholder="Buscar por nombre, usuario, DNI o correo..."
                   aria-label="Buscar usuario" value={buscar} onChange={(e) => setBuscar(e.target.value)} />
          </div>
          <div className="col-6 col-md-3">
            <select className="form-select form-select-sm" aria-label="Filtrar por rol" value={rol} onChange={(e) => setRol(e.target.value)}>
              <option value="">Todos los roles</option>
              {[...new Set(datos.usuarios.map((x) => x.rol))].map((r) => <option key={r} value={r}>{r}</option>)}
            </select>
          </div>
          <div className="col-6 col-md-3">
            <div className="form-check mb-0">
              <input id="activos" type="checkbox" className="form-check-input" checked={soloActivos} onChange={(e) => setSoloActivos(e.target.checked)} />
              <label htmlFor="activos" className="form-check-label small">Solo activos</label>
            </div>
          </div>
        </div>
      </div>

      <p className="small text-muted">{visibles.length} usuario{visibles.length === 1 ? '' : 's'}</p>
      <div className="card-panel p-0 overflow-hidden">
        <div className="table-responsive">
          <table className="table align-middle mb-0">
            <thead><tr><th>Usuario</th><th>DNI</th><th>Correo</th><th>Rol</th><th>Estado</th><th>Último acceso</th><th className="text-end">Acciones</th></tr></thead>
            <tbody>
              {visibles.map((x) => {
                const opera = x.puede_operar && !x.soy_yo;
                return (
                  <tr key={x.dni} className={x.activo ? '' : 'tarjeta-pasada'}>
                    <td><span className="fw-semibold">{x.apellido}, {x.nombre}</span>{x.soy_yo && <span className="badge text-bg-light border ms-1">vos</span>}<br /><span className="small text-muted">{x.usuario}</span></td>
                    <td className="small">{x.dni}</td>
                    <td className="small">{x.correo}</td>
                    <td className="small">{x.rol}</td>
                    <td>
                      <span className={`estado ${x.activo ? 'estado-finalizado' : 'estado-anulado'}`}>{x.activo ? 'Activo' : 'De baja'}</span>
                      {x.activo && x.debe_cambiar_clave && <div className="small text-warning-emphasis mt-1">Debe cambiar la clave</div>}
                    </td>
                    <td className="small text-muted text-nowrap">{x.ultimo_acceso || 'nunca'}</td>
                    <td className="text-end text-nowrap">
                      {x.puede_operar && puede.correo && <button type="button" className="btn btn-sm btn-outline-secondary me-1" title="Cambiar correo" aria-label={`Cambiar el correo de ${x.usuario}`} onClick={() => abrir('correo', x, x.correo)}><i className="bi bi-envelope" /></button>}
                      {opera && puede.rol && <button type="button" className="btn btn-sm btn-outline-secondary me-1" title="Cambiar rol" aria-label={`Cambiar el rol de ${x.usuario}`} onClick={() => abrir('rol', x, String(x.id_rol))}><i className="bi bi-person-gear" /></button>}
                      {x.puede_operar && puede.clave && x.rol !== 'Cliente' && x.activo && <button type="button" className="btn btn-sm btn-outline-secondary me-1" title="Restablecer clave" aria-label={`Restablecer la clave de ${x.usuario}`} onClick={() => abrir('clave', x)}><i className="bi bi-key" /></button>}
                      {opera && puede.baja && (x.activo
                        ? <button type="button" className="btn btn-sm btn-outline-danger" title="Dar de baja" aria-label={`Dar de baja a ${x.usuario}`} onClick={() => abrir('baja', x)}><i className="bi bi-person-dash" /></button>
                        : <button type="button" className="btn btn-sm btn-outline-success" title="Reactivar" aria-label={`Reactivar a ${x.usuario}`} onClick={() => abrir('reactivar', x)}><i className="bi bi-person-check" /></button>)}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>

      {ventana && (
        <ConfirmarAccion titulo={ACCIONES[ventana.tipo].titulo} boton={ACCIONES[ventana.tipo].boton}
                         claseBoton={ACCIONES[ventana.tipo].clase} accion={ACCIONES[ventana.tipo].accion} onHide={() => setVentana(null)}>
          {ventana.tipo === 'correo' && (
            <>
              <label htmlFor="correoNuevo" className="form-label">Correo nuevo</label>
              <input id="correoNuevo" type="email" className="form-control" value={ventana.valor} autoFocus
                     onChange={(e) => setVentana({ ...ventana, valor: e.target.value })} />
            </>
          )}
          {ventana.tipo === 'rol' && (
            <>
              <label htmlFor="rolNuevo" className="form-label">Rol</label>
              <select id="rolNuevo" className="form-select" value={ventana.valor} onChange={(e) => setVentana({ ...ventana, valor: e.target.value })}>
                {datos.roles.map((r) => <option key={r.id} value={r.id}>{r.nombre}</option>)}
              </select>
              <p className="small text-muted mt-2 mb-0">Solo aparecen los roles que podés asignar. Un cliente no pasa al personal ni al revés.</p>
            </>
          )}
          {ventana.tipo === 'clave' && <p className="mb-0">Se genera una clave provisoria y, al entrar, {u.usuario} la tiene que cambiar.</p>}
          {ventana.tipo === 'baja' && <p className="mb-0">Queda inactivo y no puede entrar. Se reactiva cuando quieras. No se puede si tiene pedidos activos.</p>}
          {ventana.tipo === 'reactivar' && <p className="mb-0">Vuelve a poder entrar con su clave de siempre.</p>}
        </ConfirmarAccion>
      )}
    </div>
  );
}
