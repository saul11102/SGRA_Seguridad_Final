from fastapi import APIRouter, HTTPException, status, Query, Depends
from typing import Optional
from sqlalchemy.orm import Session
from app.core.get_db import get_db
from app.schemas.response_schema import ApiResponse
from typing import List
from app.schemas.tarea_schema import Enviar_a_revision, Guardar_tarea, HistorialTareaRead, Modificar_tarea, Revisar_tarea, Tarea, Cambiar_estado_tarea, Iniciar_tarea
from app.services.tarea_service import Tarea_service
from typing import List
from app.models.tarea import PrioridadTareaEnum, EstadoTareaEnum
from app.schemas.tarea_schema import TareaListResponse
from app.models.cuenta import Cuenta
from app.core.security import get_current_user

class tarea_controller:
    router = APIRouter(prefix="/tarea", tags=["Tarea"])
    
    @router.get("/listar/{proyecto_uuid}", response_model=ApiResponse[TareaListResponse], status_code=status.HTTP_200_OK)
    def listar_tareas(
        proyecto_uuid: str, 
        page: int = Query(1, ge=1), 
        page_size: int = Query(10, ge=1, le=100),
        prioridad: Optional[PrioridadTareaEnum] = Query(None),
        estado: Optional[EstadoTareaEnum] = Query(None),
        historia_usuario_uuid: Optional[str] = Query(None),
        sprint_uuid: Optional[str] = Query(None),
        db: Session = Depends(get_db),
        current_user: Cuenta = Depends(get_current_user)
    ):
        try:
            service = Tarea_service(db)
            skip = (page - 1) * page_size
            
            # Llamamos al servicio con los filtros y paginación
            tareas, total = service.listar_tareas_por_proyecto(
                proyecto_uuid, 
                current_user,
                skip=skip, 
                limit=page_size, 
                prioridad=prioridad, 
                estado=estado,
                historia_usuario_uuid=historia_usuario_uuid,
                sprint_uuid=sprint_uuid # <-- Pasar al servicio
            )
            
            # Construimos la data de respuesta siguiendo tu patrón de ListResponse
            response_data = TareaListResponse(
                tareas=tareas,
                total=total,
                page=page,
                page_size=page_size
            )
            
            return ApiResponse(
                code=status.HTTP_200_OK, 
                msg=f"Se encontraron {total} tareas para este proyecto", 
                data=response_data
            )
        except ValueError as e:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error inesperado: {str(e)}")
    
    @router.post("/crear", response_model=ApiResponse[Tarea], status_code=status.HTTP_200_OK)
    def crear_tarea(datos: Guardar_tarea,db: Session = Depends(get_db), current_user: Cuenta = Depends(get_current_user)):
        try:
            service = Tarea_service(db)
            resp = service.guardar_tarea(
                datos, current_user
            )
            return ApiResponse(code=status.HTTP_200_OK, msg="Tarea creada correctamente", data=resp)
        except ValueError as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error inesperado del servidor: {str(e)}")
        
    @router.put("/modificar/{uuid}", response_model=ApiResponse[Tarea], status_code=status.HTTP_200_OK)
    def modificar_tarea(uuid: str, datos: Modificar_tarea, db: Session = Depends(get_db), current_user: Cuenta = Depends(get_current_user)):
        try:
            service = Tarea_service(db)
            resp = service.modificar_tarea(uuid, datos, current_user)
            return ApiResponse(
                code=status.HTTP_200_OK, 
                msg="Tarea actualizada correctamente", 
                data=resp
            )
        except ValueError as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error inesperado: {str(e)}")
        
    @router.delete("/eliminar/{uuid}", response_model=ApiResponse[None], status_code=status.HTTP_200_OK)
    def eliminar_tarea(uuid: str, db: Session = Depends(get_db), current_user: Cuenta = Depends(get_current_user)):
        try:
            service = Tarea_service(db)
            service.eliminar_tarea(uuid, current_user)
            
            return ApiResponse(
                code=status.HTTP_200_OK,
                msg="Tarea eliminada correctamente",
                data=None
            )
        except ValueError as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
        
    @router.get("/historial/{uuid}", response_model=ApiResponse[List[HistorialTareaRead]])
    def obtener_historial(uuid: str, db: Session = Depends(get_db)):
        try:
            service = Tarea_service(db)
            historial = service.obtener_historial_tarea(uuid)
            return ApiResponse(
                code=200,
                msg="Historial recuperado",
                data=historial
            )
        except ValueError as e:
            raise HTTPException(status_code=404, detail=str(e))
        
    # se recibe por la url el uuid de la tarea
    @router.patch("/iniciar-progreso/{uuid}", response_model=ApiResponse[Tarea], status_code=status.HTTP_200_OK)
    def iniciar_progreso(uuid: str, datos: Iniciar_tarea, db: Session = Depends(get_db), current_user: Cuenta = Depends(get_current_user)):
        try:
            service = Tarea_service(db)
            resp = service.iniciar_progreso_tarea(uuid, datos, current_user)
            return ApiResponse(
                code=status.HTTP_200_OK, 
                msg="La tarea se ha marcado como iniciada exitosamente",
                data=resp
            )
        except ValueError as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
        
    # se recibe por la url el uuid de la tarea
    @router.patch("/enviar-revision/{uuid}", response_model=ApiResponse[Tarea], status_code=status.HTTP_200_OK)
    def enviar_a_revision(uuid: str, datos: Enviar_a_revision, db: Session = Depends(get_db), current_user: Cuenta = Depends(get_current_user)):
        try:
            service = Tarea_service(db)
            resp = service.enviar_tarea_a_revision(uuid, datos, current_user)
            return ApiResponse(
                code=status.HTTP_200_OK, 
                msg="La tarea ha sido enviada a revisión exitosamente", 
                data=resp
            )
        except ValueError as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
        
    # se recibe por la url el uuid de la tarea
    @router.patch("/revisar/{uuid}", response_model=ApiResponse[Tarea], status_code=status.HTTP_200_OK)
    def revisar_tarea(uuid: str, datos: Revisar_tarea, db: Session = Depends(get_db), current_user: Cuenta = Depends(get_current_user)):
        try:
            service = Tarea_service(db)
            resp = service.procesar_revision_tarea(uuid, datos, current_user)
            msg_accion = "aprobada y completada" if datos.aprobado else "rechazada y requiere ajustes"
            
            return ApiResponse(
                code=status.HTTP_200_OK, 
                msg=f"La revisión ha sido procesada correctamente. La tarea fue {msg_accion}.", 
                data=resp
            )
        except ValueError as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))