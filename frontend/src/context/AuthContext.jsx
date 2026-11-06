import { createContext, useCallback, useContext, useEffect, useState } from 'react';
import { CLAVE_SESION } from '../services/api';
import { authService } from '../services/authService';
import { MOSTRAR_ADMINISTRACION } from '../config';

const AuthContext = createContext(null);

const PANTALLAS = [
  ['PED_CONSULTAR', '/pedidos'],
  ['MUDANZAS_OPERAR', '/portal'],
  ['VEH_GESTIONAR', '/vehiculos'],
  ['USR_CONSULTAR', '/usuarios'],
  ['SRV_GESTIONAR', '/servicios'],
  ['ROL_GESTIONAR', '/roles'],
];

// Con la administración oculta (config.js) solo pueden entrar los clientes
const habilitado = (datos) => MOSTRAR_ADMINISTRACION || !!datos?.usuario?.permisos.includes('PED_REGISTRAR');

function leerSesion() {
  try {
    const sesion = JSON.parse(localStorage.getItem(CLAVE_SESION));
    if (sesion && !habilitado(sesion)) localStorage.removeItem(CLAVE_SESION);
    return habilitado(sesion) ? sesion : null;
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
    if (!habilitado(datos)) {
      throw new Error('Por ahora el sistema nuevo está habilitado solo para clientes.');
    }
    guardarSesion(datos);
    setSesion(datos);
  }, []);

  const salir = useCallback(() => {
    guardarSesion(null);
    setSesion(null);
  }, []);

  const login = async (usuario, clave) => entrar(await authService.login(usuario, clave));
  const registro = async (datos) => entrar(await authService.registro(datos));
  const cambiarClave = async (datos) => entrar(await authService.cambiarClave(datos));
  const recuperarClave = async (datos) => entrar(await authService.recuperarClave(datos));

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
    <AuthContext.Provider value={{ usuario, login, registro, cambiarClave, recuperarClave, salir, puede, inicio }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  return useContext(AuthContext);
}
