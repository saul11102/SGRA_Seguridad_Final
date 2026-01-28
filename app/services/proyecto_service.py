from sqlalchemy.orm import Session, joinedload
from fastapi import HTTPException, status
from ..models.proyecto import Proyecto
from ..models.cuenta import Cuenta
from ..models.cuenta_proyecto import CuentaProyecto
from ..models.permiso import Permiso
from ..models.rol_permiso import RolPermiso
from ..models.enums.estado_proyecto_enum import EstadoProyecto, EstadoActualProyecto

from ..schemas.proyecto_schema import ProyectoCreate, ProyectoUpdate


class ProyectoService:
    def __init__(self, db: Session):
        self.db = db

    def _has_permission(self, cuenta_proyecto: CuentaProyecto, permission_name: str) -> bool:
        if not cuenta_proyecto or not cuenta_proyecto.rol_proyecto_id:
            return False

        permiso = self.db.query(Permiso).filter(Permiso.nombre == permission_name).first()
        if not permiso:
            return False

        rol_permiso = (
            self.db.query(RolPermiso)
            .filter(
                RolPermiso.rol_id == cuenta_proyecto.rol_proyecto_id,
                RolPermiso.permiso_id == permiso.id,
            )
            .first()
        )
        return rol_permiso is not None

    # def _check_product_owner(self, cuenta_id: int):
    #     """Verifica si la cuenta tiene el rol de 'product_owner'."""
    #     cuenta = self.db.query(Cuenta).options(joinedload(Cuenta.rol)).filter(Cuenta.id == cuenta_id).first()
    #     if not cuenta or not cuenta.rol or cuenta.rol.nombre != "product_owner":
    #         raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No tiene permisos para realizar esta acción.")
    #     return cuenta

    def create_proyecto(self, proyecto: ProyectoCreate, solicitante: Cuenta) -> Proyecto:
        # Verificar código repetido
        if self.db.query(Proyecto).filter(Proyecto.codigo == proyecto.codigo).first():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El código del proyecto ya existe."
            )
        
        # Verificar nombre repetido
        if self.db.query(Proyecto).filter(Proyecto.nombre == proyecto.nombre).first():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El nombre del proyecto ya existe."
            )

        # Buscar cuenta por UUID
        cuenta_usuario = (
            self.db.query(Cuenta)
            .filter(Cuenta.uuid == proyecto.uuid_usuario)
            .first()
        )

        if not cuenta_usuario:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="La cuenta del usuario no existe."
            )

        # Crear proyecto
        data = proyecto.model_dump(exclude={"uuid_usuario"})
        db_proyecto = Proyecto(**data)
        db_proyecto.estado = EstadoProyecto.ACTIVO

        # Crear relación en cuenta_proyecto
        relacion = CuentaProyecto(
            cuenta_id=cuenta_usuario.id,
            proyecto=db_proyecto
        )

        try:
            self.db.add(db_proyecto)
            self.db.add(relacion)
            self.db.commit()
            self.db.refresh(db_proyecto)
            return db_proyecto
        except Exception as e:
            self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error al crear el proyecto: {str(e)}"
        )


    def get_proyecto(self, proyecto_uuid: str) -> Proyecto:
        proyecto = (
            self.db.query(Proyecto)
            .filter(Proyecto.uuid == proyecto_uuid)
            .first()
        )

        if not proyecto:
            raise ValueError("Proyecto no encontrado.")
        
        return proyecto

    def get_proyectos(self) -> list[Proyecto]:
        """Obtiene todos los proyectos."""
        proyectos = self.db.query(Proyecto).all()
        return proyectos


    def get_proyectos_by_usuario_uuid(self, uuid_usuario: str) -> list[Proyecto]:

        cuenta = (
            self.db.query(Cuenta)
            .filter(Cuenta.uuid == uuid_usuario)
            .first()
        )

        if not cuenta:
            raise ValueError("El usuario no existe.")

        proyectos = (
            self.db.query(Proyecto)
            .join(CuentaProyecto, Proyecto.id == CuentaProyecto.proyecto_id)
            .filter(CuentaProyecto.cuenta_id == cuenta.id)
            .all()
        )

        return proyectos

    def update_proyecto(self, proyecto_uuid: str, proyecto_data: ProyectoUpdate, solicitante: Cuenta) -> Proyecto:

        db_proyecto = self.get_proyecto(proyecto_uuid)

        relacion = (
            self.db.query(CuentaProyecto)
            .filter(
                CuentaProyecto.proyecto_id == db_proyecto.id,
                CuentaProyecto.cuenta_id == solicitante.id,
            )
            .first()
        )

        if not relacion or not self._has_permission(relacion, "proyecto:editar"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tienes permiso para editar este proyecto."
            )

        # Validación código único
        if (
            proyecto_data.codigo is not None and
            proyecto_data.codigo != db_proyecto.codigo and
            self.db.query(Proyecto).filter(Proyecto.codigo == proyecto_data.codigo).first()
        ):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El código del proyecto ya existe."
            )

        # Validación nombre único
        if (
            proyecto_data.nombre is not None and
            proyecto_data.nombre != db_proyecto.nombre and
            self.db.query(Proyecto).filter(Proyecto.nombre == proyecto_data.nombre).first()
        ):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El nombre del proyecto ya existe."
            )

        # Actualizar campos
        for key, value in proyecto_data.model_dump(exclude_unset=True).items():
            setattr(db_proyecto, key, value)

        db_proyecto.version_actual += 1

        self.db.commit()
        self.db.refresh(db_proyecto)
        return db_proyecto

    def delete_proyecto(self, proyecto_uuid: str):
        db_proyecto = self.get_proyecto(proyecto_uuid)

        if not db_proyecto:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Proyecto no encontrado."
            )

        self.db.delete(db_proyecto)
        self.db.commit()

        return {"detail": "Proyecto eliminado exitosamente"}


    def agregar_usuario_al_proyecto(self, uuid_proyecto: str, uuid_usuario: str):
        # 1. Obtener proyecto por uuid
        proyecto = (
            self.db.query(Proyecto)
            .filter(Proyecto.uuid == uuid_proyecto)
            .first()
        )

        if not proyecto:
            raise ValueError("Proyecto no encontrado.")

        # 2. Obtener cuenta por uuid
        usuario = (
            self.db.query(Cuenta)
            .filter(Cuenta.uuid == uuid_usuario)
            .first()
        )

        if not usuario:
            raise ValueError("Usuario no encontrado.")

        # 3. Validar si ya pertenece al proyecto
        existe_relacion = (
            self.db.query(CuentaProyecto)
            .filter(
                CuentaProyecto.cuenta_id == usuario.id,
                CuentaProyecto.proyecto_id == proyecto.id
            )
            .first()
        )

        if existe_relacion:
            raise ValueError("El usuario ya pertenece a este proyecto.")

        # 4. Crear la relación
        nueva_relacion = CuentaProyecto(
            cuenta_id=usuario.id,
            proyecto_id=proyecto.id
        )

        self.db.add(nueva_relacion)
        self.db.commit()
        self.db.refresh(nueva_relacion)

        return nueva_relacion

    def obtener_usuarios_por_proyecto(self, uuid_proyecto:str):
        from ..models.solicitud_cuenta import SolicitudCuenta

        # 1. Obtener proyecto por uuid
        proyecto = (
            self.db.query(Proyecto)
            .filter(Proyecto.uuid == uuid_proyecto)
            .first()
        )

        if not proyecto:
            raise ValueError("Proyecto no encontrado.")

        # 2. Obtener usuarios asociados al proyecto
        relaciones = (
            self.db.query(CuentaProyecto)
            .options(joinedload(CuentaProyecto.cuenta))
            .filter(CuentaProyecto.proyecto_id == proyecto.id)
            .all()
        )

        usuarios = [relacion.cuenta for relacion in relaciones]

        # 3. buscar en solicitud los usuarios con su data completa con el uuid

        solicitudes = (
            self.db.query(SolicitudCuenta)
            .filter(SolicitudCuenta.cuenta_id.in_([usuario.id for usuario in usuarios]))
            .all()
        )

        return solicitudes

    from uuid import UUID

    def get_next_project_number_by_cuenta(self, cuenta_uuid: UUID) -> int:
        cuenta = (
            self.db.query(Cuenta)
            .filter(Cuenta.uuid == str(cuenta_uuid))
            .first()
        )

        if not cuenta:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Cuenta no encontrada"
            )

        total_proyectos = (
            self.db.query(CuentaProyecto)
            .filter(CuentaProyecto.cuenta_id == cuenta.id)
            .count()
        )

        return total_proyectos + 1