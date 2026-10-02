from django.contrib import admin
from .models import (
    Permiso, Rol, PermisoRol, Sueldo, Usuario, Vehiculo, Servicio,
    RecursoAsignado, Pedido, DetallePedido, InventarioDetalle,
    Cobranza, DetalleCobranza,
)


@admin.register(Rol)
class RolAdmin(admin.ModelAdmin):
    list_display = ('id_rol', 'nom_rol', 'desc_rol')
    search_fields = ('nom_rol',)


@admin.register(Permiso)
class PermisoAdmin(admin.ModelAdmin):
    list_display = ('id_permiso', 'nom_permiso', 'desc_permiso')
    search_fields = ('nom_permiso',)


@admin.register(PermisoRol)
class PermisoRolAdmin(admin.ModelAdmin):
    list_display = ('id_permiso_rol', 'idRol', 'idPermiso')
    list_filter = ('idRol',)


@admin.register(Usuario)
class UsuarioAdmin(admin.ModelAdmin):
    list_display = ('DNI', 'Apellido', 'Nombre', 'NombreUsuario', 'Correo',
                    'idRol', 'Activo', 'DebeCambiarClave')
    list_filter = ('idRol', 'Activo', 'DebeCambiarClave')
    search_fields = ('DNI', 'Apellido', 'Nombre', 'NombreUsuario', 'Correo')
    # la clave se guarda como hash SHA-256: se muestra, pero no se edita a mano
    readonly_fields = ('Clave', 'FechaUltimaModificacion', 'FechaUltimoAcceso')


@admin.register(Vehiculo)
class VehiculoAdmin(admin.ModelAdmin):
    list_display = ('patente', 'marca_modelo', 'tipo_vehiculo', 'estado',
                    'capacidad_kg', 'capacidad_m3', 'chofer_asignado')
    list_filter = ('estado', 'tipo_vehiculo')
    search_fields = ('patente', 'marca_modelo')
    readonly_fields = ('created_at',)


@admin.register(Servicio)
class ServicioAdmin(admin.ModelAdmin):
    list_display = ('id_servicio', 'Tipo_servicio', 'Precio_base')


@admin.register(Pedido)
class PedidoAdmin(admin.ModelAdmin):
    list_display = ('id_pedido', 'Fecha_pedido', 'patente_vehiculo', 'idUsuario')
    list_filter = ('Fecha_pedido',)


admin.site.register([Sueldo, RecursoAsignado, DetallePedido,
                     InventarioDetalle, Cobranza, DetalleCobranza])
