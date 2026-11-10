-- Mudanzas y Fletes Salta (Grupo 5) - Datos de las tablas maestras (28/10/2026)
-- Roles, permisos, sueldos, servicios con sus materiales, catalogo de objetos y vehiculos.
-- No incluye usuarios ni pedidos. Cargar despues de 01_estructura.sql.


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

LOCK TABLES `ROLES` WRITE;
/*!40000 ALTER TABLE `ROLES` DISABLE KEYS */;
INSERT INTO `ROLES` (`id_rol`, `nom_rol`, `desc_rol`) VALUES (1,'Administrador','Acceso total a la administración de seguridad y usuarios'),(2,'Chofer','Conducción de vehículos y visualización de rutas de mudanza'),(3,'Ayudante de Carga','Personal operativo de carga, descarga y embalaje de bultos'),(4,'Cliente','Cliente que registra y sigue sus pedidos de mudanza');
/*!40000 ALTER TABLE `ROLES` ENABLE KEYS */;
UNLOCK TABLES;

LOCK TABLES `PERMISOS` WRITE;
/*!40000 ALTER TABLE `PERMISOS` DISABLE KEYS */;
INSERT INTO `PERMISOS` (`id_permiso`, `nom_permiso`, `desc_permiso`) VALUES (1,'USR_CREAR','Dar de alta usuarios'),(2,'USR_EDITAR_CORREO','Modificar el correo de un usuario'),(3,'USR_BAJA','Dar de baja y reactivar usuarios'),(4,'USR_RESET_CLAVE','Restablecer la clave de un usuario'),(5,'VEH_GESTIONAR','Alta, modificación y baja de vehículos'),(6,'MUDANZAS_OPERAR','Ver el portal del personal y sus vehículos asignados'),(7,'PED_REGISTRAR','Registrar pedidos de mudanza'),(8,'PED_CONSULTAR','Consultar pedidos'),(9,'PED_GESTIONAR','Confirmar y finalizar pedidos (y ver los de todos)'),(10,'PED_ANULAR','Anular pedidos'),(11,'PED_COMPROBANTE','Emitir el comprobante del pedido'),(12,'SRV_GESTIONAR','Alta, modificación y baja de servicios'),(13,'USR_CONSULTAR','Ver el panel de usuarios'),(14,'USR_CAMBIAR_ROL','Cambiar el rol de un usuario'),(15,'ROL_GESTIONAR','Ver, crear y editar roles y sus permisos'),(16,'OBJ_GESTIONAR','Alta, modificación y baja del catálogo de objetos'),(17,'AUD_CONSULTAR','Ver el log de auditoría (quién modificó o anuló qué)');
/*!40000 ALTER TABLE `PERMISOS` ENABLE KEYS */;
UNLOCK TABLES;

LOCK TABLES `PERMISOS_ROLES` WRITE;
/*!40000 ALTER TABLE `PERMISOS_ROLES` DISABLE KEYS */;
INSERT INTO `PERMISOS_ROLES` (`id_permiso_rol`, `id_permiso`, `id_rol`) VALUES (1,1,1),(2,2,1),(3,3,1),(4,4,1),(5,5,1),(6,6,1),(9,8,1),(10,9,1),(11,10,1),(12,11,1),(13,12,1),(17,13,1),(18,14,1),(19,15,1),(20,16,1),(21,17,1),(7,6,2),(8,6,3),(14,7,4),(15,8,4),(16,11,4);
/*!40000 ALTER TABLE `PERMISOS_ROLES` ENABLE KEYS */;
UNLOCK TABLES;

LOCK TABLES `SUELDOS` WRITE;
/*!40000 ALTER TABLE `SUELDOS` DISABLE KEYS */;
INSERT INTO `SUELDOS` (`id_Sueldos`, `Monto`, `Fecha_pago`) VALUES (1,980000.00,'2026-09-05'),(2,720000.00,'2026-09-05');
/*!40000 ALTER TABLE `SUELDOS` ENABLE KEYS */;
UNLOCK TABLES;

