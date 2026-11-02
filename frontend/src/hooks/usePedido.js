import { useCallback, useEffect, useState } from 'react';
import axios from 'axios';
import { pedidoService } from '../services/pedidoService';

// Un pedido por id (para el detalle y para modificarlo)
export function usePedido(id) {
  const [pedido, setPedido] = useState(null);
  const [loading, setLoading] = useState(Boolean(id));
  const [error, setError] = useState(null);

  const cargar = useCallback(() => {
    if (!id) return undefined;
    const controller = new AbortController();
    setLoading(true);
    setError(null);
    pedidoService
      .getById(id, controller.signal)
      .then(setPedido)
      .catch((err) => {
        if (!axios.isCancel(err)) setError(err.status === 404 ? 'Ese pedido no existe.' : err.message);
      })
      .finally(() => {
        if (!controller.signal.aborted) setLoading(false);
      });
    return () => controller.abort();
  }, [id]);

  useEffect(() => cargar(), [cargar]);

  return { pedido, loading, error, refetch: cargar };
}
