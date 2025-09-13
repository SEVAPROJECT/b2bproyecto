from typing import List

from sqlalchemy import BigInteger, Boolean, CHAR, CheckConstraint, Column, Computed, Date, DateTime, Double, ForeignKeyConstraint, Identity, Index, Integer, Numeric, PrimaryKeyConstraint, SmallInteger, String, Table, Text, UniqueConstraint, Uuid, text
from sqlalchemy.dialects.postgresql import JSONB, OID
from sqlalchemy.orm import Mapped, declarative_base, mapped_column, relationship
from sqlalchemy.orm.base import Mapped
from sqlalchemy.sql.sqltypes import NullType
from geoalchemy2 import Geometry

Base = declarative_base()
metadata = Base.metadata


class Users(Base):
    __tablename__ = 'users'
    __table_args__ = (
        CheckConstraint('email_change_confirm_status >= 0 AND email_change_confirm_status <= 2', name='users_email_change_confirm_status_check'),
        PrimaryKeyConstraint('id', name='users_pkey'),
        UniqueConstraint('phone', name='users_phone_key'),
        Index('confirmation_token_idx', 'confirmation_token', unique=True),
        Index('email_change_token_current_idx', 'email_change_token_current', unique=True),
        Index('email_change_token_new_idx', 'email_change_token_new', unique=True),
        Index('reauthentication_token_idx', 'reauthentication_token', unique=True),
        Index('recovery_token_idx', 'recovery_token', unique=True),
        Index('users_email_partial_key', 'email', unique=True),
        Index('users_instance_id_email_idx', 'instance_id'),
        Index('users_instance_id_idx', 'instance_id'),
        Index('users_is_anonymous_idx', 'is_anonymous'),
        {'comment': 'Auth: Stores user login data within a secure schema.',
     'schema': 'auth'}
    )

    id = mapped_column(Uuid)
    is_sso_user = mapped_column(Boolean, nullable=False, server_default=text('false'), comment='Auth: Set this column to true when the account comes from SSO. These accounts can have duplicate emails.')
    is_anonymous = mapped_column(Boolean, nullable=False, server_default=text('false'))
    instance_id = mapped_column(Uuid)
    aud = mapped_column(String(255))
    role = mapped_column(String(255))
    email = mapped_column(String(255))
    encrypted_password = mapped_column(String(255))
    email_confirmed_at = mapped_column(DateTime(True))
    invited_at = mapped_column(DateTime(True))
    confirmation_token = mapped_column(String(255))
    confirmation_sent_at = mapped_column(DateTime(True))
    recovery_token = mapped_column(String(255))
    recovery_sent_at = mapped_column(DateTime(True))
    email_change_token_new = mapped_column(String(255))
    email_change = mapped_column(String(255))
    email_change_sent_at = mapped_column(DateTime(True))
    last_sign_in_at = mapped_column(DateTime(True))
    raw_app_meta_data = mapped_column(JSONB)
    raw_user_meta_data = mapped_column(JSONB)
    is_super_admin = mapped_column(Boolean)
    created_at = mapped_column(DateTime(True))
    updated_at = mapped_column(DateTime(True))
    phone = mapped_column(Text, server_default=text('NULL::character varying'))
    phone_confirmed_at = mapped_column(DateTime(True))
    phone_change = mapped_column(Text, server_default=text("''::character varying"))
    phone_change_token = mapped_column(String(255), server_default=text("''::character varying"))
    phone_change_sent_at = mapped_column(DateTime(True))
    confirmed_at = mapped_column(DateTime(True), Computed('LEAST(email_confirmed_at, phone_confirmed_at)', persisted=True))
    email_change_token_current = mapped_column(String(255), server_default=text("''::character varying"))
    email_change_confirm_status = mapped_column(SmallInteger, server_default=text('0'))
    banned_until = mapped_column(DateTime(True))
    reauthentication_token = mapped_column(String(255), server_default=text("''::character varying"))
    reauthentication_sent_at = mapped_column(DateTime(True))
    deleted_at = mapped_column(DateTime(True))

    historial: Mapped[List['Historial']] = relationship('Historial', uselist=True, back_populates='user')
    perfil_empresa: Mapped['PerfilEmpresa'] = relationship('PerfilEmpresa', uselist=False, back_populates='user')
    reserva: Mapped[List['Reserva']] = relationship('Reserva', uselist=True, back_populates='user')


