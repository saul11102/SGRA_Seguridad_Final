from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..schemas.proyecto_schema import Proyecto, ProyectoCreate
from ..services.proyecto_service import ProyectoService
from ..core.get_db import get_db

router = APIRouter(
    prefix="/proyectos",
    tags=["proyectos"],
    responses={404: {"description": "Not found"}},
)

@router.post("/", response_model=Proyecto)
def create_proyecto(proyecto: ProyectoCreate, db: Session = Depends(get_db)):
    service = ProyectoService(db)
    return service.create_proyecto(proyecto)

@router.get("/", response_model=list[Proyecto])
def read_proyectos(db: Session = Depends(get_db)):
    service = ProyectoService(db)
    return service.get_proyectos()

@router.get("/{proyecto_id}", response_model=Proyecto)
def read_proyecto(proyecto_id: int, db: Session = Depends(get_db)):
    service = ProyectoService(db)
    db_proyecto = service.get_proyecto(proyecto_id)
    if db_proyecto is None:
        raise HTTPException(status_code=404, detail="Proyecto not found")
    return db_proyecto
