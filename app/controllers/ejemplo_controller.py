from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from ..schemas.ejemplo_schema import EjemploCreate, EjemploResponse
from ..services.ejemplo_service import EjemploService
from app.core.get_db import get_db

class rol_controller:
    router = APIRouter(prefix="/ejemplos", tags=["Ejemplo"])

    @router.post("/", response_model=EjemploResponse, status_code=status.HTTP_201_CREATED)
    def crear_ejemplo(datos: EjemploCreate, db: Session = Depends(get_db)):
        servicio = EjemploService(db)
        nuevo = servicio.crear_ejemplo(datos)
        return nuevo

    @router.get("/")
    def listar_ejemplos(db: Session = Depends(get_db)): #esto es solo un ejemplo usen un responsemodel para sanitizar la salida de su solicitud :)
        servicio = EjemploService(db)
        ejemplos = servicio.obtener_todos()
        return {"msg": "ok funciona el ejemplo", "ejemplos": ejemplos}
