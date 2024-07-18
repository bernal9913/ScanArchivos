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
    resumen               text                                  not null,
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
    constraint numero_empleado
        unique (numero_empleado)
)
    engine = InnoDB;

create table historial_versiones
(
    id           int auto_increment
        primary key,
    documento_id int                                   null,
    accion       varchar(50)                           null,
    fecha        timestamp default current_timestamp() null,
    usuario_id   int                                   null,
    detalles     text                                  null,
    constraint historial_versiones_ibfk_1
        foreign key (documento_id) references archivos (id),
    constraint historial_versiones_ibfk_2
        foreign key (usuario_id) references usuarios (id)
)
    engine = InnoDB;

create index documento_id
    on historial_versiones (documento_id);

create index usuario_id
    on historial_versiones (usuario_id);

