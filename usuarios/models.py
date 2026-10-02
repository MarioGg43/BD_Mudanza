"""Modelo de datos según el DER de Mudanzas Salta.

Las tablas y columnas de la base se llaman exactamente como en el DER.
Los campos de control que exige el Hito 2 (usuario automático, cambio de clave
obligatorio, fecha de baja y de última modificación) se suman a USUARIOS.
"""
from django.db import models
from django.utils import timezone
import hashlib


class Permiso(models.Model):
    id_permiso = models.AutoField(primary_key=True)
    nom_permiso = models.CharField(max_length=100, unique=True, verbose_name='Nombre del permiso')
    desc_permiso = models.CharField(max_length=100, blank=True, null=True, verbose_name='Descripción')

    class Meta:
        db_table = 'PERMISOS'
        verbose_name = 'Permiso'
        verbose_name_plural = 'Permisos'

    def __str__(self):
        return self.nom_permiso


class Rol(models.Model):
    id_rol = models.AutoField(primary_key=True)
    nom_rol = models.CharField(max_length=100, unique=True, verbose_name='Nombre del rol')
    desc_rol = models.CharField(max_length=100, blank=True, null=True, verbose_name='Descripción')
    permisos = models.ManyToManyField(Permiso, through='PermisoRol', related_name='roles')

    class Meta:
        db_table = 'ROLES'
        verbose_name = 'Rol'
        verbose_name_plural = 'Roles'

    def __str__(self):
        return self.nom_rol


class PermisoRol(models.Model):
    id_permiso_rol = models.AutoField(primary_key=True)
    idRol = models.ForeignKey(Rol, on_delete=models.CASCADE, db_column='id_rol', verbose_name='Rol')
    idPermiso = models.ForeignKey(Permiso, on_delete=models.CASCADE, db_column='id_permiso', verbose_name='Permiso')

    class Meta:
        db_table = 'PERMISOS_ROLES'
        unique_together = (('idRol', 'idPermiso'),)
        verbose_name = 'Permiso por rol'
        verbose_name_plural = 'Permisos por rol'

    def __str__(self):
        return f'{self.idRol} - {self.idPermiso}'


class Sueldo(models.Model):
    id_sueldo = models.AutoField(primary_key=True, db_column='id_Sueldos')
    Monto = models.DecimalField(max_digits=12, decimal_places=2)
    Fecha_pago = models.DateField(verbose_name='Fecha de pago')

    class Meta:
        db_table = 'SUELDOS'
        verbose_name = 'Sueldo'
        verbose_name_plural = 'Sueldos'

    def __str__(self):
        return f'${self.Monto} - {self.Fecha_pago}'


