import { Link, useNavigate, useParams } from 'react-router-dom';
import { useCarga } from '../../hooks/useCarga';
import { useFormulario } from '../../hooks/useFormulario';
import { materialesService } from '../../services/materialesService';
import { Campo } from '../../components/Campo';
import { LoadingSpinner } from '../../components/LoadingSpinner';
import { ErrorAlert } from '../../components/ErrorAlert';

// Alta y edición de un material. El stock no se edita acá: cambia con ingresos, salidas y ajustes.
export function MaterialForm() {
  const { id } = useParams();
  if (!id) return <Formulario inicial={{ nom_material: '', unidad_material: 'unidades', stock_min_material: '0', stock_inicial: '', reutilizable: false, Activo: true }} />;
  return <Edicion id={id} />;
}

function Edicion({ id }) {
  const { datos, loading, error } = useCarga((signal) => materialesService.ficha(id, 1, signal), [id]);
  if (loading) return <LoadingSpinner />;
  if (error) return <ErrorAlert message={error} />;
  return (
    <Formulario id={id} material={datos} inicial={{
      nom_material: datos.nombre, unidad_material: datos.unidad, stock_min_material: String(datos.minimo),
      reutilizable: datos.reutilizable, Activo: datos.activo }} />
  );
}

function Formulario({ id, material, inicial }) {
  const navigate = useNavigate();
  const { datos, errores, enviando, enviar, campo, cambiar } = useFormulario(inicial);
  const guardar = (e) => {
    e.preventDefault();
    const accion = (d) => (id ? materialesService.editar(id, d) : materialesService.crear(d));
    enviar(accion, (m) => navigate(`/materiales/${m.id}`));
  };
  const volver = id ? `/materiales/${id}` : '/materiales';

  return (
    <form onSubmit={guardar} className="mx-auto" style={{ maxWidth: 640 }} noValidate>
      <Link to={volver} className="small text-decoration-none"><i className="bi bi-arrow-left" /> Volver</Link>
      <h1 className="h3 fw-bold mt-2 mb-4">{id ? `Editar «${material.nombre}»` : 'Nuevo material'}</h1>
      {errores.__all__ && <div className="alert alert-danger">{errores.__all__}</div>}
      <div className="card-panel p-4 mb-4">
        <div className="row g-3">
          <Campo label="Nombre" {...campo('nom_material')} maxLength={60} placeholder="Ej.: Mantas acolchadas" />
          <Campo label="Unidad (unidades, rollos, kits…)" col="col-sm-6" {...campo('unidad_material')} maxLength={20} />
          <Campo label="Stock mínimo" col="col-sm-6" tipo="number" min={0} {...campo('stock_min_material')}
                 ayuda="Si el stock baja de este número, el administrador recibe un aviso." />
          {!id && <Campo label="Stock inicial" col="col-sm-6" tipo="number" min={0} {...campo('stock_inicial')}
                         ayuda="Lo que hay hoy. Se registra como un ingreso." />}
          <div className="col-12">
            <div className="form-check">
              <input id="reutilizable" name="reutilizable" type="checkbox" className="form-check-input" checked={datos.reutilizable} onChange={cambiar} />
              <label htmlFor="reutilizable" className="form-check-label">Es reutilizable (sale con la mudanza y vuelve)</label>
            </div>
            <div className="form-check">
              <input id="Activo" name="Activo" type="checkbox" className="form-check-input" checked={datos.Activo} onChange={cambiar} />
              <label htmlFor="Activo" className="form-check-label">Activo (se puede usar en los servicios)</label>
            </div>
          </div>
          {id && <p className="form-text mb-0">El stock ({material.stock} {material.unidad}) no se edita acá: cargá un ingreso o un ajuste desde la ficha, así queda registrado quién y por qué.</p>}
        </div>
      </div>
      <div className="d-flex justify-content-end gap-3">
        <Link to={volver} className="btn btn-outline-secondary px-4">Cancelar</Link>
        <button type="submit" className="btn btn-success px-4 fw-bold" disabled={enviando}>{enviando ? 'Guardando...' : 'Guardar'}</button>
      </div>
    </form>
  );
}
