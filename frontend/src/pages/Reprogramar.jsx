import { useEffect, useState } from 'react';
import axios from 'axios';
import { Link, useNavigate, useParams, useSearchParams } from 'react-router-dom';
import { useCarga } from '../hooks/useCarga';
import { adminService } from '../services/adminService';
import { LoadingSpinner } from '../components/LoadingSpinner';
import { ErrorAlert } from '../components/ErrorAlert';

export function Reprogramar() {
  const { id } = useParams();
  const { datos, loading, error } = useCarga((signal) => adminService.getReprogramar(id, {}, signal), [id]);
  if (loading) return <LoadingSpinner />;
  if (error) return <ErrorAlert message={error} />;
  return <Formulario id={id} inicial={datos} />;
}

function Formulario({ id, inicial }) {
  const navigate = useNavigate();
  const [buscar] = useSearchParams(); // ?motivo=... desde el aviso de mudanza atrasada
  const [datos, setDatos] = useState({
    fecha_servicio: inicial.fecha_servicio, hora_servicio: inicial.hora_servicio, vehiculo: inicial.vehiculo,
    motivo: inicial.motivos.includes(buscar.get('motivo')) ? buscar.get('motivo') : '',
    observacion: '', chofer: '', quitar_ocupados: false,
  });
  const [libres, setLibres] = useState({ vehiculos: inicial.vehiculos, motivo: '', buscando: false });
  const [errores, setErrores] = useState({});
  const [enviando, setEnviando] = useState(false);

  // Al cambiar la fecha o la hora se buscan los vehículos libres en el horario nuevo
  useEffect(() => {
    if (!datos.fecha_servicio || !datos.hora_servicio) return undefined;
    const controller = new AbortController();
    setLibres((l) => ({ ...l, buscando: true }));
    adminService.getReprogramar(id, { fecha: datos.fecha_servicio, hora: datos.hora_servicio }, controller.signal)
      .then((r) => setLibres({ vehiculos: r.vehiculos, motivo: r.motivo_sin_vehiculos, buscando: false }))
      .catch((err) => { if (!axios.isCancel(err)) setLibres({ vehiculos: [], motivo: err.message, buscando: false }); });
    return () => controller.abort();
  }, [id, datos.fecha_servicio, datos.hora_servicio]);

  const cambiar = (e) => {
    const { name, value, type, checked } = e.target;
    setDatos({ ...datos, [name]: type === 'checkbox' ? checked : value });
  };
  const vehiculoLibre = libres.vehiculos.some((v) => v.patente === datos.vehiculo);

  const guardar = async (e) => {
    e.preventDefault();
    setEnviando(true);
    setErrores({});
    try {
      await adminService.reprogramar(id, { ...datos, vehiculo: vehiculoLibre ? datos.vehiculo : '' });
      navigate(`/pedidos/${id}`, { state: { aviso: `Pedido N° ${id} reprogramado. Avisale al cliente por WhatsApp.` } });
    } catch (err) {
      setErrores({ __all__: err.message, ...err.errores });
      setEnviando(false);
    }
  };

  const Error = ({ campo }) => (errores[campo] ? <div className="invalid-feedback d-block">{errores[campo]}</div> : null);

  return (
    <form onSubmit={guardar} className="mx-auto" style={{ maxWidth: 700 }} noValidate>
      <Link to={`/pedidos/${id}`} className="small text-decoration-none"><i className="bi bi-arrow-left" /> Volver al pedido</Link>
      <h1 className="h3 fw-bold mt-2 mb-1">Reprogramar el pedido N° {id}</h1>
      <p className="text-muted mb-4">
        Queda en el historial y el cliente lo ve en su pedido. El precio no cambia aunque cambie el camión. Dura unas {inicial.duracion_horas} horas.
      </p>
      {errores.__all__ && <div className="alert alert-danger">{errores.__all__}</div>}

      <div className="card-panel p-4 mb-4">
        <div className="row g-3">
          <div className="col-sm-6">
            <label htmlFor="fecha_servicio" className="form-label">Fecha nueva</label>
            <input id="fecha_servicio" name="fecha_servicio" type="date" className="form-control" value={datos.fecha_servicio} onChange={cambiar} />
            <Error campo="fecha_servicio" />
          </div>
          <div className="col-sm-6">
            <label htmlFor="hora_servicio" className="form-label">Hora nueva</label>
            <input id="hora_servicio" name="hora_servicio" type="time" step={900} className="form-control" value={datos.hora_servicio} onChange={cambiar} />
            <Error campo="hora_servicio" />
          </div>
          <div className="col-12">
            <label htmlFor="vehiculo" className="form-label">Vehículo</label>
            <select id="vehiculo" name="vehiculo" className="form-select" value={vehiculoLibre ? datos.vehiculo : ''}
                    onChange={cambiar} disabled={libres.buscando}>
              <option value="">{libres.buscando ? 'Buscando vehículos libres...' : libres.vehiculos.length ? 'Elegí un vehículo' : 'No hay vehículos libres en ese horario'}</option>
              {libres.vehiculos.map((v) => (
                <option key={v.patente} value={v.patente}>{v.patente} · {v.tipo} · {v.modelo}{v.patente === inicial.vehiculo ? ' (el que tiene)' : ''}</option>
              ))}
            </select>
            <div className={`form-text ${libres.motivo ? 'text-danger' : ''}`}>
              {libres.motivo || 'Cambialo solo si va otro vehículo (por ejemplo, por un problema técnico).'}
            </div>
            <Error campo="vehiculo" />
          </div>
          <div className="col-sm-6">
            <label htmlFor="motivo" className="form-label">Motivo</label>
            <select id="motivo" name="motivo" className="form-select" value={datos.motivo} onChange={cambiar}>
              <option value="">Elegí el motivo</option>
              {inicial.motivos.map((m) => <option key={m} value={m}>{m}</option>)}
            </select>
            <Error campo="motivo" />
          </div>
          <div className="col-sm-6">
            <label htmlFor="chofer" className="form-label">Chofer</label>
            <select id="chofer" name="chofer" className="form-select" value={datos.chofer} onChange={cambiar}>
              <option value="">Dejar el que tiene</option>
              {inicial.choferes.map((c) => <option key={c.id} value={c.id}>{c.nombre}</option>)}
            </select>
            <Error campo="chofer" />
          </div>
          <div className="col-12">
            <label htmlFor="observacion" className="form-label">Observación {datos.motivo === 'Otro' ? <span className="text-danger">(obligatoria con «Otro»)</span> : <span className="text-muted fw-normal">(opcional)</span>}</label>
            <input id="observacion" name="observacion" className="form-control" maxLength={200} autoComplete="off"
                   placeholder="Con «Otro», contá el motivo" value={datos.observacion} onChange={cambiar} />
            <Error campo="observacion" />
          </div>
          {inicial.personal.length > 0 && (
            <div className="col-12">
              <p className="small mb-1"><b>Personal asignado:</b> {inicial.personal.join(', ')}. Tiene que estar libre en el horario nuevo.</p>
              <div className="form-check">
                <input id="quitar_ocupados" name="quitar_ocupados" type="checkbox" className="form-check-input"
                       checked={datos.quitar_ocupados} onChange={cambiar} />
                <label htmlFor="quitar_ocupados" className="form-check-label">Si alguien del personal no está libre en el horario nuevo, sacarlo del pedido</label>
              </div>
              <Error campo="quitar_ocupados" />
            </div>
          )}
        </div>
      </div>

      <div className="d-flex justify-content-end gap-3">
        <Link to={`/pedidos/${id}`} className="btn btn-outline-secondary px-4">Volver</Link>
        <button type="submit" className="btn btn-success px-4 fw-bold" disabled={enviando || !datos.motivo}>
          {enviando ? 'Guardando...' : 'Reprogramar'}
        </button>
      </div>
    </form>
  );
}
