import { useState } from 'react';
import { Link, useNavigate, useParams } from 'react-router-dom';
import { useCarga } from '../../hooks/useCarga';
import { portalService } from '../../services/portalService';
import { ModalObjeto, etiqueta } from '../../components/ModalObjeto';
import { TarjetaOpcion } from '../../components/TarjetaOpcion';
import { LoadingSpinner } from '../../components/LoadingSpinner';
import { ErrorAlert } from '../../components/ErrorAlert';
import { desdeServidor, haciaServidor } from '../../utils/inventario';
import { iconoServicio } from '../../utils/servicios';

export function Relevamiento() {
  const { id } = useParams();
  const { datos, loading, error } = useCarga((signal) => portalService.getRelevamiento(id, signal), [id]);
  if (loading) return <LoadingSpinner />;
  if (error) return <ErrorAlert message={error} />;
  return <Formulario id={id} datos={datos} />;
}

/* Lo que encuentra el chofer al llegar: la cantidad real de lo declarado, lo que había y no se
   declaró (con la misma ventana «Agregar objeto» que usa el cliente, con la lógica de «Otro»),
   los adicionales que hacen falta y un recargo con su motivo. */
function Formulario({ id, datos }) {
  const navigate = useNavigate();
  const declarados = datos.items.map(desdeServidor);
  const [reales, setReales] = useState(Object.fromEntries(datos.items.map((i) => [i.id, String(i.cantidad)])));
  const [nuevos, setNuevos] = useState([]);
  const [adicionales, setAdicionales] = useState([]);
  const [recargo, setRecargo] = useState(datos.recargo ? String(datos.recargo) : '');
  const [motivo, setMotivo] = useState(datos.motivo);
  const [modal, setModal] = useState(null); // null = cerrada; -1 = agregar; n = editar el nuevo n
  const [errores, setErrores] = useState({});
  const [enviando, setEnviando] = useState(false);

  // La ventana ve lo declarado y lo nuevo juntos, así avisa si algo ya está en el pedido
  const todos = [...declarados, ...nuevos];
  const guardarObjeto = (it) => {
    setNuevos(modal >= 0 ? nuevos.map((x, k) => (k === modal ? it : x)) : [...nuevos, it]);
    setModal(null);
  };
  const editarRepetido = (k) => {
    if (k >= declarados.length) { setModal(k - declarados.length); return; }
    // un objeto declarado no se agrega de nuevo: se corrige su cantidad real arriba
    setModal(null);
    setTimeout(() => document.getElementById(`real-${datos.items[k].id}`)?.focus(), 300);
  };

  const guardar = async (e) => {
    e.preventDefault();
    setEnviando(true);
    setErrores({});
    try {
      await portalService.guardarRelevamiento(id, {
        reales, nuevos: nuevos.map(haciaServidor), adicionales, recargo: recargo || 0, motivo });
      navigate('/portal', { state: { aviso: `Relevamiento del pedido N° ${id} guardado.` } });
    } catch (err) {
      setErrores({ __all__: err.message, ...err.errores });
      setEnviando(false);
      window.scrollTo({ top: 0, behavior: 'instant' });
    }
  };

  return (
    <form onSubmit={guardar} className="mx-auto" style={{ maxWidth: 800 }} noValidate>
      <Link to="/portal" className="small text-decoration-none"><i className="bi bi-arrow-left" /> Volver a mis mudanzas</Link>
      <h1 className="h3 fw-bold mt-2 mb-1">Relevamiento del pedido N° {id}</h1>
      <p className="text-muted mb-4">Cliente: {datos.cliente}. Cargá lo que encontraste al llegar; el administrador ve lo que declaró el cliente y lo que había.</p>
      {errores.__all__ && <div className="alert alert-danger">{errores.__all__}</div>}
      {errores.inventario && <div className="alert alert-danger">{errores.inventario}</div>}

      <section className="card-panel p-4 mb-3">
        <h2 className="h6 fw-bold text-uppercase text-muted mb-1">1. Lo que declaró el cliente</h2>
        <p className="small text-muted mb-3">Poné la cantidad que hay de verdad (0 si no estaba).</p>
        <ul className="list-group list-group-flush">
          {datos.items.map((i, k) => {
            const cambio = reales[i.id] !== String(i.cantidad);
            return (
              <li key={i.id} className="list-group-item px-0 d-flex justify-content-between align-items-center gap-3">
                <label htmlFor={`real-${i.id}`} className="mb-0">
                  <b>{etiqueta(declarados[k])}</b>{i.fragil && <span className="badge text-bg-warning ms-1">frágil</span>}
                  <span className="d-block small text-muted">Declaró {i.cantidad}{cambio && <b className="text-marca"> · cambia a {reales[i.id] || 0}</b>}</span>
                </label>
                <input id={`real-${i.id}`} type="number" min={0} max={datos.max_cantidad} inputMode="numeric"
                       className="form-control text-end" style={{ maxWidth: 100 }} value={reales[i.id]}
                       onChange={(e) => setReales({ ...reales, [i.id]: e.target.value })} />
              </li>
            );
          })}
        </ul>
      </section>

      <section className="card-panel p-4 mb-3">
        <h2 className="h6 fw-bold text-uppercase text-muted mb-3">2. Lo que había y no estaba declarado</h2>
        {nuevos.length === 0 ? <p className="text-muted">No agregaste nada.</p> : (
          <ul className="list-group mb-3">
            {nuevos.map((it, k) => (
              <li key={k} className="list-group-item d-flex justify-content-between align-items-center gap-2 flex-wrap">
                <div>
                  <span className="fw-semibold">{it.cantidad} × {etiqueta(it)}</span>
                  {it.fragil && <span className="badge text-bg-warning ms-1">frágil</span>}
                  {it.detalle && <div className="small text-muted">{it.detalle}</div>}
                </div>
                <div className="d-flex gap-2">
                  <button type="button" className="btn btn-sm btn-outline-secondary" onClick={() => setModal(k)}><i className="bi bi-pencil me-1" />Editar</button>
                  <button type="button" className="btn btn-sm btn-outline-danger" onClick={() => setNuevos(nuevos.filter((_, n) => n !== k))}><i className="bi bi-trash me-1" />Quitar</button>
                </div>
              </li>
            ))}
          </ul>
        )}
        <button type="button" className="btn btn-outline-success fw-semibold" onClick={() => setModal(-1)}>
          <i className="bi bi-plus-circle me-1" />Agregar objeto
        </button>
      </section>

      {datos.adicionales.length > 0 && (
        <section className="card-panel p-4 mb-3">
          <h2 className="h6 fw-bold text-uppercase text-muted mb-3">3. Adicionales que hicieron falta</h2>
          <div className="row row-cols-1 row-cols-sm-2 g-2">
            {datos.adicionales.map((s) => (
              <div key={s.id} className="col">
                <TarjetaOpcion tipo="checkbox" id={`adi${s.id}`} icono={iconoServicio(s.nombre)} iconoClase="opcion-icono-chico"
                               titulo={s.nombre} checked={adicionales.includes(s.id)}
                               onChange={() => setAdicionales(adicionales.includes(s.id) ? adicionales.filter((a) => a !== s.id) : [...adicionales, s.id])} />
              </div>
            ))}
          </div>
          {errores.adicionales && <div className="invalid-feedback d-block">{errores.adicionales}</div>}
        </section>
      )}

      <section className="card-panel p-4 mb-4">
        <h2 className="h6 fw-bold text-uppercase text-muted mb-3">{datos.adicionales.length ? 4 : 3}. Recargo</h2>
        <div className="row g-3">
          <div className="col-sm-4">
            <label htmlFor="recargo" className="form-label">Monto ($)</label>
            <input id="recargo" type="number" min={0} className={`form-control ${errores.recargo ? 'is-invalid' : ''}`}
                   placeholder="0" value={recargo} onChange={(e) => setRecargo(e.target.value)} />
            {errores.recargo && <div className="invalid-feedback">{errores.recargo}</div>}
          </div>
          <div className="col-sm-8">
            <label htmlFor="motivo" className="form-label">Motivo {Number(recargo) > 0 && <span className="text-danger">(obligatorio)</span>}</label>
            <input id="motivo" className={`form-control ${errores.motivo ? 'is-invalid' : ''}`} maxLength={200}
                   placeholder="Ej.: había un piano que no se declaró" value={motivo} onChange={(e) => setMotivo(e.target.value)} />
            {errores.motivo && <div className="invalid-feedback">{errores.motivo}</div>}
          </div>
        </div>
        <p className="small text-muted mt-2 mb-0">Solo si hay que cobrar algo más. Se suma al total del pedido.</p>
      </section>

      <div className="d-flex justify-content-end gap-3">
        <Link to="/portal" className="btn btn-outline-secondary px-4">Volver</Link>
        <button type="submit" className="btn btn-success px-4 fw-bold" disabled={enviando}>{enviando ? 'Guardando...' : 'Guardar relevamiento'}</button>
      </div>

      {modal !== null && (
        <ModalObjeto key={modal} objetos={datos.objetos} maxCantidad={datos.max_cantidad} items={todos}
                     editando={modal >= 0 ? declarados.length + modal : -1}
                     onGuardar={guardarObjeto} onEditarOtro={editarRepetido} onHide={() => setModal(null)} />
      )}
    </form>
  );
}
