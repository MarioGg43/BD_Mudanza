import { useState } from 'react';
import { Link, useNavigate, useParams } from 'react-router-dom';
import { useCatalogo } from '../hooks/useCatalogo';
import { usePedido } from '../hooks/usePedido';
import { useVehiculosLibres } from '../hooks/useVehiculosLibres';
import { pedidoService } from '../services/pedidoService';
import { ModalObjeto, etiqueta } from '../components/ModalObjeto';
import { LoadingSpinner } from '../components/LoadingSpinner';
import { ErrorAlert } from '../components/ErrorAlert';
import { TarjetaOpcion } from '../components/TarjetaOpcion';
import { dinero, fecha } from '../utils/formato';

// Un ícono según el nombre del servicio (los servicios los carga el administrador)
function iconoServicio(nombre) {
  const n = nombre.toLowerCase();
  if (n.includes('flete')) return 'bi-box-seam';
  if (n.includes('nacional')) return 'bi-signpost-split';
  if (n.includes('mudanza')) return 'bi-house-door';
  if (n.includes('embalaje')) return 'bi-boxes';
  if (n.includes('armado')) return 'bi-tools';
  return 'bi-stars';
}

const SEP = ' — '; // separa el nombre de un objeto «Otro» de su detalle en la observación

// Inventario del servidor → filas de la lista ({ id, nombre, nuevo, cantidad, fragil, detalle })
function desdeServidor(i) {
  if (i.otro) {
    const [nombre, ...resto] = i.observacion.split(SEP);
    return { id: i.objeto, nombre: nombre.trim(), nuevo: true, cantidad: i.cantidad, fragil: i.fragil, detalle: resto.join(SEP).trim() };
  }
  return { id: i.objeto, nombre: i.nombre, nuevo: false, cantidad: i.cantidad, fragil: i.fragil, detalle: i.observacion };
}

// Filas de la lista → lo que espera la API (para «Otro», el nombre va en la observación)
const haciaServidor = (it) => ({
  objeto: it.id, cantidad: it.cantidad, fragil: it.fragil,
  observacion: it.nuevo ? it.nombre + (it.detalle ? SEP + it.detalle : '') : it.detalle,
});

const hoy = () => new Date().toLocaleDateString('sv-SE'); // AAAA-MM-DD en hora local

function finAproximado(hora, horas) {
  if (!hora) return '';
  const [h, m] = hora.split(':').map(Number);
  const total = h * 60 + m + horas * 60;
  const dias = Math.floor(total / 1440);
  const fin = `${String(Math.floor((total % 1440) / 60)).padStart(2, '0')}:${String(total % 60).padStart(2, '0')}`;
  return ` (termina aprox. a las ${fin}${dias === 0 ? '' : dias === 1 ? ' del día siguiente' : `, ${dias} días después`})`;
}

// Página: carga el catálogo (y el pedido si se modifica) y recién ahí arma el formulario
export function PedidoForm() {
  const { id } = useParams();
  const { catalogo, loading, error } = useCatalogo();
  const { pedido, loading: cargandoPedido, error: errorPedido } = usePedido(id);

  if (loading || cargandoPedido) return <LoadingSpinner />;
  if (error || errorPedido) return <ErrorAlert message={error || errorPedido} />;
  if (pedido && !pedido.puede_cambiar) {
    return (
      <div className="alert alert-warning mx-auto" style={{ maxWidth: 700 }}>
        Ya no se puede modificar el pedido N° {pedido.id}: faltan menos de {catalogo.horas_limite} horas o no está activo.{' '}
        <Link to={`/pedidos/${pedido.id}`}>Volver al pedido</Link>
      </div>
    );
  }
  return <Formulario catalogo={catalogo} pedido={pedido} />;
}

