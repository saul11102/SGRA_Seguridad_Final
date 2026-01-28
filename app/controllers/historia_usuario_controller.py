from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from typing import Optional, List

from app.core.get_db import get_db
from app.core.security import get_current_user
from app.schemas.historia_usuario_schema import (
    HistoriaUsuarioCreate,
    HistoriaUsuario as HistoriaUsuarioSchema,
    HistoriaUsuarioListItem,
    HistoriaUsuarioListResponse,
    CreadorInfo,
    RequisitoInfo,
    EliminarHistoriaUsuario,
    EditarHistoriaUsuario,
    Schema_CambiarEstadoHistoriaUsuario,
    HistoriaUsuarioResponse,
    HistoriaUsuarioAgregarASprint,
    HistoriaUsuarioQuitarDeSprint,
    HistorialHistoriaUsuarioResponse,
)
from app.schemas.response_schema import ApiResponse
from app.services.historia_usuario_service import HistoriaUsuarioService
from app.models.cuenta import Cuenta
from app.models.enums.estado_historia_usuario_enum import Estado
from app.models.enums.prioridad_historia_usuario import Prioridad


class historia_usuario_controller:
    router = APIRouter(
        prefix="/historias_usuario",
        tags=["HistoriaUsuario"]
    )

@historia_usuario_controller.router.post("/crear",
    response_model=ApiResponse[HistoriaUsuarioResponse],
    status_code=status.HTTP_201_CREATED)
def create_historia_usuario(
    historia: HistoriaUsuarioCreate,
    db: Session = Depends(get_db),
    current_user: Cuenta = Depends(get_current_user)):
    try:
        service = HistoriaUsuarioService(db)
        nueva_historia = service.create_historia_usuario(historia, current_user)

        return ApiResponse(
            code=status.HTTP_201_CREATED,
            msg="Historia de usuario creada correctamente",
            data=nueva_historia
        )

    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error inesperado del servidor: {str(e)}"
        )


@historia_usuario_controller.router.delete(
    "/eliminar",
    response_model=ApiResponse,
    status_code=status.HTTP_200_OK
)
def eliminar_historia_usuario(
    datos: EliminarHistoriaUsuario,
    db: Session = Depends(get_db),
    current_user: Cuenta = Depends(get_current_user)
):
    try:
        service = HistoriaUsuarioService(db)
        service.eliminar_historia_usuario(datos.uuid_historia, current_user)

        return ApiResponse(
            code=status.HTTP_200_OK,
            msg="Historia de usuario eliminada correctamente"
        )

    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error inesperado del servidor: {str(e)}"
        )

@historia_usuario_controller.router.get("/listar/{proyecto_uuid}", response_model=ApiResponse[HistoriaUsuarioListResponse], status_code=status.HTTP_200_OK)
def listar_historias_usuario(
    proyecto_uuid: str,
    page: Optional[int] = Query(1, ge=1, description="Número de página"),
    page_size: Optional[int] = Query(10, ge=1, le=100, description="Tamaño de página"),
    prioridad: Optional[Prioridad] = Query(None, description="Filtrar por prioridad"),
    estado: Optional[Estado] = Query(None, description="Filtrar por estado"),
    sprint_uuid: Optional[str] = Query(None, description="Filtrar por UUID del sprint"),
    db: Session = Depends(get_db),
    current_user: Cuenta = Depends(get_current_user)
):
    try:
        skip = (page - 1) * page_size
        limit = page_size

        service = HistoriaUsuarioService(db)
        historias, total = service.listar_por_proyecto(
            proyecto_uuid, 
            skip, 
            limit, 
            current_user, 
            prioridad=prioridad, 
            estado=estado,
            sprint_uuid=sprint_uuid
        )
        historias_schema: list[HistoriaUsuarioListItem] = []

        for historia in historias:
            solicitud = historia.creado_por.solicitud if historia.creado_por else None
            creador = CreadorInfo(
                uuid=historia.creado_por.uuid if historia.creado_por else None,
                nombre=solicitud.nombre if solicitud else None,
                apellido=solicitud.apellido if solicitud else None,
            )

            requisitos_info = [
                RequisitoInfo(uuid=req.uuid, identificador=req.identificador)
                for req in historia.requisitos
            ]

            historias_schema.append(
                HistoriaUsuarioListItem(
                    uuid=historia.uuid,
                    titulo=historia.titulo,
                    identificador=historia.identificador,
                    descripcion=historia.descripcion,
                    prioridad=historia.prioridad,
                    estado=historia.estado,
                    estimacion=historia.estimacion,
                    criterios_aceptacion=historia.criterios_aceptacion,
                    fecha_creacion=historia.fecha_creacion,
                    fecha_ultima_modificacion=historia.fecha_ultima_modificacion,
                    sprint_uuid=historia.sprint.uuid if historia.sprint else None,
                    requisitos=requisitos_info,
                    creador=creador
                )
            )

        response_data = HistoriaUsuarioListResponse(
            historias=historias_schema,
            total=total,
            page=page,
            page_size=page_size
        )

        return ApiResponse(
            code=status.HTTP_200_OK,
            msg="Historias de usuario obtenidas correctamente",
            data=response_data
        )

    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error inesperado del servidor: {str(e)}"
        )


