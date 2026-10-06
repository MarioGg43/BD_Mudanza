# Permisos editables: plan de implementación

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Objetivo:** que el acceso de todo el sistema dependa de los permisos (PERMISOS_ROLES) y que roles y permisos se editen desde una pantalla.

**Arquitectura:**
- `usuarios/permisos.py` concentra el catálogo de permisos, la sesión (`get_usuario_actual`), los decoradores y la pantalla de inicio de cada usuario.
- `usuarios/reglas_roles.py` tiene los candados y las operaciones del ABM de roles.
- Un procesador de contexto deja los permisos disponibles en todas las plantillas.

**Stack:** Django 5.0, MySQL 8 en Docker, plantillas Bootstrap de marca (`vehiculos/base.html` + `usuarios/static/css/marca.css`) y Tailwind en el panel.

**Especificación:** `docs/superpowers/specs/2026-10-06-permisos-editables-design.md`

## Restricciones globales

- Los comandos de Django corren en el contenedor: `docker exec mudanzas_web python manage.py ...`.
- Al terminar cada tarea: toda la suite en verde (`docker exec mudanzas_web python manage.py test`) y `makemigrations --check --dry-run` sin cambios.
- El catálogo tiene exactamente 15 permisos, con los códigos de la sección 3 de la especificación. `MUDANZAS_ADMIN` deja de existir.
- `ROLES_DEL_SISTEMA = ('Administrador', 'Cliente', 'Chofer')`.
- Respuestas: en pantallas, sin sesión → `login` y sin permiso → 403 (salvo panel y portal, que redirigen a `pantalla_inicio`). En operaciones JSON del panel: sin sesión → 401 `{'ok': False, 'error': 'Debe iniciar sesion.'}` y sin permiso → 403 `{'ok': False, 'error': 'No tenés permiso para esta operación.'}`.
- Mensaje del candado de gestor: `El sistema tiene que quedar con al menos un usuario activo que pueda gestionar roles.`
- Textos en español rioplatense. No se agregan dependencias.

---

### Tarea 1: Catálogo, permisos.py, datos y migración

**Archivos:**
- Crear: `usuarios/permisos.py`, `usuarios/context_processors.py`, `usuarios/migrations/0006_permisos_editables.py`, `usuarios/test_permisos.py`
- Modificar: `usuarios/views.py` (mover `get_usuario_actual`), `pedidos/permisos.py`, `usuarios/management/commands/init_data.py`, `core/settings.py`, `usuarios/tests.py` (conteos)

**Interfaces que produce:**
- `usuarios.permisos.CATALOGO`: `list[tuple[str, str, str]]` (área, código, descripción).
- `usuarios.permisos.PERMISOS_INICIALES`: `dict[str, list[str]]` (nombre del rol → códigos).
- `get_usuario_actual(request) -> Usuario | None`, `permisos_de(usuario) -> set[str]` y `tiene_permiso(usuario, codigo) -> bool`.
- `requiere_permiso(codigo)` y `requiere_permiso_api(codigo)`, decoradores que dejan `request.usuario`.
- `pantalla_inicio(usuario) -> HttpResponseRedirect`. Usa las URL `admin_dashboard`, `pedidos_lista`, `usuario_portal` y `sin_permisos`; esta última se crea en la Tarea 2, así que en esta tarea no se llama desde ninguna vista.
- Procesador de contexto `usuarios.context_processors.seguridad`, que deja `usuario_sesion` y `permisos`.

- [ ] **Paso 1: Pruebas que fallan.** Crear `usuarios/test_permisos.py`:

```python
"""Catálogo de permisos, datos iniciales y migración de datos."""
import importlib
import io

from django.apps import apps
from django.core.management import call_command
from django.test import TestCase

from usuarios.models import Permiso, PermisoRol, Rol
from usuarios.permisos import CATALOGO, PERMISOS_INICIALES, permisos_de, tiene_permiso
from usuarios.models import Usuario

CODIGOS = [c for _, c, _ in CATALOGO]


def permisos_del_rol(nombre):
    return set(PermisoRol.objects.filter(idRol__nom_rol=nombre)
               .values_list('idPermiso__nom_permiso', flat=True))


class CatalogoTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command('init_data', stdout=io.StringIO())

    def test_catalogo_de_15_permisos(self):
        self.assertEqual(len(CODIGOS), 15)
        self.assertEqual(set(Permiso.objects.values_list('nom_permiso', flat=True)), set(CODIGOS))
        self.assertNotIn('MUDANZAS_ADMIN', CODIGOS)

    def test_permisos_iniciales(self):
        for rol, codigos in PERMISOS_INICIALES.items():
            self.assertEqual(permisos_del_rol(rol), set(codigos), rol)
        self.assertNotIn('PED_REGISTRAR', PERMISOS_INICIALES['Administrador'])
        self.assertEqual(len(PERMISOS_INICIALES['Administrador']), 14)

    def test_init_data_no_repone_un_permiso_quitado(self):
        PermisoRol.objects.filter(idRol__nom_rol='Administrador', idPermiso__nom_permiso='USR_BAJA').delete()
        call_command('init_data', stdout=io.StringIO())
        self.assertNotIn('USR_BAJA', permisos_del_rol('Administrador'))

    def test_permisos_de_y_tiene_permiso(self):
        admin = Usuario.objects.get(DNI=35123456)
        self.assertIn('ROL_GESTIONAR', permisos_de(admin))
        self.assertTrue(tiene_permiso(admin, 'VEH_GESTIONAR'))
        self.assertFalse(tiene_permiso(admin, 'PED_REGISTRAR'))
        self.assertEqual(permisos_de(None), set())


class MigracionDatosTest(TestCase):
    def test_actualiza_una_base_vieja(self):
        call_command('init_data', stdout=io.StringIO())
        # simular la base anterior: MUDANZAS_ADMIN y sin los tres permisos nuevos
        Permiso.objects.filter(nom_permiso__in=['USR_CONSULTAR', 'USR_CAMBIAR_ROL', 'ROL_GESTIONAR']).delete()
        Permiso.objects.filter(nom_permiso='VEH_GESTIONAR').update(nom_permiso='MUDANZAS_ADMIN')
        migracion = importlib.import_module('usuarios.migrations.0006_permisos_editables')
        migracion.adelante(apps, None)
        self.assertFalse(Permiso.objects.filter(nom_permiso='MUDANZAS_ADMIN').exists())
        self.assertTrue({'USR_CONSULTAR', 'USR_CAMBIAR_ROL', 'ROL_GESTIONAR', 'VEH_GESTIONAR'}
                        <= permisos_del_rol('Administrador'))
        self.assertEqual(Permiso.objects.count(), 15)
```

