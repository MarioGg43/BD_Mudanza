import { useState } from 'react';
import { Link, useNavigate, useParams } from 'react-router-dom';
import { usePedido } from '../hooks/usePedido';
import { pedidoService } from '../services/pedidoService';
import { LoadingSpinner } from '../components/LoadingSpinner';
import { ErrorAlert } from '../components/ErrorAlert';
import { diaSemana, fecha } from '../utils/formato';

export function CancelarPedido() {
  const { id } = useParams();
  const navigate = useNavigate();
  const { pedido, loading, error } = usePedido(id);
  const [motivo, setMotivo] = useState('');
  const [enviando, setEnviando] = useState(false);
  const [errorEnvio, setErrorEnvio] = useState(null);

  if (loading) return <LoadingSpinner />;
  if (error) return <ErrorAlert message={error} />;

  const handleSubmit = async (e) => {
    e.preventDefault();
    setEnviando(true);
    setErrorEnvio(null);
    try {
      await pedidoService.cancelar(id, motivo.trim());
      navigate(`/pedidos/${id}`, { state: { aviso: `Cancelaste la mudanza del pedido N° ${id}.` } });
    } catch (err) {
      setErrorEnvio(err.errores.motivo || err.message);
      setEnviando(false);
    }
  };

  return (
    <div className="mx-auto" style={{ maxWidth: 600 }}>
      <h1 className="h3 fw-bold mb-1">Cancelar la mudanza del pedido N° {pedido.id}</h1>
      <p className="text-muted mb-4">
        {diaSemana(pedido.fecha_servicio)} {fecha(pedido.fecha_servicio)} {pedido.horario}. El pedido queda «Anulado» con tu motivo.
        Si después querés mudarte igual, podés pedir una mudanza nueva.
      </p>
      {!pedido.puede_cambiar ? (
        <div className="alert alert-warning">Ya no se puede cancelar: faltan menos de 24 horas o el pedido no está activo. Comunicate con la empresa.</div>
      ) : (
        <form onSubmit={handleSubmit} className="card-panel p-4" noValidate>
          <label htmlFor="motivo" className="form-label">¿Por qué cancelás la mudanza?</label>
          <textarea id="motivo" rows={3} maxLength={200} className={`form-control ${errorEnvio ? 'is-invalid' : ''}`}
                    value={motivo} onChange={(e) => setMotivo(e.target.value)} />
          {errorEnvio && <div className="invalid-feedback">{errorEnvio}</div>}
          <div className="d-flex justify-content-end gap-3 mt-3">
            <Link to={`/pedidos/${id}`} className="btn btn-outline-secondary">Volver</Link>
            <button type="submit" className="btn btn-danger fw-bold" disabled={enviando || motivo.trim().length < 5}>
              {enviando ? 'Cancelando...' : 'Cancelar la mudanza'}
            </button>
          </div>
        </form>
      )}
    </div>
  );
}
