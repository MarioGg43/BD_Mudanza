import { useEffect, useState } from 'react';
import { api } from '../services/api';
import { useCarga } from '../hooks/useCarga';
import { Campo } from '../components/Campo';
import { LoadingSpinner } from '../components/LoadingSpinner';
import { ErrorAlert } from '../components/ErrorAlert';

const miCuenta = {
  datos: async (signal) => (await api.get('/mi-cuenta', { signal })).data,
  guardar: async (datos) => (await api.put('/mi-cuenta', datos)).data,
  cambiarClave: async (datos) => (await api.post('/mi-cuenta/clave', datos)).data,
};

/* «Mi cuenta»: cada persona ve sus datos y cambia su clave. El cliente también cambia su correo y
   su teléfono; al personal se los cambia el administrador (como en Django). */
export function MiCuenta() {
  const { datos: u, loading, error, refetch } = useCarga((signal) => miCuenta.datos(signal), []);
  const [contacto, setContacto] = useState({ correo: '', telefono: '' });
  const [clave, setClave] = useState({ actual: '', nueva: '', confirmar: '' });
  const [errores, setErrores] = useState({});
  const [aviso, setAviso] = useState(null);

  useEffect(() => { if (u) setContacto({ correo: u.correo, telefono: u.telefono }); }, [u]);

  const enviar = (cual, accion) => async (e) => {
    e.preventDefault();
    setAviso(null);
    try {
      await accion();
      setErrores({});
      setAviso({ cual, texto: cual === 'datos' ? 'Guardamos tus datos.' : 'Listo, cambiamos tu clave. La próxima vez entrá con la nueva.' });
      if (cual === 'clave') setClave({ actual: '', nueva: '', confirmar: '' }); else refetch();
    } catch (err) {
      setErrores({ cual, ...err.errores, general: Object.keys(err.errores || {}).length ? null : err.message });
    }
  };

  if (loading) return <LoadingSpinner texto="Cargando tu cuenta..." />;
  if (error) return <ErrorAlert message={error} onRetry={refetch} />;
  const err = (cual, campo) => (errores.cual === cual ? errores[campo] : undefined);
  return (
    <div className="mx-auto" style={{ maxWidth: 820 }}>
      <h1 className="h3 fw-bold mb-1">Mi cuenta</h1>
      <p className="text-muted mb-4">Tus datos y tu clave para entrar al sistema.</p>
      <div className="row g-4">
        <div className="col-md-6">
          <form className="card-panel p-4 h-100" onSubmit={enviar('datos', () => miCuenta.guardar(contacto))} noValidate>
            <h2 className="h6 fw-bold text-uppercase text-muted mb-3">Mis datos</h2>
            {aviso?.cual === 'datos' && <div className="alert alert-success py-2">{aviso.texto}</div>}
            {errores.cual === 'datos' && errores.general && <div className="alert alert-danger py-2">{errores.general}</div>}
            <dl className="row small mb-3">
              <dt className="col-4">Nombre</dt><dd className="col-8 text-capitalize">{u.nombre} {u.apellido}</dd>
              <dt className="col-4">DNI</dt><dd className="col-8">{u.dni}</dd>
              <dt className="col-4">Usuario</dt><dd className="col-8">{u.usuario}</dd>
              <dt className="col-4">Rol</dt><dd className="col-8">{u.rol}</dd>
            </dl>
            {u.edita_datos ? (
              <div className="row g-3">
                <Campo name="correo" label="Correo" tipo="email" value={contacto.correo} error={err('datos', 'correo')}
                  onChange={(e) => setContacto({ ...contacto, correo: e.target.value })} />
                <Campo name="telefono" label="Teléfono" value={contacto.telefono} error={err('datos', 'telefono')}
                  onChange={(e) => setContacto({ ...contacto, telefono: e.target.value })} />
                <div className="col-12 text-end"><button className="btn btn-primary">Guardar mis datos</button></div>
              </div>
            ) : (
              <>
                <dl className="row small mb-2">
                  <dt className="col-4">Correo</dt><dd className="col-8">{u.correo}</dd>
                  <dt className="col-4">Teléfono</dt><dd className="col-8">{u.telefono || '—'}</dd>
                </dl>
                <p className="small text-muted mb-0">Si tu correo o tu teléfono cambiaron, pedíselo al administrador.</p>
              </>
            )}
          </form>
        </div>
        <div className="col-md-6">
          <form className="card-panel p-4 h-100" onSubmit={enviar('clave', () => miCuenta.cambiarClave(clave))} noValidate>
            <h2 className="h6 fw-bold text-uppercase text-muted mb-3">Cambiar mi clave</h2>
            {aviso?.cual === 'clave' && <div className="alert alert-success py-2">{aviso.texto}</div>}
            {errores.cual === 'clave' && errores.general && <div className="alert alert-danger py-2">{errores.general}</div>}
            <div className="row g-3">
              <Campo name="actual" label="Clave actual" tipo="password" value={clave.actual} error={err('clave', 'actual')}
                onChange={(e) => setClave({ ...clave, actual: e.target.value })} autoComplete="current-password" />
              <Campo name="nueva" label="Clave nueva" tipo="password" value={clave.nueva} error={err('clave', 'nueva')}
                ayuda="8 o más caracteres, con mayúscula, minúscula, número y un caracter especial."
                onChange={(e) => setClave({ ...clave, nueva: e.target.value })} autoComplete="new-password" />
              <Campo name="confirmar" label="Repetí la clave nueva" tipo="password" value={clave.confirmar} error={err('clave', 'confirmar')}
                onChange={(e) => setClave({ ...clave, confirmar: e.target.value })} autoComplete="new-password" />
              <div className="col-12 text-end"><button className="btn btn-primary">Cambiar la clave</button></div>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
}
