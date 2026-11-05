import { Link, useNavigate, useParams } from 'react-router-dom';
import { useCarga } from '../../hooks/useCarga';
import { useFormulario } from '../../hooks/useFormulario';
import { abmService } from '../../services/abmService';
import { Campo, opcionesDe } from '../../components/Campo';
import { LoadingSpinner } from '../../components/LoadingSpinner';
import { ErrorAlert } from '../../components/ErrorAlert';

const VACIO = { patente: '', marca_modelo: '', tipo_vehiculo: '', capacidad_kg: '', capacidad_m3: '', estado: 'Disponible',
                kilometraje: '0', anio: '', chofer_asignado: '', observaciones: '' };

// Alta (/vehiculos/nuevo) y modificación (/vehiculos/:patente/editar). Las opciones salen de la API.
export function VehiculoForm() {
  const { patente } = useParams();
  const { datos, loading, error } = useCarga(
    (signal) => (patente ? abmService.vehiculo(patente, signal) : abmService.vehiculos(signal)), [patente]);
  if (loading) return <LoadingSpinner />;
  if (error) return <ErrorAlert message={error} />;
  return <Formulario patente={patente} cargado={datos} />;
}

function Formulario({ patente, cargado }) {
  const navigate = useNavigate();
  const inicial = patente
    ? Object.fromEntries(Object.keys(VACIO).map((k) => [k, cargado[k] == null ? '' : String(cargado[k])]))
    : VACIO;
  const { errores, enviando, enviar, campo } = useFormulario(inicial);

  const guardar = (e) => {
    e.preventDefault();
    const accion = (d) => (patente ? abmService.editarVehiculo(patente, d) : abmService.crearVehiculo(d));
    enviar(accion, (v) => navigate(`/vehiculos/${v.patente}`, {
      state: { aviso: `Vehículo ${v.patente} ${patente ? 'actualizado' : 'registrado'}.` } }));
  };

  return (
    <form onSubmit={guardar} className="mx-auto" style={{ maxWidth: 800 }} noValidate>
      <Link to={patente ? `/vehiculos/${patente}` : '/vehiculos'} className="small text-decoration-none"><i className="bi bi-arrow-left" /> Volver</Link>
      <h1 className="h3 fw-bold mt-2 mb-4">{patente ? `Editar el vehículo ${patente}` : 'Nuevo vehículo'}</h1>
      {errores.__all__ && <div className="alert alert-danger">{errores.__all__}</div>}
      <div className="card-panel p-4 mb-4">
        <div className="row g-3">
          <Campo label="Patente" col="col-sm-4" {...campo('patente')} disabled={Boolean(patente)} maxLength={15}
                 ayuda={patente ? 'La patente no se cambia.' : 'Se guarda en mayúsculas y sin espacios.'} />
          <Campo label="Marca y modelo" col="col-sm-8" {...campo('marca_modelo')} maxLength={100} />
          <Campo label="Tipo" col="col-sm-4" {...campo('tipo_vehiculo')} opciones={opcionesDe(cargado.tipos)} vacio="Elegí el tamaño"
                 ayuda="Mediano +25 % y Grande +50 % sobre el servicio principal." />
          <Campo label="Capacidad (kg)" col="col-sm-4" tipo="number" {...campo('capacidad_kg')} min={100} max={40000} />
          <Campo label="Capacidad (m³)" col="col-sm-4" tipo="number" {...campo('capacidad_m3')} min={1} max={100} />
          <Campo label="Estado" col="col-sm-4" {...campo('estado')} opciones={opcionesDe(cargado.estados)} />
          <Campo label="Kilometraje" col="col-sm-4" tipo="number" {...campo('kilometraje')} min={0} />
          <Campo label="Año" col="col-sm-4" tipo="number" {...campo('anio')} min={1980} />
          <Campo label="Chofer habitual" {...campo('chofer_asignado')} vacio="Sin chofer habitual"
                 opciones={cargado.choferes.map((c) => ({ value: String(c.id), label: c.nombre }))}
                 ayuda="Se sugiere al asignar el personal de sus mudanzas." />
          <Campo label="Observaciones" tipo="textarea" {...campo('observaciones')} />
        </div>
      </div>
      <div className="d-flex justify-content-end gap-3">
        <Link to={patente ? `/vehiculos/${patente}` : '/vehiculos'} className="btn btn-outline-secondary px-4">Cancelar</Link>
        <button type="submit" className="btn btn-success px-4 fw-bold" disabled={enviando}>{enviando ? 'Guardando...' : 'Guardar'}</button>
      </div>
    </form>
  );
}
