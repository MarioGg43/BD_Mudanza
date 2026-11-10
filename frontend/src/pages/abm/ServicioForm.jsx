import { Link, useNavigate, useParams } from 'react-router-dom';
import { useCarga } from '../../hooks/useCarga';
import { useFormulario } from '../../hooks/useFormulario';
import { abmService } from '../../services/abmService';
import { Campo, opcionesDe } from '../../components/Campo';
import { LoadingSpinner } from '../../components/LoadingSpinner';
import { ErrorAlert } from '../../components/ErrorAlert';

export function ServicioForm() {
  const { id } = useParams();
  const { datos, loading, error } = useCarga(
    (signal) => (id ? abmService.servicio(id, signal) : abmService.servicios(signal)), [id]);
  if (loading) return <LoadingSpinner />;
  if (error) return <ErrorAlert message={error} />;
  return <Formulario id={id} cargado={datos} />;
}

function Formulario({ id, cargado }) {
  const navigate = useNavigate();
  const { datos, errores, enviando, enviar, campo, cambiar } = useFormulario(id ? {
    Tipo_servicio: cargado.Tipo_servicio, Categoria: cargado.Categoria, Precio_base: String(cargado.Precio_base),
    Duracion_horas: cargado.Duracion_horas == null ? '' : String(cargado.Duracion_horas),
    materiales: cargado.materiales, Activo: cargado.Activo,
  } : { Tipo_servicio: '', Categoria: 'Principal', Precio_base: '', Duracion_horas: '', materiales: '', Activo: true });
  const principal = datos.Categoria === 'Principal';

  const guardar = (e) => {
    e.preventDefault();
    const accion = (d) => (id ? abmService.editarServicio(id, d) : abmService.crearServicio(d));
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
          <Campo label="Materiales que incluye" {...campo('materiales')} ayuda="Separados por coma, con la cantidad por mudanza. Ej.: Mantas ×12, Film ×2" />
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
