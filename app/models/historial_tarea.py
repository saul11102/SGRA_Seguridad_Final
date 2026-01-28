from sqlalchemy import Column, String, Integer, ForeignKey, DateTime, func
from sqlalchemy.orm import relationship
from app.models.base_model_orm import BaseModelORM

class HistorialTarea(BaseModelORM):
    __tablename__ = "historial_tareas"

    id = Column(Integer, primary_key=True, autoincrement=True)
    
    fecha_modificacion = Column(DateTime, server_default=func.now(), nullable=False) 
    tipo_cambio = Column(String(255), nullable=False) 
    
    tarea_id = Column(Integer, ForeignKey('tareas.id'), nullable=False) 
    
    modificado_por_id = Column(Integer, ForeignKey('cuentas_proyecto.id'), nullable=True) #
    modificado_por = relationship("CuentaProyecto") #