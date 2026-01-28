from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.orm import Session
from typing import List

from ..schemas.ejemplo_schema import EjemploCreate, EjemploResponse
from ..schemas.response_schema import ApiResponse
from ..services.ejemplo_service import EjemploService
from app.core.get_db import get_db
from app.utils.utils import require_project_permission
from app.core.security import get_current_user
from app.models.cuenta import Cuenta

class ejemplo_controller:
    router = APIRouter(prefix="/ejemplos", tags=["Ejemplo"])

    @router.post(
    "/",
    response_model=ApiResponse[EjemploResponse],
    status_code=status.HTTP_201_CREATED,
    dependencies=[
        Depends(require_project_permission("historia:"))
    ]
)
    def crear_ejemplo(
        datos: EjemploCreate,
        db: Session = Depends(get_db),
        current_user: Cuenta = Depends(get_current_user)
    ):
        servicio = EjemploService(db)
        nuevo = servicio.crear_ejemplo(datos)

        return ApiResponse(
            code=status.HTTP_201_CREATED,
            msg="Ejemplo creado exitosamente",
            data=nuevo
        )

    @router.get("/", response_model=ApiResponse[List[EjemploResponse]], status_code=status.HTTP_200_OK)
    def listar_ejemplos(db: Session = Depends(get_db)):
        try:
            servicio = EjemploService(db)
            ejemplos = servicio.obtener_todos()
            return ApiResponse(
                code=status.HTTP_200_OK,
                msg="Ejemplos obtenidos correctamente",
                data=ejemplos
            )
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error inesperado del servidor: {str(e)}")
