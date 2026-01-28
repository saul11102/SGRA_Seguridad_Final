from enum import Enum

from sqlalchemy import case
from sqlalchemy.orm import Session, joinedload
from fastapi import HTTPException, status

from app.models.historia_usuario import HistoriaUsuario
from app.models.historial_historia_usuario import HistorialHistoriaUsuario
from app.models.proyecto import Proyecto
from app.models.requisito import EstadoRequisitoEnum, Requisito
from app.models.cuenta import Cuenta
from app.models.cuenta_proyecto import CuentaProyecto
from app.models.permiso import Permiso
from app.models.rol_permiso import RolPermiso
from app.models.sprint import Sprint
from app.models.enums.estado_historia_usuario_enum import Estado
from app.models.enums.estado_sprint_enum import EstadoSprint
from app.models.tarea import EstadoTareaEnum
from app.schemas.historia_usuario_schema import HistoriaUsuarioCreate
from app.schemas.historia_usuario_schema import HistoriaUsuarioAgregarASprint, HistoriaUsuarioQuitarDeSprint
from app.schemas.historia_usuario_schema import HistoriaUsuarioAgregarASprint
from app.models.enums.estado_historia_usuario_enum import Estado
from app.models.enums.prioridad_historia_usuario import Prioridad
from typing import Optional

