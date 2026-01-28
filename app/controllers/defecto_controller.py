from fastapi import APIRouter, Depends, status, HTTPException, Query
from sqlalchemy.orm import Session
from uuid import UUID
from typing import List

from ..schemas.defecto_schema import (
    DefectoCreate,
    DefectoUpdate,
    DefectoEstadoUpdate,
    DefectoAsignarEncargado,
    DefectoResponse,
    DefectoDetailResponse,
    HistorialDefectoResponse,
)
from ..schemas.response_schema import ApiResponse
from ..services.defecto_service import DefectoService
from app.core.get_db import get_db
from app.core.security import get_current_user
from ..models.cuenta import Cuenta
from typing import Optional
from app.models.defecto import EstadoDefectoEnum, PrioridadDefectoEnum,TipoDefectoEnum, TipoSeveridadEnum

class defecto_controller:
    router = APIRouter(prefix="/defectos", tags=["Defectos"])

    @router.post("/", response_model=ApiResponse[DefectoResponse], status_code=status.HTTP_201_CREATED)
    def crear_defecto(
        datos: DefectoCreate,
        db: Session = Depends(get_db),
        current_user: Cuenta = Depends(get_current_user)
    ):
        try:
            servicio = DefectoService(db)
            nuevo_defecto = servicio.create_defecto(datos, current_user)
            response_data = DefectoResponse.from_orm(nuevo_defecto)
            return ApiResponse(
                code=status.HTTP_201_CREATED,
                msg="Defecto creado exitosamente",
                data=response_data
            )
        except HTTPException as e:
            raise e
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error inesperado del servidor: {str(e)}")

    @router.get("/listar/{proyecto_uuid}", response_model=ApiResponse[dict], status_code=status.HTTP_200_OK)
    def listar_defectos(
        proyecto_uuid: str,
        db: Session = Depends(get_db),
        page: int = Query(1, ge=1),
        page_size: int = Query(10, ge=1, le=100),
        tipo_defecto: Optional[TipoDefectoEnum] = Query(None),
        prioridad: Optional[PrioridadDefectoEnum] = Query(None),
        severidad: Optional[TipoSeveridadEnum] = Query(None),
        estado: Optional[EstadoDefectoEnum] = Query(None),
        sprint_uuid: Optional[str] = Query(None)
    ):
        try:
            servicio = DefectoService(db)
            skip = (page - 1) * page_size
            
            defectos, total = servicio.listar_defectos_por_proyecto(
                proyecto_uuid,
                skip=skip,
                limit=page_size,
                tipo_defecto=tipo_defecto,
                prioridad=prioridad,
                severidad=severidad,
                estado=estado,
                sprint_uuid=sprint_uuid # <-- Lo enviamos al servicio
            )
            
            # El error era que esperabas List[DefectoResponse] pero envías este dict:
            return ApiResponse(
                code=status.HTTP_200_OK,
                msg=f"Se encontraron {total} defectos",
                data={
                    "items": [DefectoResponse.from_orm(d) for d in defectos],
                    "total": total,
                    "page": page,
                    "page_size": page_size
                }
            )
        except HTTPException as e:
            raise e
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @router.get("/historia-usuario/{historia_usuario_uuid}", response_model=ApiResponse[List[DefectoResponse]], status_code=status.HTTP_200_OK)
    def listar_defectos_por_hu(
        historia_usuario_uuid: UUID,
        db: Session = Depends(get_db)
    ):
        try:
            servicio = DefectoService(db)
            defectos = servicio.listar_defectos_por_historia_usuario(historia_usuario_uuid)
            return ApiResponse(
                code=status.HTTP_200_OK,
                msg=f"Se encontraron {len(defectos)} defectos para la historia de usuario",
                data=[DefectoResponse.from_orm(d) for d in defectos]
            )
        except HTTPException as e:
            raise e
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error inesperado del servidor: {str(e)}")

    @router.get("/{defecto_uuid}", response_model=ApiResponse[DefectoDetailResponse], status_code=status.HTTP_200_OK)
    def obtener_defecto(
        defecto_uuid: UUID,
        db: Session = Depends(get_db)
    ):
        try:
            servicio = DefectoService(db)
            defecto = servicio.get_defecto_with_history(defecto_uuid)
            
            defecto_resp = DefectoDetailResponse.from_orm(defecto)
            defecto_resp.historial_estados = []
            for hist in sorted(defecto.historial_estados, key=lambda h: h.fecha_cambio):
                mod_por = "Sistema"
                if hist.modificado_por and hist.modificado_por.cuenta and hist.modificado_por.cuenta.solicitud:
                    mod_por = f"{hist.modificado_por.cuenta.solicitud.nombre} {hist.modificado_por.cuenta.solicitud.apellido}"

                hist_resp = HistorialDefectoResponse.from_orm(hist)
                hist_resp.modificado_por = mod_por
                defecto_resp.historial_estados.append(hist_resp)

            return ApiResponse(
                code=status.HTTP_200_OK,
                msg="Defecto obtenido exitosamente",
                data=defecto_resp
            )
        except HTTPException as e:
            raise e
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error inesperado del servidor: {str(e)}")


    @router.put("/{defecto_uuid}", response_model=ApiResponse[DefectoResponse], status_code=status.HTTP_200_OK)
    def modificar_defecto(
        defecto_uuid: UUID,
        datos: DefectoUpdate,
        db: Session = Depends(get_db),
        current_user: Cuenta = Depends(get_current_user)
    ):
        try:
            servicio = DefectoService(db)
            defecto_actualizado = servicio.update_defecto(defecto_uuid, datos, current_user)
            response_data = DefectoResponse.from_orm(defecto_actualizado)
            return ApiResponse(
                code=status.HTTP_200_OK,
                msg="Defecto modificado exitosamente",
                data=response_data
            )
        except HTTPException as e:
            raise e
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error inesperado del servidor: {str(e)}")

    @router.patch("/{defecto_uuid}/estado", response_model=ApiResponse[DefectoResponse], status_code=status.HTTP_200_OK)
    def cambiar_estado_defecto(
        defecto_uuid: UUID,
        datos: DefectoEstadoUpdate,
        db: Session = Depends(get_db),
        current_user: Cuenta = Depends(get_current_user)
    ):
        try:
            servicio = DefectoService(db)
            defecto_actualizado = servicio.change_estado_defecto(defecto_uuid, datos, current_user)
            response_data = DefectoResponse.from_orm(defecto_actualizado)
            return ApiResponse(
                code=status.HTTP_200_OK,
                msg="Estado del defecto cambiado exitosamente",
                data=response_data
            )
        except HTTPException as e:
            raise e
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error inesperado del servidor: {str(e)}")

    @router.patch("/{defecto_uuid}/asignar", response_model=ApiResponse[DefectoResponse], status_code=status.HTTP_200_OK)
    def asignar_encargado_defecto(
        defecto_uuid: UUID,
        datos: DefectoAsignarEncargado,
        db: Session = Depends(get_db),
        current_user: Cuenta = Depends(get_current_user)
    ):
        try:
            servicio = DefectoService(db)
            defecto_actualizado = servicio.asignar_encargado(defecto_uuid, datos.cuenta_proyecto_uuid, current_user)
            response_data = DefectoResponse.from_orm(defecto_actualizado)
            return ApiResponse(
                code=status.HTTP_200_OK,
                msg="Encargado asignado al defecto exitosamente",
                data=response_data
            )
        except HTTPException as e:
            raise e
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error inesperado del servidor: {str(e)}")

    @router.delete("/{defecto_uuid}", response_model=ApiResponse, status_code=status.HTTP_200_OK)
    def eliminar_defecto(
        defecto_uuid: UUID,
        db: Session = Depends(get_db),
        current_user: Cuenta = Depends(get_current_user)
    ):
        try:
            servicio = DefectoService(db)
            servicio.delete_defecto(defecto_uuid, current_user)
            return ApiResponse(
                code=status.HTTP_200_OK,
                msg="Defecto eliminado exitosamente"
            )
        except HTTPException as e:
            raise e
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error inesperado del servidor: {str(e)}")
        
    
    @router.get("/{defecto_uuid}/historial", response_model=ApiResponse[List[HistorialDefectoResponse]])
    def obtener_historial_defecto(
        defecto_uuid: UUID,
        db: Session = Depends(get_db)
    ):
        try:
            servicio = DefectoService(db)
            historial = servicio.get_historial_defecto(defecto_uuid)

            response = []
            for hist in historial:
                mod_por = "Sistema"
                if hist.modificado_por and hist.modificado_por.cuenta and hist.modificado_por.cuenta.solicitud:
                    mod_por = f"{hist.modificado_por.cuenta.solicitud.nombre} {hist.modificado_por.cuenta.solicitud.apellido}"

                response.append(
                    HistorialDefectoResponse(
                        id=hist.id,
                        estado_anterior=hist.estado_anterior,
                        estado_nuevo=hist.estado_nuevo,
                        fecha_cambio=hist.fecha_cambio,
                        comentario=hist.comentario,
                        modificado_por=mod_por
                    )
                )

            return ApiResponse(
                code=200,
                msg="Historial de estados obtenido",
                data=response
            )
        except HTTPException as e:
            raise e


    @router.get("/{defecto_uuid}/comentarios", response_model=ApiResponse[List[HistorialDefectoResponse]])
    def obtener_comentarios_defecto(
        defecto_uuid: UUID,
        db: Session = Depends(get_db)
    ):
        try:
            servicio = DefectoService(db)
            comentarios = servicio.get_comentarios_defecto(defecto_uuid)

            response = []
            for hist in comentarios:
                mod_por = "Sistema"
                if hist.modificado_por and hist.modificado_por.cuenta and hist.modificado_por.cuenta.solicitud:
                    mod_por = f"{hist.modificado_por.cuenta.solicitud.nombre} {hist.modificado_por.cuenta.solicitud.apellido}"

                response.append(
                    HistorialDefectoResponse(
                        id=hist.id,
                        estado_anterior=hist.estado_anterior,
                        estado_nuevo=hist.estado_nuevo,
                        fecha_cambio=hist.fecha_cambio,
                        comentario=hist.comentario,
                        modificado_por=mod_por
                    )
                )

            return ApiResponse(
                code=200,
                msg="Comentarios del defecto obtenidos",
                data=response
            )
        except HTTPException as e:
            raise e
