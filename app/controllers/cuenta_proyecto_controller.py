from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.get_db import get_db
from app.services.cuenta_proyecto_service import cuenta_proyecto_service
from app.schemas.cuenta_proyecto_schema import CuentaProyectoBase, CuentaProyectoResponse

class cuenta_proyecto_controller:
    router = APIRouter(
        prefix="/cuenta-proyectos",
        tags=["Cuenta-Proyectos"]
    )
    
    @router.get("/", response_model=list)
    def listar_cuentas_proyecto(db: Session = Depends(get_db)):
        service = cuenta_proyecto_service(db)
        cuentas_proyecto = service.listar_cuentas_proyecto()

        respuesta = []
        for cp in cuentas_proyecto:
            respuesta.append({
                "uuid": cp.uuid,
                "cuenta_uuid": cp.cuenta.uuid if cp.cuenta else None,
                "proyecto_uuid": cp.proyecto.uuid if cp.proyecto else None,
                "rol_proyecto_uuid": cp.rol_proyecto.uuid if cp.rol_proyecto else None
            })

        return respuesta

    @router.get("/obtener_unica", response_model=CuentaProyectoResponse)
    def obtener_cuenta_proyecto(uuid_usuario: str, uuid_proyecto: str, db: Session = Depends(get_db)):
        service = cuenta_proyecto_service(db)
        cuenta_proyecto = service.obtener_cuenta_proyecto(uuid_usuario, uuid_proyecto)
        return cuenta_proyecto