class Usuario(models.Model):
    id_usuario = models.AutoField(primary_key=True)
    idRol = models.ForeignKey(Rol, on_delete=models.PROTECT, db_column='id_rol',
                              related_name='usuarios', verbose_name='Rol')
    DNI = models.BigIntegerField(unique=True, db_column='Dni_usuario', verbose_name='DNI')
    Nombre = models.CharField(max_length=100, db_column='Nombre_usuario')
    Apellido = models.CharField(max_length=100, db_column='Apellido_usuario')
    Correo = models.EmailField(max_length=150, unique=True, db_column='Correo_usuario')
    Clave = models.CharField(max_length=255, db_column='contrasena_usuario',
                             verbose_name='Clave (hash SHA-256)')
    Telefono = models.CharField(max_length=30, blank=True, null=True, db_column='Telefono_usuario')
    Activo = models.BooleanField(default=True, db_column='Estado_usuario', verbose_name='Activo (si/no)')
    FechaUltimoAcceso = models.DateTimeField(blank=True, null=True, db_column='fec_ult_acc_usuario',
                                             verbose_name='Último acceso')
    idSueldo = models.ForeignKey(Sueldo, on_delete=models.SET_NULL, blank=True, null=True,
                                 db_column='id_sueldo', related_name='usuarios', verbose_name='Sueldo')

    # --- campos de control que exige el Hito 2 ---
    NombreUsuario = models.CharField(max_length=100, unique=True, db_column='usuario_login',
                                     verbose_name='Usuario (automático)')
    DebeCambiarClave = models.BooleanField(default=True, db_column='debe_cambiar_clave',
                                           verbose_name='Debe cambiar la clave')
    FechaUltimaModificacion = models.DateTimeField(auto_now=True, db_column='fec_ult_mod_usuario',
                                                   verbose_name='Última modificación')
    FechaBaja = models.DateTimeField(blank=True, null=True, db_column='fec_baja_usuario',
                                     verbose_name='Fecha de baja')

    class Meta:
        db_table = 'USUARIOS'
        verbose_name = 'Usuario'
        verbose_name_plural = 'Usuarios'

    def __str__(self):
        return f'{self.Apellido}, {self.Nombre} ({self.NombreUsuario})'

    def verificar_clave(self, clave_plana):
        return self.Clave == hashlib.sha256(clave_plana.strip().encode('utf-8')).hexdigest()

    def set_clave(self, clave_plana):
        self.Clave = hashlib.sha256(clave_plana.strip().encode('utf-8')).hexdigest()

    def registrar_acceso(self):
        self.FechaUltimoAcceso = timezone.now()
        self.save(update_fields=['FechaUltimoAcceso'])


class Vehiculo(models.Model):
    patente = models.CharField(max_length=15, primary_key=True, db_column='Patente',
                               verbose_name='Patente')
    marca_modelo = models.CharField(max_length=100, db_column='Marca_Modelo_vehiculo',
                                    verbose_name='Marca y modelo')
    capacidad_kg = models.DecimalField(max_digits=10, decimal_places=2, db_column='Capacidad_kg_vehiculo',
                                       verbose_name='Capacidad (kg)')
    capacidad_m3 = models.DecimalField(max_digits=10, decimal_places=2, db_column='Capacidad_m3_vehiculo',
                                       verbose_name='Capacidad (m3)')
    estado = models.CharField(
        max_length=30, default='Disponible', db_column='Estado_vehiculo',
        choices=[
            ('Disponible', 'Disponible'),
            ('En Viaje', 'En Viaje'),
            ('En Mantenimiento', 'En Mantenimiento'),
            ('Fuera de Servicio', 'Fuera de Servicio'),
        ],
        verbose_name='Estado operativo')
    kilometraje = models.DecimalField(max_digits=10, decimal_places=2, default=0,
                                      db_column='Kilometraje_vehiculo')
    anio = models.IntegerField(blank=True, null=True, db_column='Anio_vehiculo', verbose_name='Año')

    # --- datos operativos que ya usaba el CRUD del Hito 1 ---
    tipo_vehiculo = models.CharField(max_length=50, verbose_name='Tipo de vehículo')
    chofer_asignado = models.ForeignKey(Usuario, on_delete=models.SET_NULL, blank=True, null=True,
                                        related_name='vehiculos_asignados', verbose_name='Chofer asignado')
    observaciones = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Fecha de registro')

    class Meta:
        db_table = 'VEHICULOS'
        verbose_name = 'Vehículo'
        verbose_name_plural = 'Vehículos'

    def __str__(self):
        return f'{self.patente} - {self.marca_modelo} ({self.estado})'


class Servicio(models.Model):
    id_servicio = models.AutoField(primary_key=True)
    Tipo_servicio = models.CharField(max_length=100, verbose_name='Tipo de servicio')
    Precio_base = models.DecimalField(max_digits=12, decimal_places=2, verbose_name='Precio base')

    class Meta:
        db_table = 'SERVICIOS'
        verbose_name = 'Servicio'
        verbose_name_plural = 'Servicios'

    def __str__(self):
        return self.Tipo_servicio


