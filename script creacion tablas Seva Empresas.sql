
CREATE TABLE public.Moneda (
                id_moneda BIGINT NOT NULL,
                codigo_iso_moneda CHAR(4) NOT NULL,
                nombre VARCHAR(50) NOT NULL,
                simbolo CHAR(3) NOT NULL,
                fecha_creacion TIMESTAMP DEFAULT now(),
                CONSTRAINT moneda_pk PRIMARY KEY (id_moneda)
);


CREATE SEQUENCE public.rol_id_rol_seq;

CREATE TABLE public.Rol (
                id_rol BIGINT NOT NULL DEFAULT nextval('public.rol_id_rol_seq'),
                nombre VARCHAR(100) NOT NULL,
                descripcion VARCHAR(200),
                fecha_creacion TIMESTAMP DEFAULT now(),
                CONSTRAINT rol_pk PRIMARY KEY (id_rol)
);


ALTER SEQUENCE public.rol_id_rol_seq OWNED BY public.Rol.id_rol;

CREATE SEQUENCE public.departamento_id_departamento_seq;

CREATE TABLE public.Departamento (
                id_departamento BIGINT NOT NULL DEFAULT nextval('public.departamento_id_departamento_seq'),
                nombre VARCHAR(100) NOT NULL,
                fecha_creacion TIMESTAMP DEFAULT now(),
                CONSTRAINT departamento_pk PRIMARY KEY (id_departamento)
);


ALTER SEQUENCE public.departamento_id_departamento_seq OWNED BY public.Departamento.id_departamento;

CREATE SEQUENCE public.ciudad_id_ciudad_seq;

CREATE TABLE public.Ciudad (
                id_ciudad BIGINT NOT NULL DEFAULT nextval('public.ciudad_id_ciudad_seq'),
                nombre VARCHAR(100) NOT NULL,
                fecha_creacion TIMESTAMP DEFAULT now(),
                id_departamento BIGINT NOT NULL,
                CONSTRAINT ciudad_pk PRIMARY KEY (id_ciudad)
);


ALTER SEQUENCE public.ciudad_id_ciudad_seq OWNED BY public.Ciudad.id_ciudad;

CREATE SEQUENCE public.barrio_id_barrio_seq;

CREATE TABLE public.Barrio (
                id_barrio BIGINT NOT NULL DEFAULT nextval('public.barrio_id_barrio_seq'),
                nombre VARCHAR(100) NOT NULL,
                fecha_creacion TIMESTAMP DEFAULT now(),
                id_ciudad BIGINT NOT NULL,
                CONSTRAINT barrio_pk PRIMARY KEY (id_barrio)
);


ALTER SEQUENCE public.barrio_id_barrio_seq OWNED BY public.Barrio.id_barrio;

CREATE SEQUENCE public.direccion_id_direccion_seq_1;

CREATE TABLE public.Direccion (
                id_direccion BIGINT NOT NULL DEFAULT nextval('public.direccion_id_direccion_seq_1'),
                calle VARCHAR(150) NOT NULL,
                numero VARCHAR(20),
                referencia VARCHAR(150),
                coodernadas VARCHAR NOT NULL,
                fecha_creacion TIMESTAMP DEFAULT now(),
                id_barrio BIGINT NOT NULL,
                CONSTRAINT direccion_pk PRIMARY KEY (id_direccion)
);
COMMENT ON TABLE public.Direccion IS 'Direcciones fisicas de empresas';


ALTER SEQUENCE public.direccion_id_direccion_seq_1 OWNED BY public.Direccion.id_direccion;

CREATE SEQUENCE public.tarifa_plan_suscripcion_id_tarifa_plan_seq_1;

CREATE TABLE public.Tarifa_Plan_Suscripcion (
                id_tarifa_plan BIGINT NOT NULL DEFAULT nextval('public.tarifa_plan_suscripcion_id_tarifa_plan_seq_1'),
                precio NUMERIC(12) NOT NULL,
                descuento NUMERIC(5,2),
                fecha_ini_vigencia DATE NOT NULL,
                fecha_fin_vigencia DATE,
                fecha_creacion TIMESTAMP DEFAULT now(),
                CONSTRAINT tarifa_plan_suscripcion_pk PRIMARY KEY (id_tarifa_plan)
);


ALTER SEQUENCE public.tarifa_plan_suscripcion_id_tarifa_plan_seq_1 OWNED BY public.Tarifa_Plan_Suscripcion.id_tarifa_plan;