En `usuarios/tests.py`, `EstructuraDERTest.test_datos_iniciales`: cambiar `Permiso.objects.count()` de 12 a 15 y los permisos del Administrador de 11 a 14.

- [ ] **Paso 2:** `docker exec mudanzas_web python manage.py test usuarios` debe fallar con `ModuleNotFoundError: No module named 'usuarios.permisos'`.

- [ ] **Paso 3: `usuarios/permisos.py`:**

```python
"""Control de acceso de todo el sistema: se consulta PERMISOS_ROLES, nunca el nombre del rol."""
from functools import wraps

from django.http import HttpResponseForbidden, JsonResponse
from django.shortcuts import redirect

from .models import PermisoRol, Usuario

# Catálogo fijo: desde la pantalla de roles los permisos se asignan, no se crean,
# porque un permiso que el código no controla no tendría ningún efecto.
CATALOGO = [
    ('Usuarios', 'USR_CONSULTAR', 'Ver el panel de usuarios'),
    ('Usuarios', 'USR_CREAR', 'Dar de alta usuarios'),
    ('Usuarios', 'USR_EDITAR_CORREO', 'Modificar el correo de un usuario'),
    ('Usuarios', 'USR_CAMBIAR_ROL', 'Cambiar el rol de un usuario'),
    ('Usuarios', 'USR_BAJA', 'Dar de baja y reactivar usuarios'),
    ('Usuarios', 'USR_RESET_CLAVE', 'Restablecer la clave de un usuario'),
    ('Roles', 'ROL_GESTIONAR', 'Ver, crear y editar roles y sus permisos'),
    ('Vehículos', 'VEH_GESTIONAR', 'Alta, modificación y baja de vehículos'),
    ('Personal', 'MUDANZAS_OPERAR', 'Ver el portal del personal y sus vehículos asignados'),
    ('Pedidos', 'PED_REGISTRAR', 'Registrar pedidos de mudanza'),
    ('Pedidos', 'PED_CONSULTAR', 'Consultar pedidos'),
    ('Pedidos', 'PED_GESTIONAR', 'Confirmar y finalizar pedidos (y ver los de todos)'),
    ('Pedidos', 'PED_ANULAR', 'Anular pedidos'),
    ('Pedidos', 'PED_COMPROBANTE', 'Emitir el comprobante del pedido'),
    ('Servicios', 'SRV_GESTIONAR', 'Alta, modificación y baja de servicios'),
]

PERMISOS_INICIALES = {
    'Administrador': [c for _, c, _ in CATALOGO if c != 'PED_REGISTRAR'],
    'Chofer': ['MUDANZAS_OPERAR'],
    'Ayudante de Carga': ['MUDANZAS_OPERAR'],
    'Cliente': ['PED_REGISTRAR', 'PED_CONSULTAR', 'PED_COMPROBANTE'],
}


def get_usuario_actual(request):
    dni = request.session.get('usuario_dni')
    if not dni:
        return None
    try:
        return Usuario.objects.select_related('idRol').get(DNI=dni, Activo=True)
    except Usuario.DoesNotExist:
        return None


def permisos_de(usuario):
    """Códigos de permiso del rol del usuario (se calculan una vez por objeto)."""
    if usuario is None:
        return set()
    if not hasattr(usuario, '_permisos'):
        usuario._permisos = set(PermisoRol.objects.filter(idRol_id=usuario.idRol_id)
                                .values_list('idPermiso__nom_permiso', flat=True))
    return usuario._permisos


def tiene_permiso(usuario, codigo):
    return codigo in permisos_de(usuario)


def requiere_permiso(codigo):
    """Para pantallas: sin sesión manda al login; sin el permiso responde 403."""
    def decorador(vista):
        @wraps(vista)
        def envoltura(request, *args, **kwargs):
            usuario = get_usuario_actual(request)
            if not usuario:
                return redirect('login')
            if not tiene_permiso(usuario, codigo):
                return HttpResponseForbidden('No tenés permiso para esta operación.')
            request.usuario = usuario
            return vista(request, *args, **kwargs)
        return envoltura
    return decorador


def requiere_permiso_api(codigo):
    """Para las operaciones JSON del panel: 401 sin sesión, 403 sin el permiso."""
    def decorador(vista):
        @wraps(vista)
        def envoltura(request, *args, **kwargs):
            usuario = get_usuario_actual(request)
            if not usuario:
                return JsonResponse({'ok': False, 'error': 'Debe iniciar sesion.'}, status=401)
            if not tiene_permiso(usuario, codigo):
                return JsonResponse({'ok': False, 'error': 'No tenés permiso para esta operación.'}, status=403)
            request.usuario = usuario
            return vista(request, *args, **kwargs)
        return envoltura
    return decorador


def pantalla_inicio(usuario):
    """La primera pantalla que le corresponde según sus permisos."""
    p = permisos_de(usuario)
    if 'USR_CONSULTAR' in p:
        return redirect('admin_dashboard')
    if p & {'PED_GESTIONAR', 'PED_REGISTRAR', 'PED_CONSULTAR'}:
        return redirect('pedidos_lista')
    if 'MUDANZAS_OPERAR' in p:
        return redirect('usuario_portal')
    return redirect('sin_permisos')
```

`usuarios/context_processors.py`:

```python
from .permisos import get_usuario_actual, permisos_de


def seguridad(request):
    """Deja en todas las plantillas el usuario de la sesión y sus permisos."""
    usuario = getattr(request, 'usuario', None) or get_usuario_actual(request)
    return {'usuario_sesion': usuario, 'permisos': permisos_de(usuario)}
```

En `core/settings.py`, agregar `'usuarios.context_processors.seguridad',` al final de `context_processors`.

En `usuarios/views.py`, borrar la función `get_usuario_actual` y agregar `from .permisos import get_usuario_actual  # noqa: F401 (la importan otras apps)` junto a los imports. `pedidos/permisos.py` se reemplaza por:

```python
"""Los permisos viven en usuarios.permisos; se reexportan para las vistas de pedidos."""
from usuarios.permisos import requiere_permiso, tiene_permiso  # noqa: F401
```

- [ ] **Paso 4: `init_data`.** Reemplazar los pasos 1 y 2 (desde `# 1. Permisos` hasta la última asignación de `PermisoRol` antes de `# 3. Sueldos`) por:

```python
        # 1. Permisos del catálogo (la descripción se mantiene al día)
        for _, codigo, descripcion in CATALOGO:
            p, creado = Permiso.objects.get_or_create(nom_permiso=codigo, defaults={'desc_permiso': descripcion})
            if not creado and p.desc_permiso != descripcion:
                p.desc_permiso = descripcion
                p.save(update_fields=['desc_permiso'])

        # 2. Roles: los permisos iniciales se cargan solo al crear el rol, para no pisar
        #    lo que se edite después desde la pantalla de roles.
        descripciones_rol = {
            'Administrador': 'Acceso total a la administración de seguridad y usuarios',
            'Chofer': 'Conducción de vehículos y visualización de rutas de mudanza',
            'Ayudante de Carga': 'Personal operativo de carga, descarga y embalaje de bultos',
            'Cliente': 'Cliente que registra y sigue sus pedidos de mudanza',
        }
        roles = {}
        for nombre, descripcion in descripciones_rol.items():
            rol, creado = Rol.objects.get_or_create(nom_rol=nombre, defaults={'desc_rol': descripcion})
            if creado:
                for p in Permiso.objects.filter(nom_permiso__in=PERMISOS_INICIALES[nombre]):
                    PermisoRol.objects.create(idRol=rol, idPermiso=p)
            roles[nombre] = rol
        r_admin, r_chofer = roles['Administrador'], roles['Chofer']
        r_ayudante, r_cliente = roles['Ayudante de Carga'], roles['Cliente']
```

y agregar `from usuarios.permisos import CATALOGO, PERMISOS_INICIALES` a los imports. Verificar que el resto del comando siga usando `r_admin`, `r_chofer`, `r_ayudante` y `r_cliente`.

- [ ] **Paso 5: migración `usuarios/migrations/0006_permisos_editables.py`.** Depende de la última migración existente (`0005_observacion_inventario`):

```python
from django.db import migrations

NUEVOS = [
    ('USR_CONSULTAR', 'Ver el panel de usuarios'),
    ('USR_CAMBIAR_ROL', 'Cambiar el rol de un usuario'),
    ('ROL_GESTIONAR', 'Ver, crear y editar roles y sus permisos'),
]


def adelante(apps, schema_editor):
    """Bases que ya existen: MUDANZAS_ADMIN pasa a VEH_GESTIONAR y el Administrador
    recibe los permisos nuevos. En una base vacía no hay roles y no asigna nada."""
    Permiso = apps.get_model('usuarios', 'Permiso')
    Rol = apps.get_model('usuarios', 'Rol')
    PermisoRol = apps.get_model('usuarios', 'PermisoRol')
    viejo = Permiso.objects.filter(nom_permiso='MUDANZAS_ADMIN').first()
    if viejo and not Permiso.objects.filter(nom_permiso='VEH_GESTIONAR').exists():
        viejo.nom_permiso = 'VEH_GESTIONAR'
        viejo.desc_permiso = 'Alta, modificación y baja de vehículos'
        viejo.save()
    nuevos = [Permiso.objects.get_or_create(nom_permiso=c, defaults={'desc_permiso': d})[0] for c, d in NUEVOS]
    admin = Rol.objects.filter(nom_rol='Administrador').first()
    if admin:
        vehiculos = Permiso.objects.filter(nom_permiso='VEH_GESTIONAR').first()
        for p in nuevos + ([vehiculos] if vehiculos else []):
            PermisoRol.objects.get_or_create(idRol=admin, idPermiso=p)


class Migration(migrations.Migration):
    dependencies = [('usuarios', '0005_observacion_inventario')]
    operations = [migrations.RunPython(adelante, migrations.RunPython.noop)]
```

- [ ] **Paso 6:** correr `migrate` y `init_data` en la base de desarrollo, y después toda la suite. Todo en verde.

- [ ] **Paso 7: commit** `Add the permission catalog, session helpers and data migration`.

---

### Tarea 2: El Hito 2 y la flota controlan por permisos

**Archivos:**
- Crear: `usuarios/reglas_roles.py` (solo la parte del gestor), `usuarios/templates/sin_permisos.html`, `usuarios/test_acceso.py`
- Modificar: `usuarios/views.py`, `usuarios/urls.py`, `usuarios/templates/usuario_portal.html`, `vehiculos/views.py`, `pedidos/views.py`

**Interfaces:**
- Consume: lo que produjo la Tarea 1.
- Produce:
  - `usuarios.reglas_roles.ROLES_DEL_SISTEMA` y `MENSAJE_SIN_GESTOR`;
  - `gestores_activos() -> QuerySet[Usuario]`;
  - `error_baja_gestor(usuario) -> str | None`;
  - `error_cambio_rol_gestor(usuario, nuevo_rol) -> str | None`;
  - la URL `sin_permisos` (`/sin-permisos/`).

- [ ] **Paso 1: pruebas que fallan.** Crear `usuarios/test_acceso.py`:

```python
"""Un rol armado a medida habilita exactamente lo que se le tildó."""
import io

from django.core.management import call_command
from django.test import TestCase

from usuarios.models import Permiso, PermisoRol, Rol, Usuario
from usuarios.utils import hash_password

ADMIN, CHOFER, AYUDANTE, CLIENTE = 35123456, 40987654, 38999888, 29876543


class BaseAcceso(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command('init_data', stdout=io.StringIO())
        cls.recepcion = Rol.objects.create(nom_rol='Recepcionista', desc_rol='Atiende a los clientes')
        for c in ('USR_CONSULTAR', 'USR_CREAR', 'PED_CONSULTAR', 'PED_GESTIONAR'):
            PermisoRol.objects.create(idRol=cls.recepcion, idPermiso=Permiso.objects.get(nom_permiso=c))
        cls.vacio = Rol.objects.create(nom_rol='Sin nada')
        for dni, usuario, rol in ((20111222, 'recepcion', cls.recepcion), (20333444, 'vacio', cls.vacio)):
            Usuario.objects.create(DNI=dni, Nombre='Test', Apellido=usuario, Correo=f'{usuario}@mail.com',
                                   NombreUsuario=usuario, Clave=hash_password('Clave123!'),
                                   DebeCambiarClave=False, idRol=rol)

    def entrar(self, dni):
        s = self.client.session
        s['usuario_dni'] = dni
        s.save()


class RolAMedidaTest(BaseAcceso):
    def setUp(self):
        self.entrar(20111222)

    def test_entra_al_panel_y_da_de_alta(self):
        self.assertEqual(self.client.get('/panel/').status_code, 200)
        r = self.client.post('/usuarios/alta/', {'dni': '30111222', 'apellido': 'Pérez', 'nombre': 'Ana',
                                                 'correo': 'ana@mail.com', 'clave': 'Cliente123!',
                                                 'idRol': Rol.objects.get(nom_rol='Cliente').id_rol})
        self.assertTrue(r.json()['ok'])

    def test_lo_que_no_se_le_tildo_da_403(self):
        for url in (f'/usuarios/{CHOFER}/baja/', f'/usuarios/{CHOFER}/cambiar-rol/',
                    f'/usuarios/{CHOFER}/restablecer-clave/', f'/usuarios/{CHOFER}/modificar-correo/'):
            self.assertEqual(self.client.post(url).status_code, 403, url)
        self.assertEqual(self.client.get('/vehiculos/').status_code, 403)

    def test_pedidos_confirma_pero_no_anula(self):
        self.assertEqual(self.client.get('/pedidos/').status_code, 200)
        p = Usuario.objects.get(DNI=CLIENTE).pedidos.first()
        self.assertEqual(self.client.get(f'/pedidos/{p.pk}/anular/').status_code, 403)

    def test_login_lo_lleva_al_panel(self):
        self.client.get('/logout/')
        r = self.client.post('/login/', {'usuario': 'recepcion', 'clave': 'Clave123!'})
        self.assertRedirects(r, '/panel/')


class PantallaInicioTest(BaseAcceso):
    def test_cada_rol_inicial_llega_a_su_pantalla(self):
        for dni, destino in ((ADMIN, '/panel/'), (CLIENTE, '/pedidos/'), (CHOFER, '/portal/'),
                             (AYUDANTE, '/portal/')):
            self.entrar(dni)
            self.assertRedirects(self.client.get('/'), destino, msg_prefix=str(dni))

    def test_un_rol_sin_permisos_llega_a_sin_permisos(self):
        self.entrar(20333444)
        self.assertRedirects(self.client.get('/'), '/sin-permisos/')
        self.assertContains(self.client.get('/sin-permisos/'), 'todavía no tiene pantallas asignadas')
        self.assertRedirects(self.client.get('/panel/'), '/sin-permisos/')
        self.assertRedirects(self.client.get('/portal/'), '/sin-permisos/')

    def test_sin_permisos_requiere_sesion(self):
        self.assertRedirects(self.client.get('/sin-permisos/'), '/login/')


class GestorActivoTest(BaseAcceso):
    def setUp(self):
        self.entrar(ADMIN)
        self.admin_rol = Rol.objects.get(nom_rol='Administrador')

    def test_no_se_da_de_baja_al_unico_gestor(self):
        # el recepcionista recibe USR_BAJA; el admin es el único gestor de roles
        PermisoRol.objects.create(idRol=self.recepcion, idPermiso=Permiso.objects.get(nom_permiso='USR_BAJA'))
        self.entrar(20111222)
        r = self.client.post(f'/usuarios/{ADMIN}/baja/')
        self.assertEqual(r.status_code, 400)
        self.assertEqual(r.json()['error'],
                         'El sistema tiene que quedar con al menos un usuario activo que pueda gestionar roles.')
        self.assertTrue(Usuario.objects.get(DNI=ADMIN).Activo)

    def test_cambiar_rol_no_deja_al_sistema_sin_gestor(self):
        from usuarios.reglas_roles import error_cambio_rol_gestor, MENSAJE_SIN_GESTOR
        admin = Usuario.objects.get(DNI=ADMIN)
        chofer_rol = Rol.objects.get(nom_rol='Chofer')
        self.assertEqual(error_cambio_rol_gestor(admin, chofer_rol), MENSAJE_SIN_GESTOR)
        Usuario.objects.filter(DNI=CHOFER).update(idRol=self.admin_rol)
        self.assertIsNone(error_cambio_rol_gestor(admin, chofer_rol))

    def test_baja_del_unico_gestor_por_regla(self):
        from usuarios.reglas_roles import error_baja_gestor, MENSAJE_SIN_GESTOR
        admin = Usuario.objects.get(DNI=ADMIN)
        self.assertEqual(error_baja_gestor(admin), MENSAJE_SIN_GESTOR)
        self.assertIsNone(error_baja_gestor(Usuario.objects.get(DNI=CHOFER)))
```

- [ ] **Paso 2:** `docker exec mudanzas_web python manage.py test usuarios.test_acceso` debe fallar (404 en `/sin-permisos/`, 403 en el panel del recepcionista, etc.).

- [ ] **Paso 3: `usuarios/reglas_roles.py`**, la parte del gestor (la Tarea 4 agrega el ABM):

```python
"""Reglas de roles: candados para que el sistema nunca quede sin quien lo administre."""
from .models import Usuario

ROLES_DEL_SISTEMA = ('Administrador', 'Cliente', 'Chofer')
MENSAJE_SIN_GESTOR = 'El sistema tiene que quedar con al menos un usuario activo que pueda gestionar roles.'


def gestores_activos():
    """Usuarios activos cuyo rol tiene ROL_GESTIONAR."""
    return Usuario.objects.filter(Activo=True, idRol__permisos__nom_permiso='ROL_GESTIONAR').distinct()


def _es_gestor(usuario):
    return usuario.Activo and gestores_activos().filter(pk=usuario.pk).exists()


def error_baja_gestor(usuario):
    if _es_gestor(usuario) and not gestores_activos().exclude(pk=usuario.pk).exists():
        return MENSAJE_SIN_GESTOR
    return None


def error_cambio_rol_gestor(usuario, nuevo_rol):
    nuevo_gestiona = nuevo_rol.permisos.filter(nom_permiso='ROL_GESTIONAR').exists()
    if not nuevo_gestiona and error_baja_gestor(usuario):
        return MENSAJE_SIN_GESTOR
    return None
```

