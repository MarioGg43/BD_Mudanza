import { api } from './api';
import { descargarPdf } from './descargas';

const get = async (url, signal, params) => (await api.get(url, { signal, params })).data;
const post = async (url, datos) => (await api.post(url, datos)).data;
const put = async (url, datos) => (await api.put(url, datos)).data;

// ABM de vehículos, servicios, objetos, usuarios y roles (api/views_abm.py y api/views_usuarios.py)
export const abmService = {
  vehiculos: (signal) => get('/vehiculos', signal),
  vehiculo: (patente, signal) => get(`/vehiculos/${patente}`, signal),
  crearVehiculo: (datos) => post('/vehiculos', datos),
  editarVehiculo: (patente, datos) => put(`/vehiculos/${patente}`, datos),
  bajaVehiculo: (patente) => post(`/vehiculos/${patente}/baja`),

  servicios: (signal) => get('/servicios', signal),
  servicio: (id, signal) => get(`/servicios/${id}`, signal),
  crearServicio: (datos) => post('/servicios', datos),
  editarServicio: (id, datos) => put(`/servicios/${id}`, datos),
  bajaServicio: (id) => post(`/servicios/${id}/baja`),

  objetos: (signal) => get('/objetos', signal),
  crearObjeto: (datos) => post('/objetos', datos),
  editarObjeto: (id, datos) => put(`/objetos/${id}`, datos),
  bajaObjeto: (id) => post(`/objetos/${id}/baja`),

  usuarios: (signal) => get('/usuarios', signal),
  nombreUsuario: (apellido, nombre, signal) => get('/usuarios/nombre', signal, { apellido, nombre }),
  crearUsuario: (datos) => post('/usuarios', datos),
  cambiarCorreo: (dni, correo) => put(`/usuarios/${dni}/correo`, { correo }),
  cambiarRol: (dni, idRol) => put(`/usuarios/${dni}/rol`, { id_rol: idRol }),
  bajaUsuario: (dni) => post(`/usuarios/${dni}/baja`),
  reactivarUsuario: (dni) => post(`/usuarios/${dni}/reactivar`),
  restablecerClave: (dni) => post(`/usuarios/${dni}/clave`),

  roles: (signal) => get('/roles', signal),
  crearRol: (datos) => post('/roles', datos),
  editarRol: (id, datos) => put(`/roles/${id}`, datos),
  eliminarRol: async (id) => (await api.delete(`/roles/${id}`)).data,

  auditoria: (filtros, signal) => get('/auditoria', signal, filtros),
  opcionesAuditoria: (signal) => get('/auditoria/opciones', signal),
  pdfAuditoria: (filtros) => descargarPdf('/auditoria/pdf', 'Auditoria.pdf', filtros),
};
