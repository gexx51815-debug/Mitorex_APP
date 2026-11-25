import hashlib
import re
from datetime import datetime
from typing import Literal, Optional

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from database import engine, Base, get_db, DBNegocio, DBUsuario, DBSolicitud

app = FastAPI(title="Mitorex APP - API de negocios")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

Base.metadata.create_all(bind=engine)

DIAS_MAP = ["Dl", "Dt", "Dc", "Dj", "Dv", "Ds", "Dg"]


def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def hora_a_minutos(hhmm: str) -> int:
    h, m = map(int, hhmm.split(":"))
    return h * 60 + m


def minutos_a_hora(mins: int) -> str:
    return f"{mins // 60:02d}:{mins % 60:02d}"


def evaluar_disponibilidad(negocio: DBNegocio, fecha: str, hora: str, db: Session) -> dict:
    try:
        fecha_dt = datetime.strptime(fecha, "%Y-%m-%d")
        mins_solicitados = hora_a_minutos(hora)
    except ValueError:
        return {
            "disponible": False,
            "mensaje_asistente": "⚠️ Format de data o hora no vàlid.",
            "horas_libres": [],
        }

    dia_codigo = DIAS_MAP[fecha_dt.weekday()]
    horario_texto = negocio.horario or ""

    # Comprovar si obre aquest dia de la setmana
    dias_abiertos = [d for d in DIAS_MAP if d in horario_texto]
    if dias_abiertos and dia_codigo not in dias_abiertos:
        return {
            "disponible": False,
            "mensaje_asistente": f"🤖 Ho sento, aquest negoci no obre els {dia_codigo}. Dies disponibles: {', '.join(dias_abiertos)}.",
            "horas_libres": [],
        }

    # Extreure franges horàries (ex: 09:00 - 14:00 i 16:30 - 20:00)
    horas_encontradas = re.findall(r"\d{2}:\d{2}", horario_texto)
    intervalos = []
    for i in range(0, len(horas_encontradas) - 1, 2):
        inicio = hora_a_minutos(horas_encontradas[i])
        fin = hora_a_minutos(horas_encontradas[i + 1])
        if fin > inicio:
            intervalos.append((inicio, fin))

    # Si no hi ha hores definides (ex: "Consultar disponibilitat"), fem franja estàndard 09:00 - 19:00
    if not intervalos:
        intervalos = [(9 * 60, 19 * 60)]

    # Generar tots els torns possibles cada 30 minuts dins l'horari comercial
    slots_totales = []
    for inicio, fin in intervalos:
        actual = inicio
        while actual + 30 <= fin:
            slots_totales.append(minutos_a_hora(actual))
            actual += 30

    # Consultar reserves ja existents per aquell dia (pendents o acceptades)
    reservas_dia = (
        db.query(DBSolicitud)
        .filter(
            DBSolicitud.negocio_id == negocio.id,
            DBSolicitud.fecha_reserva == fecha,
            DBSolicitud.estado != "rechazado",
        )
        .all()
    )
    horas_ocupadas = {r.hora_reserva for r in reservas_dia if r.hora_reserva}
    horas_libres = [s for s in slots_totales if s not in horas_ocupadas]

    # Comprovar si l'hora demanada cau dins l'horari d'obertura
    dentro_horario = any(inicio <= mins_solicitados <= fin - 30 for inicio, fin in intervalos)
    if not dentro_horario:
        sugerencias = horas_libres[:6]
        return {
            "disponible": False,
            "mensaje_asistente": f"🤖 A les {hora} el negoci està tancat. Horari: {horario_texto or '09:00 - 19:00'}.",
            "horas_libres": sugerencias,
        }

    # Comprovar si ja està ocupada per un altre client
    if hora in horas_ocupadas:
        sugerencias = horas_libres[:6]
        return {
            "disponible": False,
            "mensaje_asistente": f"🤖 Les {hora} del {fecha} ja estan ocupades. Selecciona una de les hores lliures:",
            "horas_libres": sugerencias,
        }

    modo = "Es confirmarà automàticament!" if negocio.auto_aceptar else "El negoci rebrà la petició a l'instant."
    return {
        "disponible": True,
        "mensaje_asistente": f"✅ Disponible! El {fecha} a les {hora} està lliure. {modo}",
        "horas_libres": horas_libres[:6],
    }


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
    servicios_activos: bool = False
    auto_aceptar: bool = False
    horario: str = ""
    usuario_id: Optional[int] = None


class SolicitudEntrada(BaseModel):
    cliente_nombre: str = Field(min_length=2, max_length=100)
    cliente_contacto: str = Field(min_length=4, max_length=100)
    fecha_reserva: str = Field(min_length=8, max_length=20)
    hora_reserva: str = Field(min_length=4, max_length=10)
    mensaje: str = ""


