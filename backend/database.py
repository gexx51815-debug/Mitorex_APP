import os

from sqlalchemy import create_engine, Column, Integer, String, Text, Boolean, ForeignKey
from sqlalchemy.orm import sessionmaker, declarative_base, relationship
from sqlalchemy.engine import URL


DATABASE_URL = URL.create(
    drivername="mysql+pymysql",
    username=os.getenv("DB_USER", "mitorex_user"),
    password=os.getenv("DB_PASSWORD"),
    host=os.getenv("DB_HOST", "mi-mariadb"),
    port=int(os.getenv("DB_PORT", 3306)),
    database=os.getenv("DB_NAME", "mitorex"),
)

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)

Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


class DBUsuario(Base):
    __tablename__ = "usuarios"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(100), nullable=False)
    apellidos = Column(String(150), nullable=False, default="")
    correo = Column(String(100), unique=True, index=True, nullable=False)
    password = Column(String(255), nullable=False)
    rol = Column(String(20), nullable=False, default="propietario")

    negocios = relationship("DBNegocio", back_populates="propietario")


class DBNegocio(Base):
    __tablename__ = "negocios"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(100), nullable=False)
    categoria = Column(String(50), nullable=False)
    ubicacion = Column(String(100), nullable=False)
    descripcion = Column(Text, nullable=False)
    telefono = Column(String(20), default="")
    correo = Column(String(100), default="")
    web = Column(String(150), default="")
    estado = Column(String(20), default="pendiente")
    servicios_activos = Column(Boolean, default=False, nullable=False)
    auto_aceptar = Column(Boolean, default=False, nullable=False)
    horario = Column(String(255), default="", nullable=False)
    usuario_id = Column(Integer, ForeignKey("usuarios.id"), nullable=True)

    propietario = relationship("DBUsuario", back_populates="negocios")
    solicitudes = relationship("DBSolicitud", back_populates="negocio", cascade="all, delete-orphan")


class DBSolicitud(Base):
    __tablename__ = "solicitudes"

    id = Column(Integer, primary_key=True, index=True)
    negocio_id = Column(Integer, ForeignKey("negocios.id"), nullable=False)
    cliente_nombre = Column(String(100), nullable=False)
    cliente_contacto = Column(String(100), nullable=False)
    fecha_reserva = Column(String(20), default="", nullable=False)
    hora_reserva = Column(String(10), default="", nullable=False)
    mensaje = Column(Text, nullable=False)
    estado = Column(String(20), default="pendiente", nullable=False)

    negocio = relationship("DBNegocio", back_populates="solicitudes")