- [ ] **Paso 4: `usuarios/views.py`:**
  - Borrar `solo_admin` y `redirigir_segun_rol`. Importar `from .permisos import get_usuario_actual, pantalla_inicio, requiere_permiso, requiere_permiso_api, tiene_permiso` y `from .reglas_roles import error_baja_gestor, error_cambio_rol_gestor`.
  - En `login_view` y `cambiar_clave_obligatoria`, `return redirigir_segun_rol(usuario)` pasa a `return pantalla_inicio(usuario)`.
  - Cada operación JSON lleva, debajo del `@require_POST` / `@require_GET` existente, `@requiere_permiso_api('<CÓDIGO>')`, y deja de llamar a `solo_admin`. Donde usaba `actual`, pasa a usar `request.usuario`. Los códigos son:
    - `alta_usuario` y `preview_username_view`: USR_CREAR;
    - `modificar_correo`: USR_EDITAR_CORREO;
    - `baja_usuario` y `reactivar_usuario`: USR_BAJA;
    - `restablecer_clave`: USR_RESET_CLAVE;
    - `cambiar_rol`: USR_CAMBIAR_ROL.
  - En `baja_usuario`, reemplazar todo el bloque «el sistema no puede quedarse sin administradores activos» por:

```python
    error = error_baja_gestor(usuario)
    if error:
        return JsonResponse({'ok': False, 'error': error}, status=400)
```

  - En `cambiar_rol`, después de comprobar que el rol nuevo es distinto del anterior, agregar el mismo bloque con `error_cambio_rol_gestor(usuario, rol)`. Borrar el comentario sobre «último administrador».
  - En `admin_dashboard`, reemplazar el `if usuario_actual.idRol.nom_rol.lower() != 'administrador': return redirect('usuario_portal')` por `if not tiene_permiso(usuario_actual, 'USR_CONSULTAR'): return pantalla_inicio(usuario_actual)`.
  - En `usuario_portal`, reemplazar el `if ... == 'cliente': return redirect('pedidos_lista')` por `if not tiene_permiso(usuario_actual, 'MUDANZAS_OPERAR'): return pantalla_inicio(usuario_actual)`. Renombrar la variable de contexto `permisos` a `permisos_rol`, para no chocar con el procesador de contexto, y actualizar `usuario_portal.html` (`{% for perm in permisos %}` pasa a `{% for perm in permisos_rol %}`).
  - Agregar la vista:

```python
def sin_permisos(request):
    if not get_usuario_actual(request):
        return redirect('login')
    return render(request, 'sin_permisos.html')
```

  - En `usuarios/urls.py`, agregar `path('sin-permisos/', views.sin_permisos, name='sin_permisos'),`.
  - `usuarios/templates/sin_permisos.html`:

```html
{% extends 'vehiculos/base.html' %}
{% block title %}Sin pantallas asignadas{% endblock %}
{% block content %}
<div class="card-panel p-4 p-md-5 mx-auto text-center" style="max-width: 560px;">
    <span class="icono-marca mb-3"><i class="bi bi-shield-lock fs-4"></i></span>
    <h1 class="h4 fw-bold">Tu rol todavía no tiene pantallas asignadas</h1>
    <p class="text-muted">Pedile al administrador que te asigne permisos.</p>
    <a href="{% url 'logout' %}" class="btn btn-success fw-bold px-4">Salir</a>
</div>
{% endblock %}
```

- [ ] **Paso 5: vehículos y pedidos.**
  - En `vehiculos/views.py`, borrar `solo_admin_pagina` y su import de `wraps`. Usar `from usuarios.permisos import get_usuario_actual, pantalla_inicio, requiere_permiso`, y cambiar cada `@solo_admin_pagina` por `@requiere_permiso('VEH_GESTIONAR')`.
  - En `inicio`, `redirigir_segun_rol(actual)` pasa a `pantalla_inicio(actual)`.
  - En `pedidos/views.py`, cambiar el import y el uso de `redirigir_segun_rol` por `pantalla_inicio` (de `usuarios.permisos`).
  - Buscar con `grep -rn "redirigir_segun_rol\|solo_admin" --include=*.py` y no debe quedar ninguno fuera de las pruebas.

- [ ] **Paso 6:** toda la suite en verde. Las pruebas existentes del Hito 2 que sigan esperando el texto «último administrador» se adaptan al mensaje nuevo, sin cambiar lo que verifican.

- [ ] **Paso 7: commit** `Check the Hito 2 screens and the fleet by permission instead of role name`.

---

### Tarea 3: Menú y botones según los permisos

**Archivos:** `vehiculos/templates/vehiculos/base.html`, `usuarios/templates/admin_dashboard.html`, `usuarios/test_acceso.py` (agregar pruebas)

**Interfaces:** consume `permisos` y `usuario_sesion` del procesador de contexto. La URL `roles_lista` todavía no existe (se crea en la Tarea 4): en esta tarea no se enlaza Roles.

- [ ] **Paso 1: pruebas que fallan** (agregar a `usuarios/test_acceso.py`):

```python
class MenuYBotonesTest(BaseAcceso):
    def test_menu_del_recepcionista(self):
        self.entrar(20111222)
        r = self.client.get('/pedidos/')
        self.assertContains(r, 'href="/panel/"')
        self.assertContains(r, 'href="/pedidos/"')
        self.assertNotContains(r, 'href="/vehiculos/"')
        self.assertNotContains(r, 'href="/servicios/"')
        self.assertNotContains(r, 'href="/pedidos/nuevo/"')

    def test_menu_del_cliente(self):
        self.entrar(CLIENTE)
        r = self.client.get('/pedidos/')
        self.assertContains(r, 'Mis pedidos')
        self.assertContains(r, 'href="/pedidos/nuevo/"')
        self.assertNotContains(r, 'href="/panel/"')

    def test_panel_sin_usr_baja_no_muestra_baja(self):
        self.entrar(20111222)
        r = self.client.get('/panel/')
        self.assertContains(r, 'Alta de Usuario')
        self.assertNotContains(r, 'bajaUsuario(')
        self.assertNotContains(r, 'abrirModalRestablecer(')
        self.entrar(ADMIN)
        self.assertContains(self.client.get('/panel/'), 'bajaUsuario(')
```

