-- Configuración de caracteres
SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

-- Creación de la base de datos
CREATE DATABASE IF NOT EXISTS `autolavado` DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci;
USE `autolavado`;

-- Tabla EMPLEADO
CREATE TABLE `empleado` (
  `Id` INT NOT NULL AUTO_INCREMENT,
  `Nombre` VARCHAR(100) NOT NULL,
  `Apellidos` VARCHAR(100) NOT NULL,
  `Fecha_Nacimiento` DATE NOT NULL,
  `Estado` VARCHAR(20) NOT NULL,
  PRIMARY KEY (`Id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Tabla VEHICULOS
CREATE TABLE `vehiculos` (
  `Id` INT NOT NULL AUTO_INCREMENT,
  `Tipo_Vehículo` VARCHAR(50) NOT NULL,
  `Descripcion` VARCHAR(255),
  `Estado` VARCHAR(20) NOT NULL,
  `Placa` VARCHAR(20) NOT NULL,
  `Marca` VARCHAR(50) NOT NULL,
  `Modelo` VARCHAR(50) NOT NULL,
  `Color` VARCHAR(30) NOT NULL,
  PRIMARY KEY (`Id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Tabla TIPO_INSUMO
CREATE TABLE `tipo_insumo` (
  `Id` INT NOT NULL AUTO_INCREMENT,
  `Nombre` VARCHAR(100) NOT NULL,
  `Descripción` VARCHAR(255),
  `Estado` VARCHAR(20) NOT NULL,
  PRIMARY KEY (`Id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Tabla INSUMOS
CREATE TABLE `insumos` (
  `Id` INT NOT NULL AUTO_INCREMENT,
  `Nombre` VARCHAR(100) NOT NULL,
  `Precio_Unitario` DECIMAL(10,2) NOT NULL,
  `Id_TipoInsumo` INT NOT NULL,
  `Estado` VARCHAR(20) NOT NULL,
  PRIMARY KEY (`Id`),
  KEY `FK_Insumos_TipoInsumo` (`Id_TipoInsumo`),
  CONSTRAINT `FK_Insumos_TipoInsumo` FOREIGN KEY (`Id_TipoInsumo`) REFERENCES `tipo_insumo` (`Id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Tabla TIPO_LAVADO
CREATE TABLE `tipo_lavado` (
  `Id` INT NOT NULL AUTO_INCREMENT,
  `Nombre` VARCHAR(100) NOT NULL,
  `Precio` DECIMAL(10,2) NOT NULL,
  `Id_Insumo` INT,
  `Estado` VARCHAR(20) NOT NULL,
  PRIMARY KEY (`Id`),
  CONSTRAINT `FK_TipoLavado_Insumo` FOREIGN KEY (`Id_Insumo`) REFERENCES `insumos` (`Id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Tabla JORNADA
CREATE TABLE `jornada` (
  `Id` INT NOT NULL AUTO_INCREMENT,
  `Hora_Inicio` TIME NOT NULL,
  `Hora_Final` TIME NOT NULL,
  `Estado` VARCHAR(20) NOT NULL,
  PRIMARY KEY (`Id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Tabla TURNO_EMPLEADO
CREATE TABLE `turno_empleado` (
  `Id` INT NOT NULL AUTO_INCREMENT,
  `Id_Empleado` INT NOT NULL,
  `Día` VARCHAR(20) NOT NULL,
  `Id_Jornada` INT NOT NULL,
  PRIMARY KEY (`Id`),
  KEY `FK_Turno_Empleado_Empleado` (`Id_Empleado`),
  KEY `FK_Jornada` (`Id_Jornada`),
  CONSTRAINT `FK_Turno_Empleado_Empleado` FOREIGN KEY (`Id_Empleado`) REFERENCES `empleado` (`Id`),
  CONSTRAINT `FK_Jornada` FOREIGN KEY (`Id_Jornada`) REFERENCES `jornada` (`Id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Tabla SERVICIOS
CREATE TABLE `servicios` (
  `Id` INT NOT NULL AUTO_INCREMENT,
  `Id_Empleado_Recibe` INT NOT NULL,
  `Id_Empleado_Lava` INT NOT NULL,
  `Id_Tipovehículo` INT NOT NULL,
  `Id_TipoLavado` INT NOT NULL,
  `Hora_Recibe` TIME NOT NULL,
  `Hora_Entrega` TIME,
  `Precio` DECIMAL(10,2) NOT NULL,
  `Placa` VARCHAR(20) NOT NULL,
  `Fecha` DATE NOT NULL,
  `Estado` VARCHAR(20) NOT NULL,
  PRIMARY KEY (`Id`),
  KEY `FK_Servicios_EmpleadoRecibe` (`Id_Empleado_Recibe`),
  KEY `FK_Servicios_EmpleadoLava` (`Id_Empleado_Lava`),
  KEY `FK_Servicios_TipoVehiculo` (`Id_Tipovehículo`),
  KEY `FK_Servicios_TipoLavado` (`Id_TipoLavado`),
  CONSTRAINT `FK_Servicios_EmpleadoRecibe` FOREIGN KEY (`Id_Empleado_Recibe`) REFERENCES `empleado` (`Id`),
  CONSTRAINT `FK_Servicios_EmpleadoLava` FOREIGN KEY (`Id_Empleado_Lava`) REFERENCES `empleado` (`Id`),
  CONSTRAINT `FK_Servicios_TipoVehiculo` FOREIGN KEY (`Id_Tipovehículo`) REFERENCES `vehiculos` (`Id`),
  CONSTRAINT `FK_Servicios_TipoLavado` FOREIGN KEY (`Id_TipoLavado`) REFERENCES `tipo_lavado` (`Id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Tabla INSUMOS_POR_SERVICIO
CREATE TABLE `insumos_por_servicio` (
  `Id` INT NOT NULL AUTO_INCREMENT,
  `Id_Servicio` INT NOT NULL,
  `Id_Insumo` INT NOT NULL,
  `Cantidad_Utilizada` INT NOT NULL,
  PRIMARY KEY (`Id`),
  KEY `Id_Servicio` (`Id_Servicio`),
  KEY `Id_Insumo` (`Id_Insumo`),
  CONSTRAINT `FK_InsumosPorServicio_Servicio` FOREIGN KEY (`Id_Servicio`) REFERENCES `servicios` (`Id`),
  CONSTRAINT `FK_InsumosPorServicio_Insumo` FOREIGN KEY (`Id_Insumo`) REFERENCES `insumos` (`Id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Tabla INVENTARIO
CREATE TABLE `inventario` (
  `Id` INT NOT NULL AUTO_INCREMENT,
  `Id_insumo` INT NOT NULL,
  `Stock` INT NOT NULL,
  `Estado` VARCHAR(20) NOT NULL,
  PRIMARY KEY (`Id`),
  KEY `FK_Inventario_Insumo` (`Id_insumo`),
  CONSTRAINT `FK_Inventario_Insumo` FOREIGN KEY (`Id_insumo`) REFERENCES `insumos` (`Id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Tabla PROVEEDOR
CREATE TABLE `proveedor` (
  `Id` INT NOT NULL AUTO_INCREMENT,
  `Nombre` VARCHAR(100) NOT NULL,
  `Contacto` VARCHAR(100) NOT NULL,
  `Email` VARCHAR(100) NOT NULL,
  `Telefono` VARCHAR(20) NOT NULL,
  `Direccion` VARCHAR(200) NOT NULL,
  `Fecha_Registro` DATE NOT NULL,
  `Estado` VARCHAR(20) NOT NULL,
  PRIMARY KEY (`Id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Tabla COTIZACION
CREATE TABLE `cotizacion` (
  `Id` INT NOT NULL AUTO_INCREMENT,
  `Id_Proveedor` INT NOT NULL,
  `Id_Insumo` INT NOT NULL,
  `Precio` DECIMAL(10,2) NOT NULL,
  `Fecha_Cotizacion` DATE NOT NULL,
  `Observaciones` TEXT,
  `Estado` VARCHAR(20) NOT NULL DEFAULT 'Pendiente',
  PRIMARY KEY (`Id`),
  KEY `Id_Proveedor` (`Id_Proveedor`),
  KEY `Id_Insumo` (`Id_Insumo`),
  CONSTRAINT `FK_Cotizacion_Proveedor` FOREIGN KEY (`Id_Proveedor`) REFERENCES `proveedor` (`Id`),
  CONSTRAINT `FK_Cotizacion_Insumo` FOREIGN KEY (`Id_Insumo`) REFERENCES `insumos` (`Id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Tabla SOLICITUD_COTIZACION
CREATE TABLE `solicitud_cotizacion` (
  `Id` INT NOT NULL AUTO_INCREMENT,
  `Id_Insumo` INT NOT NULL,
  `Cantidad_Requerida` INT NOT NULL,
  `Fecha_Limite` DATE NOT NULL,
  `Descripcion` TEXT,
  `Fecha_Publicacion` DATE NOT NULL,
  `Estado` VARCHAR(20) NOT NULL DEFAULT 'Activa',
  PRIMARY KEY (`Id`),
  KEY `Id_Insumo` (`Id_Insumo`),
  CONSTRAINT `FK_SolicitudCotizacion_Insumo` FOREIGN KEY (`Id_Insumo`) REFERENCES `insumos` (`Id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Tabla EVALUACION
CREATE TABLE `evaluacion` (
  `Id` INT NOT NULL AUTO_INCREMENT,
  `Id_Servicio` INT NOT NULL,
  `Tiempo_Espera` INT NOT NULL,
  `Amabilidad` INT NOT NULL,
  `Calidad_Servicio` INT NOT NULL,
  `Comentario` TEXT,
  `Fecha_Evaluacion` DATE NOT NULL,
  PRIMARY KEY (`Id`),
  KEY `Id_Servicio` (`Id_Servicio`),
  CONSTRAINT `FK_Evaluacion_Servicio` FOREIGN KEY (`Id_Servicio`) REFERENCES `servicios` (`Id`),
  CONSTRAINT `CHK_Tiempo_Espera` CHECK (`Tiempo_Espera` BETWEEN 1 AND 5),
  CONSTRAINT `CHK_Amabilidad` CHECK (`Amabilidad` BETWEEN 1 AND 5),
  CONSTRAINT `CHK_Calidad_Servicio` CHECK (`Calidad_Servicio` BETWEEN 1 AND 5)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Tabla CHECKLIST_INGRESO
CREATE TABLE `checklist_ingreso` (
  `Id` INT NOT NULL AUTO_INCREMENT,
  `Id_Servicio` INT NOT NULL,
  `Observaciones` TEXT,
  `EstadoVehiculo` VARCHAR(255) NOT NULL,
  PRIMARY KEY (`Id`),
  KEY `Id_Servicio` (`Id_Servicio`),
  CONSTRAINT `FK_ChecklistIngreso_Servicio` FOREIGN KEY (`Id_Servicio`) REFERENCES `servicios` (`Id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

SET FOREIGN_KEY_CHECKS = 1;