LOCK TABLES `SERVICIOS` WRITE;
/*!40000 ALTER TABLE `SERVICIOS` DISABLE KEYS */;
INSERT INTO `SERVICIOS` (`id_servicio`, `Tipo_servicio`, `Precio_base`, `Activo`, `Categoria`, `Duracion_horas`) VALUES (1,'Mudanza local',185000.00,1,'Principal',10),(2,'Mudanza nacional',640000.00,1,'Principal',48),(3,'Flete urbano',75000.00,1,'Principal',5),(4,'Embalaje',25000.00,1,'Adicional',NULL),(5,'Desarmado y armado de muebles',35000.00,1,'Adicional',NULL),(6,'Ayudante extra',20000.00,0,'Adicional',NULL);
/*!40000 ALTER TABLE `SERVICIOS` ENABLE KEYS */;
UNLOCK TABLES;

LOCK TABLES `RECURSOS_ASIGNADOS` WRITE;
/*!40000 ALTER TABLE `RECURSOS_ASIGNADOS` DISABLE KEYS */;
INSERT INTO `RECURSOS_ASIGNADOS` (`id_recursos_asignados`, `Materiales`, `id_servicios`) VALUES (1,'Mantas, film y cintas',1),(2,'Mantas, film, cintas y zunchos',2),(3,'Correas y mantas',3),(4,'Cajas, papel burbuja y cinta',4),(5,'Herramientas',5);
/*!40000 ALTER TABLE `RECURSOS_ASIGNADOS` ENABLE KEYS */;
UNLOCK TABLES;

LOCK TABLES `OBJETOS` WRITE;
/*!40000 ALTER TABLE `OBJETOS` DISABLE KEYS */;
INSERT INTO `OBJETOS` (`id_objeto`, `nom_objeto`, `estado_objeto`) VALUES (1,'Heladera',1),(2,'Cocina',1),(3,'Lavarropas',1),(4,'Microondas',1),(5,'Cama 1 plaza',1),(6,'Cama 2 plazas',1),(7,'Colchón',1),(8,'Ropero',1),(9,'Cómoda',1),(10,'Mesa',1),(11,'Sillas',1),(12,'Sillón',1),(13,'Televisor',1),(14,'Escritorio',1),(15,'Biblioteca',1),(16,'Cajas',1),(17,'Bolsos y valijas',1),(18,'Bicicleta',1),(19,'Plantas',1),(20,'Otro',1);
/*!40000 ALTER TABLE `OBJETOS` ENABLE KEYS */;
UNLOCK TABLES;

LOCK TABLES `VEHICULOS` WRITE;
/*!40000 ALTER TABLE `VEHICULOS` DISABLE KEYS */;
INSERT INTO `VEHICULOS` (`Patente`, `Marca_Modelo_vehiculo`, `Capacidad_kg_vehiculo`, `Capacidad_m3_vehiculo`, `Estado_vehiculo`, `Kilometraje_vehiculo`, `Anio_vehiculo`, `tipo_vehiculo`, `observaciones`, `created_at`, `chofer_asignado_id`) VALUES ('AA123XR','Mercedes Benz 710',1000.00,120.00,'Disponible',1210000.00,2018,'Camión Chico','','2026-08-27 20:51:14.229948',NULL),('AC-789-GH','Iveco Daily 70C17',3500.00,24.00,'En Mantenimiento',89300.00,2020,'Camión Mediano','Service programado de frenos y amortiguadores.','2026-10-02 18:58:09.789269',NULL),('AD-321-JK','Renault Master Furgón',1600.00,12.00,'Disponible',34500.00,2021,'Camión Chico','Ideal para fletes rápidos en microcentro.','2026-10-02 18:58:09.802671',NULL),('AE-123-CD','Mercedes-Benz Accelo 815',5000.00,32.00,'Disponible',45200.00,2022,'Camión Grande','Equipado con rampa hidráulica y mantas de protección.','2026-10-02 18:58:09.764077',2),('AF-456-EF','Ford Transit Chasis',2200.00,18.00,'En Viaje',28100.00,2023,'Camión Mediano','Asignado a servicio interurbano Salta - Cafayate.','2026-10-02 18:58:09.774850',NULL);
/*!40000 ALTER TABLE `VEHICULOS` ENABLE KEYS */;
UNLOCK TABLES;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;


-- El chofer habitual depende de los usuarios de cada instalacion: se deja vacio.
UPDATE VEHICULOS SET chofer_asignado_id = NULL;