class Categoria(Base):
    __tablename__ = 'categoria'
    __table_args__ = (
        PrimaryKeyConstraint('id_categoria', name='categoria_pkey'),
    )

    id_categoria = mapped_column(BigInteger, Identity(start=1, increment=1, minvalue=1, maxvalue=9223372036854775807, cycle=False, cache=1))
    nombre = mapped_column(String(100), nullable=False)
    estado = mapped_column(Boolean, nullable=False, server_default=text('true'))
    created_at = mapped_column(DateTime(True), server_default=text('now()'))

    servicio: Mapped[List['Servicio']] = relationship('Servicio', uselist=True, back_populates='categoria')


class Departamento(Base):
    __tablename__ = 'departamento'
    __table_args__ = (
        PrimaryKeyConstraint('id_departamento', name='departamento_pkey'),
    )

    id_departamento = mapped_column(BigInteger, Identity(start=1, increment=1, minvalue=1, maxvalue=9223372036854775807, cycle=False, cache=1))
    nombre = mapped_column(String(100), nullable=False)
    created_at = mapped_column(DateTime(True), server_default=text('now()'))

    ciudad: Mapped[List['Ciudad']] = relationship('Ciudad', uselist=True, back_populates='departamento')


t_geography_columns = Table(
    'geography_columns', metadata,
    Column('f_table_catalog', String),
    Column('f_table_schema', String),
    Column('f_table_name', String),
    Column('f_geography_column', String),
    Column('coord_dimension', Integer),
    Column('srid', Integer),
    Column('type', Text)
)


t_geometry_columns = Table(
    'geometry_columns', metadata,
    Column('f_table_catalog', String(256)),
    Column('f_table_schema', String),
    Column('f_table_name', String),
    Column('f_geometry_column', String),
    Column('coord_dimension', Integer),
    Column('srid', Integer),
    Column('type', String(30))
)


class Moneda(Base):
    __tablename__ = 'moneda'
    __table_args__ = (
        PrimaryKeyConstraint('id_moneda', name='moneda_pkey'),
    )

    id_moneda = mapped_column(BigInteger, Identity(start=1, increment=1, minvalue=1, maxvalue=9223372036854775807, cycle=False, cache=1))
    codigo_iso_moneda = mapped_column(CHAR(4), nullable=False)
    nombre = mapped_column(String(50), nullable=False)
    simbolo = mapped_column(CHAR(3), nullable=False)
    created_at = mapped_column(DateTime(True), server_default=text('now()'))

    plan_suscripcion: Mapped[List['PlanSuscripcion']] = relationship('PlanSuscripcion', uselist=True, back_populates='moneda')
    servicio: Mapped[List['Servicio']] = relationship('Servicio', uselist=True, back_populates='moneda')


t_pg_stat_statements = Table(
    'pg_stat_statements', metadata,
    Column('userid', OID),
    Column('dbid', OID),
    Column('toplevel', Boolean),
    Column('queryid', BigInteger),
    Column('query', Text),
    Column('plans', BigInteger),
    Column('total_plan_time', Double(53)),
    Column('min_plan_time', Double(53)),
    Column('max_plan_time', Double(53)),
    Column('mean_plan_time', Double(53)),
    Column('stddev_plan_time', Double(53)),
    Column('calls', BigInteger),
    Column('total_exec_time', Double(53)),
    Column('min_exec_time', Double(53)),
    Column('max_exec_time', Double(53)),
    Column('mean_exec_time', Double(53)),
    Column('stddev_exec_time', Double(53)),
    Column('rows', BigInteger),
    Column('shared_blks_hit', BigInteger),
    Column('shared_blks_read', BigInteger),
    Column('shared_blks_dirtied', BigInteger),
    Column('shared_blks_written', BigInteger),
    Column('local_blks_hit', BigInteger),
    Column('local_blks_read', BigInteger),
    Column('local_blks_dirtied', BigInteger),
    Column('local_blks_written', BigInteger),
    Column('temp_blks_read', BigInteger),
    Column('temp_blks_written', BigInteger),
    Column('shared_blk_read_time', Double(53)),
    Column('shared_blk_write_time', Double(53)),
    Column('local_blk_read_time', Double(53)),
    Column('local_blk_write_time', Double(53)),
    Column('temp_blk_read_time', Double(53)),
    Column('temp_blk_write_time', Double(53)),
    Column('wal_records', BigInteger),
    Column('wal_fpi', BigInteger),
    Column('wal_bytes', Numeric),
    Column('jit_functions', BigInteger),
    Column('jit_generation_time', Double(53)),
    Column('jit_inlining_count', BigInteger),
    Column('jit_inlining_time', Double(53)),
    Column('jit_optimization_count', BigInteger),
    Column('jit_optimization_time', Double(53)),
    Column('jit_emission_count', BigInteger),
    Column('jit_emission_time', Double(53)),
    Column('jit_deform_count', BigInteger),
    Column('jit_deform_time', Double(53)),
    Column('stats_since', DateTime(True)),
    Column('minmax_stats_since', DateTime(True))
)


