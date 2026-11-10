# Hito 3 — Pedido de mudanza: plan de implementación

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Objetivo:** el proceso completo del pedido de mudanza. El cliente lo registra; el administrador lo consulta, confirma, finaliza o anula. Además, comprobante imprimible, ABM de servicios y permisos controlados con la tabla PERMISOS.

**Arquitectura:** una app Django nueva, `pedidos`. Las reglas del negocio viven en `pedidos/reglas.py`, son funciones puras sobre el ORM y cada operación corre en `transaction.atomic()`. Las vistas son finas: validan formularios, llaman a `reglas` y muestran el resultado. Los permisos se controlan con `pedidos/permisos.py`, que consulta PERMISOS_ROLES. Los modelos siguen en `usuarios/models.py`, junto al resto del DER.

**Stack:** Django 5.0, MySQL 8 (Docker), plantillas con Bootstrap 5 (CDN, el mismo estilo que `vehiculos/base.html`) y JavaScript sin librerías.

**Especificación:** `docs/superpowers/specs/2026-10-05-hito3-pedidos-design.md`

## Restricciones globales

- Stack obligatorio: Django + Docker + MySQL. No se agregan dependencias a `requirements.txt`.
- Todo comando de Django corre dentro del contenedor: `docker exec mudanzas_web python manage.py ...`. Los contenedores tienen que estar levantados (`docker compose up -d`).
- Las tablas y columnas nuevas siguen los nombres del DER que figuran en la especificación (sección 3).
- Estados del pedido, exactamente: `Pendiente`, `Confirmado`, `Finalizado`, `Anulado`.
- Permisos, exactamente: `PED_REGISTRAR`, `PED_CONSULTAR`, `PED_GESTIONAR`, `PED_ANULAR`, `PED_COMPROBANTE`, `SRV_GESTIONAR`.
- Clienta de prueba: `gomezm` / `Cliente123!`, DNI 29876543, María Gómez, `maria.gomez@ejemplo.com`, tel. 3874112233.
- Nunca se borra un pedido: no existe ninguna vista que haga `delete()` sobre PEDIDOS, DETALLE_PEDIDOS o INVENTARIO_DETALLES.
- Los textos de la interfaz van en español rioplatense («Elegí», «Escribí»), como en el resto del sistema.
- Al terminar cada tarea tienen que pasar **todas** las pruebas: `docker exec mudanzas_web python manage.py test`.

## Mapa de archivos

| Archivo | Responsabilidad |
|---|---|
| `usuarios/models.py` | Campos nuevos de PEDIDOS, DETALLE_PEDIDOS, INVENTARIO_DETALLES y SERVICIOS |
| `usuarios/migrations/0002_hito3_pedidos.py` | Generada con `makemigrations` |
| `usuarios/migrations/0003_completar_pedidos_existentes.py` | Migración de datos para los pedidos anteriores al Hito 3 |
| `usuarios/management/commands/init_data.py` | Rol Cliente, permisos nuevos, clienta y pedido de ejemplo |
| `usuarios/utils.py` | `nombre_usuario_libre()` (compartida por el alta del Hito 2 y el registro de clientes) |
| `usuarios/views.py` | `redirigir_segun_rol()`; el cliente entra a `/pedidos/` |
| `pedidos/reglas.py` | Registrar, transiciones, vehículos libres y filtros de la consulta |
| `pedidos/permisos.py` | `tiene_permiso()` y el decorador `requiere_permiso()` |
| `pedidos/forms.py` | Formularios de pedido, inventario, filtros, anulación, registro y servicio |
| `pedidos/views.py` | Vistas del pedido y del registro de clientes |
| `pedidos/views_servicios.py` | ABM de servicios |
| `pedidos/urls.py` | Direcciones de la app |
| `pedidos/templates/pedidos/*.html` | Pantallas |
| `pedidos/test_reglas.py`, `pedidos/test_vistas.py`, `pedidos/test_servicios.py` | Pruebas |
| `vehiculos/templates/vehiculos/base.html` | Menú según el rol |
| `docs/sql/esquema_mudanzas.sql` | Script SQL del esquema para la entrega |

---

### Tarea 1: Campos nuevos del DER, migraciones y datos iniciales

**Archivos:**
- Modificar: `usuarios/models.py`, `usuarios/management/commands/init_data.py`, `usuarios/tests.py`
- Crear: `usuarios/migrations/0002_hito3_pedidos.py` (generada), `usuarios/migrations/0003_completar_pedidos_existentes.py`

**Interfaces:**
- Produce: `Pedido.PENDIENTE/CONFIRMADO/FINALIZADO/ANULADO` (str), `Pedido.ACTIVOS` (tupla con Pendiente y Confirmado), campos `Pedido.fecha_servicio, origen, destino, estado, total, fecha_anulacion, motivo_anulacion, usuario_anulacion`, propiedad `Pedido.peso_total` (Decimal), `DetallePedido.precio_unitario, subtotal`, `InventarioDetalle.Descripcion`, `Servicio.Activo`. Rol `Cliente`, los 6 permisos nuevos y el usuario `gomezm`.

- [ ] **Paso 1: Escribir las pruebas que fallan**

Agregar al final de `usuarios/tests.py`:

```python
class DatosHito3Test(BaseHito2):
    def test_rol_cliente_y_permisos(self):
        cliente = Rol.objects.get(nom_rol='Cliente')
        self.assertEqual(
            set(PermisoRol.objects.filter(idRol=cliente).values_list('idPermiso__nom_permiso', flat=True)),
            {'PED_REGISTRAR', 'PED_CONSULTAR', 'PED_COMPROBANTE'})
        admin = set(PermisoRol.objects.filter(idRol__nom_rol='Administrador')
                    .values_list('idPermiso__nom_permiso', flat=True))
        self.assertTrue({'PED_CONSULTAR', 'PED_GESTIONAR', 'PED_ANULAR',
                         'PED_COMPROBANTE', 'SRV_GESTIONAR'} <= admin)
        self.assertNotIn('PED_REGISTRAR', admin)

    def test_clienta_de_prueba(self):
        u = Usuario.objects.get(NombreUsuario='gomezm')
        self.assertEqual((u.DNI, u.idRol.nom_rol, u.DebeCambiarClave), (29876543, 'Cliente', False))
        self.assertTrue(u.verificar_clave('Cliente123!'))

    def test_pedido_de_ejemplo_con_campos_nuevos(self):
        p = Pedido.objects.get()
        self.assertEqual(p.idUsuario.NombreUsuario, 'gomezm')
        self.assertEqual(p.estado, Pedido.FINALIZADO)
        self.assertEqual(p.total, 185000)
        self.assertTrue(p.origen and p.destino)
        detalle = p.detalles.get()
        self.assertEqual((detalle.precio_unitario, detalle.subtotal), (185000, 185000))
        self.assertEqual(p.inventario.get().Descripcion, 'Cajas de libros')
        self.assertEqual(p.peso_total, 42 * Decimal('7.63'))

    def test_servicios_activos_por_defecto(self):
        self.assertFalse(Servicio.objects.filter(Activo=False).exists())
```

En el mismo archivo, agregar `from decimal import Decimal` debajo de `import io` y sumar `Servicio` al `from .models import (...)`. El resto de los imports (incluido `from .utils import ...`) queda igual.

Y ajustar las pruebas del Hito 2 que cuentan registros o usan el apellido Gómez (la clienta nueva se llama `gomezm`):

En `EstructuraDERTest.test_datos_iniciales`, reemplazar el cuerpo por:

```python
    def test_datos_iniciales(self):
        self.assertEqual(Rol.objects.count(), 4)
        self.assertEqual(Usuario.objects.count(), 4)
        self.assertEqual(Vehiculo.objects.count(), 4)
        self.assertEqual(Permiso.objects.count(), 12)
        # el administrador tiene todos los permisos menos registrar pedidos
        self.assertEqual(PermisoRol.objects.filter(idRol__nom_rol='Administrador').count(), 11)
        self.assertEqual(PermisoRol.objects.filter(idRol__nom_rol='Chofer').count(), 1)
```

En `EstructuraDERTest.test_init_data_se_puede_correr_dos_veces`, cambiar `self.assertEqual(Usuario.objects.count(), 3)` por `self.assertEqual(Usuario.objects.count(), 4)`.

En `BaseHito2.alta`, reemplazar el diccionario `base` por:

```python
        base = {'dni': '30111222', 'apellido': 'Pérez', 'nombre': 'Ana Laura',
                'correo': 'APEREZ@mail.com', 'clave': 'Cliente123!',
                'idRol': Rol.objects.get(nom_rol='Chofer').id_rol}
```

En `CrudUsuariosTest`:
- `test_alta_genera_usuario_y_exige_cambio`: `{'ok': True, 'usuario': 'pereza'}` y `u.Correo == 'aperez@mail.com'`.
- `test_alta_usuario_repetido_suma_numero`: esperar `'pereza1'`.
- `test_panel_lista_usuarios_y_filtro_activos`: esperar `4` y `3` en lugar de `3` y `2`.

- [ ] **Paso 2: Correr las pruebas y verificar que fallan**

Correr: `docker exec mudanzas_web python manage.py test usuarios`
Esperado: errores `AttributeError`/`FieldError` por campos que no existen (`estado`, `Activo`, etc.) y fallas de conteo.

- [ ] **Paso 3: Agregar los campos a los modelos**

En `usuarios/models.py`, agregar `from decimal import Decimal` arriba, junto a los otros imports.

En `class Servicio`, después de `Precio_base`:

```python
    Activo = models.BooleanField(default=True, db_column='Activo', verbose_name='Activo')
```

Reemplazar `class Pedido` completa por:

```python
class Pedido(models.Model):
    PENDIENTE, CONFIRMADO, FINALIZADO, ANULADO = 'Pendiente', 'Confirmado', 'Finalizado', 'Anulado'
    ESTADOS = [(e, e) for e in (PENDIENTE, CONFIRMADO, FINALIZADO, ANULADO)]
    ACTIVOS = (PENDIENTE, CONFIRMADO)  # ocupan el vehículo el día del servicio

    id_pedido = models.AutoField(primary_key=True)
    patente_vehiculo = models.ForeignKey(Vehiculo, on_delete=models.PROTECT, db_column='patente_vehiculos',
                                         related_name='pedidos', verbose_name='Vehículo')
    idUsuario = models.ForeignKey(Usuario, on_delete=models.PROTECT, db_column='id_usuario',
                                  related_name='pedidos', verbose_name='Usuario')
    Fecha_pedido = models.DateField(verbose_name='Fecha del pedido')

    # --- Hito 3: datos del proceso completo ---
    fecha_servicio = models.DateField(default=timezone.localdate, db_column='Fecha_servicio',
                                      verbose_name='Fecha de la mudanza')
    origen = models.CharField(max_length=200, default='', db_column='Direccion_origen', verbose_name='Desde')
    destino = models.CharField(max_length=200, default='', db_column='Direccion_destino', verbose_name='Hasta')
    estado = models.CharField(max_length=20, choices=ESTADOS, default=PENDIENTE, db_column='Estado_pedido')
    total = models.DecimalField(max_digits=12, decimal_places=2, default=0, db_column='Total_pedido')
    fecha_anulacion = models.DateTimeField(blank=True, null=True, db_column='Fec_anulacion')
    motivo_anulacion = models.CharField(max_length=200, blank=True, null=True, db_column='Motivo_anulacion')
    usuario_anulacion = models.ForeignKey(Usuario, on_delete=models.PROTECT, blank=True, null=True,
                                          db_column='id_usuario_anulacion', related_name='pedidos_anulados',
                                          verbose_name='Anulado por')

    class Meta:
        db_table = 'PEDIDOS'
        verbose_name = 'Pedido'
        verbose_name_plural = 'Pedidos'

    def __str__(self):
        return f'Pedido {self.id_pedido} - {self.Fecha_pedido}'

    @property
    def peso_total(self):
        return sum((i.Cantidad * i.Peso for i in self.inventario.all()), Decimal('0'))
```

En `class DetallePedido`, después de `idServicio`:

```python
    precio_unitario = models.DecimalField(max_digits=12, decimal_places=2, default=0,
                                          db_column='Precio_unitario', verbose_name='Precio unitario')
    subtotal = models.DecimalField(max_digits=12, decimal_places=2, default=0, db_column='Subtotal')
```

En `class InventarioDetalle`, antes de `Peso`:

```python
    Descripcion = models.CharField(max_length=100, default='', verbose_name='Descripción')
```

- [ ] **Paso 4: Generar la migración de esquema**

Correr: `docker exec mudanzas_web python manage.py makemigrations usuarios --name hito3_pedidos`
Esperado: `Migrations for 'usuarios': usuarios/migrations/0002_hito3_pedidos.py`, con un `Add field` por cada campo nuevo (13 en total).

- [ ] **Paso 5: Escribir la migración de datos**

Crear `usuarios/migrations/0003_completar_pedidos_existentes.py`:

```python
from django.db import migrations


def completar_pedidos_existentes(apps, schema_editor):
    """Los pedidos cargados antes del Hito 3 no tenían fecha de servicio, direcciones
    ni precios: se completan para que la consulta y el comprobante los muestren bien."""
    Pedido = apps.get_model('usuarios', 'Pedido')
    InventarioDetalle = apps.get_model('usuarios', 'InventarioDetalle')
    for pedido in Pedido.objects.all():
        total = 0
        for detalle in pedido.detalles.select_related('idServicio'):
            detalle.precio_unitario = detalle.subtotal = detalle.idServicio.Precio_base
            detalle.save(update_fields=['precio_unitario', 'subtotal'])
            total += detalle.subtotal
        pedido.fecha_servicio = pedido.Fecha_pedido
        pedido.origen = pedido.origen or 'Sin dato'
        pedido.destino = pedido.destino or 'Sin dato'
        pedido.estado = 'Finalizado'
        pedido.total = total
        pedido.save()
    InventarioDetalle.objects.filter(Descripcion='').update(Descripcion='Sin descripción')


class Migration(migrations.Migration):
    dependencies = [('usuarios', '0002_hito3_pedidos')]
    operations = [migrations.RunPython(completar_pedidos_existentes, migrations.RunPython.noop)]
```

- [ ] **Paso 6: Actualizar `init_data`**

En `usuarios/management/commands/init_data.py`:

a) En `permisos_data`, agregar después de `('MUDANZAS_OPERAR', ...)`:

```python
            ('PED_REGISTRAR', 'Permite registrar pedidos de mudanza'),
            ('PED_CONSULTAR', 'Permite consultar pedidos'),
            ('PED_GESTIONAR', 'Permite confirmar y finalizar pedidos'),
            ('PED_ANULAR', 'Permite anular pedidos'),
            ('PED_COMPROBANTE', 'Permite emitir el comprobante del pedido'),
            ('SRV_GESTIONAR', 'Permite dar de alta, modificar y dar de baja servicios'),
```

b) Después de crear `r_ayudante`, agregar el rol Cliente, y reemplazar la asignación de permisos (el bloque `for perm in permisos.values(): ...` y las dos líneas de chofer y ayudante) por:

```python
        r_cliente, _ = Rol.objects.get_or_create(
            nom_rol='Cliente',
            defaults={'desc_rol': 'Cliente que registra y sigue sus pedidos de mudanza'})

        # el administrador gestiona todo, pero los pedidos los registra el cliente
        for code, perm in permisos.items():
            if code != 'PED_REGISTRAR':
                PermisoRol.objects.get_or_create(idRol=r_admin, idPermiso=perm)
        PermisoRol.objects.get_or_create(idRol=r_chofer, idPermiso=permisos['MUDANZAS_OPERAR'])
        PermisoRol.objects.get_or_create(idRol=r_ayudante, idPermiso=permisos['MUDANZAS_OPERAR'])
        for code in ('PED_REGISTRAR', 'PED_CONSULTAR', 'PED_COMPROBANTE'):
            PermisoRol.objects.get_or_create(idRol=r_cliente, idPermiso=permisos[code])
```

c) En `usuarios_data`, agregar como cuarto elemento:

```python
            (29876543, 'Gómez', 'María', 'maria.gomez@ejemplo.com',
             '3874112233', 'Cliente123!', False, r_cliente, None),
```

d) Reemplazar el bloque `# 7. Un pedido de ejemplo...` hasta el `self.stdout.write(...'Pedido de ejemplo creado...')` inclusive por:

```python
        # 7. Un pedido de ejemplo de la clienta, ya finalizado, con detalle, inventario y cobranza
        cliente = Usuario.objects.filter(DNI=29876543).first()
        vehiculo = Vehiculo.objects.filter(patente='AE-123-CD').first()
        if cliente and vehiculo and not Pedido.objects.exists():
            servicio = Servicio.objects.get(Tipo_servicio='Mudanza local')
            pedido = Pedido.objects.create(
                patente_vehiculo=vehiculo, idUsuario=cliente, Fecha_pedido=date(2026, 9, 15),
                fecha_servicio=date(2026, 9, 20), origen='Av. Belgrano 1250, Salta',
                destino='Los Ceibos 340, Cerrillos', estado=Pedido.FINALIZADO,
                total=servicio.Precio_base)
            DetallePedido.objects.create(idPedido=pedido, idServicio=servicio,
                                         precio_unitario=servicio.Precio_base,
                                         subtotal=servicio.Precio_base)
            InventarioDetalle.objects.create(idPedido=pedido, Descripcion='Cajas de libros',
                                             Peso=Decimal('7.63'), Cantidad=42, Fragil=True)
            cobranza = Cobranza.objects.create(Monto_cob=185000, Met_pag_cob='Transferencia')
            DetalleCobranza.objects.create(idPedido=pedido, idCobranza=cobranza)
            self.stdout.write(self.style.SUCCESS(
                'Pedido de ejemplo creado con detalle, inventario y cobranza.'))
```

y agregar `from decimal import Decimal` debajo de `from datetime import date`.

- [ ] **Paso 7: Aplicar y correr todas las pruebas**

Correr: `docker exec mudanzas_web python manage.py migrate && docker exec mudanzas_web python manage.py init_data && docker exec mudanzas_web python manage.py test`
Esperado: `Applying usuarios.0002_hito3_pedidos... OK`, `Applying usuarios.0003_completar_pedidos_existentes... OK`, el usuario `gomezm` creado y `OK` en todas las pruebas (52).

Además: `docker exec mudanzas_web python manage.py makemigrations --check --dry-run` → `No changes detected`.

- [ ] **Paso 8: Commit**

```bash
git add usuarios/
git commit -m "Add Hito 3 order fields, Cliente role and order permissions to the DER"
```

---

### Tarea 2: Registrar un pedido (reglas del negocio)

**Archivos:**
- Crear: `pedidos/__init__.py` (vacío), `pedidos/apps.py`, `pedidos/urls.py`, `pedidos/reglas.py`, `pedidos/test_reglas.py`
- Modificar: `core/settings.py` (INSTALLED_APPS), `core/urls.py`

**Interfaces:**
- Consume: los modelos de la Tarea 1.
- Produce:
  - `reglas.ErrorPedido(errores)`: `.errores` es un `dict[str, str]`; la clave `'__all__'` indica un error general.
  - `reglas.vehiculos_libres(fecha: date) -> QuerySet[Vehiculo]`
  - `reglas.registrar_pedido(cliente: Usuario, fecha_servicio: date, origen: str, destino: str, ids_servicios: list[int], patente: str, items: list[dict]) -> Pedido`. Cada item tiene `descripcion` (str), `cantidad` (int), `peso` (Decimal) y `fragil` (bool). Las claves de error posibles son `fecha_servicio`, `origen`, `destino`, `servicios`, `inventario` y `vehiculo`.

- [ ] **Paso 1: Crear el esqueleto de la app**

`pedidos/apps.py`:

```python
from django.apps import AppConfig


class PedidosConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'pedidos'
    verbose_name = 'Pedidos (Hito 3)'
```

`pedidos/urls.py`:

```python
from django.urls import path

from . import views

urlpatterns = []
```

`pedidos/views.py`:

```python
"""Pantallas del pedido de mudanza (Hito 3). Las reglas viven en reglas.py."""
```

En `core/settings.py`, agregar `'pedidos',` al final de `INSTALLED_APPS`. En `core/urls.py`, antes de `path('', include('usuarios.urls')),`:

```python
    path('', include('pedidos.urls')),       # Hito 3: pedidos, registro de clientes y servicios
```

- [ ] **Paso 2: Escribir las pruebas que fallan**

`pedidos/test_reglas.py`:

```python
"""Pruebas de las reglas del pedido. Usan los datos de init_data:
Mudanza local $185.000, Flete urbano $75.000; AD-321-JK (1600 kg) y AE-123-CD
(5000 kg) disponibles; AC-789-GH en mantenimiento; AF-456-EF en viaje."""
import io
from datetime import timedelta
from decimal import Decimal
from unittest import mock

from django.core.management import call_command
from django.db import IntegrityError
from django.test import TestCase
from django.utils import timezone

from pedidos import reglas
from usuarios.models import DetallePedido, Pedido, Servicio, Usuario

CLIENTE, ADMIN = 29876543, 35123456


class BaseReglas(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command('init_data', stdout=io.StringIO())
        cls.cliente = Usuario.objects.get(DNI=CLIENTE)
        cls.admin = Usuario.objects.get(DNI=ADMIN)
        cls.local = Servicio.objects.get(Tipo_servicio='Mudanza local')
        cls.flete = Servicio.objects.get(Tipo_servicio='Flete urbano')

    def dia(self, dias=1):
        return timezone.localdate() + timedelta(days=dias)

    def registrar(self, **cambios):
        datos = dict(
            cliente=self.cliente, fecha_servicio=self.dia(), origen='Av. Belgrano 100, Salta',
            destino='Mitre 50, Cerrillos', ids_servicios=[self.local.id_servicio, self.flete.id_servicio],
            patente='AD-321-JK',
            items=[{'descripcion': 'Heladera', 'cantidad': 1, 'peso': Decimal('80'), 'fragil': True},
                   {'descripcion': 'Cajas', 'cantidad': 10, 'peso': Decimal('12.5'), 'fragil': False}])
        datos.update(cambios)
        return reglas.registrar_pedido(**datos)

    def assertRechaza(self, campo, **cambios):
        antes = Pedido.objects.count()
        with self.assertRaises(reglas.ErrorPedido) as ctx:
            self.registrar(**cambios)
        self.assertIn(campo, ctx.exception.errores)
        self.assertEqual(Pedido.objects.count(), antes)


class RegistrarPedidoTest(BaseReglas):
    def test_registra_el_pedido_completo(self):
        p = self.registrar()
        self.assertEqual(p.estado, Pedido.PENDIENTE)
        self.assertEqual(p.Fecha_pedido, timezone.localdate())
        self.assertEqual(p.idUsuario, self.cliente)
        self.assertEqual(p.total, Decimal('260000'))
        self.assertEqual(
            sorted((d.idServicio.Tipo_servicio, d.precio_unitario, d.subtotal) for d in p.detalles.all()),
            [('Flete urbano', 75000, 75000), ('Mudanza local', 185000, 185000)])
        self.assertEqual(sorted(i.Descripcion for i in p.inventario.all()), ['Cajas', 'Heladera'])
        self.assertEqual(p.peso_total, Decimal('205'))

    def test_el_precio_queda_fijo_en_el_pedido(self):
        p = self.registrar()
        Servicio.objects.filter(pk=self.local.pk).update(Precio_base=999999)
        self.assertEqual(p.detalles.get(idServicio=self.local).precio_unitario, 185000)

    def test_fecha_pasada(self):
        self.assertRechaza('fecha_servicio', fecha_servicio=self.dia(-1))

    def test_fecha_a_mas_de_un_anio(self):
        self.assertRechaza('fecha_servicio', fecha_servicio=self.dia(366))

    def test_se_puede_para_hoy(self):
        self.assertEqual(self.registrar(fecha_servicio=self.dia(0)).estado, Pedido.PENDIENTE)

    def test_origen_vacio(self):
        self.assertRechaza('origen', origen='   ')

    def test_destino_igual_al_origen(self):
        self.assertRechaza('destino', destino='AV. BELGRANO 100, SALTA')

    def test_sin_servicios(self):
        self.assertRechaza('servicios', ids_servicios=[])

    def test_servicio_inactivo(self):
        Servicio.objects.filter(pk=self.flete.pk).update(Activo=False)
        self.assertRechaza('servicios')

    def test_sin_objetos(self):
        self.assertRechaza('inventario', items=[])

    def test_objeto_sin_descripcion(self):
        self.assertRechaza('inventario', items=[{'descripcion': '', 'cantidad': 1, 'peso': 5}])

    def test_cantidad_fuera_de_rango(self):
        self.assertRechaza('inventario', items=[{'descripcion': 'Sillas', 'cantidad': 0, 'peso': 5}])
        self.assertRechaza('inventario', items=[{'descripcion': 'Sillas', 'cantidad': 1000, 'peso': 1}])

    def test_peso_fuera_de_rango(self):
        self.assertRechaza('inventario', items=[{'descripcion': 'Sillas', 'cantidad': 1, 'peso': 0}])
        self.assertRechaza('inventario', items=[{'descripcion': 'Piano', 'cantidad': 1, 'peso': 5001}])

    def test_sin_vehiculo(self):
        self.assertRechaza('vehiculo', patente='')

    def test_vehiculo_en_mantenimiento(self):
        self.assertRechaza('vehiculo', patente='AC-789-GH')

    def test_carga_supera_la_capacidad(self):
        self.assertRechaza('vehiculo', items=[{'descripcion': 'Máquinas', 'cantidad': 2, 'peso': 850}])

    def test_vehiculo_ocupado_ese_dia(self):
        self.registrar()
        self.assertRechaza('vehiculo')
        self.assertEqual(self.registrar(fecha_servicio=self.dia(2)).estado, Pedido.PENDIENTE)

    def test_si_falla_a_mitad_de_camino_no_queda_nada(self):
        pedidos, detalles = Pedido.objects.count(), DetallePedido.objects.count()
        with mock.patch('pedidos.reglas.InventarioDetalle.objects.bulk_create',
                        side_effect=IntegrityError('falla simulada')):
            with self.assertRaises(IntegrityError):
                self.registrar()
        self.assertEqual(Pedido.objects.count(), pedidos)
        self.assertEqual(DetallePedido.objects.count(), detalles)


class VehiculosLibresTest(BaseReglas):
    def patentes(self, fecha):
        return set(reglas.vehiculos_libres(fecha).values_list('patente', flat=True))

    def test_solo_los_disponibles(self):
        self.assertEqual(self.patentes(self.dia()), {'AD-321-JK', 'AE-123-CD'})

    def test_un_pedido_activo_ocupa_el_vehiculo_ese_dia(self):
        self.registrar()
        self.assertEqual(self.patentes(self.dia()), {'AE-123-CD'})
        self.assertEqual(self.patentes(self.dia(2)), {'AD-321-JK', 'AE-123-CD'})

    def test_un_pedido_anulado_no_ocupa(self):
        p = self.registrar()
        Pedido.objects.filter(pk=p.pk).update(estado=Pedido.ANULADO)
        self.assertIn('AD-321-JK', self.patentes(self.dia()))
```

- [ ] **Paso 3: Correr las pruebas y verificar que fallan**

Correr: `docker exec mudanzas_web python manage.py test pedidos.test_reglas`
Esperado: `ImportError: cannot import name 'reglas' from 'pedidos'`.

- [ ] **Paso 4: Implementar `pedidos/reglas.py`**

```python
"""Reglas del pedido de mudanza (Hito 3).

Las vistas solo arman los datos y muestran el resultado: todo lo que decide si un
pedido es válido, cuánto cuesta y a qué estado pasa vive acá. Cada operación que
escribe corre en una transacción: o se guarda todo, o no se guarda nada.
"""
from datetime import timedelta
from decimal import Decimal, InvalidOperation

from django.db import transaction
from django.utils import timezone

from usuarios.models import DetallePedido, InventarioDetalle, Pedido, Servicio, Vehiculo

MAX_DIAS_ADELANTO = 365
MAX_CANTIDAD = 999
MAX_PESO_UNITARIO = Decimal('5000')
MAX_DIRECCION = 200


class ErrorPedido(Exception):
    """Errores de validación como {campo: mensaje}; '__all__' es un error general."""

    def __init__(self, errores):
        if isinstance(errores, str):
            errores = {'__all__': errores}
        self.errores = errores
        super().__init__(' '.join(errores.values()))


def vehiculos_libres(fecha):
    """Vehículos en estado Disponible que no tienen otro pedido activo ese día."""
    ocupados = Pedido.objects.filter(fecha_servicio=fecha, estado__in=Pedido.ACTIVOS) \
                             .values('patente_vehiculo')
    return Vehiculo.objects.filter(estado='Disponible').exclude(patente__in=ocupados).order_by('patente')


def _validar_fecha(fecha, errores):
    hoy = timezone.localdate()
    if not fecha:
        errores['fecha_servicio'] = 'Elegí la fecha de la mudanza.'
    elif fecha < hoy:
        errores['fecha_servicio'] = 'La fecha de la mudanza tiene que ser de hoy en adelante.'
    elif fecha > hoy + timedelta(days=MAX_DIAS_ADELANTO):
        errores['fecha_servicio'] = 'Se puede reservar con un año de anticipación como máximo.'


def _validar_direcciones(origen, destino, errores):
    for campo, valor, nombre in (('origen', origen, 'origen'), ('destino', destino, 'destino')):
        if not valor:
            errores[campo] = f'Escribí la dirección de {nombre}.'
        elif len(valor) > MAX_DIRECCION:
            errores[campo] = f'La dirección de {nombre} puede tener hasta {MAX_DIRECCION} caracteres.'
    if origen and destino and origen.lower() == destino.lower():
        errores['destino'] = 'El destino tiene que ser distinto del origen.'


def _validar_servicios(ids_servicios, errores):
    ids = {int(i) for i in ids_servicios or []}
    servicios = list(Servicio.objects.filter(id_servicio__in=ids, Activo=True))
    if not ids:
        errores['servicios'] = 'Elegí al menos un servicio.'
    elif len(servicios) != len(ids):
        errores['servicios'] = 'Uno de los servicios elegidos ya no está disponible.'
    return servicios


def _validar_items(items, errores):
    if not items:
        errores['inventario'] = 'Agregá al menos un objeto.'
        return []
    limpios = []
    for n, item in enumerate(items, start=1):
        descripcion = (item.get('descripcion') or '').strip()
        try:
            cantidad = int(item.get('cantidad'))
            peso = Decimal(str(item.get('peso')))
        except (TypeError, ValueError, InvalidOperation):
            errores['inventario'] = f'Objeto {n}: la cantidad y el peso tienen que ser números.'
            continue
        if not descripcion:
            errores['inventario'] = f'Objeto {n}: escribí qué es.'
        elif not 1 <= cantidad <= MAX_CANTIDAD:
            errores['inventario'] = f'Objeto {n}: la cantidad va de 1 a {MAX_CANTIDAD}.'
        elif not Decimal('0') < peso <= MAX_PESO_UNITARIO:
            errores['inventario'] = f'Objeto {n}: el peso tiene que ser mayor a 0 y de hasta {MAX_PESO_UNITARIO} kg.'
        else:
            limpios.append({'descripcion': descripcion[:100], 'cantidad': cantidad,
                            'peso': peso, 'fragil': bool(item.get('fragil'))})
    return limpios


def registrar_pedido(cliente, fecha_servicio, origen, destino, ids_servicios, patente, items):
    """Registra el pedido completo (cabecera, servicios e inventario) en una sola
    transacción y lo deja Pendiente. Si algo no es válido lanza ErrorPedido."""
    errores = {}
    origen, destino = (origen or '').strip(), (destino or '').strip()
    _validar_fecha(fecha_servicio, errores)
    _validar_direcciones(origen, destino, errores)
    servicios = _validar_servicios(ids_servicios, errores)
    limpios = _validar_items(items, errores)
    if not patente:
        errores['vehiculo'] = 'Elegí un vehículo.'
    if errores:
        raise ErrorPedido(errores)

    with transaction.atomic():
        # Bloquea el vehículo: si dos clientes lo eligen para el mismo día, el segundo espera
        # a que el primero termine y después lo encuentra ocupado.
        vehiculo = Vehiculo.objects.select_for_update().filter(patente=patente).first()
        if not vehiculo or not vehiculos_libres(fecha_servicio).filter(patente=patente).exists():
            raise ErrorPedido({'vehiculo': 'Ese vehículo no está libre para esa fecha. Elegí otro.'})
        peso_total = sum(i['cantidad'] * i['peso'] for i in limpios)
        if peso_total > vehiculo.capacidad_kg:
            raise ErrorPedido({'vehiculo': f'La carga ({peso_total} kg) supera la capacidad '
                                           f'del vehículo ({vehiculo.capacidad_kg} kg).'})

        pedido = Pedido.objects.create(
            patente_vehiculo=vehiculo, idUsuario=cliente, Fecha_pedido=timezone.localdate(),
            fecha_servicio=fecha_servicio, origen=origen, destino=destino,
            estado=Pedido.PENDIENTE, total=sum(s.Precio_base for s in servicios))
        DetallePedido.objects.bulk_create([
            DetallePedido(idPedido=pedido, idServicio=s, precio_unitario=s.Precio_base, subtotal=s.Precio_base)
            for s in servicios])
        InventarioDetalle.objects.bulk_create([
            InventarioDetalle(idPedido=pedido, Descripcion=i['descripcion'], Cantidad=i['cantidad'],
                              Peso=i['peso'], Fragil=i['fragil'])
            for i in limpios])
    return pedido
```

