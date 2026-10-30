"""Modelo de datos según el DER de Mudanzas Salta.

Las tablas y columnas de la base se llaman exactamente como en el DER.
Los campos de control que exige el Hito 2 (usuario automático, cambio de clave
obligatorio, fecha de baja y de última modificación) se suman a USUARIOS.
"""
from django.db import models
from django.utils import timezone
import hashlib
from datetime import datetime, time, timedelta


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
        """Las claves se guardan con PBKDF2. Una clave vieja (SHA-256 sin sal) se acepta y, en
        ese mismo ingreso, se vuelve a guardar con PBKDF2: nadie tiene que cambiarla."""
        from django.contrib.auth.hashers import check_password, make_password
        plana = (clave_plana or '').strip()
        if '$' in self.Clave:  # formato de Django («algoritmo$vueltas$sal$hash»); el SHA-256 viejo no tiene «$»
            return check_password(plana, self.Clave)
        if self.Clave == hashlib.sha256(plana.encode('utf-8')).hexdigest():
            self.Clave = make_password(plana)
            # update() y no save(): es el mismo valor de clave, no un cambio para la auditoría
            Usuario.objects.filter(pk=self.pk).update(Clave=self.Clave)
            return True
        return False

    def set_clave(self, clave_plana):
        from django.contrib.auth.hashers import make_password
        self.Clave = make_password(clave_plana.strip())

    def registrar_acceso(self):
        self.FechaUltimoAcceso = timezone.now()
        self.save(update_fields=['FechaUltimoAcceso'])


class Vehiculo(models.Model):
    # Lista cerrada por tamaño: el tamaño ajusta el precio del servicio principal
    CHICO, MEDIANO, GRANDE = 'Camión Chico', 'Camión Mediano', 'Camión Grande'
    TIPOS = [CHICO, MEDIANO, GRANDE]
    RECARGOS = {CHICO: 0, MEDIANO: 25, GRANDE: 50}  # % sobre el precio del servicio principal

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
    tipo_vehiculo = models.CharField(max_length=50, choices=[(t, t) for t in TIPOS],
                                     verbose_name='Tipo de vehículo')
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

    @property
    def recargo(self):
        """Porcentaje que se suma al servicio principal por el tamaño del camión (0, 25 o 50)."""
        return self.RECARGOS.get(self.tipo_vehiculo, 0)


