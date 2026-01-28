from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID

from ..schemas.sprint_schema import (
    Sprint as SprintSchema,
    SprintCreate,
    SprintUpdate,
    SprintListItem,
    SprintBasicItem,
    AsignarHistoriaSprint,
    RemoverHistoriaSprint,
    SprintCambiarEstado,
)
from ..schemas.response_schema import ApiResponse
from ..services.sprint_service import SprintService
from ..core.get_db import get_db
from app.core.security import get_current_user
from app.models.cuenta import Cuenta


router = APIRouter(
    prefix="/sprints",
    tags=["Sprints"],
)


@router.post("/", response_model=ApiResponse[SprintSchema], status_code=status.HTTP_201_CREATED)
def create_sprint(sprint: SprintCreate, db: Session = Depends(get_db), current_user: Cuenta = Depends(get_current_user)):
    """
    Endpoint para crear un nuevo sprint.
    El Product Owner debe proporcionar:
    - Nombre del sprint
    - Fecha de inicio
    - Fecha de fin (posterior a la fecha de inicio)
    - Objetivo del sprint
    - UUID del proyecto al que pertenece
    
    El estado se establece automáticamente como PLANIFICADO.
    """
    try:
        service = SprintService(db)
        nuevo_sprint = service.create_sprint(sprint, current_user)
        return ApiResponse(
            code=status.HTTP_201_CREATED,
            msg="Sprint creado exitosamente",
            data=nuevo_sprint
        )
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error inesperado del servidor: {str(e)}"
        )


@router.get("/proyecto/{proyecto_uuid}", response_model=ApiResponse[List[SprintListItem]])
def get_sprints_by_proyecto(proyecto_uuid: UUID, db: Session = Depends(get_db), current_user: Cuenta = Depends(get_current_user)):
    """
    Obtiene todos los sprints de un proyecto específico.
    """
    try:
        service = SprintService(db)
        sprints = service.get_sprints_by_proyecto(str(proyecto_uuid), current_user)
        return ApiResponse(
            code=status.HTTP_200_OK,
            msg="Lista de sprints obtenida correctamente",
            data=sprints
        )
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error inesperado del servidor: {str(e)}"
        )


@router.get(
    "/proyecto/{proyecto_uuid}/basico",
    response_model=ApiResponse[SprintBasicItem],
    status_code=status.HTTP_200_OK,
)
def get_sprints_basic_by_proyecto(
    proyecto_uuid: UUID,
    db: Session = Depends(get_db),
    current_user: Cuenta = Depends(get_current_user)
):
    """Obtiene solo uuid y nombre de los sprints de un proyecto."""
    try:
        service = SprintService(db)
        sprint = service.get_sprint_basic_by_uuid(str(proyecto_uuid), current_user)
        return ApiResponse(
            code=status.HTTP_200_OK,
            msg="Lista básica de sprints obtenida correctamente",
            data=sprint,
        )
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error inesperado del servidor: {str(e)}"
        )


@router.put("/{sprint_uuid}", response_model=ApiResponse[SprintSchema])
def update_sprint(
    sprint_uuid: UUID,
    sprint: SprintUpdate,
    db: Session = Depends(get_db),
    current_user: Cuenta = Depends(get_current_user)
):
    """
    Actualiza un sprint existente.
    Se pueden modificar: nombre, fechas, objetivo y estado.
    """
    try:
        service = SprintService(db)
        sprint_actualizado = service.update_sprint(str(sprint_uuid), sprint, current_user)
        return ApiResponse(
            code=status.HTTP_200_OK,
            msg="Sprint actualizado exitosamente",
            data=sprint_actualizado
        )
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error inesperado del servidor: {str(e)}"
        )


@router.patch("/{sprint_uuid}/estado", response_model=ApiResponse[SprintSchema])
def cambiar_estado_sprint(
    sprint_uuid: UUID,
    data: SprintCambiarEstado,
    db: Session = Depends(get_db),
    current_user: Cuenta = Depends(get_current_user)
):
    """
    Cambia el estado de un sprint con reglas de transición y validación de creador del proyecto.
    """
    try:
        service = SprintService(db)
        sprint_actualizado = service.cambiar_estado_sprint(str(sprint_uuid), data, current_user)
        return ApiResponse(
            code=status.HTTP_200_OK,
            msg="Estado de sprint actualizado correctamente",
            data=sprint_actualizado
        )
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error inesperado del servidor: {str(e)}"
        )


@router.delete("/{sprint_uuid}", status_code=status.HTTP_200_OK)
def delete_sprint(sprint_uuid: UUID, db: Session = Depends(get_db), current_user: Cuenta = Depends(get_current_user)):
    """
    Elimina un sprint.
    """
    try:
        service = SprintService(db)
        service.delete_sprint(str(sprint_uuid), current_user)
        return ApiResponse(
            code=status.HTTP_200_OK,
            msg="Sprint eliminado exitosamente",
            data=None
        )
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error inesperado del servidor: {str(e)}"
        )


@router.post("/asignar-historia", response_model=ApiResponse, status_code=status.HTTP_200_OK)
def asignar_historia_a_sprint(data: AsignarHistoriaSprint, db: Session = Depends(get_db), current_user: Cuenta = Depends(get_current_user)):
    try:
        service = SprintService(db)
        historia = service.asignar_historia_a_sprint(data, current_user)
        return ApiResponse(
            code=status.HTTP_200_OK,
            msg="Historia asignada al sprint correctamente",
            data={
                "historia_uuid": historia.uuid,
                "sprint_uuid": data.sprint_uuid,
            }
        )
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error inesperado del servidor: {str(e)}"
        )


@router.post("/remover-historia", response_model=ApiResponse, status_code=status.HTTP_200_OK)
def remover_historia_de_sprint(data: RemoverHistoriaSprint, db: Session = Depends(get_db), current_user: Cuenta = Depends(get_current_user)):
    try:
        service = SprintService(db)
        historia = service.remover_historia_de_sprint(data, current_user)
        return ApiResponse(
            code=status.HTTP_200_OK,
            msg="Historia removida del sprint correctamente",
            data={
                "historia_uuid": historia.uuid,
                "sprint_uuid": data.sprint_uuid,
            }
        )
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error inesperado del servidor: {str(e)}"
        )