t_pg_stat_statements_info = Table(
    'pg_stat_statements_info', metadata,
    Column('dealloc', BigInteger),
    Column('stats_reset', DateTime(True))
)


class Rol(Base):
    __tablename__ = 'rol'
    __table_args__ = (
        PrimaryKeyConstraint('id', name='rol_pkey'),
        UniqueConstraint('nombre', name='rol_nombre_key')
    )

    id = mapped_column(Uuid, server_default=text('gen_random_uuid()'))
    nombre = mapped_column(String(100), nullable=False)
    descripcion = mapped_column(String(200))
    created_at = mapped_column(DateTime(True), server_default=text('now()'))

    usuario_rol: Mapped[List['UsuarioRol']] = relationship('UsuarioRol', uselist=True, back_populates='rol')


class SpatialRefSys(Base):
    __tablename__ = 'spatial_ref_sys'
    __table_args__ = (
        CheckConstraint('srid > 0 AND srid <= 998999', name='spatial_ref_sys_srid_check'),
        PrimaryKeyConstraint('srid', name='spatial_ref_sys_pkey')
    )

    srid = mapped_column(Integer)
    auth_name = mapped_column(String(256))
    auth_srid = mapped_column(Integer)
    srtext = mapped_column(String(2048))
    proj4text = mapped_column(String(2048))


class TarifaPlanSuscripcion(Base):
    __tablename__ = 'tarifa_plan_suscripcion'
    __table_args__ = (
        PrimaryKeyConstraint('id_tarifa_plan', name='tarifa_plan_suscripcion_pkey'),
    )

    id_tarifa_plan = mapped_column(BigInteger, Identity(start=1, increment=1, minvalue=1, maxvalue=9223372036854775807, cycle=False, cache=1))
    precio = mapped_column(Numeric(12, 0), nullable=False)
    fecha_ini_vigencia = mapped_column(Date, nullable=False)
    descuento = mapped_column(Numeric(5, 2))
    fecha_fin_vigencia = mapped_column(Date)
    created_at = mapped_column(DateTime(True), server_default=text('now()'))

    plan_suscripcion: Mapped[List['PlanSuscripcion']] = relationship('PlanSuscripcion', uselist=True, back_populates='tarifa_plan_suscripcion')


class TipoDocumento(Base):
    __tablename__ = 'tipo_documento'
    __table_args__ = (
        PrimaryKeyConstraint('id_tip_documento', name='tipo_documento_pkey'),
    )

    id_tip_documento = mapped_column(BigInteger, Identity(start=1, increment=1, minvalue=1, maxvalue=9223372036854775807, cycle=False, cache=1))
    tipo_documento = mapped_column(String(60), nullable=False)
    url_archivo = mapped_column(String(200), nullable=False)
    estado_documento = mapped_column(String(20), nullable=False)
    es_requerido = mapped_column(Boolean, nullable=False)
    fecha_subida = mapped_column(DateTime(True), nullable=False, server_default=text('now()'))
    created_at = mapped_column(DateTime(True), server_default=text('now()'))

    documento: Mapped[List['Documento']] = relationship('Documento', uselist=True, back_populates='tipo_documento')