class Servicio(models.Model):
    # El pedido lleva un servicio principal (la mudanza o el flete) y, si quiere, adicionales.
    # El principal se cobra según el tamaño del camión; los adicionales, a su precio.
    PRINCIPAL, ADICIONAL = 'Principal', 'Adicional'
    CATEGORIAS = [(PRINCIPAL, 'Principal (mudanza o flete)'), (ADICIONAL, 'Adicional (embalaje, armado, etc.)')]

    id_servicio = models.AutoField(primary_key=True)
    Tipo_servicio = models.CharField(max_length=100, verbose_name='Tipo de servicio')
    Precio_base = models.DecimalField(max_digits=12, decimal_places=2, verbose_name='Precio base')
    Categoria = models.CharField(max_length=10, choices=CATEGORIAS, default=PRINCIPAL,
                                 db_column='Categoria', verbose_name='Categoría')
    # Cuánto ocupa el vehículo y el personal. Solo los principales; los adicionales no suman tiempo.
    Duracion_horas = models.PositiveSmallIntegerField(blank=True, null=True, db_column='Duracion_horas',
                                                      verbose_name='Duración estimada (horas)')
    Activo = models.BooleanField(default=True, db_column='Activo', verbose_name='Activo')

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
    hora_servicio = models.TimeField(default=time(9, 0), db_column='Hora_servicio', verbose_name='Hora de inicio')
    # Copia de la duración del servicio principal al pedir: si el servicio cambia, el pedido no
    duracion_horas = models.PositiveSmallIntegerField(default=5, db_column='Duracion_horas',
                                                      verbose_name='Duración estimada (horas)')
    origen =models.CharField(max_length=200, default='', db_column='Direccion_origen', verbose_name='Desde')
    destino = models.CharField(max_length=200, default='', db_column='Direccion_destino', verbose_name='Hasta')
    estado = models.CharField(max_length=20, choices=ESTADOS, default=PENDIENTE, db_column='Estado_pedido')
    total = models.DecimalField(max_digits=12, decimal_places=2, default=0, db_column='Total_pedido')
    # Lo carga el chofer en el relevamiento si encuentra más cosas de las declaradas; suma al total
    recargo = models.DecimalField(max_digits=12, decimal_places=2, default=0, db_column='Recargo_pedido',
                                  verbose_name='Recargo')
    motivo_recargo = models.CharField(max_length=200, blank=True, null=True, db_column='Motivo_recargo',
                                      verbose_name='Motivo del recargo')
    # Lo marca el chofer desde el portal («Empezamos» / «Terminamos»): la hora real, no la estimada
    inicio_real = models.DateTimeField(blank=True, null=True, db_column='Inicio_real', verbose_name='Inicio real')
    fin_real = models.DateTimeField(blank=True, null=True, db_column='Fin_real', verbose_name='Fin real')
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
    def inicio(self):
        """Fecha y hora en que empieza la mudanza (con zona horaria)."""
        return timezone.make_aware(datetime.combine(self.fecha_servicio, self.hora_servicio))

    @property
    def fin(self):
        """Hasta cuándo ocupa el vehículo y el personal (estimado)."""
        return self.inicio + timedelta(hours=self.duracion_horas)

    @property
    def fin_esperado(self):
        """El fin estimado, corrido si empezaron tarde: inicio real + duración."""
        if self.inicio_real:
            return max(self.fin, self.inicio_real + timedelta(hours=self.duracion_horas))
        return self.fin

    @property
    def en_curso(self):
        """El chofer marcó «Empezamos» y todavía no «Terminamos»."""
        return self.estado == self.CONFIRMADO and self.inicio_real is not None and self.fin_real is None

    @property
    def hasta(self):
        """El fin para mostrar al lado del inicio: solo la hora si termina el mismo día."""
        ini, fin = timezone.localtime(self.inicio), timezone.localtime(self.fin)
        return f'{fin:%H:%M}' if fin.date() == ini.date() else f'{fin:%d/%m} {fin:%H:%M}'

    @property
    def horario(self):
        """Ej.: «de 09:00 a 14:00 (aprox.)» o «desde las 08:00 hasta el 23/10 a las 08:00 (aprox.)»."""
        ini, fin = timezone.localtime(self.inicio), timezone.localtime(self.fin)
        if fin.date() == ini.date():
            return f'de {ini:%H:%M} a {fin:%H:%M} (aprox.)'
        return f'desde las {ini:%H:%M} hasta el {fin:%d/%m} a las {fin:%H:%M} (aprox.)'

    @property
    def ya_empezo(self):
        return timezone.now() >= self.inicio

    @property
    def chofer(self):
        """El chofer asignado a esta mudanza (o None)."""
        return next((x.idUsuario for x in self.personal.all() if x.Funcion == 'Chofer'), None)

    @property
    def para_finalizar(self):
        """Confirmado cuya mudanza ya empezó: falta marcarlo como finalizado."""
        return self.estado == self.CONFIRMADO and self.ya_empezo

    @property
    def vencido(self):
        """Pendiente con la fecha y hora ya pasadas: nadie lo confirmó a tiempo."""
        return self.estado == self.PENDIENTE and self.ya_empezo


class DetallePedido(models.Model):
    id_detalle_pedidos = models.AutoField(primary_key=True)
    idPedido = models.ForeignKey(Pedido, on_delete=models.CASCADE, db_column='id_pedido',
                                 related_name='detalles', verbose_name='Pedido')
    idServicio = models.ForeignKey(Servicio, on_delete=models.PROTECT, db_column='id_servicio',
                                   related_name='detalles', verbose_name='Servicio')
    precio_unitario = models.DecimalField(max_digits=12, decimal_places=2, default=0,
                                          db_column='Precio_unitario', verbose_name='Precio unitario')
    subtotal = models.DecimalField(max_digits=12, decimal_places=2, default=0, db_column='Subtotal')

    class Meta:
        db_table = 'DETALLE_PEDIDOS'
        ordering = ['id_detalle_pedidos']  # primero el principal, después los adicionales
        verbose_name = 'Detalle de pedido'
        verbose_name_plural = 'Detalles de pedidos'

    def __str__(self):
        return f'Pedido {self.idPedido_id} - {self.idServicio}'


