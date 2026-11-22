from typing import Literal

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from database import engine, Base, get_db, DBNegocio

app = FastAPI(title="Mitorex APP - API de negocios")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

Base.metadata.create_all(bind=engine)


class NegocioEntrada(BaseModel):
    nombre: str = Field(min_length=2, max_length=100)
    categoria: str
    ubicacion: str
    descripcion: str
    telefono: str = ""
    correo: str = ""
    web: str = ""


EstadoNegocio = Literal["pendiente", "aprobado", "rechazado"]


@app.get("/")
def inicio():
    return {
        "mensaje": "Mitorex APP funciona",
        "seccion": "Perfiles de negocios",
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
            detail="Negocio no encontrado",
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
            detail="Negocio no encontrado",
        )
    for campo, valor in datos.model_dump().items():
        setattr(negocio, campo, valor)
    db.commit()
    db.refresh(negocio)
    return negocio