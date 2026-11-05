import { useCallback, useEffect, useState } from 'react';
import axios from 'axios';

/* Hook general para traer algo de la API una vez (y al cambiar `deps`), con cargando / error /
   cancelación. `pedir` recibe la señal del AbortController y devuelve la promesa del servicio.
   Ej.: useCarga((signal) => adminService.getPersonal(id, signal), [id]) */
export function useCarga(pedir, deps) {
  const [datos, setDatos] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const cargar = useCallback(() => {
    const controller = new AbortController();
    setLoading(true);
    setError(null);
    pedir(controller.signal)
      .then(setDatos)
      .catch((err) => {
        if (!axios.isCancel(err)) setError(err.message);
      })
      .finally(() => {
        if (!controller.signal.aborted) setLoading(false);
      });
    return () => controller.abort();
  }, deps);

  useEffect(() => cargar(), [cargar]);

  return { datos, loading, error, refetch: cargar };
}
