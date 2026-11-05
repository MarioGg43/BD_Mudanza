import { createContext, useCallback, useContext, useEffect, useState } from 'react';
import { CLAVE_SESION } from '../services/api';
import { authService } from '../services/authService';

const AuthContext = createContext(null);

const PANTALLAS = [
  ['PED_CONSULTAR', '/pedidos'],
  ['MUDANZAS_OPERAR', '/portal'],
  ['VEH_GESTIONAR', '/vehiculos'],
  ['USR_CONSULTAR', '/usuarios'],
  ['SRV_GESTIONAR', '/servicios'],
  ['ROL_GESTIONAR', '/roles'],
];

function leerSesion() {
  try {
    return JSON.parse(localStorage.getItem(CLAVE_SESION));
  } catch {
    return null;
  }
}

function guardarSesion(sesion) {
  try {
    if (sesion) localStorage.setItem(CLAVE_SESION, JSON.stringify(sesion));
    else localStorage.removeItem(CLAVE_SESION);
  } catch {
    // almacenamiento bloqueado: la sesión dura lo que dure la pestaña
  }
}

// Quién está conectado, para toda la app (evita pasar el usuario por props a cada página)
export function AuthProvider({ children }) {
  const [sesion, setSesion] = useState(leerSesion);

  const entrar = useCallback((datos) => {
    guardarSesion(datos);
    setSesion(datos);
  }, []);

  const salir = useCallback(() => {
    guardarSesion(null);
    setSesion(null);
  }, []);

  const login = async (usuario, clave) => entrar(await authService.login(usuario, clave));
  const registro = async (datos) => entrar(await authService.registro(datos));

  // El interceptor de Axios avisa cuando el servidor rechaza el token (401)
  useEffect(() => {
    window.addEventListener('sesion-vencida', salir);
    return () => window.removeEventListener('sesion-vencida', salir);
  }, [salir]);

  const usuario = sesion?.usuario ?? null;
  const puede = (permiso) => !!usuario?.permisos.includes(permiso);
  // La primera pantalla según los permisos (igual que pantalla_inicio de Django)
  const inicio = PANTALLAS.find(([permiso]) => puede(permiso))?.[1] ?? '/';

  return (
    <AuthContext.Provider value={{ usuario, login, registro, salir, puede, inicio }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  return useContext(AuthContext);
}
