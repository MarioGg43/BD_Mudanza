-- Mudanzas y Fletes Salta (Grupo 5) - Estructura de la base MySQL (mudanzas_db)
-- Generado desde la base con las migraciones hasta la 0014 (28/10/2026).
-- Tablas del negocio en MAYUSCULAS; las django_* y auth_* son del framework.


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!50503 SET NAMES utf8mb4 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `COBRANZAS` (
  `id_cobranza` int NOT NULL AUTO_INCREMENT,
  `Monto_cob` decimal(12,2) NOT NULL,
  `Met_pag_cob` varchar(100) NOT NULL,
  PRIMARY KEY (`id_cobranza`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `DETALLE_COBRANZAS` (
  `id_det_cob` int NOT NULL AUTO_INCREMENT,
  `id_cob` int NOT NULL,
  `id_ped` int NOT NULL,
  PRIMARY KEY (`id_det_cob`),
  KEY `DETALLE_COBRANZAS_id_cob_eb8fff82_fk_COBRANZAS_id_cobranza` (`id_cob`),
  KEY `DETALLE_COBRANZAS_id_ped_173d7ae6_fk_PEDIDOS_id_pedido` (`id_ped`),
  CONSTRAINT `DETALLE_COBRANZAS_id_cob_eb8fff82_fk_COBRANZAS_id_cobranza` FOREIGN KEY (`id_cob`) REFERENCES `COBRANZAS` (`id_cobranza`),
  CONSTRAINT `DETALLE_COBRANZAS_id_ped_173d7ae6_fk_PEDIDOS_id_pedido` FOREIGN KEY (`id_ped`) REFERENCES `PEDIDOS` (`id_pedido`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `DETALLE_PEDIDOS` (
  `id_detalle_pedidos` int NOT NULL AUTO_INCREMENT,
  `id_pedido` int NOT NULL,
  `id_servicio` int NOT NULL,
  `Precio_unitario` decimal(12,2) NOT NULL,
  `Subtotal` decimal(12,2) NOT NULL,
  PRIMARY KEY (`id_detalle_pedidos`),
  KEY `DETALLE_PEDIDOS_id_pedido_4c0d8603_fk_PEDIDOS_id_pedido` (`id_pedido`),
  KEY `DETALLE_PEDIDOS_id_servicio_f3b4a64c_fk_SERVICIOS_id_servicio` (`id_servicio`),
  CONSTRAINT `DETALLE_PEDIDOS_id_pedido_4c0d8603_fk_PEDIDOS_id_pedido` FOREIGN KEY (`id_pedido`) REFERENCES `PEDIDOS` (`id_pedido`),
  CONSTRAINT `DETALLE_PEDIDOS_id_servicio_f3b4a64c_fk_SERVICIOS_id_servicio` FOREIGN KEY (`id_servicio`) REFERENCES `SERVICIOS` (`id_servicio`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `INVENTARIO_DETALLES` (
  `id_inventario` int NOT NULL AUTO_INCREMENT,
  `Cantidad` int NOT NULL,
  `Fragil` tinyint(1) NOT NULL,
  `id_pedido` int NOT NULL,
  `Observacion` varchar(200) DEFAULT NULL,
  `id_objeto` int NOT NULL,
  PRIMARY KEY (`id_inventario`),
  KEY `INVENTARIO_DETALLES_id_pedido_00beccb2_fk_PEDIDOS_id_pedido` (`id_pedido`),
  KEY `INVENTARIO_DETALLES_id_objeto_8e0e531a_fk_OBJETOS_id_objeto` (`id_objeto`),
  CONSTRAINT `INVENTARIO_DETALLES_id_objeto_8e0e531a_fk_OBJETOS_id_objeto` FOREIGN KEY (`id_objeto`) REFERENCES `OBJETOS` (`id_objeto`),
  CONSTRAINT `INVENTARIO_DETALLES_id_pedido_00beccb2_fk_PEDIDOS_id_pedido` FOREIGN KEY (`id_pedido`) REFERENCES `PEDIDOS` (`id_pedido`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `LOG_AUDITORIA` (
  `id_log` int NOT NULL AUTO_INCREMENT,
  `tabla_log` varchar(60) NOT NULL,
  `id_registro_log` varchar(60) NOT NULL,
  `accion_log` varchar(20) NOT NULL,
  `valores_anteriores_log` longtext NOT NULL,
  `valores_nuevos_log` longtext NOT NULL,
  `fec_hora_log` datetime(6) NOT NULL,
  `id_usuario` int DEFAULT NULL,
  PRIMARY KEY (`id_log`),
  KEY `LOG_AUDITORIA_id_usuario_8e23cc12_fk_USUARIOS_id_usuario` (`id_usuario`),
  CONSTRAINT `LOG_AUDITORIA_id_usuario_8e23cc12_fk_USUARIOS_id_usuario` FOREIGN KEY (`id_usuario`) REFERENCES `USUARIOS` (`id_usuario`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `OBJETOS` (
  `id_objeto` int NOT NULL AUTO_INCREMENT,
  `nom_objeto` varchar(100) NOT NULL,
  `estado_objeto` tinyint(1) NOT NULL,
  PRIMARY KEY (`id_objeto`),
  UNIQUE KEY `nom_objeto` (`nom_objeto`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `PEDIDOS` (
  `id_pedido` int NOT NULL AUTO_INCREMENT,
  `Fecha_pedido` date NOT NULL,
  `id_usuario` int NOT NULL,
  `patente_vehiculos` varchar(15) NOT NULL,
  `Direccion_destino` varchar(200) NOT NULL,
  `Estado_pedido` varchar(20) NOT NULL,
  `Fec_anulacion` datetime(6) DEFAULT NULL,
  `Fecha_servicio` date NOT NULL,
  `Motivo_anulacion` varchar(200) DEFAULT NULL,
  `Direccion_origen` varchar(200) NOT NULL,
  `Total_pedido` decimal(12,2) NOT NULL,
  `id_usuario_anulacion` int DEFAULT NULL,
  `Hora_servicio` time(6) NOT NULL,
  `Duracion_horas` smallint unsigned NOT NULL,
  PRIMARY KEY (`id_pedido`),
  KEY `PEDIDOS_id_usuario_645b5187_fk_USUARIOS_id_usuario` (`id_usuario`),
  KEY `PEDIDOS_patente_vehiculos_2a5d10a3_fk_VEHICULOS_Patente` (`patente_vehiculos`),
  KEY `PEDIDOS_id_usuario_anulacion_cda902b9_fk_USUARIOS_id_usuario` (`id_usuario_anulacion`),
  CONSTRAINT `PEDIDOS_id_usuario_645b5187_fk_USUARIOS_id_usuario` FOREIGN KEY (`id_usuario`) REFERENCES `USUARIOS` (`id_usuario`),
  CONSTRAINT `PEDIDOS_id_usuario_anulacion_cda902b9_fk_USUARIOS_id_usuario` FOREIGN KEY (`id_usuario_anulacion`) REFERENCES `USUARIOS` (`id_usuario`),
  CONSTRAINT `PEDIDOS_patente_vehiculos_2a5d10a3_fk_VEHICULOS_Patente` FOREIGN KEY (`patente_vehiculos`) REFERENCES `VEHICULOS` (`Patente`),
  CONSTRAINT `PEDIDOS_chk_1` CHECK ((`Duracion_horas` >= 0))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `PERMISOS` (
  `id_permiso` int NOT NULL AUTO_INCREMENT,
  `nom_permiso` varchar(100) NOT NULL,
  `desc_permiso` varchar(100) DEFAULT NULL,
  PRIMARY KEY (`id_permiso`),
  UNIQUE KEY `nom_permiso` (`nom_permiso`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `PERMISOS_ROLES` (
  `id_permiso_rol` int NOT NULL AUTO_INCREMENT,
  `id_permiso` int NOT NULL,
  `id_rol` int NOT NULL,
  PRIMARY KEY (`id_permiso_rol`),
  UNIQUE KEY `PERMISOS_ROLES_id_rol_id_permiso_ae137dbf_uniq` (`id_rol`,`id_permiso`),
  KEY `PERMISOS_ROLES_id_permiso_d10c49ce_fk_PERMISOS_id_permiso` (`id_permiso`),
  CONSTRAINT `PERMISOS_ROLES_id_permiso_d10c49ce_fk_PERMISOS_id_permiso` FOREIGN KEY (`id_permiso`) REFERENCES `PERMISOS` (`id_permiso`),
  CONSTRAINT `PERMISOS_ROLES_id_rol_29bcd9af_fk_ROLES_id_rol` FOREIGN KEY (`id_rol`) REFERENCES `ROLES` (`id_rol`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `PERSONAL_PEDIDO` (
  `id_personal_pedido` int NOT NULL AUTO_INCREMENT,
  `funcion_personal` varchar(10) NOT NULL,
  `id_pedido` int NOT NULL,
  `id_usuario` int NOT NULL,
  PRIMARY KEY (`id_personal_pedido`),
  UNIQUE KEY `persona_una_vez_por_pedido` (`id_pedido`,`id_usuario`),
  KEY `PERSONAL_PEDIDO_id_usuario_c10293c8_fk_USUARIOS_id_usuario` (`id_usuario`),
  CONSTRAINT `PERSONAL_PEDIDO_id_pedido_e84f38a2_fk_PEDIDOS_id_pedido` FOREIGN KEY (`id_pedido`) REFERENCES `PEDIDOS` (`id_pedido`),
  CONSTRAINT `PERSONAL_PEDIDO_id_usuario_c10293c8_fk_USUARIOS_id_usuario` FOREIGN KEY (`id_usuario`) REFERENCES `USUARIOS` (`id_usuario`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `RECURSOS_ASIGNADOS` (
  `id_recursos_asignados` int NOT NULL AUTO_INCREMENT,
  `Materiales` varchar(50) NOT NULL,
  `id_servicios` int NOT NULL,
  PRIMARY KEY (`id_recursos_asignados`),
  KEY `RECURSOS_ASIGNADOS_id_servicios_b53d9e2e_fk_SERVICIOS` (`id_servicios`),
  CONSTRAINT `RECURSOS_ASIGNADOS_id_servicios_b53d9e2e_fk_SERVICIOS` FOREIGN KEY (`id_servicios`) REFERENCES `SERVICIOS` (`id_servicio`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `REPROGRAMACIONES` (
  `id_reprogramacion` int NOT NULL AUTO_INCREMENT,
  `Fecha_anterior` date NOT NULL,
  `Hora_anterior` time(6) NOT NULL,
  `Fecha_nueva` date NOT NULL,
  `Hora_nueva` time(6) NOT NULL,
  `Motivo_reprog` varchar(40) NOT NULL,
  `Observacion_reprog` varchar(200) DEFAULT NULL,
  `Fec_reprog` datetime(6) NOT NULL,
  `Visto_cliente` tinyint(1) NOT NULL,
  `id_pedido` int NOT NULL,
  `id_usuario` int NOT NULL,
  `patente_anterior` varchar(15) NOT NULL,
  `patente_nueva` varchar(15) NOT NULL,
  PRIMARY KEY (`id_reprogramacion`),
  KEY `REPROGRAMACIONES_id_pedido_f117e328_fk_PEDIDOS_id_pedido` (`id_pedido`),
  KEY `REPROGRAMACIONES_id_usuario_27a1e445_fk_USUARIOS_id_usuario` (`id_usuario`),
  KEY `REPROGRAMACIONES_patente_anterior_98a07847_fk_VEHICULOS_Patente` (`patente_anterior`),
  KEY `REPROGRAMACIONES_patente_nueva_def15a07_fk_VEHICULOS_Patente` (`patente_nueva`),
  CONSTRAINT `REPROGRAMACIONES_id_pedido_f117e328_fk_PEDIDOS_id_pedido` FOREIGN KEY (`id_pedido`) REFERENCES `PEDIDOS` (`id_pedido`),
  CONSTRAINT `REPROGRAMACIONES_id_usuario_27a1e445_fk_USUARIOS_id_usuario` FOREIGN KEY (`id_usuario`) REFERENCES `USUARIOS` (`id_usuario`),
  CONSTRAINT `REPROGRAMACIONES_patente_anterior_98a07847_fk_VEHICULOS_Patente` FOREIGN KEY (`patente_anterior`) REFERENCES `VEHICULOS` (`Patente`),
  CONSTRAINT `REPROGRAMACIONES_patente_nueva_def15a07_fk_VEHICULOS_Patente` FOREIGN KEY (`patente_nueva`) REFERENCES `VEHICULOS` (`Patente`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `ROLES` (
  `id_rol` int NOT NULL AUTO_INCREMENT,
  `nom_rol` varchar(100) NOT NULL,
  `desc_rol` varchar(100) DEFAULT NULL,
  PRIMARY KEY (`id_rol`),
  UNIQUE KEY `nom_rol` (`nom_rol`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `SERVICIOS` (
  `id_servicio` int NOT NULL AUTO_INCREMENT,
  `Tipo_servicio` varchar(100) NOT NULL,
  `Precio_base` decimal(12,2) NOT NULL,
  `Activo` tinyint(1) NOT NULL,
  `Categoria` varchar(10) NOT NULL,
  `Duracion_horas` smallint unsigned DEFAULT NULL,
  PRIMARY KEY (`id_servicio`),
  CONSTRAINT `SERVICIOS_chk_1` CHECK ((`Duracion_horas` >= 0))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `SUELDOS` (
  `id_Sueldos` int NOT NULL AUTO_INCREMENT,
  `Monto` decimal(12,2) NOT NULL,
  `Fecha_pago` date NOT NULL,
  PRIMARY KEY (`id_Sueldos`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `USUARIOS` (
  `id_usuario` int NOT NULL AUTO_INCREMENT,
  `Dni_usuario` bigint NOT NULL,
  `Nombre_usuario` varchar(100) NOT NULL,
  `Apellido_usuario` varchar(100) NOT NULL,
  `Correo_usuario` varchar(150) NOT NULL,
  `contrasena_usuario` varchar(255) NOT NULL,
  `Telefono_usuario` varchar(30) DEFAULT NULL,
  `Estado_usuario` tinyint(1) NOT NULL,
  `fec_ult_acc_usuario` datetime(6) DEFAULT NULL,
  `usuario_login` varchar(100) NOT NULL,
  `debe_cambiar_clave` tinyint(1) NOT NULL,
  `fec_ult_mod_usuario` datetime(6) NOT NULL,
  `fec_baja_usuario` datetime(6) DEFAULT NULL,
  `id_rol` int NOT NULL,
  `id_sueldo` int DEFAULT NULL,
  PRIMARY KEY (`id_usuario`),
  UNIQUE KEY `Dni_usuario` (`Dni_usuario`),
  UNIQUE KEY `Correo_usuario` (`Correo_usuario`),
  UNIQUE KEY `usuario_login` (`usuario_login`),
  KEY `USUARIOS_id_rol_c26d371d_fk_ROLES_id_rol` (`id_rol`),
  KEY `USUARIOS_id_sueldo_772f8916_fk_SUELDOS_id_Sueldos` (`id_sueldo`),
  CONSTRAINT `USUARIOS_id_rol_c26d371d_fk_ROLES_id_rol` FOREIGN KEY (`id_rol`) REFERENCES `ROLES` (`id_rol`),
  CONSTRAINT `USUARIOS_id_sueldo_772f8916_fk_SUELDOS_id_Sueldos` FOREIGN KEY (`id_sueldo`) REFERENCES `SUELDOS` (`id_Sueldos`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `VEHICULOS` (
  `Patente` varchar(15) NOT NULL,
  `Marca_Modelo_vehiculo` varchar(100) NOT NULL,
  `Capacidad_kg_vehiculo` decimal(10,2) NOT NULL,
  `Capacidad_m3_vehiculo` decimal(10,2) NOT NULL,
  `Estado_vehiculo` varchar(30) NOT NULL,
  `Kilometraje_vehiculo` decimal(10,2) NOT NULL,
  `Anio_vehiculo` int DEFAULT NULL,
  `tipo_vehiculo` varchar(50) NOT NULL,
  `observaciones` longtext,
  `created_at` datetime(6) NOT NULL,
  `chofer_asignado_id` int DEFAULT NULL,
  PRIMARY KEY (`Patente`),
  KEY `VEHICULOS_chofer_asignado_id_91d6b016_fk_USUARIOS_id_usuario` (`chofer_asignado_id`),
  CONSTRAINT `VEHICULOS_chofer_asignado_id_91d6b016_fk_USUARIOS_id_usuario` FOREIGN KEY (`chofer_asignado_id`) REFERENCES `USUARIOS` (`id_usuario`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `auth_group` (
  `id` int NOT NULL AUTO_INCREMENT,
  `name` varchar(150) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `name` (`name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `auth_group_permissions` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `group_id` int NOT NULL,
  `permission_id` int NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `auth_group_permissions_group_id_permission_id_0cd325b0_uniq` (`group_id`,`permission_id`),
  KEY `auth_group_permissio_permission_id_84c5c92e_fk_auth_perm` (`permission_id`),
  CONSTRAINT `auth_group_permissio_permission_id_84c5c92e_fk_auth_perm` FOREIGN KEY (`permission_id`) REFERENCES `auth_permission` (`id`),
  CONSTRAINT `auth_group_permissions_group_id_b120cbf9_fk_auth_group_id` FOREIGN KEY (`group_id`) REFERENCES `auth_group` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `auth_permission` (
  `id` int NOT NULL AUTO_INCREMENT,
  `name` varchar(255) NOT NULL,
  `content_type_id` int NOT NULL,
  `codename` varchar(100) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `auth_permission_content_type_id_codename_01ab375a_uniq` (`content_type_id`,`codename`),
  CONSTRAINT `auth_permission_content_type_id_2f476e4b_fk_django_co` FOREIGN KEY (`content_type_id`) REFERENCES `django_content_type` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `auth_user` (
  `id` int NOT NULL AUTO_INCREMENT,
  `password` varchar(128) NOT NULL,
  `last_login` datetime(6) DEFAULT NULL,
  `is_superuser` tinyint(1) NOT NULL,
  `username` varchar(150) NOT NULL,
  `first_name` varchar(150) NOT NULL,
  `last_name` varchar(150) NOT NULL,
  `email` varchar(254) NOT NULL,
  `is_staff` tinyint(1) NOT NULL,
  `is_active` tinyint(1) NOT NULL,
  `date_joined` datetime(6) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `username` (`username`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `auth_user_groups` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `user_id` int NOT NULL,
  `group_id` int NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `auth_user_groups_user_id_group_id_94350c0c_uniq` (`user_id`,`group_id`),
  KEY `auth_user_groups_group_id_97559544_fk_auth_group_id` (`group_id`),
  CONSTRAINT `auth_user_groups_group_id_97559544_fk_auth_group_id` FOREIGN KEY (`group_id`) REFERENCES `auth_group` (`id`),
  CONSTRAINT `auth_user_groups_user_id_6a12ed8b_fk_auth_user_id` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `auth_user_user_permissions` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `user_id` int NOT NULL,
  `permission_id` int NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `auth_user_user_permissions_user_id_permission_id_14a6b632_uniq` (`user_id`,`permission_id`),
  KEY `auth_user_user_permi_permission_id_1fbb5f2c_fk_auth_perm` (`permission_id`),
  CONSTRAINT `auth_user_user_permi_permission_id_1fbb5f2c_fk_auth_perm` FOREIGN KEY (`permission_id`) REFERENCES `auth_permission` (`id`),
  CONSTRAINT `auth_user_user_permissions_user_id_a95ead1b_fk_auth_user_id` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `django_admin_log` (
  `id` int NOT NULL AUTO_INCREMENT,
  `action_time` datetime(6) NOT NULL,
  `object_id` longtext,
  `object_repr` varchar(200) NOT NULL,
  `action_flag` smallint unsigned NOT NULL,
  `change_message` longtext NOT NULL,
  `content_type_id` int DEFAULT NULL,
  `user_id` int NOT NULL,
  PRIMARY KEY (`id`),
  KEY `django_admin_log_content_type_id_c4bce8eb_fk_django_co` (`content_type_id`),
  KEY `django_admin_log_user_id_c564eba6_fk_auth_user_id` (`user_id`),
  CONSTRAINT `django_admin_log_content_type_id_c4bce8eb_fk_django_co` FOREIGN KEY (`content_type_id`) REFERENCES `django_content_type` (`id`),
  CONSTRAINT `django_admin_log_user_id_c564eba6_fk_auth_user_id` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`),
  CONSTRAINT `django_admin_log_chk_1` CHECK ((`action_flag` >= 0))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `django_content_type` (
  `id` int NOT NULL AUTO_INCREMENT,
  `app_label` varchar(100) NOT NULL,
  `model` varchar(100) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `django_content_type_app_label_model_76bd3d3b_uniq` (`app_label`,`model`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `django_migrations` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `app` varchar(255) NOT NULL,
  `name` varchar(255) NOT NULL,
  `applied` datetime(6) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `django_session` (
  `session_key` varchar(40) NOT NULL,
  `session_data` longtext NOT NULL,
  `expire_date` datetime(6) NOT NULL,
  PRIMARY KEY (`session_key`),
  KEY `django_session_expire_date_a5c62663` (`expire_date`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

