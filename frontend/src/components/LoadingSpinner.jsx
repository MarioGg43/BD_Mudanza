export function LoadingSpinner({ texto = 'Cargando...' }) {
  return (
    <div className="text-center my-5 py-4" role="status">
      <div className="spinner-border text-warning" style={{ width: '3rem', height: '3rem' }} aria-hidden="true" />
      <p className="mt-3 text-muted fw-semibold">{texto}</p>
    </div>
  );
}