Antes de escribir la prueba, abrir `usuarios/templates/admin_dashboard.html` y confirmar los nombres reales de las funciones JS de cada botón (alta, modificar correo, restablecer clave, baja, reactivar, cambiar rol). Si difieren de `bajaUsuario(` o `abrirModalRestablecer(`, usar los reales en la prueba.

- [ ] **Paso 2:** confirmar que fallan.

- [ ] **Paso 3: `vehiculos/base.html`.** Reemplazar el bloque `{% with rol=request.session.usuario_rol ... %} ... {% endwith %}` del menú por uno que decide con `permisos`, conservando las clases `activo` / `aria-current` actuales según la ruta:
  - `USR_CONSULTAR` → «Usuarios» (`admin_dashboard`);
  - `VEH_GESTIONAR` → «Vehículos»;
  - `PED_CONSULTAR` → «Pedidos» si además tiene `PED_GESTIONAR`, y si no «Mis pedidos»;
  - `PED_REGISTRAR` → «Pedir mudanza»;
  - `SRV_GESTIONAR` → «Servicios»;
  - `MUDANZAS_OPERAR` → «Portal».

  Con `usuario_sesion` aparece «Salir»; sin él, «Crear cuenta» e «Ingresar», como ahora.

- [ ] **Paso 4: `admin_dashboard.html`.**
  - Encabezado: cada enlace (Flota, Pedidos, Servicios) aparece solo con su permiso.
  - Botón «Alta de Usuario»: solo con `USR_CREAR`.
  - En cada fila:
    - selector y botón de cambiar rol: con `USR_CAMBIAR_ROL` (sin el permiso se muestra el nombre del rol como texto, igual que hoy para el propio usuario);
    - modificar correo: con `USR_EDITAR_CORREO`;
    - restablecer clave: con `USR_RESET_CLAVE`;
    - baja y reactivar: con `USR_BAJA`.
  - Los modales pueden quedar en la página; lo que se oculta son los botones que los abren.
  - Usar `{% if 'USR_BAJA' in permisos %}`.

- [ ] **Paso 5:** suite en verde. Revisar en el navegador `/panel/` como `sarmientoc` (todo visible) y como un recepcionista creado en el panel de Django o con `init_data` + shell (solo alta).

- [ ] **Paso 6: commit** `Show menu options and panel buttons by permission`.

---

### Tarea 4: ABM de roles

**Archivos:**
- Crear: `usuarios/roles.py`, `usuarios/forms.py`, `usuarios/templates/roles/lista.html`, `usuarios/templates/roles/form.html`, `usuarios/test_roles.py`
- Modificar: `usuarios/reglas_roles.py`, `usuarios/urls.py`, `vehiculos/templates/vehiculos/base.html` (enlace Roles), `usuarios/templates/admin_dashboard.html` (enlace Roles)

**Interfaces:**
- Produce:
  - `reglas_roles.ErrorRol(errores)`, con `.errores` como dict (la clave `'__all__'` es un error general);
  - `guardar_rol(rol | None, nombre, descripcion, codigos, actor) -> Rol`;
  - `eliminar_rol(rol) -> None`;
  - las URL `roles_lista`, `roles_crear`, `roles_editar` (`id_rol`) y `roles_eliminar` (`id_rol`, POST).

- [ ] **Paso 1: pruebas que fallan.** Crear `usuarios/test_roles.py`:

```python
"""ABM de roles y sus candados."""
import io

from django.core.management import call_command
from django.test import TestCase

from usuarios.models import PermisoRol, Rol, Usuario

ADMIN, CHOFER, CLIENTE = 35123456, 40987654, 29876543


def codigos(rol):
    return set(PermisoRol.objects.filter(idRol=rol).values_list('idPermiso__nom_permiso', flat=True))


class RolesTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command('init_data', stdout=io.StringIO())

    def setUp(self):
        s = self.client.session
        s['usuario_dni'] = ADMIN
        s.save()

    def test_lista_con_permisos_y_usuarios(self):
        r = self.client.get('/roles/')
        self.assertContains(r, 'Administrador')
        self.assertContains(r, 'ROL_GESTIONAR')
        self.assertContains(r, 'Nuevo rol')

    def test_crear_rol_con_permisos(self):
        r = self.client.post('/roles/nuevo/', {'nombre': 'Recepcionista', 'descripcion': 'Atiende',
                                               'permisos': ['USR_CONSULTAR', 'PED_CONSULTAR']})
        self.assertRedirects(r, '/roles/')
        self.assertEqual(codigos(Rol.objects.get(nom_rol='Recepcionista')), {'USR_CONSULTAR', 'PED_CONSULTAR'})

    def test_editar_permisos(self):
        rol = Rol.objects.create(nom_rol='Recepcionista')
        self.client.post(f'/roles/{rol.pk}/editar/', {'nombre': 'Recepción', 'permisos': ['PED_GESTIONAR']})
        rol.refresh_from_db()
        self.assertEqual((rol.nom_rol, codigos(rol)), ('Recepción', {'PED_GESTIONAR'}))

    def test_nombre_repetido(self):
        r = self.client.post('/roles/nuevo/', {'nombre': 'chofer', 'permisos': []})
        self.assertIn('nombre', r.context['form'].errors)

    def test_no_se_renombra_un_rol_del_sistema(self):
        cliente = Rol.objects.get(nom_rol='Cliente')
        r = self.client.post(f'/roles/{cliente.pk}/editar/', {'nombre': 'Clientes', 'permisos': ['PED_CONSULTAR']})
        self.assertIn('nombre', r.context['form'].errors)
        self.assertTrue(Rol.objects.filter(nom_rol='Cliente').exists())

    def test_se_editan_los_permisos_de_un_rol_del_sistema(self):
        chofer = Rol.objects.get(nom_rol='Chofer')
        self.client.post(f'/roles/{chofer.pk}/editar/', {'nombre': 'Chofer',
                                                          'permisos': ['MUDANZAS_OPERAR', 'PED_CONSULTAR']})
        self.assertEqual(codigos(chofer), {'MUDANZAS_OPERAR', 'PED_CONSULTAR'})

    def test_eliminar_rol_sin_usuarios(self):
        rol = Rol.objects.create(nom_rol='Temporal')
        self.assertRedirects(self.client.post(f'/roles/{rol.pk}/eliminar/'), '/roles/')
        self.assertFalse(Rol.objects.filter(pk=rol.pk).exists())

    def test_no_se_elimina_con_usuarios_ni_del_sistema(self):
        ayudante = Rol.objects.get(nom_rol='Ayudante de Carga')  # tiene a romerol
        self.client.post(f'/roles/{ayudante.pk}/eliminar/')
        self.assertTrue(Rol.objects.filter(pk=ayudante.pk).exists())
        chofer_sin_usuarios = Rol.objects.get(nom_rol='Chofer')
        Usuario.objects.filter(idRol=chofer_sin_usuarios).update(idRol=ayudante)
        self.client.post(f'/roles/{chofer_sin_usuarios.pk}/eliminar/')
        self.assertTrue(Rol.objects.filter(pk=chofer_sin_usuarios.pk).exists())

    def test_eliminar_solo_por_post(self):
        rol = Rol.objects.create(nom_rol='Temporal')
        self.assertEqual(self.client.get(f'/roles/{rol.pk}/eliminar/').status_code, 405)

    def test_no_te_podes_quitar_rol_gestionar(self):
        admin = Rol.objects.get(nom_rol='Administrador')
        r = self.client.post(f'/roles/{admin.pk}/editar/', {'nombre': 'Administrador', 'permisos': ['USR_CONSULTAR']})
        self.assertIn('No podés quitarte el permiso de gestionar roles.', r.context['form'].errors['permisos'])
        self.assertIn('ROL_GESTIONAR', codigos(admin))

    def test_solo_con_rol_gestionar(self):
        s = self.client.session
        s['usuario_dni'] = CLIENTE
        s.save()
        self.assertEqual(self.client.get('/roles/').status_code, 403)

    def test_menu_muestra_roles_al_admin(self):
        self.assertContains(self.client.get('/pedidos/'), 'href="/roles/"')
```

