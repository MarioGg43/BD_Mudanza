import { useRef, useState } from 'react';
import { Modal } from 'react-bootstrap';
import { clave, conMayuscula } from '../utils/formato';

const etiqueta = (it) => (it.nuevo ? 'Otro: ' : '') + it.nombre; // «Otro: Piano»

// Una línea de la lista de controles: verde si está bien, rojo si hay que corregir, gris si falta
function Chequeo({ estado, children }) {
  const icono = { ok: 'bi-check-circle-fill text-success', mal: 'bi-x-circle-fill text-danger', falta: 'bi-circle text-muted' }[estado];
  const clase = estado === 'mal' ? 'text-danger fw-semibold' : estado === 'ok' ? 'text-success' : 'text-muted';
  return (
    <li className={`mb-1 ${clase}`}>
      <i className={`bi ${icono} me-1`} />
      {children}
    </li>
  );
}

/* Ventana para agregar o editar un objeto. Aplica las mismas reglas que el servidor
   (reglas._validar_items) mientras la persona escribe:
   - lo que está en el catálogo se elige de ahí;
   - lo que no está va como «Otro», que hay que elegir a propósito, y entonces es obligatorio decir qué es;
   - «Otro» no se usa para algo que ya está en la lista;
   - un objeto no se repite en el pedido. */
