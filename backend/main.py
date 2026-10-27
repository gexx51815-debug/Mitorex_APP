
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI(title="Mitorex APP")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class Producto(BaseModel):
    nombre: str
    precio: float
    cantidad: int


productos = [
    {
        "id": 1,
        "nombre": "Mitroex gratuit",
        "precio": 85.99,
        "cantidad": 100,
    }
]


@app.get("/")
def inicio():
    return {"mensaje": "¡Mitorex APP funciona!"}


@app.get("/productos")
def listar_productos():
    return productos


@app.post("/productos")
def crear_producto(producto: Producto):
    nuevo_id = max(
        (p["id"] for p in productos),
        default=0,
    ) + 1

    nuevo_producto = {
        "id": nuevo_id,
        **producto.model_dump(),
    }

    productos.append(nuevo_producto)
    return nuevo_producto


@app.put("/productos/{producto_id}")
def editar_producto(producto_id: int, producto: Producto):
    for i, existente in enumerate(productos):
        if existente["id"] == producto_id:
            productos[i] = {
                "id": producto_id,
                **producto.model_dump(),
            }
            return productos[i]

    raise HTTPException(
        status_code=404,
        detail="Producto no encontrado",
    )


@app.delete("/productos/{producto_id}")
def eliminar_producto(producto_id: int):
    for i, producto in enumerate(productos):
        if producto["id"] == producto_id:
            return productos.pop(i)

    raise HTTPException(
        status_code=404,
        detail="Producto no encontrado",
    )