- [ ] **Paso 5: Correr las pruebas y verificar que pasan**

Correr: `docker exec mudanzas_web python manage.py test pedidos.test_reglas`
Esperado: `OK` (21 pruebas). Después correr `docker exec mudanzas_web python manage.py test` y verificar que todo sigue en `OK`.

- [ ] **Paso 6: Commit**

```bash
git add pedidos/ core/settings.py core/urls.py
git commit -m "Add the order registration rules with availability, capacity and transaction"
```

---

### Tarea 3: Confirmar, finalizar, anular y filtrar (reglas)

**Archivos:**
- Modificar: `pedidos/reglas.py`, `pedidos/test_reglas.py`

**Interfaces:**
- Consume: `ErrorPedido` y `registrar_pedido` (Tarea 2).
- Produce:
  - `reglas.confirmar(id_pedido: int) -> Pedido`, `reglas.finalizar(id_pedido: int) -> Pedido` y `reglas.anular(id_pedido: int, usuario: Usuario, motivo: str) -> Pedido`. Las tres lanzan `ErrorPedido`; en la anulación, un motivo inválido da la clave `'motivo'`.
  - `reglas.filtrar_pedidos(pedidos: QuerySet, desde=None, hasta=None, estado=None, id_servicio=None, id_cliente=None) -> QuerySet`, ordenado del más nuevo al más viejo.

- [ ] **Paso 1: Escribir las pruebas que fallan**

Agregar al final de `pedidos/test_reglas.py`:

```python
class TransicionesTest(BaseReglas):
    def test_confirmar_y_finalizar(self):
        p = self.registrar()
        self.assertEqual(reglas.confirmar(p.pk).estado, Pedido.CONFIRMADO)
        self.assertEqual(reglas.finalizar(p.pk).estado, Pedido.FINALIZADO)
        self.assertEqual(Pedido.objects.get(pk=p.pk).estado, Pedido.FINALIZADO)

    def test_no_se_finaliza_un_pendiente(self):
        p = self.registrar()
        with self.assertRaises(reglas.ErrorPedido):
            reglas.finalizar(p.pk)
        self.assertEqual(Pedido.objects.get(pk=p.pk).estado, Pedido.PENDIENTE)

    def test_no_se_confirma_dos_veces(self):
        p = self.registrar()
        reglas.confirmar(p.pk)
        with self.assertRaises(reglas.ErrorPedido):
            reglas.confirmar(p.pk)

    def test_anular_guarda_fecha_motivo_y_usuario_y_libera_el_vehiculo(self):
        p = self.registrar()
        reglas.confirmar(p.pk)
        reglas.anular(p.pk, self.admin, '  El cliente suspendió la mudanza  ')
        p.refresh_from_db()
        self.assertEqual(p.estado, Pedido.ANULADO)
        self.assertEqual(p.motivo_anulacion, 'El cliente suspendió la mudanza')
        self.assertEqual(p.usuario_anulacion, self.admin)
        self.assertIsNotNone(p.fecha_anulacion)
        self.assertIn('AD-321-JK', reglas.vehiculos_libres(p.fecha_servicio).values_list('patente', flat=True))
        self.assertTrue(Pedido.objects.filter(pk=p.pk).exists())  # no se borra

    def test_motivo_invalido(self):
        p = self.registrar()
        for motivo in ['', 'nop', 'x' * 201]:
            with self.assertRaises(reglas.ErrorPedido) as ctx:
                reglas.anular(p.pk, self.admin, motivo)
            self.assertIn('motivo', ctx.exception.errores)
        self.assertEqual(Pedido.objects.get(pk=p.pk).estado, Pedido.PENDIENTE)

    def test_no_se_anula_un_finalizado_ni_un_anulado(self):
        finalizado = Pedido.objects.get(estado=Pedido.FINALIZADO)  # el de init_data
        with self.assertRaises(reglas.ErrorPedido):
            reglas.anular(finalizado.pk, self.admin, 'Motivo de prueba')
        p = self.registrar()
        reglas.anular(p.pk, self.admin, 'Motivo de prueba')
        with self.assertRaises(reglas.ErrorPedido):
            reglas.anular(p.pk, self.admin, 'Otra vez')


class FiltrarPedidosTest(BaseReglas):
    def setUp(self):
        self.p1 = self.registrar(fecha_servicio=self.dia(1), ids_servicios=[self.local.id_servicio])
        self.p2 = self.registrar(fecha_servicio=self.dia(5), ids_servicios=[self.flete.id_servicio])
        reglas.confirmar(self.p2.pk)
        self.viejo = Pedido.objects.get(estado=Pedido.FINALIZADO)  # 20/09/2026, Mudanza local

    def ids(self, **filtros):
        return [p.pk for p in reglas.filtrar_pedidos(Pedido.objects.all(), **filtros)]

    def test_sin_filtros_del_mas_nuevo_al_mas_viejo(self):
        self.assertEqual(self.ids(), [self.p2.pk, self.p1.pk, self.viejo.pk])

    def test_por_rango_de_fechas_del_servicio(self):
        self.assertEqual(self.ids(desde=self.dia(2)), [self.p2.pk])
        self.assertEqual(self.ids(hasta=self.dia(2)), [self.p1.pk, self.viejo.pk])
        self.assertEqual(self.ids(desde=self.dia(0), hasta=self.dia(2)), [self.p1.pk])

    def test_por_estado(self):
        self.assertEqual(self.ids(estado=Pedido.CONFIRMADO), [self.p2.pk])

    def test_por_servicio(self):
        self.assertEqual(self.ids(id_servicio=self.local.id_servicio), [self.p1.pk, self.viejo.pk])

    def test_por_cliente(self):
        self.assertEqual(self.ids(id_cliente=self.admin.id_usuario), [])
        self.assertEqual(len(self.ids(id_cliente=self.cliente.id_usuario)), 3)

    def test_filtros_combinados(self):
        self.assertEqual(self.ids(estado=Pedido.PENDIENTE, id_servicio=self.local.id_servicio), [self.p1.pk])
```

- [ ] **Paso 2: Correr las pruebas y verificar que fallan**

Correr: `docker exec mudanzas_web python manage.py test pedidos.test_reglas`
Esperado: `AttributeError: module 'pedidos.reglas' has no attribute 'confirmar'` (y lo mismo para `filtrar_pedidos`).

- [ ] **Paso 3: Implementar las transiciones y el filtro**

Agregar al final de `pedidos/reglas.py`:

```python
# acción: (estados desde los que se puede, estado al que pasa)
TRANSICIONES = {
    'confirmar': ((Pedido.PENDIENTE,), Pedido.CONFIRMADO),
    'finalizar': ((Pedido.CONFIRMADO,), Pedido.FINALIZADO),
    'anular': (Pedido.ACTIVOS, Pedido.ANULADO),
}


def _pasar_a(id_pedido, accion):
    """Bloquea el pedido y le cambia el estado en memoria; el que llama guarda."""
    desde, hacia = TRANSICIONES[accion]
    pedido = Pedido.objects.select_for_update().get(pk=id_pedido)
    if pedido.estado not in desde:
        raise ErrorPedido(f'No se puede {accion} un pedido en estado {pedido.estado}.')
    pedido.estado = hacia
    return pedido


def confirmar(id_pedido):
    with transaction.atomic():
        pedido = _pasar_a(id_pedido, 'confirmar')
        pedido.save(update_fields=['estado'])
    return pedido


def finalizar(id_pedido):
    with transaction.atomic():
        pedido = _pasar_a(id_pedido, 'finalizar')
        pedido.save(update_fields=['estado'])
    return pedido


def anular(id_pedido, usuario, motivo):
    """Anula sin borrar: guarda fecha, motivo y usuario. Como un pedido anulado ya no
    cuenta como activo, el vehículo vuelve a estar libre ese día."""
    motivo = (motivo or '').strip()
    if not 5 <= len(motivo) <= 200:
        raise ErrorPedido({'motivo': 'El motivo tiene que tener entre 5 y 200 caracteres.'})
    with transaction.atomic():
        pedido = _pasar_a(id_pedido, 'anular')
        pedido.fecha_anulacion = timezone.now()
        pedido.motivo_anulacion = motivo
        pedido.usuario_anulacion = usuario
        pedido.save(update_fields=['estado', 'fecha_anulacion', 'motivo_anulacion', 'usuario_anulacion'])
    return pedido


def filtrar_pedidos(pedidos, desde=None, hasta=None, estado=None, id_servicio=None, id_cliente=None):
    """Filtros de la consulta. Las fechas son de la mudanza (fecha_servicio)."""
    if desde:
        pedidos = pedidos.filter(fecha_servicio__gte=desde)
    if hasta:
        pedidos = pedidos.filter(fecha_servicio__lte=hasta)
    if estado:
        pedidos = pedidos.filter(estado=estado)
    if id_servicio:
        pedidos = pedidos.filter(detalles__idServicio_id=id_servicio)
    if id_cliente:
        pedidos = pedidos.filter(idUsuario_id=id_cliente)
    return (pedidos.distinct()
            .select_related('idUsuario', 'patente_vehiculo')
            .prefetch_related('detalles__idServicio')
            .order_by('-id_pedido'))
```

- [ ] **Paso 4: Correr las pruebas y verificar que pasan**

Correr: `docker exec mudanzas_web python manage.py test pedidos.test_reglas`
Esperado: `OK` (33 pruebas).

- [ ] **Paso 5: Commit**

```bash
git add pedidos/
git commit -m "Add order state transitions, cancellation and query filters"
```

---

### Tarea 4: Permisos, consulta y detalle

**Archivos:**
- Crear: `pedidos/permisos.py`, `pedidos/forms.py`, `pedidos/templates/pedidos/lista.html`, `pedidos/templates/pedidos/detalle.html`, `pedidos/test_vistas.py`
- Modificar: `pedidos/views.py`, `pedidos/urls.py`, `usuarios/views.py`, `vehiculos/templates/vehiculos/base.html`

**Interfaces:**
- Consume: `reglas.filtrar_pedidos`, `reglas.registrar_pedido` (en las pruebas).
- Produce:
  - `permisos.tiene_permiso(usuario: Usuario, nombre: str) -> bool`
  - `permisos.requiere_permiso(nombre: str)`: decorador que deja `request.usuario`.
  - `views._pedido_visible(request, id_pedido) -> Pedido`: da 404 si el pedido es de otro cliente.
  - Nombres de URL: `pedidos_lista` (`/pedidos/`) y `pedidos_detalle` (`/pedidos/<int:id_pedido>/`).
  - `usuarios.views.redirigir_segun_rol(usuario) -> HttpResponseRedirect`
  - `forms.FiltroPedidosForm(data, ve_todos: bool)` con `.filtros() -> dict` para `filtrar_pedidos`.

- [ ] **Paso 1: Escribir las pruebas que fallan**

`pedidos/test_vistas.py`:

```python
"""Pruebas de las pantallas del pedido: permisos, consulta y detalle."""
import io
from datetime import timedelta
from decimal import Decimal

from django.core.management import call_command
from django.test import TestCase
from django.utils import timezone

from pedidos import reglas
from pedidos.permisos import tiene_permiso
from usuarios.models import Pedido, Rol, Servicio, Usuario
from usuarios.utils import hash_password

ADMIN, CHOFER, CLIENTE = 35123456, 40987654, 29876543


class BaseVistas(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command('init_data', stdout=io.StringIO())
        cls.cliente = Usuario.objects.get(DNI=CLIENTE)
        cls.otro = Usuario.objects.create(
            DNI=31555666, Nombre='Jorge', Apellido='Herrera', Correo='jorge.herrera@ejemplo.com',
            NombreUsuario='herreraj', Clave=hash_password('Cliente123!'), DebeCambiarClave=False,
            idRol=Rol.objects.get(nom_rol='Cliente'))
        cls.local = Servicio.objects.get(Tipo_servicio='Mudanza local')

    def entrar(self, dni):
        s = self.client.session
        s['usuario_dni'] = dni
        s['usuario_rol'] = Usuario.objects.get(DNI=dni).idRol.nom_rol
        s.save()

    def pedido_de(self, cliente, dias=1, patente='AD-321-JK'):
        return reglas.registrar_pedido(
            cliente, timezone.localdate() + timedelta(days=dias), 'Origen 1', 'Destino 2',
            [self.local.id_servicio], patente,
            [{'descripcion': 'Cajas', 'cantidad': 2, 'peso': Decimal('10'), 'fragil': False}])


class PermisosTest(BaseVistas):
    def test_tiene_permiso_segun_la_tabla(self):
        admin, chofer = Usuario.objects.get(DNI=ADMIN), Usuario.objects.get(DNI=CHOFER)
        self.assertTrue(tiene_permiso(self.cliente, 'PED_REGISTRAR'))
        self.assertFalse(tiene_permiso(self.cliente, 'PED_ANULAR'))
        self.assertTrue(tiene_permiso(admin, 'PED_ANULAR'))
        self.assertFalse(tiene_permiso(admin, 'PED_REGISTRAR'))
        self.assertFalse(tiene_permiso(chofer, 'PED_CONSULTAR'))

    def test_sin_sesion_va_al_login(self):
        self.assertRedirects(self.client.get('/pedidos/'), '/login/')

    def test_chofer_no_entra(self):
        self.entrar(CHOFER)
        self.assertEqual(self.client.get('/pedidos/').status_code, 403)

    def test_login_del_cliente_va_a_sus_pedidos(self):
        r = self.client.post('/login/', {'usuario': 'gomezm', 'clave': 'Cliente123!'})
        self.assertRedirects(r, '/pedidos/')

    def test_el_portal_manda_al_cliente_a_sus_pedidos(self):
        self.entrar(CLIENTE)
        self.assertRedirects(self.client.get('/portal/'), '/pedidos/')


class ConsultaTest(BaseVistas):
    def setUp(self):
        self.mio = self.pedido_de(self.cliente)
        self.ajeno = self.pedido_de(self.otro, dias=2)

    def test_el_cliente_ve_solo_los_suyos(self):
        self.entrar(CLIENTE)
        r = self.client.get('/pedidos/')
        ids = [p.pk for p in r.context['pedidos']]
        self.assertIn(self.mio.pk, ids)
        self.assertNotIn(self.ajeno.pk, ids)
        self.assertNotIn('cliente', r.context['form'].fields)

    def test_el_admin_ve_todos_y_filtra_por_cliente(self):
        self.entrar(ADMIN)
        r = self.client.get('/pedidos/')
        self.assertEqual(len(r.context['pedidos']), 3)
        r = self.client.get('/pedidos/', {'cliente': self.otro.id_usuario})
        self.assertEqual([p.pk for p in r.context['pedidos']], [self.ajeno.pk])

    def test_filtros_por_fecha_estado_y_servicio(self):
        self.entrar(ADMIN)
        hoy = timezone.localdate()
        r = self.client.get('/pedidos/', {'desde': (hoy + timedelta(days=2)).isoformat(),
                                          'estado': 'Pendiente', 'servicio': self.local.id_servicio})
        self.assertEqual([p.pk for p in r.context['pedidos']], [self.ajeno.pk])

    def test_detalle_propio(self):
        self.entrar(CLIENTE)
        r = self.client.get(f'/pedidos/{self.mio.pk}/')
        self.assertContains(r, 'Origen 1')
        self.assertContains(r, 'Pendiente')

    def test_detalle_ajeno_da_404(self):
        self.entrar(CLIENTE)
        self.assertEqual(self.client.get(f'/pedidos/{self.ajeno.pk}/').status_code, 404)

    def test_el_admin_ve_cualquier_detalle(self):
        self.entrar(ADMIN)
        self.assertEqual(self.client.get(f'/pedidos/{self.ajeno.pk}/').status_code, 200)
```

