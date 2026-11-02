from typing import Literal

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

app = FastAPI(title="Mitorex APP - API de negocios")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class NegocioEntrada(BaseModel):
    nombre: str = Field(min_length=2, max_length=100)
    categoria: str
    ubicacion: str
    descripcion: str
    telefono: str = ""
    correo: str = ""
    web: str = ""

    
EstadoNegocio = Literal["pendiente", "aprobado", "rechazado"]


negocios = [
    {
        "id": 1,
        "nombre": "Perruqueria Maria",
        "categoria": "Perruquería",
        "ubicacion": "Terrassa",
        "descripcion": "Servicios de peluquería para todos los públicos.",
        "telefono": "",
        "correo": "",
        "web": "",
        "estado": "aprobado",
    }
]


@app.get("/")
def inicio():
    return {
        "mensaje": "Mitorex APP funciona",
        "seccion": "Perfiles de negocios",
    }


@app.get("/negocios")
def listar_negocios():
    return [
        negocio
        for negocio in negocios
        if negocio["estado"] == "aprobado"
    ]


@app.post("/negocios")
def crear_negocio(negocio: NegocioEntrada):
    nuevo_id = max(
        (n["id"] for n in negocios),
        default=0,
    ) + 1

    nuevo_negocio = {
        "id": nuevo_id,
        **negocio.model_dump(),
        "estado": "pendiente",
    }

    negocios.append(nuevo_negocio)
    return nuevo_negocio


@app.get("/admin/negocios")
def listar_todos_los_negocios():
    return negocios


@app.patch("/admin/negocios/{negocio_id}/estado")
def cambiar_estado(
    negocio_id: int,
    estado: EstadoNegocio,
):
    for negocio in negocios:
        if negocio["id"] == negocio_id:
            negocio["estado"] = estado
            return negocio

    raise HTTPException(
        status_code=404,
        detail="Negocio no encontrado",
    )


@app.put("/admin/negocios/{negocio_id}")
def editar_negocio(
    negocio_id: int,
    datos: NegocioEntrada,
):

    for i, negocio in enumerate(negocios):

        if negocio["id"] == negocio_id:

            negocios[i] = {
                "id": negocio_id,
                **datos.model_dump(),
                "estado": negocio["estado"],
            }

            return negocios[i]

    raise HTTPException(
        status_code=404,
        detail="Negocio no encontrado",
    )