class PersonalPedido(models.Model):
    """Quién hace cada mudanza: un chofer y, si hacen falta, ayudantes de carga."""
    CHOFER, AYUDANTE = 'Chofer', 'Ayudante'
    FUNCIONES = [(CHOFER, 'Chofer'), (AYUDANTE, 'Ayudante de carga')]

    id_personal_pedido = models.AutoField(primary_key=True)
    idPedido = models.ForeignKey('Pedido', on_delete=models.CASCADE, db_column='id_pedido',
                                 related_name='personal', verbose_name='Pedido')
    idUsuario = models.ForeignKey(Usuario, on_delete=models.PROTECT, db_column='id_usuario',
                                  related_name='asignaciones', verbose_name='Empleado')
    Funcion = models.CharField(max_length=10, choices=FUNCIONES, db_column='funcion_personal',
                               verbose_name='Función')

    class Meta:
        db_table = 'PERSONAL_PEDIDO'
        verbose_name = 'Personal del pedido'
        verbose_name_plural = 'Personal de los pedidos'
        ordering = ['-Funcion', 'id_personal_pedido']  # primero el chofer
        constraints = [models.UniqueConstraint(fields=['idPedido', 'idUsuario'], name='persona_una_vez_por_pedido')]

    def __str__(self):
        return f'Pedido {self.idPedido_id} - {self.Funcion}: {self.idUsuario}'


class Reprogramacion(models.Model):
    """Cada cambio de horario de un pedido: de cuándo a cuándo, por qué y quién lo hizo.
    El pedido guarda solo el horario vigente; acá queda el historial."""
    MOTIVOS = [(m, m) for m in ('Demora en una mudanza anterior', 'Problema técnico del vehículo', 'Clima',
                                'Pedido del cliente', 'Falta de personal', 'Otro')]

    id_reprogramacion = models.AutoField(primary_key=True)
    idPedido = models.ForeignKey(Pedido, on_delete=models.CASCADE, db_column='id_pedido',
                                 related_name='reprogramaciones', verbose_name='Pedido')
    fecha_anterior = models.DateField(db_column='Fecha_anterior')
    hora_anterior = models.TimeField(db_column='Hora_anterior')
    vehiculo_anterior = models.ForeignKey(Vehiculo, on_delete=models.PROTECT, db_column='patente_anterior',
                                          related_name='+', verbose_name='Vehículo anterior')
    fecha_nueva = models.DateField(db_column='Fecha_nueva')
    hora_nueva = models.TimeField(db_column='Hora_nueva')
    vehiculo_nuevo = models.ForeignKey(Vehiculo, on_delete=models.PROTECT, db_column='patente_nueva',
                                       related_name='+', verbose_name='Vehículo nuevo')
    motivo = models.CharField(max_length=40, choices=MOTIVOS, db_column='Motivo_reprog')
    observacion = models.CharField(max_length=200, blank=True, null=True, db_column='Observacion_reprog')
    usuario = models.ForeignKey(Usuario, on_delete=models.PROTECT, db_column='id_usuario',
                                related_name='reprogramaciones', verbose_name='Reprogramado por')
    fecha_registro = models.DateTimeField(default=timezone.now, db_column='Fec_reprog')
    visto_cliente = models.BooleanField(default=False, db_column='Visto_cliente')

    class Meta:
        db_table = 'REPROGRAMACIONES'
        verbose_name = 'Reprogramación'
        verbose_name_plural = 'Reprogramaciones'
        ordering = ['-fecha_registro', '-id_reprogramacion']  # la última primero

    def __str__(self):
        return f'Pedido {self.idPedido_id}: {self.fecha_anterior} → {self.fecha_nueva}'

    @property
    def motivo_completo(self):
        """«Clima» o, para «Otro», lo que se escribió."""
        if self.motivo == 'Otro':
            return self.observacion or 'Otro'
        return f'{self.motivo} ({self.observacion})' if self.observacion else self.motivo


