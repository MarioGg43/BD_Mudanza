import { useState } from 'react';
import { Modal } from 'react-bootstrap';

/* Ventana de «¿Seguro?» antes de una acción que cambia el pedido (confirmar, finalizar).
   `accion` es una función async: si falla, el error se muestra adentro de la ventana. */
export function ConfirmarAccion({ titulo, children, boton, claseBoton = 'btn-primary', accion, onHide }) {
  const [enviando, setEnviando] = useState(false);
  const [error, setError] = useState(null);

  const confirmar = async () => {
    setEnviando(true);
    setError(null);
    try {
      await accion();
    } catch (err) {
      setError(err.message);
      setEnviando(false);
    }
  };

  return (
    <Modal show onHide={onHide} centered>
      <Modal.Header closeButton>
        <Modal.Title as="h2" className="h5 fw-bold">{titulo}</Modal.Title>
      </Modal.Header>
      <Modal.Body>
        {children}
        {error && <div className="alert alert-danger mt-3 mb-0">{error}</div>}
      </Modal.Body>
      <Modal.Footer>
        <button type="button" className="btn btn-outline-secondary" onClick={onHide} disabled={enviando}>Volver</button>
        <button type="button" className={`btn ${claseBoton} fw-bold`} onClick={confirmar} disabled={enviando}>
          {enviando ? 'Guardando...' : boton}
        </button>
      </Modal.Footer>
    </Modal>
  );
}