CREATE SEQUENCE public.tipo_tarifa_servicio_id_tarifa_seq;

CREATE TABLE public.Tipo_Tarifa_Servicio (
                id_tarifa BIGINT NOT NULL DEFAULT nextval('public.tipo_tarifa_servicio_id_tarifa_seq'),
                nombre VARCHAR(50) NOT NULL,
                fecha_creacion TIMESTAMP DEFAULT now(),
                CONSTRAINT tipo_tarifa_servicio_pk PRIMARY KEY (id_tarifa)
);


ALTER SEQUENCE public.tipo_tarifa_servicio_id_tarifa_seq OWNED BY public.Tipo_Tarifa_Servicio.id_tarifa;

CREATE SEQUENCE public.categoria_id_categoria_seq_1;

CREATE TABLE public.Categoria (
                id_categoria BIGINT NOT NULL DEFAULT nextval('public.categoria_id_categoria_seq_1'),
                nombre VARCHAR(100) NOT NULL,
                estado BOOLEAN NOT NULL,
                fecha_creacion TIMESTAMP DEFAULT now(),
                CONSTRAINT categoria_pk PRIMARY KEY (id_categoria)
);


ALTER SEQUENCE public.categoria_id_categoria_seq_1 OWNED BY public.Categoria.id_categoria;

CREATE SEQUENCE public.tipo_documento_id_tip_documento_seq_1;

CREATE TABLE public.Tipo_Documento (
                id_tip_documento BIGINT NOT NULL DEFAULT nextval('public.tipo_documento_id_tip_documento_seq_1'),
                tipo_documento VARCHAR(60) NOT NULL,
                fecha_creacion TIMESTAMP DEFAULT now(),
                estado_tipo_documento VARCHAR(20) NOT NULL,
                es_requerido BIT NOT NULL,
                fecha_subida DATE NOT NULL,
                CONSTRAINT tipo_documento_pk PRIMARY KEY (id_tip_documento)
);


ALTER SEQUENCE public.tipo_documento_id_tip_documento_seq_1 OWNED BY public.Tipo_Documento.id_tip_documento;

CREATE SEQUENCE public.user_id_usuario_seq;

CREATE TABLE public.User (
                id_usuario BIGINT NOT NULL DEFAULT nextval('public.user_id_usuario_seq'),
                nombre_persona VARCHAR(80) NOT NULL,
                ultima_sesion TIMESTAMP,
                estado VARCHAR(20) DEFAULT 'ACTIVO'::character varying,
                email VARCHAR(80) NOT NULL,
                foto_perfil VARCHAR(500),
                fecha_creacion TIMESTAMP,
                fecha_actualizacion TIMESTAMP DEFAULT now(),
                fecha_conf_email TIMESTAMP,
                CONSTRAINT user_pk PRIMARY KEY (id_usuario)
);
COMMENT ON COLUMN public.User.estado IS 'Estado del usuario: ACTIVO o INACTIVO';


ALTER SEQUENCE public.user_id_usuario_seq OWNED BY public.User.id_usuario;

CREATE TABLE public.Usuario_Rol (
                id_usuario BIGINT NOT NULL,
                id_rol BIGINT NOT NULL,
                fecha_creacion TIMESTAMP DEFAULT now(),
                CONSTRAINT usuario_rol_pk PRIMARY KEY (id_usuario, id_rol)
);


CREATE SEQUENCE public.perfil_empresa_id_perfil_seq;

CREATE TABLE public.Perfil_Empresa (
                id_perfil BIGINT NOT NULL DEFAULT nextval('public.perfil_empresa_id_perfil_seq'),
                id_usuario BIGINT NOT NULL,
                verificado BOOLEAN DEFAULT false NOT NULL,
                fecha_verificacion DATE NOT NULL,
                estado BOOLEAN NOT NULL,
                nombre_fantasia VARCHAR(80) NOT NULL,
                razon_social VARCHAR(80) NOT NULL,
                fecha_fin DATE,
                fecha_inicio DATE NOT NULL,
                ruc VARCHAR(50),
                id_direccion BIGINT NOT NULL,
                fecha_creacion TIMESTAMP DEFAULT now(),
                CONSTRAINT perfil_empresa_pk PRIMARY KEY (id_perfil)
);


ALTER SEQUENCE public.perfil_empresa_id_perfil_seq OWNED BY public.Perfil_Empresa.id_perfil;

