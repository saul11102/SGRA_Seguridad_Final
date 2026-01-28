from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.get_db import get_db
from app.schemas.response_schema import ApiResponse
from app.services.rol_proyecto_service import RolProyectoService

from app.schemas.rol_proyecto_schema import RolProyecto, RolProyectoCreate
from app.schemas.permiso_schema import Permiso, PermisoCreate
from app.schemas.rol_permiso_schema import RolPermisoCreate, RolPermisoUpdate
from app.schemas.cuenta_proyecto_schema import AsignarRolCuentaProyecto

from typing import List
from app.schemas.rol_proyecto_schema import RolProyecto as RolProyectoSchema
from app.schemas.permiso_schema import Permiso as PermisoSchema


class rol_proyecto_controller:
    router = APIRouter(
        prefix="/rol-proyectos",
        tags=["Rol-Proyectos"]
    )
    

    @router.post("/", response_model=ApiResponse[RolProyectoSchema])
    def crear_rol(data: RolProyectoCreate, db: Session = Depends(get_db)):
        try:
            service = RolProyectoService(db)
            rol_orm, permisos_orm = service.crear_rol(data)

            rol_orm.permisos = permisos_orm
            rol_schema = RolProyectoSchema.model_validate(rol_orm)

            return ApiResponse(
                code=201,
                msg="RolProyecto creado correctamente",
                data=rol_schema
            )
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Error inesperado del servidor: {str(e)}"
            )
    
    @router.post("/permiso", response_model=ApiResponse[Permiso])
    def crear_permiso(data: PermisoCreate, db: Session = Depends(get_db)):
        try:
            service = RolProyectoService(db)
            permiso_orm = service.crear_permiso(data)
            permiso_schema = Permiso.model_validate(permiso_orm)
            
            return ApiResponse(
                code=201,
                msg="Permiso creado correctamente",
                data=permiso_schema
            )
        except HTTPException as e:
            raise e
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Error inesperado del servidor: {str(e)}"
            )

    @router.post("/asignar-permiso", response_model=ApiResponse) 
    def asignar_permiso(rol_uuid:str, permiso_uuid:str, db: Session = Depends(get_db)):
        try:
            service = RolProyectoService(db)
            service.asignar_permiso_a_rol(rol_uuid, permiso_uuid) 
            
            return ApiResponse(
                code=200,
                msg="Permiso asignado correctamente al RolProyecto",
                data=None
            )
        except HTTPException as e:
            raise e
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Error inesperado del servidor: {str(e)}"
            )


    @router.post("/asignar-rol-cuenta", response_model=ApiResponse) 
    def asignar_rol_cuenta(data: AsignarRolCuentaProyecto, db: Session = Depends(get_db)):
        try:
            service = RolProyectoService(db)
            service.asignar_rol_a_cuenta_proyecto(data) 
            
            return ApiResponse(
                code=200,
                msg="Rol asignado correctamente a la cuenta en el proyecto",
                data=None
            )
        except HTTPException as e:
            raise e
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Error inesperado del servidor: {str(e)}"
            )

    @router.get("/por-proyecto/{uuid_proyecto}", response_model=ApiResponse[List[RolProyectoSchema]])
    def listar_roles_por_proyecto(uuid_proyecto: str, db: Session = Depends(get_db)):
        try:
            service = RolProyectoService(db)
            roles = service.listar_roles_por_proyecto(uuid_proyecto)

            return ApiResponse(
                code=status.HTTP_200_OK,
                msg="Roles del proyecto obtenidos correctamente",
                data=roles
            )
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Error inesperado del servidor: {str(e)}"
            )
        
    @router.get("/{uuid_rol}", response_model=ApiResponse[RolProyectoSchema])
    def obtener_rol(uuid_rol: str, db: Session = Depends(get_db)):
        try:
            service = RolProyectoService(db)
            rol = service.obtener_rol(uuid_rol)

            if not rol:
                raise HTTPException(
                    status_code=404,
                    detail="Rol no encontrado"
                )

            return ApiResponse(
                code=status.HTTP_200_OK,
                msg="Rol obtenido correctamente",
                data=rol
            )
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Error inesperado del servidor: {str(e)}"
            )
    
    @router.get("/", response_model=ApiResponse[List[PermisoSchema]])
    def listar_permisos(db: Session = Depends(get_db)):
        try:
            service = RolProyectoService(db)
            permisos = service.listar_permisos()

            return ApiResponse(
                code=status.HTTP_200_OK,
                msg="Lista de permisos obtenida correctamente",
                data=permisos
            )
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Error inesperado del servidor: {str(e)}"
            )
    
    @router.get("/rol_proyectos", response_model=ApiResponse[List[RolProyectoSchema]])
    def listar_rol_proyectos(db: Session = Depends(get_db)):
        try:
            service = RolProyectoService(db)
            roles = service.listar_rol_proyecto()

            return ApiResponse(
                code=status.HTTP_200_OK,
                msg="Lista de roles de proyecto obtenida correctamente",
                data=roles
            )
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Error inesperado del servidor: {str(e)}"
            )
        
    @router.get("/usuarios-por-proyecto/{uuid_proyecto}", 
            response_model=ApiResponse[List[dict]])
    def listar_usuarios_por_proyecto(uuid_proyecto: str, db: Session = Depends(get_db)):
        try:
            service = RolProyectoService(db)
            usuarios = service.listar_usuarios_por_proyecto(uuid_proyecto)

            return ApiResponse(
                code=status.HTTP_200_OK,
                msg="Usuarios del proyecto obtenidos correctamente",
                data=usuarios
            )
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Error inesperado del servidor: {str(e)}"
        )

    @router.put("/{rol_proyecto_uuid}/permisos", response_model=ApiResponse)
    def update_rol_proyecto_permisos(rol_proyecto_uuid: str, permisos: RolPermisoUpdate, db: Session = Depends(get_db)):
        try:
            service = RolProyectoService(db)
            service.update_permisos_rol_proyecto(rol_proyecto_uuid, permisos.permisos)
            return ApiResponse(
                code=status.HTTP_200_OK,
                msg="Permisos del rol en el proyecto actualizados correctamente.",
                data=None
            )
        except ValueError as e:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error inesperado del servidor: {str(e)}")

    @router.delete("/{rol_proyecto_uuid}", response_model=ApiResponse)
    def delete_rol_proyecto(rol_proyecto_uuid: str, db: Session = Depends(get_db)):
        try:
            service = RolProyectoService(db)
            service.delete_rol_proyecto(rol_proyecto_uuid)
            return ApiResponse(
                code=status.HTTP_200_OK,
                msg="Rol de proyecto eliminado correctamente.",
                data=None
            )
        except ValueError as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error inesperado del servidor: {str(e)}")