class TipoTarifaServicio(Base):
    __tablename__ = 'tipo_tarifa_servicio'
    __table_args__ = (
        PrimaryKeyConstraint('id_tarifa', name='tipo_tarifa_servicio_pkey'),
    )

    id_tarifa = mapped_column(BigInteger, Identity(start=1, increment=1, minvalue=1, maxvalue=9223372036854775807, cycle=False, cache=1))
    nombre = mapped_column(String(50), nullable=False)
    created_at = mapped_column(DateTime(True), server_default=text('now()'))

    tarifa_servicio: Mapped[List['TarifaServicio']] = relationship('TarifaServicio', uselist=True, back_populates='tipo_tarifa_servicio')


class Ciudad(Base):
    __tablename__ = 'ciudad'
    __table_args__ = (
        ForeignKeyConstraint(['id_departamento'], ['departamento.id_departamento'], ondelete='CASCADE', name='ciudad_id_departamento_fkey'),
        PrimaryKeyConstraint('id_ciudad', name='ciudad_pkey')
    )

    id_ciudad = mapped_column(BigInteger, Identity(start=1, increment=1, minvalue=1, maxvalue=9223372036854775807, cycle=False, cache=1))
    nombre = mapped_column(String(100), nullable=False)
    id_departamento = mapped_column(BigInteger, nullable=False)
    created_at = mapped_column(DateTime(True), server_default=text('now()'))

    departamento: Mapped['Departamento'] = relationship('Departamento', back_populates='ciudad')
    barrio: Mapped[List['Barrio']] = relationship('Barrio', uselist=True, back_populates='ciudad')


class Historial(Base):
    __tablename__ = 'historial'
    __table_args__ = (
        ForeignKeyConstraint(['user_id'], ['auth.users.id'], ondelete='CASCADE', name='historial_user_id_fkey'),
        PrimaryKeyConstraint('id_historial', name='historial_pkey'),
        Index('idx_historial_user', 'user_id'),
        {'comment': 'Historial de actividades de los usuarios'}
    )

    id_historial = mapped_column(BigInteger, Identity(start=1, increment=1, minvalue=1, maxvalue=9223372036854775807, cycle=False, cache=1))
    user_id = mapped_column(Uuid, nullable=False)
    descripcion = mapped_column(String(100), nullable=False)
    fecha = mapped_column(DateTime(True), nullable=False, server_default=text('now()'))
    created_at = mapped_column(DateTime(True), server_default=text('now()'))

    user: Mapped['Users'] = relationship('Users', back_populates='historial')


class Users_(Users):
    __tablename__ = 'users'
    __table_args__ = (
        ForeignKeyConstraint(['id'], ['auth.users.id'], ondelete='CASCADE', name='users_id_fkey'),
        PrimaryKeyConstraint('id', name='users_pkey'),
        {'comment': 'Perfiles de usuario que extienden auth.users'}
    )

    id = mapped_column(Uuid)
    nombre_persona = mapped_column(Text, nullable=False)
    nombre_empresa = mapped_column(Text)
    created_at = mapped_column(DateTime(True), server_default=text('now()'))
    updated_at = mapped_column(DateTime(True), server_default=text('now()'))

    usuario_rol: Mapped[List['UsuarioRol']] = relationship('UsuarioRol', uselist=True, back_populates='users')


class Barrio(Base):
    __tablename__ = 'barrio'
    __table_args__ = (
        ForeignKeyConstraint(['id_ciudad'], ['ciudad.id_ciudad'], ondelete='CASCADE', name='barrio_id_ciudad_fkey'),
        PrimaryKeyConstraint('id_barrio', name='barrio_pkey')
    )

    id_barrio = mapped_column(BigInteger, Identity(start=1, increment=1, minvalue=1, maxvalue=9223372036854775807, cycle=False, cache=1))
    nombre = mapped_column(String(100), nullable=False)
    id_ciudad = mapped_column(BigInteger, nullable=False)
    created_at = mapped_column(DateTime(True), server_default=text('now()'))

    ciudad: Mapped['Ciudad'] = relationship('Ciudad', back_populates='barrio')
    direccion: Mapped[List['Direccion']] = relationship('Direccion', uselist=True, back_populates='barrio')


