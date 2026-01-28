from fastapi import APIRouter, HTTPException, status, Query, Depends
from typing import Optional
from sqlalchemy.orm import Session
from app.core.get_db import get_db
from app.schemas.response_schema import ApiResponse
from app.schemas.requisito_schema import Obtener_Identificador, RequisitoListResponse, schema_guardar_requisito, Requisito, schema_modificar_requisito, schema_cambiar_estado_requisito, SchemaHistorialVersionResponse, schema_responder_aprobacion
from app.services.requisito_service import Requisito_service
from app.models.requisito import EstadoRequisitoEnum, PrioridadRequisitoEnum, TipoRequisitoEnum
from typing import List
from app.core.security import get_current_user
from app.models.cuenta import Cuenta

class requisito_controller:
    router = APIRouter(prefix="/requisito", tags=["Requisito"])

    # Calcula cuál será el siguiente identifivador para un requisito   
    @router.get("/obtener-identificador", response_model=ApiResponse, status_code=status.HTTP_200_OK)
    def obtener_descripcion_requisito(datos: Obtener_Identificador, db: Session = Depends(get_db), current_user: Cuenta = Depends(get_current_user)):
        try:
            service = Requisito_service(db)
            identificador = service.obtener_siguiente_identificador(
                proyecto_uuid=datos.proyecto_uuid, 
                current_user=current_user
            )
            return ApiResponse(code=status.HTTP_200_OK, msg="Identificador obtenido correctamente", data=identificador)
        except ValueError as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error inesperado del servidor: {str(e)}")
                    
    # Guarda un requisito con estado CREADO
    @router.post("/guardar-requisito", response_model=ApiResponse[Requisito], status_code=status.HTTP_200_OK)
    def guardar_requisito(datos: schema_guardar_requisito, db: Session = Depends(get_db), current_user: Cuenta = Depends(get_current_user)):
        try:
            service = Requisito_service(db)
            resp = service.guardar_requisito(
                datos, current_user)
            return ApiResponse(code=status.HTTP_200_OK, msg="Requisito guardado correctamente", data=resp)
        except ValueError as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error inesperado del servidor: {str(e)}")
            
    # Guarda un requisito con estado CREADO
    @router.post("/modificar-requisito", response_model=ApiResponse[Requisito], status_code=status.HTTP_200_OK)
    def modificar_requisito(datos: schema_modificar_requisito, db: Session = Depends(get_db), current_user: Cuenta = Depends(get_current_user)):
        try:
            service = Requisito_service(db)
            resp = service.modificar_requisito(
                datos, current_user
            )
            return ApiResponse(code=status.HTTP_200_OK, msg="Requisito modificado correctamente", data=resp)
        except ValueError as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error inesperado del servidor: {str(e)}")
            
    @router.patch("/eliminar", response_model=ApiResponse[Requisito], status_code=status.HTTP_200_OK)
    def cambiar_estado(datos: schema_cambiar_estado_requisito, db: Session = Depends(get_db), current_user: Cuenta = Depends(get_current_user)):
        try:
            service = Requisito_service(db)
            resp = service.requisito_marcar_obsoleto(datos, current_user)
            return ApiResponse(code=status.HTTP_200_OK, msg="Estado cambiado correctamente", data=resp)
        except ValueError as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error inesperado del servidor: {str(e)}")

    @router.get("/listar-historial/{requisito_uuid}", response_model=ApiResponse[List[SchemaHistorialVersionResponse]], status_code=status.HTTP_200_OK)
    def listar_historial(requisito_uuid: str, db: Session = Depends(get_db), current_user: Cuenta = Depends(get_current_user)):
        try:
            service = Requisito_service(db)
            historial = service.listar_historial(requisito_uuid, current_user)
            return ApiResponse(code=status.HTTP_200_OK, msg="Historial obtenido correctamente", data=historial)
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error inesperado del servidor: {str(e)}")
        
    @router.get("/listar-requisitos/{proyecto_uuid}", response_model=ApiResponse[RequisitoListResponse], status_code=status.HTTP_200_OK)
    def listar_requisitos(
        proyecto_uuid: str,  
        db: Session = Depends(get_db), 
        current_user: Cuenta = Depends(get_current_user),
        page: int = Query(1, ge=1), 
        page_size: int = Query(10, ge=1, le=100),
        tipo: Optional[TipoRequisitoEnum] = Query(None),
        prioridad: Optional[PrioridadRequisitoEnum] = Query(None),
        estado: Optional[EstadoRequisitoEnum] = Query(None),
    ):
        try:
            service = Requisito_service(db)
            skip = (page - 1) * page_size

            requisitos_lista, total = service.listar_requisitos(
                proyecto_uuid, 
                skip=skip, 
                limit=page_size, 
                tipo=tipo,
                prioridad=prioridad,
                estado=estado,
                current_user=current_user
            )

            response_data = RequisitoListResponse(requisitos=requisitos_lista, total=total)
            return ApiResponse(code=status.HTTP_200_OK, msg="Requisitos obtenidos correctamente", data=response_data)
            
        except ValueError as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error inesperado: {str(e)}")

    @router.post("/responder-aprobacion", response_model=ApiResponse[Requisito], status_code=status.HTTP_200_OK)
    def responder_aprobacion(datos: schema_responder_aprobacion, db: Session = Depends(get_db), current_user: Cuenta = Depends(get_current_user)):
        try:
            service = Requisito_service(db)
            resp = service.responder_aprobacion(datos, current_user)
            return ApiResponse(code=status.HTTP_200_OK, msg="Respuesta procesada correctamente", data=resp)
        except ValueError as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error inesperado del servidor: {str(e)}")