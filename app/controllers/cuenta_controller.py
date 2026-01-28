from fastapi import APIRouter, HTTPException, status, Depends
from typing import List
from sqlalchemy.orm import Session
from uuid import UUID
from app.models.cuenta import Cuenta
from app.schemas.auth_schema import LoginRequest, LoginResponse
from app.schemas.response_schema import ApiResponse
from app.services import auth_service
from app.core.get_db import get_db
from app.core.security import get_current_user
from app.services.cuenta_service import cuenta_service
from ..schemas.cuenta_schema import CuentaResponse, CambiarRol, EstadoCuentaUpdate, CuentaDetailResponse

class cuenta_controller:

    router = APIRouter(prefix="/cuenta", tags=["Cuenta"])

    @router.post("/cambiar-rol", response_model=ApiResponse, status_code=status.HTTP_200_OK)
    def cambiar_rol(solicitud: CambiarRol, db: Session = Depends(get_db)):
        try:
            service = cuenta_service(db)
            msg = service.asignar_rol(solicitud.uuid_usuario, solicitud.rol_nombre)
            return ApiResponse(code=status.HTTP_200_OK, msg=msg)
        except ValueError as e:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error inesperado del servidor: {str(e)}")

    @router.post("/{cuenta_id}/desactivar", response_model=ApiResponse[CuentaResponse], status_code=status.HTTP_200_OK)
    def desactivar_cuenta(cuenta_id: int, db: Session = Depends(get_db)):
        """Desactiva una cuenta, cambiando su estado a INACTIVO."""
        try:
            service = cuenta_service(db)
            cuenta = service.desactivar_cuenta(cuenta_id)
            response_data = CuentaResponse.model_validate(cuenta)
            return ApiResponse(
                code=status.HTTP_200_OK,
                msg="Cuenta desactivada correctamente",
                data=response_data
            )
        except ValueError as e:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error inesperado del servidor: {str(e)}")

    @router.post("/login", response_model=ApiResponse[LoginResponse], status_code=status.HTTP_200_OK)
    def login(login_data: LoginRequest, db: Session = Depends(get_db)):
        try:
            result = auth_service.login(db, login_data.correo, login_data.contrasena)
            login_response = LoginResponse.model_validate(result)
            return ApiResponse(
                code=status.HTTP_200_OK,
                msg="Login exitoso",
                data=login_response
            )
        except ValueError as e:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error en el servidor: {str(e)}")

    @router.get("/me", status_code=status.HTTP_200_OK)
    def me(current_user: Cuenta = Depends(get_current_user)):
        return {
            "uuid": str(current_user.uuid),
            "rol_id": current_user.rol_id,
            "estado": current_user.estadoCuenta
        }

    @router.get('/usuarios', response_model=ApiResponse[List[CuentaDetailResponse]], status_code=status.HTTP_200_OK)
    def list_usuarios(db: Session = Depends(get_db)):
        """Lista todos los usuarios (cuentas)."""
        try:
            service = cuenta_service(db)
            cuentas = service.get_cuentas()
            
            result = []
            for c in cuentas:
                estado = getattr(c, 'estadoCuenta', None)
                estado_val = estado.name if hasattr(estado, 'name') else str(estado)
                
                # Asegurarse de que la solicitud y el rol existen
                nombre = c.solicitud.nombre if c.solicitud else "N/A"
                apellido = c.solicitud.apellido if c.solicitud else "N/A"
                correo = c.solicitud.correo if c.solicitud else "N/A"
                rol_nombre = c.rol.nombre if c.rol else "N/A"

                result.append(CuentaDetailResponse(
                    id=c.id,
                    uuid=c.uuid,
                    nombre=nombre,
                    apellido=apellido,
                    correo=correo,
                    estadoCuenta=estado_val,
                    rol=rol_nombre,
                    rol_id=c.rol_id
                ))

            return ApiResponse(
                code=status.HTTP_200_OK,
                msg="Lista de usuarios obtenida correctamente",
                data=result
            )
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error inesperado del servidor: {str(e)}")


    @router.post("/{cuenta_uuid}/estado", response_model=ApiResponse[CuentaResponse], status_code=status.HTTP_200_OK)
    def actualizar_estado_cuenta(cuenta_uuid: UUID, estado: EstadoCuentaUpdate, db: Session = Depends(get_db)):
        try:
            service = cuenta_service(db)
            cuenta = service.actualizar_estado_cuenta(cuenta_uuid, estado.estadoCuenta)
            response_data = CuentaResponse.model_validate(cuenta)
            return ApiResponse(
                code=status.HTTP_200_OK,
                msg="Estado de la cuenta actualizado correctamente",
                data=response_data
            )
        except ValueError as e:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error inesperado del servidor: {str(e)}")