Agregar además esta prueba directa de la regla de gestor, con un estado limpio:

```python
    def test_regla_sin_gestor_al_editar(self):
        from usuarios.reglas_roles import ErrorRol, MENSAJE_SIN_GESTOR, guardar_rol
        from usuarios.models import Permiso
        gestor = Rol.objects.create(nom_rol='Gestor')
        PermisoRol.objects.create(idRol=gestor, idPermiso=Permiso.objects.get(nom_permiso='ROL_GESTIONAR'))
        Usuario.objects.filter(DNI=CHOFER).update(idRol=gestor)
        admin_rol = Rol.objects.get(nom_rol='Administrador')
        PermisoRol.objects.filter(idRol=admin_rol, idPermiso__nom_permiso='ROL_GESTIONAR').delete()
        actor = Usuario.objects.get(DNI=ADMIN)  # ya no gestiona, pero lo usamos como actor de la regla
        with self.assertRaises(ErrorRol) as ctx:
            guardar_rol(gestor, 'Gestor', '', [], actor)
        self.assertEqual(ctx.exception.errores['permisos'], MENSAJE_SIN_GESTOR)
```

- [ ] **Paso 2:** confirmar que fallan (404 en `/roles/`).

- [ ] **Paso 3: reglas.** Agregar a `usuarios/reglas_roles.py`:

```python
from django.db import transaction

from .models import Permiso, PermisoRol, Rol
from .permisos import CATALOGO

CODIGOS_VALIDOS = {c for _, c, _ in CATALOGO}


class ErrorRol(Exception):
    def __init__(self, errores):
        if isinstance(errores, str):
            errores = {'__all__': errores}
        self.errores = errores
        super().__init__(' '.join(errores.values()))


def guardar_rol(rol, nombre, descripcion, codigos, actor):
    """Crea (rol=None) o edita un rol y deja exactamente esos permisos."""
    nombre = (nombre or '').strip()
    descripcion = (descripcion or '').strip() or None
    codigos = set(codigos or [])
    errores = {}
    if codigos - CODIGOS_VALIDOS:
        errores['permisos'] = 'Hay permisos que no existen.'
    if not nombre:
        errores['nombre'] = 'Escribí el nombre del rol.'
    elif len(nombre) > 100:
        errores['nombre'] = 'El nombre puede tener hasta 100 caracteres.'
    elif Rol.objects.filter(nom_rol__iexact=nombre).exclude(pk=getattr(rol, 'pk', None)).exists():
        errores['nombre'] = 'Ya existe un rol con ese nombre.'
    if rol and rol.nom_rol in ROLES_DEL_SISTEMA and nombre != rol.nom_rol:
        errores['nombre'] = f'«{rol.nom_rol}» es un rol del sistema: no se le puede cambiar el nombre.'
    if descripcion and len(descripcion) > 100:
        errores['descripcion'] = 'La descripción puede tener hasta 100 caracteres.'
    if rol and 'ROL_GESTIONAR' not in codigos and rol.permisos.filter(nom_permiso='ROL_GESTIONAR').exists():
        if actor.idRol_id == rol.pk:
            errores['permisos'] = 'No podés quitarte el permiso de gestionar roles.'
        elif not gestores_activos().exclude(idRol=rol).exists():
            errores['permisos'] = MENSAJE_SIN_GESTOR
    if errores:
        raise ErrorRol(errores)
    with transaction.atomic():
        if rol is None:
            rol = Rol.objects.create(nom_rol=nombre, desc_rol=descripcion)
        else:
            rol.nom_rol, rol.desc_rol = nombre, descripcion
            rol.save()
        PermisoRol.objects.filter(idRol=rol).exclude(idPermiso__nom_permiso__in=codigos).delete()
        for p in Permiso.objects.filter(nom_permiso__in=codigos):
            PermisoRol.objects.get_or_create(idRol=rol, idPermiso=p)
    return rol


def eliminar_rol(rol):
    """Solo roles que no son del sistema y no tienen usuarios (nada los referencia)."""
    if rol.nom_rol in ROLES_DEL_SISTEMA:
        raise ErrorRol(f'«{rol.nom_rol}» es un rol del sistema y no se puede eliminar.')
    cantidad = rol.usuarios.count()
    if cantidad:
        raise ErrorRol(f'«{rol.nom_rol}» tiene {cantidad} usuario(s). Cambiales el rol antes de eliminarlo.')
    with transaction.atomic():
        PermisoRol.objects.filter(idRol=rol).delete()
        rol.delete()
```