- [ ] **Paso 2: Correr las pruebas y verificar que fallan**

Correr: `docker exec mudanzas_web python manage.py test pedidos.test_vistas`
Esperado: `ModuleNotFoundError: No module named 'pedidos.permisos'`.

- [ ] **Paso 3: Implementar los permisos**

`pedidos/permisos.py`:

```python
"""Permisos del Hito 3: se consultan en PERMISOS_ROLES, no por el nombre del rol."""
from functools import wraps

from django.http import HttpResponseForbidden
from django.shortcuts import redirect

from usuarios.models import PermisoRol
from usuarios.views import get_usuario_actual


def tiene_permiso(usuario, nombre):
    return PermisoRol.objects.filter(idRol_id=usuario.idRol_id, idPermiso__nom_permiso=nombre).exists()


def requiere_permiso(nombre):
    """Sin sesión manda al login; sin el permiso responde 403.
    Deja el usuario en request.usuario para que la vista no lo vuelva a buscar."""
    def decorador(vista):
        @wraps(vista)
        def envoltura(request, *args, **kwargs):
            usuario = get_usuario_actual(request)
            if not usuario:
                return redirect('login')
            if not tiene_permiso(usuario, nombre):
                return HttpResponseForbidden('No tenés permiso para esta operación.')
            request.usuario = usuario
            return vista(request, *args, **kwargs)
        return envoltura
    return decorador
```

- [ ] **Paso 4: Redirigir al cliente según su rol**

En `usuarios/views.py`, agregar después de `solo_admin`:

```python
def redirigir_segun_rol(usuario):
    """A dónde va cada uno después de iniciar sesión."""
    rol = usuario.idRol.nom_rol.lower()
    if rol == 'administrador':
        return redirect('admin_dashboard')
    if rol == 'cliente':
        return redirect('pedidos_lista')
    return redirect('usuario_portal')
```

En `login_view` y en `cambiar_clave_obligatoria`, reemplazar el bloque

```python
    if usuario.idRol.nom_rol.lower() == 'administrador':
        return redirect('admin_dashboard')
    else:
        return redirect('usuario_portal')
```

por `return redirigir_segun_rol(usuario)`. Respetar la sangría: en `login_view` el bloque está dentro del `if request.method == 'POST':`.

En `usuario_portal`, después del `if not usuario_actual: return redirect('login')`:

```python
    if usuario_actual.idRol.nom_rol.lower() == 'cliente':
        return redirect('pedidos_lista')
```

- [ ] **Paso 5: Formulario de filtros**

`pedidos/forms.py`:

```python
from django import forms

from usuarios.models import Pedido, Servicio, Usuario


def con_bootstrap(form):
    """Las mismas clases que usa el CRUD de vehículos."""
    for field in form.fields.values():
        w = field.widget
        if isinstance(w, (forms.CheckboxInput, forms.CheckboxSelectMultiple)):
            continue
        w.attrs.setdefault('class', 'form-select' if isinstance(w, forms.Select) else 'form-control')


class FiltroPedidosForm(forms.Form):
    desde = forms.DateField(required=False, label='Desde',
                            widget=forms.DateInput(attrs={'type': 'date'}, format='%Y-%m-%d'))
    hasta = forms.DateField(required=False, label='Hasta',
                            widget=forms.DateInput(attrs={'type': 'date'}, format='%Y-%m-%d'))
    estado = forms.ChoiceField(required=False, label='Estado',
                               choices=[('', 'Todos')] + Pedido.ESTADOS)
    servicio = forms.ModelChoiceField(required=False, label='Servicio', empty_label='Todos',
                                      queryset=Servicio.objects.order_by('Tipo_servicio'))
    cliente = forms.ModelChoiceField(required=False, label='Cliente', empty_label='Todos',
                                     queryset=Usuario.objects.filter(idRol__nom_rol='Cliente')
                                                             .order_by('Apellido', 'Nombre'))

    def __init__(self, *args, ve_todos=False, **kwargs):
        super().__init__(*args, **kwargs)
        if not ve_todos:
            del self.fields['cliente']
        con_bootstrap(self)

    def filtros(self):
        d = self.cleaned_data
        return {'desde': d.get('desde'), 'hasta': d.get('hasta'), 'estado': d.get('estado') or None,
                'id_servicio': d['servicio'].id_servicio if d.get('servicio') else None,
                'id_cliente': d['cliente'].id_usuario if d.get('cliente') else None}
```

- [ ] **Paso 6: Vistas de consulta y detalle**

Reemplazar `pedidos/views.py` por:

```python
"""Pantallas del pedido de mudanza (Hito 3). Las reglas viven en reglas.py."""
from django.http import Http404
from django.shortcuts import get_object_or_404, render

from usuarios.models import Pedido
from . import reglas
from .forms import FiltroPedidosForm
from .permisos import requiere_permiso, tiene_permiso


def _ve_todos(usuario):
    """Quien gestiona pedidos ve todos; el cliente, solo los suyos."""
    return tiene_permiso(usuario, 'PED_GESTIONAR')


def _pedido_visible(request, id_pedido):
    """El pedido, si el usuario puede verlo. Un pedido ajeno da 404 y no 403,
    para no revelar que existe."""
    pedido = get_object_or_404(
        Pedido.objects.select_related('idUsuario', 'patente_vehiculo', 'usuario_anulacion')
                      .prefetch_related('detalles__idServicio', 'inventario'),
        pk=id_pedido)
    if not _ve_todos(request.usuario) and pedido.idUsuario_id != request.usuario.id_usuario:
        raise Http404('Pedido inexistente')
    return pedido


@requiere_permiso('PED_CONSULTAR')
def lista(request):
    ve_todos = _ve_todos(request.usuario)
    base = Pedido.objects.all() if ve_todos else Pedido.objects.filter(idUsuario=request.usuario)
    form = FiltroPedidosForm(request.GET or None, ve_todos=ve_todos)
    filtros = form.filtros() if form.is_valid() else {}
    return render(request, 'pedidos/lista.html', {
        'form': form, 've_todos': ve_todos,
        'pedidos': reglas.filtrar_pedidos(base, **filtros),
        'puede_registrar': tiene_permiso(request.usuario, 'PED_REGISTRAR'),
    })


@requiere_permiso('PED_CONSULTAR')
def detalle(request, id_pedido):
    pedido = _pedido_visible(request, id_pedido)
    return render(request, 'pedidos/detalle.html', {
        'pedido': pedido,
        'puede_gestionar': tiene_permiso(request.usuario, 'PED_GESTIONAR'),
        'puede_anular': tiene_permiso(request.usuario, 'PED_ANULAR'),
        'puede_comprobante': tiene_permiso(request.usuario, 'PED_COMPROBANTE'),
    })
```

`pedidos/urls.py`:

```python
from django.urls import path

from . import views

urlpatterns = [
    path('pedidos/', views.lista, name='pedidos_lista'),
    path('pedidos/<int:id_pedido>/', views.detalle, name='pedidos_detalle'),
]
```

- [ ] **Paso 7: Plantillas**

`pedidos/templates/pedidos/lista.html`:

```html
{% extends 'vehiculos/base.html' %}
{% block title %}Pedidos{% endblock %}
{% block content %}
<div class="d-flex justify-content-between align-items-center mb-4">
    <div>
        <h1 class="h3 fw-bold mb-1">{% if ve_todos %}Pedidos{% else %}Mis pedidos{% endif %}</h1>
        <p class="text-muted mb-0">{{ pedidos|length }} pedido{{ pedidos|length|pluralize }}.</p>
    </div>
    {% if puede_registrar %}
    <a href="/pedidos/nuevo/" class="btn btn-success fw-bold"><i class="bi bi-plus-circle me-1"></i>Pedir una mudanza</a>
    {% endif %}
</div>

<form method="get" class="card-panel bg-white p-3 mb-4">
    <div class="row g-2 align-items-end">
        {% for field in form %}
        <div class="col-6 col-md">
            <label for="{{ field.id_for_label }}" class="form-label small fw-semibold mb-1">{{ field.label }}</label>
            {{ field }}
            {% if field.errors %}<div class="invalid-feedback d-block">{{ field.errors.as_text }}</div>{% endif %}
        </div>
        {% endfor %}
        <div class="col-12 col-md-auto d-flex gap-2">
            <button class="btn btn-success"><i class="bi bi-funnel me-1"></i>Filtrar</button>
            <a href="{% url 'pedidos_lista' %}" class="btn btn-outline-secondary">Limpiar</a>
        </div>
    </div>
</form>

<div class="card-panel bg-white p-0 overflow-auto">
    <table class="table table-hover align-middle mb-0">
        <thead class="table-light">
            <tr>
                <th>N°</th><th>Registrado</th><th>Mudanza</th>
                {% if ve_todos %}<th>Cliente</th>{% endif %}
                <th>Servicios</th><th class="text-end">Total</th><th>Estado</th><th></th>
            </tr>
        </thead>
        <tbody>
            {% for p in pedidos %}
            <tr>
                <td class="fw-bold">{{ p.id_pedido }}</td>
                <td>{{ p.Fecha_pedido|date:"d/m/Y" }}</td>
                <td>{{ p.fecha_servicio|date:"d/m/Y" }}</td>
                {% if ve_todos %}<td>{{ p.idUsuario.Apellido }}, {{ p.idUsuario.Nombre }}</td>{% endif %}
                <td class="small">{% for d in p.detalles.all %}{{ d.idServicio.Tipo_servicio }}{% if not forloop.last %}, {% endif %}{% endfor %}</td>
                <td class="text-end">${{ p.total|floatformat:"2g" }}</td>
                <td>{% include 'pedidos/_estado.html' with estado=p.estado %}</td>
                <td class="text-end"><a href="{% url 'pedidos_detalle' p.id_pedido %}" class="btn btn-sm btn-outline-secondary">Ver</a></td>
            </tr>
            {% empty %}
            <tr><td colspan="8" class="text-center text-muted p-4">No hay pedidos con esos filtros.</td></tr>
            {% endfor %}
        </tbody>
    </table>
</div>
{% endblock %}
```

`pedidos/templates/pedidos/_estado.html`:

```html
<span class="badge {% if estado == 'Pendiente' %}text-bg-warning{% elif estado == 'Confirmado' %}text-bg-primary{% elif estado == 'Finalizado' %}text-bg-success{% else %}text-bg-secondary{% endif %}">{{ estado }}</span>
```

`pedidos/templates/pedidos/detalle.html`:

```html
{% extends 'vehiculos/base.html' %}
{% block title %}Pedido N° {{ pedido.id_pedido }}{% endblock %}
{% block content %}
<div class="mx-auto" style="max-width: 900px;">
    <a href="{% url 'pedidos_lista' %}" class="small text-decoration-none"><i class="bi bi-arrow-left"></i> Volver a pedidos</a>
    <div class="d-flex flex-wrap justify-content-between align-items-center gap-2 mt-2 mb-4">
        <h1 class="h3 fw-bold mb-0">Pedido N° {{ pedido.id_pedido }} {% include 'pedidos/_estado.html' with estado=pedido.estado %}</h1>
        <div class="d-flex flex-wrap gap-2">{% block acciones %}{% endblock %}</div>
    </div>

    {% if pedido.estado == 'Anulado' %}
    <div class="alert alert-secondary">
        <strong>Anulado</strong> el {{ pedido.fecha_anulacion|date:"d/m/Y H:i" }}
        por {{ pedido.usuario_anulacion.Nombre }} {{ pedido.usuario_anulacion.Apellido }}.
        Motivo: {{ pedido.motivo_anulacion }}
    </div>
    {% endif %}

    <div class="row g-3 mb-3">
        <div class="col-md-6"><div class="card-panel bg-white p-3 h-100">
            <h2 class="h6 fw-bold text-uppercase text-muted">Mudanza</h2>
            <p class="mb-1"><strong>Fecha:</strong> {{ pedido.fecha_servicio|date:"d/m/Y" }}</p>
            <p class="mb-1"><strong>Desde:</strong> {{ pedido.origen }}</p>
            <p class="mb-1"><strong>Hasta:</strong> {{ pedido.destino }}</p>
            <p class="mb-0"><strong>Vehículo:</strong> {{ pedido.patente_vehiculo.patente }} · {{ pedido.patente_vehiculo.marca_modelo }}</p>
        </div></div>
        <div class="col-md-6"><div class="card-panel bg-white p-3 h-100">
            <h2 class="h6 fw-bold text-uppercase text-muted">Cliente</h2>
            <p class="mb-1">{{ pedido.idUsuario.Nombre }} {{ pedido.idUsuario.Apellido }} (DNI {{ pedido.idUsuario.DNI }})</p>
            <p class="mb-1">{{ pedido.idUsuario.Correo }}</p>
            <p class="mb-0 text-muted small">Registrado el {{ pedido.Fecha_pedido|date:"d/m/Y" }}</p>
        </div></div>
    </div>

    <div class="card-panel bg-white p-3 mb-3">
        <h2 class="h6 fw-bold text-uppercase text-muted">Servicios</h2>
        <table class="table mb-0">
            <thead><tr><th>Servicio</th><th class="text-end">Precio</th><th class="text-end">Subtotal</th></tr></thead>
            <tbody>
                {% for d in pedido.detalles.all %}
                <tr><td>{{ d.idServicio.Tipo_servicio }}</td><td class="text-end">${{ d.precio_unitario|floatformat:"2g" }}</td><td class="text-end">${{ d.subtotal|floatformat:"2g" }}</td></tr>
                {% endfor %}
            </tbody>
            <tfoot><tr><th colspan="2" class="text-end">Total</th><th class="text-end">${{ pedido.total|floatformat:"2g" }}</th></tr></tfoot>
        </table>
    </div>

    <div class="card-panel bg-white p-3">
        <h2 class="h6 fw-bold text-uppercase text-muted">Inventario</h2>
        <table class="table mb-0">
            <thead><tr><th>Objeto</th><th class="text-end">Cantidad</th><th class="text-end">Peso c/u</th><th>Frágil</th></tr></thead>
            <tbody>
                {% for i in pedido.inventario.all %}
                <tr><td>{{ i.Descripcion }}</td><td class="text-end">{{ i.Cantidad }}</td><td class="text-end">{{ i.Peso }} kg</td><td>{{ i.Fragil|yesno:"Sí,No" }}</td></tr>
                {% endfor %}
            </tbody>
            <tfoot><tr><th colspan="2" class="text-end">Peso total</th><th class="text-end">{{ pedido.peso_total }} kg</th><th></th></tr></tfoot>
        </table>
    </div>
</div>
{% endblock %}
```

- [ ] **Paso 8: Menú según el rol**

