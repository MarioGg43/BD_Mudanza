export function ErrorAlert({ message, onRetry }) {
  return (
    <div className="alert alert-danger d-flex justify-content-between align-items-center gap-3 my-4" role="alert">
      <div>
        <p className="fw-bold mb-1"><i className="bi bi-exclamation-triangle me-1" />Ocurrió un error</p>
        <p className="mb-0">{message}</p>
      </div>
      {onRetry && (
        <button type="button" className="btn btn-outline-danger btn-sm" onClick={onRetry}>
          Reintentar
        </button>
      )}
    </div>
  );
}
