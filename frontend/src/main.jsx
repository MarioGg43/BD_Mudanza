import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import { BrowserRouter } from 'react-router-dom';
import 'bootstrap/dist/css/bootstrap.min.css';
import 'bootstrap-icons/font/bootstrap-icons.css';
import './styles/marca.css';
import './index.css';
import { AuthProvider } from './context/AuthContext';
import App from './App.jsx';

// Acá arranca todo: React se mete en el <div id="root"> del index.html y dibuja la app.
// BrowserRouter maneja las direcciones (/pedidos, /login...) y AuthProvider guarda quién entró.
createRoot(document.getElementById('root')).render(
  <StrictMode>
    <BrowserRouter>
      <AuthProvider>
        <App />
      </AuthProvider>
    </BrowserRouter>
  </StrictMode>,
);
