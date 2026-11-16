import { useEffect, useState } from 'react';
import { Link, useNavigate, useParams } from 'react-router-dom';
import { useCarga } from '../../hooks/useCarga';
import { portalService } from '../../services/portalService';
import { LoadingSpinner } from '../../components/LoadingSpinner';
import { ErrorAlert } from '../../components/ErrorAlert';

/* «Terminamos»: antes de cerrar la mudanza, el chofer cuenta los materiales. Ya está cargado lo que
   salió; de los que se gastan pone cuánto usó (lo que sobra vuelve al depósito) y de los
   reutilizables cuántos volvieron (los que faltan quedan como pérdida). */
export function Terminar() {
  const { id } = useParams();
  const navigate = useNavigate();
  const { datos, loading, error, refetch } = useCarga((signal) => portalService.getTerminar(id, signal), [id]);
  const [valores, setValores] = useState({});
  const [enviando, setEnviando] = useState(false);
  const [problema, setProblema] = useState(null);

  useEffect(() => {
    if (datos) setValores(Object.fromEntries(datos.materiales.map((m) => [m.id, m.salio])));
  }, [datos]);

  // Al terminar, el chofer cuenta cuántos materiales se usaron; Django devuelve al stock lo que volvió.
  const terminar = async (e) => {
    e.preventDefault();
    setEnviando(true);
    setProblema(null);
    try {
      const usados = Object.fromEntries(Object.entries(valores).map(([k, v]) => [k, Number(v)]));
      await portalService.terminar(id, usados);
      const perdidos = datos.materiales.filter((m) => m.reutilizable && Number(valores[m.id]) < m.salio)
        .map((m) => `${m.salio - Number(valores[m.id])} ${m.nombre.toLowerCase()}`);
      navigate('/portal', { state: { aviso: `Mudanza N° ${id} terminada y finalizada. ¡Buen trabajo!`
        + (perdidos.length ? ` Quedó registrado que no volvieron: ${perdidos.join(', ')}.` : '') } });
    } catch (err) {
      setProblema(err.message);
      setEnviando(false);
    }
  };

  if (loading) return <LoadingSpinner texto="Cargando los materiales..." />;
  if (error) return <ErrorAlert message={error} onRetry={refetch} />;
  return (
    <div className="mx-auto" style={{ maxWidth: 680 }}>
      <p className="mb-2"><Link to="/portal" className="small"><i className="bi bi-arrow-left me-1" />Volver al portal</Link></p>
      <div className="card-panel p-4">
        <h1 className="h4 fw-bold mb-1"><i className="bi bi-flag me-2 text-marca" />Terminar la mudanza N° {id}</h1>
        {problema && <div className="alert alert-danger mt-3">{problema}</div>}
        <form onSubmit={terminar} noValidate>
          {datos.materiales.length ? (
            <>
              <p className="text-muted mt-2">Antes de cerrar, contá los materiales. Ya está cargado lo que salió: cambiá solo lo que no coincida.</p>
              <div className="d-flex flex-column gap-2 mb-4">
                {datos.materiales.map((m) => (
                  <div key={m.id} className="caja-acciones p-3 d-flex flex-wrap justify-content-between align-items-center gap-3">
                    <div>
                      <p className="fw-bold mb-0">{m.nombre}</p>
                      <p className="small text-muted mb-0">Salieron {m.salio} {m.unidad}. {m.reutilizable ? 'Lo que no vuelva queda como pérdida.' : 'Lo que sobre vuelve al depósito.'}</p>
                    </div>
                    <label className="d-flex align-items-center gap-2 small fw-semibold">
                      {m.reutilizable ? 'Volvieron' : 'Se usaron'}
                      <input type="number" className="form-control text-end" style={{ width: 90 }} min="0" max={m.salio} inputMode="numeric"
                        value={valores[m.id] ?? ''} onChange={(e) => setValores({ ...valores, [m.id]: e.target.value })} required />
                    </label>
                  </div>
                ))}
              </div>
            </>
          ) : <p className="mt-2 mb-4">Esta mudanza no llevó materiales del depósito. Confirmá para cerrarla.</p>}
          <div className="d-flex flex-wrap justify-content-end gap-2">
            <Link to="/portal" className="btn btn-outline-secondary">Todavía no</Link>
            <button className="btn btn-primary fw-bold" disabled={enviando}><i className="bi bi-flag me-1" />{enviando ? 'Cerrando...' : 'Terminamos'}</button>
          </div>
          <p className="small text-muted mt-3 mb-0">Al confirmar se guarda la hora de fin y el pedido queda finalizado.</p>
        </form>
      </div>
    </div>
  );
}
