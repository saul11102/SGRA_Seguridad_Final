from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func, select, inspect, case

from app.models.cuenta import Cuenta
from app.models.cuenta_proyecto import CuentaProyecto
from app.models.permiso import Permiso
from ..models.requisito import Requisito, EstadoRequisitoEnum, TipoRequisitoEnum, PrioridadRequisitoEnum
from ..models.proyecto import Proyecto
from ..models.historial_requisito import HistorialRequisito
from ..schemas.requisito_schema import schema_guardar_requisito, schema_modificar_requisito, schema_listar_historial, schema_responder_aprobacion
from typing import Optional, Tuple
from app.models.enums.estado_historia_usuario_enum import Estado
from app.core.security import get_current_user
from app.models.rol_permiso import RolPermiso

class Requisito_service:
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
    
    def _buscar_proyecto_por_uuid(self, proyecto_uuid: str) -> Proyecto:
        proyecto = self.db.query(Proyecto).filter(Proyecto.uuid == proyecto_uuid).first()
        if not proyecto:
            raise HTTPException(404, f"El proyecto no existe")
        return proyecto

    def _buscar_requisito_por_uuid(self, requisito_uuid: str) -> Requisito:
        requisito = self.db.query(Requisito).filter(Requisito.uuid == requisito_uuid).first()
        if not requisito:
            raise HTTPException(404, f"El requisito no existe")
        return requisito

    def guardar_requisito(self, datos: schema_guardar_requisito, current_user: Cuenta) -> str:
        proyecto = self.buscar_proyecto_por_uuid(datos.proyecto_uuid)
        
        cuenta_proyecto = self._get_cuenta_proyecto_by_user_id_and_project_id(current_user.id, proyecto.id)
        if not self._has_permission(cuenta_proyecto, "requisito:crear"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tienes permiso para guardar un requisito."
            )
        
        if not self.validar_nombre_minimo(datos.nombre):
            raise ValueError("El nombre del requisito debe tener al menos 5 caracteres.")
        if not self.validar_descripcion_minimo(datos.descripcion):
            raise ValueError("La descripción del requisito debe tener al menos 5 caracteres.")
        if not self.validar_nombre_requisito(proyecto.id, datos.nombre):
            raise ValueError(f"Ya existe un requisito con el nombre '{datos.nombre}' en este proyecto.")
        
        nuevo_requisito = Requisito(
            identificador   =self.obtener_siguiente_identificador(proyecto.uuid),
            nombre=datos.nombre,
            descripcion=datos.descripcion,
            tipo=datos.tipo_requisito,
            prioridad=datos.prioridad,
            estado=EstadoRequisitoEnum.PENDIENTE,
            proyecto_id=proyecto.id,
            fuente=datos.fuente,
            metodo_verificacion=datos.metodo_verificacion,
            categoria=datos.categoria,
            horas_esfuerzo_estimado=datos.horas_esfuerzo_estimado,
            riesgo=datos.riesgo,
            comentarios=datos.comentarios
        )
        self.db.add(nuevo_requisito)
        self.db.commit()    
        self.db.refresh(nuevo_requisito)
        return nuevo_requisito

    # Calcula el siguiente identificador para un requisito
    def obtener_siguiente_identificador(self, proyecto_uuid: str) -> str:
        proyecto = self.buscar_proyecto_por_uuid(proyecto_uuid)
        prefijo = f"Requisito_"
        cantidad = self.contar_requisitos(proyecto.id)
        siguiente_numero = cantidad + 1
        identificador = f"{prefijo}_{siguiente_numero:03d}"
        return identificador

    # Busca un proyecto por su UUID
    def buscar_proyecto_por_uuid(self, proyecto_uuid: str) -> Proyecto:
        proyecto = self.db.query(Proyecto).filter(Proyecto.uuid == proyecto_uuid).first()
        if not proyecto:
            raise ValueError(f"El proyecto no existe")
        return proyecto
    
    # Cuenta los requisitos (distinguiendo entre los diferentes tipos) asociados a un proyecto
    def contar_requisitos(self, proyecto_id: int) -> int:
        return self.db.query(func.count(Requisito.id)).filter(
            Requisito.proyecto_id == proyecto_id,
        ).scalar()

    # Busca un requisito por su UUID
    def buscar_requisito_por_uuid(self, requisito_uuid: str) -> Requisito:
        requisito = self.db.query(Requisito).filter(Requisito.uuid == requisito_uuid).first()
        if not requisito:
            raise ValueError(f"El requisito no existe")
        return requisito

    # Modifica un requisito existente. Se pasa el UUID del requisito a modificar y
    # los datos con los campos actualizables (nombre, descripcion, tipo, prioridad).
    def modificar_requisito(self, datos: schema_modificar_requisito, current_user: Cuenta) -> Requisito:
        requisito = self.buscar_requisito_por_uuid(datos.requisito_uuid)

        cuenta_proyecto = self._get_cuenta_proyecto_by_user_id_and_project_id(current_user.id, requisito.proyecto_id)
        if not self._has_permission(cuenta_proyecto, "requisito:modificar"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tienes permiso para modificar el requisito."
            )
         
        if requisito.estado == EstadoRequisitoEnum.OBSOLETO:
            raise ValueError("No se puede modificar un requisito que se encuentra en estado OBSOLETO.")
        if not self.validar_nombre_minimo(datos.nombre):
            raise ValueError("El nombre del requisito debe tener al menos 5 caracteres.")
        if not self.validar_descripcion_minimo(datos.descripcion):
            raise ValueError("La descripción del requisito debe tener al menos 5 caracteres.")
        if not self.validar_nombre_requisito(requisito.proyecto_id, datos.nombre, requisito.id):
            raise ValueError(f"Ya existe un requisito con el nombre '{datos.nombre}' en este proyecto.")
        requisito.nombre = datos.nombre
        requisito.descripcion = datos.descripcion
        requisito.tipo = datos.tipo_requisito
        requisito.prioridad = datos.prioridad
        requisito.metodo_verificacion = datos.metodo_verificacion
        requisito.categoria = datos.categoria
        requisito.riesgo = datos.riesgo
        #opcionales
        if datos.fuente is not None:
            requisito.fuente = datos.fuente
        if datos.horas_esfuerzo_estimado is not None:
            requisito.horas_esfuerzo_estimado = datos.horas_esfuerzo_estimado
        if datos.comentarios is not None:
            requisito.comentarios = datos.comentarios
        if requisito.estado == EstadoRequisitoEnum.RECHAZADO:
            requisito.estado = EstadoRequisitoEnum.PENDIENTE
        self.db.commit()
        self.db.refresh(requisito)
        return requisito  

    def requisito_marcar_obsoleto(self, datos, current_user: Cuenta) -> Requisito:
        requisito = self.buscar_requisito_por_uuid(datos.requisito_uuid)
        
        autor = self._get_cuenta_proyecto_by_user_id_and_project_id(current_user.id, requisito.proyecto_id)
        if not self._has_permission(autor, "requisito:eliminar"): 
             raise HTTPException(403, "No tienes permiso para marcar requisitos como obsoletos")
         
        if not requisito:
            raise ValueError("El requisito no existe")
            
        elif datos.nuevo_estado == EstadoRequisitoEnum.OBSOLETO:
            self.validar_vinculacion_historias_activas(requisito)
            if not datos.razon_obsoleto:
                raise ValueError("Debe especificarse una razón al marcar el requisito como obsoleto.")
            self.cambiar_estado_obsoleto(requisito)
            requisito.razon_obsoleto = datos.razon_obsoleto
        else:
            raise ValueError("Esta operación solo permite marcar un requisito como OBSOLETO.")
        self.db.commit()
        self.db.refresh(requisito)
        return requisito

    def listar_requisitos(
        self, 
        proyecto_uuid: str, 
        current_user: Cuenta,
        skip: int = 0, 
        limit: int = 10, 
        tipo: Optional[TipoRequisitoEnum] = None,
        prioridad: Optional[PrioridadRequisitoEnum] = None,
        estado: Optional[EstadoRequisitoEnum] = None,
    ) -> Tuple[list[Requisito], int]:
    
        proyecto = self.buscar_proyecto_por_uuid(proyecto_uuid)
        
        self._get_cuenta_proyecto_by_user_id_and_project_id(current_user.id, proyecto.id)

        query = self.db.query(Requisito).filter(
            Requisito.proyecto_id == proyecto.id
        )

        if tipo:
            query = query.filter(Requisito.tipo == tipo)

        if prioridad:
            query = query.filter(Requisito.prioridad == prioridad)

        if estado:
            query = query.filter(Requisito.estado == estado)
        else:
            query = query.filter(
                Requisito.estado != EstadoRequisitoEnum.OBSOLETO
            )

        total = query.count()

        requisitos = (
            query
            .order_by(Requisito.id.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

        return requisitos, total
    
    def listar_historial(self, requisito_uuid: str, current_user: Cuenta) -> list:
        requisito = self.buscar_requisito_por_uuid(requisito_uuid)
        if not requisito:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Requisito no encontrado."
            )

        cuenta_proyecto = self._get_cuenta_proyecto_by_user_id_and_project_id(
            current_user.id,
            requisito.proyecto.id
        )

        if not self._has_permission(cuenta_proyecto, "requisito:historial"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tienes permiso para ver el historial."
            )
        
        registros = (
            self.db.query(HistorialRequisito)
            .filter(HistorialRequisito.requisito_id == requisito.id)
            .order_by(
                HistorialRequisito.version.desc(),
                HistorialRequisito.fecha.desc()
            )
            .all()
        )

        historial = {}

        for r in registros:
            if r.version not in historial:
                historial[r.version] = {
                    "version": r.version,
                    "fecha": r.fecha,
                    "cambios": set(),
                    "requirement": r
                }
            historial[r.version]["cambios"].add(r.tipo_cambio)

        return [
            {
                "version": h["version"],
                "fecha": h["fecha"],
                "cambios": sorted(list(h["cambios"])),
                "requirement": h["requirement"]
            }
            for h in sorted(
                historial.values(),
                key=lambda x: x["version"]
            )
        ]
    
    def validar_nombre_requisito(self, proyecto_id: int, nombre: str, requisito_id_actual: int = None) -> bool:
        query = self.db.query(Requisito).filter(
            Requisito.proyecto_id == proyecto_id,
            func.lower(Requisito.nombre) == nombre.lower()
        )
        if requisito_id_actual:
            query = query.filter(Requisito.id != requisito_id_actual)
        requisito_existente = query.first()
        return requisito_existente is None
    
    def validar_nombre_minimo(self, nombre: str, min_chars: int = 5) -> bool:
        return len(nombre.strip()) >= min_chars

    def validar_descripcion_minimo(self, descripcion: str, min_chars: int = 5) -> bool:
        return len(descripcion.strip()) >= min_chars
    
    def validar_vinculacion_historias_activas(self, requisito: Requisito):
        estados_bloqueantes = [
            Estado.PENDIENTE, 
            Estado.EN_PROCESO, 
            Estado.COMPLETADA, 
            Estado.ATRASADA
        ]
        
        for hu in requisito.historias_usuario:
            if hu.estado in estados_bloqueantes:
                raise ValueError(
                    f"No se puede eliminar este requisito, ya que tiene  historias de usuario activas en este momento")

    def responder_aprobacion(self, datos: schema_responder_aprobacion, current_user: Cuenta) -> Requisito:
        requisito = self.buscar_requisito_por_uuid(datos.requisito_uuid)
        
        autor = self._get_cuenta_proyecto_by_user_id_and_project_id(current_user.id, requisito.proyecto_id)
        if not self._has_permission(autor, "requisito:aprobar"):
            raise HTTPException(403, "No tienes permiso para aprobar o rechazar requisitos")
         
        if requisito.estado != EstadoRequisitoEnum.PENDIENTE:
            raise ValueError(f"El requisito no está en estado PENDIENTE y no puede ser aprobado o rechazado.")

        if datos.aprobar:
            requisito.estado = EstadoRequisitoEnum.APROBADO
        else:
            requisito.estado = EstadoRequisitoEnum.RECHAZADO 
            if not datos.motivo_rechazo:
                raise ValueError("Es obligatorio indicar un comentario/razón para rechazar el requisito.")
            requisito.motivo_rechazo = datos.motivo_rechazo

        self.db.commit()
        self.db.refresh(requisito)
        return requisito