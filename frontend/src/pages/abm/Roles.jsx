import { useState } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { useCarga } from '../../hooks/useCarga';
import { abmService } from '../../services/abmService';
import { ConfirmarAccion } from '../../components/ConfirmarAccion';
import { LoadingSpinner } from '../../components/LoadingSpinner';
import { ErrorAlert } from '../../components/ErrorAlert';

export function Roles() {
  const location = useLocation();
  const { datos, loading, error, refetch } = useCarga((signal) => abmService.roles(signal), []);
  const [eliminar, setEliminar] = useState(null);
  const [aviso, setAviso] = useState(location.state?.aviso);

  if (loading) return <LoadingSpinner />;
  if (error) return <ErrorAlert message={error} onRetry={refetch} />;
  const descripcion = Object.fromEntries(datos.catalogo.map((c) => [c.codigo, c.descripcion]));

  const borrar = async () => {
    await abmService.eliminarRol(eliminar.id);
    setAviso(`Rol «${eliminar.nombre}» eliminado.`);
    setEliminar(null);
    refetch();
  };

  return (
    <div>
      <div className="d-flex flex-wrap justify-content-between align-items-center gap-2 mb-4">
        <div>
          <h1 className="h3 fw-bold mb-1">Roles</h1>
          <p className="text-muted mb-0">Qué puede hacer cada rol. El acceso a cada pantalla se controla con estos permisos.</p>
        </div>
        <Link to="/roles/nuevo" className="btn btn-primary"><i className="bi bi-plus-lg me-1" />Nuevo rol</Link>
      </div>
      {aviso && <div className="alert alert-success">{aviso}</div>}
      <div className="row row-cols-1 row-cols-lg-2 g-3">
        {datos.roles.map((r) => (
          <div key={r.id} className="col">
            <div className="card-panel p-3 h-100 d-flex flex-column">
              <div className="d-flex justify-content-between align-items-start gap-2">
                <div>
                  <h2 className="h5 fw-bold mb-0">{r.nombre}</h2>
                  <p className="small text-muted mb-2">{r.descripcion || 'Sin descripción'} · {r.usuarios} usuario{r.usuarios === 1 ? '' : 's'}</p>
                </div>
                {r.del_sistema && <span className="badge text-bg-light border">del sistema</span>}
              </div>
              <div className="d-flex flex-wrap gap-1 mb-3">
                {r.permisos.length ? r.permisos.map((p) => (
                  <span key={p} className="chip-permiso" title={descripcion[p]}>{descripcion[p] || p}</span>
                )) : <span className="small text-muted">Sin permisos</span>}
              </div>
              <div className="d-flex gap-2 mt-auto">
                <Link to={`/roles/${r.id}/editar`} className="btn btn-sm btn-outline-secondary"><i className="bi bi-pencil me-1" />Editar</Link>
                {!r.del_sistema && (
                  <button type="button" className="btn btn-sm btn-outline-danger" onClick={() => setEliminar(r)}>Eliminar</button>
                )}
              </div>
            </div>
          </div>
        ))}
      </div>
      {eliminar && (
        <ConfirmarAccion titulo={`Eliminar el rol «${eliminar.nombre}»`} boton="Eliminar" claseBoton="btn-danger" accion={borrar} onHide={() => setEliminar(null)}>
          <p className="mb-0">Solo se puede si ningún usuario lo tiene. Esto no se deshace.</p>
        </ConfirmarAccion>
      )}
    </div>
  );
}