CREATE SEQUENCE public.excepcion_horario_id_excepcion_seq;

CREATE TABLE public.Excepcion_Horario (
                id_excepcion BIGINT NOT NULL DEFAULT nextval('public.excepcion_horario_id_excepcion_seq'),
                fecha DATE NOT NULL,
                motivo VARCHAR(500),
                tipo VARCHAR(20) NOT NULL,
                hora_inicio TIME,
                fecha_creacion TIMESTAMP DEFAULT now(),
                hora_fin TIME,
                id_perfil BIGINT NOT NULL,
                CONSTRAINT excepcion_horario_pk PRIMARY KEY (id_excepcion)
);
COMMENT ON TABLE public.Excepcion_Horario IS 'Excepciones al horario normal (d�as cerrados, horarios especiales).';
COMMENT ON COLUMN public.Excepcion_Horario.tipo IS 'Tipo de excepci�n: cerrado (d�a cerrado) o horario_especial (horario diferente)';


ALTER SEQUENCE public.excepcion_horario_id_excepcion_seq OWNED BY public.Excepcion_Horario.id_excepcion;

CREATE SEQUENCE public.horario_trabajo_id_horario_seq;

CREATE TABLE public.Horario_Trabajo (
                id_horario BIGINT NOT NULL DEFAULT nextval('public.horario_trabajo_id_horario_seq'),
                dia_semana SMALLINT NOT NULL,
                activo BOOLEAN DEFAULT true NOT NULL,
                hora_inicio TIME NOT NULL,
                hora_fin TIME NOT NULL,
                fecha_creacion TIMESTAMP,
                id_perfil BIGINT NOT NULL,
                CONSTRAINT horario_trabajo_pk PRIMARY KEY (id_horario)
);
COMMENT ON TABLE public.Horario_Trabajo IS 'Horarios de trabajo semanales de los proveedores. Aplica a todos sus servicios autom�ticamente.';
COMMENT ON COLUMN public.Horario_Trabajo.dia_semana IS 'D�a de la semana: 0=Lunes, 1=Martes, ..., 6=Domingo';


ALTER SEQUENCE public.horario_trabajo_id_horario_seq OWNED BY public.Horario_Trabajo.id_horario;

CREATE SEQUENCE public.solicitud_categoria_id_solicitud_seq;

CREATE TABLE public.Solicitud_Categoria (
                id_solicitud BIGINT NOT NULL DEFAULT nextval('public.solicitud_categoria_id_solicitud_seq'),
                nombre_categoria VARCHAR(100) NOT NULL,
                comentario_admin VARCHAR(500),
                descripcion VARCHAR(500) NOT NULL,
                estado_aprobacion VARCHAR(20) DEFAULT 'pendiente'::character varying,
                fecha_creacion TIMESTAMP,
                id_perfil BIGINT NOT NULL,
                CONSTRAINT solicitud_categoria_pk PRIMARY KEY (id_solicitud)
);
COMMENT ON TABLE public.Solicitud_Categoria IS 'Solicitudes de nuevas categor�as de servicios';
COMMENT ON COLUMN public.Solicitud_Categoria.id_solicitud IS 'Identificador �nico de la solicitud';
COMMENT ON COLUMN public.Solicitud_Categoria.nombre_categoria IS 'Nombre de la categor�a solicitada';
COMMENT ON COLUMN public.Solicitud_Categoria.comentario_admin IS 'Comentario del administrador al procesar la solicitud';
COMMENT ON COLUMN public.Solicitud_Categoria.descripcion IS 'Descripci�n de la categor�a solicitada';
COMMENT ON COLUMN public.Solicitud_Categoria.estado_aprobacion IS 'Estado de la solicitud: pendiente, aprobada, rechazada';
COMMENT ON COLUMN public.Solicitud_Categoria.fecha_creacion IS 'Fecha y hora de creaci�n de la solicitud';


ALTER SEQUENCE public.solicitud_categoria_id_solicitud_seq OWNED BY public.Solicitud_Categoria.id_solicitud;

CREATE SEQUENCE public.solicitud_servicio_id_solicitud_seq;

