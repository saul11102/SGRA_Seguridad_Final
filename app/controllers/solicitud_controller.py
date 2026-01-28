from fastapi import APIRouter, HTTPException, status, Query, Depends
from typing import Optional
from sqlalchemy.orm import Session
from app.schemas.solicitud_cuenta_schema import CreateSolicitud, SolicitudListResponse, schema_solicitud_cuenta, RecuperarPasswordRequest, SolicitudDetail
from app.schemas.response_schema import ApiResponse
from app.core.get_db import get_db
from app.services.solicitud_cuenta_service import solicitud_cuenta_service

class solicitud_controller:
    
    router = APIRouter(prefix="/solicitud", tags=["Solicitud"])

    @router.post("/crear-solicitud", response_model=ApiResponse[SolicitudDetail], status_code=status.HTTP_201_CREATED)
    def crear_solicitud(datos: CreateSolicitud, db: Session = Depends(get_db)):
        try:
            nueva_solicitud = solicitud_cuenta_service.create_solicitud(db, datos)
            response_data = SolicitudDetail.model_validate(nueva_solicitud)
            return ApiResponse(
                code=status.HTTP_201_CREATED,
                msg="Solicitud creada exitosamente",
                data=response_data
            )
        except ValueError as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error inesperado del servidor: {str(e)}")

    @router.post("/responder", response_model=ApiResponse, status_code=status.HTTP_200_OK)
    def responder_solicitud(solicitud: schema_solicitud_cuenta, db: Session = Depends(get_db)):
        try:
            service = solicitud_cuenta_service(db)
            msg = service.responder_solicitud(solicitud.uuid_usuario, solicitud.decision.value)
            return ApiResponse(code=status.HTTP_200_OK, msg=msg)
        except ValueError as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error inesperado del servidor: {str(e)}")

    @router.get("/", response_model=ApiResponse[SolicitudListResponse], status_code=status.HTTP_200_OK)
    def listar_solicitudes(
        db: Session = Depends(get_db), 
        page: Optional[int] = Query(1, ge=1, description="Número de página"),
        page_size: Optional[int] = Query(10, ge=1, le=100, description="Tamaño de página")
    ):
        try:
            skip = (page - 1) * page_size
            limit = page_size
            solicitudes, total = solicitud_cuenta_service.list_solicitudes(db, skip=skip, limit=limit)
            
            # Mapear a SolicitudDetail
            solicitudes_detail = [SolicitudDetail.model_validate(s) for s in solicitudes]

            response_data = SolicitudListResponse(solicitudes=solicitudes_detail, total=total)
            
            return ApiResponse(
                code=status.HTTP_200_OK,
                msg="Listado de solicitudes obtenido correctamente",
                data=response_data
            )
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error inesperado del servidor: {str(e)}")

    @router.post("/recuperar-password", response_model=ApiResponse, status_code=status.HTTP_200_OK)
    def recuperar_password(payload: RecuperarPasswordRequest, db: Session = Depends(get_db)):
        try:
            solicitud_cuenta_service.recuperar_contrasena_por_correo(db, payload.email)
            return ApiResponse(
                code=status.HTTP_200_OK,
                msg="Se envió la contraseña temporal al correo proporcionado si el usuario existe."
            )
        except ValueError as e:
            # Aún si no se encuentra el usuario, damos una respuesta genérica para no revelar si un email existe en el sistema.
            return ApiResponse(
                code=status.HTTP_200_OK,
                msg="Se envió la contraseña temporal al correo proporcionado si el usuario existe."
            )
        except RuntimeError as e:
            raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(e))
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error inesperado del servidor: {str(e)}")