class UsuarioRol(Base):
    __tablename__ = 'usuario_rol'
    __table_args__ = (
        ForeignKeyConstraint(['id_rol'], ['rol.id'], ondelete='CASCADE', name='usuario_rol_id_rol_fkey'),
        ForeignKeyConstraint(['id_usuario'], ['users.id'], ondelete='CASCADE', name='usuario_rol_id_usuario_fkey'),
        PrimaryKeyConstraint('id_usuario', 'id_rol', name='usuario_rol_pkey')
    )

    id_usuario = mapped_column(Uuid, nullable=False)
    id_rol = mapped_column(Uuid, nullable=False)
    created_at = mapped_column(DateTime(True), server_default=text('now()'))

    rol: Mapped['Rol'] = relationship('Rol', back_populates='usuario_rol')
    users: Mapped['Users_'] = relationship('Users_', back_populates='usuario_rol')


class Direccion(Base):
    __tablename__ = 'direccion'
    __table_args__ = (
        ForeignKeyConstraint(['id_barrio'], ['barrio.id_barrio'], ondelete='CASCADE', name='direccion_id_barrio_fkey'),
        PrimaryKeyConstraint('id_direccion', name='direccion_pkey'),
        Index('idx_direccion_coordenadas', 'coordenadas'),
        {'comment': 'Direcciones con coordenadas geográficas (PostGIS)'}
    )

    id_direccion: Mapped[int] = mapped_column(
        BigInteger,
        Identity(start=1, increment=1),
        primary_key=True
    )
    calle: Mapped[str] = mapped_column(String(150), nullable=False)
    numero: Mapped[str] = mapped_column(String(20), nullable=False)
    referencia: Mapped[str] = mapped_column(String(150), nullable=False)

    # 👇 Aquí el fix: usar Geometry en lugar de NullType
    coordenadas: Mapped[str] = mapped_column(Geometry("POINT", srid=4326), nullable=False)

    id_barrio: Mapped[int] = mapped_column(BigInteger, nullable=False)
    created_at: Mapped[str] = mapped_column(DateTime(timezone=True), server_default=text('now()'))

    # Relaciones
    barrio: Mapped["Barrio"] = relationship("Barrio", back_populates="direccion")
    perfil_empresa: Mapped[List["PerfilEmpresa"]] = relationship("PerfilEmpresa", uselist=True, back_populates="direccion")
    sucursal_empresa: Mapped[List["SucursalEmpresa"]] = relationship("SucursalEmpresa", uselist=True, back_populates="direccion")


class PerfilEmpresa(Base):
    __tablename__ = 'perfil_empresa'
    __table_args__ = (
        ForeignKeyConstraint(['id_direccion'], ['direccion.id_direccion'], ondelete='SET NULL', name='perfil_empresa_id_direccion_fkey'),
        ForeignKeyConstraint(['user_id'], ['auth.users.id'], ondelete='CASCADE', name='perfil_empresa_user_id_fkey'),
        PrimaryKeyConstraint('id_perfil', name='perfil_empresa_pkey'),
        UniqueConstraint('user_id', name='perfil_empresa_user_id_key'),
        Index('idx_perfil_empresa_user', 'user_id'),
        {'comment': 'Perfiles de empresa vinculados a usuarios autenticados'}
    )

    id_perfil = mapped_column(BigInteger, Identity(start=1, increment=1, minvalue=1, maxvalue=9223372036854775807, cycle=False, cache=1))
    user_id = mapped_column(Uuid, nullable=False)
    verificado = mapped_column(Boolean, nullable=False, server_default=text('false'))
    fecha_verificacion = mapped_column(DateTime(True), nullable=False, server_default=text('now()'))
    razon_social = mapped_column(String(80), nullable=False)
    nombre_fantasia = mapped_column(String(80), nullable=False)
    estado = mapped_column(String(20), nullable=False)
    fecha_inicio = mapped_column(DateTime(True), nullable=False, server_default=text('now()'))
    id_direccion = mapped_column(BigInteger, nullable=False)
    fecha_fin = mapped_column(DateTime(True))
    created_at = mapped_column(DateTime(True), server_default=text('now()'))

    direccion: Mapped['Direccion'] = relationship('Direccion', back_populates='perfil_empresa')
    user: Mapped['Users'] = relationship('Users', back_populates='perfil_empresa')
    plan_suscripcion: Mapped[List['PlanSuscripcion']] = relationship('PlanSuscripcion', uselist=True, back_populates='perfil_empresa')
    servicio: Mapped[List['Servicio']] = relationship('Servicio', uselist=True, back_populates='perfil_empresa')
    sucursal_empresa: Mapped[List['SucursalEmpresa']] = relationship('SucursalEmpresa', uselist=True, back_populates='perfil_empresa')
    verificacion_solicitud: Mapped[List['VerificacionSolicitud']] = relationship('VerificacionSolicitud', uselist=True, back_populates='perfil_empresa')