CREATE TABLE public.Solicitud_Servicio (
                id_solicitud BIGINT NOT NULL DEFAULT nextval('public.solicitud_servicio_id_solicitud_seq'),
                comentario_admin VARCHAR(500),
                nombre_servicio VARCHAR(60) NOT NULL,
                fecha_creacion TIMESTAMP DEFAULT now(),
                descripcion VARCHAR(500) NOT NULL,
                estado_aprobacion VARCHAR(20) DEFAULT 'pendiente'::character varying NOT NULL,
                id_perfil BIGINT NOT NULL,
                id_categoria BIGINT NOT NULL,
                CONSTRAINT solicitud_servicio_pk PRIMARY KEY (id_solicitud)
);
COMMENT ON TABLE public.Solicitud_Servicio IS 'Solicitudes de servicios pendientes de aprobaci�n';


ALTER SEQUENCE public.solicitud_servicio_id_solicitud_seq OWNED BY public.Solicitud_Servicio.id_solicitud;

CREATE SEQUENCE public.sucursal_empresa_id_sucursal_seq;

CREATE TABLE public.Sucursal_Empresa (
                id_sucursal BIGINT NOT NULL DEFAULT nextval('public.sucursal_empresa_id_sucursal_seq'),
                id_direccion BIGINT NOT NULL,
                nombre VARCHAR(100) NOT NULL,
                telefono VARCHAR(30),
                email VARCHAR(100),
                id_perfil BIGINT NOT NULL,
                es_principal BOOLEAN NOT NULL,
                fecha_creacion TIMESTAMP DEFAULT now(),
                CONSTRAINT sucursal_empresa_pk PRIMARY KEY (id_sucursal)
);


ALTER SEQUENCE public.sucursal_empresa_id_sucursal_seq OWNED BY public.Sucursal_Empresa.id_sucursal;

CREATE TABLE public.Verificacion_Solicitud (
                id_verificacion BIGINT NOT NULL,
                fecha_solicitud DATE NOT NULL,
                fecha_revision DATE NOT NULL,
                estado VARCHAR(20) NOT NULL,
                comentario VARCHAR(1000),
                id_perfil BIGINT NOT NULL,
                fecha_creacion TIMESTAMP DEFAULT now(),
                CONSTRAINT verificacion_solicitud_pk PRIMARY KEY (id_verificacion)
);


CREATE SEQUENCE public.documento_id_documento_seq;

CREATE TABLE public.Documento (
                id_documento BIGINT NOT NULL DEFAULT nextval('public.documento_id_documento_seq'),
                id_tip_documento BIGINT NOT NULL,
                estado_revision VARCHAR(20) NOT NULL,
                fecha_verificacion DATE NOT NULL,
                observacion VARCHAR(1000),
                id_verificacion BIGINT NOT NULL,
                url_archivo VARCHAR(2048),
                fecha_creacion TIMESTAMP DEFAULT now(),
                CONSTRAINT documento_pk PRIMARY KEY (id_documento)
);


ALTER SEQUENCE public.documento_id_documento_seq OWNED BY public.Documento.id_documento;

CREATE SEQUENCE public.plan_suscripcion_id_suscripcion_seq;

CREATE TABLE public.Plan_Suscripcion (
                id_suscripcion BIGINT NOT NULL DEFAULT nextval('public.plan_suscripcion_id_suscripcion_seq'),
                nombre VARCHAR(50) NOT NULL,
                descripcion VARCHAR(1000),
                fecha_creacion TIMESTAMP DEFAULT now(),
                fecha_ini_suscripcion DATE,
                fecha_fin_suscripcion DATE,
                id_tarifa_plan BIGINT NOT NULL,
                estado_plan BOOLEAN NOT NULL,
                id_perfil BIGINT NOT NULL,
                id_moneda BIGINT NOT NULL,
                CONSTRAINT plan_suscripcion_pk PRIMARY KEY (id_suscripcion)
);


ALTER SEQUENCE public.plan_suscripcion_id_suscripcion_seq OWNED BY public.Plan_Suscripcion.id_suscripcion;

CREATE TABLE public.Servicio (
                id_servicio BIGINT NOT NULL,
                id_categoria BIGINT NOT NULL,
                duracion_minutos VARCHAR DEFAULT 60,
                id_perfil BIGINT NOT NULL,
                estado BOOLEAN NOT NULL,
                nombre VARCHAR(60) NOT NULL,
                fecha_creacion TIMESTAMP,
                descripcion VARCHAR(500) NOT NULL,
                imagen VARCHAR(500),
                precio DOUBLE PRECISION NOT NULL,
                id_moneda BIGINT NOT NULL,
                CONSTRAINT servicio_pk PRIMARY KEY (id_servicio)
);
COMMENT ON COLUMN public.Servicio.imagen IS 'Ruta de la imagen representativa del servicio (PNG/JPG, m�ximo 5MB)';