EstadoNegocio = Literal["pendiente", "aprobado", "rechazado"]
EstadoSolicitud = Literal["pendiente", "aceptado", "rechazado"]


# --- Endpoints Generals i Públics ---

@app.get("/")
def inicio():
    return {
        "mensaje": "Mitorex APP funciona",
        "seccion": "Perfiles de negocios, propietarios y asistente de reservas",
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


@app.get("/negocios/{negocio_id}/disponibilidad")
def consultar_disponibilidad(
    negocio_id: int,
    fecha: str,
    hora: str,
    db: Session = Depends(get_db),
):
    negocio = db.query(DBNegocio).filter(DBNegocio.id == negocio_id).first()
    if not negocio:
        raise HTTPException(status_code=404, detail="Negoci no trobat")

    return evaluar_disponibilidad(negocio, fecha, hora, db)


@app.post("/negocios/{negocio_id}/solicitudes")
def crear_solicitud(
    negocio_id: int,
    solicitud: SolicitudEntrada,
    db: Session = Depends(get_db),
):
    negocio = db.query(DBNegocio).filter(DBNegocio.id == negocio_id).first()
    if not negocio:
        raise HTTPException(status_code=404, detail="Negoci no trobat")
    if not negocio.servicios_activos:
        raise HTTPException(status_code=400, detail="Aquest negoci no té les reserves actives")

    chequeo = evaluar_disponibilidad(negocio, solicitud.fecha_reserva, solicitud.hora_reserva, db)
    if not chequeo["disponible"]:
        raise HTTPException(status_code=409, detail=chequeo["mensaje_asistente"])

    estado_inicial = "aceptado" if negocio.auto_aceptar else "pendiente"

    nueva = DBSolicitud(
        negocio_id=negocio_id,
        cliente_nombre=solicitud.cliente_nombre,
        cliente_contacto=solicitud.cliente_contacto,
        fecha_reserva=solicitud.fecha_reserva,
        hora_reserva=solicitud.hora_reserva,
        mensaje=solicitud.mensaje.strip() or "Reserva d'hora",
        estado=estado_inicial,
    )
    db.add(nueva)
    db.commit()
    db.refresh(nueva)
    return nueva


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


@app.get("/usuarios/{usuario_id}/solicitudes")
def listar_solicitudes_propietario(usuario_id: int, db: Session = Depends(get_db)):
    solicitudes = (
        db.query(DBSolicitud)
        .join(DBNegocio)
        .filter(DBNegocio.usuario_id == usuario_id)
        .order_by(DBSolicitud.id.desc())
        .all()
    )
    return [
        {
            "id": s.id,
            "negocio_id": s.negocio_id,
            "negocio_nombre": s.negocio.nombre,
            "cliente_nombre": s.cliente_nombre,
            "cliente_contacto": s.cliente_contacto,
            "fecha_reserva": s.fecha_reserva,
            "hora_reserva": s.hora_reserva,
            "mensaje": s.mensaje,
            "estado": s.estado,
        }
        for s in solicitudes
    ]


@app.patch("/usuarios/{usuario_id}/solicitudes/{solicitud_id}/estado")
def responder_solicitud(
    usuario_id: int,
    solicitud_id: int,
    estado: EstadoSolicitud,
    db: Session = Depends(get_db),
):
    solicitud = (
        db.query(DBSolicitud)
        .join(DBNegocio)
        .filter(DBSolicitud.id == solicitud_id, DBNegocio.usuario_id == usuario_id)
        .first()
    )
    if not solicitud:
        raise HTTPException(status_code=404, detail="Sol·licitud no trobada")

    solicitud.estado = estado
    db.commit()
    db.refresh(solicitud)
    return {"id": solicitud.id, "estado": solicitud.estado}


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
        raise HTTPException(status_code=404, detail="Negoci no trobat")
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
        raise HTTPException(status_code=404, detail="Negoci no trobat")
    for campo, valor in datos.model_dump().items():
        setattr(negocio, campo, valor)
    db.commit()
    db.refresh(negocio)
    return negocio


@app.delete("/admin/negocios/{negocio_id}")
def eliminar_negocio(negocio_id: int, db: Session = Depends(get_db)):
    negocio = db.query(DBNegocio).filter(DBNegocio.id == negocio_id).first()
    if not negocio:
        raise HTTPException(status_code=404, detail="Negoci no trobat")
    db.delete(negocio)
    db.commit()
    return {"mensaje": f"Negoci #{negocio_id} eliminat correctament"}