class Objeto(models.Model):
    """Catálogo de objetos que se pueden mudar. El inventario elige de acá en vez de escribir
    el nombre, así no se llena de variantes («mesa», «meza», «Mesa»). Lo que no está en la
    lista se carga como «Otro», con la observación obligatoria."""
    OTRO = 'Otro'

    id_objeto = models.AutoField(primary_key=True)
    nom_objeto = models.CharField(max_length=100, unique=True, db_column='nom_objeto', verbose_name='Objeto')
    Activo = models.BooleanField(default=True, db_column='estado_objeto', verbose_name='Activo')

    class Meta:
        db_table = 'OBJETOS'
        verbose_name = 'Objeto'
        verbose_name_plural = 'Objetos'
        ordering = ['nom_objeto']

    def __str__(self):
        return self.nom_objeto

    @property
    def es_otro(self):
        return self.nom_objeto == self.OTRO


class InventarioDetalle(models.Model):
    id_inventario = models.AutoField(primary_key=True)
    idObjeto = models.ForeignKey(Objeto, on_delete=models.PROTECT, db_column='id_objeto',
                                 related_name='inventarios', verbose_name='Objeto')
    Cantidad = models.IntegerField()
    # Lo que había declarado el cliente, si el chofer lo corrigió en el relevamiento (0 = no lo declaró)
    cantidad_declarada = models.PositiveIntegerField(blank=True, null=True, db_column='Cantidad_declarada',
                                                     verbose_name='Cantidad declarada')
    Fragil = models.BooleanField(default=False, verbose_name='Frágil')
    Observacion = models.CharField(max_length=200, blank=True, null=True, verbose_name='Observación')
    idPedido = models.ForeignKey(Pedido, on_delete=models.CASCADE, db_column='id_pedido',
                                 related_name='inventario', verbose_name='Pedido')

    class Meta:
        db_table = 'INVENTARIO_DETALLES'
        verbose_name = 'Detalle de inventario'
        verbose_name_plural = 'Detalles de inventario'

    def __str__(self):
        return f'{self.Cantidad} x {self.idObjeto}'


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


class LogAuditoria(models.Model):
    """Cada modificación, anulación, baja o borrado de cualquier tabla: qué registro, qué valores
    tenía antes y cuáles después, cuándo y quién. Lo llena solo usuarios/auditoria.py."""
    MODIFICACION, ANULACION, BAJA, REACTIVACION, ELIMINACION = (
        'Modificación', 'Anulación', 'Baja', 'Reactivación', 'Eliminación')
    ACCIONES = [(a, a) for a in (MODIFICACION, ANULACION, BAJA, REACTIVACION, ELIMINACION)]

    id_log = models.AutoField(primary_key=True)
    tabla = models.CharField(max_length=60, db_column='tabla_log', verbose_name='Tabla')
    id_registro = models.CharField(max_length=60, db_column='id_registro_log', verbose_name='Registro')
    accion = models.CharField(max_length=20, choices=ACCIONES, db_column='accion_log', verbose_name='Acción')
    valores_anteriores = models.TextField(db_column='valores_anteriores_log', verbose_name='Valores anteriores')
    valores_nuevos = models.TextField(blank=True, default='', db_column='valores_nuevos_log',
                                      verbose_name='Valores nuevos')
    fecha_hora = models.DateTimeField(default=timezone.now, db_column='fec_hora_log', verbose_name='Fecha y hora')
    usuario = models.ForeignKey(Usuario, on_delete=models.SET_NULL, blank=True, null=True, db_column='id_usuario',
                                related_name='auditoria', verbose_name='Usuario')

    class Meta:
        db_table = 'LOG_AUDITORIA'
        verbose_name = 'Registro de auditoría'
        verbose_name_plural = 'Log de auditoría'
        ordering = ['-fecha_hora', '-id_log']

    def __str__(self):
        return f'{self.fecha_hora:%d/%m/%Y %H:%M} {self.accion} {self.tabla} {self.id_registro}'