CREATE SEQUENCE public.tarifa_servicio_id_tarifa_servicio_seq;

CREATE TABLE public.Tarifa_Servicio (
                id_tarifa_servicio BIGINT NOT NULL DEFAULT nextval('public.tarifa_servicio_id_tarifa_servicio_seq'),
                monto NUMERIC(12,2) NOT NULL,
                fecha_creacion TIMESTAMP DEFAULT now(),
                descripcion VARCHAR(200) NOT NULL,
                fecha_inicio DATE NOT NULL,
                fecha_fin DATE,
                id_servicio BIGINT NOT NULL,
                id_tarifa BIGINT NOT NULL,
                CONSTRAINT tarifa_servicio_pk PRIMARY KEY (id_tarifa_servicio)
);


ALTER SEQUENCE public.tarifa_servicio_id_tarifa_servicio_seq OWNED BY public.Tarifa_Servicio.id_tarifa_servicio;

CREATE SEQUENCE public.reserva_id_reserva_seq;

CREATE TABLE public.Reserva (
                id_reserva BIGINT NOT NULL DEFAULT nextval('public.reserva_id_reserva_seq'),
                id_servicio BIGINT NOT NULL,
                descripcion VARCHAR(500),
                observacion VARCHAR(1000),
                fecha DATE NOT NULL,
                hora_inicio TIME,
                hora_fin TIME,
                estado VARCHAR(20) NOT NULL,
                fecha_creacion TIMESTAMP DEFAULT now(),
                id_usuario BIGINT NOT NULL,
                CONSTRAINT reserva_pk PRIMARY KEY (id_reserva)
);
COMMENT ON COLUMN public.Reserva.hora_inicio IS 'Hora de inicio de la reserva';
COMMENT ON COLUMN public.Reserva.hora_fin IS 'Hora de fin de la reserva';


ALTER SEQUENCE public.reserva_id_reserva_seq OWNED BY public.Reserva.id_reserva;

CREATE SEQUENCE public.historial_estado_id_historial_seq;

CREATE TABLE public.Historial_Estado (
                id_historial BIGINT NOT NULL DEFAULT nextval('public.historial_estado_id_historial_seq'),
                observacion VARCHAR(100),
                estado_anterior VARCHAR(50) NOT NULL,
                fecha_cambio TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                id_reserva BIGINT NOT NULL,
                nuevo_estado VARCHAR(50) NOT NULL,
                id_usuario BIGINT NOT NULL,
                CONSTRAINT historial_estado_pk PRIMARY KEY (id_historial)
);


ALTER SEQUENCE public.historial_estado_id_historial_seq OWNED BY public.Historial_Estado.id_historial;

CREATE SEQUENCE public.calificacion_id_calificacion_seq;

CREATE TABLE public.Calificacion (
                id_calificacion BIGINT NOT NULL DEFAULT nextval('public.calificacion_id_calificacion_seq'),
                id_reserva BIGINT NOT NULL,
                puntaje INTEGER NOT NULL,
                fecha DATE NOT NULL,
                comentario VARCHAR(1000),
                fecha_creacion TIMESTAMP,
                rol_emisor VARCHAR(20),
                id_usuario BIGINT NOT NULL,
                satisfaccion_nps VARCHAR,
                CONSTRAINT calificacion_pk PRIMARY KEY (id_calificacion)
);


ALTER SEQUENCE public.calificacion_id_calificacion_seq OWNED BY public.Calificacion.id_calificacion;

ALTER TABLE public.Plan_Suscripcion ADD CONSTRAINT moneda_plan_suscripcion_fk
FOREIGN KEY (id_moneda)
REFERENCES public.Moneda (id_moneda)
ON DELETE NO ACTION
ON UPDATE NO ACTION
NOT DEFERRABLE;

ALTER TABLE public.Servicio ADD CONSTRAINT moneda_servicio_fk
FOREIGN KEY (id_moneda)
REFERENCES public.Moneda (id_moneda)
ON DELETE NO ACTION
ON UPDATE NO ACTION
NOT DEFERRABLE;

ALTER TABLE public.Usuario_Rol ADD CONSTRAINT rol_user_rol_fk
FOREIGN KEY (id_rol)
REFERENCES public.Rol (id_rol)
ON DELETE NO ACTION
ON UPDATE NO ACTION
NOT DEFERRABLE;

