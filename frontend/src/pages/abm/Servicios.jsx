import { useState } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { useCarga } from '../../hooks/useCarga';
import { abmService } from '../../services/abmService';
import { ConfirmarAccion } from '../../components/ConfirmarAccion';
import { LoadingSpinner } from '../../components/LoadingSpinner';
import { ErrorAlert } from '../../components/ErrorAlert';
import { dinero } from '../../utils/formato';
import { iconoServicio } from '../../utils/servicios';

export function Servicios() {
  const location = useLocation();
  const [baja, setBaja] = useState(null); // el servicio que se va a dar de baja
  const [aviso, setAviso] = useState(location.state?.aviso);
  const { datos, loading, error, refetch } = useCarga((signal) => abmService.servicios(signal), []);

  if (loading) return <LoadingSpinner />;
  if (error) return <ErrorAlert message={error} onRetry={refetch} />;

  const darDeBaja = async () => {
    await abmService.bajaServicio(baja.id);
    setAviso(`«${baja.Tipo_servicio}» dado de baja. Se reactiva editándolo.`);
    setBaja(null);
    refetch();
  };

  return (
    <div>
      <div className="d-flex flex-wrap justify-content-between align-items-center gap-2 mb-4">
        <div>
          <h1 className="h3 fw-bold mb-1">Servicios</h1>
          <p className="text-muted mb-0">Lo que el cliente elige al pedir: un principal y, si quiere, adicionales.</p>
        </div>
        <Link to="/servicios/nuevo" className="btn btn-primary"><i className="bi bi-plus-lg me-1" />Nuevo servicio</Link>
      </div>
      {aviso && <div className="alert alert-success">{aviso}</div>}
      <div className="row row-cols-1 row-cols-md-2 row-cols-lg-3 g-3">
        {datos.servicios.map((s) => (
          <div key={s.id} className="col">
            <div className={`card-panel p-3 h-100 d-flex flex-column ${s.Activo ? '' : 'tarjeta-pasada'}`}>
              <div className="d-flex justify-content-between align-items-start gap-2">
                <span className="icono-marca mb-2"><i className={`bi ${iconoServicio(s.Tipo_servicio)} fs-5`} /></span>
                <span className={`estado ${s.Activo ? 'estado-finalizado' : 'estado-anulado'}`}>{s.Activo ? 'Activo' : 'De baja'}</span>
              </div>
              <h2 className="h6 fw-bold mb-1">{s.Tipo_servicio}</h2>
              <p className="small text-muted mb-2">{s.Categoria}{s.Duracion_horas ? ` · ${s.Duracion_horas} horas` : ''} · usado en {s.cant_pedidos} pedido{s.cant_pedidos === 1 ? '' : 's'}</p>
              <p className="fs-5 fw-bold mb-1">{s.Precio_base > 0 ? dinero(s.Precio_base) : 'Sin cargo'}</p>
              {s.materiales && <p className="small mb-2"><i className="bi bi-box2 me-1 text-marca" />{s.materiales}</p>}
              <div className="d-flex gap-2 mt-auto pt-2">
                <Link to={`/servicios/${s.id}/editar`} className="btn btn-sm btn-outline-secondary"><i className="bi bi-pencil me-1" />Editar</Link>
                {s.Activo && <button type="button" className="btn btn-sm btn-outline-danger" onClick={() => setBaja(s)}>Dar de baja</button>}
              </div>
            </div>
          </div>
        ))}
      </div>
      {baja && (
        <ConfirmarAccion titulo={`Dar de baja «${baja.Tipo_servicio}»`} boton="Dar de baja" claseBoton="btn-danger"
                         accion={darDeBaja} onHide={() => setBaja(null)}>
          <p className="mb-0">Deja de ofrecerse en los pedidos nuevos. Los pedidos que ya lo tienen lo conservan.</p>
        </ConfirmarAccion>
      )}
    </div>
  );
}
