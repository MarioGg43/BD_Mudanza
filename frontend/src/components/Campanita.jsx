import { useEffect, useState } from 'react';
import { Link, useLocation } from 'react-router-dom';
import axios from 'axios';
import { analisisService } from '../services/analisisService';

/* La campanita de la barra: cuántas notificaciones sin leer tiene quien entró. Se actualiza al
   cambiar de pantalla, cada minuto y cuando la bandeja avisa que se leyó algo. */
export function Campanita() {
  const { pathname } = useLocation();
  const [sinLeer, setSinLeer] = useState(0);

  // Cuenta las notificaciones sin leer: al cambiar de pantalla, cada minuto y cuando la bandeja avisa.
  useEffect(() => {
    const controller = new AbortController();
    const contar = () => analisisService.contarNotificaciones(controller.signal)
      .then((r) => setSinLeer(r.sin_leer))
      .catch((err) => { if (!axios.isCancel(err)) setSinLeer(0); });
    contar();
    const cada = setInterval(contar, 60000);
    window.addEventListener('notificaciones-cambiaron', contar);
    return () => {
      controller.abort();
      clearInterval(cada);
      window.removeEventListener('notificaciones-cambiaron', contar);
    };
  }, [pathname]);

  const texto = sinLeer ? `${sinLeer} notificaci${sinLeer === 1 ? 'ón' : 'ones'} sin leer` : 'Notificaciones';
  return (
    <Link to="/notificaciones" className="campanita ms-1" title={texto} aria-label={texto}>
      <i className="bi bi-bell" />
      {sinLeer > 0 && <span className="campanita-numero">{sinLeer > 99 ? '99+' : sinLeer}</span>}
    </Link>
  );
}
