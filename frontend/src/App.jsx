import { Route, Routes, useLocation } from 'react-router-dom';
import { useAuth } from './context/AuthContext';
import { Navbar } from './components/Navbar';
import { PieEmpresa } from './components/PieEmpresa';
import { RutaPrivada } from './components/RutaPrivada';
import { Inicio } from './pages/Inicio';
import { Login } from './pages/Login';
import { Registro } from './pages/Registro';
import { MisPedidos } from './pages/MisPedidos';
import { PanelPedidos } from './pages/PanelPedidos';
import { PedidoDetalle } from './pages/PedidoDetalle';
import { PedidoForm } from './pages/PedidoForm';
import { CancelarPedido } from './pages/CancelarPedido';
import { AsignarPersonal } from './pages/AsignarPersonal';
import { EditarServicios } from './pages/EditarServicios';
import { Reprogramar } from './pages/Reprogramar';
import { AnularPedido } from './pages/AnularPedido';
import { NotFound } from './pages/NotFound';

// /pedidos: el administrador ve todos con avisos y filtros; el cliente, los suyos
function Pedidos() {
  const { puede } = useAuth();
  return puede('PED_GESTIONAR') ? <PanelPedidos /> : <MisPedidos />;
}

export default function App() {
  const { pathname } = useLocation();
  return (
    <div className="d-flex flex-column min-vh-100">
      <Navbar />
      <main className="container flex-grow-1 pb-5">
        <Routes>
          <Route path="/" element={<Inicio />} />
          <Route path="/login" element={<Login />} />
          <Route path="/registro" element={<Registro />} />
          <Route element={<RutaPrivada permiso="PED_CONSULTAR" />}>
            <Route path="/pedidos" element={<Pedidos />} />
            <Route path="/pedidos/:id" element={<PedidoDetalle />} />
            <Route path="/pedidos/:id/cancelar" element={<CancelarPedido />} />
          </Route>
          <Route element={<RutaPrivada permiso="PED_REGISTRAR" />}>
            <Route path="/pedidos/nuevo" element={<PedidoForm />} />
            <Route path="/pedidos/:id/modificar" element={<PedidoForm />} />
          </Route>
          <Route element={<RutaPrivada permiso="PED_GESTIONAR" />}>
            <Route path="/pedidos/:id/personal" element={<AsignarPersonal />} />
            <Route path="/pedidos/:id/servicios" element={<EditarServicios />} />
            <Route path="/pedidos/:id/reprogramar" element={<Reprogramar />} />
          </Route>
          <Route element={<RutaPrivada permiso="PED_ANULAR" />}>
            <Route path="/pedidos/:id/anular" element={<AnularPedido />} />
          </Route>
          <Route path="*" element={<NotFound />} />
        </Routes>
      </main>
      {pathname === '/' && <PieEmpresa />}
    </div>
  );
}