En `vehiculos/templates/vehiculos/base.html`, reemplazar el `<div class="d-flex align-items-center gap-3">` del encabezado, con todo su contenido hasta su `</div>`, por:

```html
            <nav class="d-flex flex-wrap align-items-center gap-3 small text-uppercase fw-semibold">
                {% with rol=request.session.usuario_rol %}
                {% if rol == 'Administrador' %}
                <a href="{% url 'admin_dashboard' %}" class="text-white-50 text-decoration-none">Panel</a>
                <a href="{% url 'lista_vehiculos' %}" class="text-white-50 text-decoration-none">Vehículos</a>
                <a href="{% url 'pedidos_lista' %}" class="text-white-50 text-decoration-none">Pedidos</a>
                {% elif rol == 'Cliente' %}
                <a href="{% url 'pedidos_lista' %}" class="text-white-50 text-decoration-none">Mis pedidos</a>
                {% elif rol %}
                <a href="{% url 'usuario_portal' %}" class="text-white-50 text-decoration-none">Portal</a>
                {% endif %}
                {% if request.session.usuario_dni %}
                <a href="{% url 'logout' %}" class="text-white text-decoration-none">Salir <i class="bi bi-box-arrow-right ms-1"></i></a>
                {% else %}
                <a href="{% url 'login' %}" class="text-white text-decoration-none">Ingresar <i class="bi bi-box-arrow-in-right ms-1"></i></a>
                {% endif %}
                {% endwith %}
            </nav>
```

- [ ] **Paso 9: Correr las pruebas y verificar que pasan**

Correr: `docker exec mudanzas_web python manage.py test`
Esperado: `OK` en todas (incluidas las 11 nuevas de `pedidos.test_vistas`).

- [ ] **Paso 10: Commit**

```bash
git add pedidos/ usuarios/views.py vehiculos/templates/vehiculos/base.html
git commit -m "Add order permissions from the PERMISOS table, order list with filters and detail"
```

---

### Tarea 5: Pantalla para registrar el pedido

**Archivos:**
- Modificar: `pedidos/forms.py`, `pedidos/views.py`, `pedidos/urls.py`, `pedidos/test_vistas.py`, `vehiculos/templates/vehiculos/base.html`
- Crear: `pedidos/templates/pedidos/nuevo.html`

**Interfaces:**
- Consume: `reglas.registrar_pedido`, `reglas.ErrorPedido`, `reglas.vehiculos_libres`, `requiere_permiso`.
- Produce: URLs `pedidos_nuevo` (`/pedidos/nuevo/`) y `pedidos_vehiculos_libres` (`/pedidos/vehiculos-libres/?fecha=AAAA-MM-DD`, que devuelve `{"vehiculos": [{"patente", "descripcion", "capacidad_kg"}]}`). Formularios `PedidoForm` e `InventarioFormSet` (prefijo `inv`).

- [ ] **Paso 1: Escribir las pruebas que fallan**

Agregar al final de `pedidos/test_vistas.py`:

```python
class RegistrarPantallaTest(BaseVistas):
    def datos(self, **cambios):
        manana = (timezone.localdate() + timedelta(days=1)).isoformat()
        d = {'fecha_servicio': manana, 'origen': 'Av. Belgrano 100', 'destino': 'Mitre 50',
             'servicios': [self.local.id_servicio], 'vehiculo': 'AD-321-JK',
             'inv-TOTAL_FORMS': '2', 'inv-INITIAL_FORMS': '0', 'inv-MIN_NUM_FORMS': '1', 'inv-MAX_NUM_FORMS': '50',
             'inv-0-descripcion': 'Heladera', 'inv-0-cantidad': '1', 'inv-0-peso': '80', 'inv-0-fragil': 'on',
             'inv-1-descripcion': 'Cajas', 'inv-1-cantidad': '10', 'inv-1-peso': '12.5'}
        d.update(cambios)
        return d

    def test_el_cliente_registra_y_va_al_detalle(self):
        self.entrar(CLIENTE)
        r = self.client.post('/pedidos/nuevo/', self.datos())
        p = Pedido.objects.latest('id_pedido')
        self.assertRedirects(r, f'/pedidos/{p.pk}/')
        self.assertEqual((p.idUsuario, p.estado, p.total), (self.cliente, 'Pendiente', 185000))
        self.assertEqual(p.inventario.count(), 2)
        self.assertContains(self.client.get(r.url), f'Pedido N° {p.pk} registrado')

    def test_error_de_reglas_vuelve_al_formulario_con_los_datos(self):
        self.entrar(CLIENTE)
        antes = Pedido.objects.count()
        r = self.client.post('/pedidos/nuevo/', self.datos(**{'inv-0-peso': '1700'}))
        self.assertEqual(r.status_code, 200)
        self.assertIn('vehiculo', r.context['form'].errors)
        self.assertContains(r, 'Av. Belgrano 100')
        self.assertEqual(Pedido.objects.count(), antes)

    def test_sin_objetos(self):
        self.entrar(CLIENTE)
        r = self.client.post('/pedidos/nuevo/', self.datos(**{
            'inv-TOTAL_FORMS': '1', 'inv-0-descripcion': '', 'inv-0-cantidad': '', 'inv-0-peso': ''}))
        self.assertEqual(r.status_code, 200)
        self.assertTrue(r.context['items'].non_form_errors() or r.context['items'].errors[0])

    def test_el_admin_no_registra(self):
        self.entrar(ADMIN)
        self.assertEqual(self.client.get('/pedidos/nuevo/').status_code, 403)

    def test_vehiculos_libres_en_json(self):
        self.entrar(CLIENTE)
        self.pedido_de(self.otro)  # ocupa AD-321-JK mañana
        manana = (timezone.localdate() + timedelta(days=1)).isoformat()
        r = self.client.get('/pedidos/vehiculos-libres/', {'fecha': manana}).json()
        self.assertEqual([v['patente'] for v in r['vehiculos']], ['AE-123-CD'])
        self.assertEqual(r['vehiculos'][0]['capacidad_kg'], 5000.0)
        self.assertEqual(self.client.get('/pedidos/vehiculos-libres/', {'fecha': 'mal'}).json(), {'vehiculos': []})
```

- [ ] **Paso 2: Correr las pruebas y verificar que fallan**

Correr: `docker exec mudanzas_web python manage.py test pedidos.test_vistas.RegistrarPantallaTest`
Esperado: 5 fallas, con 404 para `/pedidos/nuevo/`.

- [ ] **Paso 3: Formularios**

Agregar al final de `pedidos/forms.py` (y sumar `from decimal import Decimal` y `Vehiculo` a los imports de arriba):

```python
class VehiculoField(forms.ModelChoiceField):
    def label_from_instance(self, v):
        return f'{v.patente} · {v.tipo_vehiculo} · hasta {v.capacidad_kg:.0f} kg'


class PedidoForm(forms.Form):
    """Solo convierte tipos; las reglas (fechas, capacidad, disponibilidad) están en reglas.py."""
    fecha_servicio = forms.DateField(label='Fecha de la mudanza',
                                     widget=forms.DateInput(attrs={'type': 'date'}, format='%Y-%m-%d'))
    origen = forms.CharField(max_length=200, label='Desde', widget=forms.TextInput(
        attrs={'placeholder': 'Calle, número y ciudad'}))
    destino = forms.CharField(max_length=200, label='Hasta', widget=forms.TextInput(
        attrs={'placeholder': 'Calle, número y ciudad'}))
    servicios = forms.ModelMultipleChoiceField(queryset=Servicio.objects.none(), label='Servicios',
                                               widget=forms.CheckboxSelectMultiple)
    vehiculo = VehiculoField(queryset=Vehiculo.objects.none(), label='Vehículo',
                             empty_label='Elegí primero la fecha')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['servicios'].queryset = Servicio.objects.filter(Activo=True).order_by('Tipo_servicio')
        self.fields['vehiculo'].queryset = Vehiculo.objects.filter(estado='Disponible').order_by('patente')
        con_bootstrap(self)


class ItemInventarioForm(forms.Form):
    descripcion = forms.CharField(max_length=100, label='Qué es')
    cantidad = forms.IntegerField(min_value=1, max_value=999, label='Cantidad')
    peso = forms.DecimalField(max_digits=10, decimal_places=2, min_value=Decimal('0.01'),
                              max_value=Decimal('5000'), label='Peso c/u (kg)')
    fragil = forms.BooleanField(required=False, label='Frágil')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        con_bootstrap(self)


InventarioFormSet = forms.formset_factory(ItemInventarioForm, extra=0, min_num=1,
                                          validate_min=True, max_num=50, validate_max=True)
```

- [ ] **Paso 4: Vistas**

En `pedidos/views.py`, cambiar los imports por:

```python
from datetime import date

from django.contrib import messages
from django.http import Http404, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_GET

from usuarios.models import Pedido
from . import reglas
from .forms import FiltroPedidosForm, InventarioFormSet, PedidoForm
from .permisos import requiere_permiso, tiene_permiso
```

y agregar al final:

```python
@requiere_permiso('PED_REGISTRAR')
def nuevo(request):
    if request.method == 'POST':
        form = PedidoForm(request.POST)
        items = InventarioFormSet(request.POST, prefix='inv')
        if form.is_valid() and items.is_valid():
            d = form.cleaned_data
            try:
                pedido = reglas.registrar_pedido(
                    request.usuario, d['fecha_servicio'], d['origen'], d['destino'],
                    [s.id_servicio for s in d['servicios']], d['vehiculo'].patente,
                    [f.cleaned_data for f in items.forms if f.cleaned_data])
            except reglas.ErrorPedido as e:
                for campo, mensaje in e.errores.items():
                    form.add_error(campo if campo in form.fields else None, mensaje)
            else:
                messages.success(request, f'Pedido N° {pedido.id_pedido} registrado. '
                                          'Queda pendiente hasta que la empresa lo confirme.')
                return redirect('pedidos_detalle', id_pedido=pedido.id_pedido)
        messages.error(request, 'Revisá los datos marcados.')
    else:
        form = PedidoForm()
        items = InventarioFormSet(prefix='inv')
    return render(request, 'pedidos/nuevo.html', {
        'form': form, 'items': items,
        'servicios': form.fields['servicios'].queryset,
        'elegidos': [str(v) for v in (form['servicios'].value() or [])],
    })


@requiere_permiso('PED_REGISTRAR')
@require_GET
def vehiculos_libres(request):
    """Para el formulario: los vehículos libres en la fecha elegida."""
    try:
        fecha = date.fromisoformat(request.GET.get('fecha', ''))
    except ValueError:
        return JsonResponse({'vehiculos': []})
    return JsonResponse({'vehiculos': [
        {'patente': v.patente, 'descripcion': f'{v.tipo_vehiculo} · {v.marca_modelo}',
         'capacidad_kg': float(v.capacidad_kg)}
        for v in reglas.vehiculos_libres(fecha)]})
```

En `pedidos/urls.py`, agregar antes de la línea de `pedidos_detalle`:

```python
    path('pedidos/nuevo/', views.nuevo, name='pedidos_nuevo'),
    path('pedidos/vehiculos-libres/', views.vehiculos_libres, name='pedidos_vehiculos_libres'),
```

- [ ] **Paso 5: Plantilla**

`pedidos/templates/pedidos/nuevo.html`:

```html
{% extends 'vehiculos/base.html' %}
{% block title %}Pedir una mudanza{% endblock %}
{% block content %}
<div class="mx-auto" style="max-width: 900px;">
    <h1 class="h3 fw-bold mb-1">Pedir una mudanza</h1>
    <p class="text-muted mb-4">El pedido queda pendiente hasta que la empresa lo confirme.</p>

    <form method="post" novalidate id="formPedido">
        {% csrf_token %}
        {% if form.non_field_errors %}<div class="alert alert-danger">{{ form.non_field_errors|join:" " }}</div>{% endif %}

        <div class="card-panel bg-white p-4 mb-3">
            <h2 class="h6 fw-bold text-uppercase text-muted mb-3"><i class="bi bi-geo-alt me-1"></i>1. Cuándo y dónde</h2>
            <div class="row g-3">
                {% for field in form %}{% if field.name == 'fecha_servicio' or field.name == 'origen' or field.name == 'destino' %}
                <div class="col-md-4">
                    <label for="{{ field.id_for_label }}" class="form-label fw-semibold">{{ field.label }}</label>
                    {{ field }}
                    {% if field.errors %}<div class="invalid-feedback d-block">{{ field.errors.as_text }}</div>{% endif %}
                </div>
                {% endif %}{% endfor %}
            </div>
        </div>

        <div class="card-panel bg-white p-4 mb-3">
            <h2 class="h6 fw-bold text-uppercase text-muted mb-3"><i class="bi bi-list-check me-1"></i>2. Servicios</h2>
            {% for s in servicios %}
            <div class="form-check">
                <input class="form-check-input servicio" type="checkbox" name="servicios" value="{{ s.id_servicio }}"
                       id="srv{{ s.id_servicio }}" data-precio="{{ s.Precio_base|stringformat:'s' }}"
                       {% if s.id_servicio|stringformat:'s' in elegidos %}checked{% endif %}>
                <label class="form-check-label" for="srv{{ s.id_servicio }}">{{ s.Tipo_servicio }} — ${{ s.Precio_base|floatformat:"0g" }}</label>
            </div>
            {% endfor %}
            {% if form.servicios.errors %}<div class="invalid-feedback d-block">{{ form.servicios.errors.as_text }}</div>{% endif %}
            <p class="fw-bold mt-3 mb-0">Total: $<span id="total">0</span></p>
        </div>

        <div class="card-panel bg-white p-4 mb-3">
            <h2 class="h6 fw-bold text-uppercase text-muted mb-3"><i class="bi bi-box-seam me-1"></i>3. Qué hay que llevar</h2>
            {{ items.management_form }}
            {% if items.non_form_errors %}<div class="alert alert-danger py-2">{{ items.non_form_errors|join:" " }}</div>{% endif %}
            <div id="filas">
                {% for f in items %}{% include 'pedidos/_fila_inventario.html' with f=f %}{% endfor %}
            </div>
            <template id="filaVacia">{% include 'pedidos/_fila_inventario.html' with f=items.empty_form %}</template>
            <button type="button" class="btn btn-sm btn-outline-secondary" id="agregarFila"><i class="bi bi-plus"></i> Agregar objeto</button>
            <p class="fw-bold mt-3 mb-0">Peso total: <span id="pesoTotal">0</span> kg</p>
        </div>

        <div class="card-panel bg-white p-4 mb-4">
            <h2 class="h6 fw-bold text-uppercase text-muted mb-3"><i class="bi bi-truck me-1"></i>4. Vehículo</h2>
            <label for="{{ form.vehiculo.id_for_label }}" class="form-label fw-semibold">{{ form.vehiculo.label }}</label>
            {{ form.vehiculo }}
            <div class="form-text" id="ayudaVehiculo">Se muestran solo los vehículos libres en la fecha elegida.</div>
            {% if form.vehiculo.errors %}<div class="invalid-feedback d-block">{{ form.vehiculo.errors.as_text }}</div>{% endif %}
        </div>

        <div class="d-flex justify-content-end gap-3">
            <a href="{% url 'pedidos_lista' %}" class="btn btn-outline-secondary px-4">Cancelar</a>
            <button type="submit" class="btn btn-success px-4 fw-bold">Registrar pedido</button>
        </div>
    </form>
</div>

<script>
(function () {
  const form = document.getElementById('formPedido');
  const fmt = (n) => n.toLocaleString('es-AR', { maximumFractionDigits: 2 });

  function recalcular() {
    let total = 0;
    form.querySelectorAll('.servicio:checked').forEach((c) => { total += parseFloat(c.dataset.precio); });
    document.getElementById('total').textContent = fmt(total);
    let peso = 0;
    document.querySelectorAll('#filas .fila').forEach((fila) => {
      const cant = parseFloat(fila.querySelector('[name$="-cantidad"]').value) || 0;
      const kg = parseFloat(fila.querySelector('[name$="-peso"]').value) || 0;
      peso += cant * kg;
    });
    document.getElementById('pesoTotal').textContent = fmt(peso);
  }

  const total = form.querySelector('[name="inv-TOTAL_FORMS"]');
  document.getElementById('agregarFila').addEventListener('click', () => {
    const html = document.getElementById('filaVacia').innerHTML.replace(/__prefix__/g, total.value);
    document.getElementById('filas').insertAdjacentHTML('beforeend', html);
    total.value = parseInt(total.value, 10) + 1;
  });
  form.addEventListener('input', recalcular);
  form.addEventListener('change', recalcular);

  // Al cambiar la fecha se piden los vehículos libres ese día
  const fecha = form.querySelector('[name="fecha_servicio"]');
  const select = form.querySelector('[name="vehiculo"]');
  async function cargarVehiculos() {
    if (!fecha.value) return;
    const elegido = select.value;
    const r = await fetch("{% url 'pedidos_vehiculos_libres' %}?fecha=" + encodeURIComponent(fecha.value));
    const { vehiculos } = await r.json();
    select.innerHTML = '<option value="">' + (vehiculos.length ? 'Elegí un vehículo' : 'No hay vehículos libres ese día') + '</option>' +
      vehiculos.map((v) => '<option value="' + v.patente + '"' + (v.patente === elegido ? ' selected' : '') + '>' +
        v.patente + ' · ' + v.descripcion + ' · hasta ' + fmt(v.capacidad_kg) + ' kg</option>').join('');
  }
  fecha.addEventListener('change', cargarVehiculos);
  cargarVehiculos();
  recalcular();
})();
</script>
{% endblock %}
```

