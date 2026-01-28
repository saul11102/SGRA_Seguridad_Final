from sqlalchemy.orm import Session, joinedload
from fastapi import HTTPException, status
from uuid import UUID
from datetime import datetime
from typing import Tuple, Optional

from app.schemas.sprint_schema import Sprint

from ..models.defecto import (
    Defecto,
    EstadoDefectoEnum,
    PrioridadDefectoEnum,
    TipoDefectoEnum,
    TipoSeveridadEnum
)
from ..models.historial_defecto import HistorialDefecto
from ..models.historia_usuario import HistoriaUsuario
from ..models.cuenta_proyecto import CuentaProyecto
from ..models.proyecto import Proyecto
from ..models.requisito import Requisito
from ..models.cuenta import Cuenta
from ..models.permiso import Permiso
from ..models.rol_permiso import RolPermiso
from ..schemas.defecto_schema import (
    DefectoCreate,
    DefectoUpdate,
    DefectoEstadoUpdate
)


class DefectoService:

    def __init__(self, db: Session):
        self.db = db

    # ======================================================
    # UTILIDADES
    # ======================================================

    def _get_defecto_by_uuid(self, defecto_uuid: UUID) -> Defecto:
        defecto = self.db.query(Defecto).filter(
            Defecto.uuid == str(defecto_uuid)
        ).first()

        if not defecto:
            raise HTTPException(404, "Defecto no encontrado")

        self._check_and_update_overdue_status(defecto)
        return defecto

    def _get_cuenta_proyecto_by_uuid(self, cp_uuid: UUID) -> CuentaProyecto:
        cuenta = self.db.query(CuentaProyecto).filter(
            CuentaProyecto.uuid == str(cp_uuid)
        ).first()

        if not cuenta:
            raise HTTPException(404, "Miembro del proyecto no encontrado")

        return cuenta

    def _get_cuenta_proyecto_by_user_id_and_project_id(
        self, user_id: int, project_id: int
    ) -> CuentaProyecto:
        cuenta = self.db.query(CuentaProyecto).filter(
            CuentaProyecto.cuenta_id == user_id,
            CuentaProyecto.proyecto_id == project_id
        ).first()

        if not cuenta:
            raise HTTPException(
                status.HTTP_403_FORBIDDEN,
                "No eres miembro de este proyecto"
            )

        return cuenta

    def _has_permission(self, cuenta_proyecto: CuentaProyecto, permiso_nombre: str) -> bool:
        if not cuenta_proyecto.rol_proyecto_id:
            return False

        permiso = self.db.query(Permiso).filter(
            Permiso.nombre == permiso_nombre
        ).first()

        if not permiso:
            return False

        return self.db.query(RolPermiso).filter(
            RolPermiso.rol_id == cuenta_proyecto.rol_proyecto_id,
            RolPermiso.permiso_id == permiso.id
        ).first() is not None

    # ======================================================
    # HISTORIAL
    # ======================================================

    def _create_historial_entry(
        self,
        defecto: Defecto,
        estado_anterior: Optional[EstadoDefectoEnum],
        estado_nuevo: EstadoDefectoEnum,
        modificado_por_cp_id: Optional[int],
        comentario: Optional[str] = None
    ):
        historial = HistorialDefecto(
            defecto_id=defecto.id,
            estado_anterior=estado_anterior,
            estado_nuevo=estado_nuevo,
            modificado_por_id=modificado_por_cp_id,
            comentario=comentario
        )
        self.db.add(historial)

    def _check_and_update_overdue_status(self, defecto: Defecto):
        if (
            defecto.estado not in [EstadoDefectoEnum.RESUELTO, EstadoDefectoEnum.CANCELADO]
            and defecto.fecha_limite
            and defecto.fecha_limite < datetime.utcnow()
            and defecto.estado != EstadoDefectoEnum.ATRASADO
        ):
            estado_anterior = defecto.estado
            defecto.estado = EstadoDefectoEnum.ATRASADO

            self._create_historial_entry(
                defecto,
                estado_anterior,
                EstadoDefectoEnum.ATRASADO,
                None,
                "Cambio automático por fecha límite vencida"
            )

            self.db.commit()
            self.db.refresh(defecto)

    # ======================================================
    # CREAR DEFECTO
    # ======================================================

    def create_defecto(self, defecto_data: DefectoCreate, current_user: Cuenta) -> Defecto:
        historia_usuario = (
            self.db.query(HistoriaUsuario)
            .filter(HistoriaUsuario.uuid == str(defecto_data.historia_usuario_uuid))
            .options(
                joinedload(HistoriaUsuario.requisitos)
                .joinedload(Requisito.proyecto)
            )
            .first()
        )

        if not historia_usuario or not historia_usuario.requisitos:
            raise HTTPException(404, "Historia de Usuario no encontrada")

        proyecto = historia_usuario.requisitos[0].proyecto
        cuenta_proyecto = self._get_cuenta_proyecto_by_user_id_and_project_id(
            current_user.id, proyecto.id
        )

        if not self._has_permission(cuenta_proyecto, "defecto:crear"):
            raise HTTPException(403, "No tienes permiso para crear defectos")

        nuevo_defecto = Defecto(
            codigo=f"DEF-{proyecto.codigo}-{int(datetime.utcnow().timestamp())}",
            titulo=defecto_data.titulo,
            descripcion_detallada=defecto_data.descripcion_detallada,
            foto=defecto_data.foto,
            tipo_defecto=defecto_data.tipo_defecto,
            prioridad=defecto_data.prioridad,
            severidad=defecto_data.severidad,
            estado=EstadoDefectoEnum.PENDIENTE,
            historia_usuario_id=historia_usuario.id,
            fecha_limite=defecto_data.fecha_limite
        )

        self.db.add(nuevo_defecto)
        self.db.flush()

        self._create_historial_entry(
            nuevo_defecto,
            None,
            EstadoDefectoEnum.PENDIENTE,
            cuenta_proyecto.id,
            "Creación del defecto"
        )

        self.db.commit()
        self.db.refresh(nuevo_defecto)
        return nuevo_defecto

    # ======================================================
    # ACTUALIZAR DEFECTO
    # ======================================================

    def update_defecto(self, defecto_uuid: UUID, data: DefectoUpdate, current_user: Cuenta) -> Defecto:
        defecto = self._get_defecto_by_uuid(defecto_uuid)

        cuenta_proyecto = self._get_cuenta_proyecto_by_user_id_and_project_id(
            current_user.id,
            defecto.historia_usuario.requisitos[0].proyecto.id
        )

        if defecto.estado not in [EstadoDefectoEnum.PENDIENTE, EstadoDefectoEnum.ATRASADO]:
            raise HTTPException(
                400,
                "Solo se pueden modificar defectos PENDIENTES o ATRASADOS"
            )

        if defecto.estado == EstadoDefectoEnum.ATRASADO and not self._has_permission(
            cuenta_proyecto, "defecto:reabrir"
        ):
            raise HTTPException(403, "No tienes permiso para modificar defectos atrasados")

        for key, value in data.model_dump(exclude_unset=True).items():
            setattr(defecto, key, value)

        self.db.commit()
        self.db.refresh(defecto)
        return defecto

    # ======================================================
    # CAMBIO DE ESTADO
    # ======================================================

    def change_estado_defecto(
        self,
        defecto_uuid: UUID,
        update_data: DefectoEstadoUpdate,
        current_user: Cuenta
    ) -> Defecto:

        defecto = self._get_defecto_by_uuid(defecto_uuid)

        cuenta_proyecto = self._get_cuenta_proyecto_by_user_id_and_project_id(
            current_user.id,
            defecto.historia_usuario.requisitos[0].proyecto.id
        )

        estado_anterior = defecto.estado
        nuevo_estado = update_data.estado

        if estado_anterior == nuevo_estado:
            return defecto

        allowed_transitions = {
            EstadoDefectoEnum.PENDIENTE: [EstadoDefectoEnum.ASIGNADO],
            EstadoDefectoEnum.ASIGNADO: [EstadoDefectoEnum.EN_DESARROLLO],
            EstadoDefectoEnum.EN_DESARROLLO: [EstadoDefectoEnum.EN_REVISION],
            EstadoDefectoEnum.EN_REVISION: [
                EstadoDefectoEnum.RESUELTO,
                EstadoDefectoEnum.PENDIENTE
            ],
            EstadoDefectoEnum.ATRASADO: [
                EstadoDefectoEnum.ASIGNADO,
                EstadoDefectoEnum.CANCELADO
            ]
        }

        if nuevo_estado not in allowed_transitions.get(estado_anterior, []):
            raise HTTPException(
                400,
                f"No se puede cambiar de {estado_anterior.value} a {nuevo_estado.value}"
            )

        if nuevo_estado in [
            EstadoDefectoEnum.EN_DESARROLLO,
            EstadoDefectoEnum.EN_REVISION
        ]:
            if defecto.cuenta_proyecto_id != cuenta_proyecto.id:
                raise HTTPException(
                    403,
                    "Solo el responsable asignado puede realizar esta acción"
                )

        if nuevo_estado == EstadoDefectoEnum.RESUELTO:
            if not self._has_permission(cuenta_proyecto, "defecto:resolver"):
                raise HTTPException(403, "No tienes permiso para resolver defectos")

        defecto.estado = nuevo_estado

        self._create_historial_entry(
            defecto,
            estado_anterior,
            nuevo_estado,
            cuenta_proyecto.id,
            update_data.comentario
        )

        self.db.commit()
        self.db.refresh(defecto)
        return defecto

    # ======================================================
    # ASIGNAR RESPONSABLE
    # ======================================================

    def asignar_encargado(
        self,
        defecto_uuid: UUID,
        cuenta_proyecto_uuid: UUID,
        current_user: Cuenta
    ) -> Defecto:

        defecto = self._get_defecto_by_uuid(defecto_uuid)
        proyecto = defecto.historia_usuario.requisitos[0].proyecto

        autor = self._get_cuenta_proyecto_by_user_id_and_project_id(
            current_user.id, proyecto.id
        )

        if not self._has_permission(autor, "defecto:asignar_responsable"):
            raise HTTPException(403, "No tienes permiso para asignar responsables")

        asignado = self._get_cuenta_proyecto_by_uuid(cuenta_proyecto_uuid)

        if asignado.proyecto_id != proyecto.id:
            raise HTTPException(400, "El responsable no pertenece al proyecto")

        estado_anterior = defecto.estado
        defecto.cuenta_proyecto_id = asignado.id

        if defecto.estado in [EstadoDefectoEnum.PENDIENTE, EstadoDefectoEnum.ATRASADO]:
            defecto.estado = EstadoDefectoEnum.ASIGNADO

            self._create_historial_entry(
                defecto,
                estado_anterior,
                EstadoDefectoEnum.ASIGNADO,
                autor.id,
                "Defecto asignado"
            )
        else:
            self._create_historial_entry(
                defecto,
                estado_anterior,
                estado_anterior,
                autor.id,
                "Responsable reasignado"
            )

        self.db.commit()
        self.db.refresh(defecto)
        return defecto

    # ======================================================
    # LISTADOS
    # ======================================================

    def listar_defectos_por_proyecto(
        self,
        proyecto_uuid: str,
        skip: int = 0,
        limit: int = 10,
        tipo_defecto: Optional[TipoDefectoEnum] = None,
        prioridad: Optional[PrioridadDefectoEnum] = None,
        severidad: Optional[TipoSeveridadEnum] = None,
        estado: Optional[EstadoDefectoEnum] = None,
        sprint_uuid: Optional[str] = None
    ) -> Tuple[list[Defecto], int]:

        proyecto = self.db.query(Proyecto).filter(Proyecto.uuid == proyecto_uuid).first()
        if not proyecto:
            raise HTTPException(404, "Proyecto no encontrado")
        query = (
            self.db.query(Defecto)
            .join(Defecto.historia_usuario)
            .outerjoin(HistoriaUsuario.sprint)
            .join(HistoriaUsuario.requisitos)
            .filter(Requisito.proyecto_id == proyecto.id)
        )

        if tipo_defecto:
            query = query.filter(Defecto.tipo_defecto == tipo_defecto)
        if prioridad:
            query = query.filter(Defecto.prioridad == prioridad)
        if severidad:
            query = query.filter(Defecto.severidad == severidad)
        if estado:
            query = query.filter(Defecto.estado == estado)

        if sprint_uuid:
            query = query.filter(Sprint.uuid == sprint_uuid)

        total = query.distinct().count()
        defectos = (
            query.distinct()
            .order_by(Defecto.id.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

        for defecto in defectos:
            self._check_and_update_overdue_status(defecto)

        return defectos, total

    def listar_defectos_por_historia_usuario(self, historia_usuario_uuid: UUID):
        historia = self.db.query(HistoriaUsuario).filter(
            HistoriaUsuario.uuid == str(historia_usuario_uuid)
        ).first()

        if not historia:
            raise HTTPException(404, "Historia de Usuario no encontrada")

        defectos = self.db.query(Defecto).filter(
            Defecto.historia_usuario_id == historia.id
        ).all()

        for defecto in defectos:
            self._check_and_update_overdue_status(defecto)

        return defectos

    # ======================================================
    # HISTORIAL Y COMENTARIOS
    # ======================================================

    def get_historial_defecto(self, defecto_uuid: UUID):
        defecto = self.db.query(Defecto).filter(
            Defecto.uuid == str(defecto_uuid)
        ).first()

        if not defecto:
            raise HTTPException(404, "Defecto no encontrado")

        return (
            self.db.query(HistorialDefecto)
            .filter(HistorialDefecto.defecto_id == defecto.id)
            .options(
                joinedload(HistorialDefecto.modificado_por)
                .joinedload(CuentaProyecto.cuenta)
            )
            .order_by(HistorialDefecto.fecha_cambio.asc())
            .all()
        )

    def get_comentarios_defecto(self, defecto_uuid: UUID):
        defecto = self.db.query(Defecto).filter(
            Defecto.uuid == str(defecto_uuid)
        ).first()

        if not defecto:
            raise HTTPException(404, "Defecto no encontrado")

        return (
            self.db.query(HistorialDefecto)
            .filter(
                HistorialDefecto.defecto_id == defecto.id,
                HistorialDefecto.comentario.isnot(None)
            )
            .options(
                joinedload(HistorialDefecto.modificado_por)
                .joinedload(CuentaProyecto.cuenta)
            )
            .order_by(HistorialDefecto.fecha_cambio.asc())
            .all()
        )

    # ======================================================
    # ELIMINAR DEFECTO
    # ======================================================

    def delete_defecto(self, defecto_uuid: UUID, current_user: Cuenta):
        defecto = self._get_defecto_by_uuid(defecto_uuid)

        cuenta_proyecto = self._get_cuenta_proyecto_by_user_id_and_project_id(
            current_user.id,
            defecto.historia_usuario.requisitos[0].proyecto.id
        )

        if not self._has_permission(cuenta_proyecto, "defecto:eliminar"):
            raise HTTPException(403, "No tienes permiso para eliminar defectos")

        if defecto.estado != EstadoDefectoEnum.PENDIENTE:
            raise HTTPException(
                400,
                "Solo se pueden eliminar defectos en estado PENDIENTE"
            )

        self.db.delete(defecto)
        self.db.commit()