class PlanSuscripcion(Base):
    __tablename__ = 'plan_suscripcion'
    __table_args__ = (
        ForeignKeyConstraint(['id_moneda'], ['moneda.id_moneda'], ondelete='SET NULL', name='plan_suscripcion_id_moneda_fkey'),
        ForeignKeyConstraint(['id_perfil'], ['perfil_empresa.id_perfil'], ondelete='CASCADE', name='plan_suscripcion_id_perfil_fkey'),
        ForeignKeyConstraint(['id_tarifa_plan'], ['tarifa_plan_suscripcion.id_tarifa_plan'], ondelete='SET NULL', name='plan_suscripcion_id_tarifa_plan_fkey'),
        PrimaryKeyConstraint('id_suscripcion', name='plan_suscripcion_pkey'),
        Index('idx_plan_suscripcion_perfil', 'id_perfil')
    )

    id_suscripcion = mapped_column(BigInteger, Identity(start=1, increment=1, minvalue=1, maxvalue=9223372036854775807, cycle=False, cache=1))
    nombre = mapped_column(String(50), nullable=False)
    id_tarifa_plan = mapped_column(BigInteger, nullable=False)
    estado_plan = mapped_column(Boolean, nullable=False, server_default=text('true'))
    id_perfil = mapped_column(BigInteger, nullable=False)
    id_moneda = mapped_column(BigInteger, nullable=False)
    fecha_ini_suscripcion = mapped_column(DateTime(True))
    fecha_fin_suscripcion = mapped_column(DateTime(True))
    descripcion = mapped_column(String(1000))
    created_at = mapped_column(DateTime(True), server_default=text('now()'))

    moneda: Mapped['Moneda'] = relationship('Moneda', back_populates='plan_suscripcion')
    perfil_empresa: Mapped['PerfilEmpresa'] = relationship('PerfilEmpresa', back_populates='plan_suscripcion')
    tarifa_plan_suscripcion: Mapped['TarifaPlanSuscripcion'] = relationship('TarifaPlanSuscripcion', back_populates='plan_suscripcion')


class Servicio(Base):
    __tablename__ = 'servicio'
    __table_args__ = (
        ForeignKeyConstraint(['id_categoria'], ['categoria.id_categoria'], ondelete='SET NULL', name='servicio_id_categoria_fkey'),
        ForeignKeyConstraint(['id_moneda'], ['moneda.id_moneda'], ondelete='SET NULL', name='servicio_id_moneda_fkey'),
        ForeignKeyConstraint(['id_perfil'], ['perfil_empresa.id_perfil'], ondelete='CASCADE', name='servicio_id_perfil_fkey'),
        PrimaryKeyConstraint('id_servicio', name='servicio_pkey'),
        Index('idx_servicio_categoria', 'id_categoria'),
        Index('idx_servicio_estado', 'estado'),
        Index('idx_servicio_perfil', 'id_perfil'),
        {'comment': 'Servicios ofrecidos por las empresas'}
    )

    id_servicio = mapped_column(BigInteger, Identity(start=1, increment=1, minvalue=1, maxvalue=9223372036854775807, cycle=False, cache=1))
    id_categoria = mapped_column(BigInteger, nullable=False)
    id_perfil = mapped_column(BigInteger, nullable=False)
    estado = mapped_column(Boolean, nullable=False)
    nombre = mapped_column(String(60), nullable=False)
    descripcion = mapped_column(String(500), nullable=False)
    precio = mapped_column(Double(53), nullable=False)
    id_moneda = mapped_column(BigInteger, nullable=False)
    created_at = mapped_column(DateTime(True), server_default=text('now()'))

    categoria: Mapped['Categoria'] = relationship('Categoria', back_populates='servicio')
    moneda: Mapped['Moneda'] = relationship('Moneda', back_populates='servicio')
    perfil_empresa: Mapped['PerfilEmpresa'] = relationship('PerfilEmpresa', back_populates='servicio')
    reserva: Mapped[List['Reserva']] = relationship('Reserva', uselist=True, back_populates='servicio')
    tarifa_servicio: Mapped[List['TarifaServicio']] = relationship('TarifaServicio', uselist=True, back_populates='servicio')


