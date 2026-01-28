from app.models.base_model_orm import BaseModelORM
from sqlalchemy import Column, String, Date, Enum, Integer, ForeignKey
from sqlalchemy.orm import relationship
from app.models.enums.estado_sprint_enum import EstadoSprint


class Sprint(BaseModelORM):
    __tablename__ = "sprints"

    nombre = Column(String(100), nullable=False)
    fecha_inicio = Column(Date, nullable=False)
    fecha_fin = Column(Date, nullable=False)
    objetivo = Column(String(500), nullable=False)
    estado = Column(Enum(EstadoSprint), nullable=False, default=EstadoSprint.PLANIFICADO)
    
    # Relación con proyecto
    proyecto_id = Column(Integer, ForeignKey("proyectos.id"), nullable=False)
    proyecto = relationship("Proyecto", backref="sprints")
    
    # Relación uno a muchos con historias de usuario
    # NO usamos cascade delete-orphan para preservar historias al eliminar sprint
    historias_usuario = relationship(
        "HistoriaUsuario",
        back_populates="sprint",
        foreign_keys="HistoriaUsuario.sprint_id"
    )
