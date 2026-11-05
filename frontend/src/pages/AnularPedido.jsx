import { useState } from 'react';
import { Link, useNavigate, useParams } from 'react-router-dom';
import { usePedido } from '../hooks/usePedido';
import { adminService } from '../services/adminService';
import { LoadingSpinner } from '../components/LoadingSpinner';
import { ErrorAlert } from '../components/ErrorAlert';
import { diaSemana, fecha } from '../utils/formato';

// El administrador anula un pedido (queda «Anulado» con el motivo, la fecha y quién fue)
export function AnularPedido() {
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
      await adminService.anular(id, motivo.trim());
      navigate(`/pedidos/${id}`, { state: { aviso: `Pedido N° ${id} anulado. El vehículo queda libre en ese horario.` } });
    } catch (err) {
      setErrorEnvio(err.errores.motivo || err.message);
      setEnviando(false);
    }
  };

  return (
    <div className="mx-auto" style={{ maxWidth: 600 }}>
      <h1 className="h3 fw-bold mb-1">Anular el pedido N° {pedido.id}</h1>
      <p className="text-muted mb-4">
        {pedido.cliente} · {diaSemana(pedido.fecha_servicio)} {fecha(pedido.fecha_servicio)} {pedido.horario}.
        El pedido no se borra: queda «Anulado» con el motivo, la fecha y quién lo anuló.
      </p>
      {!pedido.gestion?.puede_anular ? (
        <div className="alert alert-warning">El pedido está {pedido.estado.toLowerCase()}: ya no se puede anular.</div>
      ) : (
        <form onSubmit={handleSubmit} className="card-panel p-4" noValidate>
          <label htmlFor="motivo" className="form-label">Motivo de la anulación</label>
          <textarea id="motivo" rows={3} maxLength={200} className={`form-control ${errorEnvio ? 'is-invalid' : ''}`}
                    value={motivo} onChange={(e) => setMotivo(e.target.value)} />
          {errorEnvio && <div className="invalid-feedback">{errorEnvio}</div>}
          <div className="d-flex justify-content-end gap-3 mt-3">
            <Link to={`/pedidos/${id}`} className="btn btn-outline-secondary">Volver</Link>
            <button type="submit" className="btn btn-danger fw-bold" disabled={enviando || motivo.trim().length < 5}>
              {enviando ? 'Anulando...' : 'Anular pedido'}
            </button>
          </div>
        </form>
      )}
    </div>
  );
}