class RecursoAsignado(models.Model):
    id_recursos_asignados = models.AutoField(primary_key=True)
    idServicio = models.ForeignKey(Servicio, on_delete=models.CASCADE, db_column='id_servicios',
                                   related_name='recursos', verbose_name='Servicio')
    Materiales = models.CharField(max_length=50)

    class Meta:
        db_table = 'RECURSOS_ASIGNADOS'
        verbose_name = 'Recurso asignado'
        verbose_name_plural = 'Recursos asignados'

    def __str__(self):
        return f'{self.idServicio} - {self.Materiales}'


class Pedido(models.Model):
    id_pedido = models.AutoField(primary_key=True)
    patente_vehiculo = models.ForeignKey(Vehiculo, on_delete=models.PROTECT, db_column='patente_vehiculos',
                                         related_name='pedidos', verbose_name='Vehículo')
    idUsuario = models.ForeignKey(Usuario, on_delete=models.PROTECT, db_column='id_usuario',
                                  related_name='pedidos', verbose_name='Usuario')
    Fecha_pedido = models.DateField(verbose_name='Fecha del pedido')

    class Meta:
        db_table = 'PEDIDOS'
        verbose_name = 'Pedido'
        verbose_name_plural = 'Pedidos'

    def __str__(self):
        return f'Pedido {self.id_pedido} - {self.Fecha_pedido}'


class DetallePedido(models.Model):
    id_detalle_pedidos = models.AutoField(primary_key=True)
    idPedido = models.ForeignKey(Pedido, on_delete=models.CASCADE, db_column='id_pedido',
                                 related_name='detalles', verbose_name='Pedido')
    idServicio = models.ForeignKey(Servicio, on_delete=models.PROTECT, db_column='id_servicio',
                                   related_name='detalles', verbose_name='Servicio')

    class Meta:
        db_table = 'DETALLE_PEDIDOS'
        verbose_name = 'Detalle de pedido'
        verbose_name_plural = 'Detalles de pedidos'

    def __str__(self):
        return f'Pedido {self.idPedido_id} - {self.idServicio}'


class InventarioDetalle(models.Model):
    id_inventario = models.AutoField(primary_key=True)
    Peso = models.DecimalField(max_digits=10, decimal_places=2)
    Cantidad = models.IntegerField()
    Fragil = models.BooleanField(default=False, verbose_name='Frágil')
    idPedido = models.ForeignKey(Pedido, on_delete=models.CASCADE, db_column='id_pedido',
                                 related_name='inventario', verbose_name='Pedido')

    class Meta:
        db_table = 'INVENTARIO_DETALLES'
        verbose_name = 'Detalle de inventario'
        verbose_name_plural = 'Detalles de inventario'

    def __str__(self):
        return f'{self.Cantidad} bultos - {self.Peso} kg'


class Cobranza(models.Model):
    id_cobranza = models.AutoField(primary_key=True)
    Monto_cob = models.DecimalField(max_digits=12, decimal_places=2, verbose_name='Monto')
    Met_pag_cob = models.CharField(max_length=100, verbose_name='Método de pago')

    class Meta:
        db_table = 'COBRANZAS'
        verbose_name = 'Cobranza'
        verbose_name_plural = 'Cobranzas'

    def __str__(self):
        return f'${self.Monto_cob} ({self.Met_pag_cob})'


class DetalleCobranza(models.Model):
    id_det_cob = models.AutoField(primary_key=True)
    idPedido = models.ForeignKey(Pedido, on_delete=models.CASCADE, db_column='id_ped',
                                 related_name='cobranzas', verbose_name='Pedido')
    idCobranza = models.ForeignKey(Cobranza, on_delete=models.CASCADE, db_column='id_cob',
                                   related_name='detalles', verbose_name='Cobranza')

    class Meta:
        db_table = 'DETALLE_COBRANZAS'
        verbose_name = 'Detalle de cobranza'
        verbose_name_plural = 'Detalles de cobranzas'

    def __str__(self):
        return f'Pedido {self.idPedido_id} - Cobranza {self.idCobranza_id}'