function Formulario({ catalogo, pedido }) {
  const navigate = useNavigate();
  const principalInicial = pedido?.servicios.find((s) => !s.adicional)?.id;
  const [datos, setDatos] = useState({
    fecha_servicio: pedido?.fecha_servicio ?? '',
    hora_servicio: pedido?.hora_servicio ?? '',
    origen: pedido?.origen ?? '',
    destino: pedido?.destino ?? '',
    servicio: principalInicial ? String(principalInicial) : '',
    adicionales: pedido?.servicios.filter((s) => s.adicional).map((s) => String(s.id)) ?? [],
    vehiculo: pedido?.vehiculo ?? '',
  });
  const [items, setItems] = useState(pedido ? pedido.inventario.map(desdeServidor) : []);
  const [modal, setModal] = useState(null); // null = cerrada; -1 = agregar; n = editar la fila n
  const [errores, setErrores] = useState({});
  const [enviando, setEnviando] = useState(false);

  const { vehiculos, motivo, loading: buscandoVehiculos } = useVehiculosLibres({
    fecha: datos.fecha_servicio, hora: datos.hora_servicio, servicio: datos.servicio, pedido: pedido?.id,
  });

  const cambiar = (e) => setDatos({ ...datos, [e.target.name]: e.target.value });
  const alternarAdicional = (id) => setDatos({
    ...datos,
    adicionales: datos.adicionales.includes(id) ? datos.adicionales.filter((a) => a !== id) : [...datos.adicionales, id],
  });

  // Total = principal con el recargo del camión + adicionales (igual que reglas.registrar_pedido)
  const principal = catalogo.principales.find((s) => String(s.id) === datos.servicio);
  const vehiculo = vehiculos.find((v) => v.patente === datos.vehiculo);
  const recargo = vehiculo?.recargo ?? 0;
  const precioPrincipal = principal ? Math.round(principal.precio * (100 + recargo)) / 100 : 0;
  const extras = catalogo.adicionales
    .filter((s) => datos.adicionales.includes(String(s.id)))
    .reduce((t, s) => t + s.precio, 0);

  const guardarObjeto = (it) => {
    setItems(modal >= 0 ? items.map((x, k) => (k === modal ? it : x)) : [...items, it]);
    setModal(null);
    setErrores({ ...errores, inventario: undefined });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!items.length) {
      setErrores({ inventario: 'Agregá al menos un objeto con el botón «Agregar objeto».' });
      return;
    }
    setEnviando(true);
    setErrores({});
    const cuerpo = { ...datos, vehiculo: vehiculo ? datos.vehiculo : '', inventario: items.map(haciaServidor) };
    try {
      const { id } = pedido ? await pedidoService.update(pedido.id, cuerpo) : await pedidoService.create(cuerpo);
      const hecho = pedido ? 'modificado' : 'registrado';
      navigate(`/pedidos/${id}`, {
        state: { aviso: `Pedido N° ${id} ${hecho}. Queda pendiente hasta que la empresa lo confirme.` },
      });
    } catch (err) {
      setErrores({ __all__: err.message, ...err.errores });
      setEnviando(false);
      window.scrollTo({ top: 0, behavior: 'smooth' });
    }
  };

  const Error = ({ campo }) => (errores[campo] ? <div className="invalid-feedback d-block">{errores[campo]}</div> : null);
  const campoTexto = (name, label, props = {}) => (
    <div className="col-sm-6 col-lg-3">
      <label htmlFor={name} className="form-label">{label}</label>
      <input id={name} name={name} className={`form-control ${errores[name] ? 'is-invalid' : ''}`}
             value={datos[name]} onChange={cambiar} {...props} />
      <Error campo={name} />
    </div>
  );

  return (
    <div className="mx-auto" style={{ maxWidth: 900 }}>
      <h1 className="h3 fw-bold mb-1">{pedido ? `Modificar pedido N° ${pedido.id}` : 'Pedir una mudanza'}</h1>
      <p className="text-muted mb-4">
        {pedido
          ? `Podés cambiar todo hasta ${catalogo.horas_limite} horas antes. Al guardar, el pedido vuelve a quedar pendiente hasta que la empresa lo confirme, y el total se recalcula con los precios de hoy.`
          : 'El pedido queda pendiente hasta que la empresa lo confirme.'}
      </p>

      {errores.__all__ && <div className="alert alert-danger">{errores.__all__}</div>}

      <form onSubmit={handleSubmit} noValidate>
        <section className="card-panel p-4 mb-3">
          <h2 className="h6 fw-bold text-uppercase text-muted mb-3"><i className="bi bi-geo-alt me-1" />1. Cuándo y dónde</h2>
          <div className="row g-3">
            {campoTexto('fecha_servicio', 'Fecha de la mudanza', { type: 'date', min: hoy() })}
            {campoTexto('hora_servicio', 'Hora de inicio', { type: 'time', step: 900 })}
            {campoTexto('origen', 'Desde', { maxLength: 200, placeholder: 'Calle, número y ciudad' })}
            {campoTexto('destino', 'Hasta', { maxLength: 200, placeholder: 'Calle, número y ciudad' })}
          </div>
        </section>

        <section className="card-panel p-4 mb-3">
          <h2 className="h6 fw-bold text-uppercase text-muted mb-3"><i className="bi bi-list-check me-1" />2. Servicio</h2>
          <div className="row row-cols-1 row-cols-sm-3 g-2" role="radiogroup" aria-label="Servicio">
            {catalogo.principales.map((s) => (
              <div key={s.id} className="col">
                <TarjetaOpcion id={`srv${s.id}`} name="servicio" icono={iconoServicio(s.nombre)} titulo={s.nombre}
                               checked={datos.servicio === String(s.id)}
                               onChange={() => setDatos({ ...datos, servicio: String(s.id) })}>
                  <span className="fw-bold fs-5">{dinero(s.precio)}</span>
                  <span className="small text-muted">unas {s.horas} horas</span>
                </TarjetaOpcion>
              </div>
            ))}
          </div>
          <Error campo="servicio" />

          {principal && catalogo.adicionales.length > 0 && (
            <div className="border-top mt-3 pt-3">
              <p className="fw-semibold mb-2">¿Querés sumar algo más? <span className="text-muted fw-normal small">(opcional)</span></p>
              <div className="row row-cols-1 row-cols-sm-2 g-2">
                {catalogo.adicionales.map((s) => (
                  <div key={s.id} className="col">
                    <TarjetaOpcion tipo="checkbox" id={`adi${s.id}`} icono={iconoServicio(s.nombre)} iconoClase="opcion-icono-chico"
                                   titulo={s.nombre} checked={datos.adicionales.includes(String(s.id))}
                                   onChange={() => alternarAdicional(String(s.id))}>
                      <span className="small fw-semibold">{s.precio > 0 ? `+ ${dinero(s.precio)}` : 'Sin cargo'}</span>
                    </TarjetaOpcion>
                  </div>
                ))}
              </div>
              <Error campo="adicionales" />
            </div>
          )}
          <p className="fw-bold mt-3 mb-0">Total: {dinero(precioPrincipal + extras)}</p>
          <p className="text-muted small mb-0">
            {principal && vehiculo
              ? `Servicio ${dinero(precioPrincipal)}${recargo ? ` (con +${recargo} % por el camión)` : ''}${extras ? ` + adicionales ${dinero(extras)}` : ''}.`
              : 'El servicio principal tiene un recargo según el camión: Mediano +25 %, Grande +50 %.'}
          </p>
          {principal && (
            <p className="text-muted small mb-0">Duración estimada: {principal.horas} horas{finAproximado(datos.hora_servicio, principal.horas)}.</p>
          )}
        </section>

        <section className="card-panel p-4 mb-3">
          <h2 className="h6 fw-bold text-uppercase text-muted mb-3"><i className="bi bi-box-seam me-1" />3. Qué hay que llevar</h2>
          {items.length === 0 ? (
            <p className="text-muted mb-3">Todavía no agregaste nada.</p>
          ) : (
            <ul className="list-group mb-3" aria-live="polite">
              {items.map((it, k) => (
                <li key={k} className="list-group-item d-flex justify-content-between align-items-center gap-2 flex-wrap">
                  <div>
                    <span className="fw-semibold">{it.cantidad} × {etiqueta(it)}</span>
                    {it.fragil && <span className="badge text-bg-warning ms-1">frágil</span>}
                    {it.detalle && <div className="small text-muted">{it.detalle}</div>}
                  </div>
                  <div className="d-flex gap-2">
                    <button type="button" className="btn btn-sm btn-outline-secondary" onClick={() => setModal(k)}
                            aria-label={`Editar ${etiqueta(it)}`}><i className="bi bi-pencil me-1" />Editar</button>
                    <button type="button" className="btn btn-sm btn-outline-danger" onClick={() => setItems(items.filter((_, n) => n !== k))}
                            aria-label={`Quitar ${etiqueta(it)}`}><i className="bi bi-trash me-1" />Quitar</button>
                  </div>
                </li>
              ))}
            </ul>
          )}
          {errores.inventario && <div className="alert alert-danger py-2">{errores.inventario}</div>}
          <button type="button" className="btn btn-outline-success fw-semibold" onClick={() => setModal(-1)}>
            <i className="bi bi-plus-circle me-1" />Agregar objeto
          </button>
        </section>

        <section className="card-panel p-4 mb-4">
          <h2 className="h6 fw-bold text-uppercase text-muted mb-3"><i className="bi bi-truck me-1" />4. Vehículo</h2>
          {!datos.fecha_servicio || !datos.hora_servicio || !datos.servicio ? (
            <p className="text-muted mb-0"><i className="bi bi-info-circle me-1" />Elegí primero la fecha, la hora y el servicio: te mostramos los camiones libres en ese horario.</p>
          ) : buscandoVehiculos ? (
            <p className="text-muted mb-0"><span className="spinner-border spinner-border-sm me-2" aria-hidden="true" />Buscando camiones libres...</p>
          ) : !vehiculos.length ? (
            <div className="alert alert-warning mb-0">{motivo || 'No hay camiones libres en ese horario.'}</div>
          ) : (
            <>
              <p className="small text-muted mb-2">Libres el {fecha(datos.fecha_servicio)} a las {datos.hora_servicio}. El servicio cambia de precio según el tamaño.</p>
              <div className="row row-cols-1 row-cols-sm-3 g-2" role="radiogroup" aria-label="Vehículo">
                {vehiculos.map((v) => (
                  <div key={v.patente} className="col">
                    <TarjetaOpcion id={`veh${v.patente}`} name="vehiculo" icono="bi-truck" iconoClase={`camion-${v.tipo.split(' ').pop().toLowerCase()}`}
                                   titulo={v.tipo} checked={datos.vehiculo === v.patente}
                                   onChange={() => setDatos({ ...datos, vehiculo: v.patente })}>
                      <span className="small text-muted">{v.patente} · {v.modelo}</span>
                      <span className="small">Hasta {v.capacidad_kg.toLocaleString('es-AR')} kg · {v.capacidad_m3.toLocaleString('es-AR')} m³</span>
                      <span className={`badge rounded-pill mt-1 ${v.recargo ? 'text-bg-warning' : 'text-bg-light border'}`}>
                        {v.recargo ? `+${v.recargo} % al servicio` : 'Sin recargo'}
                      </span>
                      {principal && <span className="fw-bold mt-1">Servicio: {dinero(Math.round(principal.precio * (100 + v.recargo)) / 100)}</span>}
                    </TarjetaOpcion>
                  </div>
                ))}
              </div>
            </>
          )}
          <Error campo="vehiculo" />
        </section>

        <div className="d-flex justify-content-end gap-3">
          <Link to={pedido ? `/pedidos/${pedido.id}` : '/pedidos'} className="btn btn-outline-secondary px-4">
            {pedido ? 'Volver' : 'Cancelar'}
          </Link>
          <button type="submit" className="btn btn-success px-4 fw-bold" disabled={enviando}>
            {enviando ? 'Guardando...' : pedido ? 'Guardar cambios' : 'Registrar pedido'}
          </button>
        </div>
      </form>

      {modal !== null && (
        <ModalObjeto
          key={modal}
          objetos={catalogo.objetos}
          maxCantidad={catalogo.max_cantidad}
          items={items}
          editando={modal}
          onGuardar={guardarObjeto}
          onEditarOtro={setModal}
          onHide={() => setModal(null)}
        />
      )}
    </div>
  );
}
