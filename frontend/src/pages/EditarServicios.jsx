import { useState } from 'react';
import { Link, useNavigate, useParams } from 'react-router-dom';
import { useCarga } from '../hooks/useCarga';
import { adminService } from '../services/adminService';
import { TarjetaOpcion } from '../components/TarjetaOpcion';
import { LoadingSpinner } from '../components/LoadingSpinner';
import { ErrorAlert } from '../components/ErrorAlert';
import { dinero } from '../utils/formato';
import { iconoServicio } from '../utils/servicios';

export function EditarServicios() {
  const { id } = useParams();
  const { datos, loading, error } = useCarga((signal) => adminService.getServicios(id, signal), [id]);
  if (loading) return <LoadingSpinner />;
  if (error) return <ErrorAlert message={error} />;
  return <Formulario id={id} datos={datos} />;
}

function Formulario({ id, datos }) {
  const navigate = useNavigate();
  const [servicio, setServicio] = useState(datos.servicio);
  const [adicionales, setAdicionales] = useState(datos.elegidos);
  const [errores, setErrores] = useState({});
  const [enviando, setEnviando] = useState(false);

  const alternar = (n) => setAdicionales(adicionales.includes(n) ? adicionales.filter((a) => a !== n) : [...adicionales, n]);

  const guardar = async (e) => {
    e.preventDefault();
    setEnviando(true);
    setErrores({});
    try {
      await adminService.editarServicios(id, servicio, adicionales);
      navigate(`/pedidos/${id}`, { state: { aviso: `Servicios del pedido N° ${id} actualizados. El total se recalculó.` } });
    } catch (err) {
      setErrores({ __all__: err.message, ...err.errores });
      setEnviando(false);
    }
  };

  return (
    <form onSubmit={guardar} className="mx-auto" style={{ maxWidth: 800 }} noValidate>
      <Link to={`/pedidos/${id}`} className="small text-decoration-none"><i className="bi bi-arrow-left" /> Volver al pedido</Link>
      <h1 className="h3 fw-bold mt-2 mb-1">Servicios del pedido N° {id}</h1>
      <p className="text-muted mb-4">
        Los servicios que ya tenía conservan su precio; los nuevos van al precio de hoy
        {datos.recargo ? ` (el principal, con +${datos.recargo} % por el camión)` : ''}. Si el principal dura distinto,
        el vehículo y el personal tienen que seguir libres.
      </p>
      {errores.__all__ && <div className="alert alert-danger">{errores.__all__}</div>}

      <section className="card-panel p-4 mb-3">
        <h2 className="h6 fw-bold text-uppercase text-muted mb-3">Servicio principal</h2>
        <div className="row row-cols-1 row-cols-sm-3 g-2" role="radiogroup" aria-label="Servicio principal">
          {datos.principales.map((s) => (
            <div key={s.id} className="col">
              <TarjetaOpcion id={`srv${s.id}`} name="servicio" icono={iconoServicio(s.nombre)} titulo={s.nombre}
                             checked={servicio === s.id} onChange={() => setServicio(s.id)}>
                <span className="fw-bold">{dinero(s.precio)}</span>
                <span className="small text-muted">unas {s.horas} horas</span>
              </TarjetaOpcion>
            </div>
          ))}
        </div>
        {errores.servicio && <div className="invalid-feedback d-block">{errores.servicio}</div>}
      </section>

      <section className="card-panel p-4 mb-4">
        <h2 className="h6 fw-bold text-uppercase text-muted mb-3">Adicionales</h2>
        <div className="row row-cols-1 row-cols-sm-2 g-2">
          {datos.adicionales.map((s) => (
            <div key={s.id} className="col">
              <TarjetaOpcion tipo="checkbox" id={`adi${s.id}`} icono={iconoServicio(s.nombre)} iconoClase="opcion-icono-chico"
                             titulo={s.nombre} checked={adicionales.includes(s.id)} onChange={() => alternar(s.id)}>
                <span className="small fw-semibold">{s.precio > 0 ? `+ ${dinero(s.precio)}` : 'Sin cargo'}</span>
              </TarjetaOpcion>
            </div>
          ))}
        </div>
        {errores.adicionales && <div className="invalid-feedback d-block">{errores.adicionales}</div>}
      </section>

      <div className="d-flex justify-content-end gap-3">
        <Link to={`/pedidos/${id}`} className="btn btn-outline-secondary px-4">Volver</Link>
        <button type="submit" className="btn btn-success px-4 fw-bold" disabled={enviando || !servicio}>
          {enviando ? 'Guardando...' : 'Guardar servicios'}
        </button>
      </div>
    </form>
  );
}
