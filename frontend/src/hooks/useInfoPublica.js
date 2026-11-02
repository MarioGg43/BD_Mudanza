import { useCallback, useEffect, useState } from 'react';
import axios from 'axios';
import { publicoService } from '../services/publicoService';

// Servicios y camiones para la página de inicio
export function useInfoPublica() {
  const [info, setInfo] = useState(null);
  const [error, setError] = useState(null);

  const cargar = useCallback(() => {
    const controller = new AbortController();
    setError(null);
    publicoService
      .getInfo(controller.signal)
      .then(setInfo)
      .catch((err) => {
        if (!axios.isCancel(err)) setError(err.message);
      });
    return () => controller.abort();
  }, []);

  useEffect(() => cargar(), [cargar]);

  return { info, loading: !info && !error, error, refetch: cargar };
}
