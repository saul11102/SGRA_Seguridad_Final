from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from sqlalchemy.orm import Session

from app.core.get_db import get_db
from app.services.rol_service import rol_service
from app.schemas.response_schema import ApiResponse
from app.schemas.rol_schema import Rol as RolSchema

class rol_controller:
    router = APIRouter(prefix="/rol", tags=["Rol"])

    @router.get('/roles', response_model=ApiResponse[List[RolSchema]], status_code=status.HTTP_200_OK)
    def list_roles(db: Session = Depends(get_db)):
        """Devuelve todos los roles del sistema."""
        try:
            roles = rol_service.get_roles(db)
            return ApiResponse(
                code=status.HTTP_200_OK,
                msg="Lista de roles obtenida correctamente",
                data=roles
            )
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error inesperado del servidor: {str(e)}")
