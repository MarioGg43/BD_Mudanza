import { Navigate, Route, Routes } from 'react-router-dom';
import { Navbar } from './components/Navbar';
import { RutaPrivada } from './components/RutaPrivada';
import { Login } from './pages/Login';
import { Registro } from './pages/Registro';
import { MisPedidos } from './pages/MisPedidos';
import { PedidoDetalle } from './pages/PedidoDetalle';
import { PedidoForm } from './pages/PedidoForm';
import { CancelarPedido } from './pages/CancelarPedido';
import { NotFound } from './pages/NotFound';

export default function App() {
  return (
    <div className="d-flex flex-column min-vh-100">
      <Navbar />
      <main className="container flex-grow-1 pb-5">
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route path="/registro" element={<Registro />} />
          <Route element={<RutaPrivada permiso="PED_CONSULTAR" />}>
            <Route path="/" element={<Navigate to="/pedidos" replace />} />
            <Route path="/pedidos" element={<MisPedidos />} />
            <Route path="/pedidos/:id" element={<PedidoDetalle />} />
            <Route path="/pedidos/:id/cancelar" element={<CancelarPedido />} />
          </Route>
          <Route element={<RutaPrivada permiso="PED_REGISTRAR" />}>
            <Route path="/pedidos/nuevo" element={<PedidoForm />} />
            <Route path="/pedidos/:id/modificar" element={<PedidoForm />} />
          </Route>
          <Route path="*" element={<NotFound />} />
        </Routes>
      </main>
      <footer className="pie-marca py-3 text-center small">
        Mudanzas y Fletes Salta · Grupo 5 · Frontend en React &copy; {new Date().getFullYear()}
      </footer>
    </div>
  );
}
