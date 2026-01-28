from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from uuid import UUID

from ..schemas.proyecto_schema import Proyecto as ProyectoSchema, ProyectoCreate, ProyectoUpdate
from ..schemas.response_schema import ApiResponse
from ..services.proyecto_service import ProyectoService
from ..core.get_db import get_db
from ..services.auth_service import get_current_user
from ..models.cuenta import Cuenta
from ..schemas.solicitud_cuenta_schema import SolicitudDetail

router = APIRouter(
    prefix="/proyectos",
    tags=["Proyectos"],
)

@router.post("/", response_model=ApiResponse[ProyectoSchema], status_code=status.HTTP_201_CREATED)
def create_proyecto(
    proyecto: ProyectoCreate,
    db: Session = Depends(get_db),
    current_user: Cuenta = Depends(get_current_user),
):
    try:
        service = ProyectoService(db)
        nuevo_proyecto = service.create_proyecto(proyecto, current_user)
        return ApiResponse(
            code=status.HTTP_201_CREATED,
            msg="Proyecto creado exitosamente",
            data=nuevo_proyecto
        )
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error inesperado del servidor: {str(e)}")

@router.get("/", response_model=ApiResponse[List[ProyectoSchema]], status_code=status.HTTP_200_OK)
def read_proyectos(db: Session = Depends(get_db)):
    try:
        service = ProyectoService(db)
        proyectos = service.get_proyectos()
        return ApiResponse(
            code=status.HTTP_200_OK,
            msg="Lista de proyectos obtenida correctamente",
            data=proyectos
        )
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error inesperado del servidor: {str(e)}")


@router.get("/por-usuario/{usuario_uuid}", response_model=ApiResponse[List[ProyectoSchema]])
def read_proyectos_por_usuario(usuario_uuid: UUID, db: Session = Depends(get_db)):
    try:
        service = ProyectoService(db)
        proyectos = service.get_proyectos_by_usuario_uuid(str(usuario_uuid))

        return ApiResponse(
            code=status.HTTP_200_OK,
            msg="Lista de proyectos del usuario obtenida correctamente",
            data=proyectos
        )

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error inesperado del servidor: {str(e)}")


@router.get("/{proyecto_uuid}", response_model=ApiResponse[ProyectoSchema])
def read_proyecto(proyecto_uuid: UUID, db: Session = Depends(get_db)):
    try:
        service = ProyectoService(db)
        proyecto = service.get_proyecto(str(proyecto_uuid))

        return ApiResponse(
            code=status.HTTP_200_OK,
            msg="Proyecto obtenido correctamente",
            data=proyecto
        )

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error inesperado del servidor: {str(e)}")

@router.put("/{proyecto_uuid}", response_model=ApiResponse[ProyectoSchema])
def update_proyecto(
    proyecto_uuid: UUID,
    proyecto: ProyectoUpdate,
    db: Session = Depends(get_db),
    current_user: Cuenta = Depends(get_current_user),
):
    try:
        service = ProyectoService(db)
        proyecto_actualizado = service.update_proyecto(str(proyecto_uuid), proyecto, current_user)

        return ApiResponse(
            code=status.HTTP_200_OK,
            msg="Proyecto actualizado exitosamente",
            data=proyecto_actualizado
        )

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error inesperado del servidor: {str(e)}")


@router.delete("/{proyecto_uuid}", response_model=ApiResponse)
def delete_proyecto(proyecto_uuid: UUID, db: Session = Depends(get_db)):
    try:
        service = ProyectoService(db)
        service.delete_proyecto(str(proyecto_uuid))

        return ApiResponse(
            code=status.HTTP_200_OK,
            msg="Proyecto eliminado exitosamente",
            data=None
        )

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error inesperado del servidor: {str(e)}")
    

@router.post("/agregar-usuario", response_model=ApiResponse, status_code=status.HTTP_201_CREATED)
def agregar_usuario_a_proyecto(
    uuid_proyecto: str,
    uuid_usuario: str,
    db: Session = Depends(get_db)
):
    try:
        service = ProyectoService(db)
        relacion = service.agregar_usuario_al_proyecto(uuid_proyecto, uuid_usuario)

        return ApiResponse(
            code=status.HTTP_201_CREATED,
            msg="Usuario agregado correctamente al proyecto",
            data=None
        )

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error inesperado del servidor: {str(e)}"
        )

@router.get("/miembros/{proyecto_uuid}", response_model=ApiResponse[List[SolicitudDetail]])
def obtener_usuarios_por_proyecto(
    uuid_proyecto:str,
    db: Session = Depends(get_db)
):
    try:
        service = ProyectoService(db)
        usuarios = service.obtener_usuarios_por_proyecto(uuid_proyecto)
        return ApiResponse(
            code=status.HTTP_200_OK,
            msg="Lista de usuarios del proyecto obtenida correctamente",
            data=usuarios
        )

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error inesperado del servidor: {str(e)}"
        )

@router.get(
    "/next-project-number/{cuenta_uuid}",
    response_model=ApiResponse[int],
    status_code=status.HTTP_200_OK
)
def get_next_project_number(
    cuenta_uuid: UUID,
    db: Session = Depends(get_db)
):
    service = ProyectoService(db)
    next_number = service.get_next_project_number_by_cuenta(cuenta_uuid)

    return ApiResponse(
        code=status.HTTP_200_OK,
        msg="Número para el siguiente proyecto obtenido correctamente.",
        data=next_number
    )
