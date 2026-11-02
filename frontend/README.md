# Frontend en React — Mudanzas y Fletes Salta

SPA en **React + Vite** que consume la **API REST de Django** (app `api/` del proyecto).
Primera etapa: todo lo del **cliente** (login, registro, mis pedidos, pedir mudanza,
detalle, modificar, cancelar y comprobante PDF). Las demás pantallas siguen en Django
mientras se migran.

## Cómo se levanta

Con Docker (junto con el resto del sistema):

```bash
docker compose up -d
```

- Frontend React: http://localhost:5173
- Django (API en `/api/` y pantallas viejas): http://localhost:8002

Sin Docker (Node 20 o más): `npm install` y `npm run dev` dentro de `frontend/`.
Vite reenvía `/api` a Django (ver `vite.config.js`), así que el navegador ve un solo
origen y no hace falta CORS.

## Arquitectura (Unidad 4)

```
Componente / Página  →  Custom hook  →  Servicio  →  Axios (api.js)  →  API Django
```

| Carpeta | Qué hay |
|---|---|
| `src/services/api.js` | Instancia de Axios con `baseURL` de `VITE_API_URL` (`.env`) e **interceptores**: el de request agrega el token; el de response normaliza los errores (red, 4xx, 5xx) y cierra la sesión si llega un 401. |
| `src/services/*Service.js` | Una función por endpoint (`getAll`, `getById`, `create`, `update`, `cancelar`...). Los componentes no conocen URLs. |
| `src/hooks/` | `usePedidos`, `usePedido`, `useCatalogo`, `useVehiculosLibres`: estados **loading / éxito / error** y cancelación con `AbortController` en la limpieza de `useEffect`. |
| `src/context/AuthContext.jsx` | Quién está conectado y sus permisos, para toda la app. Guarda el token en `localStorage`. |
| `src/components/` | Navbar, RutaPrivada (protege rutas por permiso), ModalObjeto (popup «Agregar objeto» con la lógica de «Otro»), spinner, alerta de error, estado del pedido. |
| `src/pages/` | Una por ruta de React Router: `/login`, `/registro`, `/pedidos`, `/pedidos/nuevo`, `/pedidos/:id`, `/pedidos/:id/modificar`, `/pedidos/:id/cancelar` y la 404. |

## Contrato de la API

Todas las rutas empiezan con `/api`. Las que no son de login piden el encabezado
`Authorization: Bearer <token>` (401 sin token o vencido, 403 sin el permiso).
Los errores de validación vuelven con 400 y `{ "error": "...", "errores": { "campo": "mensaje" } }`.

| Método | Ruta | Qué hace | Permiso |
|---|---|---|---|
| POST | `/auth/login` | `{usuario, clave}` → `{token, usuario}` (DNI, usuario o correo) | — |
| POST | `/auth/registro` | Alta de cliente → `{token, usuario}` | — |
| GET | `/auth/yo` | El usuario del token | cualquiera |
| GET | `/catalogo` | Servicios principales y adicionales, objetos, límites | PED_REGISTRAR |
| GET | `/vehiculos-libres?fecha&hora&servicio[&pedido]` | Vehículos libres en ese horario | PED_REGISTRAR |
| GET | `/pedidos[?estado&desde&hasta]` | Mis pedidos (todos si gestiona) | PED_CONSULTAR |
| POST | `/pedidos` | Registrar un pedido | PED_REGISTRAR |
| GET | `/pedidos/:id` | Detalle (uno ajeno da 404) | PED_CONSULTAR |
| PUT | `/pedidos/:id` | Modificarlo hasta 24 h antes | PED_REGISTRAR |
| POST | `/pedidos/:id/cancelar` | `{motivo}`: cancelarlo hasta 24 h antes | PED_CONSULTAR |
| GET | `/pedidos/:id/comprobante` | Comprobante en PDF | PED_COMPROBANTE |

El token es el DNI firmado con la `SECRET_KEY` de Django y con fecha (vence a las 12 horas);
no se puede falsificar. Las reglas de negocio no se repiten en la API: llama a las mismas
funciones de `pedidos/reglas.py` que usan las pantallas de Django. Pruebas: `api/tests.py`.
