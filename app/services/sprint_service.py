from datetime import date
from datetime import date
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from ..models.sprint import Sprint
from ..models.proyecto import Proyecto
from ..models.historia_usuario import HistoriaUsuario
from ..models.requisito import Requisito
from ..models.cuenta_proyecto import CuentaProyecto
from ..models.cuenta import Cuenta
from ..models.permiso import Permiso
from ..models.rol_permiso import RolPermiso
from ..models.enums.estado_sprint_enum import EstadoSprint
from ..schemas.sprint_schema import (
    SprintCreate,
    SprintUpdate,
    AsignarHistoriaSprint,
    RemoverHistoriaSprint,
    SprintCambiarEstado,
    SprintBasicItem,
)


class SprintService:
    def __init__(self, db: Session):
        self.db = db

    def _get_cuenta_proyecto_by_user_id_and_project_id(self, user_id: int, project_id: int) -> CuentaProyecto:
        cuenta_proyecto = (
            self.db.query(CuentaProyecto)
            .filter(
                CuentaProyecto.cuenta_id == user_id,
                CuentaProyecto.proyecto_id == project_id
            )
            .first()
        )
        if not cuenta_proyecto:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No perteneces a este proyecto."
            )
        return cuenta_proyecto

    def _has_permission(self, cuenta_proyecto: CuentaProyecto, permission_name: str) -> bool:
        if not cuenta_proyecto.rol_proyecto_id:
            return False

        permiso = self.db.query(Permiso).filter(Permiso.nombre == permission_name).first()
        if not permiso:
            return False

        rol_permiso = (
            self.db.query(RolPermiso)
            .filter(
                RolPermiso.rol_id == cuenta_proyecto.rol_proyecto_id,
                RolPermiso.permiso_id == permiso.id
            )
            .first()
        )

        return rol_permiso is not None

    def create_sprint(self, sprint: SprintCreate, solicitante: Cuenta) -> Sprint:
        """
        Crea un nuevo sprint asociado a un proyecto.
        Valida que el proyecto exista y que las fechas sean coherentes.
        """
        # Buscar proyecto por UUID
        proyecto = (
            self.db.query(Proyecto)
            .filter(Proyecto.uuid == sprint.uuid_proyecto)
            .first()
        )

        if not proyecto:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="El proyecto no existe."
            )

        cuenta_proyecto = self._get_cuenta_proyecto_by_user_id_and_project_id(solicitante.id, proyecto.id)
        if not self._has_permission(cuenta_proyecto, "sprint:crear"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tienes permiso para crear sprints."
            )

        # Validar que no exista un sprint con el mismo nombre en el proyecto
        sprint_existente = (
            self.db.query(Sprint)
            .filter(Sprint.nombre == sprint.nombre, Sprint.proyecto_id == proyecto.id)
            .first()
        )

        if sprint_existente:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Ya existe un sprint con ese nombre en el proyecto."
            )

        # Crear el sprint
        data = sprint.model_dump(exclude={"uuid_proyecto"})
        db_sprint = Sprint(**data)
        db_sprint.proyecto_id = proyecto.id
        db_sprint.estado = EstadoSprint.PLANIFICADO

        try:
            self.db.add(db_sprint)
            self.db.commit()
            self.db.refresh(db_sprint)
            return db_sprint
        except Exception as e:
            self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error al crear el sprint: {str(e)}"
            )

    def get_sprints_by_proyecto(self, proyecto_uuid: str, solicitante: Cuenta) -> list[Sprint]:
        """
        Obtiene todos los sprints de un proyecto específico.
        """
        proyecto = (
            self.db.query(Proyecto)
            .filter(Proyecto.uuid == proyecto_uuid)
            .first()
        )

        if not proyecto:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="El proyecto no existe."
            )

        cuenta_proyecto = self._get_cuenta_proyecto_by_user_id_and_project_id(solicitante.id, proyecto.id)
        if not self._has_permission(cuenta_proyecto, "sprint:listar"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tienes permiso para listar sprints."
            )

        sprints = (
            self.db.query(Sprint)
            .filter(Sprint.proyecto_id == proyecto.id)
            .order_by(Sprint.fecha_inicio.desc())
            .all()
        )

        return sprints

    def get_sprint_basic_by_uuid(self, sprint_uuid: str, solicitante: Cuenta) -> SprintBasicItem:
        
        sprint = (
            self.db.query(Sprint)
            .filter(Sprint.uuid == sprint_uuid)
            .first()
        )

        if not sprint:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="El sprint no existe."
            )
        '''
        cuenta_proyecto = self._get_cuenta_proyecto_by_user_id_and_project_id(
            solicitante.id,
            sprint.proyecto_id
        )

        if not self._has_permission(cuenta_proyecto, "sprint:ver"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tienes permiso para ver este sprint."
            )
        '''
        return SprintBasicItem(
            uuid=sprint.uuid,
            nombre=sprint.nombre,
            estado=sprint.estado
        )

    def update_sprint(self, sprint_uuid: str, sprint_update: SprintUpdate, solicitante: Cuenta) -> Sprint:
        """
        Actualiza un sprint existente.
        Valida que las nuevas fechas sean coherentes si se proporcionan.
        Valida que el nombre no se duplique en el proyecto.
        """
        db_sprint = (
            self.db.query(Sprint)
            .filter(Sprint.uuid == sprint_uuid)
            .first()
        )

        if not db_sprint:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Sprint no encontrado."
            )

        pertenece_proyecto = self._get_cuenta_proyecto_by_user_id_and_project_id(solicitante.id, db_sprint.proyecto_id)

        if not self._has_permission(pertenece_proyecto, "sprint:editar"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tienes permiso para editar sprints."
            )

        creador_relacion = (
            self.db.query(CuentaProyecto)
            .filter(CuentaProyecto.proyecto_id == db_sprint.proyecto_id)
            .order_by(CuentaProyecto.id.asc())
            .first()
        )

        es_creador = creador_relacion and creador_relacion.cuenta_id == solicitante.id

        # Obtener datos a actualizar excluyendo None
        update_data = sprint_update.model_dump(exclude_unset=True)

        # Validación de nombre único si se actualiza el nombre
        if 'nombre' in update_data and update_data['nombre'] != db_sprint.nombre:
            sprint_duplicado = (
                self.db.query(Sprint)
                .filter(
                    Sprint.nombre == update_data['nombre'],
                    Sprint.proyecto_id == db_sprint.proyecto_id,
                    Sprint.id != db_sprint.id
                )
                .first()
            )
            if sprint_duplicado:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Ya existe otro sprint con ese nombre en el proyecto."
                )

        # Validación adicional de fechas si ambas están presentes
        fecha_inicio = update_data.get('fecha_inicio', db_sprint.fecha_inicio)
        fecha_fin = update_data.get('fecha_fin', db_sprint.fecha_fin)

        if fecha_fin <= fecha_inicio:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="La fecha de fin debe ser posterior a la fecha de inicio."
            )

        # Validar transición de estado si se envía
        if 'estado' in update_data:
            nuevo_estado = update_data['estado']
            estado_actual = db_sprint.estado

            if not self._has_permission(pertenece_proyecto, "sprint:cambiar_estado"):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="No tienes permiso para cambiar el estado del sprint."
                )

            if estado_actual == EstadoSprint.PLANIFICADO:
                if nuevo_estado != EstadoSprint.EN_CURSO:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Desde PLANIFICADO solo se puede cambiar a EN_CURSO."
                    )

            elif estado_actual == EstadoSprint.EN_CURSO:
                if nuevo_estado not in (EstadoSprint.COMPLETADO, EstadoSprint.CANCELADO):
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Desde EN_CURSO solo se puede cambiar a COMPLETADO o CANCELADO."
                    )
                if nuevo_estado == EstadoSprint.COMPLETADO and db_sprint.fecha_fin > date.today():
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="No se puede completar el sprint antes de su fecha de fin."
                    )

            elif estado_actual == EstadoSprint.COMPLETADO:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Un sprint COMPLETADO no puede cambiar de estado."
                )

            elif estado_actual == EstadoSprint.CANCELADO:
                if nuevo_estado != EstadoSprint.PLANIFICADO:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Desde CANCELADO solo se puede cambiar a PLANIFICADO."
                    )

        # Actualizar el sprint
        for field, value in update_data.items():
            setattr(db_sprint, field, value)

        try:
            self.db.commit()
            self.db.refresh(db_sprint)
            return db_sprint
        except Exception as e:
            self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error al actualizar el sprint: {str(e)}"
            )

    def delete_sprint(self, sprint_uuid: str, solicitante: Cuenta) -> None:
        """
        Elimina un sprint.
        """
        db_sprint = (
            self.db.query(Sprint)
            .filter(Sprint.uuid == sprint_uuid)
            .first()
        )

        if not db_sprint:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Sprint no encontrado."
            )

        cuenta_proyecto = self._get_cuenta_proyecto_by_user_id_and_project_id(solicitante.id, db_sprint.proyecto_id)
        if not self._has_permission(cuenta_proyecto, "sprint:eliminar"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tienes permiso para eliminar sprints."
            )

        try:
            self.db.delete(db_sprint)
            self.db.commit()
        except Exception as e:
            self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error al eliminar el sprint: {str(e)}"
            )

    def _get_sprint(self, sprint_uuid: str) -> Sprint:
        sprint = (
            self.db.query(Sprint)
            .filter(Sprint.uuid == sprint_uuid)
            .first()
        )
        if not sprint:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Sprint no encontrado."
            )
        return sprint

    def _get_historia(self, historia_uuid: str) -> HistoriaUsuario:
        historia = (
            self.db.query(HistoriaUsuario)
            .options()
            .filter(HistoriaUsuario.uuid == historia_uuid)
            .first()
        )
        if not historia:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Historia de usuario no encontrada."
            )
        return historia

    def _validar_creador_historia(self, historia: HistoriaUsuario, uuid_creador: str) -> None:
        """Restringe la acción al creador de la historia (mismo patrón que HU editar/eliminar)."""
        creador = self.db.query(Cuenta).filter(Cuenta.uuid == uuid_creador).first()
        if not creador:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="El usuario no existe."
            )

        if historia.creado_por_id != creador.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Solo el creador de la historia puede realizar esta acción."
            )

    def _obtener_proyecto_id_de_historia(self, historia: HistoriaUsuario) -> int:
        if not historia.requisitos:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="La historia no tiene requisitos asociados para determinar el proyecto."
            )

        proyecto_id = historia.requisitos[0].proyecto_id

        for req in historia.requisitos:
            if req.proyecto_id != proyecto_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="La historia tiene requisitos de distintos proyectos."
                )

        return proyecto_id

    def asignar_historia_a_sprint(self, data: AsignarHistoriaSprint, solicitante: Cuenta) -> HistoriaUsuario:
        sprint = self._get_sprint(data.sprint_uuid)
        historia = self._get_historia(data.historia_uuid)

        proyecto_id_historia = self._obtener_proyecto_id_de_historia(historia)

        if sprint.proyecto_id != proyecto_id_historia:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="La historia y el sprint no pertenecen al mismo proyecto."
            )

        cuenta_proyecto = self._get_cuenta_proyecto_by_user_id_and_project_id(solicitante.id, proyecto_id_historia)
        if not self._has_permission(cuenta_proyecto, "sprint:asignar_historia"):
            raise HTTPException(
               detail="No tienes permiso para asignar historias a sprints."
            )

        if historia.sprint_id and historia.sprint_id != sprint.id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="La historia ya está asignada a otro sprint."
            )

        historia.sprint_id = sprint.id

        try:
            self.db.commit()
            self.db.refresh(historia)
            return historia
        except Exception as e:
            self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error al asignar la historia al sprint: {str(e)}"
            )

    def remover_historia_de_sprint(self, data: RemoverHistoriaSprint, solicitante: Cuenta) -> HistoriaUsuario:
        sprint = self._get_sprint(data.sprint_uuid)
        historia = self._get_historia(data.historia_uuid)

        proyecto_id_historia = self._obtener_proyecto_id_de_historia(historia)

        if sprint.proyecto_id != proyecto_id_historia:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="La historia y el sprint no pertenecen al mismo proyecto."
            )

        cuenta_proyecto = self._get_cuenta_proyecto_by_user_id_and_project_id(solicitante.id, proyecto_id_historia)
        if not self._has_permission(cuenta_proyecto, "sprint:remover_historia"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tienes permiso para remover historias de sprints."
            )

        if historia.sprint_id != sprint.id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="La historia no está asignada a este sprint."
            )

        historia.sprint_id = None

        try:
            self.db.commit()
            self.db.refresh(historia)
            return historia
        except Exception as e:
            self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error al remover la historia del sprint: {str(e)}"
            )

    def cambiar_estado_sprint(self, sprint_uuid: str, data: SprintCambiarEstado, solicitante: Cuenta) -> Sprint:
        sprint = self._get_sprint(sprint_uuid)

        pertenece_proyecto = self._get_cuenta_proyecto_by_user_id_and_project_id(solicitante.id, sprint.proyecto_id)

        if not self._has_permission(pertenece_proyecto, "sprint:cambiar_estado"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tienes permiso para cambiar el estado del sprint."
            )

        creador_relacion = (
            self.db.query(CuentaProyecto)
            .filter(CuentaProyecto.proyecto_id == sprint.proyecto_id)
            .order_by(CuentaProyecto.id.asc())
            .first()
        )

        if not creador_relacion or creador_relacion.cuenta_id != solicitante.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Solo el creador del proyecto puede cambiar el estado del sprint."
            )

        estado_actual = sprint.estado
        nuevo_estado = data.nuevo_estado

        if estado_actual == EstadoSprint.PLANIFICADO:
            if nuevo_estado != EstadoSprint.EN_CURSO:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Desde PLANIFICADO solo se puede cambiar a EN_CURSO."
                )

        elif estado_actual == EstadoSprint.EN_CURSO:
            if nuevo_estado not in (EstadoSprint.COMPLETADO, EstadoSprint.CANCELADO):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Desde EN_CURSO solo se puede cambiar a COMPLETADO o CANCELADO."
                )
            if nuevo_estado == EstadoSprint.COMPLETADO and sprint.fecha_fin > date.today():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="No se puede completar el sprint antes de su fecha de fin."
                )

        elif estado_actual == EstadoSprint.COMPLETADO:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Un sprint COMPLETADO no puede cambiar de estado."
            )

        elif estado_actual == EstadoSprint.CANCELADO:
            if nuevo_estado != EstadoSprint.PLANIFICADO:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Desde CANCELADO solo se puede cambiar a PLANIFICADO."
                )

        if estado_actual == nuevo_estado:
            return sprint

        try:
            sprint.estado = nuevo_estado
            self.db.commit()
            self.db.refresh(sprint)
            return sprint
        except Exception as e:
            self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error al cambiar el estado del sprint: {str(e)}"
            )
