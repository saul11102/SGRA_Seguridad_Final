
from app.models.base_model_orm import BaseModelORM
from sqlalchemy import Column, String, Integer, ForeignKey
from sqlalchemy.orm import relationship

class CuentaProyecto(BaseModelORM):
    __tablename__ = "cuentas_proyecto"

    cuenta_id = Column(Integer, ForeignKey("cuentas.id"))
    proyecto_id = Column(Integer, ForeignKey("proyectos.id"))
    rol_proyecto_id = Column(Integer, ForeignKey("roles_proyecto.id"))
    cuenta = relationship("Cuenta", back_populates="proyectos")
    proyecto = relationship("Proyecto", back_populates="cuentas")
    rol_proyecto = relationship("RolProyecto", back_populates="cuentas_proyecto")
    
    #relación a tareas
    tareas = relationship("Tarea", back_populates="responsable")
    #relación a defectos
    defectos = relationship("Defecto", back_populates="cuenta_proyecto")