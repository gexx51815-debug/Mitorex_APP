import hashlib
from typing import Literal, Optional

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from database import engine, Base, get_db, DBNegocio, DBUsuario

app = FastAPI(title="Mitorex APP - API de negocios")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

Base.metadata.create_all(bind=engine)


def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


# --- Esquemes Pydantic ---

class UsuarioRegistro(BaseModel):
    nombre: str = Field(min_length=2, max_length=100)
    apellidos: str = Field(min_length=2, max_length=150)
    correo: str = Field(min_length=5, max_length=100)
    password: str = Field(min_length=4, max_length=100)


class UsuarioLogin(BaseModel):
    correo: str
    password: str


class NegocioEntrada(BaseModel):
    nombre: str = Field(min_length=2, max_length=100)
    categoria: str
    ubicacion: str
    descripcion: str
    telefono: str = ""
    correo: str = ""
    web: str = ""
    usuario_id: Optional[int] = None


EstadoNegocio = Literal["pendiente", "aprobado", "rechazado"]


# --- Endpoints Generals i Públics ---

@app.get("/")
def inicio():
    return {
        "mensaje": "Mitorex APP funciona",
        "seccion": "Perfiles de negocios y propietarios",
    }


@app.get("/negocios")
def listar_negocios(db: Session = Depends(get_db)):
    return db.query(DBNegocio).filter(DBNegocio.estado == "aprobado").all()


@app.post("/negocios")
def crear_negocio(negocio: NegocioEntrada, db: Session = Depends(get_db)):
    nuevo_negocio = DBNegocio(**negocio.model_dump())
    db.add(nuevo_negocio)
    db.commit()
    db.refresh(nuevo_negocio)
    return nuevo_negocio


# --- Endpoints de Propietaris (Usuaris) ---

@app.post("/usuarios/registro")
def registrar_usuario(datos: UsuarioRegistro, db: Session = Depends(get_db)):
    existente = db.query(DBUsuario).filter(DBUsuario.correo == datos.correo).first()
    if existente:
        raise HTTPException(status_code=400, detail="Aquest correu ja està registrat")

    nuevo_usuario = DBUsuario(
        nombre=datos.nombre,
        apellidos=datos.apellidos,
        correo=datos.correo,
        password=hash_password(datos.password),
        rol="propietario",
    )
    db.add(nuevo_usuario)
    db.commit()
    db.refresh(nuevo_usuario)
    return {
        "id": nuevo_usuario.id,
        "nombre": nuevo_usuario.nombre,
        "apellidos": nuevo_usuario.apellidos,
        "correo": nuevo_usuario.correo,
        "rol": nuevo_usuario.rol,
    }


@app.post("/usuarios/login")
def login_usuario(datos: UsuarioLogin, db: Session = Depends(get_db)):
    usuario = db.query(DBUsuario).filter(DBUsuario.correo == datos.correo).first()
    if not usuario or usuario.password != hash_password(datos.password):
        raise HTTPException(status_code=401, detail="Correu o contrasenya incorrectes")

    return {
        "id": usuario.id,
        "nombre": usuario.nombre,
        "apellidos": usuario.apellidos,
        "correo": usuario.correo,
        "rol": usuario.rol,
    }


@app.get("/usuarios/{usuario_id}/negocios")
def listar_negocios_usuario(usuario_id: int, db: Session = Depends(get_db)):
    return db.query(DBNegocio).filter(DBNegocio.usuario_id == usuario_id).all()


@app.put("/usuarios/{usuario_id}/negocios/{negocio_id}")
def editar_negocio_propietario(
    usuario_id: int,
    negocio_id: int,
    datos: NegocioEntrada,
    db: Session = Depends(get_db),
):
    negocio = (
        db.query(DBNegocio)
        .filter(DBNegocio.id == negocio_id, DBNegocio.usuario_id == usuario_id)
        .first()
    )
    if not negocio:
        raise HTTPException(
            status_code=404,
            detail="Negoci no trobat o no tens permisos per editar-lo",
        )

    campos = datos.model_dump(exclude={"usuario_id"})
    for campo, valor in campos.items():
        setattr(negocio, campo, valor)

    db.commit()
    db.refresh(negocio)
    return negocio


# --- Endpoints d'Administració ---

@app.get("/admin/negocios")
def listar_todos_los_negocios(db: Session = Depends(get_db)):
    return db.query(DBNegocio).all()


@app.patch("/admin/negocios/{negocio_id}/estado")
def cambiar_estado(
    negocio_id: int,
    estado: EstadoNegocio,
    db: Session = Depends(get_db),
):
    negocio = db.query(DBNegocio).filter(DBNegocio.id == negocio_id).first()
    if not negocio:
        raise HTTPException(
            status_code=404,
            detail="Negoci no trobat",
        )
    negocio.estado = estado
    db.commit()
    db.refresh(negocio)
    return negocio


@app.put("/admin/negocios/{negocio_id}")
def editar_negocio(
    negocio_id: int,
    datos: NegocioEntrada,
    db: Session = Depends(get_db),
):
    negocio = db.query(DBNegocio).filter(DBNegocio.id == negocio_id).first()
    if not negocio:
        raise HTTPException(
            status_code=404,
            detail="Negoci no trobat",
        )
    for campo, valor in datos.model_dump().items():
        setattr(negocio, campo, valor)
    db.commit()
    db.refresh(negocio)
    return negocio


@app.delete("/admin/negocios/{negocio_id}")
def eliminar_negocio(negocio_id: int, db: Session = Depends(get_db)):
    negocio = db.query(DBNegocio).filter(DBNegocio.id == negocio_id).first()
    if not negocio:
        raise HTTPException(
            status_code=404,
            detail="Negoci no trobat",
        )
    db.delete(negocio)
    db.commit()
    return {"mensaje": f"Negoci #{negocio_id} eliminat correctament"}