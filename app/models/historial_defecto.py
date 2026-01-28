from sqlalchemy import Column, String, Integer, ForeignKey, DateTime, func, Enum as SAEnum
from sqlalchemy.orm import relationship
from app.models.base_model_orm import BaseModelORM
from .defecto import EstadoDefectoEnum

class HistorialDefecto(BaseModelORM):
    __tablename__ = "historial_defectos"

    defecto_id = Column(Integer, ForeignKey("defectos.id"), nullable=False)
    modificado_por_id = Column(Integer, ForeignKey("cuentas_proyecto.id"), nullable=True)
    
    estado_anterior = Column(SAEnum(EstadoDefectoEnum), nullable=True)
    estado_nuevo = Column(SAEnum(EstadoDefectoEnum), nullable=False)
    
    fecha_cambio = Column(DateTime, server_default=func.now(), nullable=False)
    comentario = Column(String(500), nullable=True)

    defecto = relationship("Defecto", back_populates="historial_estados")
    modificado_por = relationship("CuentaProyecto")