class HistoriaUsuarioService:

    def __init__(self, db: Session):
        self.db = db

    def _get_cuenta_proyecto_by_user_id_and_project_id(self, user_id: int, project_id: int) -> CuentaProyecto:
        cuenta_proyecto = (
            self.db.query(CuentaProyecto)
            .filter(
                CuentaProyecto.cuenta_id == user_id,
                CuentaProyecto.proyecto_id == project_id,
            )
            .first()
        )
        if not cuenta_proyecto:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No eres miembro de este proyecto."
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
                RolPermiso.permiso_id == permiso.id,
            )
            .first()
        )

        return rol_permiso is not None

    def _formatear_valor_historial(self, valor):
        if valor is None:
            return None
        if isinstance(valor, Enum):
            return valor.value
        if isinstance(valor, list):
            return ", ".join(valor)
        return str(valor)

    def _registrar_historial_historia_usuario(self, historia: HistoriaUsuario, cuenta_proyecto_id: int, cambios: list[tuple[str, object, object]]):
        for campo, anterior, nuevo in cambios:
            registro = HistorialHistoriaUsuario(
                historia_usuario_id=historia.id,
                modificado_por_id=cuenta_proyecto_id,
                campo=campo,
                valor_anterior=self._formatear_valor_historial(anterior),
                valor_nuevo=self._formatear_valor_historial(nuevo),
            )
            self.db.add(registro)

    def create_historia_usuario(self, data: HistoriaUsuarioCreate, solicitante: Cuenta) -> HistoriaUsuario:
        if not data.uuids_requisitos:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Debe proporcionar al menos un requisito.")

        requisitos = []
        proyecto_id= None
        
        #validación de estado de los requisitos, ya lo hice pool mmhuevo jajaxd salu2.
        # tienes que ver si funciona con múltiples requisitos, yo solo le probe de una hu a un requisito
        estados_prohibidos = {
            EstadoRequisitoEnum.PENDIENTE,
            EstadoRequisitoEnum.RECHAZADO,
            EstadoRequisitoEnum.OBSOLETO,
        }
        
        for uuid_req in data.uuids_requisitos:
            requisito = (self.db.query(Requisito).filter(Requisito.uuid == uuid_req).first())
            if not requisito:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail=f"El requisito con UUID {uuid_req} no existe.")
            
            # verificación del estado de los requisitos tambien
            if requisito.estado in estados_prohibidos:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=(
                        "No se puede crear la historia porque el requisito "
                        f"está en estado '{requisito.estado.value}'."
                    ),
                )
            
            if proyecto_id is None:
                proyecto_id = requisito.proyecto_id
                
            # esta es la parte donde se cambia el estado de los requisitos
            if requisito.estado == EstadoRequisitoEnum.APROBADO:
                requisito.estado = EstadoRequisitoEnum.EN_CONSTRUCCION
            elif requisito.estado == EstadoRequisitoEnum.TERMINADO:
                 requisito.estado = EstadoRequisitoEnum.EN_CONSTRUCCION
                
            requisitos.append(requisito)

        cuenta_proyecto = self._get_cuenta_proyecto_by_user_id_and_project_id(solicitante.id, proyecto_id)
        if not self._has_permission(cuenta_proyecto, "historia_usuario:crear"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tienes permiso para crear historias de usuario."
            )

        existente_mismo_titulo = (
            self.db.query(HistoriaUsuario)
            .join(HistoriaUsuario.requisitos)
            .filter(Requisito.proyecto_id == proyecto_id, HistoriaUsuario.titulo == data.titulo)
            .first()
        )

        if existente_mismo_titulo:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Ya existe una historia de usuario con ese título en el proyecto."
            )

        nueva_historia = HistoriaUsuario(
            titulo=data.titulo,
            identificador=self.generar_identificador(proyecto_id),
            descripcion=data.descripcion,
            prioridad=data.prioridad,
            estado=Estado.PENDIENTE,
            estimacion=data.estimacion,
            criterios_aceptacion=data.criterios_aceptacion,
            requisitos=requisitos,
            creado_por_id=solicitante.id,
        )

        try:
            self.db.add(nueva_historia)
            self.db.commit()
            self.db.refresh(nueva_historia)
            return nueva_historia

        except Exception as e:
            self.db.rollback()
            raise HTTPException(                                                                                                                                                                    
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error al crear la historia de usuario: {str(e)}"
            )

    def generar_identificador(self, proyecto_id: int) -> str:
        total_historias_proyecto = (
            self.db.query(HistoriaUsuario)
            .join(HistoriaUsuario.requisitos)
            .filter(Requisito.proyecto_id == proyecto_id) 
            .distinct() 
            .count()
        )
        
        siguiente_numero = total_historias_proyecto + 1
        return f"HU_{siguiente_numero:03d}"


    def listar_por_proyecto(
        self, 
        proyecto_uuid: str, 
        skip: int, 
        limit: int, 
        solicitante: Cuenta, 
        prioridad: Optional[Prioridad] = None, 
        estado: Optional[Estado] = None,
        sprint_uuid: Optional[str] = None # <-- Nuevo parámetro
    ):
        # 1. Verificación de proyecto y permisos (se mantiene igual)
        proyecto = self.db.query(Proyecto).filter(Proyecto.uuid == proyecto_uuid).first()
        if not proyecto:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="El proyecto no existe.")

        cuenta_proyecto = self._get_cuenta_proyecto_by_user_id_and_project_id(solicitante.id, proyecto.id)
        if not self._has_permission(cuenta_proyecto, "historia_usuario:listar"):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No tienes permiso.")

        # 2. Definición del orden (se mantiene igual)
        estado_order = case(
            (HistoriaUsuario.estado == Estado.PENDIENTE, 1),
            (HistoriaUsuario.estado == Estado.EN_PROCESO, 2),
            (HistoriaUsuario.estado == Estado.COMPLETADA, 3),
            (HistoriaUsuario.estado == Estado.ATRASADA, 4),
            (HistoriaUsuario.estado == Estado.OBSOLETA, 5),
            else_=6,
        )

        # 3. Base de la consulta
        # Importante: Usamos outerjoin con Sprint para poder filtrar por su UUID
        base_query = (
            self.db.query(HistoriaUsuario)
            .join(HistoriaUsuario.requisitos)
            .outerjoin(HistoriaUsuario.sprint) # <-- Join con la relación sprint
            .filter(Requisito.proyecto_id == proyecto.id)
        )

        # 4. Lógica de filtrado por Sprint
        if sprint_uuid:
            # Si recibimos un UUID, filtramos por ese sprint específico
            base_query = base_query.filter(Sprint.uuid == sprint_uuid)
        else:
            # Si no hay UUID, mostramos solo las HU que NO tienen sprint (el backlog)
            # Nota: Mantengo tu lógica original aquí.
            base_query = base_query.filter(HistoriaUsuario.sprint_id.is_(None))

        # 5. Filtros dinámicos (Prioridad y Estado)
        if prioridad:
            base_query = base_query.filter(HistoriaUsuario.prioridad == prioridad)
        
        if estado:
            base_query = base_query.filter(HistoriaUsuario.estado == estado)
        else:
            base_query = base_query.filter(HistoriaUsuario.estado != Estado.OBSOLETA)

        # 6. Ejecución
        total = base_query.distinct().count()
        historias = (
            base_query.distinct()
            .order_by(estado_order, HistoriaUsuario.fecha_creacion.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

        return historias, total

    def listar_por_sprint(self, sprint_uuid: str, solicitante: Cuenta) -> list[HistoriaUsuario]:
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

        cuenta_proyecto = self._get_cuenta_proyecto_by_user_id_and_project_id(solicitante.id, sprint.proyecto_id)
        if not self._has_permission(cuenta_proyecto, "historia_usuario:listar"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tienes permiso para listar historias de usuario."
            )

        historias = (
            self.db.query(HistoriaUsuario)
            .filter(HistoriaUsuario.sprint_id == sprint.id)
            .order_by(HistoriaUsuario.fecha_creacion.desc())
            .all()
        )

        return historias

    def agregar_historia_a_sprint(self, data: HistoriaUsuarioAgregarASprint, solicitante: Cuenta) -> HistoriaUsuario:
        historia = (
            self.db.query(HistoriaUsuario)
            .filter(HistoriaUsuario.uuid == data.uuid_historia)
            .first()
        )

        if not historia:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="La historia de usuario no existe."
            )

        sprint = (
            self.db.query(Sprint)
            .filter(Sprint.uuid == data.uuid_sprint)
            .first()
        )
        if not sprint:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="El sprint no existe."
            )

        if not historia.requisitos:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="La historia de usuario no tiene requisitos asociados."
            )

        proyectos_historia = {req.proyecto_id for req in historia.requisitos}
        if len(proyectos_historia) != 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="La historia de usuario pertenece a múltiples proyectos."
            )

        proyecto_id = proyectos_historia.pop()

        if sprint.proyecto_id != proyecto_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El sprint no pertenece al mismo proyecto que la historia de usuario."
            )

        if sprint.estado in (EstadoSprint.COMPLETADO, EstadoSprint.CANCELADO):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El sprint está cerrado/finalizado; no se pueden agregar historias."
            )

        pertenece_proyecto = (
            self.db.query(CuentaProyecto)
            .filter(
                CuentaProyecto.proyecto_id == proyecto_id,
                CuentaProyecto.cuenta_id == solicitante.id
            )
            .first()
        )

        if not pertenece_proyecto:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No perteneces al proyecto de la historia."
            )

        if not self._has_permission(pertenece_proyecto, "historia_usuario:cambiar_estado"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tienes permiso para cambiar el estado de historias de usuario."
            )

        if not self._has_permission(pertenece_proyecto, "historia_usuario:agregar_sprint"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tienes permiso para agregar historias a sprints."
            )

        if sprint.estado in (EstadoSprint.COMPLETADO, EstadoSprint.CANCELADO):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No se pueden agregar historias a un sprint completado o cancelado."
            )

        if historia.sprint_id:
            if historia.sprint_id == sprint.id:
                return historia
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="La historia de usuario ya está asignada a otro sprint."
            )

        try:
            historia.sprint_id = sprint.id
            self.db.add(historia)
            self.db.commit()
            self.db.refresh(historia)
            return historia
        except Exception as e:
            self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error al agregar la historia de usuario al sprint: {str(e)}"
            )

    def quitar_historia_de_sprint(self, data: HistoriaUsuarioQuitarDeSprint, solicitante: Cuenta) -> HistoriaUsuario:
        historia = (
            self.db.query(HistoriaUsuario)
            .filter(HistoriaUsuario.uuid == data.uuid_historia)
            .first()
        )

        if not historia:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="La historia de usuario no existe."
            )

        sprint = (
            self.db.query(Sprint)
            .filter(Sprint.uuid == data.uuid_sprint)
            .first()
        )
        if not sprint:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="El sprint no existe."
            )

        if historia.sprint_id != sprint.id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="La historia de usuario no está asignada a este sprint."
            )

        if sprint.estado in (EstadoSprint.COMPLETADO, EstadoSprint.CANCELADO):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El sprint está cerrado/finalizado; no se pueden quitar historias."
            )

        proyectos_historia = {req.proyecto_id for req in historia.requisitos}
        if len(proyectos_historia) != 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="La historia de usuario pertenece a múltiples proyectos."
            )

        proyecto_id = proyectos_historia.pop()

        if sprint.proyecto_id != proyecto_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El sprint no pertenece al mismo proyecto que la historia de usuario."
            )

        pertenece_proyecto = (
            self.db.query(CuentaProyecto)
            .filter(
                CuentaProyecto.proyecto_id == proyecto_id,
                CuentaProyecto.cuenta_id == solicitante.id
            )
            .first()
        )

        if not pertenece_proyecto:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No perteneces al proyecto de la historia."
            )

        if not self._has_permission(pertenece_proyecto, "historia_usuario:quitar_sprint"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tienes permiso para quitar historias de sprints."
            )

        try:
            historia.sprint_id = None
            historia.estado = Estado.PENDIENTE
            self.db.add(historia)
            self.db.commit()
            self.db.refresh(historia)
            return historia
        except Exception as e:
            self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error al quitar la historia de usuario del sprint: {str(e)}"
            )

    def eliminar_historia_usuario(self, historia_uuid: str, solicitante: Cuenta) -> None:
        historia = (
            self.db.query(HistoriaUsuario)
            .filter(HistoriaUsuario.uuid == historia_uuid)
            .first()
        )

        if not historia:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="La historia de usuario no existe."
            )

        proyectos_historia = {req.proyecto_id for req in historia.requisitos}
        if not proyectos_historia:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="La historia no tiene requisitos asociados."
            )
        if len(proyectos_historia) != 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="La historia de usuario pertenece a múltiples proyectos."
            )

        proyecto_id = proyectos_historia.pop()
        cuenta_proyecto = self._get_cuenta_proyecto_by_user_id_and_project_id(solicitante.id, proyecto_id)

        if not self._has_permission(cuenta_proyecto, "historia_usuario:eliminar"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tienes permiso para eliminar historias de usuario."
            )

        if historia.estado.value not in [Estado.PENDIENTE.value, Estado.OBSOLETA.value]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Solo se pueden eliminar historias en estado 'Pendiente' u 'Obsoleta'. Estado actual: {historia.estado.value}"
            )

        if historia.tareas:
            estados_bloqueados = {EstadoTareaEnum.EN_PROGRESO, EstadoTareaEnum.FINALIZADA}
            tiene_bloqueadas = any(t.estado in estados_bloqueados for t in historia.tareas)
            if tiene_bloqueadas:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=(
                        "No se puede eliminar la historia: existen tareas en estado "
                        "'EN_PROGRESO' o 'FINALIZADA'."
                    ),
                )
        
        # actualización de estado de requisito
        for requisito in historia.requisitos:
                flag = self.verificar_existencia_historia_usuario(requisito.id, historia.id)
                if flag and requisito.estado in [EstadoRequisitoEnum.EN_CONSTRUCCION, EstadoRequisitoEnum.TERMINADO]:
                    requisito.estado = EstadoRequisitoEnum.APROBADO

        try:
            self.db.delete(historia)
            self.db.commit()
        except Exception as e:
            self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error al eliminar la historia de usuario: {str(e)}"
            )
            
    # verifica si existe al menos una historia de usuario en un determinado requisitos
    def verificar_existencia_historia_usuario(self, requisito_id: int, historia_id_a_excluir: int) -> bool:
        """
        Devuelve True si el requisito NO tiene otras historias de usuario asociadas
        (excluyendo la que se va a eliminar).
        """
        conteo_otras_hu = (
            self.db.query(HistoriaUsuario)
            .filter(HistoriaUsuario.requisitos.any(id=requisito_id))
            .filter(HistoriaUsuario.id != historia_id_a_excluir)
            .count()
        )
        return conteo_otras_hu == 0


    def editar_historia_usuario(self, historia_uuid: str, solicitante: Cuenta, datos_actualizacion) -> HistoriaUsuario:
        historia = (
            self.db.query(HistoriaUsuario)
            .filter(HistoriaUsuario.uuid == historia_uuid)
            .first()
        )

        if not historia:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="La historia de usuario no existe."
            )

        if historia.estado != Estado.PENDIENTE:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Solo se pueden editar historias en estado 'Pendiente'. Estado actual: {historia.estado.value}"
            )

        proyectos_historia = {req.proyecto_id for req in historia.requisitos}
        if not proyectos_historia:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="La historia no tiene requisitos asociados."
            )
        if len(proyectos_historia) != 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="La historia de usuario pertenece a múltiples proyectos."
            )

        proyecto_id = proyectos_historia.pop()
        cuenta_proyecto_actual = self._get_cuenta_proyecto_by_user_id_and_project_id(solicitante.id, proyecto_id)
        if not self._has_permission(cuenta_proyecto_actual, "historia_usuario:editar"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tienes permiso para editar historias de usuario."
            )

        estados_prohibidos = {
            EstadoRequisitoEnum.PENDIENTE,
            EstadoRequisitoEnum.RECHAZADO,
            EstadoRequisitoEnum.OBSOLETO,
        }

        cambios: list[tuple[str, object, object]] = []
        requisitos_previos = [req.uuid for req in historia.requisitos]

        if datos_actualizacion.uuids_requisitos is not None:
            if not datos_actualizacion.uuids_requisitos:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Debe proporcionar al menos un requisito."
                )

            requisitos = []
            for uuid_req in datos_actualizacion.uuids_requisitos:
                requisito = (
                    self.db.query(Requisito)
                    .filter(Requisito.uuid == uuid_req)
                    .first()
                )
                if not requisito:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail=f"El requisito con UUID {uuid_req} no existe."
                    )
                if requisito.estado in estados_prohibidos:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=(
                            "No se puede actualizar la historia porque el requisito "
                            f"está en estado '{requisito.estado.value}'."
                        ),
                    )
                if requisito.proyecto_id != proyecto_id:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Todos los requisitos deben pertenecer al mismo proyecto que la historia."
                    )
                requisitos.append(requisito)

            historia.requisitos = requisitos
            if set(requisitos_previos) != set(datos_actualizacion.uuids_requisitos):
                cambios.append(("requisitos", requisitos_previos, datos_actualizacion.uuids_requisitos))

        if datos_actualizacion.titulo is not None and datos_actualizacion.titulo != historia.titulo:
            existente_mismo_titulo = (
                self.db.query(HistoriaUsuario)
                .join(HistoriaUsuario.requisitos)
                .filter(
                    Requisito.proyecto_id == proyecto_id,
                    HistoriaUsuario.titulo == datos_actualizacion.titulo,
                    HistoriaUsuario.id != historia.id,
                )
                .first()
            )
            if existente_mismo_titulo:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Ya existe una historia de usuario con ese título en el proyecto."
                )
            cambios.append(("titulo", historia.titulo, datos_actualizacion.titulo))
            historia.titulo = datos_actualizacion.titulo

        if datos_actualizacion.descripcion is not None and datos_actualizacion.descripcion != historia.descripcion:
            cambios.append(("descripcion", historia.descripcion, datos_actualizacion.descripcion))
            historia.descripcion = datos_actualizacion.descripcion

        if datos_actualizacion.prioridad is not None and datos_actualizacion.prioridad != historia.prioridad:
            cambios.append(("prioridad", historia.prioridad, datos_actualizacion.prioridad))
            historia.prioridad = datos_actualizacion.prioridad

        if datos_actualizacion.criterios_aceptacion is not None and datos_actualizacion.criterios_aceptacion != historia.criterios_aceptacion:
            cambios.append(("criterios_aceptacion", historia.criterios_aceptacion, datos_actualizacion.criterios_aceptacion))
            historia.criterios_aceptacion = datos_actualizacion.criterios_aceptacion

        if datos_actualizacion.estimacion is not None and datos_actualizacion.estimacion != historia.estimacion:
            cambios.append(("estimacion", historia.estimacion, datos_actualizacion.estimacion))
            historia.estimacion = datos_actualizacion.estimacion
        # No se permite editar estado desde este endpoint; usar cambiar-estado

        try:
            if cambios:
                self._registrar_historial_historia_usuario(historia, cuenta_proyecto_actual.id, cambios)
            self.db.add(historia)
            self.db.commit()
            self.db.refresh(historia)
            return historia
        except Exception as e:
            self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error al editar la historia de usuario: {str(e)}"
            )

    def obtener_historial_historia_usuario(self, historia_uuid: str, solicitante: Cuenta):
        historia = (
            self.db.query(HistoriaUsuario)
            .filter(HistoriaUsuario.uuid == historia_uuid)
            .first()
        )

        if not historia:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="La historia de usuario no existe."
            )

        proyectos_historia = {req.proyecto_id for req in historia.requisitos}
        if not proyectos_historia:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="La historia no tiene requisitos asociados."
            )
        if len(proyectos_historia) != 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="La historia de usuario pertenece a múltiples proyectos."
            )

        proyecto_id = proyectos_historia.pop()
        cuenta_proyecto = self._get_cuenta_proyecto_by_user_id_and_project_id(solicitante.id, proyecto_id)

        if not self._has_permission(cuenta_proyecto, "historia_usuario:listar"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tienes permiso para ver el historial de historias de usuario."
            )

        registros = (
            self.db.query(HistorialHistoriaUsuario)
            .filter(HistorialHistoriaUsuario.historia_usuario_id == historia.id)
            .options(
                joinedload(HistorialHistoriaUsuario.modificado_por)
                .joinedload(CuentaProyecto.cuenta)
            )
            .order_by(HistorialHistoriaUsuario.fecha_modificacion.asc())
            .all()
        )

        historial = []
        for r in registros:
            mod_por = "Sistema"
            if r.modificado_por and r.modificado_por.cuenta and r.modificado_por.cuenta.solicitud:
                mod_por = f"{r.modificado_por.cuenta.solicitud.nombre} {r.modificado_por.cuenta.solicitud.apellido}"

            historial.append(
                {
                    "campo": r.campo,
                    "valor_anterior": r.valor_anterior,
                    "valor_nuevo": r.valor_nuevo,
                    "fecha_modificacion": r.fecha_modificacion,
                    "modificado_por": mod_por,
                }
            )

        return historial

    def cambiar_estado_historia_usuario(self, datos, solicitante: Cuenta) -> HistoriaUsuario:
            historia = self.buscar_historia_usuario_por_uuid(datos.uuid_historia)
            if not historia:
                raise ValueError("La historia de usuario no existe")

            proyectos_historia = {req.proyecto_id for req in historia.requisitos}
            if not proyectos_historia:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="La historia no tiene requisitos asociados."
                )
            if len(proyectos_historia) != 1:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="La historia de usuario pertenece a múltiples proyectos."
                )

            proyecto_id = proyectos_historia.pop()

            pertenece_proyecto = (
                self.db.query(CuentaProyecto)
                .filter(
                    CuentaProyecto.proyecto_id == proyecto_id,
                    CuentaProyecto.cuenta_id == solicitante.id
                )
                .first()
            )

            if not pertenece_proyecto:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="No perteneces al proyecto de la historia."
                )

            estado_actual = historia.estado
            estado_objetivo = datos.nuevo_estado

            allowed_transitions = {
                Estado.PENDIENTE: {Estado.EN_PROCESO, Estado.OBSOLETA},
                Estado.EN_PROCESO: {Estado.COMPLETADA, Estado.ATRASADA, Estado.OBSOLETA},
                Estado.COMPLETADA: set(),
                Estado.ATRASADA: set(),
                Estado.OBSOLETA: set(),
            }

            if estado_objetivo == estado_actual:
                return historia

            if estado_objetivo not in allowed_transitions.get(estado_actual, set()):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=(
                        f"Transición no permitida desde '{estado_actual.value}' "
                        f"a '{estado_objetivo.value}'."
                    ),
                )

            if estado_objetivo == Estado.OBSOLETA and historia.tareas:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="No se puede marcar la historia como obsoleta porque tiene tareas asociadas."
                )

            if estado_objetivo in {Estado.COMPLETADA, Estado.ATRASADA}:
                self._validar_tareas_finalizadas(historia)

            historia.estado = estado_objetivo
            # método que actualiza automáticamente el estado de los requisitos asociados
            self._verificar_actualizacion_requisitos(historia)

            self.db.commit()
            self.db.refresh(historia)
            return historia
    
    def _verificar_actualizacion_requisitos(self, hu: HistoriaUsuario):
        for requisito in hu.requisitos:
            if hu.estado == Estado.COMPLETADA:
                todas_completadas = all(h.estado == Estado.COMPLETADA for h in requisito.historias_usuario)
                if todas_completadas:
                    requisito.estado = EstadoRequisitoEnum.TERMINADO
            
            elif hu.estado in [Estado.EN_PROCESO, Estado.PENDIENTE, Estado.ATRASADA]:
                if requisito.estado in [EstadoRequisitoEnum.APROBADO, EstadoRequisitoEnum.TERMINADO]:
                    requisito.estado = EstadoRequisitoEnum.EN_CONSTRUCCION

    def _validar_tareas_finalizadas(self, hu: HistoriaUsuario) -> None:
        if not hu.tareas:
            return

        estados_validos = {EstadoTareaEnum.COMPLETADA}
        todas_finalizadas = all(t.estado in estados_validos for t in hu.tareas)
        if not todas_finalizadas:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    "No se puede cambiar el estado de la historia: "
                    "todas las tareas deben estar en estado 'COMPLETADA'."
                ),
            )

    def buscar_historia_usuario_por_uuid(self, historia_uuid: str) -> HistoriaUsuario:
            historia = self.db.query(HistoriaUsuario).filter(HistoriaUsuario.uuid == historia_uuid).first()
            if not historia:
                raise ValueError(f"La historia de usuario no existe")
            return historia