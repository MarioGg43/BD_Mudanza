import { useEffect, useState } from 'react';
import axios from 'axios';
import { Link, useNavigate } from 'react-router-dom';
import { useCarga } from '../../hooks/useCarga';
import { useFormulario } from '../../hooks/useFormulario';
import { abmService } from '../../services/abmService';
import { Campo } from '../../components/Campo';
import { LoadingSpinner } from '../../components/LoadingSpinner';
import { ErrorAlert } from '../../components/ErrorAlert';

export function UsuarioNuevo() {
  const { datos, loading, error } = useCarga((signal) => abmService.usuarios(signal), []);
  if (loading) return <LoadingSpinner />;
  if (error) return <ErrorAlert message={error} />;
  return <Formulario roles={datos.roles} />;
}

function Formulario({ roles }) {
  const navigate = useNavigate();
  const { datos, errores, enviando, enviar, campo } = useFormulario(
    { dni: '', apellido: '', nombre: '', correo: '', clave: '', id_rol: '' });
  const [usuario, setUsuario] = useState('');

  // El nombre de usuario es automático (apellido + inicial): se muestra cómo va a quedar
  useEffect(() => {
    if (!datos.apellido.trim() || !datos.nombre.trim()) { setUsuario(''); return undefined; }
    const controller = new AbortController();
    abmService.nombreUsuario(datos.apellido, datos.nombre, controller.signal)
      .then((r) => setUsuario(r.usuario))
      .catch((err) => { if (!axios.isCancel(err)) setUsuario(''); });
    return () => controller.abort();
  }, [datos.apellido, datos.nombre]);

  const guardar = (e) => {
    e.preventDefault();
    enviar(abmService.crearUsuario, (u) => navigate('/usuarios', {
      state: { aviso: `Usuario ${u.usuario} creado. Al entrar por primera vez tiene que cambiar la clave.` } }));
  };

  return (
    <form onSubmit={guardar} className="mx-auto" style={{ maxWidth: 700 }} noValidate>
      <Link to="/usuarios" className="small text-decoration-none"><i className="bi bi-arrow-left" /> Volver a usuarios</Link>
      <h1 className="h3 fw-bold mt-2 mb-1">Nuevo usuario</h1>
      <p className="text-muted mb-4">Para el personal. Los clientes se registran solos desde la página.</p>
      {errores.__all__ && <div className="alert alert-danger">{errores.__all__}</div>}
      <div className="card-panel p-4 mb-4">
        <div className="row g-3">
          <Campo label="DNI" col="col-sm-4" inputMode="numeric" {...campo('dni')} />
          <Campo label="Apellido" col="col-sm-4" {...campo('apellido')} maxLength={100} />
          <Campo label="Nombre" col="col-sm-4" {...campo('nombre')} maxLength={100} />
          <div className="col-12">
            <p className="small mb-0"><i className="bi bi-person-badge me-1 text-marca" />Usuario: <b>{usuario || '—'}</b> <span className="text-muted">(se arma solo con el apellido y la inicial)</span></p>
          </div>
          <Campo label="Correo" tipo="email" {...campo('correo')} />
          <Campo label="Clave provisoria" col="col-sm-6" tipo="password" autoComplete="new-password" {...campo('clave')}
                 ayuda="8 o más caracteres, con mayúscula, minúscula, número y un caracter especial. Al entrar la tiene que cambiar." />
          <Campo label="Rol" col="col-sm-6" {...campo('id_rol')} vacio="Elegí el rol"
                 opciones={roles.map((r) => ({ value: String(r.id), label: r.nombre }))}
                 ayuda="Solo los roles que podés asignar." />
        </div>
      </div>
      <div className="d-flex justify-content-end gap-3">
        <Link to="/usuarios" className="btn btn-outline-secondary px-4">Cancelar</Link>
        <button type="submit" className="btn btn-success px-4 fw-bold" disabled={enviando}>{enviando ? 'Creando...' : 'Crear usuario'}</button>
      </div>
    </form>
  );
}
