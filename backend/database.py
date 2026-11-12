import os

from sqlalchemy import create_engine, Column, Integer, String, Text
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.engine import URL


DATABASE_URL = URL.create(
    drivername="mysql+pymysql",
    username=os.getenv("DB_USER", "mitorex_user"),
    password=os.getenv("DB_PASSWORD"),
    host=os.getenv("DB_HOST", "mi-mariadb"),
    port=3306,
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