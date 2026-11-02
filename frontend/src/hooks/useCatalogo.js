import { useEffect, useState } from 'react';
import axios from 'axios';
import { catalogoService } from '../services/catalogoService';

export function useCatalogo() {
  const [catalogo, setCatalogo] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    const controller = new AbortController();
    catalogoService
      .get(controller.signal)
      .then(setCatalogo)
      .catch((err) => {
        if (!axios.isCancel(err)) setError(err.message);
      });
    return () => controller.abort();
  }, []);

  return { catalogo, loading: !catalogo && !error, error };
}
