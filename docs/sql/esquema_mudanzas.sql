-- Esquema de Mudanzas y Fletes Salta (Hito 3). Generado desde las migraciones de Django.
-- MySQL 8. Base: mudanzas_db.
--
-- Create model Cobranza
--
CREATE TABLE `COBRANZAS` (`id_cobranza` integer AUTO_INCREMENT NOT NULL PRIMARY KEY, `Monto_cob` numeric(12, 2) NOT NULL, `Met_pag_cob` varchar(100) NOT NULL);
--
-- Create model Pedido
--
CREATE TABLE `PEDIDOS` (`id_pedido` integer AUTO_INCREMENT NOT NULL PRIMARY KEY, `Fecha_pedido` date NOT NULL);
--
-- Create model Permiso
--
CREATE TABLE `PERMISOS` (`id_permiso` integer AUTO_INCREMENT NOT NULL PRIMARY KEY, `nom_permiso` varchar(100) NOT NULL UNIQUE, `desc_permiso` varchar(100) NULL);
--
-- Create model Servicio
--
CREATE TABLE `SERVICIOS` (`id_servicio` integer AUTO_INCREMENT NOT NULL PRIMARY KEY, `Tipo_servicio` varchar(100) NOT NULL, `Precio_base` numeric(12, 2) NOT NULL);
--
-- Create model Sueldo
--
CREATE TABLE `SUELDOS` (`id_Sueldos` integer AUTO_INCREMENT NOT NULL PRIMARY KEY, `Monto` numeric(12, 2) NOT NULL, `Fecha_pago` date NOT NULL);
--
-- Create model InventarioDetalle
--
CREATE TABLE `INVENTARIO_DETALLES` (`id_inventario` integer AUTO_INCREMENT NOT NULL PRIMARY KEY, `Peso` numeric(10, 2) NOT NULL, `Cantidad` integer NOT NULL, `Fragil` bool NOT NULL, `id_pedido` integer NOT NULL);
--
-- Create model DetalleCobranza
--
CREATE TABLE `DETALLE_COBRANZAS` (`id_det_cob` integer AUTO_INCREMENT NOT NULL PRIMARY KEY, `id_cob` integer NOT NULL, `id_ped` integer NOT NULL);
--
-- Create model PermisoRol
--
CREATE TABLE `PERMISOS_ROLES` (`id_permiso_rol` integer AUTO_INCREMENT NOT NULL PRIMARY KEY, `id_permiso` integer NOT NULL);
--
-- Create model Rol
--
CREATE TABLE `ROLES` (`id_rol` integer AUTO_INCREMENT NOT NULL PRIMARY KEY, `nom_rol` varchar(100) NOT NULL UNIQUE, `desc_rol` varchar(100) NULL);
--
-- Add field idRol to permisorol
--
ALTER TABLE `PERMISOS_ROLES` ADD COLUMN `id_rol` integer NOT NULL , ADD CONSTRAINT `PERMISOS_ROLES_id_rol_29bcd9af_fk_ROLES_id_rol` FOREIGN KEY (`id_rol`) REFERENCES `ROLES`(`id_rol`);
--
-- Create model RecursoAsignado
--
CREATE TABLE `RECURSOS_ASIGNADOS` (`id_recursos_asignados` integer AUTO_INCREMENT NOT NULL PRIMARY KEY, `Materiales` varchar(50) NOT NULL, `id_servicios` integer NOT NULL);
--
-- Create model DetallePedido
--
CREATE TABLE `DETALLE_PEDIDOS` (`id_detalle_pedidos` integer AUTO_INCREMENT NOT NULL PRIMARY KEY, `id_pedido` integer NOT NULL, `id_servicio` integer NOT NULL);
--
-- Create model Usuario
--
CREATE TABLE `USUARIOS` (`id_usuario` integer AUTO_INCREMENT NOT NULL PRIMARY KEY, `Dni_usuario` bigint NOT NULL UNIQUE, `Nombre_usuario` varchar(100) NOT NULL, `Apellido_usuario` varchar(100) NOT NULL, `Correo_usuario` varchar(150) NOT NULL UNIQUE, `contrasena_usuario` varchar(255) NOT NULL, `Telefono_usuario` varchar(30) NULL, `Estado_usuario` bool NOT NULL, `fec_ult_acc_usuario` datetime(6) NULL, `usuario_login` varchar(100) NOT NULL UNIQUE, `debe_cambiar_clave` bool NOT NULL, `fec_ult_mod_usuario` datetime(6) NOT NULL, `fec_baja_usuario` datetime(6) NULL, `id_rol` integer NOT NULL, `id_sueldo` integer NULL);
--
-- Add field idUsuario to pedido
--
ALTER TABLE `PEDIDOS` ADD COLUMN `id_usuario` integer NOT NULL , ADD CONSTRAINT `PEDIDOS_id_usuario_645b5187_fk_USUARIOS_id_usuario` FOREIGN KEY (`id_usuario`) REFERENCES `USUARIOS`(`id_usuario`);
--
-- Create model Vehiculo
--
CREATE TABLE `VEHICULOS` (`Patente` varchar(15) NOT NULL PRIMARY KEY, `Marca_Modelo_vehiculo` varchar(100) NOT NULL, `Capacidad_kg_vehiculo` numeric(10, 2) NOT NULL, `Capacidad_m3_vehiculo` numeric(10, 2) NOT NULL, `Estado_vehiculo` varchar(30) NOT NULL, `Kilometraje_vehiculo` numeric(10, 2) NOT NULL, `Anio_vehiculo` integer NULL, `tipo_vehiculo` varchar(50) NOT NULL, `observaciones` longtext NULL, `created_at` datetime(6) NOT NULL, `chofer_asignado_id` integer NULL);
--
-- Add field patente_vehiculo to pedido
--
ALTER TABLE `PEDIDOS` ADD COLUMN `patente_vehiculos` varchar(15) NOT NULL , ADD CONSTRAINT `PEDIDOS_patente_vehiculos_2a5d10a3_fk_VEHICULOS_Patente` FOREIGN KEY (`patente_vehiculos`) REFERENCES `VEHICULOS`(`Patente`);
--
-- Alter unique_together for permisorol (1 constraint(s))
--
ALTER TABLE `PERMISOS_ROLES` ADD CONSTRAINT `PERMISOS_ROLES_id_rol_id_permiso_ae137dbf_uniq` UNIQUE (`id_rol`, `id_permiso`);
ALTER TABLE `INVENTARIO_DETALLES` ADD CONSTRAINT `INVENTARIO_DETALLES_id_pedido_00beccb2_fk_PEDIDOS_id_pedido` FOREIGN KEY (`id_pedido`) REFERENCES `PEDIDOS` (`id_pedido`);
ALTER TABLE `DETALLE_COBRANZAS` ADD CONSTRAINT `DETALLE_COBRANZAS_id_cob_eb8fff82_fk_COBRANZAS_id_cobranza` FOREIGN KEY (`id_cob`) REFERENCES `COBRANZAS` (`id_cobranza`);
ALTER TABLE `DETALLE_COBRANZAS` ADD CONSTRAINT `DETALLE_COBRANZAS_id_ped_173d7ae6_fk_PEDIDOS_id_pedido` FOREIGN KEY (`id_ped`) REFERENCES `PEDIDOS` (`id_pedido`);
ALTER TABLE `PERMISOS_ROLES` ADD CONSTRAINT `PERMISOS_ROLES_id_permiso_d10c49ce_fk_PERMISOS_id_permiso` FOREIGN KEY (`id_permiso`) REFERENCES `PERMISOS` (`id_permiso`);
ALTER TABLE `RECURSOS_ASIGNADOS` ADD CONSTRAINT `RECURSOS_ASIGNADOS_id_servicios_b53d9e2e_fk_SERVICIOS` FOREIGN KEY (`id_servicios`) REFERENCES `SERVICIOS` (`id_servicio`);
ALTER TABLE `DETALLE_PEDIDOS` ADD CONSTRAINT `DETALLE_PEDIDOS_id_pedido_4c0d8603_fk_PEDIDOS_id_pedido` FOREIGN KEY (`id_pedido`) REFERENCES `PEDIDOS` (`id_pedido`);
ALTER TABLE `DETALLE_PEDIDOS` ADD CONSTRAINT `DETALLE_PEDIDOS_id_servicio_f3b4a64c_fk_SERVICIOS_id_servicio` FOREIGN KEY (`id_servicio`) REFERENCES `SERVICIOS` (`id_servicio`);
ALTER TABLE `USUARIOS` ADD CONSTRAINT `USUARIOS_id_rol_c26d371d_fk_ROLES_id_rol` FOREIGN KEY (`id_rol`) REFERENCES `ROLES` (`id_rol`);
ALTER TABLE `USUARIOS` ADD CONSTRAINT `USUARIOS_id_sueldo_772f8916_fk_SUELDOS_id_Sueldos` FOREIGN KEY (`id_sueldo`) REFERENCES `SUELDOS` (`id_Sueldos`);
ALTER TABLE `VEHICULOS` ADD CONSTRAINT `VEHICULOS_chofer_asignado_id_91d6b016_fk_USUARIOS_id_usuario` FOREIGN KEY (`chofer_asignado_id`) REFERENCES `USUARIOS` (`id_usuario`);
--
-- Add field precio_unitario to detallepedido
--
ALTER TABLE `DETALLE_PEDIDOS` ADD COLUMN `Precio_unitario` numeric(12, 2) DEFAULT 0 NOT NULL;
ALTER TABLE `DETALLE_PEDIDOS` ALTER COLUMN `Precio_unitario` DROP DEFAULT;
--
-- Add field subtotal to detallepedido
--
ALTER TABLE `DETALLE_PEDIDOS` ADD COLUMN `Subtotal` numeric(12, 2) DEFAULT 0 NOT NULL;
ALTER TABLE `DETALLE_PEDIDOS` ALTER COLUMN `Subtotal` DROP DEFAULT;
--
-- Add field Descripcion to inventariodetalle
--
ALTER TABLE `INVENTARIO_DETALLES` ADD COLUMN `Descripcion` varchar(100) DEFAULT '' NOT NULL;
ALTER TABLE `INVENTARIO_DETALLES` ALTER COLUMN `Descripcion` DROP DEFAULT;
--
-- Add field destino to pedido
--
ALTER TABLE `PEDIDOS` ADD COLUMN `Direccion_destino` varchar(200) DEFAULT '' NOT NULL;
ALTER TABLE `PEDIDOS` ALTER COLUMN `Direccion_destino` DROP DEFAULT;
--
-- Add field estado to pedido
--
ALTER TABLE `PEDIDOS` ADD COLUMN `Estado_pedido` varchar(20) DEFAULT 'Pendiente' NOT NULL;
ALTER TABLE `PEDIDOS` ALTER COLUMN `Estado_pedido` DROP DEFAULT;
--
-- Add field fecha_anulacion to pedido
--
ALTER TABLE `PEDIDOS` ADD COLUMN `Fec_anulacion` datetime(6) NULL;
--
-- Add field fecha_servicio to pedido
--
ALTER TABLE `PEDIDOS` ADD COLUMN `Fecha_servicio` date DEFAULT '2026-10-05' NOT NULL;
ALTER TABLE `PEDIDOS` ALTER COLUMN `Fecha_servicio` DROP DEFAULT;
--
-- Add field motivo_anulacion to pedido
--
ALTER TABLE `PEDIDOS` ADD COLUMN `Motivo_anulacion` varchar(200) NULL;
--
-- Add field origen to pedido
--
ALTER TABLE `PEDIDOS` ADD COLUMN `Direccion_origen` varchar(200) DEFAULT '' NOT NULL;
ALTER TABLE `PEDIDOS` ALTER COLUMN `Direccion_origen` DROP DEFAULT;
--
-- Add field total to pedido
--
ALTER TABLE `PEDIDOS` ADD COLUMN `Total_pedido` numeric(12, 2) DEFAULT 0 NOT NULL;
ALTER TABLE `PEDIDOS` ALTER COLUMN `Total_pedido` DROP DEFAULT;
--
-- Add field usuario_anulacion to pedido
--
ALTER TABLE `PEDIDOS` ADD COLUMN `id_usuario_anulacion` integer NULL , ADD CONSTRAINT `PEDIDOS_id_usuario_anulacion_cda902b9_fk_USUARIOS_id_usuario` FOREIGN KEY (`id_usuario_anulacion`) REFERENCES `USUARIOS`(`id_usuario`);
--
-- Add field Activo to servicio
--
ALTER TABLE `SERVICIOS` ADD COLUMN `Activo` bool DEFAULT 1 NOT NULL;
ALTER TABLE `SERVICIOS` ALTER COLUMN `Activo` DROP DEFAULT;
