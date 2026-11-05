import { useState } from 'react';
import { useCarga } from '../../hooks/useCarga';
import { abmService } from '../../services/abmService';
import { ConfirmarAccion } from '../../components/ConfirmarAccion';
import { LoadingSpinner } from '../../components/LoadingSpinner';
import { ErrorAlert } from '../../components/ErrorAlert';

/* El catálogo de objetos del que el cliente elige qué hay que llevar. Se agrega arriba, y cada
   objeto se renombra, se da de baja o se reactiva desde su fila. «Otro» es fijo. */
export function Objetos() {
  const { datos, loading, error, refetch } = useCarga((signal) => abmService.objetos(signal), []);
  const [nuevo, setNuevo] = useState('');
  const [errorNuevo, setErrorNuevo] = useState(null);
  const [aviso, setAviso] = useState(null);
  const [editando, setEditando] = useState(null); // { objeto, nombre }
  const [baja, setBaja] = useState(null);
  const [buscar, setBuscar] = useState('');

  if (loading) return <LoadingSpinner />;
  if (error) return <ErrorAlert message={error} onRetry={refetch} />;

  const agregar = async (e) => {
    e.preventDefault();
    setErrorNuevo(null);
    try {
      const o = await abmService.crearObjeto({ nom_objeto: nuevo, Activo: true });
      setAviso(`«${o.nom_objeto}» agregado a la lista.`);
      setNuevo('');
      refetch();
    } catch (err) {
      setErrorNuevo(err.errores.nom_objeto || err.message);
    }
  };

  const renombrar = async () => {
    try {
      await abmService.editarObjeto(editando.objeto.id, { nom_objeto: editando.nombre, Activo: editando.objeto.Activo });
    } catch (err) {
      throw new Error(err.errores?.nom_objeto || err.message); // se muestra dentro de la ventana
    }
    setAviso(`Objeto renombrado a «${editando.nombre.trim()}».`);
    setEditando(null);
    refetch();
  };

  const reactivar = async (o) => {
    await abmService.editarObjeto(o.id, { nom_objeto: o.nom_objeto, Activo: true });
    setAviso(`«${o.nom_objeto}» vuelve a estar en la lista.`);
    refetch();
  };

  const darDeBaja = async () => {
    await abmService.bajaObjeto(baja.id);
    setAviso(`«${baja.nom_objeto}» dado de baja.`);
    setBaja(null);
    refetch();
  };

  const visibles = datos.objetos.filter((o) => o.nom_objeto.toLowerCase().includes(buscar.trim().toLowerCase()));

  return (
    <div className="mx-auto" style={{ maxWidth: 800 }}>
      <h1 className="h3 fw-bold mb-1">Objetos</h1>
      <p className="text-muted mb-4">La lista de la que el cliente elige qué hay que llevar. No se repiten nombres: «silla» y «Sillas» cuentan como el mismo.</p>
      {aviso && <div className="alert alert-success">{aviso}</div>}

      <form onSubmit={agregar} className="card-panel p-3 mb-3" noValidate>
        <label htmlFor="nuevo" className="form-label">Agregar un objeto</label>
        <div className="input-group">
          <input id="nuevo" className={`form-control ${errorNuevo ? 'is-invalid' : ''}`} maxLength={100} placeholder="Ej.: Piano"
                 value={nuevo} onChange={(e) => setNuevo(e.target.value)} />
          <button type="submit" className="btn btn-success fw-bold" disabled={!nuevo.trim()}><i className="bi bi-plus-lg me-1" />Agregar</button>
        </div>
        {errorNuevo && <div className="invalid-feedback d-block">{errorNuevo}</div>}
      </form>

      <input type="search" className="form-control mb-2" placeholder="Buscar en la lista..." aria-label="Buscar objeto"
             value={buscar} onChange={(e) => setBuscar(e.target.value)} />
      <div className="card-panel p-0 overflow-hidden">
        <table className="table align-middle mb-0">
          <thead><tr><th>Objeto</th><th className="text-end">Veces pedido</th><th className="text-end">Acciones</th></tr></thead>
          <tbody>
            {visibles.map((o) => (
              <tr key={o.id} className={o.Activo ? '' : 'tarjeta-pasada'}>
                <td>{o.nom_objeto}{o.otro && <span className="badge text-bg-light border ms-2">fijo</span>}{!o.Activo && <span className="estado estado-anulado ms-2">De baja</span>}</td>
                <td className="text-end">{o.usos}</td>
                <td className="text-end text-nowrap">
                  {!o.otro && (o.Activo ? (
                    <>
                      <button type="button" className="btn btn-sm btn-outline-secondary me-1" onClick={() => setEditando({ objeto: o, nombre: o.nom_objeto })}>Renombrar</button>
                      <button type="button" className="btn btn-sm btn-outline-danger" onClick={() => setBaja(o)}>Dar de baja</button>
                    </>
                  ) : (
                    <button type="button" className="btn btn-sm btn-outline-success" onClick={() => reactivar(o)}>Reactivar</button>
                  ))}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {editando && (
        <ConfirmarAccion titulo={`Renombrar «${editando.objeto.nom_objeto}»`} boton="Guardar" accion={renombrar} onHide={() => setEditando(null)}>
          <label htmlFor="renombrar" className="form-label">Nombre nuevo</label>
          <input id="renombrar" className="form-control" maxLength={100} value={editando.nombre} autoFocus
                 onChange={(e) => setEditando({ ...editando, nombre: e.target.value })} />
        </ConfirmarAccion>
      )}
      {baja && (
        <ConfirmarAccion titulo={`Dar de baja «${baja.nom_objeto}»`} boton="Dar de baja" claseBoton="btn-danger" accion={darDeBaja} onHide={() => setBaja(null)}>
          <p className="mb-0">Deja de aparecer en la lista para los pedidos nuevos. Los {baja.usos} pedido(s) que ya lo tienen lo conservan.</p>
        </ConfirmarAccion>
      )}
    </div>
  );
}