@historia_usuario_controller.router.get(
    "/sprint/{sprint_uuid}",
    response_model=ApiResponse[List[HistoriaUsuarioListItem]],
    status_code=status.HTTP_200_OK
)
def listar_historias_por_sprint(
    sprint_uuid: str,
    db: Session = Depends(get_db),
    current_user: Cuenta = Depends(get_current_user)
):
    try:
        service = HistoriaUsuarioService(db)
        historias = service.listar_por_sprint(sprint_uuid, current_user)

        historias_schema: list[HistoriaUsuarioListItem] = []

        for historia in historias:
            solicitud = historia.creado_por.solicitud if historia.creado_por else None
            creador = CreadorInfo(
                uuid=historia.creado_por.uuid if historia.creado_por else None,
                nombre=solicitud.nombre if solicitud else None,
                apellido=solicitud.apellido if solicitud else None,
            )

            requisitos_info = [
                RequisitoInfo(uuid=req.uuid, identificador=req.identificador)
                for req in historia.requisitos
            ]

            historias_schema.append(
                HistoriaUsuarioListItem(
                    uuid=historia.uuid,
                    titulo=historia.titulo,
                    identificador=historia.identificador,
                    descripcion=historia.descripcion,
                    prioridad=historia.prioridad,
                    estado=historia.estado,
                    estimacion=historia.estimacion,
                    criterios_aceptacion=historia.criterios_aceptacion,
                    fecha_creacion=historia.fecha_creacion,
                    fecha_ultima_modificacion=historia.fecha_ultima_modificacion,
                    sprint_uuid=historia.sprint.uuid if historia.sprint else None,
                    requisitos=requisitos_info,
                    creador=creador
                )
            )

        return ApiResponse(
            code=status.HTTP_200_OK,
            msg="Historias de usuario obtenidas correctamente",
            data=historias_schema
        )

    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error inesperado del servidor: {str(e)}"
        )


@historia_usuario_controller.router.post(
    "/agregar-a-sprint",
    response_model=ApiResponse[HistoriaUsuarioSchema],
    status_code=status.HTTP_200_OK
)
def agregar_historia_a_sprint(
    datos: HistoriaUsuarioAgregarASprint,
    db: Session = Depends(get_db),
    current_user: Cuenta = Depends(get_current_user)
):
    try:
        service = HistoriaUsuarioService(db)
        historia_actualizada = service.agregar_historia_a_sprint(datos, current_user)

        return ApiResponse(
            code=status.HTTP_200_OK,
            msg="Historia de usuario agregada al sprint correctamente",
            data=historia_actualizada
        )
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error inesperado del servidor: {str(e)}"
        )


@historia_usuario_controller.router.post(
    "/quitar-de-sprint",
    response_model=ApiResponse[HistoriaUsuarioSchema],
    status_code=status.HTTP_200_OK
)
def quitar_historia_de_sprint(
    datos: HistoriaUsuarioQuitarDeSprint,
    db: Session = Depends(get_db),
    current_user: Cuenta = Depends(get_current_user)
):
    try:
        service = HistoriaUsuarioService(db)
        historia_actualizada = service.quitar_historia_de_sprint(datos, current_user)

        return ApiResponse(
            code=status.HTTP_200_OK,
            msg="Historia de usuario quitada del sprint correctamente",
            data=historia_actualizada
        )
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error inesperado del servidor: {str(e)}"
        )


@historia_usuario_controller.router.put(
    "/editar",
    response_model=ApiResponse[HistoriaUsuarioSchema],
    status_code=status.HTTP_200_OK
)
def editar_historia_usuario(
    datos: EditarHistoriaUsuario,
    db: Session = Depends(get_db),
    current_user: Cuenta = Depends(get_current_user)
):
    try:
        service = HistoriaUsuarioService(db)
        historia_actualizada = service.editar_historia_usuario(
            datos.uuid_historia,
            current_user,
            datos.datos
        )

        return ApiResponse(
            code=status.HTTP_200_OK,
            msg="Historia de usuario actualizada correctamente",
            data=historia_actualizada
        )

    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error inesperado del servidor: {str(e)}"
        )


@historia_usuario_controller.router.get(
    "/{historia_uuid}/historial",
    response_model=ApiResponse[List[HistorialHistoriaUsuarioResponse]],
    status_code=status.HTTP_200_OK
)
def obtener_historial_historia_usuario(
    historia_uuid: str,
    db: Session = Depends(get_db),
    current_user: Cuenta = Depends(get_current_user)
):
    try:
        service = HistoriaUsuarioService(db)
        historial = service.obtener_historial_historia_usuario(historia_uuid, current_user)

        return ApiResponse(
            code=status.HTTP_200_OK,
            msg="Historial obtenido correctamente",
            data=historial
        )

    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error inesperado del servidor: {str(e)}"
        )

@historia_usuario_controller.router.patch("/cambiar-estado", response_model=ApiResponse[HistoriaUsuarioSchema], status_code=status.HTTP_200_OK)
def cambiar_estado(
    datos: Schema_CambiarEstadoHistoriaUsuario,
    db: Session = Depends(get_db),
    current_user: Cuenta = Depends(get_current_user)
):
        try:
            service = HistoriaUsuarioService(db)
            resp = service.cambiar_estado_historia_usuario(datos, current_user)
            return ApiResponse(code=status.HTTP_200_OK, msg="Estado cambiado correctamente", data=resp)
        except HTTPException as e:
            # Reenviar errores conocidos (p.ej., validación de tareas incompletas)
            raise e
        except ValueError as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error inesperado del servidor: {str(e)}")