export function ModalObjeto({ objetos, maxCantidad, items, editando, onGuardar, onEditarOtro, onHide }) {
  const OTRO = objetos.find((o) => o.otro);
  const lista = objetos.filter((o) => !o.otro);
  const actual = editando >= 0 ? items[editando] : null;

  const [modo, setModo] = useState(actual?.nuevo ? 'otro' : 'lista');
  const [buscar, setBuscar] = useState(actual && !actual.nuevo ? actual.nombre : '');
  const [queEs, setQueEs] = useState(actual?.nuevo ? actual.nombre : '');
  const [cantidad, setCantidad] = useState(actual ? String(actual.cantidad) : '1');
  const [fragil, setFragil] = useState(actual?.fragil ?? false);
  const [detalle, setDetalle] = useState(actual?.detalle ?? '');
  const buscarRef = useRef(null);
  const queEsRef = useRef(null);

  // Lo buscado: el que coincide exacto (sin tildes, mayúsculas ni plural) y los parecidos
  const q = clave(buscar.trim());
  const exacto = q ? lista.find((o) => o.clave === q) : null;
  const parecidos = !q
    ? lista
    : lista
        .filter((o) => o !== exacto && o.clave.includes(q))
        .sort((a, b) => b.clave.startsWith(q) - a.clave.startsWith(q))
        .slice(0, 6);

  const seleccion = modo === 'otro'
    ? { id: OTRO.id, nombre: conMayuscula(queEs.trim()), nuevo: true }
    : exacto && { id: exacto.id, nombre: exacto.nombre, nuevo: false };

  const elegir = (o) => {
    setModo('lista');
    setBuscar(o.nombre);
    setQueEs('');
  };
  const elegirOtro = () => {
    setModo('otro');
    setQueEs(exacto ? '' : conMayuscula(buscar.trim())); // lo que buscó y no estaba pasa a «¿qué es?»
  };

  // ----- controles
  let okObjeto = false;
  let chequeoObjeto;
  const enLista = seleccion?.nuevo ? lista.find((o) => o.clave === clave(seleccion.nombre)) : null;
  if (!seleccion) {
    chequeoObjeto = <Chequeo estado="falta">Elegí qué hay que llevar de la lista (o «Otro»)</Chequeo>;
  } else if (!seleccion.nuevo) {
    okObjeto = true;
    chequeoObjeto = <Chequeo estado="ok">Elegiste «{seleccion.nombre}» de la lista</Chequeo>;
  } else if (clave(seleccion.nombre).length < 2) {
    chequeoObjeto = <Chequeo estado="falta">Elegiste «Otro»: contá qué es</Chequeo>;
  } else if (enLista) {
    chequeoObjeto = (
      <Chequeo estado="mal">
        «{queEs.trim()}» ya está en la lista como «{enLista.nombre}»: elegilo de ahí, no hace falta «Otro».
      </Chequeo>
    );
  } else {
    okObjeto = true;
    chequeoObjeto = <Chequeo estado="ok">Otro: «{seleccion.nombre}»</Chequeo>;
  }

  const repetido = seleccion
    ? items.findIndex((i, n) => n !== editando && (seleccion.nuevo
        ? i.nuevo && clave(i.nombre) === clave(seleccion.nombre)
        : !i.nuevo && i.id === seleccion.id))
    : -1;
  const n = Number(cantidad);
  const okCantidad = Number.isInteger(n) && n >= 1 && n <= maxCantidad;
  const ok = okObjeto && seleccion && repetido < 0 && okCantidad;

  const guardar = () => {
    if (!ok) return;
    onGuardar({ ...seleccion, cantidad: n, fragil, detalle: detalle.trim() });
  };
  const enterGuarda = (e) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      guardar();
    }
  };

  // ----- aviso debajo del buscador
  let aviso = null;
  if (exacto) {
    aviso = exacto.nombre === buscar.trim()
      ? <div className="alert alert-success py-2 mb-0 small"><i className="bi bi-check-circle-fill me-1" />«{exacto.nombre}» está en la lista.</div>
      : <div className="alert alert-info py-2 mb-0 small"><i className="bi bi-info-circle-fill me-1" />«{buscar.trim()}» ya está en la lista como <b>«{exacto.nombre}»</b>. Lo elegimos de ahí.</div>;
  } else if (q && !parecidos.length) {
    aviso = (
      <div className="alert alert-warning py-2 mb-0 small">
        <i className="bi bi-exclamation-triangle-fill me-1" />«{buscar.trim()}» no está en la lista. Revisá cómo lo escribiste o,
        si es otra cosa, elegí <b>«Otro»</b> y contá qué es.
      </div>
    );
  } else if (q) {
    aviso = <span className="small"><i className="bi bi-hand-index-thumb me-1" />¿Es alguno de estos? Tocalo.</span>;
  }

  return (
    // el foco va al campo cuando termina de abrirse (antes, la ventana se lo queda)
    <Modal show onHide={onHide} centered scrollable onKeyDown={enterGuarda}
           onEntered={() => (modo === 'otro' ? queEsRef : buscarRef).current?.focus()}>
      <Modal.Header closeButton>
        <Modal.Title as="h2" className="h5 fw-bold">{actual ? 'Editar objeto' : 'Agregar objeto'}</Modal.Title>
      </Modal.Header>
      <Modal.Body>
        {modo === 'lista' ? (
          <div>
            <label htmlFor="buscarObjeto" className="form-label">¿Qué hay que llevar? Buscalo en la lista</label>
            <input
              id="buscarObjeto" ref={buscarRef} type="text" className="form-control form-control-lg" maxLength={50} autoComplete="off"
              placeholder="Escribí para buscar: heladera, sillas…" value={buscar} autoFocus
              onChange={(e) => setBuscar(e.target.value)}
            />
            <div className="mt-2" aria-live="polite">{aviso}</div>
            <p className="small text-muted mt-2 mb-1">{q ? 'En la lista:' : 'O tocá uno de la lista:'}</p>
            <div className="d-flex flex-wrap gap-2 mb-3">
              {[...(exacto ? [exacto] : []), ...parecidos].map((o) => (
                <button key={o.id} type="button" onClick={() => elegir(o)}
                        className={`btn btn-sm rounded-pill ${seleccion?.id === o.id ? 'btn-success' : 'btn-outline-secondary'}`}>
                  {o.nombre}
                </button>
              ))}
              {/* «Otro» siempre al final, y hay que elegirlo a propósito */}
              <button type="button" className="btn btn-sm rounded-pill btn-outline-dark" onClick={elegirOtro}>
                <i className="bi bi-three-dots me-1" />Otro (no está en la lista)
              </button>
            </div>
          </div>
        ) : (
          <div className="mb-3">
            <button type="button" className="btn btn-link px-0 mb-2" onClick={() => { setModo('lista'); setQueEs(''); }}>
              <i className="bi bi-arrow-left me-1" />Volver a buscar en la lista
            </button>
            <label htmlFor="queEsOtro" className="form-label d-block">
              Elegiste «Otro»: ¿qué es? <span className="text-danger">(obligatorio)</span>
            </label>
            <input id="queEsOtro" ref={queEsRef} type="text" className="form-control" maxLength={50} autoComplete="off" autoFocus
                   placeholder="Ej.: piano, cuna, acuario" value={queEs} onChange={(e) => setQueEs(e.target.value)} />
            {enLista && (
              <button type="button" className="btn btn-sm btn-outline-success mt-2" onClick={() => elegir(enLista)}>
                Elegir «{enLista.nombre}»
              </button>
            )}
          </div>
        )}

        <div className="row g-3 align-items-end">
          <div className="col-5">
            <label htmlFor="cantObjeto" className="form-label">Cantidad</label>
            <input id="cantObjeto" type="number" className="form-control" min={1} max={maxCantidad} inputMode="numeric"
                   value={cantidad} onChange={(e) => setCantidad(e.target.value)} />
          </div>
          <div className="col-7">
            <div className="form-check mb-2">
              <input id="fragilObjeto" type="checkbox" className="form-check-input" checked={fragil}
                     onChange={(e) => setFragil(e.target.checked)} />
              <label htmlFor="fragilObjeto" className="form-check-label">Es frágil</label>
            </div>
          </div>
          <div className="col-12">
            <label htmlFor="detalleObjeto" className="form-label">Detalle <span className="text-muted fw-normal">(opcional)</span></label>
            <input id="detalleObjeto" type="text" className="form-control" maxLength={140} autoComplete="off"
                   placeholder="Ej.: se desarma, tiene vidrio" value={detalle} onChange={(e) => setDetalle(e.target.value)} />
          </div>
        </div>

        <ul className="list-unstyled small mt-3 mb-0">
          {chequeoObjeto}
          {!seleccion ? (
            <Chequeo estado="falta">Que no esté repetido en tu pedido</Chequeo>
          ) : repetido >= 0 ? (
            <Chequeo estado="mal">
              Ya agregaste {items[repetido].cantidad} × {etiqueta(items[repetido])}: no hace falta agregarlo de nuevo.
              <button type="button" className="btn btn-sm btn-outline-danger d-block mt-2 fw-normal" onClick={() => onEditarOtro(repetido)}>
                <i className="bi bi-pencil me-1" />Cambiar la cantidad de {etiqueta(items[repetido])}
              </button>
            </Chequeo>
          ) : (
            <Chequeo estado="ok">No está repetido en tu pedido</Chequeo>
          )}
          {okCantidad
            ? <Chequeo estado="ok">Cantidad: {n}</Chequeo>
            : <Chequeo estado="mal">La cantidad tiene que ser un número entero de 1 a {maxCantidad}</Chequeo>}
        </ul>
      </Modal.Body>
      <Modal.Footer>
        <button type="button" className="btn btn-outline-secondary" onClick={onHide}>Cancelar</button>
        <button type="button" className="btn btn-success fw-bold" disabled={!ok} onClick={guardar}>
          {actual ? 'Guardar cambios' : 'Agregar a la lista'}
        </button>
      </Modal.Footer>
    </Modal>
  );
}

export { etiqueta };
