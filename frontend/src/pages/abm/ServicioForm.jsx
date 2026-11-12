import { useState } from 'react';
import { Link, useNavigate, useParams } from 'react-router-dom';
import { useCarga } from '../../hooks/useCarga';
import { useFormulario } from '../../hooks/useFormulario';
import { abmService } from '../../services/abmService';
import { materialesService } from '../../services/materialesService';
import { Campo, opcionesDe } from '../../components/Campo';
import { LoadingSpinner } from '../../components/LoadingSpinner';
import { ErrorAlert } from '../../components/ErrorAlert';

export function ServicioForm() {
  const { id } = useParams();
  const { datos, loading, error } = useCarga(
    (signal) => (id ? abmService.servicio(id, signal) : abmService.servicios(signal)), [id]);
  const { datos: catalogo, loading: cargandoCatalogo } = useCarga((signal) => materialesService.catalogo(signal), []);
  if (loading || cargandoCatalogo) return <LoadingSpinner />;
  if (error) return <ErrorAlert message={error} />;
  return <Formulario id={id} cargado={datos} catalogo={catalogo?.materiales || []} />;
}

// «Mantas acolchadas ×12, Film stretch ×2» (lo que manda la API) → filas del formulario
function filasDesde(texto, catalogo) {
  return (texto || '').split(',').map((parte) => parte.trim()).filter(Boolean).map((parte) => {
    const [, nombre, cantidad] = parte.match(/^(.*?)\s*(?:×\s*(\d+))?$/);
    const m = catalogo.find((x) => x.nombre.toLowerCase() === nombre.toLowerCase());
    return { material: m ? String(m.id) : '', cantidad: cantidad || '1' };
  });
}

function Formulario({ id, cargado, catalogo }) {
  const navigate = useNavigate();
  // los materiales que lleva el servicio: material + cantidad por mudanza (como en Django)
  const [filas, setFilas] = useState(() => {
    const iniciales = id ? filasDesde(cargado.materiales, catalogo) : [];
    return iniciales.length ? iniciales : [{ material: '', cantidad: '1' }];
  });
  const cambiarFila = (i, campo, valor) => setFilas(filas.map((f, j) => (j === i ? { ...f, [campo]: valor } : f)));
  const { datos, errores, enviando, enviar, campo, cambiar } = useFormulario(id ? {
    Tipo_servicio: cargado.Tipo_servicio, Categoria: cargado.Categoria, Precio_base: String(cargado.Precio_base),
    Duracion_horas: cargado.Duracion_horas == null ? '' : String(cargado.Duracion_horas),
    materiales: cargado.materiales, Activo: cargado.Activo,
  } : { Tipo_servicio: '', Categoria: 'Principal', Precio_base: '', Duracion_horas: '', materiales: '', Activo: true });
  const principal = datos.Categoria === 'Principal';

  const guardar = (e) => {
    e.preventDefault();
    // la API los recibe como texto: «Mantas acolchadas ×12, Film stretch ×2»
    const materiales = filas.filter((f) => f.material)
      .map((f) => `${catalogo.find((m) => String(m.id) === f.material).nombre} ×${f.cantidad || 1}`).join(', ');
    const accion = (d) => (id ? abmService.editarServicio(id, { ...d, materiales }) : abmService.crearServicio({ ...d, materiales }));
    enviar(accion, (s) => navigate('/servicios', { state: { aviso: `Servicio «${s.Tipo_servicio}» ${id ? 'actualizado' : 'creado'}.` } }));
  };

  return (
    <form onSubmit={guardar} className="mx-auto" style={{ maxWidth: 700 }} noValidate>
      <Link to="/servicios" className="small text-decoration-none"><i className="bi bi-arrow-left" /> Volver a servicios</Link>
      <h1 className="h3 fw-bold mt-2 mb-4">{id ? `Editar «${cargado.Tipo_servicio}»` : 'Nuevo servicio'}</h1>
      {errores.__all__ && <div className="alert alert-danger">{errores.__all__}</div>}
      <div className="card-panel p-4 mb-4">
        <div className="row g-3">
          <Campo label="Tipo de servicio" {...campo('Tipo_servicio')} maxLength={100} placeholder="Ej.: Mudanza local" />
          <Campo label="Categoría" col="col-sm-6" {...campo('Categoria')} opciones={opcionesDe(cargado.categorias)}
                 ayuda={principal ? 'El cliente elige uno por pedido. Lleva recargo según el camión.' : 'Se suma a un principal, a su precio.'} />
          <Campo label="Precio base ($)" col="col-sm-6" tipo="number" min={0} {...campo('Precio_base')}
                 ayuda={principal ? 'Mayor a 0.' : 'Vacío o 0 = sin cargo.'} />
          {principal && (
            <Campo label="Duración (horas)" col="col-sm-6" tipo="number" {...campo('Duracion_horas')}
                   min={cargado.min_horas} max={cargado.max_horas}
                   ayuda={`Cuánto ocupa el vehículo y el personal: de ${cargado.min_horas} a ${cargado.max_horas} horas. Un día de trabajo son unas 10.`} />
          )}
          <div className="col-12">
            <label className="form-label fw-semibold mb-1"><i className="bi bi-box-seam me-1 text-marca" />Materiales que lleva</label>
            <p className="form-text mt-0 mb-2">Lo que se sugiere llevar en cada mudanza con este servicio. Sale del stock cuando el chofer toca «Empezamos». Si falta un material, cargalo en <Link to="/materiales">Materiales</Link>.</p>
            {errores.materiales && <div className="alert alert-danger py-2 small">{errores.materiales}</div>}
            {filas.map((f, i) => (
              <div key={i} className="row g-2 align-items-center mb-2">
                <div className="col-7">
                  <select className="form-select" aria-label="Material" value={f.material} onChange={(e) => cambiarFila(i, 'material', e.target.value)}>
                    <option value="">Elegí un material</option>
                    {catalogo.map((m) => <option key={m.id} value={m.id}>{m.nombre} ({m.unidad})</option>)}
                  </select>
                </div>
                <div className="col-3">
                  <input type="number" className="form-control" aria-label="Cantidad por mudanza" min={1} max={500}
                    value={f.cantidad} onChange={(e) => cambiarFila(i, 'cantidad', e.target.value)} />
                </div>
                <div className="col-2">
                  <button type="button" className="btn btn-sm btn-outline-danger" aria-label="Quitar" onClick={() => setFilas(filas.filter((_, j) => j !== i))}>
                    <i className="bi bi-x-lg" />
                  </button>
                </div>
              </div>
            ))}
            {filas.length < 12 && (
              <button type="button" className="btn btn-sm btn-outline-secondary" onClick={() => setFilas([...filas, { material: '', cantidad: '1' }])}>
                <i className="bi bi-plus-lg" /> Otro material
              </button>
            )}
          </div>
          <div className="col-12">
            <div className="form-check">
              <input id="Activo" name="Activo" type="checkbox" className="form-check-input" checked={datos.Activo} onChange={cambiar} />
              <label htmlFor="Activo" className="form-check-label">Activo (se ofrece en los pedidos nuevos)</label>
            </div>
          </div>
        </div>
      </div>
      <div className="d-flex justify-content-end gap-3">
        <Link to="/servicios" className="btn btn-outline-secondary px-4">Cancelar</Link>
        <button type="submit" className="btn btn-success px-4 fw-bold" disabled={enviando}>{enviando ? 'Guardando...' : 'Guardar'}</button>
      </div>
    </form>
  );
}