class SucursalEmpresa(Base):
    __tablename__ = 'sucursal_empresa'
    __table_args__ = (
        ForeignKeyConstraint(['id_direccion'], ['direccion.id_direccion'], ondelete='SET NULL', name='sucursal_empresa_id_direccion_fkey'),
        ForeignKeyConstraint(['id_perfil'], ['perfil_empresa.id_perfil'], ondelete='CASCADE', name='sucursal_empresa_id_perfil_fkey'),
        PrimaryKeyConstraint('id_sucursal', name='sucursal_empresa_pkey'),
        Index('idx_sucursal_empresa_perfil', 'id_perfil'),
        {'comment': 'Sucursales de las empresas'}
    )

    id_sucursal = mapped_column(BigInteger, Identity(start=1, increment=1, minvalue=1, maxvalue=9223372036854775807, cycle=False, cache=1))
    nombre = mapped_column(String(100), nullable=False)
    telefono = mapped_column(String(30), nullable=False)
    email = mapped_column(String(100), nullable=False)
    id_perfil = mapped_column(BigInteger, nullable=False)
    id_direccion = mapped_column(BigInteger, nullable=False)
    es_principal = mapped_column(Boolean, nullable=False, server_default=text('false'))
    created_at = mapped_column(DateTime(True), server_default=text('now()'))

    direccion: Mapped['Direccion'] = relationship('Direccion', back_populates='sucursal_empresa')
    perfil_empresa: Mapped['PerfilEmpresa'] = relationship('PerfilEmpresa', back_populates='sucursal_empresa')


class VerificacionSolicitud(Base):
    __tablename__ = 'verificacion_solicitud'
    __table_args__ = (
        ForeignKeyConstraint(['id_perfil'], ['perfil_empresa.id_perfil'], ondelete='CASCADE', name='verificacion_solicitud_id_perfil_fkey'),
        PrimaryKeyConstraint('id_verificacion', name='verificacion_solicitud_pkey'),
        Index('idx_verificacion_solicitud_perfil', 'id_perfil')
    )

    id_verificacion = mapped_column(BigInteger, Identity(start=1, increment=1, minvalue=1, maxvalue=9223372036854775807, cycle=False, cache=1))
    fecha_solicitud = mapped_column(DateTime(True), nullable=False, server_default=text('now()'))
    fecha_revision = mapped_column(DateTime(True), nullable=False, server_default=text('now()'))
    estado = mapped_column(String(20), nullable=False)
    id_perfil = mapped_column(BigInteger, nullable=False)
    comentario = mapped_column(String(1000))
    created_at = mapped_column(DateTime(True), server_default=text('now()'))

    perfil_empresa: Mapped['PerfilEmpresa'] = relationship('PerfilEmpresa', back_populates='verificacion_solicitud')
    documento: Mapped[List['Documento']] = relationship('Documento', uselist=True, back_populates='verificacion_solicitud')


class Documento(Base):
    __tablename__ = 'documento'
    __table_args__ = (
        ForeignKeyConstraint(['id_tip_documento'], ['tipo_documento.id_tip_documento'], ondelete='CASCADE', name='documento_id_tip_documento_fkey'),
        ForeignKeyConstraint(['id_verificacion'], ['verificacion_solicitud.id_verificacion'], ondelete='CASCADE', name='documento_id_verificacion_fkey'),
        PrimaryKeyConstraint('id_documento', name='documento_pkey'),
        Index('idx_documento_verificacion', 'id_verificacion')
    )

    id_documento = mapped_column(BigInteger, Identity(start=1, increment=1, minvalue=1, maxvalue=9223372036854775807, cycle=False, cache=1))
    id_tip_documento = mapped_column(BigInteger, nullable=False)
    estado_revision = mapped_column(String(20), nullable=False)
    fecha_verificacion = mapped_column(DateTime(True), nullable=False, server_default=text('now()'))
    id_verificacion = mapped_column(BigInteger, nullable=False)
    observacion = mapped_column(String(1000))
    created_at = mapped_column(DateTime(True), server_default=text('now()'))

    tipo_documento: Mapped['TipoDocumento'] = relationship('TipoDocumento', back_populates='documento')
    verificacion_solicitud: Mapped['VerificacionSolicitud'] = relationship('VerificacionSolicitud', back_populates='documento')


