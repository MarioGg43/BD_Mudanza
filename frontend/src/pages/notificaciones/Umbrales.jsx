import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { useCarga } from '../../hooks/useCarga';
import { analisisService } from '../../services/analisisService';
import { Campo } from '../../components/Campo';
import { LoadingSpinner } from '../../components/LoadingSpinner';
import { ErrorAlert } from '../../components/ErrorAlert';

/* Los umbrales de las reglas de notificación (tabla CONFIGURACION). No están en el código: se
   cambian acá y cada cambio queda en la auditoría. «Evaluar ahora» corre la tarea programada. */
export function Umbrales() {
  const { datos, loading, error, refetch } = useCarga((signal) => analisisService.configuracion(signal), []);
  const [valores, setValores] = useState({});
  const [errores, setErrores] = useState({});
  const [aviso, setAviso] = useState(null);
  const [guardando, setGuardando] = useState(false);

  useEffect(() => {
    if (datos) setValores(Object.fromEntries(datos.parametros.map((p) => [p.clave, p.valor])));
  }, [datos]);

  const guardar = async (e) => {
    e.preventDefault();
    setGuardando(true);
    setAviso(null);
    try {
      await analisisService.guardarConfiguracion(valores);
      setErrores({});
      setAviso({ tipo: 'success', texto: 'Guardamos los umbrales. Las reglas los usan desde ahora.' });
      refetch();
    } catch (err) {
      setErrores(err.errores || {});
      setAviso({ tipo: 'danger', texto: err.message });
    } finally {
      setGuardando(false);
    }
  };
  const evaluar = async () => {
    const r = await analisisService.evaluarAlertas();
    const detalle = Object.entries(r.detalle).map(([regla, n]) => `${regla}: ${n}`).join(', ');
    setAviso({ tipo: 'success', texto: `Evaluamos las reglas programadas: ${r.total} aviso${r.total !== 1 ? 's' : ''} nuevo${r.total !== 1 ? 's' : ''} (${detalle}).` });
    window.dispatchEvent(new Event('notificaciones-cambiaron'));
  };

  if (loading) return <LoadingSpinner texto="Cargando los umbrales..." />;
  if (error) return <ErrorAlert message={error} onRetry={refetch} />;
  return (
    <div className="mx-auto" style={{ maxWidth: 720 }}>
      <p className="mb-2"><Link to="/notificaciones" className="small"><i className="bi bi-arrow-left me-1" />Notificaciones</Link></p>
      <div className="d-flex flex-wrap justify-content-between align-items-start gap-2 mb-3">
        <div>
          <h1 className="h3 fw-bold mb-1">Umbrales de alertas</h1>
          <p className="text-muted mb-0">Cuándo avisa cada regla. Los cambios quedan en la auditoría.</p>
        </div>
        <button type="button" className="btn btn-outline-secondary" onClick={evaluar}><i className="bi bi-play-circle me-1" />Evaluar ahora</button>
      </div>
      {aviso && <div className={`alert alert-${aviso.tipo}`}>{aviso.texto}</div>}
      <form className="card-panel p-4" onSubmit={guardar} noValidate>
        <div className="row g-3">
          {datos.parametros.map((p) => (
            <Campo key={p.clave} name={p.clave} label={p.descripcion} value={valores[p.clave] ?? ''} error={errores[p.clave]}
              tipo={p.limites ? 'number' : 'email'} min={p.limites?.[0]} max={p.limites?.[1]}
              ayuda={p.limites ? `De ${p.limites[0]} a ${p.limites[1]}.` : 'Vacío: no se manda el correo a la empresa.'}
              onChange={(e) => setValores({ ...valores, [p.clave]: e.target.value })} />
          ))}
        </div>
        <div className="d-flex justify-content-end mt-4">
          <button className="btn btn-primary px-4" disabled={guardando}>{guardando ? 'Guardando...' : 'Guardar'}</button>
        </div>
      </form>
    </div>
  );
}
