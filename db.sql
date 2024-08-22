CREATE DATABASE IF NOT EXISTS digitalizacion_archivos;

USE digitalizacion_archivos;
create table archivos
(
    id                    int auto_increment
        primary key,
    asunto                varchar(255)                          not null,
    numero_oficio         varchar(50)                           not null,
    fecha_creacion        date                                  not null,
    fecha_subida          timestamp default current_timestamp() null,
    unidad_administrativa varchar(100)                          not null,
    folio_inicial         int                                   not null,
    folio_final           int                                   not null,
    emisor                varchar(100)                          not null,
    remitente             varchar(100)                          not null,
    resumen               text                                         not null,
    categoria_id          int                                   null,
    subcategoria_id       int                                   null
)
    engine = InnoDB;

create table categorias
(
    id     int auto_increment
        primary key,
    nombre varchar(255) not null
)
    engine = InnoDB;

create table subcategorias
(
    id           int auto_increment
        primary key,
    nombre       varchar(255) null,
    categoria_id int          null,
    constraint subcategorias_ibfk_1
        foreign key (categoria_id) references categorias (id)
)
    engine = InnoDB;

create index categoria_id
    on subcategorias (categoria_id);

create table usuarios
(
    id              int auto_increment
        primary key,
    nombre          varchar(100) not null,
    numero_empleado int          not null,
    rol             varchar(50)  not null,
    password        varchar(255) not null,
    nivel           varchar(15) not null,
    constraint numero_empleado
        unique (numero_empleado)
)
    engine = InnoDB;

CREATE TABLE historial_versiones (
    id INT AUTO_INCREMENT PRIMARY KEY,
    documento_id INT,
    accion VARCHAR(50),
    fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    usuario_id INT,
    detalles TEXT,
    CONSTRAINT historial_versiones_ibfk_1
        FOREIGN KEY (documento_id) REFERENCES archivos(id) ON DELETE CASCADE,
    CONSTRAINT historial_versiones_ibfk_2
        FOREIGN KEY (usuario_id) REFERENCES usuarios(id)
) ENGINE=InnoDB;


create table unidades_administrativas
(
    id     int auto_increment
        primary key,
    nombre varchar(255) not null
)
    engine = InnoDB;

create index documento_id
    on historial_versiones (documento_id);

create index usuario_id
    on historial_versiones (usuario_id);

    INSERT INTO categorias (nombre) VALUES ('Tecnología');

INSERT INTO subcategorias (nombre, categoria_id) VALUES ('Programación', 1);

    INSERT INTO unidades_administrativas (nombre) VALUES ('Mineria');


