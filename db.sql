CREATE DATABASE IF NOT EXISTS digitalizacion_archivos;

USE digitalizacion_archivos;

CREATE TABLE archivos (
    id INT AUTO_INCREMENT PRIMARY KEY,
    asunto VARCHAR(255) NOT NULL,
    numero_oficio VARCHAR(50) NOT NULL,
    fecha_creacion DATE NOT NULL,
    fecha_subida TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    unidad_administrativa VARCHAR(100) NOT NULL,
    folio_inicial INT NOT NULL,
    folio_final INT NOT NULL,
    emisor VARCHAR(100) NOT NULL,
    remitente VARCHAR(100) NOT NULL,
    resumen TEXT NOT NULL
);

select * from archivos;

CREATE TABLE usuarios (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
    numero_empleado INT UNIQUE NOT NULL,
    rol VARCHAR(50) NOT NULL,
    password VARCHAR(255) NOT NULL
);

select * from usuarios;