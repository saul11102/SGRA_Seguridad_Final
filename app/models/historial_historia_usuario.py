from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, func
from sqlalchemy.orm import relationship

from app.models.base_model_orm import BaseModelORM


class HistorialHistoriaUsuario(BaseModelORM):
    __tablename__ = "historial_historias_usuario"

    historia_usuario_id = Column(Integer, ForeignKey("historias_usuario.id"), nullable=False)
    modificado_por_id = Column(Integer, ForeignKey("cuentas_proyecto.id"), nullable=True)

    campo = Column(String(100), nullable=False)
    valor_anterior = Column(String(1000), nullable=True)
    valor_nuevo = Column(String(1000), nullable=True)
    fecha_modificacion = Column(DateTime, server_default=func.now(), nullable=False)

    historia_usuario = relationship("HistoriaUsuario", back_populates="historial_cambios")
    modificado_por = relationship("CuentaProyecto")
