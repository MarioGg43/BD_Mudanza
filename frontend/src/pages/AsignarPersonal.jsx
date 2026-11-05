import { useState } from 'react';
import { Link, useNavigate, useParams } from 'react-router-dom';
import { useCarga } from '../hooks/useCarga';
import { adminService } from '../services/adminService';
import { TarjetaOpcion } from '../components/TarjetaOpcion';
import { LoadingSpinner } from '../components/LoadingSpinner';
import { ErrorAlert } from '../components/ErrorAlert';

// Página: trae los choferes y ayudantes libres y recién ahí arma el formulario
export function AsignarPersonal() {
  const { id } = useParams();
  const { datos, loading, error } = useCarga((signal) => adminService.getPersonal(id, signal), [id]);
  if (loading) return <LoadingSpinner texto="Buscando personal libre..." />;
  if (error) return <ErrorAlert message={error} />;
  return <Formulario id={id} datos={datos} />;
}

function Formulario({ id, datos }) {
  const navigate = useNavigate();
  const [chofer, setChofer] = useState(datos.chofer ?? datos.sugerido);
  const [ayudantes, setAyudantes] = useState(datos.elegidos);
  const [errores, setErrores] = useState({});
  const [enviando, setEnviando] = useState(false);

  const alternar = (n) => setAyudantes(ayudantes.includes(n) ? ayudantes.filter((a) => a !== n) : [...ayudantes, n]);
  const demasiados = ayudantes.length > datos.max_ayudantes;

  const guardar = async (e) => {
    e.preventDefault();
    setEnviando(true);
    setErrores({});
    try {
      await adminService.asignarPersonal(id, chofer, ayudantes);
      navigate(`/pedidos/${id}`, { state: { aviso: `Personal del pedido N° ${id} asignado.` } });
    } catch (err) {
      setErrores({ __all__: err.message, ...err.errores });
      setEnviando(false);
    }
  };

  return (
    <form onSubmit={guardar} className="mx-auto" style={{ maxWidth: 800 }} noValidate>
      <Link to={`/pedidos/${id}`} className="small text-decoration-none"><i className="bi bi-arrow-left" /> Volver al pedido</Link>
      <h1 className="h3 fw-bold mt-2 mb-1">Personal del pedido N° {id}</h1>
      <p className="text-muted mb-4">Solo aparece quien está libre en el horario de la mudanza.</p>
      {errores.__all__ && <div className="alert alert-danger">{errores.__all__}</div>}

      <section className="card-panel p-4 mb-3">
        <h2 className="h6 fw-bold text-uppercase text-muted mb-3"><i className="bi bi-person-badge me-1" />Chofer <span className="text-danger">(obligatorio)</span></h2>
        {datos.choferes.length === 0 ? (
          <div className="alert alert-warning mb-0">No hay choferes libres en ese horario. Reprogramá el pedido o liberá a alguien.</div>
        ) : (
          <div className="row row-cols-1 row-cols-sm-2 row-cols-md-3 g-2" role="radiogroup" aria-label="Chofer">
            {datos.choferes.map((c) => (
              <div key={c.id} className="col">
                <TarjetaOpcion id={`chofer${c.id}`} name="chofer" icono="bi-person-badge" iconoClase="opcion-icono-chico"
                               titulo={c.nombre} checked={chofer === c.id} onChange={() => setChofer(c.id)}>
                  {c.id === datos.sugerido && <span className="badge rounded-pill text-bg-light border mt-1">Chofer habitual del camión</span>}
                </TarjetaOpcion>
              </div>
            ))}
          </div>
        )}
        {errores.chofer && <div className="invalid-feedback d-block">{errores.chofer}</div>}
      </section>

      <section className="card-panel p-4 mb-4">
        <h2 className="h6 fw-bold text-uppercase text-muted mb-3">
          <i className="bi bi-people me-1" />Ayudantes de carga <span className="fw-normal">(opcional, hasta {datos.max_ayudantes})</span>
        </h2>
        {datos.ayudantes.length === 0 ? (
          <p className="text-muted mb-0">No hay ayudantes libres en ese horario.</p>
        ) : (
          <div className="row row-cols-1 row-cols-sm-2 row-cols-md-3 g-2">
            {datos.ayudantes.map((a) => (
              <div key={a.id} className="col">
                <TarjetaOpcion tipo="checkbox" id={`ayudante${a.id}`} icono="bi-person" iconoClase="opcion-icono-chico"
                               titulo={a.nombre} checked={ayudantes.includes(a.id)} onChange={() => alternar(a.id)} />
              </div>
            ))}
          </div>
        )}
        {demasiados && <div className="invalid-feedback d-block">Se pueden asignar hasta {datos.max_ayudantes} ayudantes.</div>}
        {errores.ayudantes && <div className="invalid-feedback d-block">{errores.ayudantes}</div>}
      </section>

      <div className="d-flex justify-content-end gap-3">
        <Link to={`/pedidos/${id}`} className="btn btn-outline-secondary px-4">Volver</Link>
        <button type="submit" className="btn btn-success px-4 fw-bold" disabled={enviando || !chofer || demasiados}>
          {enviando ? 'Guardando...' : 'Guardar personal'}
        </button>
      </div>
    </form>
  );
}
