from app.models.base_model_orm import BaseModelORM
from sqlalchemy import Column, String, Integer, ForeignKey, DateTime, func, Enum
from sqlalchemy.orm import relationship
from datetime import datetime
from app.models.enums.prioridad_historia_usuario import Prioridad
from app.models.enums.estado_historia_usuario_enum import Estado
from app.models.cuenta_proyecto import CuentaProyecto
from app.models.requisitos_historias_usuario import requisitos_historias_usuario


class HistoriaUsuario(BaseModelORM):
    __tablename__ = "historias_usuario"

    titulo = Column(String(256), nullable=False)
    identificador = Column(String(100), nullable=True)
    descripcion = Column(String(550), nullable=False)

    prioridad = Column(Enum(Prioridad), nullable=False)
    estado = Column(Enum(Estado), nullable=False, default=Estado.PENDIENTE)

    estimacion = Column(Integer, nullable=True)  # Estimación puntos de historia

    requisitos = relationship(
        "Requisito",
        secondary=requisitos_historias_usuario,
        back_populates="historias_usuario"
    )
    
    creado_por_id = Column(Integer, ForeignKey("cuentas.id"), nullable=False)
    creado_por = relationship(
        "Cuenta",
        foreign_keys=[creado_por_id]
    )

    # Relación con Sprint (muchos a uno)
    sprint_id = Column(Integer, ForeignKey("sprints.id"), nullable=True)
    sprint = relationship("Sprint", back_populates="historias_usuario")

    # Criterios de aceptación para saber cuándo se cumple la historia
    criterios_aceptacion = Column(String(1000), nullable=True)

    fecha_creacion = Column(DateTime, server_default=func.now(), nullable=False)
    fecha_ultima_modificacion = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relación con las tareas
    tareas = relationship("Tarea", back_populates="historia_usuario")

    # Relación con los defectos
    defectos = relationship("Defecto", back_populates="historia_usuario")

    historial_cambios = relationship("HistorialHistoriaUsuario", back_populates="historia_usuario")
