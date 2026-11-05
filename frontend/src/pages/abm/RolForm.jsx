import { Link, useNavigate, useParams } from 'react-router-dom';
import { useCarga } from '../../hooks/useCarga';
import { useFormulario } from '../../hooks/useFormulario';
import { abmService } from '../../services/abmService';
import { Campo } from '../../components/Campo';
import { LoadingSpinner } from '../../components/LoadingSpinner';
import { ErrorAlert } from '../../components/ErrorAlert';

export function RolForm() {
  const { id } = useParams();
  const { datos, loading, error } = useCarga((signal) => abmService.roles(signal), []);
  if (loading) return <LoadingSpinner />;
  if (error) return <ErrorAlert message={error} />;
  const rol = id ? datos.roles.find((r) => String(r.id) === id) : null;
  if (id && !rol) return <ErrorAlert message="Ese rol no existe." />;
  return <Formulario rol={rol} catalogo={datos.catalogo} />;
}

function Formulario({ rol, catalogo }) {
  const navigate = useNavigate();
  const { datos, setDatos, errores, enviando, enviar, campo } = useFormulario(
    { nombre: rol?.nombre ?? '', descripcion: rol?.descripcion ?? '', permisos: rol?.permisos ?? [] });
  // los permisos agrupados por área (Usuarios, Pedidos, Vehículos...)
  const areas = [...new Set(catalogo.map((c) => c.area))];

  const alternar = (codigo) => setDatos((d) => ({
    ...d, permisos: d.permisos.includes(codigo) ? d.permisos.filter((p) => p !== codigo) : [...d.permisos, codigo] }));

  const guardar = (e) => {
    e.preventDefault();
    const accion = (d) => (rol ? abmService.editarRol(rol.id, d) : abmService.crearRol(d));
    enviar(accion, (r) => navigate('/roles', { state: { aviso: `Rol «${r.nombre}» guardado.` } }));
  };

  return (
    <form onSubmit={guardar} className="mx-auto" style={{ maxWidth: 900 }} noValidate>
      <Link to="/roles" className="small text-decoration-none"><i className="bi bi-arrow-left" /> Volver a roles</Link>
      <h1 className="h3 fw-bold mt-2 mb-4">{rol ? `Editar «${rol.nombre}»` : 'Nuevo rol'}</h1>
      {errores.__all__ && <div className="alert alert-danger">{errores.__all__}</div>}
      <div className="card-panel p-4 mb-3">
        <div className="row g-3">
          <Campo label="Nombre" col="col-sm-5" {...campo('nombre')} maxLength={100} disabled={rol?.del_sistema}
                 ayuda={rol?.del_sistema ? 'Es un rol del sistema: el nombre no se cambia.' : undefined} />
          <Campo label="Descripción" col="col-sm-7" {...campo('descripcion')} maxLength={100} />
        </div>
      </div>
      <div className="card-panel p-4 mb-4">
        <h2 className="h6 fw-bold text-uppercase text-muted mb-3">Permisos</h2>
        {errores.permisos && <div className="alert alert-danger py-2">{errores.permisos}</div>}
        <div className="row row-cols-1 row-cols-md-2 g-3">
          {areas.map((area) => (
            <div key={area} className="col">
              <p className="fw-semibold mb-1">{area}</p>
              {catalogo.filter((c) => c.area === area).map((c) => (
                <div key={c.codigo} className="form-check">
                  <input id={c.codigo} type="checkbox" className="form-check-input"
                         checked={datos.permisos.includes(c.codigo)} onChange={() => alternar(c.codigo)} />
                  <label htmlFor={c.codigo} className="form-check-label">{c.descripcion}</label>
                </div>
              ))}
            </div>
          ))}
        </div>
      </div>
      <div className="d-flex justify-content-end gap-3">
        <Link to="/roles" className="btn btn-outline-secondary px-4">Cancelar</Link>
        <button type="submit" className="btn btn-success px-4 fw-bold" disabled={enviando}>{enviando ? 'Guardando...' : 'Guardar rol'}</button>
      </div>
    </form>
  );
}
