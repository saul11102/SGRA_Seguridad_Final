from enum import Enum
from sqlalchemy import Column, String, Integer, ForeignKey, DateTime, func, Enum as SAEnum
from sqlalchemy.orm import relationship
from app.models.base_model_orm import BaseModelORM


class EstadoTareaEnum(str, Enum):
    PENDIENTE = "PENDIENTE"
    ASIGNADA = "ASIGNADA"
    EN_PROGRESO = "EN_PROGRESO"
    PENDIENTE_POR_REVISAR = "PENDIENTE_POR_REVISAR"
    AJUSTES_REQUERIDOS = "AJUSTES_REQUERIDOS"
    COMPLETADA = "COMPLETADA"

class PrioridadTareaEnum(str, Enum):
    ALTA = "ALTA"
    MEDIA = "MEDIA"
    BAJA = "BAJA"
    

class Tarea(BaseModelORM):
    __tablename__ = "tareas"

    identificador = Column(String(100), nullable=False)
    titulo = Column(String(150), nullable=False)
    descripcion = Column(String(255), nullable=True)
    criterios_entrada = Column(String(255), nullable=True) # Criterios que deben cumplirse antes de iniciar la tarea
    criterios_salida = Column(String(255), nullable=True) # Criterios que deben cumplirse para considerar la tarea como completada
    comentario_para_ajustes = Column(String(255), nullable=True) # Comentarios para ajustes en caso de que la tarea pase a un estado ajustes requeridos
    
    # fechas
    fecha_creacion = Column(DateTime, server_default=func.now(), nullable=False)
    fecha_limite = Column(DateTime, nullable=True) # Fecha límite para completar la tarea
    
    tipo_tarea = Column(String(100), nullable=True) # Tipo de tarea (e.g., desarrollo, prueba, documentación)
    estimacion_horas = Column(Integer, nullable=True) # Estimación de horas para completar la tarea

    # Relaciones con Enumeraciones
    estado = Column(SAEnum(EstadoTareaEnum), nullable=False, default=EstadoTareaEnum.PENDIENTE)
    prioridad = Column(SAEnum(PrioridadTareaEnum), nullable=False, default=PrioridadTareaEnum.MEDIA)

    # Relación con las Historias de usuario
    historia_usuario_id = Column(Integer, ForeignKey('historias_usuario.id'), nullable=False)
    historia_usuario = relationship("HistoriaUsuario", back_populates="tareas")
    
    # Relación con la cuenta responsable de hacer la tarea
    cuenta_proyecto_id = Column(Integer, ForeignKey('cuentas_proyecto.id'), nullable=True)
    responsable = relationship("CuentaProyecto", back_populates="tareas")