ALTER TABLE public.Ciudad ADD CONSTRAINT departamento_ciudad_fk
FOREIGN KEY (id_departamento)
REFERENCES public.Departamento (id_departamento)
ON DELETE NO ACTION
ON UPDATE NO ACTION
NOT DEFERRABLE;

ALTER TABLE public.Barrio ADD CONSTRAINT ciudad_barrio_fk
FOREIGN KEY (id_ciudad)
REFERENCES public.Ciudad (id_ciudad)
ON DELETE NO ACTION
ON UPDATE NO ACTION
NOT DEFERRABLE;

ALTER TABLE public.Direccion ADD CONSTRAINT barrio_direccion_fk
FOREIGN KEY (id_barrio)
REFERENCES public.Barrio (id_barrio)
ON DELETE NO ACTION
ON UPDATE NO ACTION
NOT DEFERRABLE;

ALTER TABLE public.Perfil_Empresa ADD CONSTRAINT direccion_perfil_empresa_fk
FOREIGN KEY (id_direccion)
REFERENCES public.Direccion (id_direccion)
ON DELETE NO ACTION
ON UPDATE NO ACTION
NOT DEFERRABLE;

ALTER TABLE public.Sucursal_Empresa ADD CONSTRAINT direccion_sucursal_empresa_fk
FOREIGN KEY (id_direccion)
REFERENCES public.Direccion (id_direccion)
ON DELETE NO ACTION
ON UPDATE NO ACTION
NOT DEFERRABLE;

ALTER TABLE public.Plan_Suscripcion ADD CONSTRAINT tarifa_plan_suscripcion_plan_suscripcion_fk
FOREIGN KEY (id_tarifa_plan)
REFERENCES public.Tarifa_Plan_Suscripcion (id_tarifa_plan)
ON DELETE NO ACTION
ON UPDATE NO ACTION
NOT DEFERRABLE;

ALTER TABLE public.Tarifa_Servicio ADD CONSTRAINT tarifa_servicio_tarifa_servicio_fk
FOREIGN KEY (id_tarifa)
REFERENCES public.Tipo_Tarifa_Servicio (id_tarifa)
ON DELETE NO ACTION
ON UPDATE NO ACTION
NOT DEFERRABLE;

ALTER TABLE public.Servicio ADD CONSTRAINT categoria_servicio_fk
FOREIGN KEY (id_categoria)
REFERENCES public.Categoria (id_categoria)
ON DELETE NO ACTION
ON UPDATE NO ACTION
NOT DEFERRABLE;

ALTER TABLE public.Solicitud_Servicio ADD CONSTRAINT categoria_solicitud_servicio_fk
FOREIGN KEY (id_categoria)
REFERENCES public.Categoria (id_categoria)
ON DELETE NO ACTION
ON UPDATE NO ACTION
NOT DEFERRABLE;

ALTER TABLE public.Documento ADD CONSTRAINT tipo_documento_documento_fk
FOREIGN KEY (id_tip_documento)
REFERENCES public.Tipo_Documento (id_tip_documento)
ON DELETE NO ACTION
ON UPDATE NO ACTION
NOT DEFERRABLE;

ALTER TABLE public.Perfil_Empresa ADD CONSTRAINT usuario_perfil_fk
FOREIGN KEY (id_usuario)
REFERENCES public.User (id_usuario)
ON DELETE NO ACTION
ON UPDATE NO ACTION
NOT DEFERRABLE;

ALTER TABLE public.Usuario_Rol ADD CONSTRAINT usuario_user_rol_fk
FOREIGN KEY (id_usuario)
REFERENCES public.User (id_usuario)
ON DELETE NO ACTION
ON UPDATE NO ACTION
NOT DEFERRABLE;

ALTER TABLE public.Reserva ADD CONSTRAINT users_reserva_fk
FOREIGN KEY (id_usuario)
REFERENCES public.User (id_usuario)
ON DELETE NO ACTION
ON UPDATE NO ACTION
NOT DEFERRABLE;

ALTER TABLE public.Historial_Estado ADD CONSTRAINT users_historial_estados_fk
FOREIGN KEY (id_usuario)
REFERENCES public.User (id_usuario)
ON DELETE NO ACTION
ON UPDATE NO ACTION
NOT DEFERRABLE;