`pedidos/templates/pedidos/_fila_inventario.html`:

```html
<div class="fila row g-2 align-items-end mb-2">
    <div class="col-md-5">
        <label class="form-label small mb-1">{{ f.descripcion.label }}</label>{{ f.descripcion }}
    </div>
    <div class="col-4 col-md-2">
        <label class="form-label small mb-1">{{ f.cantidad.label }}</label>{{ f.cantidad }}
    </div>
    <div class="col-4 col-md-3">
        <label class="form-label small mb-1">{{ f.peso.label }}</label>{{ f.peso }}
    </div>
    <div class="col-4 col-md-2">
        <div class="form-check mb-2">{{ f.fragil }} <label class="form-check-label small" for="{{ f.fragil.id_for_label }}">{{ f.fragil.label }}</label></div>
    </div>
    {% if f.errors %}<div class="col-12 invalid-feedback d-block">{% for e in f.errors.values %}{{ e.as_text }} {% endfor %}</div>{% endif %}
</div>
```

En `vehiculos/templates/vehiculos/base.html`, dentro de `{% elif rol == 'Cliente' %}`, después del enlace «Mis pedidos»:

```html
                <a href="{% url 'pedidos_nuevo' %}" class="text-white-50 text-decoration-none">Pedir mudanza</a>
```

En `pedidos/templates/pedidos/lista.html`, cambiar `href="/pedidos/nuevo/"` por `href="{% url 'pedidos_nuevo' %}"`.

- [ ] **Paso 6: Correr las pruebas y verificar que pasan**

Correr: `docker exec mudanzas_web python manage.py test`
Esperado: `OK` en todas.

- [ ] **Paso 7: Probar a mano en el navegador**

Entrar como `gomezm` en http://localhost:8002/login/ y abrir «Pedir mudanza».
- Al elegir la fecha de mañana, el combo de vehículos tiene que mostrar AD-321-JK y AE-123-CD.
- El total y el peso total tienen que cambiar al tildar servicios y escribir pesos.
- «Agregar objeto» suma una fila.
- Al registrar, se llega al detalle con el mensaje verde.

- [ ] **Paso 8: Commit**

```bash
git add pedidos/ vehiculos/templates/vehiculos/base.html
git commit -m "Add the order registration page with live totals and free vehicles by date"
```

---

### Tarea 6: Confirmar, finalizar y anular desde la pantalla

**Archivos:**
- Modificar: `pedidos/forms.py`, `pedidos/views.py`, `pedidos/urls.py`, `pedidos/templates/pedidos/detalle.html`, `pedidos/test_vistas.py`
- Crear: `pedidos/templates/pedidos/anular.html`

**Interfaces:**
- Consume: `reglas.confirmar`, `reglas.finalizar`, `reglas.anular`, `reglas.ErrorPedido`.
- Produce: URLs `pedidos_confirmar`, `pedidos_finalizar` (solo POST) y `pedidos_anular` (GET muestra el formulario; POST anula).

- [ ] **Paso 1: Escribir las pruebas que fallan**

Agregar al final de `pedidos/test_vistas.py`:

```python
class AccionesTest(BaseVistas):
    def setUp(self):
        self.p = self.pedido_de(self.cliente)

    def test_el_admin_confirma_y_finaliza(self):
        self.entrar(ADMIN)
        self.assertRedirects(self.client.post(f'/pedidos/{self.p.pk}/confirmar/'), f'/pedidos/{self.p.pk}/')
        self.client.post(f'/pedidos/{self.p.pk}/finalizar/')
        self.assertEqual(Pedido.objects.get(pk=self.p.pk).estado, 'Finalizado')

    def test_transicion_invalida_muestra_el_error(self):
        self.entrar(ADMIN)
        r = self.client.post(f'/pedidos/{self.p.pk}/finalizar/', follow=True)
        self.assertContains(r, 'No se puede finalizar')
        self.assertEqual(Pedido.objects.get(pk=self.p.pk).estado, 'Pendiente')

    def test_las_acciones_son_solo_por_post(self):
        self.entrar(ADMIN)
        self.assertEqual(self.client.get(f'/pedidos/{self.p.pk}/confirmar/').status_code, 405)

    def test_el_admin_anula_con_motivo(self):
        self.entrar(ADMIN)
        self.assertContains(self.client.get(f'/pedidos/{self.p.pk}/anular/'), 'Motivo')
        r = self.client.post(f'/pedidos/{self.p.pk}/anular/', {'motivo': 'Pedido duplicado'})
        self.assertRedirects(r, f'/pedidos/{self.p.pk}/')
        p = Pedido.objects.get(pk=self.p.pk)
        self.assertEqual((p.estado, p.motivo_anulacion, p.usuario_anulacion.DNI), ('Anulado', 'Pedido duplicado', ADMIN))

    def test_motivo_corto(self):
        self.entrar(ADMIN)
        r = self.client.post(f'/pedidos/{self.p.pk}/anular/', {'motivo': 'no'})
        self.assertEqual(r.status_code, 200)
        self.assertIn('motivo', r.context['form'].errors)
        self.assertEqual(Pedido.objects.get(pk=self.p.pk).estado, 'Pendiente')

    def test_el_cliente_no_confirma_ni_anula(self):
        self.entrar(CLIENTE)
        self.assertEqual(self.client.post(f'/pedidos/{self.p.pk}/confirmar/').status_code, 403)
        self.assertEqual(self.client.post(f'/pedidos/{self.p.pk}/anular/', {'motivo': 'Me arrepentí'}).status_code, 403)
        self.assertEqual(Pedido.objects.get(pk=self.p.pk).estado, 'Pendiente')

    def test_botones_segun_el_perfil(self):
        self.entrar(ADMIN)
        r = self.client.get(f'/pedidos/{self.p.pk}/')
        self.assertContains(r, 'Confirmar')
        self.assertContains(r, 'Anular')
        self.entrar(CLIENTE)
        r = self.client.get(f'/pedidos/{self.p.pk}/')
        self.assertNotContains(r, '/confirmar/')
        self.assertNotContains(r, '/anular/')
```

- [ ] **Paso 2: Correr las pruebas y verificar que fallan**

Correr: `docker exec mudanzas_web python manage.py test pedidos.test_vistas.AccionesTest`
Esperado: fallas por 404 en `/confirmar/`, `/finalizar/` y `/anular/`.

- [ ] **Paso 3: Formulario y vistas**

Agregar al final de `pedidos/forms.py`:

```python
class AnularForm(forms.Form):
    motivo = forms.CharField(min_length=5, max_length=200, label='Motivo de la anulación',
                             widget=forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}))
```

En `pedidos/views.py`, agregar `require_POST` al import de `django.views.decorators.http` y `AnularForm` al import de `.forms`, y agregar al final:

```python
def _accion(request, id_pedido, funcion, hecho):
    get_object_or_404(Pedido, pk=id_pedido)
    try:
        funcion(id_pedido)
        messages.success(request, f'Pedido N° {id_pedido} {hecho}.')
    except reglas.ErrorPedido as e:
        messages.error(request, str(e))
    return redirect('pedidos_detalle', id_pedido=id_pedido)


@requiere_permiso('PED_GESTIONAR')
@require_POST
def confirmar(request, id_pedido):
    return _accion(request, id_pedido, reglas.confirmar, 'confirmado')


@requiere_permiso('PED_GESTIONAR')
@require_POST
def finalizar(request, id_pedido):
    return _accion(request, id_pedido, reglas.finalizar, 'finalizado')


@requiere_permiso('PED_ANULAR')
def anular(request, id_pedido):
    pedido = get_object_or_404(Pedido, pk=id_pedido)
    form = AnularForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        try:
            reglas.anular(id_pedido, request.usuario, form.cleaned_data['motivo'])
        except reglas.ErrorPedido as e:
            if 'motivo' in e.errores:
                form.add_error('motivo', e.errores['motivo'])
            else:
                messages.error(request, str(e))
                return redirect('pedidos_detalle', id_pedido=id_pedido)
        else:
            messages.success(request, f'Pedido N° {id_pedido} anulado.')
            return redirect('pedidos_detalle', id_pedido=id_pedido)
    return render(request, 'pedidos/anular.html', {'pedido': pedido, 'form': form})
```

En `pedidos/urls.py`, agregar al final de la lista:

```python
    path('pedidos/<int:id_pedido>/confirmar/', views.confirmar, name='pedidos_confirmar'),
    path('pedidos/<int:id_pedido>/finalizar/', views.finalizar, name='pedidos_finalizar'),
    path('pedidos/<int:id_pedido>/anular/', views.anular, name='pedidos_anular'),
```

- [ ] **Paso 4: Plantillas**

`pedidos/templates/pedidos/anular.html`:

```html
{% extends 'vehiculos/base.html' %}
{% block title %}Anular pedido N° {{ pedido.id_pedido }}{% endblock %}
{% block content %}
<div class="mx-auto" style="max-width: 600px;">
    <h1 class="h3 fw-bold mb-1">Anular pedido N° {{ pedido.id_pedido }}</h1>
    <p class="text-muted mb-4">El pedido no se borra: queda «Anulado» con la fecha, el motivo y tu usuario, y el vehículo vuelve a estar libre ese día.</p>
    <form method="post" class="card-panel bg-white p-4" novalidate>
        {% csrf_token %}
        <label for="{{ form.motivo.id_for_label }}" class="form-label fw-semibold">{{ form.motivo.label }}</label>
        {{ form.motivo }}
        {% if form.motivo.errors %}<div class="invalid-feedback d-block">{{ form.motivo.errors.as_text }}</div>{% endif %}
        <div class="d-flex justify-content-end gap-3 mt-3">
            <a href="{% url 'pedidos_detalle' pedido.id_pedido %}" class="btn btn-outline-secondary">Volver</a>
            <button class="btn btn-danger fw-bold">Anular pedido</button>
        </div>
    </form>
</div>
{% endblock %}
```

En `pedidos/templates/pedidos/detalle.html`, reemplazar `<div class="d-flex flex-wrap gap-2">{% block acciones %}{% endblock %}</div>` por:

```html
        <div class="d-flex flex-wrap gap-2">
            {% if puede_gestionar and pedido.estado == 'Pendiente' %}
            <form method="post" action="{% url 'pedidos_confirmar' pedido.id_pedido %}">{% csrf_token %}
                <button class="btn btn-primary"><i class="bi bi-check2-circle me-1"></i>Confirmar</button></form>
            {% endif %}
            {% if puede_gestionar and pedido.estado == 'Confirmado' %}
            <form method="post" action="{% url 'pedidos_finalizar' pedido.id_pedido %}">{% csrf_token %}
                <button class="btn btn-success"><i class="bi bi-flag me-1"></i>Finalizar</button></form>
            {% endif %}
            {% if puede_anular and pedido.estado == 'Pendiente' or puede_anular and pedido.estado == 'Confirmado' %}
            <a href="{% url 'pedidos_anular' pedido.id_pedido %}" class="btn btn-outline-danger"><i class="bi bi-x-circle me-1"></i>Anular</a>
            {% endif %}
        </div>
```

- [ ] **Paso 5: Correr las pruebas y verificar que pasan**

Correr: `docker exec mudanzas_web python manage.py test`
Esperado: `OK` en todas.

- [ ] **Paso 6: Commit**

```bash
git add pedidos/
git commit -m "Let the admin confirm, finish and cancel orders with a reason"
```

---

### Tarea 7: Comprobante imprimible

**Archivos:**
- Modificar: `pedidos/views.py`, `pedidos/urls.py`, `pedidos/templates/pedidos/detalle.html`, `pedidos/test_vistas.py`
- Crear: `pedidos/templates/pedidos/comprobante.html`

**Interfaces:**
- Consume: `_pedido_visible`, `requiere_permiso`.
- Produce: URL `pedidos_comprobante` (`/pedidos/<int:id_pedido>/comprobante/`).

- [ ] **Paso 1: Escribir las pruebas que fallan**

Agregar al final de `pedidos/test_vistas.py`:

```python
class ComprobanteTest(BaseVistas):
    def setUp(self):
        self.p = self.pedido_de(self.cliente)

    def test_el_cliente_imprime_el_suyo(self):
        self.entrar(CLIENTE)
        r = self.client.get(f'/pedidos/{self.p.pk}/comprobante/')
        self.assertContains(r, f'Pedido N° {self.p.pk}')
        self.assertContains(r, 'Mudanza local')
        self.assertContains(r, '185.000,00')
        self.assertContains(r, 'window.print()')

    def test_el_comprobante_ajeno_da_404(self):
        ajeno = self.pedido_de(self.otro, dias=2)
        self.entrar(CLIENTE)
        self.assertEqual(self.client.get(f'/pedidos/{ajeno.pk}/comprobante/').status_code, 404)

    def test_muestra_la_anulacion(self):
        reglas.anular(self.p.pk, Usuario.objects.get(DNI=ADMIN), 'Pedido duplicado')
        self.entrar(ADMIN)
        r = self.client.get(f'/pedidos/{self.p.pk}/comprobante/')
        self.assertContains(r, 'ANULADO')
        self.assertContains(r, 'Pedido duplicado')

    def test_el_chofer_no_emite(self):
        self.entrar(CHOFER)
        self.assertEqual(self.client.get(f'/pedidos/{self.p.pk}/comprobante/').status_code, 403)
```

- [ ] **Paso 2: Correr las pruebas y verificar que fallan**

Correr: `docker exec mudanzas_web python manage.py test pedidos.test_vistas.ComprobanteTest`
Esperado: fallas por 404.

- [ ] **Paso 3: Vista y URL**

Agregar al final de `pedidos/views.py` (y sumar `from django.utils import timezone` a los imports):

```python
@requiere_permiso('PED_COMPROBANTE')
def comprobante(request, id_pedido):
    pedido = _pedido_visible(request, id_pedido)
    return render(request, 'pedidos/comprobante.html', {'pedido': pedido, 'emitido': timezone.localtime()})
```

En `pedidos/urls.py`, agregar al final de la lista:

```python
    path('pedidos/<int:id_pedido>/comprobante/', views.comprobante, name='pedidos_comprobante'),
```

- [ ] **Paso 4: Plantilla del comprobante**

`pedidos/templates/pedidos/comprobante.html`:

