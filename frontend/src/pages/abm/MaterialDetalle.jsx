import { useState } from 'react';
import { Link, useNavigate, useParams } from 'react-router-dom';
import { useCarga } from '../../hooks/useCarga';
import { materialesService } from '../../services/materialesService';
import { Campo } from '../../components/Campo';
import { ConfirmarAccion } from '../../components/ConfirmarAccion';
import { LoadingSpinner } from '../../components/LoadingSpinner';
import { ErrorAlert } from '../../components/ErrorAlert';
import { FilaMovimiento } from './Materiales';

const TIPOS = [{ value: 'Ingreso', label: 'Ingreso (compra o reposición)' }, { value: 'Ajuste', label: 'Ajuste del inventario (después de contar)' }];

/* La ficha de un material: su stock, en qué servicios va y todos sus movimientos. Desde acá se carga
   una compra (Ingreso) o una corrección después de contar (Ajuste, con motivo). El stock no se
   edita a mano: así siempre queda quién lo cambió y por qué. */
export function MaterialDetalle() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [pagina, setPagina] = useState(1);
  const { datos: m, loading, error, refetch } = useCarga((signal) => materialesService.ficha(id, pagina, signal), [id, pagina]);
  const [mov, setMov] = useState({ tipo: 'Ingreso', cantidad: '', observacion: '' });
  const [errores, setErrores] = useState({});
  const [aviso, setAviso] = useState(null);
  const [darDeBaja, setDarDeBaja] = useState(false);

  const registrar = async (e) => {
    e.preventDefault();
    setAviso(null);
    try {
      const r = await materialesService.movimiento(id, { ...mov, cantidad: Number(mov.cantidad) });
      setErrores({});
      setMov({ tipo: mov.tipo, cantidad: '', observacion: '' });
      setAviso({ tipo: 'success', texto: mov.tipo === 'Ingreso' ? `Ingresaron ${mov.cantidad} ${r.unidad}.` : `Ajuste registrado: el stock quedó en ${r.stock}.` });
      setPagina(1);
      refetch();
    } catch (err) {
      setErrores(err.errores || {});
      setAviso({ tipo: 'danger', texto: err.message });
    }
  };
  const baja = async () => {
    await materialesService.baja(id);
    navigate('/materiales', { state: { aviso: `Material «${m.nombre}» dado de baja. Ya no sale en las mudanzas; se reactiva editándolo.` } });
  };

  if (loading) return <LoadingSpinner texto="Cargando el material..." />;
  if (error) return <ErrorAlert message={error} onRetry={refetch} />;
  const ajuste = mov.tipo === 'Ajuste';
  return (
    <div>
      <p className="mb-2"><Link to="/materiales" className="small"><i className="bi bi-arrow-left me-1" />Materiales</Link></p>
      <div className="d-flex flex-wrap justify-content-between align-items-start gap-2 mb-4">
        <div>
          <h1 className="h3 fw-bold mb-1">{m.nombre}</h1>
          <p className="text-muted mb-0">{m.reutilizable
            ? 'Reutilizable: sale con la mudanza y vuelve al «Terminamos». Lo que no vuelve queda como pérdida.'
            : 'Se gasta: sale con la mudanza y al «Terminamos» se descuenta lo usado; lo que sobra vuelve al stock.'}</p>
        </div>
        <div className="d-flex gap-2">
          <Link to={`/materiales/${id}/editar`} className="btn btn-warning">Editar</Link>
          {m.activo && <button type="button" className="btn btn-outline-danger" onClick={() => setDarDeBaja(true)}>Dar de baja</button>}
        </div>
      </div>

      <div className="row g-3 mb-4">
        <div className="col-6 col-xl-3"><div className={`aviso-tarjeta ${m.bajo_minimo ? 'rojo' : 'verde'}`}><span className="aviso-icono"><i className="bi bi-box-seam" /></span>
          <span className="aviso-texto"><b>{m.stock}</b><span>En stock ({m.unidad})</span><small>{m.bajo_minimo ? 'Por debajo del mínimo: conviene reponer' : 'Por encima del mínimo'}</small></span></div></div>
        <div className="col-6 col-xl-3"><div className="aviso-tarjeta gris"><span className="aviso-icono"><i className="bi bi-speedometer2" /></span>
          <span className="aviso-texto"><b>{m.minimo}</b><span>Stock mínimo</span><small>Debajo de esto, avisa al administrador</small></span></div></div>
        {m.reutilizable && <div className="col-6 col-xl-3"><div className={`aviso-tarjeta ${m.en_uso ? 'violeta' : 'apagada'}`}><span className="aviso-icono"><i className="bi bi-truck" /></span>
          <span className="aviso-texto"><b>{m.en_uso}</b><span>Afuera ahora</span><small>En mudanzas que todavía no terminaron</small></span></div></div>}
        <div className="col-6 col-xl-3"><div className="aviso-tarjeta azul"><span className="aviso-icono"><i className="bi bi-tags" /></span>
          <span className="aviso-texto"><b>{m.servicios_que_lo_usan.length}</b><span>Servicios</span>
            <small>{m.servicios_que_lo_usan.map((s) => `${s.servicio} ×${s.cantidad}`).join(', ') || 'No lo usa ningún servicio'}</small></span></div></div>
      </div>

      <div className="row g-4">
        <div className="col-lg-4">
          <form className="card-panel p-4" onSubmit={registrar} noValidate>
            <h2 className="h6 fw-bold mb-3"><i className="bi bi-plus-slash-minus me-1" />Cargar un movimiento</h2>
            {aviso && <div className={`alert alert-${aviso.tipo} py-2 small`}>{aviso.texto}</div>}
            <div className="row g-3">
              <Campo name="tipo" label="Tipo" opciones={TIPOS} value={mov.tipo} error={errores.tipo} onChange={(e) => setMov({ ...mov, tipo: e.target.value })} />
              <Campo name="cantidad" label="Cantidad" tipo="number" min={ajuste ? -100000 : 1} value={mov.cantidad} error={errores.cantidad}
                ayuda={ajuste ? 'Positiva si hay más de lo que dice el sistema, negativa si hay menos.' : undefined}
                onChange={(e) => setMov({ ...mov, cantidad: e.target.value })} />
              <Campo name="observacion" label="Observación" value={mov.observacion} maxLength={200}
                placeholder={ajuste ? 'Ej.: conteo del viernes, había 3 menos' : 'Ej.: compra a proveedor (opcional)'}
                ayuda={ajuste ? 'En un ajuste es obligatoria: contá el motivo.' : undefined}
                onChange={(e) => setMov({ ...mov, observacion: e.target.value })} />
            </div>
            <button className="btn btn-primary fw-bold w-100 mt-3">Registrar</button>
            <p className="form-text mb-0 mt-2">Las salidas y devoluciones de las mudanzas se registran solas con «Empezamos» y «Terminamos».</p>
          </form>
        </div>
        <div className="col-lg-8">
          <h2 className="h6 fw-bold mb-2"><i className="bi bi-clock-history me-1" />Movimientos</h2>
          <div className="card-panel p-0 overflow-hidden">
            <div className="table-responsive">
              <table className="table table-sm align-middle mb-0">
                <thead><tr><th>Fecha</th><th>Movimiento</th><th className="text-end">Stock</th><th>Mudanza</th><th>Quién</th></tr></thead>
                <tbody>
                  {m.movimientos.map((mv) => <FilaMovimiento key={mv.id} mv={mv} />)}
                  {!m.movimientos.length && <tr><td colSpan="5" className="text-center text-muted py-3">Sin movimientos todavía.</td></tr>}
                </tbody>
              </table>
            </div>
          </div>
          {m.paginas > 1 && (
            <nav className="d-flex justify-content-between align-items-center mt-2 small">
              <button type="button" className="btn btn-link btn-sm" disabled={pagina <= 1} onClick={() => setPagina(pagina - 1)}>← Más nuevos</button>
              <span className="text-muted">Página {m.pagina} de {m.paginas}</span>
              <button type="button" className="btn btn-link btn-sm" disabled={pagina >= m.paginas} onClick={() => setPagina(pagina + 1)}>Más viejos →</button>
            </nav>
          )}
        </div>
      </div>

      {darDeBaja && (
        <ConfirmarAccion titulo={`¿Dar de baja «${m.nombre}»?`} boton="Dar de baja" claseBoton="btn-danger"
          accion={baja} onHide={() => setDarDeBaja(false)}>
          Deja de salir en las mudanzas; el historial queda.
        </ConfirmarAccion>
      )}
    </div>
  );
}
