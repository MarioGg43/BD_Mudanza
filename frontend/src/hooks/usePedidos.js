import { useCallback, useEffect, useState } from 'react';
import axios from 'axios';
import { pedidoService } from '../services/pedidoService';

// Lista de pedidos con sus estados de interfaz (cargando / éxito / error).
// Si el filtro cambia antes de que llegue la respuesta, la petición vieja se cancela.
export function usePedidos(filtros) {
  const [pedidos, setPedidos] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const clave = JSON.stringify(filtros);

  const cargar = useCallback(() => {
    const controller = new AbortController();
    setLoading(true);
    setError(null);
    pedidoService
      .getAll(JSON.parse(clave), controller.signal)
      .then(setPedidos)
      .catch((err) => {
        if (!axios.isCancel(err)) setError(err.message);
      })
      .finally(() => {
        if (!controller.signal.aborted) setLoading(false);
      });
    return () => controller.abort();
  }, [clave]);

  useEffect(() => cargar(), [cargar]);

  return { pedidos, loading, error, refetch: cargar };
}
