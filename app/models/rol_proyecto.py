from app.models.base_model_orm import BaseModelORM
from sqlalchemy import Column, String, Integer
from sqlalchemy.orm import relationship
from sqlalchemy import ForeignKey

class RolProyecto(BaseModelORM):
    __tablename__ = "roles_proyecto"

    nombre = Column(String(50), nullable=False)
    descripcion = Column(String(255), nullable=True)

    cuentas_proyecto = relationship("CuentaProyecto", back_populates="rol_proyecto")
    permisos_rol = relationship("RolPermiso", back_populates="rol", cascade="all, delete-orphan", viewonly=False)
    proyecto_id = Column(Integer, ForeignKey("proyectos.id"))
    proyecto = relationship("Proyecto", back_populates="roles_proyecto")