```html
{% load static %}
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Comprobante — Pedido N° {{ pedido.id_pedido }}</title>
    <style>
        body { font-family: Arial, sans-serif; color: #1c1006; margin: 0; background: #f4f1ee; }
        .hoja { background: #fff; max-width: 800px; margin: 24px auto; padding: 32px; box-shadow: 0 2px 8px rgba(0,0,0,.1); }
        header { display: flex; justify-content: space-between; align-items: center; border-bottom: 3px solid #ea580c; padding-bottom: 12px; }
        header img { height: 56px; background: #1c1006; padding: 6px; border-radius: 6px; }
        h1 { font-size: 20px; margin: 0; }
        h2 { font-size: 13px; text-transform: uppercase; color: #7c6f64; margin: 20px 0 6px; }
        table { width: 100%; border-collapse: collapse; font-size: 14px; }
        th, td { border-bottom: 1px solid #e7ddd3; padding: 6px; text-align: left; }
        .num { text-align: right; }
        .total td { font-weight: bold; border-top: 2px solid #1c1006; }
        .datos { display: grid; grid-template-columns: 1fr 1fr; gap: 4px 24px; font-size: 14px; }
        .anulado { border: 2px solid #b91c1c; color: #b91c1c; padding: 8px 12px; margin-top: 16px; font-weight: bold; }
        .pie { font-size: 12px; color: #7c6f64; margin-top: 24px; }
        .acciones { text-align: center; margin: 16px; }
        .acciones button, .acciones a { font-size: 15px; padding: 8px 18px; margin: 0 4px; }
        @media print {
            body { background: #fff; }
            .hoja { box-shadow: none; margin: 0; max-width: none; }
            .acciones { display: none; }
        }
    </style>
</head>
<body>
<div class="acciones">
    <button onclick="window.print()">Imprimir / Guardar PDF</button>
    <a href="{% url 'pedidos_detalle' pedido.id_pedido %}">Volver al pedido</a>
</div>
<div class="hoja">
    <header>
        <img src="{% static 'img/logo.png' %}" alt="Mudanzas y Fletes Salta">
        <div style="text-align:right">
            <h1>Pedido N° {{ pedido.id_pedido }}</h1>
            <div>Estado: <strong>{{ pedido.estado }}</strong></div>
            <div>Registrado el {{ pedido.Fecha_pedido|date:"d/m/Y" }}</div>
        </div>
    </header>

    {% if pedido.estado == 'Anulado' %}
    <div class="anulado">ANULADO el {{ pedido.fecha_anulacion|date:"d/m/Y H:i" }} por {{ pedido.usuario_anulacion.Nombre }} {{ pedido.usuario_anulacion.Apellido }}. Motivo: {{ pedido.motivo_anulacion }}</div>
    {% endif %}

    <h2>Cliente</h2>
    <div class="datos">
        <div>{{ pedido.idUsuario.Apellido }}, {{ pedido.idUsuario.Nombre }}</div>
        <div>DNI {{ pedido.idUsuario.DNI }}</div>
        <div>{{ pedido.idUsuario.Correo }}</div>
        <div>{{ pedido.idUsuario.Telefono|default:"" }}</div>
    </div>

    <h2>Mudanza</h2>
    <div class="datos">
        <div><strong>Fecha:</strong> {{ pedido.fecha_servicio|date:"d/m/Y" }}</div>
        <div><strong>Vehículo:</strong> {{ pedido.patente_vehiculo.patente }} — {{ pedido.patente_vehiculo.marca_modelo }}</div>
        <div><strong>Desde:</strong> {{ pedido.origen }}</div>
        <div><strong>Hasta:</strong> {{ pedido.destino }}</div>
    </div>

    <h2>Servicios</h2>
    <table>
        <tr><th>Servicio</th><th class="num">Precio</th><th class="num">Subtotal</th></tr>
        {% for d in pedido.detalles.all %}
        <tr><td>{{ d.idServicio.Tipo_servicio }}</td><td class="num">${{ d.precio_unitario|floatformat:"2g" }}</td><td class="num">${{ d.subtotal|floatformat:"2g" }}</td></tr>
        {% endfor %}
        <tr class="total"><td colspan="2" class="num">TOTAL</td><td class="num">${{ pedido.total|floatformat:"2g" }}</td></tr>
    </table>

    <h2>Inventario</h2>
    <table>
        <tr><th>Objeto</th><th class="num">Cantidad</th><th class="num">Peso c/u</th><th>Frágil</th></tr>
        {% for i in pedido.inventario.all %}
        <tr><td>{{ i.Descripcion }}</td><td class="num">{{ i.Cantidad }}</td><td class="num">{{ i.Peso }} kg</td><td>{{ i.Fragil|yesno:"Sí,No" }}</td></tr>
        {% endfor %}
        <tr class="total"><td colspan="2" class="num">Peso total</td><td class="num">{{ pedido.peso_total }} kg</td><td></td></tr>
    </table>

    <p class="pie">Mudanzas y Fletes Salta · Comprobante emitido el {{ emitido|date:"d/m/Y H:i" }}. No válido como factura.</p>
</div>
</body>
</html>
```

En `pedidos/templates/pedidos/detalle.html`, dentro del `<div class="d-flex flex-wrap gap-2">` de las acciones, agregar al principio:

```html
            {% if puede_comprobante %}
            <a href="{% url 'pedidos_comprobante' pedido.id_pedido %}" class="btn btn-outline-secondary" target="_blank"><i class="bi bi-printer me-1"></i>Comprobante</a>
            {% endif %}
```

- [ ] **Paso 5: Correr las pruebas y verificar que pasan**

Correr: `docker exec mudanzas_web python manage.py test`
Esperado: `OK` en todas. Si `test_el_cliente_imprime_el_suyo` falla por el formato del número, revisar `LANGUAGE_CODE = 'es-ar'` en `core/settings.py`: `floatformat:"2g"` usa el separador de miles del idioma activo y da `185.000,00`.

- [ ] **Paso 6: Commit**

```bash
git add pedidos/
git commit -m "Add the printable order receipt"
```

---

### Tarea 8: Crear cuenta de cliente

**Archivos:**
- Modificar: `usuarios/utils.py`, `usuarios/views.py` (`alta_usuario`), `usuarios/templates/login.html`, `pedidos/forms.py`, `pedidos/views.py`, `pedidos/urls.py`, `pedidos/test_vistas.py`
- Crear: `pedidos/templates/pedidos/registro.html`

**Interfaces:**
- Produce: `usuarios.utils.nombre_usuario_libre(apellido: str, nombre: str) -> str`, la URL `registro_cliente` (`/registro/`) y `forms.RegistroClienteForm` con `.crear_cliente() -> Usuario`.

- [ ] **Paso 1: Escribir las pruebas que fallan**

Agregar al final de `pedidos/test_vistas.py`:

```python
class RegistroClienteTest(BaseVistas):
    def datos(self, **cambios):
        d = {'dni': '33444555', 'apellido': 'Herrera', 'nombre': 'Juan Pablo', 'correo': 'JP@Mail.com',
             'telefono': '3874000000', 'clave': 'Cliente123!', 'clave2': 'Cliente123!'}
        d.update(cambios)
        return d

    def test_crea_la_cuenta_y_entra(self):
        r = self.client.post('/registro/', self.datos())
        self.assertRedirects(r, '/pedidos/')
        u = Usuario.objects.get(DNI=33444555)
        self.assertEqual(u.NombreUsuario, 'herreraj1')  # herreraj ya existe
        self.assertEqual((u.idRol.nom_rol, u.DebeCambiarClave, u.Correo), ('Cliente', False, 'jp@mail.com'))
        self.assertTrue(u.verificar_clave('Cliente123!'))
        self.assertNotEqual(u.Clave, 'Cliente123!')
        self.assertEqual(self.client.session['usuario_dni'], 33444555)

    def test_rechaza_repetidos_y_clave_debil(self):
        for cambios, campo in [({'dni': str(CLIENTE)}, 'dni'),
                               ({'correo': 'maria.gomez@ejemplo.com'}, 'correo'),
                               ({'clave': 'debil', 'clave2': 'debil'}, 'clave'),
                               ({'clave2': 'Otra123!'}, 'clave2')]:
            r = self.client.post('/registro/', self.datos(**cambios))
            self.assertEqual(r.status_code, 200, cambios)
            self.assertIn(campo, r.context['form'].errors, cambios)
        self.assertFalse(Usuario.objects.filter(DNI=33444555).exists())

    def test_el_login_ofrece_crear_cuenta(self):
        self.assertContains(self.client.get('/login/'), '/registro/')
```

- [ ] **Paso 2: Correr las pruebas y verificar que fallan**

Correr: `docker exec mudanzas_web python manage.py test pedidos.test_vistas.RegistroClienteTest`
Esperado: fallas por 404 en `/registro/`.

- [ ] **Paso 3: Usuario automático compartido**

Agregar al final de `usuarios/utils.py`:

```python
def nombre_usuario_libre(apellido: str, nombre: str) -> str:
    """Apellido + inicial; si ya existe, le suma un número (gomezm, gomezm1, ...)."""
    from .models import Usuario  # import local: utils no depende de los modelos para lo demás
    base = generate_username(apellido, nombre)
    candidato, n = base, 1
    while Usuario.objects.filter(NombreUsuario=candidato).exists():
        candidato, n = f'{base}{n}', n + 1
    return candidato
```

En `usuarios/views.py`, dentro de `alta_usuario`, reemplazar el bloque desde `# Regla: Apellido + primera letra del primer nombre` hasta el `idx += 1` del `while` por:

```python
        # Regla: Apellido + primera letra del primer nombre
        final_user = nombre_usuario_libre(apellido, nombre)
```

y sumar `nombre_usuario_libre` al import de `.utils`.

- [ ] **Paso 4: Formulario y vista**

Agregar al final de `pedidos/forms.py` (sumar `Rol` al import de `usuarios.models` y agregar `from usuarios.utils import hash_password, nombre_usuario_libre, validate_strong_password`):

```python
class RegistroClienteForm(forms.Form):
    dni = forms.IntegerField(label='DNI', min_value=1000000, max_value=99999999)
    apellido = forms.CharField(max_length=100, label='Apellido')
    nombre = forms.CharField(max_length=100, label='Nombre')
    correo = forms.EmailField(max_length=150, label='Correo')
    telefono = forms.CharField(max_length=30, required=False, label='Teléfono')
    clave = forms.CharField(label='Clave', widget=forms.PasswordInput,
                            help_text='8 o más caracteres, con mayúscula, minúscula, número y un caracter especial.')
    clave2 = forms.CharField(label='Repetir clave', widget=forms.PasswordInput)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        con_bootstrap(self)

    def clean_dni(self):
        dni = self.cleaned_data['dni']
        if Usuario.objects.filter(DNI=dni).exists():
            raise forms.ValidationError('Ya hay una cuenta con ese DNI.')
        return dni

    def clean_correo(self):
        correo = self.cleaned_data['correo'].strip().lower()
        if Usuario.objects.filter(Correo=correo).exists():
            raise forms.ValidationError('Ese correo ya está en uso.')
        return correo

    def clean_clave(self):
        valida, mensaje = validate_strong_password(self.cleaned_data['clave'])
        if not valida:
            raise forms.ValidationError(mensaje)
        return self.cleaned_data['clave']

    def clean(self):
        datos = super().clean()
        if datos.get('clave') and datos.get('clave2') and datos['clave'] != datos['clave2']:
            self.add_error('clave2', 'Las claves no coinciden.')
        return datos

    def crear_cliente(self):
        d = self.cleaned_data
        return Usuario.objects.create(
            DNI=d['dni'], Apellido=d['apellido'].strip(), Nombre=d['nombre'].strip(), Correo=d['correo'],
            Telefono=d['telefono'] or None,
            NombreUsuario=nombre_usuario_libre(d['apellido'], d['nombre']),
            Clave=hash_password(d['clave']), Activo=True,
            DebeCambiarClave=False,  # la clave la eligió el cliente
            idRol=Rol.objects.get(nom_rol='Cliente'))
```

Agregar al final de `pedidos/views.py` (sumar `RegistroClienteForm` al import de `.forms`):

```python
def registro(request):
    """Alta pública de clientes: queda con el rol Cliente e inicia sesión."""
    form = RegistroClienteForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        cliente = form.crear_cliente()
        cliente.registrar_acceso()
        request.session['usuario_dni'] = cliente.DNI
        request.session['usuario_rol'] = cliente.idRol.nom_rol
        messages.success(request, f'¡Bienvenida/o! Tu usuario es {cliente.NombreUsuario}.')
        return redirect('pedidos_lista')
    return render(request, 'pedidos/registro.html', {'form': form})
```

En `pedidos/urls.py`, agregar al principio de la lista:

```python
    path('registro/', views.registro, name='registro_cliente'),
```

- [ ] **Paso 5: Plantillas**

`pedidos/templates/pedidos/registro.html`:

```html
{% extends 'vehiculos/base.html' %}
{% block title %}Crear cuenta{% endblock %}
{% block content %}
<div class="mx-auto" style="max-width: 640px;">
    <h1 class="h3 fw-bold mb-1">Crear cuenta</h1>
    <p class="text-muted mb-4">Con tu cuenta podés pedir mudanzas y seguir su estado. Tu usuario se genera solo con tu apellido y la inicial de tu nombre.</p>
    <form method="post" class="card-panel bg-white p-4" novalidate>
        {% csrf_token %}
        <div class="row g-3">
            {% for field in form %}
            <div class="col-md-6">
                <label for="{{ field.id_for_label }}" class="form-label fw-semibold">{{ field.label }}</label>
                {{ field }}
                {% if field.help_text %}<div class="form-text">{{ field.help_text }}</div>{% endif %}
                {% if field.errors %}<div class="invalid-feedback d-block">{{ field.errors.as_text }}</div>{% endif %}
            </div>
            {% endfor %}
        </div>
        <div class="d-flex justify-content-between align-items-center mt-4">
            <a href="{% url 'login' %}">Ya tengo cuenta</a>
            <button class="btn btn-success fw-bold px-4">Crear cuenta</button>
        </div>
    </form>
</div>
{% endblock %}
```

En `usuarios/templates/login.html`, dentro del `<div class="pt-2 text-center">` que tiene el botón «¿Olvidaste tu contraseña?», agregar después de ese `</button>`:

```html
        <a href="{% url 'registro_cliente' %}" class="block mt-3 text-xs text-gray-300 hover:text-white font-semibold transition">
          ¿Querés pedir una mudanza? <span class="text-amber-gold">Creá tu cuenta</span>
        </a>
```

- [ ] **Paso 6: Correr las pruebas y verificar que pasan**

Correr: `docker exec mudanzas_web python manage.py test`
Esperado: `OK` en todas, incluidas las de alta del Hito 2 (`pereza`, `pereza1`), que ahora pasan por `nombre_usuario_libre`.

- [ ] **Paso 7: Commit**

```bash
git add usuarios/ pedidos/
git commit -m "Let clients create their own account from the login page"
```

---

### Tarea 9: ABM de servicios

**Archivos:**
- Modificar: `pedidos/forms.py`, `pedidos/urls.py`, `vehiculos/templates/vehiculos/base.html`, `usuarios/templates/admin_dashboard.html`
- Crear: `pedidos/views_servicios.py`, `pedidos/templates/pedidos/servicios_lista.html`, `pedidos/templates/pedidos/servicio_form.html`, `pedidos/test_servicios.py`

**Interfaces:**
- Consume: `requiere_permiso('SRV_GESTIONAR')`, `con_bootstrap`.
- Produce: URLs `servicios_lista`, `servicios_crear`, `servicios_editar` y `servicios_baja` (POST). `forms.ServicioForm` con el campo extra `materiales` (texto separado por comas).

- [ ] **Paso 1: Escribir las pruebas que fallan**

`pedidos/test_servicios.py`:

```python
"""ABM de servicios (tabla maestra del Hito 3) con sus materiales."""
import io
from datetime import timedelta
from decimal import Decimal

from django.core.management import call_command
from django.test import TestCase
from django.utils import timezone

from pedidos import reglas
from usuarios.models import Servicio, Usuario

ADMIN, CLIENTE = 35123456, 29876543


class ServiciosTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command('init_data', stdout=io.StringIO())

    def entrar(self, dni):
        s = self.client.session
        s['usuario_dni'] = dni
        s['usuario_rol'] = Usuario.objects.get(DNI=dni).idRol.nom_rol
        s.save()

    def test_lista(self):
        self.entrar(ADMIN)
        r = self.client.get('/servicios/')
        self.assertContains(r, 'Mudanza nacional')
        self.assertContains(r, 'Mantas, film y cintas')

    def test_alta_con_materiales(self):
        self.entrar(ADMIN)
        r = self.client.post('/servicios/nuevo/', {'Tipo_servicio': 'Embalaje', 'Precio_base': '40000',
                                                   'Activo': 'on', 'materiales': 'Cajas, burbujas ,  cinta'})
        self.assertRedirects(r, '/servicios/')
        s = Servicio.objects.get(Tipo_servicio='Embalaje')
        self.assertEqual(sorted(s.recursos.values_list('Materiales', flat=True)), ['Cajas', 'burbujas', 'cinta'])

    def test_precio_tiene_que_ser_positivo(self):
        self.entrar(ADMIN)
        r = self.client.post('/servicios/nuevo/', {'Tipo_servicio': 'Gratis', 'Precio_base': '0', 'materiales': ''})
        self.assertEqual(r.status_code, 200)
        self.assertIn('Precio_base', r.context['form'].errors)

    def test_material_demasiado_largo(self):
        self.entrar(ADMIN)
        r = self.client.post('/servicios/nuevo/', {'Tipo_servicio': 'X', 'Precio_base': '1', 'materiales': 'a' * 51})
        self.assertIn('materiales', r.context['form'].errors)

    def test_editar_reemplaza_los_materiales(self):
        self.entrar(ADMIN)
        s = Servicio.objects.get(Tipo_servicio='Flete urbano')
        self.client.post(f'/servicios/{s.pk}/editar/', {'Tipo_servicio': 'Flete urbano', 'Precio_base': '80000',
                                                        'Activo': 'on', 'materiales': 'Correas'})
        s.refresh_from_db()
        self.assertEqual(s.Precio_base, 80000)
        self.assertEqual(list(s.recursos.values_list('Materiales', flat=True)), ['Correas'])

    def test_baja_logica_conserva_los_pedidos_viejos(self):
        self.entrar(ADMIN)
        s = Servicio.objects.get(Tipo_servicio='Mudanza local')
        self.assertRedirects(self.client.post(f'/servicios/{s.pk}/baja/'), '/servicios/')
        s.refresh_from_db()
        self.assertFalse(s.Activo)
        self.assertTrue(s.detalles.exists())  # el pedido de ejemplo lo sigue teniendo
        with self.assertRaises(reglas.ErrorPedido):
            reglas.registrar_pedido(
                Usuario.objects.get(DNI=CLIENTE), timezone.localdate() + timedelta(days=1), 'A 1', 'B 2',
                [s.id_servicio], 'AD-321-JK', [{'descripcion': 'Caja', 'cantidad': 1, 'peso': Decimal('1')}])

    def test_el_cliente_no_entra(self):
        self.entrar(CLIENTE)
        self.assertEqual(self.client.get('/servicios/').status_code, 403)
```

- [ ] **Paso 2: Correr las pruebas y verificar que fallan**

Correr: `docker exec mudanzas_web python manage.py test pedidos.test_servicios`
Esperado: fallas por 404 en `/servicios/`.

- [ ] **Paso 3: Formulario**

Agregar al final de `pedidos/forms.py` (sumar `RecursoAsignado` al import de `usuarios.models` y `from django.db import transaction` arriba):

```python
class ServicioForm(forms.ModelForm):
    materiales = forms.CharField(required=False, label='Materiales que incluye',
                                 help_text='Separados por coma. Ej.: Mantas, film, cintas')

    class Meta:
        model = Servicio
        fields = ['Tipo_servicio', 'Precio_base', 'Activo']
        labels = {'Tipo_servicio': 'Tipo de servicio', 'Precio_base': 'Precio base ($)'}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk:
            self.fields['materiales'].initial = ', '.join(
                self.instance.recursos.values_list('Materiales', flat=True))
        con_bootstrap(self)
        self.fields['Activo'].widget.attrs['class'] = 'form-check-input'

    def clean_Precio_base(self):
        precio = self.cleaned_data['Precio_base']
        if precio <= 0:
            raise forms.ValidationError('El precio tiene que ser mayor a 0.')
        return precio

    def clean_materiales(self):
        lista = [m.strip() for m in self.cleaned_data['materiales'].split(',') if m.strip()]
        largos = [m for m in lista if len(m) > 50]
        if largos:
            raise forms.ValidationError(f'«{largos[0][:20]}…» supera los 50 caracteres.')
        return lista

    def save(self, commit=True):
        with transaction.atomic():
            servicio = super().save()
            servicio.recursos.all().delete()  # los materiales se reemplazan; el servicio no se borra
            RecursoAsignado.objects.bulk_create(
                [RecursoAsignado(idServicio=servicio, Materiales=m) for m in self.cleaned_data['materiales']])
        return servicio
```

- [ ] **Paso 4: Vistas y URLs**

`pedidos/views_servicios.py`:

```python
"""ABM de servicios: la tabla maestra que el pedido necesita y no se hizo en hitos anteriores."""
from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from usuarios.models import Servicio
from .forms import ServicioForm
from .permisos import requiere_permiso


@requiere_permiso('SRV_GESTIONAR')
def lista(request):
    servicios = Servicio.objects.prefetch_related('recursos').order_by('-Activo', 'Tipo_servicio')
    return render(request, 'pedidos/servicios_lista.html', {'servicios': servicios})


@requiere_permiso('SRV_GESTIONAR')
def crear(request):
    form = ServicioForm(request.POST or None, initial={'Activo': True})
    if request.method == 'POST' and form.is_valid():
        servicio = form.save()
        messages.success(request, f'Servicio «{servicio.Tipo_servicio}» creado.')
        return redirect('servicios_lista')
    return render(request, 'pedidos/servicio_form.html', {'form': form, 'titulo': 'Nuevo servicio'})


@requiere_permiso('SRV_GESTIONAR')
def editar(request, id_servicio):
    servicio = get_object_or_404(Servicio, pk=id_servicio)
    form = ServicioForm(request.POST or None, instance=servicio)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, f'Servicio «{servicio.Tipo_servicio}» actualizado.')
        return redirect('servicios_lista')
    return render(request, 'pedidos/servicio_form.html', {'form': form, 'titulo': f'Editar «{servicio.Tipo_servicio}»'})


@requiere_permiso('SRV_GESTIONAR')
@require_POST
def baja(request, id_servicio):
    """Baja lógica: deja de ofrecerse, pero los pedidos que ya lo tienen lo conservan."""
    servicio = get_object_or_404(Servicio, pk=id_servicio)
    servicio.Activo = False
    servicio.save(update_fields=['Activo'])
    messages.success(request, f'Servicio «{servicio.Tipo_servicio}» dado de baja. Se reactiva editándolo.')
    return redirect('servicios_lista')
```

En `pedidos/urls.py`, cambiar `from . import views` por `from . import views, views_servicios` y agregar al final de la lista:

```python
    path('servicios/', views_servicios.lista, name='servicios_lista'),
    path('servicios/nuevo/', views_servicios.crear, name='servicios_crear'),
    path('servicios/<int:id_servicio>/editar/', views_servicios.editar, name='servicios_editar'),
    path('servicios/<int:id_servicio>/baja/', views_servicios.baja, name='servicios_baja'),
```

- [ ] **Paso 5: Plantillas y enlaces**

`pedidos/templates/pedidos/servicios_lista.html`:

```html
{% extends 'vehiculos/base.html' %}
{% block title %}Servicios{% endblock %}
{% block content %}
<div class="d-flex justify-content-between align-items-center mb-4">
    <div>
        <h1 class="h3 fw-bold mb-1">Servicios</h1>
        <p class="text-muted mb-0">Lo que el cliente puede elegir al pedir una mudanza.</p>
    </div>
    <a href="{% url 'servicios_crear' %}" class="btn btn-success fw-bold"><i class="bi bi-plus-circle me-1"></i>Nuevo servicio</a>
</div>
<div class="card-panel bg-white p-0 overflow-auto">
    <table class="table align-middle mb-0">
        <thead class="table-light"><tr><th>Servicio</th><th class="text-end">Precio base</th><th>Materiales</th><th>Estado</th><th></th></tr></thead>
        <tbody>
            {% for s in servicios %}
            <tr class="{% if not s.Activo %}text-muted{% endif %}">
                <td class="fw-semibold">{{ s.Tipo_servicio }}</td>
                <td class="text-end">${{ s.Precio_base|floatformat:"2g" }}</td>
                <td class="small">{% for r in s.recursos.all %}{{ r.Materiales }}{% if not forloop.last %}, {% endif %}{% empty %}—{% endfor %}</td>
                <td>{% if s.Activo %}<span class="badge text-bg-success">Activo</span>{% else %}<span class="badge text-bg-secondary">Dado de baja</span>{% endif %}</td>
                <td class="text-end text-nowrap">
                    <a href="{% url 'servicios_editar' s.id_servicio %}" class="btn btn-sm btn-warning">Editar</a>
                    {% if s.Activo %}
                    <form method="post" action="{% url 'servicios_baja' s.id_servicio %}" class="d-inline"
                          onsubmit="return confirm('¿Dar de baja «{{ s.Tipo_servicio|escapejs }}»? Los pedidos que ya lo tienen no cambian.')">
                        {% csrf_token %}<button class="btn btn-sm btn-outline-danger">Dar de baja</button>
                    </form>
                    {% endif %}
                </td>
            </tr>
            {% endfor %}
        </tbody>
    </table>
</div>
{% endblock %}
```

`pedidos/templates/pedidos/servicio_form.html`:

```html
{% extends 'vehiculos/base.html' %}
{% block title %}{{ titulo }}{% endblock %}
{% block content %}
<div class="mx-auto" style="max-width: 640px;">
    <h1 class="h3 fw-bold mb-4">{{ titulo }}</h1>
    <form method="post" class="card-panel bg-white p-4" novalidate>
        {% csrf_token %}
        {% for field in form %}
        <div class="mb-3 {% if field.name == 'Activo' %}form-check{% endif %}">
            {% if field.name == 'Activo' %}
                {{ field }} <label class="form-check-label" for="{{ field.id_for_label }}">Activo (se ofrece al registrar pedidos)</label>
            {% else %}
                <label for="{{ field.id_for_label }}" class="form-label fw-semibold">{{ field.label }}</label>
                {{ field }}
                {% if field.help_text %}<div class="form-text">{{ field.help_text }}</div>{% endif %}
            {% endif %}
            {% if field.errors %}<div class="invalid-feedback d-block">{{ field.errors.as_text }}</div>{% endif %}
        </div>
        {% endfor %}
        <div class="d-flex justify-content-end gap-3">
            <a href="{% url 'servicios_lista' %}" class="btn btn-outline-secondary px-4">Cancelar</a>
            <button class="btn btn-success fw-bold px-4">Guardar</button>
        </div>
    </form>
</div>
{% endblock %}
```

En `vehiculos/templates/vehiculos/base.html`, dentro de `{% if rol == 'Administrador' %}`, después del enlace «Pedidos»:

```html
                <a href="{% url 'servicios_lista' %}" class="text-white-50 text-decoration-none">Servicios</a>
```

En `usuarios/templates/admin_dashboard.html`, en la línea del enlace `Flota de vehículos` (línea 22), insertar antes de `<span class="font-semibold text-white">Sesión:`:

```html
<a href="/pedidos/" class="text-xs font-semibold px-3 py-1.5 rounded-lg bg-[#252833] border border-gray-700 text-amber-gold hover:text-white hover:border-amber-gold transition mr-3"><i class="fa-solid fa-clipboard-list mr-1"></i> Pedidos</a><a href="/servicios/" class="text-xs font-semibold px-3 py-1.5 rounded-lg bg-[#252833] border border-gray-700 text-amber-gold hover:text-white hover:border-amber-gold transition mr-3"><i class="fa-solid fa-tags mr-1"></i> Servicios</a>
```

- [ ] **Paso 6: Correr las pruebas y verificar que pasan**

Correr: `docker exec mudanzas_web python manage.py test`
Esperado: `OK` en todas.

- [ ] **Paso 7: Commit**

```bash
git add pedidos/ vehiculos/templates/vehiculos/base.html usuarios/templates/admin_dashboard.html
git commit -m "Add the services master CRUD with logical deletion"
```

---

### Tarea 10: Script SQL, documentación y prueba completa

**Archivos:**
- Crear: `docs/sql/esquema_mudanzas.sql`
- Modificar: `README.md`, `C:\Users\gaboo\Downloads\CONTEXTO_PROYECTO_MUDANZAS.md` (fuera del repo, no se versiona)

- [ ] **Paso 1: Generar el script SQL**

Correr (en Git Bash, desde la raíz del repo):

```bash
mkdir -p docs/sql
{ echo "-- Esquema de Mudanzas y Fletes Salta (Hito 3). Generado desde las migraciones de Django."
  echo "-- MySQL 8. Base: mudanzas_db."
  for m in 0001 0002; do docker exec mudanzas_web python manage.py sqlmigrate usuarios $m; done
} > docs/sql/esquema_mudanzas.sql
grep -c "CREATE TABLE" docs/sql/esquema_mudanzas.sql
```

Esperado: `13`.

- [ ] **Paso 2: Actualizar el README**

En `README.md`:
- En la lista inicial, agregar después del Hito 2: `- **Hito 3** — proceso completo del pedido de mudanza: registro por el cliente, consulta con filtros, confirmación, anulación y comprobante; ABM de servicios (app \`pedidos\`).`
- En la tabla de direcciones, agregar las filas `/registro/` (Crear cuenta de cliente), `/pedidos/` (Pedidos: el cliente ve los suyos y el admin todos), `/pedidos/nuevo/` (Pedir una mudanza, solo clientes) y `/servicios/` (ABM de servicios, solo admin).
- En la tabla de usuarios de prueba, agregar `| \`gomezm\` | \`Cliente123!\` | Cliente | Sus pedidos; puede pedir mudanzas |`.
- Agregar una sección `## Reglas del Hito 3` con el resumen de las secciones 5 y 6 de la especificación: estados, vehículo libre, validaciones, anulación sin borrado y la tabla de permisos.
- En la estructura, agregar `├── pedidos/              # Hito 3: reglas.py, permisos.py, vistas y ABM de servicios` y `├── docs/sql/             # Script del esquema para la entrega`.

- [ ] **Paso 3: Prueba completa en el navegador**

Con los contenedores levantados, recorrer el proceso entero:
1. Entrar como `gomezm` y registrar un pedido para mañana con 2 servicios y 2 objetos.
2. Salir, entrar como `sarmientoc`, ir a Pedidos y filtrar por estado «Pendiente»; el pedido tiene que aparecer.
3. Confirmar el pedido, abrir el comprobante y usar «Imprimir / Guardar PDF».
4. Registrar otro pedido como `gomezm` y anularlo como `sarmientoc`, con un motivo.
5. Comprobar que el vehículo de ese pedido vuelve a aparecer libre para esa fecha.

Estas son las capturas de la entrega: registración, consulta, anulación y comprobante. Guardarlas en `Descargas\Capturas Hito3`.

- [ ] **Paso 4: Verificación final**

Correr:
```bash
docker exec mudanzas_web python manage.py test
docker exec mudanzas_web python manage.py makemigrations --check --dry-run
```
Esperado: `OK` en todas las pruebas y `No changes detected`.

- [ ] **Paso 5: Commit**

```bash
git add docs/sql/ README.md
git commit -m "Add the SQL schema script and document the Hito 3 order process"
```

- [ ] **Paso 6: Actualizar el archivo de contexto**

En `C:\Users\gaboo\Downloads\CONTEXTO_PROYECTO_MUDANZAS.md`, agregar en la sección 4 un apartado «Hito 3» con lo hecho (rama `hito3-pedidos`, las pantallas, la cantidad de pruebas y la clienta de prueba), y en «Pendientes» lo que queda: corregir el DFD «Registrar un Pedido», el documento de avance y las capturas.
