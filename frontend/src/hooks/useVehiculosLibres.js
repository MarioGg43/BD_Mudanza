import { useEffect, useState } from 'react';
import axios from 'axios';
import { catalogoService } from '../services/catalogoService';

// Cada vez que cambia la fecha, la hora o el servicio se piden los vehículos libres en ese horario.
// La petición anterior se cancela: así nunca se pisa una respuesta nueva con una vieja.
export function useVehiculosLibres({ fecha, hora, servicio, pedido }) {
  const [estado, setEstado] = useState({ vehiculos: [], motivo: '', loading: false });

  useEffect(() => {
    if (!fecha || !hora || !servicio) {
      setEstado({ vehiculos: [], motivo: '', loading: false });
      return undefined;
    }
    const controller = new AbortController();
    setEstado((e) => ({ ...e, loading: true }));
    catalogoService
      .vehiculosLibres({ fecha, hora, servicio, pedido }, controller.signal)
      .then(({ vehiculos, motivo }) => setEstado({ vehiculos, motivo, loading: false }))
      .catch((err) => {
        if (!axios.isCancel(err)) setEstado({ vehiculos: [], motivo: err.message, loading: false });
      });
    return () => controller.abort();
  }, [fecha, hora, servicio, pedido]);

  return estado;
}
