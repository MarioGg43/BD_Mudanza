import { createContext, useCallback, useContext, useEffect, useState } from 'react';
import { CLAVE_SESION } from '../services/api';
import { authService } from '../services/authService';
import { MOSTRAR_ADMINISTRACION } from '../config';

const AuthContext = createContext(null);

const PANTALLAS = [
  ['PED_GESTIONAR', '/tablero'],
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

// El «guardián» de la sesión: cualquier pantalla puede preguntar quién entró o si puede hacer algo,
// sin que le pasemos el usuario de mano en mano.
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

  // Si la API dice «token vencido», acá nos enteramos y cerramos la sesión solos.
  useEffect(() => {
    window.addEventListener('sesion-vencida', salir);
    return () => window.removeEventListener('sesion-vencida', salir);
  }, [salir]);

  const usuario = sesion?.usuario ?? null;
  // puede('PED_GESTIONAR') → ¿este usuario tiene ese permiso? Sirve para mostrar u ocultar botones.
  // Ojo: esto es solo para la vista; la seguridad de verdad la vuelve a revisar Django en cada consulta.
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