class Reserva(Base):
    __tablename__ = 'reserva'
    __table_args__ = (
        ForeignKeyConstraint(['id_servicio'], ['servicio.id_servicio'], ondelete='CASCADE', name='reserva_id_servicio_fkey'),
        ForeignKeyConstraint(['user_id'], ['auth.users.id'], ondelete='CASCADE', name='reserva_user_id_fkey'),
        PrimaryKeyConstraint('id_reserva', name='reserva_pkey'),
        Index('idx_reserva_servicio', 'id_servicio'),
        Index('idx_reserva_user', 'user_id'),
        {'comment': 'Reservas de servicios por parte de los clientes'}
    )

    id_reserva = mapped_column(BigInteger, Identity(start=1, increment=1, minvalue=1, maxvalue=9223372036854775807, cycle=False, cache=1))
    id_servicio = mapped_column(BigInteger, nullable=False)
    user_id = mapped_column(Uuid, nullable=False)
    descripcion = mapped_column(String(500), nullable=False)
    fecha = mapped_column(DateTime(True), nullable=False, server_default=text('now()'))
    estado = mapped_column(String(20), nullable=False)
    observacion = mapped_column(String(1000))
    created_at = mapped_column(DateTime(True), server_default=text('now()'))

    servicio: Mapped['Servicio'] = relationship('Servicio', back_populates='reserva')
    user: Mapped['Users'] = relationship('Users', back_populates='reserva')
    calificacion: Mapped[List['Calificacion']] = relationship('Calificacion', uselist=True, back_populates='reserva')


class TarifaServicio(Base):
    __tablename__ = 'tarifa_servicio'
    __table_args__ = (
        ForeignKeyConstraint(['id_servicio'], ['servicio.id_servicio'], ondelete='CASCADE', name='tarifa_servicio_id_servicio_fkey'),
        ForeignKeyConstraint(['id_tarifa'], ['tipo_tarifa_servicio.id_tarifa'], ondelete='SET NULL', name='tarifa_servicio_id_tarifa_fkey'),
        PrimaryKeyConstraint('id_tarifa_servicio', name='tarifa_servicio_pkey'),
        Index('idx_tarifa_servicio_servicio', 'id_servicio')
    )

    id_tarifa_servicio = mapped_column(BigInteger, Identity(start=1, increment=1, minvalue=1, maxvalue=9223372036854775807, cycle=False, cache=1))
    monto = mapped_column(Numeric(12, 2), nullable=False)
    descripcion = mapped_column(String(200), nullable=False)
    fecha_inicio = mapped_column(Date, nullable=False)
    id_servicio = mapped_column(BigInteger, nullable=False)
    id_tarifa = mapped_column(BigInteger, nullable=False)
    fecha_fin = mapped_column(Date)
    created_at = mapped_column(DateTime(True), server_default=text('now()'))

    servicio: Mapped['Servicio'] = relationship('Servicio', back_populates='tarifa_servicio')
    tipo_tarifa_servicio: Mapped['TipoTarifaServicio'] = relationship('TipoTarifaServicio', back_populates='tarifa_servicio')


class Calificacion(Base):
    __tablename__ = 'calificacion'
    __table_args__ = (
        CheckConstraint('puntaje >= 1 AND puntaje <= 5', name='calificacion_puntaje_check'),
        ForeignKeyConstraint(['id_reserva'], ['reserva.id_reserva'], ondelete='CASCADE', name='calificacion_id_reserva_fkey'),
        PrimaryKeyConstraint('id_calificacion', name='calificacion_pkey'),
        Index('idx_calificacion_reserva', 'id_reserva'),
        {'comment': 'Calificaciones y rese�as de los servicios'}
    )

    id_calificacion = mapped_column(BigInteger, Identity(start=1, increment=1, minvalue=1, maxvalue=9223372036854775807, cycle=False, cache=1))
    id_reserva = mapped_column(BigInteger, nullable=False)
    puntaje = mapped_column(Integer, nullable=False)
    fecha = mapped_column(DateTime(True), nullable=False, server_default=text('now()'))
    comentario = mapped_column(String(1000))
    created_at = mapped_column(DateTime(True), server_default=text('now()'))

    reserva: Mapped['Reserva'] = relationship('Reserva', back_populates='calificacion')
