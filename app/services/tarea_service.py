from sqlalchemy.orm import Session, joinedload
from fastapi import HTTPException, status
from sqlalchemy import func
from ..models.tarea import Tarea, EstadoTareaEnum, PrioridadTareaEnum
from ..models.historia_usuario import HistoriaUsuario
from app.core.security import get_current_user
from app.schemas.tarea_schema import Enviar_a_revision, Guardar_tarea, Modificar_tarea, Cambiar_estado_tarea, Iniciar_tarea, Revisar_tarea
from ..models.cuenta_proyecto import CuentaProyecto
from ..models.historial_tarea import HistorialTarea
from sqlalchemy.orm import joinedload
from ..models.cuenta import Cuenta
from app.models.proyecto import Proyecto
from app.models.requisito import Requisito
from app.models.sprint import Sprint
from typing import Optional
from app.models.enums.estado_historia_usuario_enum import Estado as EstadoHU
from app.models.cuenta import Cuenta
from ..models.permiso import Permiso
from ..models.rol_permiso import RolPermiso

class Tarea_service:
    def __init__(self, db: Session):
        self.db = db
        
    # ======================================================
    # UTILIDADES Y SEGURIDAD (Mismo patrón que Defectos)
    # ======================================================

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

    def _buscar_tarea_por_uuid(self, tarea_uuid: str) -> Tarea:
        tarea = self.db.query(Tarea).filter(Tarea.uuid == tarea_uuid).first()
        if not tarea:
            raise HTTPException(404, "La tarea no existe")
        return tarea

    def _buscar_responsable_por_uuid(self, cuenta_proyecto_uuid: str) -> CuentaProyecto:
        responsable = self.db.query(CuentaProyecto).filter(
                CuentaProyecto.uuid == str(cuenta_proyecto_uuid)
            ).first()
        if not responsable:
            raise HTTPException(404, "El usuario responsable no existe o no está asignado al proyecto")
        return responsable

    def _get_project_id_from_hu(self, hu_uuid: str) -> int:
        hu = self.db.query(HistoriaUsuario).filter(HistoriaUsuario.uuid == str(hu_uuid)).options(
            joinedload(HistoriaUsuario.requisitos)
        ).first()
        if not hu or not hu.requisitos:
            raise HTTPException(404, "Historia de Usuario no encontrada o sin proyecto asociado")
        return hu.requisitos[0].proyecto_id

    # ======================================================
    # LÓGICA DE NEGOCIO
    # ======================================================
        
    def listar_tareas_por_hu(self, historia_usuario_uuid: str):
        hu = self.buscar_historia_usuario_por_uuid(historia_usuario_uuid)
        return hu.tareas
        
    def guardar_tarea(self, datos: Guardar_tarea, current_user: Cuenta):
        hu = self.buscar_historia_usuario_por_uuid(datos.historia_usuario_uuid)
        estado_inicial = EstadoTareaEnum.PENDIENTE
        
        proyecto_id = hu.requisitos[0].proyecto_id
        cuenta_proyecto =self._get_cuenta_proyecto_by_user_id_and_project_id(current_user.id, proyecto_id)
        if not self._has_permission(cuenta_proyecto, "tarea:crear"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tienes permiso para crear tareas."
            )
        
        responsable_id = None
        if datos.cuenta_proyecto_uuid:
            responsable = self.buscar_responsable_por_uuid(datos.cuenta_proyecto_uuid)
            if responsable:
                responsable_id = responsable.id
                estado_inicial = EstadoTareaEnum.ASIGNADA

        nuevo_identificador = self.generar_identificador_tarea(hu.id, hu.titulo)
        
        nueva_tarea = Tarea(
            identificador=nuevo_identificador,
            titulo=datos.titulo,
            descripcion=datos.descripcion,
            criterios_entrada=datos.criterios_entrada,
            criterios_salida=datos.criterios_salida,
            fecha_limite=datos.fecha_limite,
            tipo_tarea=datos.tipo_tarea,
            estimacion_horas=datos.estimacion_horas,
            prioridad=datos.prioridad,
            historia_usuario_id=hu.id,
            cuenta_proyecto_id=responsable_id,
            estado=estado_inicial
        )
        
        try:
            if hu.estado == EstadoHU.PENDIENTE:
                hu.estado = EstadoHU.EN_PROCESO
            self.db.add(nueva_tarea)
            self.db.commit()
            self.db.refresh(nueva_tarea)
            return nueva_tarea
        except Exception as e:
            self.db.rollback()
            ValueError(f"Error al guardar la tarea: {str(e)}")
            
    def modificar_tarea(self, tarea_uuid: str, datos: Modificar_tarea, current_user: Cuenta):
        tarea = self.buscar_tarea_por_uuid(tarea_uuid)
        responsable_cambio = self.buscar_responsable_por_uuid(datos.responsable_cambio_uuid)
        proyecto_id = self._get_project_id_from_hu(tarea.historia_usuario.uuid)
        
        cuenta_proyecto = self._get_cuenta_proyecto_by_user_id_and_project_id(current_user.id, proyecto_id)
        if not self._has_permission(cuenta_proyecto, "tarea:modificar"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tienes permiso para modificar tareas."
            )
            
        if not responsable_cambio:
            raise ValueError("Error al identificar al responsable del cambio")
        tarea._usuario_autor_id = responsable_cambio.id

        estados_permitidos = [EstadoTareaEnum.PENDIENTE, EstadoTareaEnum.ASIGNADA, EstadoTareaEnum.PENDIENTE_POR_REVISAR]
        if tarea.estado not in estados_permitidos:
            if tarea.estado == EstadoTareaEnum.AJUSTES_REQUERIDOS:
                raise ValueError(f"La tarea ya fue revisada y tiene ajustes requeridos. Primero deben aplicarse las correcciones antes de permitir nuevas modificaciones.") 
            elif tarea.estado == EstadoTareaEnum.COMPLETADA:
                raise ValueError(f"No se permiten cambios si la tarea ha sido marcada como completada")
            else:
                raise ValueError(f"No se permiten cambios si ya hay alguien trabajando en la tarea")   

        update_data = datos.model_dump(exclude_unset=True) 
        
        if "cuenta_proyecto_uuid" in update_data:
            uuid_responsable = update_data.pop("cuenta_proyecto_uuid")
            if uuid_responsable:
                responsable = self.buscar_responsable_por_uuid(uuid_responsable)
                tarea.cuenta_proyecto_id = responsable.id
                if tarea.estado == EstadoTareaEnum.PENDIENTE:
                    tarea.estado = EstadoTareaEnum.ASIGNADA 
            else:
                tarea.cuenta_proyecto_id = None

        for key, value in update_data.items():
            setattr(tarea, key, value)

        try:
            self.db.commit()
            self.db.refresh(tarea)
            return tarea
        except Exception as e:
            self.db.rollback()
            raise ValueError(f"Error al actualizar la tarea: {str(e)}")
        
    def eliminar_tarea(self, tarea_uuid: str, current_user: Cuenta):
        tarea = self.buscar_tarea_por_uuid(tarea_uuid)
        proyecto_id = self._get_project_id_from_hu(tarea.historia_usuario.uuid)
        
        cuenta_proyecto = self._get_cuenta_proyecto_by_user_id_and_project_id(current_user.id, proyecto_id)
        if not self._has_permission(cuenta_proyecto, "tarea:eliminar"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tienes permiso para eliminar tareas."
            )
            
        if tarea.estado != EstadoTareaEnum.PENDIENTE:
            raise ValueError("Solo se pueden eliminar tareas en un estado de pendiente.")

        try:
            self.db.delete(tarea)
            self.db.commit()
            return True
        except Exception as e:
            self.db.rollback()
            raise ValueError(f"Error al intentar eliminar la tarea: {str(e)}")
        
    def obtener_historial_tarea(self, tarea_uuid: str):
        tarea = self.buscar_tarea_por_uuid(tarea_uuid)
        
        historial_raw = self.db.query(HistorialTarea).options(
            joinedload(HistorialTarea.modificado_por)  
            .joinedload(CuentaProyecto.cuenta)         
            .joinedload(Cuenta.solicitud)              
        ).filter(
            HistorialTarea.tarea_id == tarea.id
        ).order_by(HistorialTarea.fecha_modificacion.desc()).all()
        
        resultado = []
        for registro in historial_raw:
            datos_usuario = None
            if registro.modificado_por and registro.modificado_por.cuenta and registro.modificado_por.cuenta.solicitud:
                solicitud = registro.modificado_por.cuenta.solicitud
                datos_usuario = {
                    "nombre": solicitud.nombre,
                    "apellido": solicitud.apellido
                }
            
            resultado.append({
                "id": registro.id,
                "fecha_modificacion": registro.fecha_modificacion,
                "tipo_cambio": registro.tipo_cambio,
                "usuario": datos_usuario
            })
            
        return resultado
        
    def buscar_tarea_por_uuid(self, tarea_uuid: str) -> Tarea:
        tarea = self.db.query(Tarea).filter(Tarea.uuid == tarea_uuid).first()
        if not tarea:
            raise ValueError("La tarea no existe")
        return tarea

    def generar_identificador_tarea(self, historia_usuario_id: int, nombre_hu: str) -> str:
        max_id = self.db.query(func.max(Tarea.id)).filter(
        Tarea.historia_usuario_id == historia_usuario_id
        ).scalar()

        if max_id is None:
            nuevo_numero = 1
        else:
            ultima_tarea = self.db.query(Tarea.identificador).filter(
                Tarea.historia_usuario_id == historia_usuario_id
            ).order_by(Tarea.id.desc()).first()
            
            if ultima_tarea:
                ultimo_identificador = ultima_tarea[0]
                try:
                    nuevo_numero = int(ultimo_identificador.split('-')[-1]) + 1
                except (ValueError, IndexError):
                    nuevo_numero = 1
            else:
                nuevo_numero = 1

        prefix = nombre_hu[:5].upper().replace(" ", "")
        return f"T-{prefix}-{nuevo_numero:03d}"
    
    def buscar_historia_usuario_por_uuid(self, historia_usuario_uuid: str) -> HistoriaUsuario:
        hu = self.db.query(HistoriaUsuario).filter(
            HistoriaUsuario.uuid == historia_usuario_uuid
        ).first()
        if not hu:
            raise ValueError("La historia de usuario no existe")
        return hu
    
    def listar_tareas_por_proyecto(
        self, 
        proyecto_uuid: str, 
        current_user: Cuenta,
        skip: int = 0, 
        limit: int = 10, 
        prioridad: Optional[PrioridadTareaEnum] = None, 
        estado: Optional[EstadoTareaEnum] = None,
        historia_usuario_uuid: Optional[str] = None,
        sprint_uuid: Optional[str] = None # <-- Nuevo parámetro
        ):
        proyecto = self.db.query(Proyecto).filter(Proyecto.uuid == proyecto_uuid).first()
        if not proyecto:
            raise ValueError("El proyecto no existe.")
        
        # Construcción de la Query
        query = (
            self.db.query(Tarea)
            .options(
                joinedload(Tarea.responsable)
                .joinedload(CuentaProyecto.cuenta)
                .joinedload(Cuenta.solicitud),
                joinedload(Tarea.historia_usuario)
            )
            .join(Tarea.historia_usuario) # Join a HU
            .outerjoin(HistoriaUsuario.sprint) # Join de HU a Sprint para poder filtrar
            .join(HistoriaUsuario.requisitos)
            .filter(Requisito.proyecto_id == proyecto.id)
        )

        # Aplicación de filtros
        if prioridad:
            query = query.filter(Tarea.prioridad == prioridad)
        if estado:
            query = query.filter(Tarea.estado == estado)
        if historia_usuario_uuid:
            query = query.filter(HistoriaUsuario.uuid == historia_usuario_uuid)
        
        # Nuevo filtro por Sprint UUID
        if sprint_uuid:
            query = query.filter(Sprint.uuid == sprint_uuid)

        total = query.distinct().count()

        tareas = (
            query.distinct()
            .order_by(Tarea.fecha_creacion.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

        return tareas, total

    def buscar_responsable_por_uuid(self, cuenta_proyecto_uuid: str):
        responsable = self.db.query(CuentaProyecto).filter(
                CuentaProyecto.uuid == cuenta_proyecto_uuid
            ).first()
        if not responsable:
            raise ValueError("El usuario responsable no existe o no está asignado al proyecto")
        return responsable
    
    def iniciar_progreso_tarea(self, tarea_uuid: str, datos: Iniciar_tarea, current_user: Cuenta):
        tarea = self.buscar_tarea_por_uuid(tarea_uuid)
        usuario_solicitante = self.buscar_responsable_por_uuid(datos.responsable_cambio_uuid)
        
        proyecto_id = self._get_project_id_from_hu(tarea.historia_usuario.uuid)
        self._get_cuenta_proyecto_by_user_id_and_project_id(current_user.id, proyecto_id)
        
        if not tarea.cuenta_proyecto_id:
             raise ValueError("Esta tarea no tiene un responsable asignado, por lo tanto no se puede iniciar.")

        if tarea.cuenta_proyecto_id != usuario_solicitante.id:
             raise ValueError("Solo el usuario asignado a esta tarea puede marcarla como 'En Progreso'.")
         
        if tarea.estado == EstadoTareaEnum.EN_PROGRESO:
            raise ValueError("La tarea ya está en progreso.")

        estados_permitidos = [EstadoTareaEnum.ASIGNADA, EstadoTareaEnum.AJUSTES_REQUERIDOS]
        
        if tarea.estado not in estados_permitidos:
            raise ValueError(f"No se puede iniciar la tarea en su estado actual. Solo se permite si ya está asignada a alguien o si tiene ajustes necesarios.")

        
        tarea._usuario_autor_id = usuario_solicitante.id
        tarea.estado = EstadoTareaEnum.EN_PROGRESO
        
        try:
            self.db.commit()
            self.db.refresh(tarea)
            return tarea
        except Exception as e:
            self.db.rollback()
            raise ValueError(f"Error al iniciar el progreso de la tarea: {str(e)}")
    
    def enviar_tarea_a_revision(self, tarea_uuid: str, datos: Enviar_a_revision, current_user: Cuenta):
        tarea = self.buscar_tarea_por_uuid(tarea_uuid)
        usuario_solicitante = self.buscar_responsable_por_uuid(datos.responsable_cambio_uuid)
        
        proyecto_id = self._get_project_id_from_hu(tarea.historia_usuario.uuid)
        self._get_cuenta_proyecto_by_user_id_and_project_id(current_user.id, proyecto_id)
        
        if not tarea.cuenta_proyecto_id:
             raise ValueError("La tarea no tiene un responsable asignado.")

        if tarea.cuenta_proyecto_id != usuario_solicitante.id:
             raise ValueError("Solo el usuario responsable de la tarea puede enviarla a revisión.")

        if tarea.estado != EstadoTareaEnum.EN_PROGRESO:
            raise ValueError(f"No se puede enviar a revisión en su estado actual. Primero se debe iniciar el progreso de la tarea.")

        tarea._usuario_autor_id = usuario_solicitante.id
        tarea.estado = EstadoTareaEnum.PENDIENTE_POR_REVISAR
        
        try:
            self.db.commit()
            self.db.refresh(tarea)
            return tarea
        except Exception as e:
            self.db.rollback()
            raise ValueError(f"Error al enviar la tarea a revisión: {str(e)}")
        
    def procesar_revision_tarea(self, tarea_uuid: str, datos: Revisar_tarea, current_user: Cuenta):
        tarea = self.buscar_tarea_por_uuid(tarea_uuid)
        revisor = self.buscar_responsable_por_uuid(datos.responsable_cambio_uuid)
        
        proyecto_id = self._get_project_id_from_hu(tarea.historia_usuario.uuid)
        cuenta_proyecto = self._get_cuenta_proyecto_by_user_id_and_project_id(current_user.id, proyecto_id)
        if not self._has_permission(cuenta_proyecto, "tarea:revisar"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Tu no eres el encargado de revisar la tarea."
            )
        
        if tarea.estado != EstadoTareaEnum.PENDIENTE_POR_REVISAR:
            raise ValueError(f"La tarea aún no ha sido enviada a revisión. El responsable debe marcarla como pendiente por revisar antes de poder evaluarla.")

        tarea._usuario_autor_id = revisor.id
        
        if datos.aprobado:
            tarea.estado = EstadoTareaEnum.COMPLETADA
            tarea.comentario_para_ajustes = None
        else:
            
            if not datos.comentario:
                raise ValueError("Se debe proporcionar un comentario explicando los ajustes requeridos.")
            
            tarea.estado = EstadoTareaEnum.AJUSTES_REQUERIDOS
            tarea.comentario_para_ajustes = datos.comentario

        try:
            self.db.commit()
            self.db.refresh(tarea)
            return tarea
        except Exception as e:
            self.db.rollback()
            raise ValueError(f"Error al procesar la revisión de la tarea: {str(e)}")