ALTER TABLE public.Calificacion ADD CONSTRAINT user_calificacion_fk
FOREIGN KEY (id_usuario)
REFERENCES public.User (id_usuario)
ON DELETE NO ACTION
ON UPDATE NO ACTION
NOT DEFERRABLE;

ALTER TABLE public.Servicio ADD CONSTRAINT perfil_servicio_fk
FOREIGN KEY (id_perfil)
REFERENCES public.Perfil_Empresa (id_perfil)
ON DELETE NO ACTION
ON UPDATE NO ACTION
NOT DEFERRABLE;

ALTER TABLE public.Plan_Suscripcion ADD CONSTRAINT perfil_plan_suscripcion_fk
FOREIGN KEY (id_perfil)
REFERENCES public.Perfil_Empresa (id_perfil)
ON DELETE NO ACTION
ON UPDATE NO ACTION
NOT DEFERRABLE;

ALTER TABLE public.Verificacion_Solicitud ADD CONSTRAINT perfil_empresa_verificacion_solicitud_fk
FOREIGN KEY (id_perfil)
REFERENCES public.Perfil_Empresa (id_perfil)
ON DELETE NO ACTION
ON UPDATE NO ACTION
NOT DEFERRABLE;

ALTER TABLE public.Sucursal_Empresa ADD CONSTRAINT perfil_empresa_sucursal_empresa_fk
FOREIGN KEY (id_perfil)
REFERENCES public.Perfil_Empresa (id_perfil)
ON DELETE NO ACTION
ON UPDATE NO ACTION
NOT DEFERRABLE;

ALTER TABLE public.Solicitud_Servicio ADD CONSTRAINT perfil_empresa_solicitud_servicio_fk
FOREIGN KEY (id_perfil)
REFERENCES public.Perfil_Empresa (id_perfil)
ON DELETE NO ACTION
ON UPDATE NO ACTION
NOT DEFERRABLE;

ALTER TABLE public.Solicitud_Categoria ADD CONSTRAINT perfil_empresa_solicitud_categoria_fk
FOREIGN KEY (id_perfil)
REFERENCES public.Perfil_Empresa (id_perfil)
ON DELETE NO ACTION
ON UPDATE NO ACTION
NOT DEFERRABLE;

ALTER TABLE public.Horario_Trabajo ADD CONSTRAINT perfil_empresa_horario_trabajo_fk
FOREIGN KEY (id_perfil)
REFERENCES public.Perfil_Empresa (id_perfil)
ON DELETE NO ACTION
ON UPDATE NO ACTION
NOT DEFERRABLE;

ALTER TABLE public.Excepcion_Horario ADD CONSTRAINT perfil_empresa_excepciones_horario_fk
FOREIGN KEY (id_perfil)
REFERENCES public.Perfil_Empresa (id_perfil)
ON DELETE NO ACTION
ON UPDATE NO ACTION
NOT DEFERRABLE;

ALTER TABLE public.Documento ADD CONSTRAINT verificacion_solicitud_documento_fk
FOREIGN KEY (id_verificacion)
REFERENCES public.Verificacion_Solicitud (id_verificacion)
ON DELETE NO ACTION
ON UPDATE NO ACTION
NOT DEFERRABLE;

ALTER TABLE public.Reserva ADD CONSTRAINT servicio_reserva_fk
FOREIGN KEY (id_servicio)
REFERENCES public.Servicio (id_servicio)
ON DELETE NO ACTION
ON UPDATE NO ACTION
NOT DEFERRABLE;

ALTER TABLE public.Tarifa_Servicio ADD CONSTRAINT servicio_tarifa_servicio_fk
FOREIGN KEY (id_servicio)
REFERENCES public.Servicio (id_servicio)
ON DELETE NO ACTION
ON UPDATE NO ACTION
NOT DEFERRABLE;

ALTER TABLE public.Calificacion ADD CONSTRAINT reserva_calificacion_fk
FOREIGN KEY (id_reserva)
REFERENCES public.Reserva (id_reserva)
ON DELETE NO ACTION
ON UPDATE NO ACTION
NOT DEFERRABLE;

ALTER TABLE public.Historial_Estado ADD CONSTRAINT reserva_historial_estados_fk
FOREIGN KEY (id_reserva)
REFERENCES public.Reserva (id_reserva)
ON DELETE NO ACTION
ON UPDATE NO ACTION
NOT DEFERRABLE;