(El `from .models import ...` existente se amplía con `Permiso, PermisoRol, Rol`.)

- [ ] **Paso 4: formulario y vistas.**

`usuarios/forms.py`:

```python
from django import forms

from .permisos import CATALOGO


class RolForm(forms.Form):
    nombre = forms.CharField(max_length=100, label='Nombre del rol')
    descripcion = forms.CharField(max_length=100, required=False, label='Descripción')
    permisos = forms.MultipleChoiceField(required=False, label='Permisos',
                                         choices=[(c, c) for _, c, _ in CATALOGO],
                                         widget=forms.CheckboxSelectMultiple)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for nombre in ('nombre', 'descripcion'):
            self.fields[nombre].widget.attrs['class'] = 'form-control'

    def grupos(self):
        """[(área, [(código, descripción, marcado)])] para dibujar las casillas agrupadas."""
        marcados = set(self['permisos'].value() or [])
        salida = []
        for area, codigo, descripcion in CATALOGO:
            if not salida or salida[-1][0] != area:
                salida.append((area, []))
            salida[-1][1].append((codigo, descripcion, codigo in marcados))
        return salida
```

`usuarios/roles.py`:

```python
"""ABM de roles: cada rol con los permisos que se le tildan."""
from django.contrib import messages
from django.db.models import Count
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from .forms import RolForm
from .models import Rol
from .permisos import requiere_permiso
from .reglas_roles import ROLES_DEL_SISTEMA, ErrorRol, eliminar_rol, guardar_rol


@requiere_permiso('ROL_GESTIONAR')
def lista(request):
    roles = (Rol.objects.annotate(cantidad=Count('usuarios', distinct=True))
             .prefetch_related('permisos').order_by('id_rol'))
    return render(request, 'roles/lista.html', {'roles': roles, 'del_sistema': ROLES_DEL_SISTEMA})


def _guardar(request, rol, titulo):
    if request.method == 'POST':
        form = RolForm(request.POST)
        if form.is_valid():
            d = form.cleaned_data
            try:
                guardado = guardar_rol(rol, d['nombre'], d['descripcion'], d['permisos'], request.usuario)
            except ErrorRol as e:
                for campo, mensaje in e.errores.items():
                    form.add_error(campo if campo in form.fields else None, mensaje)
            else:
                messages.success(request, f'Rol «{guardado.nom_rol}» guardado.')
                return redirect('roles_lista')
    else:
        inicial = {}
        if rol:
            inicial = {'nombre': rol.nom_rol, 'descripcion': rol.desc_rol or '',
                       'permisos': list(rol.permisos.values_list('nom_permiso', flat=True))}
        form = RolForm(initial=inicial)
    return render(request, 'roles/form.html', {
        'form': form, 'titulo': titulo, 'rol': rol,
        'nombre_fijo': bool(rol and rol.nom_rol in ROLES_DEL_SISTEMA)})


@requiere_permiso('ROL_GESTIONAR')
def crear(request):
    return _guardar(request, None, 'Nuevo rol')


@requiere_permiso('ROL_GESTIONAR')
def editar(request, id_rol):
    rol = get_object_or_404(Rol, pk=id_rol)
    return _guardar(request, rol, f'Editar «{rol.nom_rol}»')


@requiere_permiso('ROL_GESTIONAR')
@require_POST
def eliminar(request, id_rol):
    rol = get_object_or_404(Rol, pk=id_rol)
    try:
        nombre = rol.nom_rol
        eliminar_rol(rol)
        messages.success(request, f'Rol «{nombre}» eliminado.')
    except ErrorRol as e:
        messages.error(request, str(e))
    return redirect('roles_lista')
```

Sumar a `usuarios/urls.py` (con `from . import roles, views`):

```python
    path('roles/', roles.lista, name='roles_lista'),
    path('roles/nuevo/', roles.crear, name='roles_crear'),
    path('roles/<int:id_rol>/editar/', roles.editar, name='roles_editar'),
    path('roles/<int:id_rol>/eliminar/', roles.eliminar, name='roles_eliminar'),
```

- [ ] **Paso 5: plantillas** (extienden `vehiculos/base.html` y usan las clases de `marca.css`, como `servicios_lista.html` y `servicio_form.html`):
  - `roles/lista.html`:
    - título «Roles», con el subtítulo «Cada rol habilita solo los permisos que tiene tildados.» y el botón «Nuevo rol»;
    - tabla con Rol (y una etiqueta «del sistema» si corresponde), Descripción, Usuarios (`rol.cantidad`), Permisos (cada código como etiqueta `<span class="badge ...">`, con su descripción en `title`) y Acciones (Editar; Eliminar como formulario POST con `confirm()`, que solo aparece si `rol.cantidad == 0` y el rol no es del sistema).
  - `roles/form.html`:
    - campo nombre (con `readonly` y la ayuda «Es un rol del sistema: el nombre no se cambia.» cuando `nombre_fijo`) y campo descripción;
    - para cada área de `form.grupos`, un título y sus casillas `<input type="checkbox" name="permisos" value="CODIGO">`, marcadas según el tercer valor, con el código y la descripción;
    - los errores de cada campo y los no asociados a un campo;
    - botones Guardar y Cancelar.
  - Enlaces «Roles»:
    - en `vehiculos/base.html`, con `ROL_GESTIONAR`, después de «Usuarios»;
    - en el encabezado de `admin_dashboard.html`, también con `ROL_GESTIONAR`.

- [ ] **Paso 6:** suite en verde. Revisar en el navegador `/roles/`, «Nuevo rol» y editar «Chofer».

- [ ] **Paso 7: commit** `Add the roles screen to assign permissions to each role`.

---

### Tarea 5: Documentación

- [ ] `README.md`:
  - En «Reglas del Hito 2», reemplazar «Cada operación valida del lado del servidor que quien la llama sea un administrador activo» y «No se puede dar de baja al último administrador activo» por:
    - que el acceso se decide por los permisos del rol (tabla PERMISOS_ROLES);
    - que los roles y sus permisos se editan en `/roles/`;
    - los candados de roles.
  - Agregar la tabla del catálogo de 15 permisos con los permisos iniciales.
  - Agregar `/roles/` a la tabla de direcciones.
- [ ] Commit `Document permission-based access and the roles screen`.
